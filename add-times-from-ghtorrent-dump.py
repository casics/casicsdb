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
from datetime import datetime
from time import time, sleep
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Helpers
# .............................................................................

def update(entry, ghentry):
    updates = {}

    time = {'data_refreshed': now_timestamp()}
    if not 'repo_created' in entry['time'] or not entry['time']['repo_created']:
        time['repo_created'] = canonicalize_timestamp(ghentry['created_at'])
    if not 'repo_updated' in entry['time'] or not entry['time']['repo_updated']:
        time['repo_updated'] = canonicalize_timestamp(ghentry['updated_at'])
    if not 'repo_pushed' in entry['time'] or not entry['time']['repo_pushed']:
        time['repo_pushed'] = canonicalize_timestamp(ghentry['pushed_at'])
    updates['time'] = time

    # Issue the update to our db.
    msg('{}/{} (#{}) updated'.format(owner, name, entry['_id']))
    repos.update_one({'_id': entry['_id']}, {'$set': updates}, upsert=False)


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
        msg('* {}/{} not found in GHTorrent dump'.format(owner, name))
        continue

    # First try to find it with the repo id, because that's more invariant
    # than the name of the repo.
    entry = repos.find_one({'_id': ghentry['id']})
    if entry:
        if entry['owner'] != owner or entry['name'] != name:
            # We have the id, but with a different owner/name.  We keep ours
            # because we are more likely to have updated our records compared
            # to the older dumps from GHTorrent (at least at the time I'm
            # doing this today, 2016-05-12).
            msg('*** owner/name mismatch: using {}/{} for {}'.format(
                entry['owner'], entry['name'], entry['_id']))
        update(entry, ghentry)
    else:
        # We didn't find the id.  Check if we have the owner/name.
        entry = repos.find_one({'owner': owner, 'name': name})
        if entry:
            # We have different id's for the same owner/name path.  This can
            # happen if an owner renames a repository "A" to "B" but then
            # creates another repository called "A".  Depending on when we
            # sample GH versus when GHTorrent samples GH, we may have
            # different id's for the same owner/name path.  Now the question
            # is, which one is more correct?  We should take the one with the
            # most recent creation date.

            ghentry_date = canonicalize_timestamp(ghentry['created_at'])
            if entry['time']['repo_created'] > ghentry_date:
                msg('*** id mismatch: {}/{} is our #{} but their #{} -- ours is newer'.format(
                    entry['owner'], entry['name'], entry['_id'], ghentry['id']))
                update(entry, ghentry)
            else:
                # Their entry has a newer creation date.  It's tempting to
                # delete our entry and replace it with their presumably-newer
                # data, but in my spot-checking of cases when this happened,
                # our data was correct and theirs didn't match what's in GH.
                # I am leaving ours in place.

                msg('*** id mismatch: {}/{} is our #{} but their #{} -- theirs is newer'.format(
                    entry['owner'], entry['name'], entry['_id'], ghentry['id']))
                # repos.remove_one({'_id' : entry['_id']})
                # add(ghentry, owner, name)
                update(entry, ghentry)
        else:
            msg('!!! missing entry {}/{}'.format(owner, name))

    # Misc.

    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
