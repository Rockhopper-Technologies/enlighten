# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Functions to help with build and setup
"""

import re


RE_VERSION = re.compile(r'__version__\s*=\s*[\'\"](.+)[\'\"]$')


def get_version(filename):
    """
    Get __version__ definition out of a source file
    """

    with open(filename) as sourcecode:
        for line in sourcecode:
            version = RE_VERSION.match(line)
            if version:
                return version.group(1)

    return None
