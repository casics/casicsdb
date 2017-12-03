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

for entry in repos.find():
    if entry['readme']:
        try:
            raw = zlib.decompress(entry['readme'])
            if raw:
                status = repos.update_one( {'_id' : entry['_id'] },
                                           {'$set' : { 'readme' : raw } } )
                msg('{}: {}'.format(entry['_id'], status.modified_count))
        except:
            msg('failed on {}'.format(entry['_id']))
