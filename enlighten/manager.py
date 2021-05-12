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


try:
    from IPython import get_ipython
    IN_NOTEBOOK = 'IPKernelApp' in get_ipython().config
    from enlighten._notebook_manager import NotebookManager  # pylint: disable=ungrouped-imports
except (ImportError, AttributeError):
    IN_NOTEBOOK = False


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

    If running inside a notebook, a :py:class:`NotebookManager`
    instance is returned. otherwise a standard :py:class:`Manager` instance is returned.

    If a a standard :py:class:`Manager` instance is used and ``stream`` is not attached
    to a TTY, the :py:class:`Manager` instance is disabled.
    """

    if IN_NOTEBOOK:
        return NotebookManager(stream=stream, counter_class=counter_class, **kwargs)

    stream = sys.stdout if stream is None else stream
    isatty = hasattr(stream, 'isatty') and stream.isatty()
    kwargs['enabled'] = isatty and kwargs.get('enabled', True)
    return Manager(stream=stream, counter_class=counter_class, **kwargs)
