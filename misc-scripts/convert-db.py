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
    '''Create & manipulate index of projects found in repository hosting sites.'''
    convert()


def convert():
    db = Database()
    dbroot = db.open()
    msg('Converting ...')
    start = time()
    count = 0
    for key, entry in dbroot.items():
        pdb.set_trace()
        count += 1
        if isinstance(entry, RepoEntry):
            n = NewRepoEntry(Host.GITHUB,
                             entry.id,
                             entry.path,
                             entry.description,
                             '',
                             entry.owner,
                             entry.owner_type)
            dbroot[key] = n
        if count % 10000 == 0:
            # update_progress(i/count)
            transaction.savepoint(True)
        if count % 100000 == 0:
            transaction.commit()
            msg('{} [{:2f}]'.format(count, time() - start))
            start = time()
    transaction.commit()
    # update_progress(1)

    db.close()
    msg('')
    msg('Done.')


# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
