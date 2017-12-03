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

repos.update({'readme': '-'*2048}, {'$set': {'readme': ''}}, multi=True)
repos.update({'description': '-'*512}, {'$set': {'description': ''}}, multi=True)
