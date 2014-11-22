#! /usr/bin/env python

from cassandra.cluster import Cluster
from datetime import datetime, timedelta
import logging
from TwisterScraper.RpcScraper import dummy_scraper_task
from cassandra_queries import setup_cassandra_schema

__author__ = 'daan'


class Dispatcher:
    # todo: change the cache timeout to something more realistic?
    def __init__(self, cache_timeout=3600 * 24, rescrape_timeout=3600 * 21, cassy_nodes=['127.0.0.1']):
        """

        :param cache_timeout: how long to wait until we try to pull new posts from soneone we already have posts of
        :param rescrape_timeout: how long to wait until considering to scrape a profile again for which we failed to
        retrieve anything before. the 21h default aims at considering each profile at different times of day so that
        we don't miss someone just because we always try to pull their profile while they (and all their peers) are
        at work and not runnning twister. Not sure of that's actually an issue but why not...
        """
        self.rescrape_timeout = rescrape_timeout
        self.log = logging.getLogger()

        self.log.debug("Connect to cassandra...")
        cluster = Cluster(cassy_nodes)
        self.cassy = cluster.connect()
        setup_cassandra_schema(self.cassy)

        self.cache_timeout = timedelta(seconds=cache_timeout)
        self.due_query = self.cassy.prepare("SELECT username, highest_k_indexed, last_update_time FROM user LIMIT 1000000")

    def get_due_users(self):
        due_users = list(self.cassy.execute(self.due_query))
        print('retrieved %i users from db' % len(due_users))
        due_users = [row for row in due_users
                     if row[2]+self.cache_timeout < datetime.utcnow()]
        # due_users = [row for row in due_users
        #              if (row[1] >= 0 and row[2]+self.cache_timeout < datetime.utcnow())
        #              or row[2] < datetime.utcfromtimestamp(1000)]
        print('%i users due' % len(due_users))

        return due_users



    def dispatch_due_tasks(self):
        due_users = self.get_due_users()

        for row in due_users:
            # dummy_scraper_task(row[0], row[1], row[2])
            dummy_scraper_task.delay(row[0], row[1])


if __name__ == '__main__':
    dispatcher = Dispatcher()
    dispatcher.dispatch_due_tasks()
