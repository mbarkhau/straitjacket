# This file is part of the straitjacket project
# https://gitlab.com/mbarkhau/straitjacket
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT
from straitjacket import sjfmt
import black
import blackd

sjfmt.patch_format_str()
main = blackd.main


if __name__ == '__main__':
    black.patch_click()
    main()
