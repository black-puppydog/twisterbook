#! /usr/bin/env python

from cassandra.cluster import Cluster
from cassandra_queries import *

cluster = Cluster(['127.0.0.1'])
cassy = cluster.connect()
cassy.set_keyspace(KEYSPACE)
setup_cassandra_schema(cassy)
