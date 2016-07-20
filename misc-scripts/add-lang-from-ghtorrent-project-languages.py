#!/usr/bin/env python3.4
#
# @file    add-lang-from-ghtorrent.py
# @brief   Add language info we don't have, using a ghtorrent mysql dump.
# @author  Michael Hucka
#
# <!---------------------------------------------------------------------------
# Copyright (C) 2015 by the California Institute of Technology.
# This software is part of CASICS, the Comprehensive and Automated Software
# Inventory Creation System.  For more information, visit http://casics.org.
# ------------------------------------------------------------------------- -->

# Example lines from project-languages.csv:
# 79607,"viml",367,"2015-10-09 20:51:55"
# 58021,"c",43562612,"2015-10-09 20:51:55"
# 935276,"perl",2291,"2015-10-09 20:51:55"
# 58021,"php",25023586,"2015-10-09 20:51:55"
# 58021,"c++",1268014,"2015-10-09 20:51:55"
# 58021,"objective-c",711164,"2015-10-09 20:51:55"
# 58021,"shell",293443,"2015-10-09 20:51:55"
# 1982683,"javascript",333654,"2015-10-09 20:51:55"
# 58021,"javascript",92321,"2015-10-09 20:51:55"
# 58021,"perl",10643,"2015-10-09 20:51:55"

import sys
import plac
import os
import csv
from collections import defaultdict
from time import time, sleep

sys.path.append(os.path.join(os.path.dirname(__file__), "../common"))
sys.path.append(os.path.join(os.path.dirname(__file__), "../../common"))
from casicsdb import *


# Main body.
# .............................................................................

start = time()

msg('Opening database ...')

casicsdb = CasicsDB()
github_db = casicsdb.open('github')
repos = github_db.repos

# We need to read both the projects.csv and project_languages.csv files,
# because the GHTorrent identifiers for projects are found in projects.csv.
# The GHTorrent CSV projects.csv file has an "id" as the first column, but
# I believe that's the id for the entry in the table and not the project id.

proj_fields = {'id'          : 0,            # Don't use this -- no the project id.
               'url'         : 1,
               'name'        : 3,
               'description' : 4,
               'language'    : 5,
               'created'     : 6,
               'forked_from' : 7,
               'deleted'     : 8}

namestart = len('https://api.github.com/repos/')
id_map = {}

# Read the projects.csv file once and build a mapping from GHTorrent's
# project identifiers to project owner/name path strings.

