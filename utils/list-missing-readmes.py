#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
import sys
import time

sys.path.append('..')
sys.path.append('../common')
sys.path.append('../../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

for entry in repos.find({'readme': -1,
                         'files': {'$in': ['README.md', 'README', 'README.txt',
                                           'README.markdown', 'README.roc',
                                           'README.rst', 'README.textile']}}):
    msg('{}/{}'.format(entry['owner'], entry['name']))
