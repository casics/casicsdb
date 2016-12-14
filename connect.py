#!/usr/bin/env python3.4

import bson
import json
import os
import pprint
import sys
import time
import humanize

sys.path.append('../common')
from casicsdb import *
from utils import *
from pymongo import ASCENDING, DESCENDING, TEXT

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos
