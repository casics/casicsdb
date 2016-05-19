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

# Change handling of time again.
# .............................................................................
# time.repo_modified is now time.repo_updated
# we have a new field time.repo_pushed

count = 0
start = time()
for entry in repos.find({}):
    repos.update({'_id': entry['_id']},
                 {'$set': {'time': {'repo_created': entry['created'],
                                    'repo_updated': None,
                                    'repo_pushed': None,
                                    'data_refreshed': entry['refreshed']}}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()
