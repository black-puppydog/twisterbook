import pymysql
from LoginData import *
from TwisterScraper import RpcScraper

from datetime import datetime
import logging

__author__ = 'daan'

from celery import Celery

app = Celery('RpcScraper', broker=RABBITMQ_PUBLISHER_URL)


class Dispatcher:

    # todo: change the cache timeout to something more realistic?
    def __init__(self, cache_timeout=3600*24):
        self.log = logging.getLogger()

        self.cache_timeout =cache_timeout

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
        result = cursor.execute("SELECT username, last_indexed_k, last_indexed_time "
                                "FROM users "
                                "WHERE unix_timestamp(last_indexed_time) + %s <= %s", (self.cache_timeout, now) )
        print("User that neet scraping: %i" % len(result))

        # todo: if filtering in SQL works then this should be unneccessary
        # return [row for row in result if row[2] + self.cache_timeout <= now]
        return result

    def dispatch_due_tasks(self):
        due_users = self.getdue_users()

        for row in due_users:
            RpcScraper.dummy_scraper_task.delay(row[0], row[1])


if __name__=='__main__':
    pass
