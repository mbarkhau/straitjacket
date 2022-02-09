<div align="center">
<p align="center">
  <img alt="logo" src="https://gitlab.com/mbarkhau/straitjacket/-/raw/master/logo.png">
</p>
</div>


# [StraitJacket: Another Uncompromising Code Formatter for Python][repo_ref]

StraitJacket is a wrapper around black which implements post
processing to perform automatic code alignment.

Project/Repo:

[![MIT License][license_img]][license_ref]
[![Supported Python Versions][pyversions_img]][pyversions_ref]
[![CalVer v202202.1024][version_img]][version_ref]
[![PyPI Version][pypi_img]][pypi_ref]
[![PyPI Downloads][downloads_img]][downloads_ref]

Code Quality/CI:

[![GitHub Build Status][github_build_img]][github_build_ref]
[![GitLab Build Status][gitlab_build_img]][gitlab_build_ref]
[![Type Checked with mypy][mypy_img]][mypy_ref]
[![Code Coverage][codecov_img]][codecov_ref]
[![Code Style: sjfmt][style_img]][style_ref]


|               Name                  |    role           |  since  | until |
|-------------------------------------|-------------------|---------|-------|
| Manuel Barkhau (mbarkhau@gmail.com) | author/maintainer | 2018-10 | -     |


<!--
  To update the TOC:
  $ pip install md-toc
  $ md_toc -i gitlab README.md
-->


[](TOC)

  - [Alignment](#alignment)
  - [Usage](#usage)
  - [Editor/Tooling Integration](#editortooling-integration)
      - [sublack](#sublack)
      - [vscode python extension](#vscode-python-extension)
      - [BlackPycharm](#blackpycharm)
  - [Flake8](#flake8)

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

## Editor/Tooling Integration

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

PS C:\Users\Username> (gcm sjfmt).Path
C:\Python37\Scripts\sjfmt.exe
```

### [sublack](https://github.com/jgirardet/sublack):

```json
{

    "black_command": "C:/Python37/Scripts/sjfmt.exe",
    "black_line_length": 100,
    // ...
}
```

Document formatting can be triggered with `Ctrl+Alt+F`.


### [vscode python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)


```json
{
    "python.formatting.provider": "black",
    "python.formatting.blackPath": "C:\\Python37\\Scripts\\sjfmt.exe",
    "python.formatting.blackArgs": [
        "--line-length", "100",
        "--py36",
        "--skip-string-normalization"
    ],
}
```

Document formatting can be triggered with `Shift+Alt+F`.


### [BlackPycharm](https://github.com/pablogsal/black-pycharm)

Install the plugin `black-pycharm`, which can be found in
`Settings > Plugins > Brows Repositories`. You may have to
restart PyCharm for the plugin to load.

To configure the path, go to `Settings > Tools > BlackPycharm
Configuration` and set `Path to Black executable` to the location
of the sjfmt binary.

You can reformat your code using `Ctrl + Shift + A` to access the
`Find Action` panel. The name of the action to format your code
is `Reformat code (BLACK)`. You may want to rebind this action,
at least in my setup the default binding didn't seem to work.


## Flake8

By the nature of this plugin, certain flake8 codes will be
violated. This is an excerpt from what you might put in your
`setup.cfg` to ignore these:

```
[flake8]
ignore =
    # No whitespace after paren open "("
    E201
    # No whitespace before paren ")"
    E202
    # Whitespace before ":"
    E203
    # Multiple spaces before operator
    E221
    # Multiple spaces after operand
    E222
    # Multiple spaces after ':'
    E241
    # Multiple spaces before keyword
    E272
    # Spaces around keyword/parameter equals
    E251
```


[repo_ref]: https://github.com/mbarkhau/straitjacket

[github_build_img]: https://github.com/mbarkhau/straitjacket/workflows/CI/badge.svg
[github_build_ref]: https://github.com/mbarkhau/straitjacket/actions?query=workflow%3ACI

[gitlab_build_img]: https://gitlab.com/mbarkhau/straitjacket/badges/master/pipeline.svg
[gitlab_build_ref]: https://gitlab.com/mbarkhau/straitjacket/pipelines

[codecov_img]: https://gitlab.com/mbarkhau/straitjacket/badges/master/coverage.svg
[codecov_ref]: https://mbarkhau.gitlab.io/straitjacket/cov

[license_img]: https://img.shields.io/badge/License-MIT-blue.svg
[license_ref]: https://gitlab.com/mbarkhau/straitjacket/blob/master/LICENSE

[mypy_img]: https://img.shields.io/badge/mypy-checked-green.svg
[mypy_ref]: https://mbarkhau.gitlab.io/straitjacket/mypycov

[style_img]: https://img.shields.io/badge/code%20style-%20sjfmt-f71.svg
[style_ref]: https://gitlab.com/mbarkhau/straitjacket/

[pypi_img]: https://img.shields.io/badge/PyPI-wheels-green.svg
[pypi_ref]: https://pypi.org/project/straitjacket/#files

[downloads_img]: https://pepy.tech/badge/straitjacket/month
[downloads_ref]: https://pepy.tech/project/straitjacket

[version_img]: https://img.shields.io/static/v1.svg?label=CalVer&message=v202202.1024&color=blue
[version_ref]: https://pypi.org/project/bumpver/

[pyversions_img]: https://img.shields.io/pypi/pyversions/straitjacket.svg
[pyversions_ref]: https://pypi.python.org/pypi/straitjacket

