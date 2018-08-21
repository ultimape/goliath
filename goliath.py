#!/usr/bin/env python

'''
Goliath Birdeater
by @ultimape

A birdsite spider; For backing up your external brain.
Eats backups, shits tweets

The Goliath bird-eating spider;
    "Despite its name, it is rare for the Goliath birdeater to actually prey on birds; [...]
    it is not uncommon for this species to kill and consume
    a variety of insects and small terrestrial vertebrates."
    https://en.wikipedia.org/wiki/Goliath_birdeater

Site: murmurology.wovensoup.com

This is free and unencumbered software released into the public domain.
Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means. For more information, please refer to <http://unlicense.org/>
'''

import argparse
import json
import re
import sys
import time
from urllib.parse import urlparse
from twarc import Twarc
import os

from eatgrail import eatgrail as graileater

# load the secrets to run twarc against a valid API
with open("twarc_creds.secret") as secrets_file:
    twitter_consumer_key = secrets_file.readline().rstrip('\n')
    twitter_consumer_secret = secrets_file.readline().rstrip('\n')
    twitter_access_token = secrets_file.readline().rstrip('\n')
    twitter_access_token_secret = secrets_file.readline().rstrip('\n')
    secrets_file.close()

twarc = Twarc(twitter_consumer_key, twitter_consumer_secret, twitter_access_token, twitter_access_token_secret)


# Handles configuration of command line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description='A birdsite spider; For backing up your external brain')
    parser.add_argument('--journal-location',
                        dest='JOURNAL_LOCATION',
                        default='runtime_journal_log.jsonl',
                        help='location for the journal to save/load spider state from')
    parser.add_argument('--continue-after-failure',
                        action='store_true',
                        help='continue if something hits an error')
    parser.add_argument('-dr', '--dry-run',
                        action='store_true',
                        help='don\'t modify or download anything')
    parser.add_argument('-ts', '--tweet-source',
                        type=str, dest='TWEETS_LOCATION',
                        default='tweets.txt',
                        help='the file to load tweets from')
    parser.add_argument('-extract', '--extract-backup',
                        type=str, dest='TWITTER_EXPORT_LOCATION',
                        help="the location of the twitter export to parse for tweet IDs, as a directory")
    parser.add_argument('-jsonl', '--input-is-jsonl',
                        action='store_true',
                        help='the tweets are stored in a jsonl format')
    parser.add_argument('--parse-twitter-export',
                        action='store_true',
                        help='the tweets stored in the twitter backup format')
    return parser.parse_args()


