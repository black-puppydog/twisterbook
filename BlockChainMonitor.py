#! /usr/bin/env python

import datetime
import pymysql
import simplejson
import logging
import sys

__author__ = 'daan wynen'

# This script should be called by the twisterd hook "blocknotify" to enter newly registered users into the the system



from LoginData import *


def delete_all(db):
    cursor = db.cursor()
    cursor.execute("DELETE FROM posts;")
    cursor.execute("DELETE FROM blocks;")
    cursor.execute("DELETE FROM users;")
    db.commit()

def print_db_stats(db):
    cursor = db.cursor()
    result = cursor.execute("SELECT COUNT(*) FROM users")
    print("User Count: %i" % result[0])

    # todo: fix this shit!
    bh = cursor.execute("SELECT * FROM last_scanned_block")[0]
    print("Last scanned block: %s" % bh[1])


def main():
    try:
        from bitcoinrpc.authproxy import AuthServiceProxy
    except ImportError as exc:
        sys.stderr.write("Error: install python-bitcoinrpc (https://github.com/jgarzik/python-bitcoinrpc)\n")
        exit(-1)

    log.debug("Creating twister connection...")
    twister = AuthServiceProxy(TWISTER_RPC_URL)

    log.debug("Connect to database...")
    conn = pymysql.connect(
        host=MYSQL_HOSTNAME,
        port=MYSQL_PORT, user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DATABASE,
        charset="utf8")

    # do a full scan if we don't get any hash
    if len(sys.argv) == 1 or sys.argv[1] == '--init':
        full_blockchain_scan(conn, twister)
        return

    if sys.argv[1] == '--stats':
        print_db_stats(conn)

    if sys.argv[1] == '--reset':
        delete_all(conn)

    if sys.argv[1] == '--up-to-block':
        block_hash = sys.argv[2]
        print("will scan from last known block up to the new block with hash %s" % block_hash)
        # todo: do that thing

    if sys.argv[1] == '--only-block':
        read_block(sys.argv[2], conn, twister)


def read_block(block_hash, conn, twister):

    block = twister.getblock(block_hash)
    usernames = block["usernames"]
    print("Block height: %i contains %i user registrations." % (block["height"], len(usernames)))

    cur = conn.cursor()
    for u in usernames:
        cur.execute('INSERT IGNORE INTO users(username, last_indexed_k, last_indexed_time, json) '
                    'VALUES ("%s",%s,%s,"%s")', (u, -1, "FROM_UNIXTIME(1)", "{}"))
    cur.execute('INSERT IGNORE INTO blocks(height, hash, user_registrations, json) '
                'VALUES (%s,"%s",%s,"%s")', (int(block['height']), block_hash, len(usernames), simplejson.dumps(block, use_decimal=True, encoding='utf8')))
    conn.commit()
    return block


def full_blockchain_scan(cassy, twister):

    nextHash = twister.getblockhash(0)

    while True:
        block = read_block(nextHash, cassy, twister)

        # continue with next block?
        if "nextblockhash" in block:
            nextHash = block["nextblockhash"]
        else:
            break


if __name__ == "__main__":

    # region setup logging
    log = logging.getLogger()
    log.setLevel('DEBUG')
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    log.addHandler(handler)
    #endregion

    main()