msg('Building project id mapping')
with open('projects.csv', encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    for row in reader:
        id   = int(row[0])
        if id == -1:
            continue
        path = row[1][namestart:]
        id_map[id] = path
        count += 1
        if count % 1000000 == 0:
            msg(count)

# Read project-languages.csv and create a list of languages known for each
# project.

lang_fields = {'id'   : 0,            # Their id, not ours.
               'lang' : 1}

lang_map = defaultdict(list)

msg('Reading languages')
with open('project_languages.csv', encoding="utf-8", errors="replace") as f:
    reader = csv.reader(f, escapechar='\\')
    count = 0
    for row in reader:
        id   = int(row[0])
        if id == -1:
            continue
        lang = row[1]
        if lang not in lang_map[id]:
            lang_map[id].append(lang)
        count += 1
        if count % 1000000 == 0:
            msg(count)

# At this point, we have a dictionary that looks like this:
#
# defaultdict(<class 'list'>, {'79607': ['viml'],
#                             '58021': ['c', 'php', 'objective-c', 'shell'],
#                             '935276': ['perl']
#                             ...})
# We need to:
# 1) translate id numbers to project owner/name strings
# 2) correct the case of the language strings ("viml" -> "VimL")
# 3) convert the language list to the form [{'name': 'c'}, {'name': 'VimL']...}

final_map = {}

msg('Building final map: 1st stage')
count = 0
for id, languages in lang_map.items():
    if id not in id_map:
        msg('*** {} not found'.format(id))
        continue
    final_map[id_map[id]] = languages
    count += 1
    if count % 1000000 == 0:
        msg(count)

lang_names = [
    "ABAP",
    "ABC",
    "AGS Script",
    "AMPL",
    "ANTLR",
    "API Blueprint",
    "APL",
    "ASP",
    "ATLAS",
    "ATS",
    "ActionScript",
    "Ada",
    "Agda",
    "AgilentVEE",
    "Algol",
    "Alice",
    "Alloy",
    "Angelscript",
    "Ant Build System",
    "ApacheConf",
    "Apex",
    "AppleScript",
    "Arc",
    "Arduino",
    "AsciiDoc",
    "AspectJ",
    "Assembly",
    "Augeas",
    "AutoHotkey",
    "AutoIt",
    "AutoLISP",
    "Automator",
    "Avenue",
    "Awk",
    "BASIC",
    "BCPL",
    "BETA",
    "Bash",
    "Batchfile",
    "BeanShell",
    "Befunge",
    "Bison",
    "BitBake",
    "BlitzBasic",
    "BlitzMax",
    "Bluespec",
    "Boo",
    "BourneShell",
    "Brainfuck",
    "Brightscript",
    "Bro",
    "C",
    "C#",
    "C++",
    "C-ObjDump",
    "C2hs Haskell",
    "CFML",
    "CHILL",
    "CIL",
    "CIL",
    "CLIPS",
    "CLU",
    "CMake",
    "CMake",
    "COBOL",
    "COMAL",
    "COmega",
    "CPL",
    "CSS",
    "CShell",
    "Caml",
    "Cap&#39;n Proto",
    "Cap'n Proto",
    "CartoCSS",
    "Ceylon",
    "Ch",
    "Chapel",
    "Charity",
    "Chef",
    "ChucK",
    "Cirru",
    "Clarion",
    "Clean",
    "Clipper",
    "Clojure",
    "Cobra",
    "CoffeeScript",
    "ColdFusion CFC",
    "ColdFusion",
    "Common Lisp",
    "Component Pascal",
    "Cool",
    "Coq",
    "Cpp-ObjDump",
    "Creole",
    "Crystal",
    "Cucumber",
    "Cuda",
    "Curl",
    "Cycript",
    "Cython",
    "D",
    "D-ObjDump",
    "DCL",
    "DCPU-16 ASM",
    "DCPU16ASM",
    "DIGITAL Command Language",
    "DM",
    "DNS Zone",
    "DOT",
    "DTrace",
    "DTrace",
    "Darcs Patch",
    "Dart",
    "Delphi",
    "DiBOL",
    "Diff",
    "Dockerfile",
    "Dogescript",
    "Dylan",
    "E",
    "ECL",
    "ECLiPSe",
    "ECMAScript",
    "EGL",
    "EPL",
    "EXEC",
    "Eagle",
    "Ecere Projects",
    "Ecl",
    "Eiffel",
    "Elixir",
    "Elm",
    "Emacs Lisp",
    "EmberScript",
    "Erlang",
    "Escher",
    "Etoys",
    "Euclid",
    "Euphoria",
    "F#",
    "FLUX",
    "FORTRAN",
    "Factor",
    "Falcon",
    "Fancy",
    "Fantom",
    "Felix",
    "Filterscript",
    "Formatted",
    "Forth",
    "Fortress",
    "FourthDimension 4D",
    "FreeMarker",
    "Frege",
    "G-code",
    "GAMS",
    "GAP",
    "GAP",
    "GAS",
    "GDScript",
    "GLSL",
    "GNU Octave",
    "Gambas",
    "Game Maker Language",
    "Genshi",
    "Gentoo Ebuild",
    "Gentoo Eclass",
    "Gettext Catalog",
    "Glyph",
    "Gnuplot",
    "Go",
    "Golo",
    "GoogleAppsScript",
    "Gosu",
    "Grace",
    "Gradle",
    "Grammatical Framework",
    "Graph Modeling Language",
    "Graphviz (DOT)",
    "Groff",
    "Groovy Server Pages",
    "Groovy",
    "HCL",
    "HPL",
    "HTML",
    "HTML+Django",
    "HTML+EEX",
    "HTML+ERB",
    "HTML+PHP",
    "HTTP",
    "Hack",
    "Haml",
    "Handlebars",
    "Harbour",
    "Haskell",
    "Haxe",
    "Haxe",
    "Heron",
    "Hy",
    "HyPhy",
    "HyperTalk",
    "IDL",
    "IGOR Pro",
    "INI",
    "INTERCAL",
    "IRC log",
    "Icon",
    "Idris",
    "Inform 7",
    "Inform",
    "Informix 4GL",
    "Inno Setup",
    "Io",
    "Ioke",
    "Isabelle ROOT",
    "Isabelle",
    "J",
    "J#",
    "JADE",
    "JFlex",
    "JSON",
    "JSON5",
    "JSONLD",
    "JSONiq",
    "JSX",
    "JScript",
    "JScript.NET",
    "Jade",
    "Jasmin",
    "Java Server Pages",
    "Java",
    "JavaFXScript",
    "JavaScript",
    "Julia",
    "Jupyter Notebook",
    "KRL",
    "KiCad",
    "Kit",
    "KornShell",
    "Kotlin",
    "LFE",
    "LLVM",
    "LOLCODE",
    "LPC",
    "LSL",
    "LaTeX",
    "LabVIEW",
    "LadderLogic",
    "Lasso",
    "Latte",
    "Lean",
    "Less",
    "Lex",
    "LilyPond",
    "Limbo",
    "Lingo",
    "Linker Script",
    "Linux Kernel Module",
    "Liquid",
    "Lisp",
    "Literate Agda",
    "Literate CoffeeScript",
    "Literate Haskell",
    "LiveScript",
    "Logo",
    "Logos",
    "Logtalk",
    "LookML",
    "LoomScript",
    "LotusScript",
    "Lua",
    "Lucid",
    "Lustre",
    "M",
    "M4",
    "MAD",
    "MANTIS",
    "MAXScript",
    "MDL",
    "MEL",
    "ML",
    "MOO",
    "MSDOSBatch",
    "MTML",
    "MUF",
    "MUMPS",
    "Magic",
    "Magik",
    "Makefile",
    "Mako",
    "Malbolge",
    "Maple",
    "Markdown",
    "Mask",
    "Mathematica",
    "Matlab",
    "Maven POM",
    "Max",
    "MaxMSP",
    "MediaWiki",
    "Mercury",
    "Metal",
    "MiniD",
    "Mirah",
    "Miva",
    "Modelica",
    "Modula-2",
    "Modula-3",
    "Module Management System",
    "Monkey",
    "Moocode",
    "MoonScript",
    "Moto",
    "Myghty",
    "NATURAL",
    "NCL",
    "NL",
    "NQC",
    "NSIS",
    "NXTG",
    "Nemerle",
    "NetLinx",
    "NetLinx+ERB",
    "NetLogo",
    "NewLisp",
    "Nginx",
    "Nimrod",
    "Ninja",
    "Nit",
    "Nix",
    "Nu",
    "Nu",
    "NumPy",
    "OCaml",
    "OPL",
    "Oberon",
    "ObjDump",
    "Object Rexx",
    "Objective-C",
    "Objective-C++",
    "Objective-J",
    "Occam",
    "Omgrofl",
    "Opa",
    "Opal",
    "OpenCL",
    "OpenEdge ABL",
    "OpenEdgeABL",
    "OpenSCAD",
    "Org",
    "Ox",
    "Oxygene",
    "Oz",
    "PAWN",
    "PHP",
    "PILOT",
    "PLI",
    "PLSQL",
    "PLpgSQL",
    "POVRay",
    "Pan",
    "Papyrus",
    "Paradox",
    "Parrot Assembly",
    "Parrot Internal Representation",
    "Parrot",
    "Pascal",
    "Perl",
    "Perl6",
    "PicoLisp",
    "PigLatin",
    "Pike",
    "Pliant",
    "Pod",
    "PogoScript",
    "PostScript",
    "PowerBasic",
    "PowerScript",
    "PowerShell",
    "Processing",
    "Prolog",
    "Propeller Spin",
    "Protocol Buffer",
    "Public Key",
    "Puppet",
    "Pure Data",
    "PureBasic",
    "PureData",
    "PureScript",
    "Python traceback",
    "Python",
    "Q",
    "QML",
    "QMake",
    "R",
    "RAML",
    "RDoc",
    "REALbasic",
    "REALbasicDuplicate",
    "REBOL",
    "REXX",
    "RHTML",
    "RMarkdown",
    "RPGOS400",
    "Racket",
    "Ragel in Ruby Host",
    "Ratfor",
    "Raw token data",
    "Rebol",
    "Red",
    "Redcode",
    "RenderScript",
    "Revolution",
    "RobotFramework",
    "Rouge",
    "Ruby",
    "Rust",
    "S",
    "SAS",
    "SCSS",
    "SIGNAL",
    "SMT",
    "SPARK",
    "SPARQL",
    "SPLUS",
    "SPSS",
    "SQF",
    "SQL",
    "SQLPL",
    "SQR",
    "STON",
    "SVG",
    "Sage",
    "SaltStack",
    "Sass",
    "Sather",
    "Scala",
    "Scaml",
    "Scheme",
    "Scilab",
    "Scratch",
    "Seed7",
    "Self",
    "Shell",
    "ShellSession",
    "Shen",
    "Simula",
    "Simulink",
    "Slash",
    "Slate",
    "Slim",
    "Smali",
    "Smalltalk",
    "Smarty",
    "SourcePawn",
    "Squeak",
    "Squirrel",
    "Standard ML",
    "Stata",
    "Stylus",
    "Suneido",
    "SuperCollider",
    "Swift",
    "SystemVerilog",
    "TACL",
    "TOM",
    "TOML",
    "TXL",
    "Tcl",
    "Tcsh",
    "TeX",
    "Tea",
    "Text",
    "Textile",
    "Thrift",
    "Transact-SQL",
    "Turing",
    "Turtle",
    "Twig",
    "TypeScript",
    "Unified Parallel C",
    "Unity3D Asset",
    "UnrealScript",
    "VBScript",
    "VCL",
    "VHDL",
    "Vala",
    "Verilog",
    "VimL",
    "Visual Basic",
    "Visual Basic.NET",
    "Visual Fortran",
    "Visual FoxPro",
    "Volt",
    "Vue",
    "Web Ontology Language",
    "WebDNA",
    "WebIDL",
    "Whitespace",
    "Wolfram Language",
    "X10",
    "XBase++",
    "XC",
    "XML",
    "XPL",
    "XPages",
    "XProc",
    "XQuery",
    "XS",
    "XSLT",
    "Xen",
    "Xojo",
    "Xtend",
    "YAML",
    "Yacc",
    "Yorick",
    "Zephir",
    "Zimpl",
    "Zshell",
    "bc",
    "cT",
    "cg",
    "dBase",
    "desktop",
    "eC",
    "edn",
    "fish",
    "haXe",
    "ksh",
    "mupad",
    "nesC",
    "ooc",
    "reStructuredText",
    "sed",
    "thinBasic",
    "wisp",
    "xBase",
    "Other",
]

lang_name_map = {name.lower() : name for name in lang_names}

def rename(lang):
    return lang_name_map[lang] if lang in lang_name_map else lang

msg('Building final map: 2nd stage')
count = 0
for path, languages in final_map.items():
    final_map[path] = [{'name': rename(n)} for n in final_map[path]]
    count += 1
    if count % 1000000 == 0:
        msg(count)

msg('Updating database')
count = 0
for path, languages in final_map.items():
    owner       = path[:path.find('/')]
    name        = path[path.find('/') + 1:]

    entry = repos.find_one({'owner': owner, 'name': name}, {'languages': 1})

    if not entry:
        # We need to deal with these using our cataloguer.
        msg('*** Unknown entry {}'.format(path))
        continue

    if not entry['languages'] or entry['languages'] == -1 \
       or (len(entry['languages']) < len(languages)):
        msg('Updating {}'.format(path))
        repos.update_one({'_id': entry['_id']},
                         {'$set': {'languages': languages}},
                         upsert=False)

    if count % 1000000 == 0:
        msg(count)
