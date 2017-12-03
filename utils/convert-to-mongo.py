#!/usr/bin/env python3.4

from database import *
import os
import sys
from pymongo import MongoClient

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
from reporecord import *
from database import *
from dbinterface import *


def convert_langs(entry):
    if not entry.languages:
        return (Lang.OTHER, [])
    orig_langs = entry.languages
    lang_bitmask = 0b0
    for lang in list(orig_langs):
        name = Language.name(lang)
        code = Lang.code(name)
        if code != Lang.OTHER:
            lang_bitmask |= code
            orig_langs.remove(lang)
    langs_left = []
    for lang in orig_langs:
        langs_left.append(Language.name(lang))
    return (lang_bitmask, langs_left)


def doit():
    database = Database()
    old_db = database.open()

    import ipdb; ipdb.set_trace()

    casicsdb = CasicsDB()
    github_db = casicsdb.open('github')
    new_db = github_db.repos

    for key in old_db.keys():
        if key == 0: continue
        entry = old_db[key]

        # Create a blank to preallocate space.
        new_db.insert_one(repo_entry(entry.id))

        # Create the real record.
        # Be careful about not accidentally changing "None" values.
        copy_of = None
        if entry.copy_of != True and entry.copy_of != None and entry.copy_of != False:
            copy_of = entry.copy_of
        is_fork = bool(entry.copy_of)
        (lang_bitmask, other_langs) = convert_langs(entry)
        new_entry = repo_entry(id=entry.id,
                               name=entry.name,
                               owner=entry.owner,
                               description=entry.description,
                               readme=entry.readme,
                               language_codes=lang_bitmask,
                               language_others=other_langs,
                               created=entry.created,
                               refreshed=entry.refreshed,
                               is_deleted=entry.deleted,
                               is_fork=is_fork,
                               fork_of=copy_of)

        # Finally, update the blank with the real values.
        new_db.replace_one({'_id' : entry.id}, new_entry)

        print(entry.id, flush=True)

    casicsdb.close()

doit()

# to do:
# - create indexes
