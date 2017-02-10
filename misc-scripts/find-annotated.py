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

count = 0
for i, entry in enumerate(repos.find({'topics.lcsh': {'$ne' : []}})):
    msg(entry['_id'])
    i += 1
msg('Total: {}'.format(i))
