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

repos.update({'is_visible': True, 'is_deleted': True},
             {'$set': {'is_visible': False}}, multi=True)

repos.update({'is_visible': '', 'is_deleted': False, 'files': {'$ne': []}},
             {'$set': {'is_visible': True}}, multi=True)

repos.update({'is_visible': '', 'is_deleted': False, 'readme': {'$nin': [-1, -2, '']}},
             {'$set': {'is_visible': True}}, multi=True)

repos.update({'is_visible': '', 'is_deleted': False, 'description': {'$ne': ''}},
             {'$set': {'is_visible': True}}, multi=True)
