#! /usr/bin/env python

import datetime

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

KEYSPACE = "queuebuilder"

dbFileName = "usernameCrawler.pickle"
serverUrl = "http://user:pwd@127.0.0.1:28332"


def delete_all(cassy):
    cassy.execute("DROP KEYSPACE " + KEYSPACE)


def setup_cassandra_schema(session):
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '2' }
        """ % KEYSPACE)

    log.info("setting keyspace...")
    session.set_keyspace(KEYSPACE)

    log.info("creating table last_scanned_block")
    session.execute("""
        CREATE TABLE IF NOT EXISTS last_scanned_block (
            fake_id int,
            block_hash text,
            PRIMARY KEY (fake_id)
        )
        """)

    log.info("creating table user_indexing_data")
    session.execute("""
        CREATE TABLE IF NOT EXISTS user_indexing_state (
            username text,
            last_indexed_k int,
            last_indexing_time timestamp,
            PRIMARY KEY (username)
        )
        """)


def print_db_stats(cassy):
    result = cassy.execute("SELECT COUNT(*) FROM user_indexing_state")
    print("User Count: %i"% result[0])

    bh = cassy.execute("SELECT * FROM last_scanned_block")[0]
    print("Last scanned block: %s" % bh[1])


def main():

    try:
        from bitcoinrpc.authproxy import AuthServiceProxy
    except ImportError as exc:
        sys.stderr.write("Error: install python-bitcoinrpc (https://github.com/jgarzik/python-bitcoinrpc)\n")
        exit(-1)

    log.debug("Creating twister connection...")
    twister = AuthServiceProxy(serverUrl)

    log.debug("Connect to cassandra...")
    # todo: change this back to cluster = Cluster(['127.0.0.1]) once we figure out how to talk to the spotify cassandra docker container
    cluster = Cluster(['172.17.0.4'])
    cassy = cluster.connect()

    # do a full scan if we don't get any hash
    if len(sys.argv) == 1 or sys.argv[1] == '--init':
        full_blockchain_scan(cassy, twister)
        return

    cassy.set_keyspace(KEYSPACE)
    if sys.argv[1] == '--stats':
        print_db_stats(cassy)

    if sys.argv[1] == '--reset':
        delete_all(cassy)

    block_hash = sys.argv[1]
    print("got a new block with hash %s" % block_hash)


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
    # todo: this should be changed iff we use more than one nod ein cassy's cluster :P
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

