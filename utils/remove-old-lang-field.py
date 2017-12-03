#!/usr/bin/env python3.4

import os
import sys
import zlib

from datetime import datetime

sys.path.append('../common')

from database import *
from lang import *

casicsdb  = CasicsDB()
github_db = casicsdb.open('github')
repos     = github_db.repos

repos.update({}, {'$unset': { 'language': ''} }, multi=True)
