from __future__ import absolute_import
from datetime import datetime
import re
from bitcoinrpc.authproxy import AuthServiceProxy
import simplejson
from TwisterScraper.celery import app
from cassandra.cluster import Cluster
from cassandra_queries import *

# region setup logging
import logging

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)
# endregion

__author__ = 'daan'

# todo: once we understand celery this should instead call the actual RpcScraper and do actual work!


@app.task
def dummy_scraper_task(username, last_k):
    scraper = RpcScraper()
    scraper.refresh_user(username, last_k)


class RpcScraper:
    def __init__(self, url="http://user:pwd@127.0.0.1:28332", cassy_nodes=['127.0.0.1']):
        self.url = url
        self.twister = AuthServiceProxy(self.url)

        log.debug("Connect to cassandra...")
        cluster = Cluster(cassy_nodes)
        self.cassy = cluster.connect()
        self.cassy.set_keyspace(KEYSPACE)

        # prepare insert queries
        self.insert_post = self.cassy.prepare(CQL_INSERT_POST)
        self.insert_reply = self.cassy.prepare(CQL_INSERT_REPLY)
        self.insert_user = self.cassy.prepare(CQL_INSERT_USER)
        self.insert_new_k = self.cassy.prepare(CQL_INSERT_NEW_K)
        self.insert_retransmit = self.cassy.prepare(CQL_INSERT_RETRANSMIT)
        self.insert_hashtag = self.cassy.prepare(CQL_INSERT_HASHTAG)
        self.insert_mention = self.cassy.prepare(CQL_INSERT_MENTION)

    def refresh_user(self, username, last_k, posts_only=False):
        if posts_only:
            profile = None
        else:
            profile = self.get_full_user_profile(username)
        new_posts = self.get_user_posts_greater_than(username, last_k + 1)

        self.write_to_db(username, last_k, profile, new_posts)

    def write_to_db(self, username, last_k, profile, new_posts):

        if not profile and not new_posts:
            return

        new_k = max([p['k'] for p in new_posts]) if new_posts else last_k

        # save posts first, only after that update the k value for the user
        for post in new_posts:
            self.save_post(post)

        if profile:
            self.save_user(username, new_k, profile)
        else:
            self.save_new_k(username, new_k)

        log.info("indexed %i new posts for user %s" % (len(new_posts), username))

    def save_post(self, json):
        username = json['n']
        k = json['k']
        lastk = json['lastk'] if 'lastk' in json else None
        (rt_user, rt_k) = (json['rt']['n'], json['rt']['k']) if 'rt' in json else (None, None)
        (reply_user, reply_k) = (json['reply']['n'], json['reply']['k']) if 'reply' in json else (None, None)
        time = json['time']
        msg = json['rt']['msg'] if 'rt' in json else json['msg']
        # json = simplejson.dumps(json, encoding='utf8', use_decimal=True) # todo: still needed?

        self.cassy.execute(self.insert_post,
                           (username, k, lastk, time, msg, rt_user, rt_k, reply_user, reply_k,
                            simplejson.dumps(json, encoding='utf8', use_decimal=True)))

        if 'rt' in json:
            self.cassy.execute(self.insert_retransmit, (rt_user, rt_k, username, k, time))

        if 'reply' in json:
            self.cassy.execute(self.insert_reply, (reply_user, reply_k, username, k, time))

        for tag in self.find_hashtags(msg):
            self.cassy.execute(self.insert_hashtag, (tag, username, k, time))

        for mentioned_user in self.find_mentions(msg):
            self.cassy.execute(self.insert_mention, (mentioned_user, username, k, time))

    def get_user_posts_greater_than(self, username, min_k):
        """gets all posts from a user for which k >= min_k"""

        # this should never happen, but just to be sure:
        if min_k < 0:
            raise ValueError("min_k crucially has to be non-negative!")

        # get the user's latest posting. this acts as an entry point to go backwards
        latest_status = self.twister.dhtget(username, 'status', 's', 2000)

        # if cannot even get the latest posting, then it makes little sense to keep trying
        if not latest_status:
            print('was unable to retrieve any post')
            return []

        # check out which number the last posting has
        latest_posting = latest_status[0]['p']['v']['userpost']
        latest_k = latest_posting['k']
        print("k=%i" % latest_k)

        # if it is too old, we are already done!
        if latest_k < min_k:
            return []
        results = [latest_posting]

        # now start going back in time as the posts tell us
        # start from the k referenced in the latest post, defaulting to last_k-1
        if 'lastk' in latest_posting:
            last_referenced_k = latest_posting['lastk']
        else:
            last_referenced_k = latest_k - 1

        while last_referenced_k >= min_k:

            finished = True

            # given a last_referenced_k that we believe to hold a post...
            for k in range(last_referenced_k, min_k - 1, -1):

                # ... get that post. give some extra time if we really expect this to be successful
                posting_k = self.twister.dhtget(username, 'post%i' % k, 's', 2000 if k == last_referenced_k else 1000)

                # and if it exists, break the loop, using the explicitely referenced lastk instead
                if posting_k:
                    print("k=%i" % k)
                    results.append(posting_k[0]['p']['v']['userpost'])
                    if ['lastk'] in posting_k:
                        last_referenced_k = posting_k['lastk']
                    else:
                        # just in case we don't have a lastk, default to decrementing by one again
                        last_referenced_k = k - 1

                    # got a new k, so we need to keep going
                    finished = False
                    break
                else:
                    print("failed to get k=%i, being more impatient now" % k)

            # this is only true if we finished that for loop, i.e. if we tried all interesting k's
            if finished:
                break

        return list(results)

    def save_user(self, username, new_k, json, time=None):

        location = json['location'] if 'location' in json else None
        fullname = json['fullname'] if 'fullname' in json else None
        bio = json['bio'] if 'bio' in json else None
        url = json['url'] if 'url' in json else None
        avatar_b64 = json['avatar'] if 'avatar' in json else None
        following = json['following'] if 'following' in json else []
        json = simplejson.dumps(json, encoding='utf8', use_decimal=True) if json else '{}'

        self.cassy.execute(self.insert_user,
                           (username,
                            fullname,
                            location,
                            bio,
                            url,
                            avatar_b64,
                            following,
                            new_k,
                            datetime.utcnow() if not time else time,
                            json))

    def save_new_k(self, username, new_k, time=None):
        self.cassy.execute(self.insert_new_k,
                           (username,
                            new_k,
                            datetime.utcnow() if not time else time))

    def get_full_user_profile(self, u):

        result = {'username': u}

        try:
            print("getting profile for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "profile", "s", 2000)

        if len(d) == 1 and 'p' in d[0] and 'v' in d[0]["p"]:
            for key in d[0]["p"]["v"]:
                result[key] = d[0]["p"]["v"][key]

        try:
            print("getting avatar for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "avatar", "s", 2000)
        if len(d) == 1 and 'p' in d[0] and 'v' in d[0]["p"]:
            result['avatar'] = d[0]["p"]["v"]

        try:
            print("getting followings for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        result["following"] = set()

        # following is paged, so we try until one of the pages is empty.
        followingPage = 1
        while True:
            d = self.twister.dhtget(u, "following%i" % followingPage, "s", 2000)
            if len(d) == 1 and "p" in d[0] and "v" in d[0]["p"]:
                result['following'] = result["following"].union(d[0]["p"]["v"])
                print("got following%i" % followingPage)
                followingPage += 1
            else:
                break

        # if we use the set like this we cannot serialize to json
        result['following'] = list(result['following'])

        return result

    def find_hashtags(self, a):
        # todo: if this does not work properly, re-index all posts from their json
        # use this: https://stackoverflow.com/questions/8451846

        # find all occurences of the hash symbols (one normal, one weird unicode stuff)
        hts=[m.start() for m in re.finditer('[#＃]', a)]

        # split message into non-overlapping substrings starting with hashes
        substrs_idx = zip(hts, hts[1:]+[len(a)])
        substrs = [a[i:j] for i,j in substrs_idx]

        # split the potential hashtags again at the characters the html client also uses
        res = [re.split('[ \n\t.,:/?!;\'\"()\[\]{}*@]', s)[0][1:] for s in substrs]

        return [word for word in res if word]

    def find_mentions(self, msg):
        # todo: if this does not work properly, re-index all posts from their json
        # use this https://stackoverflow.com/questions/8451846
        return [word[1:] for word in re.findall('@[a-z0-9_]+', msg)]
