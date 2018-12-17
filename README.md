# [StraitJacket: Another Uncompromising Code Formatter for Python][repo_ref]

StraitJacket is a wrapper around black which implements post
processing to perform automatic code alignment.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![PyCalVer v201812.0007-alpha][version_img]][version_ref]
[![PyPI Version][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Style: sjfmt][style_img]][style_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Build Status][build_img]][build_ref]


|               Name                  |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-10 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc -i gitlab README.md
-->


[](TOC)

[](TOC)

## Alignment

Example of automatic alignment.

```python
class TokenType(enum.Enum):           # class TokenType(enum.Enum):

    INDENT    = 0                     #     INDENT = 0
    SEPARATOR = 1                     #     SEPARATOR = 1
    CODE      = 2                     #     CODE = 2


Indent      = str                     # Indent = str
RowIndex    = int                     # RowIndex = int
ColIndex    = int                     # ColIndex = int
OffsetWidth = int                     # OffsetWidth = int
TokenTable  = typ.List[TokenRow]      # TokenTable = typ.List[TokenRow]
```

## Usage

Usage is exactly the same as for `black`, except that the command is named `sjfmt`.

```shell
$ pip install straitjacket
$ sjfmt --help
Usage: sjfmt [OPTIONS] [SRC]...

  Another uncompromising code formatter.

Options:
  -l, --line-length INTEGER       How many characters per line to allow.
                                  [default: 88]
  --py36                          Allow using Python 3.6-only syntax on all
```

## Editors

Plugins for your editor usually support setting a custom path to black. You
can simply point to sjfmt instead.

Unix
```shell
$ which sjfmt
/home/user/miniconda3/envs/py36/bin/sjfmt
$ which sjfmtd
/home/user/miniconda3/envs/py36/bin/sjfmtd
```

Windows
```shell
C:\Users\Username>where sjfmt
C:\Python37\Scripts\sjfmt.exe

or

PS C:\Users\ManuelBarkhau> (gcm sjfmt).Path
C:\Python37\Scripts\sjfmt.exe
```

[sublack]:

```json
{
      "black_command": "C:/Python37/Scripts/sjfmt.exe",
      "black_line_length": 100,
      // ...
}
```



[repo_ref]: https://gitlab.com/mbarkhau/straitjacket

[build_img]: https://gitlab.com/mbarkhau/straitjacket/badges/master/pipeline.svg
[build_ref]: https://gitlab.com/mbarkhau/straitjacket/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/straitjacket/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/straitjacket/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/straitjacket/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: http://mypy-lang.org/

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/straitjacket/#files

[downloads_img]: https://pepy.tech/badge/straitjacket
[downloads_ref]: https://pepy.tech/project/straitjacket

[version_img]: https://img.shields.io/badge/PyCalVer-v201812.0007--alpha-blue.svg
[version_ref]: https://pypi.org/project/pycalver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/straitjacket.svg
[pyversions_ref]: https://pypi.python.org/pypi/straitjacket

