#!/usr/bin/env python3.4
#
# @file    add-from-ghtorrent.py
# @brief   Add info we don't have, using a ghtorrent mysql dump.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Example lines from projects.csv:
#
# 1,"https://api.github.com/repos/tosch/ruote-kit",1,"ruote-kit","RESTful wrapper for ruote workflow engine","Ruby","2009-12-08 11:17:27",2,0
# 2,"https://api.github.com/repos/kennethkalmer/ruote-kit",4,"ruote-kit","RESTful wrapper for ruote workflow engine","Ruby","2009-06-10 20:32:21",\N,0
# 3,"https://api.github.com/repos/matplotlib/basemap",23,"basemap","","C++","2011-02-19 02:58:42",\N,0
# 4,"https://api.github.com/repos/jswhit/basemap",24,"basemap","","C++","2012-06-14 16:14:56",3,0
# 5,"https://api.github.com/repos/funkaster/cocos2d-x",28,"cocos2d-x","Port of cocos2d-iphone in C++","C++","2012-03-12 17:48:19",6,0
# 6,"https://api.github.com/repos/cocos2d/cocos2d-x",31,"cocos2d-x","Port of cocos2d-iphone in C++","C++","2010-11-18 23:17:00",\N,0
# 7,"https://api.github.com/repos/pixonic/cocos2d-x",42,"cocos2d-x","Port of cocos2d-iphone in C++","C","2012-04-23 12:20:29",6,0
# 8,"https://api.github.com/repos/NUBIC/ncs_navigator_core",65,"ncs_navigator_core","Case management and instrument administration for NCS Navigator","Ruby","2012-04-19 21:45:52",\N,0
# 9,"https://api.github.com/repos/sgonyea/rake-compiler",66,"rake-compiler","Provide a standard and simplified way to build and package Ruby C and Java extensions using Rake as glue.","Ruby","2012-08-01 20:33:51",28,0
# 10,"https://api.github.com/repos/chapuni/llvm",67,"llvm","Chapuni's branch based on http://llvm.org/git/llvm.git","C++","2011-02-01 09:11:48",\N,0
#
# Here's what the schema is documented as being:
#
# SET time_zone='+0:00';
# CREATE TABLE IF NOT EXISTS `ghtorrent`.`projects` (
#   `id` INT(11) NOT NULL AUTO_INCREMENT COMMENT '',
#   `url` VARCHAR(255) NULL DEFAULT NULL COMMENT '',
#   `owner_id` INT(11) NULL DEFAULT NULL COMMENT '',
#   `name` VARCHAR(255) NOT NULL COMMENT '',
#   `description` VARCHAR(255) NULL DEFAULT NULL COMMENT '',
#   `language` VARCHAR(255) NULL DEFAULT NULL COMMENT '',
#   `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '',
#   `forked_from` INT(11) NULL DEFAULT NULL COMMENT '',
#   `deleted` TINYINT(1) NOT NULL DEFAULT '0' COMMENT '',
#   `updated_at` TIMESTAMP NOT NULL DEFAULT '1970-01-01 00:00:01' COMMENT '',
#   PRIMARY KEY (`id`)  COMMENT '',
#   CONSTRAINT `projects_ibfk_1`
#     FOREIGN KEY (`owner_id`)
#     REFERENCES `ghtorrent`.`users` (`id`),
#   CONSTRAINT `projects_ibfk_2`
#     FOREIGN KEY (`forked_from`)
#     REFERENCES `ghtorrent`.`projects` (`id`))
# ENGINE = InnoDB
# DEFAULT CHARACTER SET = utf8;
# SET time_zone=@OLD_TIME_ZONE;


import sys
import plac
import os
import csv
from time import time, sleep

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

