#!/usr/bin/env python3.4
#
# @file    database.py
# @brief   Module to encapsulate connecting to our MongoDB database.
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
# The eventual goal is to have are separate databases for different hosting
# service such as GitHub, SourceForge, etc.  Currently we only have GitHub,
# though.  Within each database, there is a MongoDB "collection" for
# repositories named 'repos'.
#
# The class CasicsDB() below handles connections to the database.  Here is
# the simplest case of creating a connection to the server and opening the
# Github database:
#
#   connection = CasicsDB(server='X', port='Y', login='Z', password='W')
#   github_db = connection.open('github')
#
# Then, to get ahold of a collection like the repository collection, access
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
# (Note that the value of the identifier here is an integer, not a string.)
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
#  repos.find({'owner': 'mhucka', 'languages.name': 'Python'})
#
# When you use multiple key:value pairs in one query, MongoDB treats it as an
# implicit "and" operation, so the above returns entries that have both an
# 'owner' value of 'mhucka' and 'Python' in one of the languages array names.
#
# The next example does a logical-and search for "sbml" and "java" in all
# indexed text fields, which for the current 'github' database are the
# "description" and the "readme" fields.  Part of this is really not obvious:
# the reason it's interpreted as a logical-and instead of logical-or is the
# fact that the two words are in double quotes.  If "sbml" and "java" were
# unquoted, it would be interpreted as a logical-or instead.
#
#  repos.find( {'$text': {'$search': '"sbml" "java"'}})
#
# The following web page has a list of the available query operators:
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
# _id              string      identifier of repo (e.g., 14344655)
# owner            string      owner name
# name             string      name of the repo
# description      string      description field in GitHub entry
# readme           string      README file in GitHub, as a text string
# text_languages   array       (human) languages used in description & readme
# is_deleted       bool        whether it's now listed by GitHub as deleted
# is_visible       bool        False if private or not visible for any reason
# default_branch   string      default branch according to GitHub
# homepage         string      not on github.com, but separate home pg if given
# time             dictionary  has the form
#                                 {'repo_created': timestamp,
#                                  'repo_pushed': timestamp,
#                                  'repo_updated': timestamp,
#                                  'data_refreshed': timestamp }
# fork             dictionary  has the form
#                                 {'parent': 'someOwner/someName',
#                                  'root': 'someOtherOwner/someOtherName' }
# languages        array       array of values of the form
#                                 [{'name': 'string'},
#                                  {'name': 'string'}, ... ]
# files            array       array of strings listing top level files/dirs
# content_type     string      array of values of the form
#                                 [{‘content’: type, ‘basis’: method},
#                                  {‘content’: type, ‘basis’: method}, ...]
# topics           array       has the form
#                                 {'lcsh': ['string', 'string, ...]}
#                              and may have more keys besides 'lcsh' if we
#                              use terms from other ontologies.
# functions        array       TBD
# licenses         array       array of values of the form
#                                 [{'name': 'LGPL'}, ...]
#
# About the representation of languages
# .....................................
#
# The languages used in the files of a repository are stored in the field named
# 'languages'.  The field can have three possible values:
#
#   - a non-empty array: the languages used in the repo
#   - an empty array: this means we have not tried to get languages
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
# Finally, it's possible the values are actually incorrect.  The software used
# by GitHub (a program called Linguist) is known to be imperfect.
#
# When the value is an array of languages, it has a slightly peculiar structure:
#
#  'languages': [{'name': 'Python'}, {'name': 'Java'}]
#
# The extra level of dictionaries is currently unnecessary but gives us
# flexibility if we ever want to attach info besides the language name.
# Operationally, what this structure means is that to use operators such as
# find() on the language field, the query must use dotted notation to the to
# the 'name' part.  Here's an example:
#
#  results = repos.find( {'languages.name': 'Java' } )
#
# To find all repositories that mention *either* of two or more languages,
# a convenient approach is to use the "$in" operator:
#
#  results = repos.find( {'languages.name': { '$in': ['Matlab', 'C'] }} )
#
# Note: the reason our field is named 'languages' (plural) instead of
# 'language' is because MongoDB treats a field named 'language' specially:
# it's used to determine the human language to assume for text indexing.  If
# a field named 'language' exists but is actually meant for a different
# purpose, then some operations fail in obscure ways unless one goes through
# some contortions to make it work.  So to save the hassle, our field is
# named 'languages'.
#
#
# About the 'readme' field
# ........................
#
# The 'readme' field is the content of a README file of some kind, if one
# exists.  The possible values of this field are:
#   * None if we have not tried to get it
#   * '' if we tried and it exists, but it was an empty file
#   * -1 if we tried but no README file exists
#   * -2 if we tried and it does exist, but it's garbage
#   * a string, if we obtained README file content.
#
#
# About the 'files' field
# .......................
#
# It is too expensive (in terms of time) to recursively get the list of files
# for all repositories, so we only try to get the top-level list of files and
# subdirectories.  The field 'files' is a list of the files found at the top
# level in the default branch of the repository.  Directory names will have a
# trailing '/' in their names, as in "somedir/".
#
# If we have no info about the files in the repo (which happens if we have
# not yet tried to get the data), 'files' will be [].  If we know the
# repository is empty (i.e., has no files), the value will be -1.
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


