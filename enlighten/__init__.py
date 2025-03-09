# -*- coding: utf-8 -*-
# Copyright 2017 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten Progress Bar**

Provides progress bars and counters which play nice in a TTY console
"""

from enlighten.counter import Counter, StatusBar, SubCounter
from enlighten.manager import Manager, get_manager
from enlighten._util import EnlightenWarning, Justify, format_time


__version__ = '1.14.0'
__all__ = ['Counter', 'EnlightenWarning', 'format_time', 'get_manager', 'Justify',
           'Manager', 'NotebookManager', 'StatusBar', 'SubCounter']

try:
    from enlighten.manager import NotebookManager  # noqa: F401
except ImportError:
    __all__.remove('NotebookManager')
