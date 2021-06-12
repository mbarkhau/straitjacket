# This file is part of the straitjacket project
# https://github.com/mbarkhau/straitjacket
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import re
import sys
import enum
import typing as typ
import functools
import multiprocessing as mp

import black
import click

__version__ = "v202106.1019"


DEBUG_LVL = 0


FileContent = str


# fmt: off
ALIGN_BEFORE_TOKENS = {
    "<<=", ">>=", "**=", "//=",
    "+=", "-=", "*=", "/=", "%=", "|=", "&=", "@=",
    "==", "!=", "<=", ">=",
    "//", "<<", ">>", "^=", "~=",
    "in", "is",
    "},", "],", "),",
    "->",
    ",", ":", "=",
    "+", "-", "*", "/",
    "%", "|", "&", "^", "~",
    "!", "<", ">",
    "}", "]", ")",
}
# fmt: on


# NOTE (mb 2018-09-12): An alternative implementation
#   might use lookback and count backslashes.

TRIPPLE_QUOTE_END_PATTERN = r"""
(
    (?<=^)
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
'''
"""


TRIPPLE_DOUBLE_QUOTE_END_PATTERN = r"""
(
    (?<=^)
    | (?<=\\\\)
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
\"\"\"
"""


DOUBLE_QUOTE_END_PATTERN = r"""
(
    (?<=^)
    | (?<=\\\\)
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
"
"""


QUOTE_END_PATTERN = r"""
(
    (?<=^)
    | (?<=\\\\)
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
'
"""


COMMENT_END_PATTERN = r"$"


NO_ALIGN_BLOCK_END_MATCHERS = {
    "'''": re.compile(TRIPPLE_QUOTE_END_PATTERN       , flags=re.VERBOSE),
    '"""': re.compile(TRIPPLE_DOUBLE_QUOTE_END_PATTERN, flags=re.VERBOSE),
    '"'  : re.compile(DOUBLE_QUOTE_END_PATTERN        , flags=re.VERBOSE),
    "'"  : re.compile(QUOTE_END_PATTERN               , flags=re.VERBOSE),
    "#"  : re.compile(COMMENT_END_PATTERN             , flags=re.MULTILINE),
}


TOKEN_SEP_PATTERN = r"""
(
    '''
    |\"\"\"
    |\"
    |'
    |\#

    |<<= |>>= |\*\*= |//=
    |\+= |\-= |\*= |/= |%= |\|= |&= |@=
    |== |!= |<= |>=
    |// |<< |>> |\^= |~=
    |(?<!\w)in(?!\w) |(?<!\w)is(?!\w)
    |\}, |\], |\),
    |\->
    |, |: |=(?=[ ])
    |\+ |\- |\* |/
    |% |\| |& |\^ |~
    |! |< |>
    |\{ |\[ |\(
    |\} |\] |\)

    |$
)
"""


TOKEN_SEP_RE = re.compile(TOKEN_SEP_PATTERN, flags=re.MULTILINE | re.VERBOSE)

SYMBOL_STRING_RE = re.compile(r"\"[a-zA-Z0-9_\-]+\"")

NON_SYMBOL_STRING_RE = re.compile(r"[^a-zA-Z0-9_\-]")

FMT_ON_OFF_RE = re.compile(r"#\s*fmt\s*:\s*(on|off)")


class TokenType(enum.Enum):

    INDENT     = 0
    SEPARATOR  = 1
    CODE       = 2
    NEWLINE    = 3
    BLOCK      = 4
    COMMENT    = 5
    WHITESPACE = 6


TokenVal = str


class Token(typ.NamedTuple):

    typ: TokenType
    val: TokenVal

    def __repr__(self) -> str:
        """Token representation with alignment.

        >>> repr(Token(TokenType.CODE, 'tokenval'))
        "Token(TokenType.CODE      , 'tokenval')"
        """
        return f"Token({self.typ:<20}, {repr(self.val)})"


TokenRow = typ.List[Token]


