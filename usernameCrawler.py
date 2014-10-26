#!/usr/bin/python
#
# This sample script is a username crawler: it will obtain all known usernames
# from block chain and then try to download avatar and profiles for all of
# them. The report is shown as an html file.
#
# Downloaded data is cached in a python pickle file, so it may be executed
# again and it won't need to get everything all over again (you may run it
# from cron scripts, for example)

import sys, cPickle, time
import traceback
import pprint

dbFileName = "usernameCrawler.pickle"
htmlFileName = "userlist.html"
cacheTimeout = 72 * 3600

try:
    from bitcoinrpc.authproxy import AuthServiceProxy
except ImportError as exc:
    sys.stderr.write("Error: install python-bitcoinrpc (https://github.com/jgarzik/python-bitcoinrpc)\n")
    exit(-1)

serverUrl = "http://user:pwd@127.0.0.1:28332"
if len(sys.argv) > 1:
    serverUrl = sys.argv[1]

twister = AuthServiceProxy(serverUrl)


class MyDb:
    lastBlockHash = 0


try:
    db = cPickle.load(open(dbFileName))
    nextHash = db.lastBlockHash
except:
    db = MyDb()
    db.usernames = {}
    nextHash = twister.getblockhash(0)

while True:
    block = twister.getblock(nextHash)
    db.lastBlockHash = block["hash"]
    print str(block["height"]) + "\r",
    usernames = block["usernames"]
    for u in usernames:
        if not db.usernames.has_key(u):
            db.usernames[u] = {'updateTime': 0}
    if block.has_key("nextblockhash"):
        nextHash = block["nextblockhash"]
    else:
        break

from html import HTML
from cgi import escape


def outputHtmlUserlist(fname, db, keys):
    columns = set()
    for username in keys:
        dbentry = db.usernames[username]
        # print(dbentry)

        for columnname in dbentry.keys():
            columns.add(columnname)

        columns.discard('avatar')
        columns.discard('username')
        columns.discard('following')
        columns.discard('updateTime')
    columns = list(columns)
    columns.sort()
    print("columns: " + str(columns))

    h = HTML()
    h.head("")
    with h.body(""):
        with h.table(border='1', newlines=True):
            with h.tr:
                h.th("avatar")
                h.th("username")
                for column in columns:
                    h.th(column)

            for u in keys:
                if 'updateTime' not in db.usernames[u]:
                    print("weird user without updateTime:")
                    pprint.pprint(db.usernames[u])
                if db.usernames[u]['updateTime'] == 0 or len(db.usernames[u])==2:
                    continue
                with h.tr:
                    with h.td():
                        if 'avatar' in db.usernames[u]:
                            h.img('', src=escape(db.usernames[u]['avatar']), width="64", height="64")
                        else:
                            h.text("none")
                    h.td(u)
                    for column in columns:
                        with h.td():
                            if column in db.usernames[u]:
                                h.text(unicode(db.usernames[u][column]))#.replace(u"&", u"&amp;")))
    with open(fname, "w") as f:
        f.write(unicode(h).encode('utf8'))


candidates = set(db.usernames.keys())
closedSet = set()
loadedCounter = 0

try:
    while len(candidates) > 0 or len(openSet) > 0:
        root = candidates.pop()
        print "STARTING NEW BFS FROM USER ", root
        openSet = [root]
        openCount=1
        while openCount > 0:
            u = openSet.pop(0)
            # u = openSet.pop(random.randint(0, len(openSet)-1))
            try:
                print "dealing with ", u
            except UnicodeEncodeError:
                print "cannot print user info since Unicode error..."
            closedSet.add(u)
            candidates.discard(u)
            now = time.time()
            actualWorkDone = 'updateTime' not in db.usernames[u] or db.usernames[u]['updateTime'] + cacheTimeout < now
            if actualWorkDone:
                try:
                    print "getting profile for", u, "..."
                except UnicodeEncodeError:
                    print "cannot print user info since Unicode error..."
                d = twister.dhtget(u, "profile", "s")

                if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
                    db.usernames[u] = d[0]["p"]["v"]

                try:
                    print "getting avatar for", u, "..."
                except UnicodeEncodeError:
                    print "cannot print user info since Unicode error..."
                d = twister.dhtget(u, "avatar", "s")
                if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
                    db.usernames[u]['avatar'] = d[0]["p"]["v"]

                try:
                    print "getting following1 for", u, "..."
                except UnicodeEncodeError:
                    print "cannot print user info since Unicode error..."
                d = twister.dhtget(u, "following1", "s")
                if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
                    db.usernames[u]['following'] = [d[0]["p"]["v"]]
                else:
                    db.usernames[u]['following'] = [[]]
                loadedCounter += 1
                db.usernames[u]['updateTime'] = now
            for u2 in db.usernames[u]['following'][0]:
                if not db.usernames.has_key(u2):  # in case the user registered just now
                    db.usernames[u2] = {'updateTime': 0}
                if u2 not in closedSet and u2 not in openSet:
                    openSet.append(u2)
                    # print("added {0} to openSet.".format(u2))

            if 'updateTime' not in db.usernames[u] or (actualWorkDone and loadedCounter % 10 == 0):
                with open(dbFileName, "w") as picklefile:
                    cPickle.dump(db, picklefile)

                print "Generating", htmlFileName, "..."

                keys = db.usernames.keys()
                keys.sort()  # sorted by username
                print(str(len(keys)) + " users in database")
                print("{0} users with info".format(len([u for u in keys if db.usernames[u]['updateTime'] > 0 and len(db.usernames[u]) > 2 ])))
                outputHtmlUserlist(htmlFileName, db, keys)
            print
            openCount = len(openSet)
            print "open nodes: ", openCount


# try:
#     for u in db.usernames.keys():
#         now = time.time()
#         if db.usernames[u]['updateTime'] + cacheTimeout < now:
#
#             print "getting profile for", u, "..."
#             d = twister.dhtget(u,"profile","s")
#             print(d)
#             if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
#                 db.usernames[u] = d[0]["p"]["v"]
#
#             print "getting avatar for", u, "..."
#             d = twister.dhtget(u,"avatar","s")
#             if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
#                 db.usernames[u]['avatar'] = d[0]["p"]["v"]
#
#             print "getting following1 for", u, "..."
#             d = twister.dhtget(u,"following1","s")
#             if len(d) == 1 and d[0].has_key("p") and d[0]["p"].has_key("v"):
#                 db.usernames[u]['following'] = [d[0]["p"]["v"]]
#             db.usernames[u]['updateTime'] = now
except:
    tb = traceback.format_exc()
else:
    tb = "No error"
finally:
    print tb
    with open(dbFileName, "w") as picklefile:
        cPickle.dump(db, picklefile)

print "Generating", htmlFileName, "..."

keys = db.usernames.keys()
keys.sort()  # sorted by username
print(str(len(keys)) + " users in database")
print("{0} users with info".format(len([u for u in keys if db.usernames[u]['updateTime'] > 0 and len(db.usernames[u]) > 2   ])))
outputHtmlUserlist(htmlFileName, db, keys)