msg('Opening database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

# The GHTorrent CSV projects.csv file has an "id" as the first column, but
# I believe that's the id for the entry in the table and not github's id
# for the repository.  We don't reference this in our database.

fields = {'id'          : 0,            # Don't use this -- no the repo id.
          'url'         : 1,
          'owner'       : 2,
          'name'        : 3,
          'description' : 4,
          'language'    : 5,
          'created'     : 6,
          'forked_from' : 7,
          'deleted'     : 8,
          'updated'     : 9}

namestart = len('https://api.github.com/repos/')
id_map = {}

# Read the file once and build a mapping from their identifiers to project
# owner/name path strings.  We need this because we have to match up their
# id's when they say a project is a fork of another project.

msg('Building project id mapping')
with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    for row in reader:
        id   = row[fields['id']]
        if id == '-1':
            continue
        path = row[fields['url']][namestart:]
        id_map[id] = path
        count += 1
        if count % 10000 == 0:
            msg(count)

msg('Processing {} for real.'.format(sys.argv[1]))
with open(sys.argv[1], encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    start = time()
    for row in reader:
        id   = row[fields['id']]
        if id == '-1':
            continue
        count += 1

        path        = row[fields['url']][namestart:]
        desc        = row[fields['description']]
        lang        = row[fields['language']]
        forked_from = row[fields['forked_from']]
        created     = row[fields['created']]
        deleted     = row[fields['deleted']]
        updated     = row[fields['updated']]

        owner       = path[:path.find('/')]
        name        = path[path.find('/') + 1:]
        is_fork     = True if forked_from != 'N' else False
        is_deleted  = True if deleted != '0' else False

        entry = repos.find_one({'owner': owner, 'name': name})

        if not entry:
            # We need to deal with these using our cataloguer.
            msg('*** Unknown entry {}'.format(path))
            continue

        # We gather up changes and issue a single update command for an entry.

        updates = {}

        # If GHTorrent says something is a fork and we don't have it that way
        # in our database, then it is very unlikely that it is *not* a fork.
        # Trust GHTorrent on this.  Unfortunately, the GHTorrent data about
        # the fork source is in terms of their id numbers, not github's, so
        # we can only update it if we can find the id in the map we create.

        if is_fork and not entry['fork'] and forked_from in id_map:
            msg('Updating is_fork for {}'.format(path))
            fork = {}
            fork['parent'] = id_map[forked_from]
            fork['root'] = ''           # It's not in projects.csv.
            updates['fork'] = fork

        # If GHTorrent knows something has been deleted, it's probably
        # a good bet that it has not been reverted somehow.

        if is_deleted and not entry['is_deleted']:
            msg('Marking {} as deleted'.format(path))
            updates['is_deleted'] = True
            updates['is_visible'] = False

        # If we find it in projects.csv, call it visible if we didn't already.

        if not is_deleted and not entry['is_visible']:
            msg('Marking {} as visible'.format(path))
            updates['is_visible'] = True
        elif entry['is_visible'] == '':
            updates['is_visible'] = not(is_deleted)

        # If GHTorrent has language info for an entry and we don't,
        # take GHTorrent's value.  However, since GHTorrent's
        # projects.csv only lists 1 language for a project, don't
        # replace what we have in our database if we have something
        # for an entry already.

        if lang and lang != 'N' and (not entry['languages'] or entry['languages'] == -1):
            msg('Updating languages for {} with {}'.format(path, lang))
            updates['languages'] = [{'name':lang}]

        # If GHTorrent has a description and we don't, use theirs.  However,
        # if we have a description, don't overwrite it because ours might be
        # more recently-updated one than theirs.

        if desc and (not entry['description'] or entry['description'] == -1):
            msg('Updating description for {}'.format(path))
            updates['description'] = desc

        # If GHTorrent has a creation date and we don't, use theirs.
        # Ditto for update date.  The projects.csv files don't have pushed
        # times, unfortunately, so we use whatever we have already.

        time_dict = {}                  # Don't call this variable "time".
        if created and created != '0000-00-00 00:00:00' and not entry['time']['repo_created']:
            msg('Updating creation date for {}'.format(path))
            time_dict['repo_created'] = canonicalize_timestamp(created)
        if updated and updated != '0000-00-00 00:00:00' and not entry['time']['repo_updated']:
            msg('Updating update date for {}'.format(path))
            time_dict['repo_updated'] = canonicalize_timestamp(updated)
        if time_dict:
            # If we're updating any part of the time field, we have to update
            # all of it.  We use existing values if we don't have new ones.
            time_dict['repo_pushed'] = entry['time']['repo_pushed']
            time_dict['data_refreshed'] = now_timestamp()
            if 'repo_created' not in time_dict:
                time_dict['repo_created'] = entry['time']['repo_created']
            if 'repo_updated' not in time_dict:
                time_dict['repo_updated'] = entry['time']['repo_updated']
            updates['time'] = time_dict

        # Send the updates if there are any.

        if updates:
            repos.update_one({'_id': entry['_id']},
                             {'$set': updates},
                             upsert=False)

        if count % 1000 == 0:
            msg('{} [{:2f}]'.format(count, time() - start))
            start = time()

msg('Done')
