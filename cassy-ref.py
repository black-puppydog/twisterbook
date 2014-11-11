#! /usr/bin/env python

import datetime
from cassandra_queries import *
__author__ = 'daan wynen'

# This script should be called by the twisterd hook "blocknotify" to enter newly registered users into the the system

import logging
import sys
from cassandra import ConsistencyLevel
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement, BatchStatement

log = logging.getLogger()
log.setLevel('DEBUG')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

KEYSPACE = "twisterbook"
serverUrl = "http://user:pwd@127.0.0.1:28332"


def delete_all(cassy):
    cassy.execute("DROP KEYSPACE " + KEYSPACE)


def setup_cassandra_schema(session):
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)

    log.info("setting keyspace")
    session.set_keyspace(KEYSPACE)

    log.info("creating table block")
    session.execute(CQL_CREATE_TABLE_BLOCK)

    log.info("creating table user")
    session.execute(CQL_CREATE_TABLE_USER)

    log.info("creating table post")
    session.execute(CQL_CREATE_TABLE_POST)

    log.info("creating table reply")
    session.execute(CQL_CREATE_TABLE_REPLY)

    log.info("creating table retransmit")
    session.execute(CQL_CREATE_TABLE_RETRANSMIT)

    log.info("creating table hashtag")
    session.execute(CQL_CREATE_TABLE_HASHTAG)

    log.info("creating table mention")
    session.execute(CQL_CREATE_TABLE_MENTION)




def print_db_stats(cassy):
    result = cassy.execute("SELECT COUNT(*) FROM post")
    print("Post Count: %i" % result[0])
    # todo: add more here.



def read_block(block_hash, cassy, twister):
    insert_user = cassy.prepare("""INSERT INTO user_indexing_state (
                username,
                last_indexed_k,
                last_indexing_time) VALUES (?, ?, ?)""")
    update_last_block = cassy.prepare("""
                INSERT INTO last_scanned_block (fake_id, block_hash)
                VALUES (?, ?)""")

    block = twister.getblock(block_hash)
    print("Block height: %i" % block["height"], end='')

    usernames = block["usernames"]
    # todo: this should be changed iff we use more than one node in cassy's cluster :P
    batch = BatchStatement(consistency_level=ConsistencyLevel.ANY)
    for u in usernames:
        batch.add(insert_user, (u, -1, datetime.datetime.utcfromtimestamp(0)))
    batch.add(update_last_block, (0, block_hash,))
    cassy.execute(batch)
    print(" contains %i user registrations." % len(usernames))
    return block


def full_blockchain_scan(cassy, twister):
    setup_cassandra_schema(cassy)

    nextHash = twister.getblockhash(0)

    while True:
        block = read_block(nextHash, cassy, twister)

        # continue with next block?
        if "nextblockhash" in block:
            nextHash = block["nextblockhash"]
        else:
            break


if __name__ == "__main__":
    main()

