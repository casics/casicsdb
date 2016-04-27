#!/usr/bin/env python3.4
#
# @file    lang.py
# @brief   Programming languages
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# For efficiency reasons, programming language information is not stored as a
# simple list of language names in a repository documents.  Doing so would be
# insanely redundant: the name of every language used in every repository
# would be stored as a list of strings stored inside every repository
# document.  This would lead to gigabytes of bloat for no good reason.
#
# Instead, the approach here uses a bit mask to indicate the use of the most
# common 25 languages, and only use an array of strings if a repo uses other
# languages than those most common 25.  Language info is therefore stored in
# a 2-element subarray inside the repository document: a bit mask, and a list
# of strings for uncommon languages.  The codes are encapsulated in the class
# Lang inside lang.py.  The bitmask is used such that it stores a 1 bit for
# every language used (for the most common 25); so, e.g., if a given
# repository uses Java, Python and C++, the bitmask's value will be the
# logical-or of the Lang.code('Java') + Lang.code('Python') + Lang.code('C++').
# MongoDB even has bit-oriented operators, including the very convenient
# operator $bitsAnySet that can be used to match against any of the 1-bits in
# a bitmask.  Here's an example of finding all repositories that include Java:
#
#     repos.find( { 'languages.codes': { '$bitsAnySet': Lang.JAVA } } )
#
# The operation above takes 28 seconds for the current 25,000,000 entries.
# When the language is *not* one of the 25 predefined ones, the language gets
# stored as a list of strings under the language.others field.  E.g.,
#
#     [ 'Visual Basic', 'F#' ]

# Usage:
#
# Uses binary bit masks for the most popular programming languages.
# Values go from 0 to 25.
# Value 0 means "Other", to be stored as a string elsewhere.
# Values 1-24 stand for languages.
# To indicate language info is unknown, leave the language field empty.
#
# Examples of usage:
#   >>> Lang.PYTHON
#   4
#   >>> Lang.code('Python')
#   4
#   >>> langs = Lang.code('Python') + Lang.code('Shell')
#   >>> langs & Lang.code('Java')
#   0
#   >>> langs & Lang.code('Python')
#   4
#   >>> x = Lang.convert(['C', 'Java'])
#   >>> bool(x & Lang.C)
#   True
#   >>> bool(x & Lang.PYTHON)
#   False
#
# The top 25 languages were derived from looking at http://githut.info
# (Note: the githut data ends in 2014.  However, that doesn't matter enough
# for our purposes.  From 2014-2016, the relative rankings of languages may
# have changed, but mostly the same languages show up in the top 10-20.  For
# instance, this 2015 GitHub page lists all the same languages we below, just
# in different order: https://github.com/blog/2047-language-trends-on-github
# Here's another source, and with the eception of Visual Basic, VBA and Delphi,
# we have them all in our top 25: http://pypl.github.io/PYPL.html
# And not to be forgotten, the RedMonk survey, for Feb. 2016:
# http://redmonk.com/sogrady/2016/02/19/language-rankings-1-16/
# This time we're missing Groovy and Visual Basic.
#
# Why 25 and not 30?  In Python 3.4, sys.int_info says bits_per_digit = 30.
# I wanted to leave space for a few unassigned locations in the word, in case
# we discover some reason to need them in the future.