# Database entry template.
# -----------------------------------------------------------------------------

def repo_entry(id,
               name=None,
               owner=None,
               description=None,
               readme=None,
               text_languages=[],
               languages=[],
               licenses=[],
               files=[],
               content_type=[],
               kind=[],
               interfaces=[],
               topics=[],
               functions=[],
               num_commits=None,
               num_releases=None,
               num_branches=None,
               num_contributors=None,
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
    '''Creates a repo record, with blank values for uninitialized fields.

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

      'text_languages' is a list of human languages present in the description
      and/or readme fields.  The values are ISO 639-1 codes, such as 'en' for
      English and 'zh' for Chinese.  There can be more than one value if we
      detect more than one language used, or if the description and the readme
      fields use different languages.  A value of [] means we have not tried to
      infer the languages; a value of -1 means we tried but failed, perhaps
      because the text is missing or too short to make automated inferences.

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
      a fork but don't have more info than that.  Basically, callers should
      query against [] to find out if something is a for or not, and when
      look for more details about forks, query fields like 'fork.parent' or
      'fork.root' to find out what we know.  If we have full details on the
      fork, then both fields will have values.  If the fork is a single level,
      the values will be the same (i.e., parent and root will be the same
      original repo).  If the fork is multiple levels, 'parent' is the 
      immediate parent and 'root' is the highest level parent.

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
      GitHub don't seem to have a value for this.

      'files' is a list of the files found at the top level in the default
      branch of the repository.  Directory names will have a trailing '/' in
      their names, as in "somedir/".  If we have no info about the files in
      the repo, 'files' will be [].  If we know the repository is empty,
      the value will be -1.

      'num_commits' is the number of commits ever made to this repository.
      'num_contributors' is the number of contributors to this repository.
      'num_branches' is the number of branches in the repository.
      'num_releases' is the number of releases ever made using GitHub's
      release-making system.  (These numbers are shown below the description
      of a project, on the project's web page on GitHub.)

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

      'kind' refers to what kind of software it is: library, application,
      etc.  It can be either [] if we don't know or have not assigned a
      value, or a list of terms:
        ['term', 'term', ...]
      The terms are taken from our "software kind" subontology.

      'interfaces' refers to the types of interfaces offered by the software.
      It can be either [] if we don't know or have not assigned a value, or a
      list of terms:
        ['term', 'term', ...]
      The terms are taken from our "interfaces" subontology.

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
        fork_field = make_fork(fork_of, fork_root)
    if not topics:
        topics = make_topics('lcsh', [])
    entry = {'_id'              : id,
             'owner'            : owner,
             'name'             : name,
             'description'      : description,
             'readme'           : readme,
             'text_languages'   : text_languages,
             'languages'        : languages,
             'licenses'         : licenses,
             'files'            : files,
             'content_type'     : content_type,
             'kind'             : kind,
             'interfaces'       : interfaces,
             'topics'           : topics,
             'functions'        : functions,
             'num_commits'      : num_commits,
             'num_releases'     : num_releases,
             'num_branches'     : num_branches,
             'num_contributors' : num_contributors,
             'is_visible'       : is_visible,
             'is_deleted'       : is_deleted,
             'fork'             : fork_field,
             'time'             : {'repo_created'   : created,
                                   'repo_updated'   : last_updated,
                                   'repo_pushed'    : last_pushed,
                                   'data_refreshed' : data_refreshed },
             'default_branch'   : default_branch,
             'homepage'         : homepage
            }
    return entry


# Utility functions for dealing with repo entries.
# -----------------------------------------------------------------------------

def e_path(entry):
    '''Given an entry, return a full path of the form "owner/repo-name".'''
    return entry['owner'] + '/' + entry['name']


def e_summary(entry):
    '''Summarize the full path and id number of the given entry.'''
    summary = '{} (#{})'.format(e_path(entry), entry['_id'])
    return summary.encode(sys.stdout.encoding, errors='replace').decode('ascii')


def e_languages(entry):
    '''Return the list of languages as a plain list of strings.'''
    if not entry['languages']:
        return []
    elif entry['languages'] == -1:
        return -1
    elif isinstance(entry['languages'], list):
        return [lang['name'] for lang in entry['languages']]
    else:
        # This shouldn't happen.
        return entry['languages']


def make_fork(fork_parent, fork_root):
    return {'parent' : fork_parent, 'root' : fork_root}


def make_languages(langs):
    '''Create a list of 'name':language dictionary pairs.'''
    langs = [langs] if not isinstance(langs, list) else langs
    return [{'name': lang} for lang in langs]


def make_content_type(content, method='file names'):
    '''Create a dictionary element suitable as a single content_type value.'''
    return {'content': content, 'basis': method}


def make_topics(ontology, topics):
    return {ontology: topics}


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
