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
repos.update({'content_type': 'empty'}, {'$set': {'files': -1}}, multi=True)
repos.update({'files': 'empty'}, {'$set': {'files': -1}}, multi=True)

# We no longer use values of 'empty' or 'nonempty' in content_type.  If we
# used them before, we change it to an unknown content type.
repos.update({'content_type': 'empty'}, {'$set': {'content_type': []}}, multi=True)
repos.update({'content_type': 'nonempty'}, {'$set': {'content_type': []}}, multi=True)

# The others have a different format.
repos.update({'content_type': 'noncode'},
             {'$set': {'content_type': [ {'content': 'noncode', 'determined_by': 'languages'} ]}},
             multi=True)

# We'll have to redo this one b/c I didn't keep the evidence/approach info
# the first time around.
repos.update({'content_type': 'code'}, {'$set': {'content_type': [] }}, multi=True)
