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
from BTrees.OOBTree import TreeSet

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from dbinterface import *
from utils import *
from reporecord import *


# Helpers.
# .............................................................................

def get_language_list(db):
    if '__ENTRIES_WITH_LANGUAGES__' not in db:
        db['__ENTRIES_WITH_LANGUAGES__'] = TreeSet()
    return db['__ENTRIES_WITH_LANGUAGES__']

def set_language_list(the_list, db):
    db['__ENTRIES_WITH_LANGUAGES__'] = the_list


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

start = time()

msg('Opening database ...')

dbinterface = Database()
db = dbinterface.open()

msg('Adding data from projects.csv ...')

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
    failures = 0
    entries_with_languages = get_language_list(db)
    while failures < 1000:
        # The file from GHTorrent has some problems due to some broken unicode.
        # Python csv library will generate an exception if it can't read a row.
        try:
            for row in reader:
                key     = row[fields['url']][namestart:]
                desc    = row[fields['description']]
                lang    = row[fields['language']]
                fork    = row[fields['forked_from']]
                deleted = row[fields['deleted']]

                if not key in db:
                    msg('Unknown project {}'.format(key))
                    continue
                else:
                    old = db[key]

                    # projects.csv only lists 1 language for a project.
                    languages = old.languages
                    already_has_language = False
                    try:
                        lang_id = Language.identifier(lang)
                    except:
                        msg('Unrecognized language {} -- skipping {}'.format(lang, key))
                        continue
                    if languages:
                        if not lang_id in languages:
                            languages.append(lang_id)
                            entries_with_languages.add(key)
                        else:
                            msg('Already know {} has language {}'.format(key, lang))
                            already_has_language = True
                    else:
                        languages = [lang_id]
                        entries_with_languages.add(key)

                    # Other info we can gather from projects.csv.
                    is_copy=True if fork != 'N' else False
                    is_deleted=True if deleted != '0' else False

                    # If we don't need to update our entry for language or
                    # copy info, we can move on.
                    if already_has_language and not is_copy:
                        continue

                    msg('Updating {} for {}, is_copy {}'.format(key, lang, is_copy))
                    n = RepoEntry(host=old.host,
                                  id=old.id,
                                  path=old.path,
                                  description=old.description,
                                  readme=old.readme,
                                  copy_of=is_copy,
                                  owner=old.owner,
                                  owner_type=old.owner_type,
                                  languages=languages,
                                  deleted=is_deleted,
                                  topics=old.topics,
                                  categories=old.categories)
                    db[key] = n
                    count += 1
                    failures = 0
                if count % 100000 == 0:
                    msg('{} [{:2f}]'.format(count, time() - start))
                    set_language_list(entries_with_languages, db)
                    transaction.commit()
                    start = time()
        except Exception as ex:
            msg('Skipping {} because of parsing error: {}'.format(key, ex))
            failures += 1
            continue

    transaction.commit()
    # update_progress(1)
