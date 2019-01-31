# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten Progress Bar**

Provides progress bars and counters which play nice in a TTY console
"""

from enlighten.counter import Counter
from enlighten._multicounter import MultiCounter
from enlighten._manager import Manager, get_manager


__version__ = '1.1.0'
__all__ = ('Counter', 'MultiCounter', 'Manager', 'get_manager')