def _tokenize_for_alignment(src_contents: str) -> typ.Iterator[Token]:
    rest          : str = src_contents
    prev_rest     : typ.Optional[str] = None
    prev_token_val: typ.Optional[str] = None

    while rest:
        assert rest != prev_rest, "No progress at: " + repr(rest[:40])
        prev_rest = rest

        curr_token_sep = TOKEN_SEP_RE.search(rest)
        assert curr_token_sep is not None
        curr_token_start, curr_token_end = curr_token_sep.span()
        is_eof = curr_token_start == len(rest)
        # newline match has zero width
        is_newline = curr_token_start == curr_token_end

        if is_eof:
            if prev_token_val and len(prev_token_val.strip()) == 0:
                yield Token(TokenType.WHITESPACE, rest)
            else:
                yield Token(TokenType.CODE, rest)
            return
        elif is_newline:
            # adjust for zero width match
            curr_token_end = curr_token_start + 1

            # Get everything (if anything) up to (and excluding) the newline
            token_val = rest[:curr_token_start]
            if token_val:
                assert token_val != "\n"
                yield Token(TokenType.CODE, token_val)

            # The newline itself (note that black promises to
            # have normalized CRLF etc. to plain LF)
            token_val = rest[curr_token_start:curr_token_end]
            assert token_val == "\n"
            yield Token(TokenType.NEWLINE, token_val)

            rest = rest[curr_token_end:]
            # parse any indent
            new_rest   = rest.lstrip(" \t")
            indent_len = len(rest) - len(new_rest)
            if indent_len > 0:
                indent_token_val = rest[:indent_len]
                yield Token(TokenType.INDENT, indent_token_val)
                rest = new_rest
        elif curr_token_start > 0:
            prev_token_val = rest[:curr_token_start]
            rest           = rest[curr_token_start:]
            assert prev_token_val != "\n"
            assert prev_token_val not in ALIGN_BEFORE_TOKENS, repr(prev_token_val)
            if len(prev_token_val.strip()) == 0:
                yield Token(TokenType.WHITESPACE, prev_token_val)
            else:
                yield Token(TokenType.CODE, prev_token_val)
        else:
            token_val = curr_token_sep.group(0)
            if token_val in NO_ALIGN_BLOCK_END_MATCHERS:
                # comment, string or docstring
                block_begin_val = token_val
                assert curr_token_end > 0
                rest            = rest[len(block_begin_val) :]
                end_matcher     = NO_ALIGN_BLOCK_END_MATCHERS[token_val]
                block_end_match = end_matcher.search(rest)
                assert block_end_match, rest[:40]
                block_end_token = block_end_match.group(0)
                block_end_index = block_end_match.span()[-1]
                assert block_end_index <= len(rest), f"{len(rest)} < {block_end_index}"
                block_rest      = rest[:block_end_index]
                block_token_val = block_begin_val + block_rest
                assert block_token_val.endswith(block_end_token)
                if block_token_val.strip().startswith("#"):
                    yield Token(TokenType.COMMENT, block_token_val)
                else:
                    yield Token(TokenType.BLOCK, block_token_val)
                rest = rest[block_end_index:]
            else:
                sep_token_val = token_val
                yield Token(TokenType.SEPARATOR, sep_token_val)
                rest = rest[curr_token_end:]

            # NOTE (mb 2018-09-09): The way we tokenize, we always consume
            #   all content belonging to strings and comments. This means that
            #   the rest (after consuming all content of a string or comment),
            #   should continue to be valid python. This means we can do some
            #   basic sanity checks. For example, no valid python token begins
            #   with a questionmark (though this is actually introduced because
            #   one of the test cases conveniently has a questionmark as the
            #   first character after an edge case of string parsing).
            assert not rest.startswith("?"), repr(rest)


Indent      = str
RowIndex    = int
ColIndex    = int
OffsetWidth = int
TokenTable  = typ.List[TokenRow]


class RowLayoutToken(typ.NamedTuple):
    """Disambiguate between lines with different layout/structure.

    We only want to align lines which have the same structure of
    indent and separators. Any difference in the number of elements
    or type of separators causes alignment to be disabled.
    """

    typ: TokenType
    # val is only set if it should cause a different prefix
    # eg. if a separator is a comma vs a period.
    val: TokenVal


# Tokens which have values which are relevant to to the layout of
# a cell group.
LAYOUT_VAL_TOKENS = {TokenType.SEPARATOR, TokenType.INDENT}

RowLayoutTokens = typ.Tuple[RowLayoutToken, ...]


class AlignmentContextKey(typ.NamedTuple):
    """Does not change between multiple lines that can be aligned."""

    col_idx: ColIndex
    row_idx: RowIndex
    tok_typ: TokenType
    tok_val: TokenVal
    layout : RowLayoutTokens


