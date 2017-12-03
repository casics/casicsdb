#!/usr/bin/env python3.4

import os
import sys
import zlib

from datetime import datetime

sys.path.append('..')
sys.path.append('../../common')

from casicsdb import *
from utils import *

casicsdb  = CasicsDB()
github_db = casicsdb.open('github')
repos     = github_db.repos

for entry in repos.find({'description': None, 'is_visible': True}, {'_id': 1}):
    msg(entry['_id'])
