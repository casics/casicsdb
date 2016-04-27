#!/usr/bin/env python3.4
#
# @file    database.py
# @brief   Simple module to encapsulate connecting to our MongoDB database.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# The organization of the database
# ................................
#
# There are separate databases for different hosting service such as GitHub,
# SourceForge, etc.  (Currently we only have GitHub, though.)  Within each
# database, there is a MongoDB "collection" for repositories (named 'repos'),
# another collection for users (named 'users'), and maybe more in the future.
#
# The class CasicsDB() below handles connections to the database.  Here is
# the simplest case of creating a connection to the server and opening the
# Github database:
#
#   connection = CasicsDB(server='X', port='Y', login='Z', password='W')
#   github_db = connection.open('github')
#
# Then, to get ahold of a collection, like the repository collection, access
# it like a field on the object.  For the repos, the field is named '.repos':
#
#   repos = github_db.repos
#
# And that's it -- the variable `repos` is a MongoDB collection with normal
# MongoDB operations available.  The first thing to know is that every GitHub
# repository in this collection has a unique numeric identifier.  The
# database is set up to use that as the value of the MongoDB `_id` field.  So
# to find a repo with the id 16335, you can do
#
#   entry = repos.find_one( { '_id' : 16335 } )
#
# The fields stored with each entry are described in the next section below.
# You can access the fields as dictionary elements: entry['name'] gives the
# name, entry['description'] gives the description, etc.  Here is a more
# complicated example, to find all repositories that are known to use Python:
#
#   results = repos.find( {'languages.name': 'Python' } )
#
# This time, the value of `results` will be an iterator (a "Cursor" in
# pymongo).  You can iterate over each result in a standard Python way such
# as
#
#   for entry in results:
#      ... do something with entry ...
#
# Finally, here are some examples of using text search.  This first one
# finds all the repositories with "mhucka" as the owner and "Python" listed
# as one of the programming languages:
#
#  repos.find({'$and': [ {'owner': 'mhucka'}, {'languages.name': 'Python'} ] })
#
# The next one does a logical-and search for "sbml" and "java" in all indexed
# text fields, which for the current 'github' database are the "description"
# and the "readme" fields.  (The reason it's interpreted as a logical-and
# instead of logical-or is the fact that the two words are in double quotes.
# If they were unquoted, it would be interpreted as a logical-or instead.)
# Note: this will take approx 1.5 hrs to complete:
#
#  repos.find( {'$text': {'$search': '"sbml" "java"'}})
#
# The following page has a list of the available query operators:
# https://docs.mongodb.org/manual/reference/operator/query/
#
#
# Fields in repo entries
# ......................
#
# Each entry in a collection (known as a "document" in MongoDB parlance) has
# the folllowing fields:
#
# Field name       Mongo type  Purpose/meaning
# ----------       ----------  ---------------
# _id              string      identifier of repo (e.g., "14344655")
# name             string      name of the repo
# owner            string      owner name; also is key into collection['users']
# description      string      description field in GitHub entry
# readme           string      README file in GitHub, as plain text
# languages        array       has the form [{'name': 'C'}, {'name': 'R'}, ...]
# created          date        time of creation in GitHub, according to them
# refreshed        date        time of our last update for this entry
# is_deleted       bool        whether it's now listed by GitHub as deleted
# is_fork          bool        empty if unknown, true if known to be fork
# fork_of          string      a repo_id if we know what this is a fork of
# default_branch   string      default branch according to GitHub
# archive_url      string      archive URL according to GitHub
#
# In our database, the name of a user in a repo entry is also the key of that
# user in collection 'users'.  So to find out more info about a user beyond
# the name, look up the user in the 'users' collection.
#
#
# About the representation of languages
# .....................................
#
# The languages used in the files of a repository are stored as an array with
# a slightly peculiar structure, as in this example:
#
#  'languages': [{'name': 'Python'}, {'name': 'Java'}]
#
# This style is actually conventional in MongoDB.  The result is that to use
# operators such as find() on the language field, the query must use dotted
# notation to the to the 'name' part.  Here's an example:
#
#  results = repos.find( {'languages.name': 'Java' } )
#
# To find all repositories that mention *either* of two or more languages,
# a convenient approach is to use the "$in" operator:
#
#  results = repos.find( {'languages.name': { '$in': ['Matlab', 'C'] }} )
#
# Note: the reason the field is named 'languages' instead of 'language' is
# because MongoDB treats a field named 'language' specially: it uses it to
# determine the human language to assume for text indexing.  If a field named
# 'language' exists but is actually meant for a different purpose, then some
# operations fail in obscure ways unless one goes through some contortions to
# make it work.  So to save the hassle, our field is named 'languages'.
#
#
# About the representation of time stamps
# .......................................
# Mongo date & time objects are in UTC.  (See here for examples:
# https://api.mongodb.org/python/current/examples/datetimes.html)
# However, those objects take up 48 bytes.  It is possible to store date/time
# values as floats, and they only take up 24 bytes.  Since every entry in the
# database has at least 2 dates, that means we can save 48 * 25,000,000 bytes
# = 1.2 GB (at least) by storing them as floats instead of the default date
# objects.  So, that's how they're stored.  See ../common/utils.py for some
# functions that make it easier to work with this.
#
#
# Additional references about mongodb types and tips:
# ...................................................
# https://www.rainforestqa.com/blog/2012-11-05-mongodb-gotchas-and-how-to-avoid-them/
# https://www.mongosoup.de/blog-entry/Storing-Large-Lists-In-MongoDB.html
# https://www.quora.com/Is-string-more-storage-efficient-than-integer-in-64-bit-MongoDB
# http://stackoverflow.com/questions/27351143/how-should-i-store-boolean-values-in-mongodb
# http://stackoverflow.com/questions/11634601/mongodb-null-field-or-true-false
# http://stackoverflow.com/questions/18837486/query-for-boolean-field-as-not-true-e-g-either-false-or-non-existent

