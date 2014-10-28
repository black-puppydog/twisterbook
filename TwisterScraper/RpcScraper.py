from __future__ import absolute_import
from datetime import datetime
from bitcoinrpc.authproxy import AuthServiceProxy
from TwisterScraper.celery import app

__author__ = 'daan'

# todo: once we understand celery this should instead call the actual RpcScraper and do actual work!


@app.task
def dummy_scraper_task(username, last_k):
    scraper = RpcScraper()
    return scraper.refresh_user(username, last_k)


class RpcScraper:
    def __init__(self, url="http://user:pwd@127.0.0.1:28332"):
        self.url = url
        self.twister = AuthServiceProxy(self.url)

    def refresh_user(self, username, last_k):
        profile = self.get_full_user_profile(username)
        new_posts = self.get_user_posts(username, last_k+1)

        return profile, new_posts

    def get_user_posts(self, username, min_k):
        """gets all posts from a user for which k >= min_k"""

        # get only the last post by the user to see the last k
        d = self.twister.getposts(1, [{'username': username}])

        # user has made no posts or the torrent cannot be reached.
        # cannot really do anything about that atm.
        if len(d) == 0:
            return []

        last_post = d[0]

        # there are no posts we don't already know or that we care about atm
        if last_post['k'] < min_k:
            return []
        # we were lucky: there was exactly one new post
        if last_post['k'] == min_k:
            return [last_post]

        # now we know the last k, so we can upper-bound the number of posts we need to retrieve
        d = self.twister.getposts(last_post['k'] - min_k + 1, [{'username': username}])
        result = [post for post in d if post['k'] >= min_k]
        return result


    def get_full_user_profile(self, u):

        result = {'username': u}

        try:
            print("getting profile for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "profile", "s")

        if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
            for key in d[0]["p"]["v"]:
                result[key] = d[0]["p"]["v"][key]

        try:
            print("getting avatar for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        d = self.twister.dhtget(u, "avatar", "s")
        if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
            result['avatar'] = d[0]["p"]["v"]

        try:
            print("getting following1 for %s ..." % u)
        except UnicodeEncodeError:
            print("cannot print user info since Unicode error...")
        result["following"] = set()

        # following is paged, so we try until one of the pages is empty.
        followingPage = 1
        while True:
            d = self.twister.dhtget(u, "following%i" % followingPage, "s")
            if len(d) == 1 and "p" in d[0] and "v" in d[0]["p"]:
                result['following'] = result["following"].union(d[0]["p"]["v"])
            else:
                break
        result['following'] = list(result['following'])
        result["updated_time"] = datetime.now()

