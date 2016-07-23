#!/usr/bin/env python3.4
#
# @file    id-to-url.py
# @brief   Take a list of repo id's and return a list of URLs to GitHub
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

import sys
import plac
import os
import csv
import http
import requests
import urllib
from datetime import datetime
from time import time, sleep
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

msg("Reading file of id's")

lines = None
with open(sys.argv[1], encoding="utf-8") as f:
    lines = f.readlines()
    for line in lines:
        id = line.strip()
        if not id.isdigit():
            msg('*** {} is not an integer'.format(id))
            continue
        entry = repos.find_one({'_id': int(id)})
        if not entry:
            # We need to deal with these using our cataloguer.
            msg('*** Unknown entry {}'.format(id))
            continue
        msg('https://github.com/{}/{}'.format(entry['owner'], entry['name']))
