#!/usr/bin/env python3.4

import os
import pytest
import sys

myPath = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, myPath + '/../')

sys.path.append('..')
sys.path.append('../..')

from lang import *

# Unit tests.
# .............................................................................

def test_names():
    assert 'C'      == Lang.name(Lang.C)
    assert 'Python' == Lang.name(Lang.PYTHON)
    try:
        # Should get an error because Lang.name expects an int.
        assert 'Other'  == Lang.name('foo')
        assert False
    except:
        assert True


def test_codes():
    assert Lang.code('Perl') == Lang.PERL
    assert Lang.code('foo') == Lang.OTHER


def test_convert():
    assert Lang.convert('C') == Lang.C

    x = Lang.convert(['C', 'Java'])
    assert x > 0
    assert x & Lang.C

    x = Lang.convert(Lang.PYTHON + Lang.PHP)
    assert 'Python' in x

    x = Lang.convert(Lang.PYTHON + Lang.PHP + Lang.code('foo'))
    assert x == ['Python', 'PHP']
