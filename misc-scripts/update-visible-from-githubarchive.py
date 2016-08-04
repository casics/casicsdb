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


def make_visible(entry, is_visible=True, checked_github=False):
    msg('{}/{} (#{}) is_visible = {}'.format(
        entry['owner'], entry['name'], entry['_id'], is_visible))
    if checked_github:
        refresh_time = now_timestamp()
    else:
        refresh_time = entry['time']['data_refreshed']
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'is_visible': is_visible,
                               'time.data_refreshed': refresh_time}},
                     upsert=False)


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

        repo       = contents['repo']
        id         = repo['id']
        path       = repo['name']
        owner      = path[:path.find('/')]
        name       = path[path.find('/') + 1 :]
        their_time = canonicalize_timestamp(contents['created_at'])

        if path in done:
            continue
        done.add(path)

        fields = {'owner': 1, 'name': 1, 'is_visible': 1, 'time': 1}
        entry = repos.find_one({'_id': id}, fields)
        if not entry:
            entry = repos.find_one({'owner': owner, 'name': name}, fields)
            if not entry:
                # They're all public.
                # if not contents['public']:
                #     msg('unknown {} (#{}) is not public anyway -- skipping'.format(path, id))
                #     continue
                msg('*** unknown {} (#{}) is public -- skipping but should add'.format(path, id))
            else:
                # We know it under a different name.
                msg('*** missmatch: their {} (#{}) is our {}/{} (#{})'.format(
                    path, id, entry['owner'], entry['name'], entry['_id']))

                if entry['is_visible'] != '' and their_time < entry['time']['data_refreshed']:
                    # We have a value and our refresh time is newer.
                    continue
                # They're all public.
                # if not contents['public']:
                #     msg('{} (#{}) is not public'.format(path, id))
                #     make_visible(entry, False)
                if not github_url_exists(entry):
                    msg('{} (#{}) no longer exists'.format(path, id))
                    make_visible(entry, False, True)
                else:
                    make_visible(entry, True, True)
        else:
            if entry['is_visible'] != '' and their_time < entry['time']['data_refreshed']:
                # We have a value and our refresh time is newer.
                continue
            make_visible(entry, contents['public'])

    count += 1
    if count % 100 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
