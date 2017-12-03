#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
import sys
import time

sys.path.append('../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

# Add new fields for topics, functions, licenses.
# .............................................................................

bulk = repos.initialize_unordered_bulk_op()
bulk.find({}).update({'$set': {'licenses': [],
                             'topics': [],
                             'functions': [],
                             'refreshed': now_timestamp()}})
msg(bulk.execute())

# Remove useless field 'archive_url'.
# .............................................................................

start = time()
msg(repos.update_many({}, {'$unset': {'archive_url': 1}}))
print('time elapsed: {}'.format(time() - start))

# Change handling of fork info.
# .............................................................................
# New idea is that we have a single field called 'fork', with the following
# possible values:
#
#   [] means we don't know know whether something is a fork
#   else, a value means we do know, and in that case,
#      fork.parent = None means it is not a fork, else the parent is named
#      fork.root has a value only if it's a fork and we know the original source

count = 0
start = time()
for entry in repos.find({'is_fork': True}):
    if entry['fork_of']:
        fork = entry['fork_of']
    else:
        fork = None
    if entry['fork_root']:
        root = entry['fork_root']
    else:
        root = None
    repos.update({'_id': entry['_id']},
                 {'$set': {'fork': {'parent': fork, 'root': root}}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

start = time()
msg(repos.update_many({'is_fork': False},
                      {'$set': {'fork': {'parent': None, 'root': None} }}))
print('time elapsed: {}'.format(time() - start))

start = time()
msg(repos.update_many({}, {'$unset': {'is_fork': 1}}))
print('time elapsed: {}'.format(time() - start))

start = time()
msg(repos.update_many({}, {'$unset': {'fork_of': 1}}))
print('time elapsed: {}'.format(time() - start))

start = time()
msg(repos.update_many({}, {'$unset': {'fork_root': 1}}))
print('time elapsed: {}'.format(time() - start))


# Change handling of time info.
# .............................................................................
# New fields:
#   time.repo_created   ==> when the repo was created on github
#   time.repo_modified  ==> when the repo was last updated (if we know)
#   time.data_refreshed ==> when we last touched this entry

count = 0
start = time()
for entry in repos.find({}):
    repos.update({'_id': entry['_id']},
                 {'$set': {'time': {'repo_created': entry['created'],
                                    'repo_modified': None,
                                    'data_refreshed': entry['refreshed']}}})
    count += 1
    if count % 100 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

start = time()
msg(repos.update_many({}, {'$unset': {'created': 1}}))
print('time elapsed: {}'.format(time() - start))

start = time()
msg(repos.update_many({}, {'$unset': {'refreshed': 1}}))
print('time elapsed: {}'.format(time() - start))
