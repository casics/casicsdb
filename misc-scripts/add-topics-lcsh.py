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

# repos.update_many({}, {'$set': {'topics': {'lcsh': []}}}, upsert=False);
