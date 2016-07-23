#!/usr/bin/env python3.4

import sys
import time

sys.path.append('../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

for entry in repos.find({'content_type': 'empty'}, {'owner':1, 'name':1}, no_cursor_timeout=True):
    msg('{}/{}'.format(entry['owner'], entry['name']))
