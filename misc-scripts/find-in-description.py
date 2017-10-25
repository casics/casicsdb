#!/usr/bin/env python3.4

import os
import re
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

msg('Searching repos for "{}" in the description field'.format(term))

regex = re.compile(term, re.IGNORECASE)
for entry in repos.find({'description': {'$regex': regex}},
                        {'description': 1, 'owner': 1, 'name': 1}):
    msg('-'*70)
    msg(e_summary(entry))
    msg(entry['description'])

msg('-'*70)