class Lang(object):

    OTHER        = 0b000000000000000000000000000000
    JAVASCRIPT   = 0b000000000000000000000000000001
    JAVA         = 0b000000000000000000000000000010
    PYTHON       = 0b000000000000000000000000000100
    CSS          = 0b000000000000000000000000001000
    PHP          = 0b000000000000000000000000010000
    RUBY         = 0b000000000000000000000000100000
    CPLUSPLUS    = 0b000000000000000000000001000000
    C            = 0b000000000000000000000010000000
    SHELL        = 0b000000000000000000000100000000
    CSHARP       = 0b000000000000000000001000000000
    OBJECTIVEC   = 0b000000000000000000010000000000
    R            = 0b000000000000000000100000000000
    VIML         = 0b000000000000000001000000000000
    GO           = 0b000000000000000010000000000000
    PERL         = 0b000000000000000100000000000000
    COFFEESCRIPT = 0b000000000000001000000000000000
    TEX          = 0b000000000000010000000000000000
    SWIFT        = 0b000000000000100000000000000000
    SCALA        = 0b000000000001000000000000000000
    EMACSLISP    = 0b000000000010000000000000000000
    HASKELL      = 0b000000000100000000000000000000
    LUA          = 0b000000001000000000000000000000
    CLOJURE      = 0b000000010000000000000000000000
    MATLAB       = 0b000000100000000000000000000000
    ARDUINO      = 0b000001000000000000000000000000

    _names = {
        OTHER        : "(Other)",
        JAVASCRIPT   : "JavaScript",
        JAVA         : "Java",
        PYTHON       : "Python",
        CSS          : "CSS",
        PHP          : "PHP",
        RUBY         : "Ruby",
        CPLUSPLUS    : "C++",
        C            : "C",
        SHELL        : "Shell",
        CSHARP       : "C#",
        OBJECTIVEC   : "Objective-C",
        R            : "R",
        VIML         : "VimL",
        GO           : "Go",
        PERL         : "Perl",
        COFFEESCRIPT : "CoffeeScript",
        TEX          : "TeX",
        SWIFT        : "Swift",
        SCALA        : "Scala",
        EMACSLISP    : "Emacs Lisp",
        HASKELL      : "Haskell",
        LUA          : "Lua",
        CLOJURE      : "Clojure",
        MATLAB       : "Matlab",
        ARDUINO      : "Arduino"
    }

    _codes = {
        "(other)"      : OTHER,
        "javascript"   : JAVASCRIPT,
        "java"         : JAVA,
        "python"       : PYTHON,
        "css"          : CSS,
        "php"          : PHP,
        "ruby"         : RUBY,
        "c++"          : CPLUSPLUS,
        "c"            : C,
        "shell"        : SHELL,
        "c#"           : CSHARP,
        "objective-c"  : OBJECTIVEC,
        "r"            : R,
        "viml"         : VIML,
        "go"           : GO,
        "perl"         : PERL,
        "coffeescript" : COFFEESCRIPT,
        "tex"          : TEX,
        "swift"        : SWIFT,
        "scala"        : SCALA,
        "emacs lisp"   : EMACSLISP,
        "haskell"      : HASKELL,
        "lua"          : LUA,
        "clojure"      : CLOJURE,
        "matlab"       : MATLAB,
        "arduino"      : ARDUINO
    }

    @classmethod
    def name(cls, val):
        '''Given an identifier, returns the corresponding name as a string.
        Examples:
            Lang.name(Lang.CPLUSPLUS) => "C++"
        '''
        if not isinstance(val, int):
            raise ValueError('Expected an integer but got "{}"'.format(val))
        try:
            return cls._names[val]
        except:
            return cls._names[cls.OTHER]


    @classmethod
    def code(cls, val):
        '''Given a string, returns the corresponding value.  If the language
        string is not recognized, returns 0.  Comparisons are made in a
        case-insensitive manner.

        Examples:
            Lang.code("C++") => 64
            Lang.code("python") => 4
        '''
        if not isinstance(val, str):
            raise ValueError('Expected a string but got "{}"'.format(val))
        try:
            return cls._codes[val.lower()]
        except:
            return cls.OTHER


    @classmethod
    def convert(cls, val):
        '''Convert a value to either a bit mask (as integer), or a list of
        strings, depending on the type of the value "val".  If the type is
        an integer, it assumes that it should convert to a list of string
        names; if the value is a list, it assumes it should produce an
        integer bit mask; and if the value is a single string, it just does
        the same thing as Lang.code(val).
        '''
        if not val:
            return None
        elif isinstance(val, int):
            strings = []
            for num, name in cls._names.items():
                if val & num:
                    strings.append(name)
            return strings
        elif isinstance(val, str):
            return Lang.code(val)
        elif isinstance(val, list):
            mask = 0
            for name in val:
                mask |= Lang.code(name)
            return mask
        else:
            raise ValueError('Unexpected type of argument: {}'.format(val))
