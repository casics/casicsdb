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

file = sys.argv[1]

msg('Listing descriptions for repos found in file {}'.format(file))

id_list = []
with open(file) as f:
    id_list = f.read().splitlines()

for id in id_list:
    entry = repos.find_one({'_id': int(id)}, {'description': 1, 'owner': 1, 'name': 1})
    msg('{}: {}'.format(e_summary(entry), entry['description']))
