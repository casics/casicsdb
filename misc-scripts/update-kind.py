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

def replace(old, new):
    repos.update_many({'kind': old}, {'$addToSet': {'kind': new}})
    repos.update_many({'kind': old}, {'$pull': {'kind': old}})

replace('application', 'standalone')
