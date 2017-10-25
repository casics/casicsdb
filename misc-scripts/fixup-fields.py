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

count = 0
start = time()
for entry in repos.find({ 'homepage' : { '$exists' : False } }):
    repos.update({'_id': entry['_id']},
                 {'$set': {'homepage': None,
                           'fork_root': None,
                           'refreshed': now_timestamp()}})
    count += 1
    if count % 100 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

# 2016-05-12 <mhucka@caltech.edu>
# Fix a mistake.

count = 0
start = time()
for entry in repos.find({'languages.name': 'N'}, {'languages': 1, 'refreshed': 1}):
    if len(entry['languages']) == 1:
        repos.update({'_id': entry['_id']},
                     {'$set': {'languages': [],
                               'refreshed': now_timestamp()}})
    count += 1
    if count % 100 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()