import os
import sys
from pymongo import MongoClient
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))

try:
    from .utils import *
except:
    from utils import *


# CasicsDB interface class
# -----------------------------------------------------------------------------
# This class encapsulates interactions with MongoDB.  Callers should create a
# CasicsDB() object, then call open() on the object.

class CasicsDB():
    connect_timeout = 15000          # in milliseconds

    def __init__(self, server=None, port=None, login=None, password=None,
                 quiet=False):
        '''Reads the configuration file but does not open the database.
        If parameters "server", "port", "login" and "password" are provided,
        it will not read them from the configuration file.  Otherwise, it
        will look for a "mongodb.ini" file in this directory or in ../common/.
        If parameter "quiet" is non-False, it will be less chatty.
        '''
        # Read config & set ourselves up.
        if server and port:
            self.dbserver = server
            self.dbport   = int(port)
        else:
            cfg = None
            try:
                cfg = Config('mongodb.ini')
            except:
                try:
                    cfg = Config('../common/mongodb.ini')
                except:
                    pass
            if cfg:
                self.dbserver = cfg.get('MongoDB', 'dbserver')
                self.dbport   = int(cfg.get('MongoDB', 'dbport'))
            else:
                raise RuntimeError('no mongodb.ini and no parameters given')

        self.quiet      = quiet
        self.dblogin    = None
        self.dbpassword = None
        if login:
            self.dblogin    = login
        if password:
            self.dbpassword = password
        if not self.dblogin and not self.dbpassword:
            try:
                self.dblogin    = cfg.get('MongoDB', 'login')
                self.dbpassword = cfg.get('MongoDB', 'password')
            except:
                raise RuntimeError('Must provide user login and password')
        self.dbconn     = None


    def open(self, dbname):
        '''Opens a connection to the database server and either reads our
        top-level element, or creates the top-level element if it doesn't
        exist in the database.  Returns the top-level element.'''

        if not self.dbconn:
            if not self.quiet: msg('Connecting to {}.'.format(self.dbserver))
            self.dbconn = MongoClient(
                'mongodb://{}:{}@{}:{}'.format(self.dblogin, self.dbpassword,
                                               self.dbserver, self.dbport),
                connectTimeoutMS=CasicsDB.connect_timeout, maxPoolSize=25,
                tz_aware=True, connect=True, socketKeepAlive=True)

        # The following requires that the user has the role dbAdminAnyDatabase
        if dbname not in self.dbconn.database_names():
            if not self.quiet: msg('Creating new database "{}".'.format(dbname))
            self.db = self.dbconn[dbname]
            self.dbconn.fsync()
        else:
            if not self.quiet: msg('Accessing existing database "{}"'.format(dbname))
            self.db = self.dbconn[dbname]

        return self.db


    def close(self):
        '''Closes the connection to the database.'''
        self.dbconn.close()
        if not self.quiet: msg('Closed connection to "{}".'.format(self.dbserver))


    def info(self):
        '''Return info about the database server.'''
        return self.dbconn.server_info()


# Database templates
# -----------------------------------------------------------------------------

# This preallocates fields with data objects, for database efficiency.  It's
# not required when using Mongodb, but doing this is said to improve efficiency
# when Mongo updates a record, reducing the probability that it will have to
# relocate the data object because it doesn't fit in its existing location.
# The actual sizes of the fields can be anything once the real document is
# created -- they are not at all constrained to the sizes allocated here.

def repo_entry(id, name='-'*16, owner='-'*16, description='-'*512,
               readme='-'*2048, languages=[],
               created=canonicalize_timestamp(0.0),
               refreshed=canonicalize_timestamp(0.0),
               is_deleted=None, is_fork=None, fork_of=None,
               default_branch=None, archive_url=None):
    '''Create a repo record, blank-padded if field values are not given.'''

    entry = {'_id'             : id,
             'owner'           : owner,
             'name'            : name,
             'description'     : description,
             'readme'          : readme,
             'languages'       : languages,
             'created'         : created,
             'refreshed'       : refreshed,
             'is_deleted'      : is_deleted,
             'is_fork'         : is_fork,
             'fork_of'         : fork_of,
             'default_branch'  : default_branch,
             'archive_url'     : archive_url }
    return entry
