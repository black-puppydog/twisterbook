#! /usr/bin/env python

import pymysql
from LoginData import *

from datetime import datetime
import logging
from TwisterScraper.RpcScraper import dummy_scraper_task

__author__ = 'daan'


class Dispatcher:
    # todo: change the cache timeout to something more realistic?
    def __init__(self, cache_timeout=3600 * 24, rescrape_timeout=3600 * 21):
        """

        :param cache_timeout: how long to wait until we try to pull new posts from soneone we already have posts of
        :param rescrape_timeout: how long to wait until considering to scrape a profile again for which we failed to
        retrieve anything before. the 21h default aims at considering each profile at different times of day so that
        we don't miss someone just because we always try to pull their profile while they (and all their peers) are
        at work and not runnning twister. Not sure of that's actually an issue but why not...
        """
        self.rescrape_timeout = rescrape_timeout
        self.log = logging.getLogger()

        self.cache_timeout = cache_timeout

        self.log.debug("Connect to database...")
        self.conn = pymysql.connect(
            host=MYSQL_HOSTNAME,
            port=MYSQL_PORT, user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            db=MYSQL_DATABASE)

    def get_due_users(self):
        now = datetime.now().timestamp()

        cursor = self.conn.cursor()
        # todo: filter this down to due tasks in SQL if possible
        result = cursor.execute("""(SELECT username, id, last_indexed_k, last_indexed_time
                                    FROM users as u
                                    WHERE unix_timestamp(u.last_indexed_time) + %s <= %s
                                    ORDER BY u.last_indexed_time ASC, RAND()
                                    LIMIT 1000)
                                    UNION
                                    (SELECT username, id, last_indexed_k, last_indexed_time
                                    FROM users AS u
                                    WHERE unix_timestamp(u.last_indexed_time) >100 -- we tried this user before
                                      AND u.last_indexed_k = -1
                                      AND unix_timestamp(u.last_indexed_time) + %s <= %s
                                    LIMIT 2000);
                                    """, (self.cache_timeout, now, self.rescrape_timeout, now))
        print("User that need scraping: %i" % result)

        # todo: if filtering in SQL works then this should be unneccessary
        # return [row for row in result if row[2] + self.cache_timeout <= now]
        return cursor.fetchall()

    def dispatch_due_tasks(self):
        due_users = self.get_due_users()

        for row in due_users:
            # dummy_scraper_task(row[0], row[1], row[2])
            dummy_scraper_task.delay(row[0], row[1], row[2])


if __name__ == '__main__':
    dispatcher = Dispatcher()
    dispatcher.dispatch_due_tasks()
