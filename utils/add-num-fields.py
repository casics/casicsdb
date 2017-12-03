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

# Add new fields for num_commits, num_releases, num_branches.
# .............................................................................

start = time()
msg(repos.update_many({}, {'$set': {'num_commits': None,
                                    'num_releases': None,
                                    'num_branches': None,
                                    'num_contributors': None}}))
print('time elapsed: {}'.format(time() - start))
