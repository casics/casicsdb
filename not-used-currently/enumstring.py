#!/usr/bin/env python3.4
#
# @file    enumstring.py
# @brief   EnumeratedString base class
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Originally I used the Enum class introduced in Python 3.4, but found it was
# too easy to accidentally store the full objects instead of the identifiers
# for the enum values.  Later I needed a way to map strings to values, and
# finally gave up on using the Enum class in favor of this simple approach.

class EnumeratedStrings():
    '''Base class for simple string enumerations.  Subclasses need to define
    a class constant named "_name", which is a dictionary mapping integer
    values to strings.'''

    @classmethod
    def name(cls, val):
        '''Given an identifier, returns the corresponding name as a string.
        Examples:
            Language.name(Language.CPLUSPLUS) => "C++"
            Language.name(43) => "C++"
        '''
        if not isinstance(val, int):
            raise EnumerationValueError('Expected an integer but got "{}"'.format(val))
        if not hasattr(cls, '_last_key'):
            cls._last_key = sorted(cls._name.keys())[-1]
        if val >= 0 and val <= cls._last_key:
            return cls._name[val]
        else:
            raise EnumerationValueError('Unknown language identifier {}'.format(val))


    @classmethod
    def identifier(cls, val):
        '''Given a string, returns the corresponding value.  If the language
        string is not recognized, returns 0.
        Examples:
            Language.identifier("C++") => 43
            Language.name(43) => "C++"
            Language.name(Language.CPLUSPLUS) => "C++"
        '''
        if not isinstance(val, str):
            raise EnumerationValueError('Expected a string but got "{}"'.format(val))
        for identifier, string in cls._name.items():
            if val == string:
                return identifier
        return 0
