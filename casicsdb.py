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
# And that's it -- the variable `repos` will be a MongoDB collection with
# normal MongoDB operations available.  The first thing to know is that every
# GitHub repository in this collection has a unique numeric identifier.  The
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
# This time, the value of `results` will be an iterator (known as a "Cursor" in
# Mongo).  You can iterate over each result in a standard Python way such as
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
# languages        array       array of values of the form
#                                 [{'name': 'string'},
#                                  {'name': 'string'}, ... ]
# licenses         array       array of values of the form
#                                 [{'name': 'LGPL'}, ...]
# time             dictionary  has the form
#                                 {'repo_created': timestamp,
#                                  'repo_pushed': timestamp,
#                                  'repo_updated': timestamp,
#                                  'data_refreshed': timestamp }
# fork             dictionary  has the form
#                                 {'parent': 'someOwner/someName',
#                                  'root': 'someOtherOwner/someOtherName' }
# files            array       array of strings
# content_type     string      array of values of the form
#                                 [{‘content’: type, ‘basis’: method},
#                                  {‘content’: type, ‘basis’: method}, ...]
# topics           array       has the form
#                                 {'lcsh': ['string', 'string, ...]}
#                              and may have more keys besides 'lcsh' if we
#                              use terms from other ontologies.
# functions        array       TBD
# is_deleted       bool        whether it's now listed by GitHub as deleted
# is_visible       bool        False if private or not visible for any reason
# default_branch   string      default branch according to GitHub
# homepage         string      not the github.com page, but a different one, if
#                              a project's record in GitHub lists one
#
# In our database, the name of a user in a repo entry is also the key of that
# user in collection 'users'.  So to find out more info about a user beyond
# the name, look up the user in the 'users' collection.
#
#
# About the representation of languages
# .....................................
#
# The languages used in the files of a repository are stored in the field named
# 'languages'.  The field can have three possible values:
#
#   - a non-empty array: the languages used in the repo
#   - an empty array: this means we have not tried to get language the
#   - info value -1: we tried to get language info but Github didn't give any
#
# The last case (-1) can happen for real repositories that have files;
# sometimes GitHub just doesn't seem to record language info for some repos,
# and other times the repository is empty or has no programming language files.
# We mark it in our database so that we don't keep trying fruitlessly to
# retrieve the info when it's not there, but it does not mean that the repo
# does not have files that could be analyzed -- it *might*.
#
# It is also worth keeping in mind that the list of languages we *do* have (if
# we have it) may be incomplete: a repo may use more languages than what we
# have listed, depending on how we got the info and how complete it was.
# Also, it's possible the repo has changed since we retrieved the info.
#
# When the value is an array of languages, it has a slightly peculiar structure:
#
#  'languages': [{'name': 'Python'}, {'name': 'Java'}]
#
# The extra level of dictionaries is unnecessary for our needs but this
# approach is actually conventional in MongoDB.  The result is that to use
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
# Note: the reason our field is named 'languages' instead of 'language' is
# because MongoDB treats a field named 'language' specially: it uses it to
# determine the human language to assume for text indexing.  If a field named
# 'language' exists but is actually meant for a different purpose, then some
# operations fail in obscure ways unless one goes through some contortions to
# make it work.  So to save the hassle, our field is named 'languages'.
#
#
# About the 'time' field
# ......................
#
# The 'time' field contains a dictionary of 4 values.  The 'data_refreshed'
# subfield refers to our database entry, and is changed whenever we change
# something about the entry in our database.  The separate subfields
# 'repo_updated' and 'repo_pushed' merit further explanation.  The need for
# these two fields is due to the following explanation by a GitHub
# representative in a Stack Overflow answer at
# http://stackoverflow.com/a/15922637/743730 --
#
#   "'pushed_at' [the equivalent of our 'repo_pushed'] will be updated any
#   time a commit is pushed to any of the repository's branches. 'updated_at'
#   [the equivalent of our 'repo_updated'] will be updated any time the
#   repository object is updated, e.g. when the description or the primary
#   language of the repository is updated. It's not necessary that a push
#   will update the updated_at attribute -- that will only happen if a push
#   triggers an update to the repository object. For example, if the primary
#   language of the repository was Python, and then you pushed lots of
#   JavaScript code -- that might change the primary language to JavaScript,
#   which updates the repository object's language attribute and in turn
#   updates the updated_at attribute."
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

