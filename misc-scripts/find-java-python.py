#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
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

# Too slow.

# count = 0
# with open('four-million-project-ids.txt', encoding="utf-8") as f:
#     for line in f:
#         id = int(line.strip())
#         entry = repos.find_one({'_id': id, 'is_visible': True,
#                                 'files': {'$ne': -1},
#                                 '$or': [{'languages.name': 'Python'},
#                                         {'languages.name': 'Java'}]},
#                                {'_id': 1})
#         if entry:
#             msg(entry['_id'])
#             count += 1

count = 0
with open('four-million-project-ids.txt', encoding="utf-8") as f:
    for line in f:
        id = int(line.strip())
        entry = repos.find_one({'_id': id, 'files': {'$ne': -1}, 'is_visible': True},
                               {'languages': 1})
        if entry and entry['languages'] != -1:
            langs = [x['name'] for x in entry['languages']]
            if 'Java' in langs or 'Python' in langs:
                msg(id)
                count += 1

msg('{} total'.format(count))
