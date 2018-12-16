# This file is part of the straitjacket project
# https://gitlab.com/mbarkhau/straitjacket
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
from straitjacket import sjfmt
import black
import blackd


def main(*args, **kwargs) -> None:
    sjfmt.patch_format_str()
    black.patch_click()
    return blackd.main(*args, **kwargs)


if __name__ == '__main__':
    main()
