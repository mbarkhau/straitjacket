import black
import straitjacket.sjfmt as sjfmt


str_contents = """
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

# str_contents = open("blacker.py").read()
# str_contents = open("test.txt").read()


#####################
# integration tests #
#####################


def _(code: str) -> str:
    """Helper to normalize indent level of inline fixtures."""
    code   = code.lstrip("\n")
    indent = min(len(line) - len(line.lstrip(" ")) for line in code.splitlines())
    lines  = [line[indent:].rstrip(" ") for line in code.splitlines()]
    return "\n".join(lines).rstrip() + "\n"


def _fmt(code: str) -> str:
    code = _(code)

    # NOTE (mb 2018-12-16): We're not testing arbitrary
    #   formatting here, rather we're testing
    #   _align_formatted_str specifically, which expects input
    #   which has already been formatted by black.format_str.
    #   Accordingly, the first thing we do is to check that the
    #   test is valid code as would have been produced by
    #   black.format_str.

    line_length   = max(len(line) + 1 for line in code.splitlines())
    mode          = black.FileMode.NO_STRING_NORMALIZATION
    blackend_code = black.format_str(code, line_length=line_length, mode=mode)
    assert blackend_code == code

    sjfmt.DEBUG_LVL = 0
    try:
        return sjfmt._align_formatted_str(code)
    finally:
        sjfmt.DEBUG_LVL = 0


def test_selftest():
    with open(__file__) as fh:
        unfmt = fh.read()
    assert _fmt(unfmt) == unfmt


def test_string_quoting():
    assert _fmt("""text_ok = "foo }"         """) == """text_ok = "foo }"         """.strip()
    assert _fmt("""text_nok = 'foo }'        """) == """text_nok = "foo }"        """.strip()
    assert _fmt("""unchanged = "foo"         """) == """unchanged = "foo"         """.strip()
    assert _fmt("""unchanged = 'foo'         """) == """unchanged = 'foo'         """.strip()
    assert _fmt("""unchanged = ("foo", 'bar')""") == """unchanged = ("foo", 'bar')""".strip()
    assert _fmt("""unchanged = ['foo', "bar"]""") == """unchanged = ['foo', "bar"]""".strip()

    assert _fmt("""d["symbol_key"]  """) == """d['symbol_key']  """.strip()
    assert _fmt("""d['symbol_key']  """) == """d['symbol_key']  """.strip()
    assert _fmt("""d["text key"]    """) == """d["text key"]    """.strip()
    assert _fmt("""d['text key']    """) == """d["text key"]    """.strip()

    assert _fmt("""d = {"symbol_key": 3}  """) == """d = {'symbol_key': 3}""".strip()
    assert _fmt("""d = {'symbol_key': 3}  """) == """d = {'symbol_key': 3}""".strip()
    assert _fmt("""d = {"text key": 3}    """) == """d = {"text key": 3}  """.strip()
    assert _fmt("""d = {'text key': 3}    """) == """d = {"text key": 3}  """.strip()


def test_backslash():
    _fmt(r'''x = "\\"   ''') == r'''x = "\\"  '''.strip()


def test_symbol_normalization():
    unfmt = '''d["bar"] = 123'''
    assert _fmt(unfmt) == '''d['bar'] = 123'''

    unfmt = '''d["foo"], d["bar"] = something.split()'''
    assert _fmt(unfmt ) == '''d['foo'], d['bar'] = something.split()'''

    unfmt = '''x = ["bar", "baz"]'''
    assert _fmt(unfmt) == '''x = ["bar", "baz"]'''

    unfmt = '''x = ['bar', 'baz']'''
    assert _fmt(unfmt) == '''x = ['bar', 'baz']'''

    unfmt = '''x = ("bar", "baz")'''
    assert _fmt(unfmt) == '''x = ("bar", "baz")'''

    unfmt = '''x = ('bar', 'baz')'''
    assert _fmt(unfmt) == '''x = ('bar', 'baz')'''

    unfmt = '''x = {"bar", "baz"}'''
    assert _fmt(unfmt) == '''x = {"bar", "baz"}'''

    unfmt = '''x = {'bar', 'baz'}'''
    assert _fmt(unfmt) == '''x = {'bar', 'baz'}'''

    unfmt = '''d["foo"], d["bar"] = something.split()'''
    assert _fmt(unfmt) == '''d['foo'], d['bar'] = something.split()'''


def test_fmt_off():
    pass


def test_alignment():
    pass
