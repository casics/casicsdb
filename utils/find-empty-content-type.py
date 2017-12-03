#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
import sys
import time

sys.path.append('../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

for entry in repos.find({'content_type': ''}, {}, no_cursor_timeout=True):
    print(entry['_id'])
