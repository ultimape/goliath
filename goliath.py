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

from eatgrail import eatgrail as graileater


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


# Load Journal
    journal = load_journal(args.JOURNAL_LOCATION)


# Populate Queues from Journal
    queues = dict()

    queues['input_tweets'] = list()
    queues['download_queue'] = list()
    queues['ingest'] = dict()
    queues['ingest']['tweets'] = list()
    queues['ingest']['retweets'] = list()
    queues['ingest']['quote_tweets'] = list()

    queues['input_tweets'].append("dog")
    queues['download_queue'].append("cat")
    queues['ingest']['tweets'].append("rat")
    queues['ingest']['retweets'].append("bat")
    queues['ingest']['quote_tweets'].append("dat")

    # print(json.dumps(queues))
    # print(queues)


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


# load an existing journal to restore spider state
def load_journal(journal_location):
    #
    return "blarg"


# save spider state to journal
def save_journal(journal_location):
    #
    pass

# add/update state to journal


def update_journal(tweet_id, state, value):
    #
    pass


if __name__ == "__main__":
    main()
