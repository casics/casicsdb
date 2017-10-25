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

repos.update({'time.repo_created' : {'$exists': False}}, {'$set': {'time.repo_created': ''}}, multi=True)
repos.update({'time.repo_updated' : {'$exists': False}}, {'$set': {'time.repo_updated': ''}}, multi=True)
repos.update({'time.repo_pushed'  : {'$exists': False}}, {'$set': {'time.repo_pushed': ''}},  multi=True)
repos.update({'time.data_refreshed'  : {'$exists': False}}, {'$set': {'time.data_refreshed': ''}},  multi=True)
