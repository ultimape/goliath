#!/usr/bin/env python

'''
Eat Grail
by @ultimape

This tool consumes the twitter backup/export (codenamed 'Grailbird') and poops out tweet IDs.

Part of "Goliath Birdeater" A birdsite spider; For backing up your external brain.
Eats backups, shits tweets

The Goliath bird-eating spider;
    "Despite its name, it is rare for the Goliath birdeater to actually prey on birds; [...]
    it is not uncommon for this species to kill and consume
    a variety of insects and small terrestrial vertebrates."
    https://en.wikipedia.org/wiki/Goliath_birdeater

Site: murmurology.wovensoup.com

Credits:
Modified
  "Twitter export image fill 1.10"
    by Marcin Wichary (aresluna.org)
    Site: https://github.com/mwichary/twitter-export-image-fill
    
    I borrowed and tweaked some code from it
    To handle the parsing of the twitter export data.
    So we can harvest tweet IDs from a personal backup/export
    Since the twitter API is limited

This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means. For more information, please refer to <http://unlicense.org/>
'''

import argparse
import json
import os
import zipfile
import re
import sys
import time
from urllib.parse import urlparse


# Handles configuration of command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='A birdsite spider; For backing up your external brain')
    parser.add_argument('-extract', '--extract-backup',
                        type=str, dest='TWITTER_EXPORT_LOCATION',
                        help="the location of the twitter export to parse for tweet IDs, as a directory, or a zip file")
    return parser.parse_args()


def main():
    # Set Up
    args = parse_arguments()

    print("Extract Twitter Export Mode Detected\n\t[value is \"%s\"]" % args.TWITTER_EXPORT_LOCATION)
    parse_twitter_export_for_ids(args.TWITTER_EXPORT_LOCATION)


# Takes a twitter export file and parses out relevant tweet IDs for processing later
def parse_twitter_export_for_ids(EXPORT_LOCATION):

    EXPORT_LOCATION = EXPORT_LOCATION.strip().rstrip("/")

    # some sanity checks for the export location
    is_zip_archive = test_if_zip_archive(EXPORT_LOCATION)
    is_corrupt = test_if_zip_archive_corrupt(EXPORT_LOCATION)

    if is_zip_archive and is_corrupt:
        print("Could not open the Archive Zip!")
        print("    (location:\"%s\")" % EXPORT_LOCATION)
        print("  It appears corrupt.")
        print("")
        sys.exit(-1)

    if is_zip_archive:
        print("  Archive is a Zip File.")

    print("  Attempting to load tweet export index.")
    tweets_by_month = load_tweet_export_index(EXPORT_LOCATION, is_zip_archive)

    month_count = len(tweets_by_month)
    print("    Found %s Months in Export" % month_count)

    tweet_count = 0
    for month in tweets_by_month:
        tweet_count += month['tweet_count']
    print("    Found %s Total Tweets in Export" % tweet_count)

    print("  Begining extract.")
    total_tweet_count, total_retweet_count, total_quotetweet_count, total_replyto_count = \
        extract_tweets_from_tweet_export(tweets_by_month, EXPORT_LOCATION, is_zip_archive)
    total_tweet_ids = total_tweet_count + total_retweet_count + total_quotetweet_count + total_replyto_count

    print("  Extracted %s tweets, %s retweets, %s quotetweets, %s reply_tos. Totalling %s tweets!" %
          (total_tweet_count, total_retweet_count, total_quotetweet_count, total_replyto_count, total_tweet_ids))


def test_if_zip_archive(EXPORT_LOCATION):
    if os.path.exists(EXPORT_LOCATION):
        if os.path.isfile(EXPORT_LOCATION):
            if zipfile.is_zipfile(EXPORT_LOCATION):
                #print("  Archive selected is a Zip file.")
                return True
    return False


def test_if_zip_archive_corrupt(EXPORT_LOCATION):
    try:
        archive_file = zipfile.ZipFile(EXPORT_LOCATION)

        corrupt_file = archive_file.testzip()
        if corrupt_file is not None:
            #print("  Corrupted file detected in Zip Archive! %s" % corrupt_file)
            pass
        else:
            #print("  Zip Archive seems sound.")
            return False
    except Exception as e:
        #print("  Archive was unable to be opened as a Zip. (Exception: %s)" % str(e))
        return False

    return True


