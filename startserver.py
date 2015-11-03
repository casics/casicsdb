#!/usr/bin/env python3.4
#
# @file    startserver.py
# @brief   Start a ZEO server for the ZODB database.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Basic principles
# ----------------
# ZEO is a client-server interface to ZODB: https://pypi.python.org/pypi/ZEO
# This very simple program reads our configuration file ("config.ini") to get
# the necessary connection parameters for the database, and then invokes the
# "runzeo.py" script provided by the Python ZEO distribution.  This script
# starts a ZEO server listening to a port on the local host.  The actual ZODB
# database is stored in a file which is handed to runzeo.py.  (This is the
# "dbfile" argument seen below.)
#
# Clients can connect to the ZEO port and read/write data in the database.
# There should be only one ZEO database process running for a given database.

import os
import sys
import plac
from subprocess import call

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
from utils import *


# Main body.
# .............................................................................

def main():
    try:
        cfg = Config()
        dbserver = cfg.get('global', 'dbserver')
        dbport = cfg.get('global', 'dbport')
        dbfile = cfg.get('global', 'dbfile')
        runzeo = cfg.get('global', 'runzeo')
    except Exception as err:
        raise SystemExit('Failed to read configuration variables from config file')

    try:
        portinfo = '{}:{}'.format(dbserver, dbport)
        msg('Starting server on', portinfo)
        os.system('python3.4 ' + runzeo + ' -a ' + portinfo + ' -f ' + dbfile)
    except PermissionError:
        msg('Permission error -- maybe something is using port {}?'.format(dbport))
    except Exception as err:
        msg(err)


# Entry point
# .............................................................................

def cli_main():
    plac.call(main)

cli_main()
