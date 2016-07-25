#!/usr/bin/env python3.4
#
# @file    add-empty-from-ghtorrent-dump.py
# @brief   Look for repos with empty sizes
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
import http
import requests
import urllib
from datetime import datetime
from time import time, sleep
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Helpers
# .............................................................................

def update(entry, ghentry):
    updates = {}

    # Turns out we can't trust the value returned by GitHub: if it's 0, the
    # repo is often *not* actually empty.  So all we can do is record when we
    # find it's not 0.
    if ghentry['size'] > 0 and entry['content_type'] == '':
        updates['content_type'] = 'nonempty'
        repos.update_one({'_id': entry['_id']}, {'$set': updates}, upsert=False)
        msg('{}/{} (#{}) updated'.format(owner, name, entry['_id']))


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

start = time()

msg('Opening local database ...')

ghtorrentdb = MongoClient(tz_aware=True, connect=True)
ghtorrentgithub = ghtorrentdb['github']
ghtorrentrepos = ghtorrentgithub.repos

msg('Opening remote CASICS database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

msg('Doing updates')
count = 0
start = time()
for ghentry in ghtorrentrepos.find({}, {'size': 1, 'owner': 1, 'name': 1}, no_cursor_timeout=True):
    owner = ghentry['owner']['login']
    name = ghentry['name']
    entry = repos.find_one({'owner': owner, 'name': name}, {'content_type': 1, 'owner': 1, 'name': 1})
    if not entry:
        msg('*** {}/{} not found in our database'.format(owner, name))
        continue
    update(entry, ghentry)

    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
