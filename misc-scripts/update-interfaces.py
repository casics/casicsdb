#!/usr/bin/env python3.4

import sys
import time

sys.path.append('..')
sys.path.append('../common')
sys.path.append('../../common')
from casicsdb import *
from utils import *

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

# Add new fields for content_type
# .............................................................................

def replace(old, new):
    repos.update_many({'interfaces': old}, {'$addToSet': {'interfaces': new}})
    repos.update_many({'interfaces': old}, {'$pull': {'interfaces': old}})

replace('function/method/class library interface', 'function/class library interface')
replace('function call interface', 'function/class library interface')
replace('class library interface', 'function/method/class library interface')
replace('network interface', 'network communications interface')
replace('WebSockets', 'WebSocket')
replace('internet sockets', 'network sockets')
replace('web services', 'web services interface')
replace('remote procedure call', 'RPC/RMI interface')
replace('remote method invocation', 'RPC/RMI interface')
