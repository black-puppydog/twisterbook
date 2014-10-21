#! /usr/bin/python

import cPickle

dbFileName = "usernameCrawler.pickle"

class MyDb:
    lastBlockHash = 0

with open(dbFileName) as pickleFile:
    db = cPickle.load(pickleFile)

for u in db.usernames.keys():
    db.usernames[u] = {'updateTime': 0}


with open(dbFileName, "w") as picklefile:
    cPickle.dump(db,picklefile)
