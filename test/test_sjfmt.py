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


def _fmt(code: str) -> str:
    sjfmt.DEBUG = 1
    try:
        return sjfmt._align_formatted_str(code.strip())
    finally:
        sjfmt.DEBUG = 0


def test_string_quoting():
    assert _fmt("""text_ok = "ast }"   """) == """text_ok = "ast }"   """.strip()
    assert _fmt("""text_nok = 'ast }'  """) == """text_nok = "ast }"  """.strip()
    assert _fmt("""unchanged = "ast"   """) == """unchanged = "ast"   """.strip()
    assert _fmt("""unchanged = 'ast'   """) == """unchanged = 'ast'   """.strip()

    assert _fmt("""d["symbol_key"]  """) == """d['symbol_key']  """.strip()
    assert _fmt("""d['symbol_key']  """) == """d['symbol_key']  """.strip()
    assert _fmt("""d["text key"]    """) == """d["text key"]    """.strip()
    assert _fmt("""d['text key']    """) == """d["text key"]    """.strip()

    assert _fmt("""d = {"symbol_key": 3}  """) == """d = {'symbol_key': 3}""".strip()
    assert _fmt("""d = {'symbol_key': 3}  """) == """d = {'symbol_key': 3}""".strip()
    assert _fmt("""d = {"text key": 3}    """) == """d = {"text key": 3}  """.strip()
    assert _fmt("""d = {'text key': 3}    """) == """d = {"text key": 3}  """.strip()


def test_fmt_off():
    pass


def test_alignment():
    pass
