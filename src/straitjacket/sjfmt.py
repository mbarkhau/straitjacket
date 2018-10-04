# This file is part of the straitjacket project
# https://github.com/mbarkhau/straitjacket
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import os
import re
import sys
import pathlib as pl

import enum
import typing as typ

import black


DEBUG = 0


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


# TODO (mb 2018-09-12): Alternatively, implement this using
# lookback by counting backslashes.

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
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
\"
"""


QUOTE_END_PATTERN = r"""
(
    (?<=^)
    | (?<=[^\\])
    | (?<=[^\\]\\\\)
    | (?<=[^\\]\\\\\\\\)
    | (?<=[^\\]\\\\\\\\\\\\)
)
'
"""


NO_ALIGN_BLOCK_END_MATCHERS = {
    "'''": re.compile(TRIPPLE_QUOTE_END_PATTERN       , flags=re.VERBOSE),
    '"""': re.compile(TRIPPLE_DOUBLE_QUOTE_END_PATTERN, flags=re.VERBOSE),
    '"'  : re.compile(DOUBLE_QUOTE_END_PATTERN        , flags=re.VERBOSE),
    "'"  : re.compile(QUOTE_END_PATTERN               , flags=re.VERBOSE),
    "#"  : re.compile(r"$", flags=re.MULTILINE),
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


TokenRow = typ.List[Token]


def _tokenize_for_alignment(src_contents: str) -> typ.Iterator[Token]:
    rest      = src_contents
    prev_rest = None

    while rest:
        assert rest != prev_rest, "No progress at: " + repr(rest[:40])
        prev_rest = rest

        curr_token_sep = TOKEN_SEP_RE.search(rest)
        assert curr_token_sep is not None
        curr_token_start, curr_token_end = curr_token_sep.span()

        # newline match has zero width
        is_newline = curr_token_start == curr_token_end
        if is_newline:
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
    """Disambiguate between lines with different layout/structure

    We only want to align lines which have the same structure of
    indent and separators. Any difference in the number of elements
    or type of separators causes alignment to be disabled.
    """

    typ: TokenType
    # val is only set if it should cause a different prefix
    # eg. if a separator is a comma vs a period.
    val: typ.Optional[TokenVal]


# Tokens which have values which are relevant to to the layout of
# a cell group.
LAYOUT_VAL_TOKENS = set([TokenType.SEPARATOR, TokenType.INDENT])

RowLayoutTokens = typ.Tuple[RowLayoutToken, ...]


class AlignmentContextKey(typ.NamedTuple):
    """Does not change between multiple lines that can be aligned."""

    col_idx: ColIndex
    tok_typ: TokenType
    tok_val: TokenVal
    layout : RowLayoutTokens


AlignmentContext = typ.Dict[AlignmentContextKey, OffsetWidth]


class AlignmentCellKey(typ.NamedTuple):
    last_row_index: RowIndex
    col_index     : ColIndex
    token_val     : TokenVal
    layout        : RowLayoutTokens


class AlignmentCell(typ.NamedTuple):
    row_idx     : RowIndex
    offset_width: OffsetWidth


CellGroups = typ.Dict[AlignmentCellKey, typ.List[AlignmentCell]]


def _is_dict_key_symbol_access(col_index: int, tok_cell: Token, row: TokenRow) -> bool:
    return (
        tok_cell.typ == TokenType.SEPARATOR
        and tok_cell.val in (":", "]")
        and col_index > 0
        and row[col_index - 1].typ == TokenType.BLOCK
        and SYMBOL_STRING_RE.match(row[col_index - 1].val)
    )


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
        and SYMBOL_STRING_RE.match(row[col_index + 5].val)
    )


