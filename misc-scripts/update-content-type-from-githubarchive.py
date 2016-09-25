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

root = 'https://api.github.com/repos/'
root_len = len(root)

done = set()
with gzip.open(input, 'r') as f:
    count = 0
    start = time()
    for line in f:
        contents = json.loads(line.decode('ascii', 'ignore'))

        if contents['type'] != 'ReleaseEvent' and contents['type'] != 'ForkEvent':
            continue

        id = None
        entry = None
        owner = None
        name = None
        path = None
        if 'repository' in contents:
            repo  = contents['repository']
            owner = repo['owner']
            name  = repo['name']
            path  = owner + '/' + name
            id    = repo['id']
        elif 'repo' in contents:
            repo  = contents['repo']
            if 'id' not in repo:
                msg('*** ignoring bad content: {}'.format(contents))
                continue
            path  = repo['name']
            owner = path[:path.find('/')]
            name  = path[path.find('/') + 1 :]
            id    = repo['id']
        elif 'payload' in contents:
            payload = contents['payload']
            if not payload:
                msg('*** empty payload in contents: {}'.format(contents))
                continue
            elif 'release' in payload:
                url = payload['release']['url']
                url = url[root_len: ]
                owner = url[: url.find('/')]
                name = url[url.find('/') + 1 : url.find('/releases')]
            else:
                msg('problem 1')
                import ipdb; ipdb.set_trace()
        else:
            msg('problem 2')
            import ipdb; ipdb.set_trace()


        if owner == '' or name == '':
            msg('*** ignoring bad path {}/{}'.format(owner, name))
            continue

        fields = {'owner': 1, 'name': 1, 'content_type': 1, 'is_visible':1, 'is_deleted':1}
        if id:
            entry = repos.find_one({'_id': id}, fields)
        if not entry:
            entry = repos.find_one({'owner': owner, 'name': name}, fields)
            if not entry:
                msg('*** unknown {} (#{}) -- skipping'.format(path, id))
                continue
            elif entry['is_deleted']:
                msg('*** {} (#{}) marked as deleted -- skipping'.format(path, entry['_id']))
                continue
            elif not entry['is_visible']:
                msg('*** {} (#{}) marked as not visible -- skipping'.format(path, entry['_id']))
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
