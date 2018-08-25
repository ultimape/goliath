#!/usr/bin/env python

'''
Goliath Birdeater
by @ultimape

A birdsite spider; For backing up your external brain.
Eats backups, poops tweets

The Goliath bird-eating spider;
    "Despite its name, it is rare for the Goliath birdeater to actually prey on birds; [...]
    it is not uncommon for this species to kill and consume
    a variety of insects and small terrestrial vertebrates."
    https://en.wikipedia.org/wiki/Goliath_birdeater

Site: murmurology.wovensoup.com
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

# TODO: update this to work with unicode characters in usernames (forign languages?),
# but in a way that doesn't risk corrupting the filesystem
ascii_pattern = re.compile('[^a-zA-Z0-9_]+')


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

    is_dry_run = False
    if args.dry_run is not None:
        print("dry-run detected")
        is_dry_run = True

    if args.TWITTER_EXPORT_LOCATION is not None:
        print("Extract Twitter Export Mode Detected\n\t[value is \"%s\"]" % args.TWITTER_EXPORT_LOCATION)
        graileater.parse_twitter_export(args.TWITTER_EXPORT_LOCATION)

    if args.TWEETS_LOCATION is not None:
        print("Download Twitter Data Mode Detected\n\t[value is \"%s\"]" % args.TWEETS_LOCATION)
        download_json_data(args.TWEETS_LOCATION, is_dry_run)


def close_all_open_handles(file_set):
    for filename in file_set:
        if not file_set[filename].closed:
            # print("  closing %s" % filename)
            file_set[filename].close()


def extract_media_links_to_file(tweet, file):

    # sometimes the urls are duplicates, so using a set lets us keeps only one copy
    media_urls = set()

    # media extraction done via modified version of DocNow/Twarc/utils/media_urls.py (file was licened as MIT)
    if 'media' in tweet['entities']:
        for media in tweet['entities']['media']:
            if media['type'] == 'photo':
                media_urls.add(media['media_url_https'])

    if 'extended_entities' in tweet and 'media' in tweet['extended_entities']:
        for media in tweet['extended_entities']['media']:

            if media['type'] == 'animated_gif':
                media_urls.add(media['media_url_https'])

            if 'video_info' in media:
                for v in media['video_info']['variants']:
                    media_urls.add(v['url'])

    for url in media_urls:
        file.write("%s\n" % url)

    return len(media_urls)


def get_filehandle(filepool, pool, filename):

    # TODO the file pool might be a good candidate for a LRU

    try:
        return maybe_open_a_file(filepool[pool], filename)
    except OSError as e:
        if e.errno == 24:  # max file descriptors
            print("    Max open files reached while trying to open %s,\n      closing open files (may take a moment)" % filename)
            for open_pool in filepool:
                close_all_open_handles(filepool[open_pool])
            return maybe_open_a_file(filepool[pool], filename)
        else:
            raise


def create_new_filehandle(filepool, pool, filename):
    filehandle = get_filehandle(filepool, pool, filename)
    filehandle.truncate(0)
    filehandle.flush()
    return filehandle


def maybe_open_a_file(file_set, filename):
    try:
        # see if a file is not yet opened
        if filename in file_set:
            if file_set[filename].closed:
                # if so, open it
                file_set[filename] = open(filename, 'a')
            else:
                # file is already open, so do nothing
                pass
        else:
            # filename isn't in set, so it needs to be made
            file_set[filename] = open(filename, 'a')
        # return the opened file
        return file_set[filename]
    except:
        print("  Was unable to open %s" % filename)
        raise


def download_user_details(user_ids):

    print("  creating /user_details/ directory")
    if not os.path.exists('user_details'):
        os.makedirs('user_details')

    user_details = dict()
    user_id_all = set()
    user_id_json_map = dict()

    # gather all of the follower/following ids'
    print("gathering user details")
    for user_id in user_ids:

        user_id_all.add(str(user_id))

    #    print("  getting followers for %s" % (user_id,))
    #    follower_set = set()
    #    for follower_id in twarc.follower_ids(user_id):
    #        follower_set.add(str(follower_id))
    #
    #    print("  getting following/friends for %s" % (user_id,))
    #    following_set = set()
    #    for following_id in twarc.friend_ids(user_id):
    #        following_set.add(str(following_id))
    #
        user_details[str(user_id)] = dict()

    # perform a lookup to populate ids as json details
    print("  Looking up details for %s accounts" % len(user_id_all))
    for user_details_json in twarc.user_lookup(ids=list(user_id_all), id_type="user_id"):
        user_id_json_map[str(user_details_json['id_str'])] = user_details_json

    # TODO: the logic here is odd

    print("  Exporting Data")
    all_user_details_filename = "user_details/all_user_details.jsonl"
    with open(all_user_details_filename, 'a', encoding="utf-8-sig") as master_details_file:
        master_details_file.truncate(0)

        for user_details_id in user_id_json_map:

            user_details_json = user_id_json_map[user_details_id]

            # store the tweet json to the master file so we can look up on a per-tweet basis
            master_details_file.write(str(user_details_json))
            master_details_file.write('\n')

            # if the user is someone we've looked up follower/following for, then store associated metadata in a subfolder
            if str(user_details_json["id_str"]) in user_details:

                print("    Storing details for %s" % user_details_json["screen_name"])
                # writing to the file system? make sure the shit isn't going to overwrite /etc/passwd
                unsafe_username = user_details_json["screen_name"]
                safe_username = ascii_pattern.sub('', str(unsafe_username))

                unsafe_userid = user_details_json["id_str"]
                safe_userid = ascii_pattern.sub('', str(unsafe_userid))

                filename_pre = "%s_%s" % (safe_userid, safe_username)
                #user_details_following_filename = "user_details/%s/%s_user_details_following.jsonl" % (filename_pre, filename_pre)
                #user_details_followers_filename = "user_details/%s/%s_user_details_followers.jsonl" % (filename_pre, filename_pre)
                user_details_self_filename = "user_details/%s/%s_user_details_self.jsonl" % (filename_pre, filename_pre)

                if not os.path.exists('user_details/'+filename_pre):
                    os.makedirs('user_details/' + filename_pre)

                print("    Storing self")
                with open(user_details_self_filename, 'a', encoding="utf-8-sig") as details_file:
                    details_file.truncate(0)
                    details_file.write(str(user_details_json))
                    details_file.write('\n')
                    details_file.close()

                #print("      Storing %s following" % len(user_details[str(safe_userid)]['following_ids']))
                # with open(user_details_following_filename, 'a', encoding="utf-8-sig") as details_file:
                #    details_file.truncate(0)
                #    for user_id in user_details[str(safe_userid)]['following_ids']:
                #        details_file.write(str(user_id_json_map[user_id]))
                #        details_file.write('\n')
                #    details_file.close()

                #print("      Storing %s followers" % len(user_details[str(safe_userid)]['follower_ids']))
                # with open(user_details_followers_filename, 'a', encoding="utf-8-sig") as details_file:
                #    details_file.truncate(0)
                #    for user_id in user_details[str(safe_userid)]['follower_ids']:
                #        details_file.write(str(user_id_json_map[user_id]))
                #        details_file.write('\n')
                #    details_file.close()

        master_details_file.close()


def download_json_data(TWEETS_LOCATION, is_dry_run):

    # We use a dict to store filenames of users we write to
    # this lets us track all the open files to close them later
    # it also gives us a way to check if a file is open already or not
    # this avoids continuously running the open() command, speading this up a bit for large tweet collections
    filepool = dict()
    filepool["tweet_files"] = dict()
    filepool["media_url_files"] = dict()

    print("Beginning twarc tweet download")
    try:

        print("  creating /tweet_metadata/ directory")
        if not os.path.exists('tweet_metadata'):
            os.makedirs('tweet_metadata')

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

        user_ids = set()

        for tweet in twarc.hydrate(open(TWEETS_LOCATION)):
            tweet_json = json.dumps(tweet)

            # writing to the file system? make sure the shit isn't going to overwrite /etc/passwd
            unsafe_username = tweet["user"]["screen_name"]
            safe_username = ascii_pattern.sub('', str(unsafe_username))

            unsafe_userid = tweet["user"]["id"]
            safe_userid = ascii_pattern.sub('', str(unsafe_userid))

            # store user ID for lookup later
            user_ids.add(safe_userid)

            # generate a filename programatically
            filename_pre = "%s_%s" % (safe_userid, safe_username)
            tweet_data_filename = "tweets/%s/%s_twarc_output.jsonl" % (filename_pre, filename_pre)
            media_urls_filename = "media/%s/%s_media_to_download.txt" % (filename_pre, filename_pre)

            if tweet_data_filename not in filepool["tweet_files"]:
                user_count += 1

                if not os.path.exists('tweets/'+filename_pre):
                    os.makedirs('tweets/' + filename_pre)

                if not os.path.exists('media/'+filename_pre):
                    os.makedirs('media/' + filename_pre)

                create_new_filehandle(filepool, "tweet_files", tweet_data_filename)
                create_new_filehandle(filepool, "media_url_files", media_urls_filename)

                # print("  creating file for %s (%s)" % (tweet["user"]["screen_name"], tweet["user"]["id"]))

            tweet_file = get_filehandle(filepool, "tweet_files", tweet_data_filename)
            media_url_file = get_filehandle(filepool, "media_url_files", media_urls_filename)

            # store the json we got from the tweet
            tweet_file.write("%s\n" % tweet_json)
            tweet_count += 1

            media_count += extract_media_links_to_file(tweet, media_url_file)

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
        close_all_open_handles(filepool["tweet_files"])
        close_all_open_handles(filepool["media_url_files"])

    print("Looking up User Details / Followers / Following")
    download_user_details(user_ids)


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
