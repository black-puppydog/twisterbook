from __future__ import absolute_import
from bitcoinrpc.authproxy import AuthServiceProxy
import pymysql
import simplejson
from LoginData import *
from TwisterScraper.celery import app

__author__ = 'daan'

# todo: once we understand celery this should instead call the actual RpcScraper and do actual work!


@app.task
def dummy_scraper_task(username, userid, last_k):
    scraper = RpcScraper()
    scraper.refresh_user(username, userid, last_k)


class RpcScraper:
    def __init__(self, url="http://user:pwd@127.0.0.1:28332"):
        self.url = url
        self.twister = AuthServiceProxy(self.url)

    def refresh_user(self, username, userid, last_k):
        profile = self.get_full_user_profile(username)
        new_posts = self.get_user_posts(username, last_k+1)

        self.write_to_db(username, userid, last_k, profile, new_posts)

    def get_user_posts(self, username, min_k):
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
            last_referenced_k = latest_k-1

        while last_referenced_k >= min_k:

            finished = True

            # given a last_referenced_k that we believe to hold a post...
            for k in range(last_referenced_k, min_k-1, -1):

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

        return results


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
        result['following'] = list(result['following'])

        return result

    def write_to_db(self, username, userid, last_k, profile, new_posts):

        conn = pymysql.connect(
            host=MYSQL_HOSTNAME,
            port=MYSQL_PORT, user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            db=MYSQL_DATABASE,
            charset="utf8")

        cursor = conn.cursor()

        if new_posts:
            new_k = max([p['k'] for p in new_posts])
        else:
            new_k = last_k
        cursor.execute("UPDATE users set last_indexed_time=NOW(), last_indexed_k=%s, json=%s WHERE id=%s",
                       (new_k, simplejson.dumps(profile, encoding='utf8', use_decimal=True), userid))

        for post in new_posts:

            k = post['k']

            post_type = 'normal'
            if 'rt' in post:
                post_type = 'rt'
            elif 'reply' in post:
                post_type = 'reply'

            time = post['time']

            if post_type == 'rt':
                msg = post['rt']['msg']
            else:
                msg = post['msg']

            parent_post_username, parent_post_k = 'NULL', 'NULL'
            if post_type != 'normal':
                parent_post_username = post[post_type]['n']
                parent_post_k = post[post_type]['k']

            json = simplejson.dumps(post, encoding='utf8', use_decimal=True)

            cursor.execute(
                """INSERT IGNORE
                  INTO posts(
                  userid, k, post_type, time,
                  msg, parent_post_username, parent_post_k, json)
                  VALUES (%s,%s,%s,FROM_UNIXTIME(%s),%s,%s,%s,%s);""",
                (userid, k, post_type, time,
                  msg, parent_post_username, parent_post_k, json)
            )

        conn.commit()
        conn.close()

        print("Indexed %i new posts for user %s" % (len(new_posts), username))
