# -*- coding: utf-8 -*-
# Copyright 2017 - 2023 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten counter submodule**

Provides Counter class
"""

from enlighten._counter import Counter as _Counter
from enlighten._counter import SubCounter  # pylint: disable=unused-import # noqa: F401
from enlighten._statusbar import StatusBar  # pylint: disable=unused-import # noqa: F401
from enlighten.manager import get_manager


# Counter is defined here to avoid circular dependencies
class Counter(_Counter):  # pylint: disable=missing-docstring
    # pylint: disable=too-many-instance-attributes

    __doc__ = _Counter.__doc__

    def __new__(cls, **kwargs):

        manager = kwargs.pop('manager', None)
        stream = kwargs.pop('stream', None)

        if manager is None:
            manager = get_manager(stream=stream)

        return manager.counter(**kwargs)
