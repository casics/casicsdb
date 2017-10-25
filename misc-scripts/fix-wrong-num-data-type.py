#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
import sys
import time

sys.path.append('../')
sys.path.append('../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

count = 0
start = time()
for entry in repos.find({ 'num_commits' : { '$type' : 2 } }, {'num_commits': 1, '_id': 1}):
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'num_commits': int(entry['num_commits'].replace(',', ''))}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

for entry in repos.find({ 'num_branches' : { '$type' : 2 } }, {'num_branches': 1, '_id': 1}):
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'num_branches': int(entry['num_branches'].replace(',', ''))}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

for entry in repos.find({ 'num_contributors' : { '$type' : 2 } }, {'num_contributors': 1, '_id': 1}):
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'num_contributors': int(entry['num_contributors'].replace(',', ''))}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()

for entry in repos.find({ 'num_releases' : { '$type' : 2 } }, {'num_releases': 1, '_id': 1}):
    repos.update_one({'_id': entry['_id']},
                     {'$set': {'num_releases': int(entry['num_releases'].replace(',', ''))}})
    count += 1
    if count % 1000 == 0:
        msg('{} [{:2f}]'.format(count, time() - start))
        start = time()
