#!/usr/bin/env python3.4

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

# Add new fields for content_type
# .............................................................................

start = time()
msg(repos.update_many({}, {'$set': {'content_type': ''}}))
print('time elapsed: {}'.format(time() - start))
