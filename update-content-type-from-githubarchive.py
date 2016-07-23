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
import http
import requests
import urllib
import gzip
import json
from datetime import datetime
from time import time, sleep
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Helpers
# .............................................................................

def update_content(entry, value):
    # Purposefully not updating the data_refreshed time, because i'm running
    # this concurrently with other updates and the others do check the refresh
    # time.  It's not crucial to touch the refresh time for this update.
    updates = {}
    updates['content_type'] = value
    repos.update_one({'_id': entry['_id']}, {'$set': updates}, upsert=False)
    msg('{}/{} (#{}) updated to {}'.format(owner, name, entry['_id'], value))


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

start = time()

msg('Opening remote CASICS database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

input = sys.argv[1]
msg('Opening file {}'.format(input))

done = set()
with gzip.open(input, 'r') as f:
    count = 0
    start = time()
    for line in f:
        contents = json.loads(line.decode('ascii', 'ignore'))

        if contents['type'] != 'ReleaseEvent':
            continue

        id = None
        entry = None
        if 'repo' in contents:
            repo  = contents['repo']
            path  = repo['name']
            owner = path[:path.find('/')]
            name  = path[path.find('/') + 1 :]
            id    = repo['id']
        else
            msg('problem 1')
            import ipdb; ipdb.set_trace()

        if path in done:
            continue
        done.add(path)

        fields = {'owner': 1, 'name': 1, 'content_type': 1}
        if id:
            entry = repos.find_one({'_id': id}, fields)
        if not entry:
            entry = repos.find_one({'owner': owner, 'name': name}, fields)
            if not entry:
                msg('*** unknown {} (#{}) -- skipping'.format(path, id))
                continue
            elif id:
                # We know it under a different id or name.
                msg('*** mismatch: their {} (#{}) is our {}/{} (#{})'.format(
                    path, id, entry['owner'], entry['name'], entry['_id']))

        if entry['content_type'] == '':
            update_content(entry, 'nonempty')

    count += 1
    if count % 100 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
