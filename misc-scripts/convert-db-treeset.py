#!/usr/bin/env python3.4
#
# @file    convert-db-treeset.py
# @brief   One-off script to convert the language info structure to a TreeSet
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

import pdb
import sys
import os
import plac
from time import time
from BTrees.OOBTree import TreeSet

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
from utils import *
from dbinterface import *


# Main body.
# .............................................................................

def main():
    '''Create & manipulate index of projects found in repository hosting sites.'''
    convert()


def convert():
    db = Database()
    dbroot = db.open()
    msg('Converting ...')
    if '__ENTRIES_WITH_LANGUAGES__' in dbroot:
        entries_with_languages = TreeSet()
        entries_with_languages.update(dbroot['__ENTRIES_WITH_LANGUAGES__'])
        dbroot['__ENTRIES_WITH_LANGUAGES__'] = entries_with_languages
        transaction.commit()
    else:
        msg('No __ENTRIES_WITH_LANGUAGES__ entry?')

    db.close()
    msg('')
    msg('Done.')


# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
