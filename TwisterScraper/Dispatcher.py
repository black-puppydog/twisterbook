__author__ = 'daan'

from celery import Celery

app = Celery('tasks', broker='amqp://guest@localhost//')

@app.task
def add(x, y):
    return x + y

from datetime import datetime
import logging
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, BatchStatement
import RpcScraper

class Dispatcher:

    # todo: change this back to cluster = Cluster(['127.0.0.1]) once we figure out how to talk to the spotify cassandra docker container
    # todo: change the cache timeout to something more realistic?
    def __init__(self, cassandra_urls=['172.17.0.4'], cache_timeout=3600*24):
        log.debug("Connect to cassandra...")
        self.cluster = Cluster()
        self.cassy = cluster.connect()

        self.cache_timeout = cache_timeout

    def get_due_users(self):

        now = datetime.now().timestamp()

        # todo: filter this down to due tasks in CQL if possible
        result = cassy.execute("SELECT * FROM user_indexing_state")
        print("User Count: %i" % len(result))

        # todo: if filtering in CQL works then this should be unneccessary
        return [row[0] from row in result if row[2]+self.cache_timeout <= now]

    def dispatch_due_tasks(self):
        due_users = self.getdue_users()

        for username in due_users:
            RpcScraper.dummy_scraper_task.delay(username)


if __name__=='__main__':

