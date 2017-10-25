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

term = sys.argv[1]

for entry in repos.find({'topics.lcsh': term}):
    msg(entry['_id'])

