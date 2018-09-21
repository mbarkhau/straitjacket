# This file is part of the straitjacket project
# https://github.com/mbarkhau/straitjacket
#
# (C) 2018 Manuel Barkhau (@mbarkhau)
# SPDX-License-Identifier: MIT

import sys

import black
from . import sjfmt

if __name__ == '__main__':
    black.patch_click()
    sys.exit(sjfmt.main())
