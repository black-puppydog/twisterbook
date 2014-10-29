from __future__ import absolute_import
from datetime import datetime
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

        latest_status = self.twister.dhtget(username, 'status', 's')
        if not latest_status:
            print('was unable to retrieve any post')
            return []

        latest_posting = latest_status[0]['p']['v']['userpost']
        latest_k = latest_posting['k']
        print("k=%i" % latest_k)

        if latest_k < min_k:
            return []

        results = [latest_posting]
        for k in range(latest_k-1, min_k-1, -1):
            posting_k = self.twister.dhtget(username, 'post%i' % k, 's')
            if posting_k:
                print("k=%i" % k)
                results.append(posting_k[0]['p']['v']['userpost'])

        return results


    def get_full_user_profile(self, u):

        result = {'username': u}

        try:
            print("getting profile for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "profile", "s")

        if len(d) == 1 and 'p' in d[0] and 'v' in d[0]["p"]:
            for key in d[0]["p"]["v"]:
                result[key] = d[0]["p"]["v"][key]

        try:
            print("getting avatar for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "avatar", "s")
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
            d = self.twister.dhtget(u, "following%i" % followingPage, "s")
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
