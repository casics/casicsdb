#!/usr/bin/env python3.4
#
# @file    add-from-ghtorrent-dump.py
# @brief   Add entries from a GHTorrent MongoDB database dump.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# This assumes that the current machine is running mongodb and has been
# loaded with a ghtorrent dump.  In that case, the local database will
# have a github database and a collection called "repos" inside of it.


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

msg('Opening local database ...')

ghtorrentdb = MongoClient(tz_aware=True, connect=True)
ghtorrentgithub = ghtorrentdb.open('github')
ghtorrentrepos = ghtorrentgithub.repos

msg('Opening remote CASICS database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

msg('Reading file of repositories')

lines = None
with open(sys.argv[1], encoding="utf-8") as f:
    lines = f.readlines()

msg('Doing updates')
count = 0
start = time()
for line in lines:
    line  = line.strip()
    owner = line[:line.find('/')]
    name  = line[line.find('/') + 1:]

    ghentry = ghtorrentrepos.find_one({'owner.login': owner, 'name': name})
    if not ghentry:
        msg('*** {}/{} not found in GHTorrent dump'.format(owner, name))
        continue

    entry = repos.find_one({'owner': owner, 'name': name})
    if not entry:
        msg('*** {}/{} not found in our db'.format(owner, name))
        continue
    if ghentry['id'] != entry['_id']:
        msg('*** {}/{} GH id {} does not match our id {}'.format(
            owner, name, ghentry['id'], entry['_id']))
        continue

    # Gather up the data we're going to store.

    updates = {}

    updates['homepage'] = ghentry['homepage']
    updates['default_branch'] = ghentry['default_branch']

    updates['is_fork'] = bool(ghentry['fork'])
    if ghentry['fork']:
        if ghentry['parent']:
            updates['fork_of'] = ghentry['parent.full_name']
        else:
            updates['fork_of'] = ''
            msg('*** {}/{} missing parent field'.format(owner, name))

        if ghentry['source']:
            updates['fork_root'] = ghentry['source.full_name']
        else:
            updates['fork_root'] = ''
            msg('*** {}/{} missing source field'.format(owner, name))

    # Issue the update to our db.

    repos.update_one({'_id': entry['_id']}, {'$set': updates}, upsert=False)

    # Misc.

    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
