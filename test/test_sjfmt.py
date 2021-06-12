# -*- coding: utf-8 -*-
# pylint:disable=protected-access

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os

import black

import straitjacket.sjfmt as sjfmt

STR_CONTENTS = """
#!/usr/bin/env python3
# fmt: on
# Some license here.
#
# Has many lines. Many, many lines.
# Many, many, many lines.
\"\"\"Module docstring.

Possibly also many, many lines.
\"\"\"


import os.path
import sys

import a
from b.c import X  # some noqa comment


def test_parse():
    \"\"\"Docstring comes first.

    Possibly many lines.
    \"\"\"
    # FIXME: Some comment about why this function is crap but still in production.

    environ = {
        "MYAPP_DB_HOST": "1.2.3.4",
        "MYAPP_DB_PORT": "1234",
        'MYAPP_DB_PASSWORD': "secret",
        'MYAPP_DB_READ_ONLY': "0",
        'MYAPP_DB_DDL': "~/mkdb.sql",
        'MYAPP_DL': 123_123,
        'MYAPP_DL': 123_123_929,
        'MYAPP_DBDL': 12,
    }

    barf = {
        22: 23_222,
        2234: 231_231_231_232,
        1234: 231_231_232,
    }

    dbenv = myenv.parse(DBEnv, environ, prefix="MYAPP_DB_")

    assert dbenv.host == "1.2.3.4"
    assert dbenv.user == "new_user"
    assert dbenv.password == "secret"

    assert dbenv.read_only is False
    assert isinstance(dbenv.ddl, pl.Path)
    assert str(dbenv.ddl).endswith("mkdb.sql")

    assert len(attrnames) == 7


GLOBAL_STATE = {"a": a(1), "b": a(2), "c": a(3)}

'What\\'s the deal "here"?'
'And "here"?'

StrList = List[str]
PathList = List[Path]

class TestEnv(myenv.BaseEnv):
    '''
    notakey: notaval
    notakeyeither: notaval
    '''

    str_val_wo_default: str
    float_val_wo_default: float
    path_val_wo_default: pl.Path
    paths_val_wo_default: List[pl.Path]

    str_val: str = "foo"
    strs_val: StrList = ["foo = bar", "barfoo = baz"]
    float_val: float = 12.34
    path_val: pl.Path = pl.Path("file.txt")
    paths_val: PathList = [
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [1, 22, 2243, 4],

        {23: "asdf", 22: "aaaa", 443: "bbbb", 439: "cccc"},
        {1123: "asdf", 22: "k3k3", 443: "jfjf", 439: "k2k2"},
        {1: "asdf", 2332: "asdfk3k3", 42243: "jssdfjf", 4: "k2k2eie"},
    ]
    \"\"\"Docstring for instance attribute spam.\"\"\"
"""

# STR_CONTENTS = open("blacker.py").read()
# STR_CONTENTS = open("test.txt").read()


#####################
# integration tests #
#####################


def _(code: str) -> str:
    """Helper to normalize indent level of inline fixtures."""
    code   = code.lstrip(os.linesep)
    indent = min(len(line) - len(line.lstrip(" ")) for line in code.splitlines() if line.strip())
    lines  = [line[indent:].rstrip(" ") for line in code.splitlines()]
    return os.linesep.join(lines).rstrip() + os.linesep


def _fmt(code: str) -> str:
    code = _(code)

    # NOTE (mb 2018-12-16): We're not testing arbitrary
    #   formatting here, rather we're testing
    #   align_formatted_str specifically, which expects input
    #   which has already been formatted by black.format_str.
    #   Accordingly, the first thing we do is to check that the
    #   test is valid code as would have been produced by
    #   black.format_str.

    line_length   = max(len(line) + 1 for line in code.splitlines())
    mode          = black.FileMode(line_length=line_length)
    mode          = sjfmt._mode_override_defaults(mode)
    blackend_code = sjfmt.original_format_str(code, mode=mode)
    assert blackend_code == code

    sjfmt.DEBUG_LVL = 0
    try:
        sjfmt_out_code = sjfmt.align_formatted_str(code)
    finally:
        sjfmt.DEBUG_LVL = 0

    black.assert_equivalent(code, sjfmt_out_code)
    return sjfmt_out_code


def test_string_quoting():
    assert _fmt("""text_ok = "foo }"         """) == _("""text_ok = "foo }"         """)
    assert _fmt("""text_nok = 'foo }'        """) == _("""text_nok = "foo }"        """)
    assert _fmt("""unchanged = "foo"         """) == _("""unchanged = "foo"         """)
    assert _fmt("""unchanged = 'foo'         """) == _("""unchanged = 'foo'         """)
    assert _fmt("""unchanged = ("foo", 'bar')""") == _("""unchanged = ("foo", 'bar')""")
    assert _fmt("""unchanged = ['foo', "bar"]""") == _("""unchanged = ['foo', "bar"]""")

    assert _fmt("""d["symbol_key"]  """) == _("""d['symbol_key']  """)
    assert _fmt("""d['symbol_key']  """) == _("""d['symbol_key']  """)
    assert _fmt("""d["text key"]    """) == _("""d["text key"]    """)
    assert _fmt("""d['text key']    """) == _("""d["text key"]    """)

    assert _fmt("""d = {"symbol_key": 3}  """) == _("""d = {'symbol_key': 3}""")
    assert _fmt("""d = {'symbol_key': 3}  """) == _("""d = {'symbol_key': 3}""")
    assert _fmt("""d = {"text key": 3}    """) == _("""d = {"text key": 3}  """)
    assert _fmt("""d = {'text key': 3}    """) == _("""d = {"text key": 3}  """)


