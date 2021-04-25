# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten manager submodule**

Provides Manager classes and utilities
"""

import sys

from enlighten._counter import Counter
from enlighten._manager import Manager


def get_manager(stream=None, counter_class=Counter, **kwargs):
    """
    Args:
        stream(:py:term:`file object`): Output stream. If :py:data:`None`,
            defaults to :py:data:`sys.stdout`
        counter_class(:py:term:`class`): Progress bar class (Default: :py:class:`Counter`)
        kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
            will passed to the manager class.

    Returns:
        :py:class:`Manager`: Manager instance

    Convenience function to get a manager instance

    If ``stream`` is not attached to a TTY, the :py:class:`Manager` instance is disabled.
    """

    stream = sys.stdout if stream is None else stream
    isatty = hasattr(stream, 'isatty') and stream.isatty()
    kwargs['enabled'] = isatty and kwargs.get('enabled', True)
    return Manager(stream=stream, counter_class=counter_class, **kwargs)