AlignmentContext = typ.Dict[AlignmentContextKey, OffsetWidth]


class AlignmentCellKey(typ.NamedTuple):
    col_index     : ColIndex
    last_row_index: RowIndex
    token_val     : TokenVal
    layout        : RowLayoutTokens


class AlignmentCell(typ.NamedTuple):
    row_idx     : RowIndex
    offset_width: OffsetWidth


CellGroups = typ.Dict[AlignmentCellKey, typ.List[AlignmentCell]]


def _is_dict_key_symbol_access(col_index: int, tok_cell: Token, row: TokenRow) -> bool:
    """Determine if the current token is a separator for __getitem__, __setitem__."""

    if col_index - 1 < 0:
        return False
    elif tok_cell.val not in ": ] ],":
        return False

    prev_tok = row[col_index - 1]
    if prev_tok.typ != TokenType.BLOCK:
        return False
    elif SYMBOL_STRING_RE.match(prev_tok.val) is None:
        return False
    elif tok_cell.typ != TokenType.SEPARATOR:
        return False
    elif tok_cell.val in ("]", "],"):
        if col_index - 2 < 0:
            return False

        prevprev_tok = row[col_index - 2]
        if prevprev_tok == Token(TokenType.SEPARATOR, "["):
            return True

    elif tok_cell.val == ":":
        return True

    return False


ATTR_ACCESORS = ('getattr', 'setattr', 'delattr')


def _is_attr_symbol_access(col_index: int, tok_cell: Token, row: TokenRow) -> bool:
    if not (tok_cell.typ == TokenType.CODE and tok_cell.val in ATTR_ACCESORS):
        return False

    return (
        col_index + 5 < len(row)
        and row[col_index + 1].typ == TokenType.SEPARATOR
        and row[col_index + 1].val == "("
        and row[col_index + 2].typ == TokenType.CODE
        and row[col_index + 3].typ == TokenType.SEPARATOR
        and row[col_index + 3].val == ","
        and row[col_index + 4].typ == TokenType.WHITESPACE
        and row[col_index + 4].val == " "
        and row[col_index + 5].typ == TokenType.BLOCK
        and bool(SYMBOL_STRING_RE.match(row[col_index + 5].val))
    )


def _is_single_quoted_non_symbol(tok_cell: Token) -> bool:
    return (
        tok_cell.typ == TokenType.BLOCK
        and len(tok_cell.val) > 2
        and tok_cell.val[:3] != "'''"
        and tok_cell.val[0] == "'"
        and tok_cell.val[-1] == "'"
        and '"' not in tok_cell.val[1:-1]
        and bool(NON_SYMBOL_STRING_RE.search(tok_cell.val[1:-1]))
    )


def _normalize_strings(row: TokenRow) -> None:
    """Apply string quoting rules.

    - Enforces quoting of "text" in double quotes
    - Enforces quoting of 'symbols' in single quotes

    Text/Data/Paths are considered to be anything which contains
    whitespace, punctuation or non ascii characters.

    Internal/Symbol/Atom strings are strings which are code as opposed
    to data. They have no meaning outside of the context of the
    program. Symbol strings must be valid python identifiers

    They are:
        - dictionary keys
        - attribute names
        - implicit enums
    They are not:
        - urls
        - user readable text
        - translation strings
        - format strings

    This function performs conversion only for a subset of cases,
    since it cannot detect all. For symbols these cases are, strings
    used as dictionary keys and for attribute access via getattr,
    setattr, delattr.
    """

    if len(row) == 1 and row[0].typ == TokenType.NEWLINE:
        return

    # single quotes.
    for col_index, tok_cell in enumerate(row):
        if _is_dict_key_symbol_access(col_index, tok_cell, row):
            normalized_token_val = row[col_index - 1].val.replace('"', "'")
            row[col_index - 1] = Token(TokenType.BLOCK, normalized_token_val)

        if _is_attr_symbol_access(col_index, tok_cell, row):
            normalized_token_val = "'" + row[col_index + 5].val[1:-1] + "'"
            row[col_index + 5] = Token(TokenType.BLOCK, normalized_token_val)

    # double quotes.
    for col_index, tok_cell in enumerate(row):
        if _is_single_quoted_non_symbol(tok_cell):
            normalized_token_val = '"' + tok_cell.val[1:-1] + '"'
            row[col_index] = Token(TokenType.BLOCK, normalized_token_val)


