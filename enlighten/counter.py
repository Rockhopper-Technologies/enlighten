# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten counter submodule**

Provides Counter class
"""

import sys

from enlighten._counter import Counter as _Counter
from enlighten._counter import SubCounter  # pylint: disable=unused-import # noqa: F401
from enlighten._manager import get_manager


# Counter is defined here to avoid circular dependencies
class Counter(_Counter):  # pylint: disable=missing-docstring

    __doc__ = _Counter.__doc__

    def __init__(self, **kwargs):

        manager = kwargs.get('manager', None)
        if manager is None:
            manager = get_manager(stream=kwargs.get('stream', sys.stdout),
                                  counter_class=self.__class__, set_scroll=False)
            manager.counters[self] = 1
            kwargs['manager'] = manager

        super(Counter, self).__init__(**kwargs)
