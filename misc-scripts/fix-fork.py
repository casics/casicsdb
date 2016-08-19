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

# We now use files == 'empty' to indicate empty.
msg('Doing update')
repos.update({'fork': {'$ne': False}, 'fork.parent': '', 'fork.root': ''},
             {'$set': {'fork.parent': None, 'fork.root': None}},
             multi=True)
msg('Done')
