#!/usr/bin/env python3.4

import os
import pprint
import sys
import time

sys.path.append('../common')

from casicsdb import *
from pymongo import ASCENDING, DESCENDING, TEXT

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

start = time.time()
repos.create_index( [('owner', ASCENDING), ('name', ASCENDING)], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('description', TEXT), ('readme', TEXT)], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('languages.name', ASCENDING )], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('created', ASCENDING )], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('refreshed', ASCENDING )], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('is_deleted', ASCENDING )], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('is_fork', ASCENDING )], background=True)
print(time.time() - start)

start = time.time()
repos.create_index( [('is_visible', ASCENDING )], background=True)
print(time.time() - start)
