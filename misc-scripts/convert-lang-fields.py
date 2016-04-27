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
    if entry['language']:
        current = entry['language']
        from_codes = Lang.convert(current['codes'])
        langlist = (from_codes or []) + (current['others'] or [])
        if langlist:
            langlist = [{'name' : x} for x in sorted(langlist)]
        else:
            langlist = []
        status = repos.update_one( {'_id' : entry['_id'] },
                                   {'$set' : { 'languages' : langlist } } )

        msg('{}: {}'.format(entry['_id'], status.modified_count))
