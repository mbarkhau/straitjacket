# This file is part of the straitjacket project
# https://github.com/mbarkhau/straitjacket
#
# Copyright (c) 2018-2021 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import black
import click
import blackd

from straitjacket import sjfmt


def main(*args, **kwargs) -> None:
    try:
        # monkey patch
        black.format_str = sjfmt.format_str

        black.patch_click()
        blackd.main = click.version_option(version=sjfmt.__version__)(black.main)
        blackd.main(*args, **kwargs)
    finally:
        # monkey unpatch
        black.format_str = sjfmt.original_format_str


if __name__ == '__main__':
    main()
