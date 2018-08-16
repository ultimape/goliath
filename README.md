# Goliath Birdeater

## A birdsite spider; For backing up your external brain.

**Eats backups, shits tweets.**

----

The Goliath bird-eating spider;

> "Despite its name, it is rare for the Goliath birdeater to actually prey on birds; [...]  
> it is not uncommon for this species to kill and consume a variety of insects and small terrestrial vertebrates."  
> [(via Wikipedia)](https://en.wikipedia.org/wiki/Goliath_birdeater)

Future Site: https://murmurology.wovensoup.com

# About

***This is a work in progress.***

It is intended to be a tool to get a more complete export of your twitter archive.

From what I can tell, Twitter released the archive functionality [back in 2012](https://blog.twitter.com/official/en_us/a/2012/your-twitter-archive.html) and it hasn't really been updated since. A number of outstanding deficiencies still exist, many outlined in this blog [post from 2013](https://shkspr.mobi/blog/2013/02/deficiencies-in-the-twitter-archive/) a mere ~3 months after the feature rollout.

As a number of people are seeking to leave this platform for greener pastures (myself included), this completely broken archive system is *unacceptable*. I seek to fix that.

**Problems with the Archive Include, but are not limited to:**
* Images are not part of the archive, but are still stored on twitter's image hosting service.
* If you delete the original tweet off of Twitter, the associated images are also removed.
* Many images in the backup itself are not even linked properly to begin with.
* You are unable to view tweets as threads, even your own.
* You are unable to view replies, even your own.
* You are unable to view 
* Quotetweets aren't captured as part of the archive at all.
* Search functionality is severely limited.

Under the *Big Picture* section below, I describe the current workflow I am using for myself.

My goal for this project is to automate this entire process. I aim to provide a more fluid and complete offline interface for interacting with your tweets/threads based on the data from the twitter API.

----

## How to Use

### Big Picture

My current workflow is to parse through the twitter archive and harvest relevant tweet IDs, storing them in as newline separated files.

the look something like this:

```
9134308873956xxxx
10012628829176xxxxx
100849193564291xxxxx
10084900989276xxxxx
10040143094317xxxxx
10023544410587xxxxx
10087770597228xxxxx
10100033655882xxxxx
10123091526711xxxxx
10133490981230xxxxx
10157128656412xxxxx
10161879035028xxxxx
10166529826063xxxxx
```

I then take these IDs and use [DocNow/twarc](https://github.com/DocNow/twarc) via the command line to 'rehydrate' the tweets directly from the twitter API.

Note: This requires you to sign up for the Twitter Developer API and generate an Authorized user token associated with the app. In the future my intention is to provide access to this tool as a standalone service.

After rehydrating, I use one of twarc's utilities to extract all the media urls to a file, which I then download using wget.

### Parsing the archive

Under the `eatgrail` directory, is a python module called `eatgrail.py` that can be ran directly as a script. This module can be told about to your twitter acrchive directory, and it will harvest tweet IDs for you.

One you have your twitter archive, extract/unzip it. Then you can run eatgrail.py from a commandline/console/terminal as follows:

`$ ./eatgrail/eatgrail.py -extract ./[$PATH_TO_ROOT_OF_ARCHIVE]`

Be sure to replace `[$PATH_TO_ROOT_OF_ARCHIVE]` with the directory of your archive

The script depends on the orginal structure of the acrhive, and will look for the file `[$PATH_TO_ROOT_OF_ARCHIVE]/data/js/tweets/tweet_index.js` and begin reading in tweets, exporting tweet IDs as it goes.

Tweet IDs will be exported/saved to a couple of files with a `.txt` extension, into whatever your console/terminal's current working dirctor is.

### Working with ID files

At the moment, tweet IDs are saved to four different files depending on what kind of tweet they are.

Due to the way tweets, retweets, and quotetweets work (and how they are encoded in the archive), it might seem a little strange.

**When you retweet a tweet**: Internally, you are actually creating your own tweet that encapsulates the other tweet with an "RT @username " appended to the front. This is due to the historical nature of how Twitter implemented the RT'ing functionality into their service. the "RT @username " thing was originally more of a social convention. Twitter then adopted this as a feature in their interface, hiding the RT to maintain backwards compatibility for older clients. I am not certain about older tweets, but in all RTs (since that was implemented) also contain the ID of the originla tweet being Retweeted. I've split these two IDs into buckets. The 'retweet_ids' are your "RT @username " tweets, and the "retweeted_ids" are the IDs of the original tweet being retweeted. *It is important to capture both*, because the retweet_ids tell us when YOU retweeted it, and the retweeted_ids contain the all the retweeted content.

**When you quotetweet a tweet**: The twitter archvie does not currently encode anything about the tweet being quoted. Structurally it is just treated as a link to another tweet in the vein of `https://twitter.com/user/status/[TWEET_ID]`. This is one of the deficiencies in the archive data. I've instructed the script to look for these URLs and read out the embedded Tweet IDs. This is to ensure that all the relevant tweets and context are being captured to match the current day behavior of Twitter's UI. Due to the nature of of the embedded URLs, the script can not distinguish which of the URLs was intended to be the quoted tweet, so it will grab all links to Twitter statuses.

*Note*: for both retweets and quotetweets, they may contain redundant IDs, as it will also store quotetweets or RT'ing you've done of yourself. At the moment the system does not cache or otherwise filter out the IDs.

**I do not currently handle moments**: I am not even sure if/how they appear in the twitter archive. Feel free to make pull-requests accounting for them.

The files generated by eatgrail.py will appear in your current working directly:

`backup_export_tweet_ids.txt` contains all the IDs tweets you've personally tweeted out.  
`backup_export_retweet_ids.txt` contains all the IDs of your tweet IDS associated with a retweet.  
`backup_export_retweeted_ids.txt` contains all the IDs of actual retweeted tweet.  
`backup_export_quotetweet_ids.txt` contains all the IDs of any tweets you've linked ('quoted') to in a tweet.

### Twarc Workflow

If you want to work with your own exports, I recommend reading thru [DocNow/twarc](https://github.com/DocNow/twarc)'s excelent documentation. It will help you setup and configure your environment as well. **I intend to have twarc baked into the main goliath.py to automate it all**, but I wanted to *release this tool in it's current form* for people to tinker with.

But for the adventuerous, here's the commands I run, in the order I run them, on my own computer. I have tested using gitbash and a flavor of linux.

Rehydrating all the tweets:  
`twarc hydrate ./backup_export_tweet_ids.txt > hydrated_tweets.jsonl`  
`twarc hydrate ./backup_export_retweet_ids.txt > hydrated_retweets.jsonl`  
`twarc hydrate ./backup_export_retweeted_ids.txt > hydrated_retweeted_tweets.jsonl`  
`twarc hydrate ./backup_export_quotetweet_ids.txt > hydrated_quotetweets.jsonl`  

Combining them together:  
`cat hydrated_tweets.jsonl hydrated_retweets.jsonl hydrated_retweeted_tweets.jsonl hydrated_quotetweets.jsonl > master_hydrated_tweets.jsonl`

Sorting by ID:  
`./twarc/utils/sort_by_id.py master_hydrated_tweets.jsonl > master_hydrated_tweets_sorted.jsonl`

Deduplicating:  
`./twarc/utils/deduplicate.py master_hydrated_tweets_sorted.jsonl > master_hydrated_tweets_sorted_deduped.jsonl`

Using the 'unshortening service' to expand stuff like bit.ly links (optional):  
`docker run -p 3000:3000 docnow/unshrtn`  
`./twarc/utils/unshrtn.py master_hydrated_tweets_sorted_deduped.jsonl > master_hydrated_tweets_sorted_deduped_unshrtned.jsonl`  

Gather Media Urls from ***MY*** own tweets (optional):  
`./twarc/utils/media_urls.py hydrated_tweets.jsonl > media_urls_my_tweets.txt`

Gather Media URLs from ***ALL*** tweets:
`./twarc/utils/media_urls.py master_hydrated_tweets_sorted_deduped_unshrtned.jsonl > media_urls_all_tweets.txt`

Use WGET to download ***MY*** media urls (optional):  
`mkdir -p tweets/ultimape/images`  
`wget -P ./tweets/ultimape/images/ -i ./media_urls_tweets.txt --wait=5 --random-wait --no-clobber --adjust-extension`

Use WGET to download ***ALL*** media urls:  
`mkdir -p tweets/images`  
`wget -P ./tweets/images/ -i ./media_urls_tweets.txt --wait=5 --random-wait --no-clobber --adjust-extension`

----

## Future Goals and Milestones

This is a rough guideline of what I'm thinking needs to get done. This is an evolving list. No promises.

**Manual Exploration:**  
*Stuff I've figured out how to do manually*  
- [x] export tweets 
- [x] extract
- [x] script to comb thru json for relevant tweet IDs
- [x] use twarc to download the real data from the twitter API / correct images links 
- [x] extract correct media file urls
- [ ] extract user avatars 
- [ ] download images

**Programatic features:**  
*Stuff I need to write code to do*  
- [x] Tool to scavange for tweet IDs in Twitter Archive
- [ ] Consume archive .zip files directly
- [ ] Incremental support (feed in new backup export, reuse / update old data)
- [ ] Monitor tweet stream for continuous backup
- [ ] End to End automation: Insert backup, output complete jsonl w/ images.
- [ ] Error checking / recovery
  - [ ] Deleted tweets
  - [ ] Temporarily inaccessible tweets
  - [ ] Periodic reattempts
- [ ] Convert to Mastodon flavored activitypub

**Features for widespread use**  
*stuff that would help others use this*  
- [ ] A offline backup viewer for Mastodon flavored activitypub, thread capable
- [ ] Offline search tool that consumes Mastodon flavored activitypub
- [ ] Turn into an opensource self-hosted / docker service
- [ ] Provide self-service platform online (remove need DEV api KEY)
  - [ ] A way to pay for expensive features at cost? (donations? tips? funding drives?)
  - [ ] Vuild a script for users to run on their end to avoid downloading bulk images
  - [ ] Lightweight
  - [ ] Minimize Risk Profile (super important)
  - [ ] No storing of user identifiable info
  - [ ] No storing of tweet data beyond nessiary to offer download, delete after done
- [ ] Safe way to access tweets that aren't part of your backup.
  - [ ] Encrypted Storage
    - [ ] Optionally store backups in keybase's filesystem - providing public acessible / private shared access(?)
  - [ ] Reference Twitter/Mastodon API's follower/following lists
  - [ ] Portal to authorize mutual sharing of backups (like https://bridge.joinmastodon.org/ ?)
  - [ ] Share / renknit tweets over DAT:// or other decentralized service?
  - [ ] Submitting tweet corpuses to archive.org?
