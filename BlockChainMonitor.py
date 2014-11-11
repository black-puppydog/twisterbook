#! /usr/bin/env python

from datetime import datetime
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import BatchStatement
import simplejson
import sys
from cassandra_queries import *
from bitcoinrpc.authproxy import AuthServiceProxy


# region setup logging
log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)
#endregion

__author__ = 'daan wynen'

# This script should be called by the twisterd hook "blocknotify" to enter newly registered users into the the system


class BlockChainMonitor:

    def __init__(self, url="http://user:pwd@127.0.0.1:28332", cassy_nodes=['127.0.0.1']):
        self.url = url
        self.twister = AuthServiceProxy(self.url)

        log.debug("Connect to cassandra...")
        cluster = Cluster(cassy_nodes)
        self.cassy = cluster.connect()
        setup_cassandra_schema(self.cassy)

        self.insert_user = self.cassy.prepare(CQL_INSERT_USER_CONSERVATIVE)
        self.insert_block = self.cassy.prepare(CQL_INSERT_BLOCK)

    def full_blockchain_scan(self):

        nextHash = self.twister.getblockhash(0)

        while True:
            block = self.read_block(nextHash)

            # continue with next block?
            if "nextblockhash" in block:
                nextHash = block["nextblockhash"]
            else:
                break

    def read_block(self, block_hash):

        block = self.twister.getblock(block_hash)
        usernames = block["usernames"]

        if usernames:
            print("Block height: %i contains %i user registrations." % (block["height"], len(usernames)))

        for u in usernames:
            json = {'username': u, 'following': []}
            json = simplejson.dumps(json, encoding='utf8', use_decimal=True)
            self.cassy.execute(self.insert_user, (u, None, None, None, None, None, [], -1, datetime.utcfromtimestamp(1), json))

        height = int(block['height'])
        user_registrations = len(usernames)
        new_users = set(usernames)
        username = block['spamUser']
        spam_msg = block['spamMessage']
        block_json = simplejson.dumps(block, encoding='utf8', use_decimal=True)
        self.cassy.execute(self.insert_block, (height, block_hash, user_registrations, new_users, username, spam_msg, block_json))

        return block


def main():

    mon = BlockChainMonitor()

    # do a full scan if we don't get any hash
    if len(sys.argv) == 1 or sys.argv[1] == '--init':
        mon.full_blockchain_scan()
        return

    if sys.argv[1] == '--up-to-block':
        block_hash = sys.argv[2]
        print("will scan from last known block up to the new block with hash %s" % block_hash)
        # todo: do that thing
        raise NotImplementedError("soon to come?")

    if sys.argv[1] == '--only-block':
        mon.read_block(sys.argv[2])

if __name__ == "__main__":
    main()

