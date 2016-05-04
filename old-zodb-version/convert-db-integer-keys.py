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
from time import time
from BTrees.IOBTree import BTree

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from dbinterface import *
from utils import *
from reporecord import *


# Main body.
# .............................................................................
# Currently this only does GitHub, but extending this to handle other hosts
# should hopefully be possible.

def main():
    db = Database()

    # Get the original database root.
    origdb = db.open()

    # Create a new db as an IOBtree.
    newdb = BTree()

    # Convert everything.
    msg('Converting ...')
    start = time()
    count = 0
    for key, entry in origdb.items():
        count += 1
        if isinstance(entry, RepoEntry):
            newdb[entry.id] = entry
        if count % 100000 == 0:
            transaction.commit()
            msg('{} [{:2f}]'.format(count, time() - start))
            start = time()

    # Replace the original database.
    db.dbroot[db.dbname] = newdb
    transaction.commit()

    # Close up shop.
    db.close()
    msg('')
    msg('Done.')
    msg('')
    msg('Now run cataloguer -u.')
    msg('')


# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