# loads the twitter export index into a json compatible format for later digestion
def load_tweet_export_index(EXPORT_LOCATION, is_zip_archive):

    # TODO: Handling Zips ought to be abstracted to avoid the duplication

    if is_zip_archive:
        try:
            with zipfile.ZipFile(EXPORT_LOCATION) as tweet_archive:

                index_filename = "data/js/tweet_index.js"
                index_str = tweet_archive.read(index_filename).decode('utf-8')
                index_str = re.sub(r'var tweet_index =', '', index_str)
                print("    loaded \"%s\" from Zip Archive" % index_filename)
                return json.loads(index_str)

        except Exception as e:
            print("Could not open the Archive Zip!")
            print("    (location:\"%s\")" % EXPORT_LOCATION)
            print("  (Exception: %s)" % str(e))
            print("")
            sys.exit(-1)

    else:
        index_filename = EXPORT_LOCATION + "/data/js/tweet_index.js"
        try:
            with open(index_filename) as index_file:
                index_str = index_file.read()
                index_str = re.sub(r'var tweet_index =', '', index_str)
                print("    loaded \"%s\"" % index_filename)
                return json.loads(index_str)

        except Exception as e:
            print("Could not open the data from the archive!")
            print("    (location:\"%s\")" % index_filename)
            print("Please ensure the location exists, and modify the -export parameter as nessisary")
            print("  (Exception: %s)" % str(e))
            print("")
            sys.exit(-1)


# checks if the twitter export tweet is a retweet
def is_retweet(tweet):
    return 'retweeted_status' in tweet.keys()


# grabs all the urls that link to twitter statuses and extracts IDs
def extract_quoted_tweet_links(tweet):
    quote_tweet_ids = list()
    try:

        TWEET_ID_PATTERN = re.compile(r"status/(\d*)$")

        if is_retweet(tweet):
            tweet = tweet['retweeted_status']

        urls = tweet['entities']['urls']

        for entry in urls:
            parsed_url = urlparse(entry['expanded_url'])
            if parsed_url.netloc.endswith("twitter.com"):
                if "/status/" in parsed_url.path:
                    match = TWEET_ID_PATTERN.search(parsed_url.path)
                    if match is not None:
                        quote_tweet_ids.append(match.group(1))

        return quote_tweet_ids
    except KeyError:
        print("keyerror")
        return quote_tweet_ids


# empties out a file of existing data
def clear_file(FILE_NAME):
    with open(FILE_NAME, 'w') as file_to_clear:
        file_to_clear.truncate()
        file_to_clear.close()


