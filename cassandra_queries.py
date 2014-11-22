import logging

__author__ = 'daan'

#region insert/upsert
CQL_INSERT_POST = \
"""INSERT INTO post (
    username,
    k,
    last_k,
    time,
    msg,
    rt_username,
    rt_k,
    reply_username,
    reply_k,
    json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

CQL_INSERT_REPLY = \
"""INSERT INTO reply (
    parent_username,
    parent_k,
    reply_username,
    reply_k,
    reply_time)
VALUES (?, ?, ?, ?, ?)"""

CQL_INSERT_RETRANSMIT = \
"""INSERT INTO retransmit (
    parent_username,
    parent_k,
    retransmit_username,
    retransmit_k,
    retransmit_time)
VALUES (?, ?, ?, ?, ?)"""

CQL_INSERT_MENTION = \
"""INSERT INTO mention (
    mentioned_username,
    mentioning_username,
    mentioning_k,
    mention_time)
VALUES (?, ?, ?, ?)"""

CQL_INSERT_HASHTAG = \
"""INSERT INTO hashtag (
    hashtag,
    username,
    k,
    post_time)
VALUES (?, ?, ?, ?)"""

CQL_INSERT_USER = \
"""INSERT INTO user (
    username,
    fullname,
    location,
    bio,
    url,
    avatar_b64,
    following,
    highest_k_indexed,
    last_update_time,
    json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""

CQL_INSERT_NEW_K = \
"""INSERT INTO user (
    username,
    highest_k_indexed,
    last_update_time)
VALUES (?, ?, ?)"""

CQL_INSERT_USER_CONSERVATIVE = \
"""INSERT INTO user (
    username,
    fullname,
    location,
    bio,
    url,
    avatar_b64,
    following,
    highest_k_indexed,
    last_update_time,
    json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
IF NOT EXISTS"""

CQL_INSERT_BLOCK = \
"""INSERT INTO block (
    height,
    hash,
    user_registrations,
    new_users,
    username,
    spam_msg,
    json)
VALUES (?, ?, ?, ?, ?, ?, ?)"""

#endregion

#region creating tables

CQL_CREATE_TABLE_USER = \
"""CREATE TABLE IF NOT EXISTS user (
    username text,
    fullname text,
    location text,
    bio text,
    url text,
    avatar_b64 text,
    following set<text>,
    highest_k_indexed int,
    last_update_time timestamp,
    json text,
    PRIMARY KEY (username)
)"""

CQL_CREATE_TABLE_UPDATE_JOB = \
"""CREATE TABLE update_jobs (
  due timestamp,
  username text,
  PRIMARY KEY (due, username)
)"""

CQL_CREATE_TABLE_POST = \
"""CREATE TABLE IF NOT EXISTS post (
    username text,
    k int,
    last_k int,
    time timestamp,
    msg text,
    rt_username text,
    rt_k int,
    reply_username text,
    reply_k int,
    json text,
    PRIMARY KEY (username, k)
)"""

CQL_CREATE_TABLE_HASHTAG = \
"""CREATE TABLE IF NOT EXISTS hashtag(
    hashtag text,
    username text,
    k int,
    post_time timestamp,
    PRIMARY KEY(hashtag, username, k)
)"""

CQL_CREATE_TABLE_MENTION = \
"""CREATE TABLE IF NOT EXISTS mention(
    mentioned_username text,
    mentioning_username text,
    mentioning_k int,
    mention_time timestamp,
    PRIMARY KEY(mentioned_username, mentioning_username, mentioning_k)
)"""

CQL_CREATE_TABLE_REPLY = \
"""CREATE TABLE IF NOT EXISTS reply(
    parent_username text,
    parent_k int,
    reply_username text,
    reply_k int,
    reply_time timestamp,
    PRIMARY KEY(parent_username, parent_k, reply_username, reply_k)
)"""

CQL_CREATE_TABLE_RETRANSMIT = \
"""CREATE TABLE IF NOT EXISTS retransmit(
    parent_username text,
    parent_k int,
    retransmit_username text,
    retransmit_k int,
    retransmit_time timestamp,
    PRIMARY KEY(parent_username, parent_k, retransmit_username, retransmit_k)
)"""

CQL_CREATE_TABLE_BLOCK = \
"""CREATE TABLE IF NOT EXISTS block (
    height int,
    hash text,
    user_registrations int,
    new_users set<text>,
    username text,
    spam_msg text,
    json text,
    PRIMARY KEY (height)
)"""

#endregion

#region queries

#endregion

log = logging.getLogger('cassy')
log.setLevel('INFO')
log = logging.getLogger('cassandra')
log.setLevel('INFO')
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
log.addHandler(handler)

KEYSPACE = "twisterbook"
def setup_cassandra_schema(session):
    log.info("creating keyspace...")
    session.execute("""
        CREATE KEYSPACE IF NOT EXISTS %s
        WITH replication = { 'class': 'SimpleStrategy', 'replication_factor': '1' }
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