def _is_single_quoted_non_symbol(col_index: int, tok_cell: Token) -> bool:
    return (
        tok_cell.typ == TokenType.BLOCK
        and len(tok_cell.val) > 2
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
        if _is_single_quoted_non_symbol(col_index, tok_cell):
            normalized_token_val = '"' + tok_cell.val[1:-1] + '"'
            row[col_index] = Token(TokenType.BLOCK, normalized_token_val)


def _find_alignment_contexts(table: TokenTable) -> typ.Iterator[AlignmentContext]:
    is_fmt_enabled = True

    for row in table:
        ctx   : AlignmentContext = {}
        layout: RowLayoutTokens  = tuple()

        if is_fmt_enabled:
            _normalize_strings(row)

        for col_index, token in enumerate(row):
            if token.typ == TokenType.COMMENT and "fmt: off" in token.val:
                is_fmt_enabled = False
            if token.typ == TokenType.COMMENT and "fmt: on" in token.val:
                is_fmt_enabled = True

            if not is_fmt_enabled:
                continue

            layout_token_val: typ.Optional[TokenVal]
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
                else:
                    layout_token_val = None
            else:
                layout_token_val = None

            layout += (RowLayoutToken(token.typ, layout_token_val),)

            if token.val in ALIGN_BEFORE_TOKENS:
                assert token.typ == TokenType.SEPARATOR
                prev_token = row[col_index - 1]
                if prev_token.typ != TokenType.SEPARATOR:
                    offset_width = len(prev_token.val)
                    ctx_key      = AlignmentContextKey(col_index, token.typ, token.val, layout)
                    ctx[ctx_key] = offset_width

        yield ctx


def _find_cell_groups(alignment_contexts: typ.List[AlignmentContext]) -> CellGroups:
    cell_groups: typ.Dict[AlignmentCellKey, typ.List[AlignmentCell]] = {}
    for row_index, ctx in enumerate(alignment_contexts):
        ctx_items = sorted(ctx.items())
        for ctx_key, offset_width in ctx_items:
            col_index, token_typ, token_val, layout = ctx_key

            prev_cell_key = AlignmentCellKey(row_index - 1, col_index, token_val, layout)
            curr_cell_key = AlignmentCellKey(row_index, col_index, token_val, layout)

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
    prev_col_index = -1
    for ctx_key, cells in sorted(cell_groups.items()):
        prev_col_index = ctx_key.col_index
        if len(cells) < 2:
            continue

        max_offset_width = max(ow for _, ow in cells)
        for row_index, offset_width in cells:
            extra_offset = max_offset_width - offset_width
            if extra_offset == 0:
                continue

            row          = table[row_index]
            left_token   = row[ctx_key.col_index - 1]
            maybe_number = left_token.val.strip().replace("_", "")

            if maybe_number.isdigit():
                padded_left_token_val = " " * extra_offset + left_token.val
            elif _is_last_sep_token(ctx_key, row):
                # don't align if this is the last token of the row
                continue
            else:
                padded_left_token_val = left_token.val + " " * extra_offset
            padded_token = Token(TokenType.CODE, padded_left_token_val)
            padded_token = Token(TokenType.CODE, padded_left_token_val)
            row[ctx_key.col_index - 1] = padded_token

    return "".join("".join(token.val for token in row) for row in table)


def _align_formatted_str(src_contents: str) -> FileContent:
    table: TokenTable = [[]]
    for token in _tokenize_for_alignment(src_contents):
        if DEBUG:
            print("TOKEN: ", repr(token.val).ljust(50), token)
        table[-1].append(token)
        if token.typ == TokenType.NEWLINE:
            table.append([])
        else:
            is_block_token = token.typ in (TokenType.BLOCK, TokenType.COMMENT, TokenType.WHITESPACE)
            assert is_block_token or "\n" not in token.val

    if DEBUG:
        for row in table:
            print("ROW: ", end="")
            for tok_cell in row:
                print(tok_cell, end="\n     ")
            print()

    alignment_contexts = list(_find_alignment_contexts(table))
    cell_groups        = _find_cell_groups(alignment_contexts)

    if DEBUG:
        for cell_key, cells in cell_groups.items():
            if len(cells) > 1:
                print("CELL", len(cells), cell_key)
                for all_cell in cells:
                    print("\t\t", all_cell)

    return _realigned_contents(table, cell_groups)


def patch_format_str():
    if hasattr(black, '_black_format_str_unpatched'):
        return

    black_format_str = black.format_str

    def format_str_wrapper(
        src_contents: str, line_length: int, *, mode: black.FileMode = black.FileMode.AUTO_DETECT
    ) -> black.FileContent:
        black_dst_contents = black_format_str(src_contents, line_length, mode=mode)
        sjfmt_dst_contents = _align_formatted_str(black_dst_contents)
        return sjfmt_dst_contents

    black.format_str = format_str_wrapper
    setattr(black, '_black_format_str_unpatched', black_format_str)


patch_format_str()
main = black.main


if __name__ == '__main__':
    black.patch_click()
    main()
