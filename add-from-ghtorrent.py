#!/usr/bin/env python3.4
#
# @file    add-from-ghtorrent.py
# @brief   Add info we don't have, using a ghtorrent mysql dump.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Example lines from projects.csv:
#
# 1,"https://api.github.com/repos/tosch/ruote-kit",1,"ruote-kit","RESTful wrapper for ruote workflow engine","Ruby","2009-12-08 11:17:27",2,0
# 2,"https://api.github.com/repos/kennethkalmer/ruote-kit",4,"ruote-kit","RESTful wrapper for ruote workflow engine","Ruby","2009-06-10 20:32:21",\N,0
# 3,"https://api.github.com/repos/matplotlib/basemap",23,"basemap","","C++","2011-02-19 02:58:42",\N,0
# 4,"https://api.github.com/repos/jswhit/basemap",24,"basemap","","C++","2012-06-14 16:14:56",3,0
# 5,"https://api.github.com/repos/funkaster/cocos2d-x",28,"cocos2d-x","Port of cocos2d-iphone in C++","C++","2012-03-12 17:48:19",6,0
# 6,"https://api.github.com/repos/cocos2d/cocos2d-x",31,"cocos2d-x","Port of cocos2d-iphone in C++","C++","2010-11-18 23:17:00",\N,0
# 7,"https://api.github.com/repos/pixonic/cocos2d-x",42,"cocos2d-x","Port of cocos2d-iphone in C++","C","2012-04-23 12:20:29",6,0
# 8,"https://api.github.com/repos/NUBIC/ncs_navigator_core",65,"ncs_navigator_core","Case management and instrument administration for NCS Navigator","Ruby","2012-04-19 21:45:52",\N,0
# 9,"https://api.github.com/repos/sgonyea/rake-compiler",66,"rake-compiler","Provide a standard and simplified way to build and package Ruby C and Java extensions using Rake as glue.","Ruby","2012-08-01 20:33:51",28,0
# 10,"https://api.github.com/repos/chapuni/llvm",67,"llvm","Chapuni's branch based on http://llvm.org/git/llvm.git","C++","2011-02-01 09:11:48",\N,0


import sys
import plac
import os
import csv
from time import time, sleep

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

start = time()

msg('Opening database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

# The GHTorrent CSV projects.csv file has an "id" as the first column, but
# I believe that's the id for the entry in the table and not the project id.

fields = {'id'          : 0,            # Don't use this -- no the project id.
          'url'         : 1,
          'name'        : 3,
          'description' : 4,
          'language'    : 5,
          'created'     : 6,
          'forked_from' : 7,
          'deleted'     : 8}

namestart = len('https://api.github.com/repos/')
id_map = {}

# Read the file once and build a mapping from their identifiers to
# project owner/name path strings.

msg('Building project id mapping')
with open('projects.csv', encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    for row in reader:
        id   = row[fields['id']]
        if id == '-1':
            continue
        path = row[fields['url']][namestart:]
        id_map[id] = path
        count += 1
        if count % 10000 == 0:
            msg(count)

# Now process the file for real.

msg('Extracting the data for real.')
with open('projects.csv', encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    start = time()
    for row in reader:
        id   = row[fields['id']]
        if id == '-1':
            continue
        count += 1

        path        = row[fields['url']][namestart:]
        desc        = row[fields['description']]
        lang        = row[fields['language']]
        forked_from = row[fields['forked_from']]
        created     = row[fields['created']]
        deleted     = row[fields['deleted']]

        owner       = path[:path.find('/')]
        name        = path[path.find('/') + 1:]
        is_fork     = True if forked_from != 'N' else False
        is_deleted  = True if deleted != '0' else False

        entry = repos.find_one({'owner': owner, 'name': name})

        if not entry:
            # We need to deal with these using our cataloguer.
            msg('*** Unknown entry {}'.format(path))
            continue

        # We gather up changes and issue a single update command for an entry.

        updates = {}

        # If GHTorrent says something is a fork and we don't have it
        # that way in our database, then it is very unlikely that it
        # is *not* a fork.  Trust GHTorrent on this.  Unfortunately,
        # the GHTorrent data abou the fork source is in terms of
        # their id numbers, not github's, and I don't want to deal
        # with matching up their numbers and projects.  So we only
        # record that something *is* a fork, not its parent.

        if is_fork and not entry['is_fork']:
            msg('Updating is_fork for {}'.format(path))
            updates['is_fork'] = True
        if is_fork and not entry['fork_of'] and forked_from in id_map:
            msg('Updating fork_of for {}'.format(path))
            updates['fork_of'] = id_map[forked_from]

        # If GHTorrent knows something has been deleted, it's probably
        # a good bet that it has not been reverted somehow.

        if is_deleted:
            msg('Marking {} as deleted'.format(path))
            updates['is_deleted'] = True

        # If GHTorrent has language info for an entry and we don't,
        # take GHTorrent's value.  However, since GHTorrent's
        # projects.csv only lists 1 language for a project, don't
        # replace what we have in our database if we have something
        # for an entry already.

        if lang and (not entry['languages'] or entry['languages'] == -1):
            msg('Updating languages for {}'.format(path))
            updates['languages'] = [{'name':lang}]

        # If GHTorrent has a description and we don't, use theirs.
        # However, if we have a description, don't overwrite it because
        # it might be more recently-updated than theirs.

        if desc and (not entry['description'] or entry['description'] == -1):
            msg('Updating description for {}'.format(path))
            updates['description'] = desc

        # If GHTorrent has a creation date and we don't, use theirs.

        if created and not entry['created'] and created != '0000-00-00 00:00:00':
            msg('Updating creation date for {}'.format(path))
            updates['created'] = canonicalize_timestamp(created)

        # Send the updates if there are any.

        if updates:
            repos.update_one({'_id': entry['_id']},
                             {'$set': updates},
                             upsert=False)

        if count % 10000 == 0:
            msg('{} [{:2f}]'.format(count, time() - start))
            start = time()