def _iter_formattable_rows(table: TokenTable) -> typ.Iterator[typ.Tuple[int, TokenRow]]:
    is_fmt_enabled = True
    for row_index, row in enumerate(table):
        for tok in row:
            if tok.typ != TokenType.COMMENT:
                continue

            fmt_on_off_match = FMT_ON_OFF_RE.match(tok.val)
            if fmt_on_off_match is None:
                continue

            if fmt_on_off_match.group(1) == 'on':
                is_fmt_enabled = True
            if fmt_on_off_match.group(1) == 'off':
                is_fmt_enabled = False

        if is_fmt_enabled:
            yield row_index, row


def _iter_alignment_contexts(table: TokenTable) -> typ.Iterator[AlignmentContext]:
    for row_index, row in _iter_formattable_rows(table):
        is_multiline_row = any(
            token.typ != TokenType.NEWLINE and "\n" in token.val for token in row
        )
        if is_multiline_row:
            continue

        ctx   : AlignmentContext = {}
        layout: RowLayoutTokens  = ()

        for col_index, token in enumerate(row):
            layout_token_val: TokenVal = ""

            if token.typ in LAYOUT_VAL_TOKENS:
                if token.typ == TokenType.INDENT:
                    layout_token_val = token.val
                elif token.val in ALIGN_BEFORE_TOKENS:
                    layout_token_val = token.val
                elif col_index > 0:
                    # Layout tokens such as ([{ don't cause alignment, to
                    # their preceding token, so line offset up to the
                    # column of those tokens can a be different. We only
                    # want to continue with alignment if the tokens are
                    # all at the same line offset.
                    layout_token_val = token.val + f"::{len(row[col_index - 1].val)}"

            layout += (RowLayoutToken(token.typ, layout_token_val),)

            if token.val in ALIGN_BEFORE_TOKENS:
                assert token.typ == TokenType.SEPARATOR
                prev_token = row[col_index - 1]
                if prev_token.typ != TokenType.SEPARATOR:
                    offset_width = len(prev_token.val)
                    ctx_key      = AlignmentContextKey(
                        col_index, row_index, token.typ, token.val, layout
                    )
                    ctx[ctx_key] = offset_width

        yield ctx


def _find_cell_groups(alignment_contexts: typ.List[AlignmentContext]) -> CellGroups:
    cell_groups: typ.Dict[AlignmentCellKey, typ.List[AlignmentCell]] = {}
    for ctx in alignment_contexts:
        ctx_items = sorted(ctx.items())
        for ctx_key, offset_width in ctx_items:
            col_index, row_index, _, token_val, layout = ctx_key
            prev_row_idx = row_index - 1

            prev_cell_key = AlignmentCellKey(col_index, prev_row_idx, token_val, layout)
            curr_cell_key = AlignmentCellKey(col_index, row_index   , token_val, layout)

            curr_cell = AlignmentCell(row_index, offset_width)

            if prev_cell_key in cell_groups:
                prev_cells = cell_groups[prev_cell_key]
                del cell_groups[prev_cell_key]
                cell_groups[curr_cell_key] = prev_cells + [curr_cell]
            else:
                cell_groups[curr_cell_key] = [curr_cell]

    return cell_groups


def _is_last_sep_token(ctx_key: AlignmentCellKey, row: TokenRow) -> bool:
    return all(
        token.typ in (TokenType.NEWLINE, TokenType.COMMENT, TokenType.WHITESPACE)
        for token in row[ctx_key.col_index + 1 :]
    )


