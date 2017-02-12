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

list_file = sys.argv[1]

msg('Visible repos from list in {}'.format(list_file))

with open(list_file, 'r') as f:
    for id in f.readlines():
        id = int(id.strip())
        entry = repos.find_one({'_id': id, 'is_visible': True}, {'visibility': 1})
        if entry:
            msg(id)
