#!/usr/bin/env python3

import os
import re
import sys
import zlib

from datetime import datetime

sys.path.append('..')
sys.path.append('../../common')

from casicsdb import *
from utils import *

file = sys.argv[1]

with open(file, 'r') as f:
    for id in f.readlines():
        msg(generate_path('/srv/repositories', id.strip()))
