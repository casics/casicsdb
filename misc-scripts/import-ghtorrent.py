#!/usr/bin/env python3.4
#
# @file    convert-db.py
# @brief   Convert database to new record format
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

import pdb
import sys
import plac
import os
import csv
import pdb
from time import time

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from dbinterface import *
from utils import *
from reporecord import *

# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

start = time()

msg('Opening database ...')

db = Database()
dbroot = db.open()

msg('Opening projects.csv ...')

# The GHTorrent CSV projects.csv file has an "id" as the first column, but
# I believe that's the id for the entry in the table and not the project id.

fields = {'id'          : 0,            # Don't use this -- no the project id.
          'url'         : 1,
          'description' : 4,
          'language'    : 5,
          'forked_from' : 7,
          'deleted'     : 8}

namestart = len('https://api.github.com/repos/')

with open('projects.csv') as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    for row in reader:
        try:
            key     = row[fields['url']][namestart:]
            desc    = row[fields['description']]
            lang    = row[fields['language']]
            fork    = row[fields['forked_from']]
            deleted = row[fields['deleted']]
        except Exception as ex:
            msg('Skipping {} because of parsing error: {}'.format(key, ex))
            continue

        if not key in dbroot:
            msg('Unknown project {}'.format(key))
            continue
        else:
            old = dbroot[key]
            try:
                lang_id = Language.identifier(lang)
            except:
                msg('Unrecognized language {} -- skipping'.format(lang))
                continue
            if old.languages:
                if not lang_id in old.languages:
                    old.languages.append(lang_id)
                else:
                    msg('Already know {} has language {}'.format(key, lang))
                    continue            # We already know about it.
            else:
                old.languages = [lang_id]

            is_copy=True if fork != 'N' else False
            is_deleted=True if deleted != '0' else False

            msg('Updating {} to add {}'.format(key, lang))
            n = RepoEntry(host=old.host,
                          id=old.id,
                          path=old.path,
                          description=old.description,
                          readme=old.readme,
                          copy_of=is_copy,
                          owner=old.owner,
                          type=old.owner_type,
                          languages=old.languages,
                          deleted=is_deleted,
                          topics=old.topics,
                          categories=old.categories)
            dbroot[key] = n
            count += 1
        if count % 10 == 0:
            transaction.commit()
            msg('{} [{:2f}]'.format(count, time() - start))
            start = time()
    transaction.commit()
    # update_progress(1)
