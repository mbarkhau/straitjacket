#!/usr/bin/env python
# This file is part of the straitjacket project
# https://gitlab.com/mbarkhau/straitjacket
#
# Copyright (c) 2018 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

try:
    import backtrace

    # To enable pretty tracebacks:
    #   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)
except ImportError:
    pass


import sys

from . import sjfmt


if __name__ == '__main__':
    sjfmt.main()
    sys.exit(0)