def main():
    # Set Up
    args = parse_arguments()

    if args.dry_run is not None:
        print("dry-run detected")

    if args.TWITTER_EXPORT_LOCATION is not None:
        print("Extract Twitter Export Mode Detected\n\t[value is \"%s\"]" % args.TWITTER_EXPORT_LOCATION)
        graileater.parse_twitter_export_for_ids(args.TWITTER_EXPORT_LOCATION)

    print(args.TWEETS_LOCATION)

    # TODO: update this to work with unicode characters in usernames (forign languages?),
    # but in a way that doesn't risk corrupting the filesystem
    ascii_pattern = re.compile('[^a-zA-Z0-9_]+')

    # We use a dict to store filenames of users we write to
    # this lets us track all the open files to close them later
    # it also gives us a way to check if a file is open already or not
    # this avoids continuously running the open() command, speading this up a bit for large tweet collections
    tweet_files = dict()

    # We use a dict to store filenames of users we write to
    # this lets us track all the open files to close them later
    # it also gives us a way to check if a file is open already or not
    # this avoids continuously running the open() command, speading this up a bit for large tweet collections
    media_url_files = dict()

    print("Beginning twarc tweet download")
    try:

        print("  Creating /tweet/ dirctory")
        if not os.path.exists('tweets'):
            os.makedirs('tweets')

        print("  creating /media/ directory")
        if not os.path.exists('media'):
            os.makedirs('media')

        tweet_count = 0
        user_count = 0
        media_count = 0
        last_tweet_count = 0
        last_user_count = 0
        last_media_count = 0

        should_display_tweet_count = False
        should_display_user_count = False
        should_display_media_count = False

        for tweet in twarc.hydrate(open(args.TWEETS_LOCATION)):
            tweet_json = json.dumps(tweet)

            # writing to the file system? make sure the shit isn't going to overwrite /etc/passwd
            unsafe_username = tweet["user"]["screen_name"]
            safe_username = ascii_pattern.sub('', str(unsafe_username))

            unsafe_userid = tweet["user"]["id"]
            safe_userid = ascii_pattern.sub('', str(unsafe_userid))

            # generate a filename programatically
            filename_pre = "%s_%s" % (safe_userid, safe_username)
            filename = "tweets/%s/%s_twarc_output.jsonl" % (filename_pre, filename_pre)

            media_urls_filename = "media/%s/%s_index.jsonl" % (filename_pre, filename_pre)

            if filename not in tweet_files:
                user_count += 1

                if not os.path.exists('tweets/'+filename_pre):
                    os.makedirs('tweets/' + filename_pre)

                if not os.path.exists('media/'+filename_pre):
                    os.makedirs('media/' + filename_pre)

                #print("  creating file for %s (%s)" % (tweet["user"]["screen_name"], tweet["user"]["id"]))
                try:
                    if filename not in tweet_files:
                        tweet_files[filename] = open(filename, 'a')
                    else:
                        if tweet_files[filename].closed:
                            tweet_files[filename] = open(filename, 'a')
                except:
                    print("  exception encountered while trying to create %s, closing open files (may take a moment)" % filename)
                    close_all_open_handles(tweet_files)
                    close_all_open_handles(media_url_files)
                finally:
                    try:
                        if filename not in tweet_files:
                            tweet_files[filename] = open(filename, 'a')
                        else:
                            if tweet_files[filename].closed:
                                tweet_files[filename] = open(filename, 'a')

                    except:
                        print("Can not open %s" % filename)
                        raise
                tweet_files[filename].truncate()

                try:
                    if media_urls_filename not in media_url_files:
                        media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
                    else:
                        if media_url_files[media_urls_filename].closed:
                            media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
                except:
                    print("  exception encountered while trying to create %s, closing open files (may take a moment)" % filename)
                    close_all_open_handles(tweet_files)
                    close_all_open_handles(media_url_files)
                finally:
                    try:
                        if media_urls_filename not in media_url_files:
                            media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
                        else:
                            if media_url_files[media_urls_filename].closed:
                                media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
                    except:
                        print("  Can not open %s" % media_urls_filename)
                        raise
                media_url_files[media_urls_filename].truncate()

            try:
                if tweet_files[filename].closed:
                    tweet_files[filename] = open(filename, 'a')
            except:
                print("  exception encountered while trying to open %s, closing open files (may take a moment)" % filename)
                close_all_open_handles(tweet_files)
                close_all_open_handles(media_url_files)
            finally:
                try:
                    if tweet_files[filename].closed:
                        tweet_files[filename] = open(filename, 'a')
                except:
                    print("  Can not open %s" % filename)
                    raise

            # store the json we got from the tweet
            tweet_files[filename].write("%s\n" % tweet_json)
            tweet_count += 1

            try:
                if media_url_files[media_urls_filename].closed:
                    media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
            except:
                print("  exception encountered while trying to open %s, closing open files (may take a moment)" % media_urls_filename)
                close_all_open_handles(tweet_files)
                close_all_open_handles(media_url_files)
            finally:
                try:
                    if media_url_files[media_urls_filename].closed:
                        media_url_files[media_urls_filename] = open(media_urls_filename, 'a+')
                except:
                    print("Can not open %s" % media_urls_filename)
                    raise

            media_count += extract_media_links_to_file(tweet, media_url_files[media_urls_filename])

            # Periodically display counts of things

            # Only display if they change
            if last_tweet_count != tweet_count:
                should_display_tweet_count = True
                last_tweet_count = tweet_count
            else:
                should_display_tweet_count = False

            if last_user_count != user_count:
                should_display_user_count = True
                last_user_count = user_count
            else:
                should_display_user_count = False

            if last_media_count != media_count:
                should_display_media_count = True
                last_media_count = media_count
            else:
                should_display_media_count = False

            # Only display if big number
            if should_display_tweet_count and not tweet_count % 100:
                print("Stored: %s Tweets, From %s Users, and captured %s Media URLs" % (tweet_count, user_count, media_count))

            if should_display_user_count and not user_count % 100:
                print("Stored: %s Tweets, From %s Users, and captured %s Media URLs" % (tweet_count, user_count, media_count))

            if should_display_media_count and not media_count % 100:
                print("Stored: %s Tweets, From %s Users, and captured %s Media URLs" % (tweet_count, user_count, media_count))

            # print("%s by %s (%s)" % (tweet["id"], tweet["user"]["screen_name"], tweet["user"]["id"]))
    finally:
        # don't forget to close all the open handles (since we aren't using 'with open')
        print("Stored: %s Tweets, From %s Users, and captured %s Media URLs" % (tweet_count, user_count, media_count))
        print("Done downloading tweets, Closing files (may take a moment)")
        close_all_open_handles(tweet_files)
        close_all_open_handles(media_url_files)


def close_all_open_handles(file_set):
    for filename in file_set:
        if not file_set[filename].closed:
            #print("  closing %s" % filename)
            file_set[filename].close()


def extract_media_links_to_file(tweet, file):
    media_count = 0
    # media extraction done via modified version of DocNow/Twarc/utils/media_urls.py (file was licened as MIT)
    if 'media' in tweet['entities']:
        for media in tweet['entities']['media']:
            if media['type'] == 'photo':
                file.write(media['media_url_https'])
                file.write('\n')
                media_count += 1

    if 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
        for media in tweet['extended_entities']['media']:

            if media['type'] == 'animated_gif':
                file.write(media['media_url_https'])
                file.write('\n')
                media_count += 1

            if 'video_info' in media:
                for v in media['video_info']['variants']:
                    file.write(v['url'])
                    file.write('\n')
                    media_count += 1
    return media_count


# parse and strip twitter backup/export
# input tweets
# download queue
# injest queue(s)
# psudocode
# until ingress queues are empty
#   get next ingress queue
#   For each tweet_id in ingress queue
#       Try to download (enqueue in download queue)
#       if downloaded (check status)
#            Persist tweet
#            Put in parse queue
#        else log error to journal
#   for each unparsed tweet
#       exhume tweet
#           extract retweets as tweet_id
#           extract quote tweets as tweet_id
#           extract extra tweets from urls as tweet_id
#           extrat in_reply_to as tweet_id
#           store extracted ids into relevant injest queue
#       exhume media
#           save details into dated file for wgetting
#           // can we WGET via python?
#           // if so maybe enqueue into wget?
#           // ideally we have a way to store tweet data into a user/media/YYYY-MM/ format
#       extract all other links and save into archive queue
#       mark harvest state in journal

# persist
#  clean up
#       deshorten
#   save tweet data jsonl into user/tweets/YYYY-MM/YYYYMMDD_userid_username_tweettype.jsonl
#       add to existing jsonl if exists
#       dedupe
#       or create new if doesn't
#       regenerate index.jsonl mapping tweet_id to .json filename
#       mark save update journal


if __name__ == "__main__":
    main()