def _realigned_contents(table: TokenTable, cell_groups: CellGroups) -> str:
    for ctx_key, cells in sorted(cell_groups.items()):
        if len(cells) <= 1:
            continue

        col_idx = ctx_key.col_index - 1

        max_offset_width = max(cell.offset_width for cell in cells)

        cells_and_rows  = [(cell, table[cell.row_idx]) for cell in cells]
        cell_row_tokens = [
            (cell, row, row[col_idx]) for cell, row in cells_and_rows if col_idx < len(row)
        ]

        is_numeric_cell_group = True
        all_prefix_lens       = set()
        for _, row, token in cell_row_tokens:
            maybe_number = token.val.strip().replace('_', "")
            if not maybe_number.isdigit():
                is_numeric_cell_group = False

            prefix_lens = [
                len(token.val) for _prefix_idx, token in enumerate(row) if _prefix_idx < col_idx
            ]
            all_prefix_lens.add(sum(prefix_lens))

        if len(all_prefix_lens) > 1:
            # don't align cell groups with prefixes of different length
            break

        for cell, row, token in cell_row_tokens:
            extra_offset = max_offset_width - cell.offset_width
            if extra_offset == 0:
                continue

            if is_numeric_cell_group:
                padded_token_val = " " * extra_offset + token.val
            elif _is_last_sep_token(ctx_key, row):
                # don't align if this is the last token of the row
                continue
            else:
                padded_token_val = token.val + " " * extra_offset

            padded_token = Token(TokenType.CODE, padded_token_val)
            row[col_idx] = padded_token

    return "".join("".join(token.val for token in row) for row in table)


def align_formatted_str(src_contents: str) -> FileContent:
    table: TokenTable = [[]]
    for token in _tokenize_for_alignment(src_contents):
        if DEBUG_LVL >= 2:
            print(f"TOKEN: {token.val:<50} {token}")

        table[-1].append(token)
        if token.typ == TokenType.NEWLINE:
            table.append([])
        else:
            is_block_token = token.typ in (TokenType.BLOCK, TokenType.COMMENT, TokenType.WHITESPACE)
            assert is_block_token or "\n" not in token.val

    if DEBUG_LVL >= 1:
        for row in table:
            print("ROW: ", end="")
            for tok_cell in row:
                print(tok_cell, end="\n     ")
            print()

    for _, row in _iter_formattable_rows(table):
        _normalize_strings(row)

    alignment_contexts = list(_iter_alignment_contexts(table))
    cell_groups        = _find_cell_groups(alignment_contexts)

    if DEBUG_LVL >= 2:
        for cell_key, cells in sorted(cell_groups.items()):
            if len(cells) > 1:
                print('CELL', len(cells), cell_key)
                for _cell in sorted(cells):
                    print("\t\t", _cell)

    return _realigned_contents(table, cell_groups)


IS_FORK_METHOD_AVAILABLE = sys.platform != 'win32'


def set_fork_method():
    # NOTE (mb 2020-08-09): Since we vendor black (and we don't monkey patch),
    #   we don't require any restriction to the 'fork' method, 'spawn' should
    #   work just as well. Be aware of this, if you want to return to the
    #   monkey patching method.

    is_fork_method_setable = (
        IS_FORK_METHOD_AVAILABLE
        and hasattr(mp, 'get_start_method')
        and mp.get_start_method(allow_none=True) is None
    )
    # Method 'fork' is the only thing that works for us,
    #   since we're monkey patching, we need the memory
    #   state to be preserved.
    if is_fork_method_setable:
        # NOTE (mb 2020-08-09): This is actually requred on MacOS,
        #   on Linux this appears to be the default anyway.
        #   https://bugs.python.org/issue33725
        mp.set_start_method('fork')


PY36_VERSIONS = {
    black.mode.TargetVersion.PY36,
    black.mode.TargetVersion.PY37,
    black.mode.TargetVersion.PY38,
    black.mode.TargetVersion.PY39,
}


def _mode_override_defaults(mode: black.mode.Mode) -> black.mode.Mode:
    return black.mode.Mode(
        target_versions=PY36_VERSIONS,
        line_length=mode.line_length,
        string_normalization=False,
        is_pyi=mode.is_pyi,
    )


original_format_str = black.format_str


@functools.wraps(black.format_str)
def format_str(src_contents: str, *, mode: black.mode.Mode) -> black.FileContent:
    mode = _mode_override_defaults(mode)

    black_dst_contents = original_format_str(src_contents, mode=mode)
    sjfmt_dst_contents = align_formatted_str(black_dst_contents)
    return sjfmt_dst_contents


def main(*args, **kwargs) -> None:
    # set_fork_method()
    mp.freeze_support()
    try:
        # monkey patch
        black.format_str = format_str

        black.main.help = "Another uncompromising code formatter."
        black.main      = click.version_option(version=__version__)(black.main)
        black.main(*args, **kwargs)
    finally:
        # monkey unpatch
        black.format_str = original_format_str


if __name__ == '__main__':
    main()