def test_backslash():
    assert _fmt(r'''x = "\\"  ''') == _(r'''x = "\\"  ''')


def test_symbol_normalization():
    unfmt    = '''d["bar"] = 123'''
    expected = _('''d['bar'] = 123''')
    assert _fmt(unfmt) == expected

    unfmt    = '''d["foo"], d["bar"] = something.split()'''
    expected = _('''d['foo'], d['bar'] = something.split()''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = ["bar", "baz"]'''
    expected = _('''x = ["bar", "baz"]''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = ['bar', 'baz']'''
    expected = _('''x = ['bar', 'baz']''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = ("bar", "baz")'''
    expected = _('''x = ("bar", "baz")''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = ('bar', 'baz')'''
    expected = _('''x = ('bar', 'baz')''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = {"bar", "baz"}'''
    expected = _('''x = {"bar", "baz"}''')
    assert _fmt(unfmt) == expected

    unfmt    = '''x = {'bar', 'baz'}'''
    expected = _('''x = {'bar', 'baz'}''')
    assert _fmt(unfmt) == expected

    unfmt    = '''d["foo"], d["bar"] = something.split()'''
    expected = _('''d['foo'], d['bar'] = something.split()''')
    assert _fmt(unfmt) == expected


def test_fmt_off_on():
    unfmt = '''
    # fmt: off
    x = {"foo": "bar"}
    # fmt: on
    y = {'foo': "bar"}
    '''
    assert _fmt(unfmt) == _(unfmt)

    unfmt = '''
    # fmt: moep
    x = {"foo": "bar"}
    # fmt: on
    y = {'foo': "bar"}
    '''
    expected = '''
    # fmt: moep
    x = {'foo': "bar"}
    # fmt: on
    y = {'foo': "bar"}
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_1():
    unfmt = '''
    {
        "hitcount": 0,
        "bookmark_id": bm_id,
    }
    '''
    expected = '''
    {
        'hitcount'   : 0,
        'bookmark_id': bm_id,
    }
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_2():
    unfmt = '''
    {
        "foo": 0,
        "foobar": 123,
        "foobarbaz": 123_456,
    }
    '''
    expected = '''
    {
        'foo'      :       0,
        'foobar'   :     123,
        'foobarbaz': 123_456,
    }
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_3():
    unfmt = '''
    log("found a total of {} files on s3".format(len(files_on_s3)))
    log("a total of {} files are stored locally".format(len(local_file_names)))
    '''
    assert _fmt(unfmt) == _(unfmt)


def test_alignment_4():
    unfmt = '''
    NO_ALIGN_BLOCK_END_MATCHERS = {
        '"': re.compile(DOUBLE_QUOTE_END_PATTERN, flags=re.VERBOSE),
        '"""': re.compile(TRIPPLE_DOUBLE_QUOTE_END_PATTERN, flags=re.VERBOSE),
        "'": re.compile(QUOTE_END_PATTERN, flags=re.VERBOSE),
    }
    '''
    expected = '''
    NO_ALIGN_BLOCK_END_MATCHERS = {
        '"'  : re.compile(DOUBLE_QUOTE_END_PATTERN        , flags=re.VERBOSE),
        '"""': re.compile(TRIPPLE_DOUBLE_QUOTE_END_PATTERN, flags=re.VERBOSE),
        "'"  : re.compile(QUOTE_END_PATTERN               , flags=re.VERBOSE),
    }
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_5():
    unfmt = '''
    foo = """
    bar
    """
    foobar = """
    baz
    """
    '''
    expected = '''
    foo = """
    bar
    """
    foobar = """
    baz
    """
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_6():
    unfmt = '''
    import typing as typ

    # Cache for already loaded environment configs. Environment
    # variables are only parsed once during initialization.

    EnvMapKey = typ.Tuple[typ.Type[EnvType], int]
    EnvMap = typ.Dict[EnvMapKey, EnvType]

    _envmap: EnvMap = {}
    '''
    expected = '''
    import typing as typ

    # Cache for already loaded environment configs. Environment
    # variables are only parsed once during initialization.

    EnvMapKey = typ.Tuple[typ.Type[EnvType], int]
    EnvMap    = typ.Dict[EnvMapKey, EnvType]

    _envmap: EnvMap = {}
    '''
    assert _fmt(unfmt) == _(expected)


def test_alignment_7():
    unfmt = '''
    import typing as typ


    class _Field(typ.NamedTuple):
        fname: str
        ftyp: FieldType
        env_key: str
        fallback: FieldValue
    '''
    expected = '''
    import typing as typ


    class _Field(typ.NamedTuple):
        fname   : str
        ftyp    : FieldType
        env_key : str
        fallback: FieldValue
    '''

    assert _fmt(unfmt) == _(expected)


def test_debug():
    unfmt = '''
    # fmt: off


    # fmt: on


    def fn():
        if d:
            x
        x = x


    b = int
    oo = str
    '''

    expected = '''
    # fmt: off


    # fmt: on


    def fn():
        if d:
            x
        x = x


    b  = int
    oo = str
    '''

    assert _fmt(unfmt) == _(expected)
