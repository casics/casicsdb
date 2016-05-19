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

def add(entry, owner, name):
    visible = github_url_exists(None, owner, name)
    if visible:
        msg('Adding new entry {}/{} (#{})'.format(owner, name, ghentry['id']))
    else:
        msg('Adding {}/{} (#{}) but marking as invisible'.format(owner, name, ghentry['id']))

    is_fork   = (ghentry['fork'] == 'true')
    parent    = ghentry['parent']['full_name'] if is_fork else None
    fork_root = ghentry['source']['full_name'] if is_fork else None
    languages = [{'name': ghentry['language']}] if ghentry['language'] else []

    entry =  repo_entry(id=ghentry['id'],
                        owner=owner,
                        name=name,
                        description=ghentry['description'],
                        languages=languages,
                        homepage=ghentry['homepage'],
                        is_visible=visible,
                        is_deleted=False,
                        default_branch=ghentry['default_branch'],
                        created=canonicalize_timestamp(ghentry['created_at']),
                        last_updated=canonicalize_timestamp(ghentry['updated_at']),
                        last_pushed=canonicalize_timestamp(ghentry['pushed_at']),
                        data_refreshed=now_timestamp(),
                        is_fork=is_fork,
                        fork_of=parent,
                        fork_root=fork_root)
    repos.insert_one(entry)


def update(entry, ghentry):
    updates = {}

    # We haven't tracked home page URLs until now, so we always take theirs.
    # We have to update the data_refreshed field since we're modifying our
    # entry.

    updates['homepage'] = ghentry['homepage']

    time = {'data_refreshed': now_timestamp()}
    time['repo_created'] = canonicalize_timestamp(ghentry['created_at'])
    time['repo_updated'] = canonicalize_timestamp(ghentry['updated_at'])
    their_pushed_time = canonicalize_timestamp(ghentry['pushed_at'])
    if entry['time']['repo_pushed'] < their_pushed_time:
        time['time']['repo_pushed'] = their_pushed_time
    updates['time'] = time

    # For the rest, we only update stuff we don't have yet.

    if not entry['default_branch']:
        updates['default_branch'] = ghentry['default_branch']

    if (not entry['languages'] or entry['languages'] == -1) and ghentry['language']:
        updates['languages'] = [{'name': ghentry['language']}]

    if ghentry['fork'] == 'true' and not entry['fork']:
        fork = {}
        fork['parent'] = ghentry['parent']['full_name']
        fork['root']   = ghentry['source']['full_name']
        updates['fork'] = fork

    # Issue the update to our db.
    msg('{}/{} (#{}) updated'.format(owner, name, entry['_id']))
    repos.update_one({'_id': entry['_id']}, {'$set': updates}, upsert=False)


def github_url_path(entry, owner=None, name=None):
    if not owner:
        owner = entry['owner']
    if not name:
        name  = entry['name']
    return '/' + owner + '/' + name


def github_url(entry, owner=None, name=None):
    return 'http://github.com' + github_url_path(entry, owner, name)


def github_url_exists(entry, owner=None, name=None):
    url_path = github_url_path(entry, owner, name)
    try:
        conn = http.client.HTTPSConnection('github.com', timeout=15)
    except:
        # If we fail (maybe due to a timeout), try it one more time.
        try:
            sleep(1)
            conn = http.client.HTTPSConnection('github.com', timeout=15)
        except Exception:
            msg('Failed url check for {}: {}'.format(url_path, err))
            return None
    conn.request('HEAD', url_path)
    resp = conn.getresponse()
    return resp.status < 400


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
            # We didn't find it at all.
            add(ghentry, owner, name)

    # Misc.

    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
