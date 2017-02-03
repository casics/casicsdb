#!/usr/bin/env python3

import os
import plac
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

def run(file=None, lang=None):
    count = 0
    msg('-'*70)
    with open(file, encoding="utf-8") as f:
        for line in f:
            id = int(line.strip())
            entry = repos.find_one({'_id': id,
                                    'files': {'$ne': -1},
                                    'is_visible': True},
                                   {'languages': 1, 'owner': 1, 'name': 1})
            if entry and entry['languages'] != -1:
                if lang in [x['name'] for x in entry['languages']]:
                    msg('{:<8d}  {}/{}'.format(id, entry['owner'], entry['name']))
                    count += 1
    msg('-'*70)
    msg('{} total'.format(count))

run.__annotations__ = dict(
    file = ('file containing repo identifiers', 'option', 'f'),
    lang = ('language to look for', 'option', 'l'),
)

if __name__ == '__main__':
    plac.call(run)
