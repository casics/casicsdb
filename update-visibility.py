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


def update(entry):
    is_visible = bool(github_url_exists(entry))
    msg('{}/{} (#{}) is_visible = {}'.format(
        entry['owner'], entry['name'], entry['_id'], is_visible))
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'is_visible': is_visible,
                               'time.data_refreshed': now_timestamp()}},
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

msg('Doing updates')

count = 0
start = time()
for entry in repos.find({'is_visible': ''},
                        {'is_visible': 1, 'owner': 1, 'name': 1, 'time': 1}):
    update(entry)

    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

msg('Done')
