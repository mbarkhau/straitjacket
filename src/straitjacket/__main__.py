#!/usr/bin/env python
# This file is part of the straitjacket project
# https://gitlab.com/mbarkhau/straitjacket
#
# Copyright (c) 2019 Manuel Barkhau (mbarkhau@gmail.com) - MIT License
# SPDX-License-Identifier: MIT

import os
import sys

from . import sjfmt


# To enable pretty tracebacks:
#   echo "export ENABLE_BACKTRACE=1;" >> ~/.bashrc
if os.environ.get('ENABLE_BACKTRACE') == "1":
    import backtrace
    backtrace.hook(align=True, strip_path=True, enable_on_envvar_only=True)


if __name__ == '__main__':
    sjfmt.main()
    sys.exit(0)