# goes through and loads each of the tweet files in the twitter export index and harvest the IDs
def extract_tweets_from_tweet_export(tweets_by_month, EXPORT_LOCATION, is_zip_archive):
    total_tweet_count = 0
    total_retweet_count = 0
    total_quotetweet_count = 0
    total_replyto_count = 0

    tweet_id_filename = "backup_export_tweet_ids.txt"
    retweet_id_filename = "backup_export_retweet_ids.txt"
    retweeted_id_filename = "backup_export_retweeted_ids.txt"
    quotetweet_id_filename = "backup_export_quotetweet_ids.txt"
    replyto_id_filename = "backup_export_replyto_ids.txt"

    # clear out existing tweets to start from fresh (avoids duplicates if ran multiple times)
    clear_file(tweet_id_filename)
    clear_file(retweet_id_filename)
    clear_file(retweeted_id_filename)
    clear_file(quotetweet_id_filename)
    clear_file(replyto_id_filename)

    # Loop 1: Go through all the months
    # ---------------------------------

    tweet_ids_file = open(tweet_id_filename, 'a')
    retweet_ids_file = open(retweet_id_filename, 'a')
    retweeted_ids_file = open(retweeted_id_filename, 'a')
    quotetweet_ids_file = open(quotetweet_id_filename, 'a')
    replyto_ids_file = open(replyto_id_filename, 'a')

    try:
        for date in tweets_by_month:
            try:
                year_str = '%04d' % date['year']
                month_str = '%02d' % date['month']

                tweet_count = 0
                retweet_count = 0
                quotetweet_count = 0
                replyto_count = 0

                # Loop 2: Go through all the tweets in a month
                # --------------------------------------------

                # Load the tweets from either the zip file, or the extracted archive
                # TODO: Handling Zips ought to be abstracted to avoid the duplication

                data = {}  # Data is initialized as empty
                if is_zip_archive:
                    try:
                        with zipfile.ZipFile(EXPORT_LOCATION) as zip_data_file:

                            zip_data_filename = 'data/js/tweets/%s_%s.js' % (year_str, month_str)
                            data_str = zip_data_file.read(zip_data_filename).decode('utf-8')
                            first_data_line = re.match(r'Grailbird.data.tweets_(.*) =', data_str).group(0)
                            data_str = re.sub(first_data_line, '', data_str)
                            data = json.loads(data_str)
                            #print("    Successfully loaded \"%s\" from Zip Archive" % zip_data_filename)

                    except Exception as e:
                        print("Could not open the Archive Zip!")
                        print("    (location:\"%s\")" % zip_data_filename)
                        print("  (Exception: %s)" % str(e))
                        print("")
                        sys.exit(-1)

                else:
                    try:
                        data_filename = EXPORT_LOCATION + '/data/js/tweets/%s_%s.js' % (year_str, month_str)
                        with open(data_filename) as data_file:
                            data_str = data_file.read()
                            # Remove the assignment to a variable that breaks JSON parsing,
                            # but save for later since we have to recreate the file
                            first_data_line = re.match(r'Grailbird.data.tweets_(.*) =', data_str).group(0)
                            data_str = re.sub(first_data_line, '', data_str)
                            data = json.loads(data_str)
                            #print("    Successfully loaded \"%s\" from data Archive" % data_filename)

                    except Exception as e:
                        print("Could not open the data file!")
                        print("    (location:\"%s\")" % data_filename)
                        print("Please ensure the location exists, and modify the -export parameter as nessisary")
                        print("  (Exception: %s)" % str(e))
                        print("")
                        sys.exit(-1)

                # handle each tweet
                for tweet in data:

                    # capture all retweet tweet IDs
                    if is_retweet(tweet):
                        retweet_count += capture_retweet(tweet, retweet_ids_file, retweeted_ids_file)

                    # capture all non-retweet tweet IDs
                    else:
                        tweet_count += capture_tweet(tweet, tweet_ids_file)

                    # capture all embedded links to statuses (these are quote tweets!)
                    quotetweet_count += capture_quotetweet(tweet, quotetweet_ids_file)

                    # capture replyto to recreate context
                    replyto_count += capture_replyto(tweet, replyto_ids_file)

                    # try to capture the retweeted status' replyto since we can
                    if is_retweet(tweet):
                        retweeted_tweet = tweet['retweeted_status']
                        replyto_count += capture_replyto(retweeted_tweet, replyto_ids_file)

                # End loop 2 (tweets in a month)

                print("    Parsed %s tweets, %s retweets, %s quotetweets, and %s reply_tos, from \"data/js/tweets/%s_%s.js\"" %
                      (tweet_count, retweet_count, quotetweet_count, replyto_count, year_str, month_str))
                total_tweet_count += tweet_count
                total_retweet_count += retweet_count
                total_quotetweet_count += quotetweet_count
                total_replyto_count += replyto_count

            # Nicer support for Ctrl-C
            except KeyboardInterrupt:
                print("")
                print("Interrupted! Come back any time.")
                sys.exit(-3)
    finally:
        tweet_ids_file.close()
        retweet_ids_file.close()
        retweeted_ids_file.close()
        quotetweet_ids_file.close()
        replyto_ids_file.close()

    # End loop 1 (all the months)
    return total_tweet_count, total_retweet_count, total_quotetweet_count, total_replyto_count


def capture_tweet(tweet, OUTPUT_FILE):
    try:
        if is_retweet(tweet):
            return 0
        else:
            field = tweet['id']
            OUTPUT_FILE.write(str(field) + "\n")
            return 1
    except KeyError:
        return 0


def capture_retweet(tweet, OUTPUT_FILE_RETWEETS, OUTPUT_FILE_RETWEETED_TWEETS):
    try:
        field = tweet['id']
        if is_retweet(tweet):
            OUTPUT_FILE_RETWEETS.write(str(field) + "\n")
            capture_retweeted(tweet, OUTPUT_FILE_RETWEETED_TWEETS)
            return 1
        return 0
    except KeyError:
        return 0


def capture_retweeted(tweet, OUTPUT_FILE):
    try:
        field = tweet['retweeted_status']['id']
        OUTPUT_FILE.write(str(field) + "\n")
        return 1
    except KeyError:
        return 0


def capture_quotetweet(tweet, OUTPUT_FILE):
    count = 0
    for quotetweet_id in extract_quoted_tweet_links(tweet):
        OUTPUT_FILE.write(str(quotetweet_id) + "\n")
        count += 1
    return count


def capture_replyto(tweet, OUTPUT_FILE):
    try:
        field = tweet['in_reply_to_status_id']
        OUTPUT_FILE.write(str(field) + "\n")
        return 1
    except KeyError:
        return 0


#
if __name__ == "__main__":
    main()
