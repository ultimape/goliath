# Goliath BirdEater

## A birdsite spider; For backing up your external brain.

**Eats backups, poops tweets.**

----

The Goliath bird-eating spider;

> "Despite its name, it is rare for the Goliath birdeater to actually prey on birds; [...]  
> it is not uncommon for this species to kill and consume a variety of insects and small terrestrial vertebrates."  
> [(via Wikipedia)](https://en.wikipedia.org/wiki/Goliath_birdeater)

Future Site: https://murmurology.wovensoup.com

# About

***This is a work in progress.***

Goliath BirdEater is intended to be a tool to get a more complete export of your Twitter Archive.

Twitter released their archive functionality [back in 2012](https://blog.twitter.com/official/en_us/a/2012/your-Twitter-archive.html) and it hasn't really been updated since. A number of outstanding deficiencies still exist, many outlined in this blog [post from 2013](https://shkspr.mobi/blog/2013/02/deficiencies-in-the-Twitter-archive/) a mere ~3 months after the feature rollout. It has been nearly 6 years and there are no signs that the Archive is going to be improved.

As a number of people are seeking to leave the platform for greener pasture (*\*cough\** Mastodon *\*cough\**), this completely broken archive system is *unacceptable*.

We seek to fix that.

**Problems with the Archive Include, but are not limited to:**
* Images are not part of the archive, but are still stored on Twitter's image hosting service.
* If you delete the original tweet off of Twitter, the associated images are also removed.
* Many images in the backup itself are not even linked properly to begin with.
* You are unable to view tweets as threads, even your own.
* You are unable to view replies, even your own.
* You are unable to view Polls, or Moments.
* Quotetweets aren't captured as part of the archive at all.
* Search functionality is severely limited.

It is possible to take these archives and transform them into an up-to-date and hopefully more complete archive.

The goal for this project is to automate this entire process. The most immediate goal is to build something to automate the downloading of all of your images. The longterm aim is to provide a fluid offline interface for interacting with your tweets/threads based on the data from the Twitter API.

----

## How to Use

### Big Picture

The current workflow is to parse through the Twitter Archive to harvest relevant tweet IDs, storing them in as newline separated files.

They look something like this:

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

We can take these IDs and use [DocNow/twarc](https://github.com/DocNow/twarc) to 'rehydrate' the tweets directly from the Twitter API.

After rehydrating, one of twarc's utilities can extract all the media urls to a file. These can then be fed into a bulk-download utility such as wget.

> *Note*: Twarc requires using the Twitter Developer API, and effectively running a "Twitter App". While you will always be able to use your own credentials, a longterm goal for Goliath to provide access to this tool as a standalone service, avoiding this requirement.


### Parsing the archive

Under the `eatgrail` directory within this repository is a python module called `eatgrail.py`. This module can be ran directly as a script, told about your Twitter Archive, and will harvest tweet IDs for you.

Once you have your Twitter Archive you can run eatgrail.py from a commandline/console/terminal as follows:

`$ ./eatgrail/eatgrail.py -extract ./[$PATH_TO_ARCHIVE_ZIP]`

Be sure to replace `[$PATH_TO_ARCHIVE_ZIP]` with the directory and filename of your archive

This script depends on the orginal structure of the archive, and will look for the file `data/js/tweets/tweet_index.js` to begin reading in tweets, exporting tweet IDs as it goes.

Tweet IDs will be exported to a couple of files matching the pattern `backup_export_[tweettype]_ids.txt`. They will be stored into whatever your console/terminal's current working dirctory is when you run the script.

> *Note*: you can also point to an extracted archive and it will look for those files within it directly instead of inside of the Zip file.

### Working with ID files

At the moment, tweet IDs are saved to different files depending on what kind of tweet they are.

Due to the way tweets, retweets, and quotetweets work (and how they are encoded in the archive), it might seem a little strange.

**When you retweet a tweet**: Internally, you are actually creating your own tweet that encapsulates the other tweet with an "RT @username " appended to the front. This is due to the historical nature of how Twitter implemented the RT'ing functionality into their service. the "RT @username " thing was originally more of a social convention. Twitter then adopted this as a feature in their interface, hiding the RT to maintain backwards compatibility for older clients. I am not certain about older tweets, but in all RTs (since that was implemented) also contain the ID of the originla tweet being Retweeted. I've split these two IDs into buckets. The 'retweet_ids' are your "RT @username " tweets, and the "retweeted_ids" are the IDs of the original tweet being retweeted. *It is important to capture both*, because the retweet_ids tell us when YOU retweeted it, and the retweeted_ids contain the all the retweeted content.

**When you quotetweet a tweet**: The Twitter archvie does not currently encode anything about the tweet being quoted. Structurally it is just treated as a link to another tweet in the vein of `https://twitter.com/user/status/[TWEET_ID]`. This is one of the deficiencies in the archive data. I've instructed the script to look for these URLs and read out the embedded Tweet IDs. This is to ensure that all the relevant tweets and context are being captured to match the current day behavior of Twitter's UI. Due to the nature of of the embedded URLs, the script can not distinguish which of the URLs was intended to be the quoted tweet, so it will grab all links to Twitter statuses.

**I do not currently handle moments or polls**: I am not even sure if/how they appear in the Twitter Archive. Feel free to make pull-requests accounting for them.

### Contents of ID files

The files generated by eatgrail.py will appear in your current working directly:

`backup_export_tweet_ids.txt` contains all the IDs tweets you've personally tweeted out.  
`backup_export_retweet_ids.txt` contains all the IDs of your tweet IDS associated with a retweet.  
`backup_export_retweeted_ids.txt` contains all the IDs of actual retweeted tweet.  
`backup_export_quotetweet_ids.txt` contains all the IDs of any tweets you've linked ('quoted') to in a tweet.  
`backup_export_replyto_ids.txt` contains all the IDs of a tweet that is list as having been replied to.  
`backup_export_all_ids.txt` contains every ID of all the other files (mostly for convenience factor).  

> *Note*: Tweet IDs are "deduplicated". So, say for example you have a tweetstorm where you've replied to and often quotetweet yourself. Since these tweet IDs already show up under `...tweet_ids.txt`, they will not be present within the `...retweeted_ids.txt`, `...quotetweet_ids.txt`, or `...replyto_ids.txt` files. However `...retweet_id.txt` will still contain the proxy entries that retweeting generates (needed for recreating a feed).


### Twarc Workflow

To work with your own exports, it is highly recommend you read thru [DocNow/twarc](https://github.com/DocNow/twarc)'s excelent documentation. It will help you setup and configure your environment as well as introduce you to how the command line versionf twarc operates.

**Eventually twarc baked into the main goliath.py to automate it all**, but it was important to *release this tool in it's current form* for people to tinker with.

But for the adventuerous, here's the commands I personaly run to download all the media/images. They have been tested using gitbash and a flavor of linux.

- Rehydrating all the tweets:  
`twarc hydrate ./backup_export_tweet_ids.txt > hydrated_tweets.jsonl`  
`twarc hydrate ./backup_export_retweet_ids.txt > hydrated_retweets.jsonl`  
`twarc hydrate ./backup_export_retweeted_ids.txt > hydrated_retweeted_tweets.jsonl`  
`twarc hydrate ./backup_export_quotetweet_ids.txt > hydrated_quotetweets.jsonl`  
`twarc hydrate ./backup_export_replyto_ids.txt > hydrated_replyto.jsonl`  

- Combining them together:  
`cat hydrated_tweets.jsonl hydrated_retweets.jsonl hydrated_retweeted_tweets.jsonl hydrated_quotetweets.jsonl hydrated_replyto.jsonl > master_hydrated_tweets.jsonl`

- Sorting by ID:  
`./twarc/utils/sort_by_id.py master_hydrated_tweets.jsonl > master_hydrated_tweets_sorted.jsonl`

- Deduplicating:  
`./twarc/utils/deduplicate.py master_hydrated_tweets_sorted.jsonl > master_hydrated_tweets_sorted_deduped.jsonl`

- Using the 'unshortening service' to expand stuff like bit.ly links (optional):  
`docker run -p 3000:3000 docnow/unshrtn`  
`./twarc/utils/unshrtn.py master_hydrated_tweets_sorted_deduped.jsonl > master_hydrated_tweets_sorted_deduped_unshrtned.jsonl`  

- Gather Media Urls from ***MY*** own tweets (optional):  
`./twarc/utils/media_urls.py hydrated_tweets.jsonl > media_urls_my_tweets.txt`

- Gather Media URLs from ***ALL*** tweets:
`./twarc/utils/media_urls.py master_hydrated_tweets_sorted_deduped_unshrtned.jsonl > media_urls_all_tweets.txt`

- Use WGET to download ***MY*** media urls (optional):  
`mkdir -p tweets/ultimape/images`  
`wget -P ./tweets/ultimape/images/ -i ./media_urls_tweets.txt --wait=5 --random-wait --no-clobber --adjust-extension`

- Use WGET to download ***ALL*** media urls:  
`mkdir -p tweets/images`  
`wget -P ./tweets/images/ -i ./media_urls_tweets.txt --wait=5 --random-wait --no-clobber --adjust-extension`


----


## Future Goals, Milestones, and TODO

This is a rough guideline of the direction Goliath is headed.  
It is an evolving list. *Not promises*.  

**Manual Exploration:**  
*Stuff that has been figured out how to do manually.*  
- [x] Extract tweet IDs
- [x] Script to comb thru json for relevant tweet IDs
- [x] Use twarc to download the real data from the Twitter API / correct images links 
- [x] Extract correct media file urls
- [x] Download images
- [ ] Extract user avatars 

**Programatic features:**  
*Stuff that needs written code to do.*  
- [x] A tool to scavange for tweet IDs in Twitter Archive
  - [x] Must gather tweet IDs
  - [x] Must gather retweet IDs (older RT @username bla bla)
  - [x] Must gather retweeted tweet IDs 
  - [x] Must gather quotetweet IDs (technically just links back to twitter.com/)
  - [x] Must gather "in reply to" (for recreating context)
  - [x] Handle deduplication of IDs
- [x] Consume archive .zip files directly
- [ ] End to End automation.
  - [ ] Insert backup => output complete bundle of jsonl w/ images.
  - [ ] Generate a standalone script to download images. 
  - [ ] Export as Zip Archive
- [ ] Error checking / Recovery
  - [ ] Deleted tweets
  - [ ] Temporarily inaccessible tweets
  - [ ] Periodic reattempts
- [ ] Incremental support (feed in new backup export, reuse / update old data)
- [ ] Monitor tweet stream for continuous backup
- [ ] Converter to generate Mastodon flavored ActivityPub compatible json

**Features for widespread use**  
*Stuff that would help others use this easier.*  
- [ ] Turn into an opensource self-hosted / docker service
- [ ] Provide self-service platform online (to remove the harsh requirement of getting an api KEY)
  - [ ] A way to pay for expensive features at cost? (donations? tips? funding drives?)
  - [ ] Build a script for users to run on their end to avoid downloading bulk images
  - [ ] Lightweight
  - [ ] Minimize Risk Profile (super important)
  - [ ] No storing of user identifiable info
  - [ ] No storing of tweet data beyond nessiary to offer download, delete after done
- [ ] A standalone offline backup viewer for Mastodon flavored ActivityPub
  - [ ] Must have thread support!
  - [ ] Extensive Search Functionality
- [ ] Safe ways to access tweets that aren't part of your backup, but without requiring access to Twitter
  - [ ] Encrypted Storage
    - [ ] Optionally store backups in Keybase's filesystem - providing public acessible / private shared access(?)
  - [ ] Reference Twitter/Mastodon API's follower/following lists
  - [ ] Portal to authorize / bootstrap mutual sharing of backups (like https://bridge.joinmastodon.org/ ?)
  - [ ] Share / renknit tweets over DAT:// or other decentralized service?
  - [ ] IPFS / Torrent support
  - [ ] Facility for voluntarily submitting Tweet corpuses to archive.org?