def repo_entry(id,
               name=None,
               owner=None,
               description=None,
               readme=None,
               languages=[],
               licenses=[],
               files=[],
               content_type=[],
               topics=[],
               functions=[],
               default_branch=None,
               homepage=None,
               is_deleted=None,
               is_visible=None,
               is_fork=None,
               fork_of=None,
               fork_root=None,
               created=None,
               last_updated=None,
               last_pushed=None,
               data_refreshed=None
              ):
    '''Creates a repo record, blank if field values are not given.

    GENERAL NOTES:

      The general principles for the field values are the following:
        * None or [] means we don't know (we haven't tried to get it yet)
        * a negative value mean we tried to get it, but it doesn't exist
        * a positive or content value is the value in question
        * a value of '' is a legitimate possible value.

    SPECIFIC NOTES ABOUT DIFFERENT FIELDS:

      'description' is the description field for repositories in GitHub.  The
      possible values here are:
        * None if we never tried to obtain it
        * '' if we obtained it but the description field was empty
        * a string if the description field has a value.

      'readme' is the content of a README file of some kind, if one exists.
      The possible values of this field are:
        * None if we have not tried to get it
        * '' if we tried and it exists, but it was an empty file
        * -1 if we tried but no README file exists
        * -2 if we tried and it does exist, but it's garbage
        * a string, if we obtained README file content.

      'is_visible' is False for entries that we somehow (perhaps during a
      past indexing run, or perhaps from a GHTorrent dump) added to our
      database at one time, but that we know we can no longer access on
      GitHub.  This may happen for any of several reasons:
        * GitHub returns http code 451 (access blocked)
        * GitHub returns code 403 (often "problem with this repository on disk")
        * GitHub returns code 404 when you go to the repos' page on GitHub
        * we find out it's a private repo
      If we don't know whether a repo is visible or not, 'is_visible' == None.

      'is_deleted' is True if we know that a repo is reported to not exist in
      GitHub.  This is different from 'is_visible' because we don't always
      know whether something has been deleted -- sometimes all we know is
      that we can't find it on github.com, yet another source (such as the
      API) still reports it exists.  Another case where we mark something as
      is_deleted == False but is_visible == True is when we get a code 451 or
      403 during network accesses, because this means the repo entry does
      still exist -- we just can't see it anymore.  Note that in all cases,
      a value of is_deleted == True means is_visible == False.  If we don't
      know whether it is deleted, 'is_deleted' == None.

      'fork' has the value False when we know it's NOT a fork, the value []
      when we don't know whether a repo is a fork or not, and a dictionary
      with the following fields when we know it IS a fork:
        'parent': the parent repo from which this is a fork
        'root': the original repo, if this is a fork of a fork
      Note that the values of the fields in 'fork' can be None if we don't
      know them, which can happen in cases when all we know is that a repo is
      a fork but don't have more info than that.  Basically, what this means
      is that callers should query against [] to find out if something is a
      for or not, and when look for more details about forks, query fields
      like 'fork.parent' or 'fork.root' to find out what we know.

      'time' is a dictionary with the following fields; all values are in UTC
      and are stored as floating point numbers:
        'repo_created': time stamp for the creation of the repo on GitHub
        'repo_pushed': last time a push was made to the git repo
        'repo_updated': last modification to the entry in GitHub
        'data_refreshed': when we last updated this record in our database
      The reason for two 'repo_pushed' and 'repo_updated' is this: GitHub
      tracks changes to the git repository separately from changes to the
      project entry at github.com.  The project entry will be updated only
      when the repository information is updated for some reason, e.g., when
      the description or the primary language of the repository is updated.
      Changes to the git contents will not necessarily trigger a change to
      to 'repo_updated' date in GitHub.

      'languages' is a list of programming languages found in the source code
      of the repository.  The field can have one of three possible values:
        * an empty array: this means we have not tried to get language info
        * the value -1: we tried to get language info but it doesn't exist
        * a non-empty array: the languages used in the repo (see below)

      The case of languages == -1 can happen for real repositories that have
      files.  Sometimes GitHub just doesn't seem to record language info for
      some repos, and other times, the repository is empty or has no
      programming language files per se.  We mark these cases as -1 in our
      database so that we don't keep trying fruitlessly to retrieve the info
      when it's not there, but it does not mean that the repo does not have
      files that could be analyzed -- it *might*.  We just know that we
      couldn't get it the last time we tried.

      When the value is an array of languages, it has this structure:
        'languages': [{'name': 'Python'}, {'name': 'Java'}]
      Currently, all we store with each language is the name, but we may
      expand this in the future.  To use operators such as find() on the
      language field, the query must use dotted notation.  Example:
         results = repos.find( {'languages.name': 'Java' } )
      To find all repositories that mention *either* of two or more languages,
      a convenient approach is to use the "$in" operator:
         results = repos.find( {'languages.name': { '$in': ['Matlab', 'C'] }} )

      'homepage' is the URL of a home page (usually a GitHub Pages page) if
      it is known.  This is NOT the path to the page on github.com -- it is a
      different home page for the project, if it has one.  Most entries in
      GitHub don't seem to have a value for this, and GitHub doesn't even
      seem to provide a direct way to set this field from the user-level GUI.
      It seems to get set only by creating a GitHub Pages site for a project,
      or else maybe using the API directly.

      'files' is a list of the files found at the top level in the default
      branch of the repository.  Directory names will have a trailing '/' in
      their names, as in "somedir/".  If we have no info about the files in
      the repo, 'files' will be [].  If we know the repository is empty,
      the value will be -1.

      'content_type' provides basic info about a repository.  It can be
      either [] if we don't know, or a list of elements, each of which is a
      dictionary of two terms:
         {'content': value, 'basis': method}
      There can be more than one such dictionary because we may try different
      methods of inferring the content, and each may produce different guesses.
      The "basis" can be 'file names' (to indicate it was determined by
      analyzing file names only), 'languages' (to indicate it was determined
      by anaylzing the languages reportedly used in the repository), or other
      strings yet to be determined for other possible methods or sources of
      evidence.  The "value" can be one of 2: 'code', or 'noncode'. The value
      'code' means we know it's software source code, and the value 'noncode'
      means we know it contains something other than source code.  "Other
      than source code" could be, for example, documents (even LaTeX code) or
      media files; the fundamental point is that the files are something
      other than software or files intended to generate runnable software.

      'topics' holds application area/topic ontology labels.  It is a
      dictionary in which the keys are ontology labels and their values are
      ontology terms (as strings).  For example, we are currently using the
      Library of Congress Subject Headings, so a value for this field
      might be: {'lcsh': ['sh85133180', 'sh85107318']}.

    '''
    if is_fork == False:
        fork_field = False
    elif not is_fork:
        fork_field = []
    else:
        fork_field = {'parent' : fork_of, 'root' : fork_root}
    if not topics:
        topics = {'lcsh': []}
    entry = {'_id'             : id,
             'owner'           : owner,
             'name'            : name,
             'description'     : description,
             'readme'          : readme,
             'languages'       : languages,
             'licenses'        : licenses,
             'files'           : files,
             'content_type'    : content_type,
             'topics'          : topics,
             'functions'       : functions,
             'is_visible'      : is_visible,
             'is_deleted'      : is_deleted,
             'fork'            : fork_field,
             'time'            : {'repo_created'   : created,
                                  'repo_updated'   : last_updated,
                                  'repo_pushed'    : last_pushed,
                                  'data_refreshed' : data_refreshed },
             'default_branch'  : default_branch,
             'homepage'        : homepage
            }
    return entry
