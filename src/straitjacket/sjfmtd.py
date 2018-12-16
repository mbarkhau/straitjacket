# This file is part of the straitjacket project
# https://gitlab.com/mbarkhau/straitjacket
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
from straitjacket import sjfmt

import click
import black
import blackd


def main(*args, **kwargs) -> None:
    sjfmt.patch_format_str()
    black.patch_click()
    blackd.main = click.version_option(version=sjfmt.__version__)(black.main)
    return blackd.main(*args, **kwargs)


if __name__ == '__main__':
    main()
