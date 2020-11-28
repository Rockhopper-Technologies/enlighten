
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten utility submodule**

Provides utility functions and objects
"""

import inspect
import os
import sys
import warnings

try:
    BASESTRING = basestring
except NameError:
    BASESTRING = str

BASE_DIR = os.path.basename(os.path.dirname(__file__))
FORMAT_MAP_SUPPORT = sys.version_info[:2] >= (3, 2)


class EnlightenWarning(Warning):
    """
    Generic warning class for Enlighten
    """


def warn_best_level(message, category):
    """
    Helper function to warn at first frame stack outside of library
    """

    level = 5  # Unused default
    for level, frame in enumerate(inspect.stack(), 1):  # pragma: no cover
        if os.path.basename(os.path.dirname(frame[1])) != BASE_DIR:
            break

    warnings.warn(message, category=category, stacklevel=level)


def format_time(seconds):
    """
    Args:
        seconds (float): amount of time

    Format time string for eta and elapsed
    """

    # Always do minutes and seconds in mm:ss format
    minutes = seconds // 60
    hours = minutes // 60
    rtn = u'%02.0f:%02.0f' % (minutes % 60, seconds % 60)

    #  Add hours if there are any
    if hours:

        rtn = u'%dh %s' % (int(hours % 24), rtn)

        #  Add days if there are any
        days = int(hours // 24)
        if days:
            rtn = u'%dd %s' % (days, rtn)

    return rtn


def raise_from_none(exc):  # pragma: no cover
    """
    Convenience function to raise from None in a Python 2/3 compatible manner
    """
    raise exc


if sys.version_info[0] >= 3:  # pragma: no branch
    exec('def raise_from_none(exc):\n    raise exc from None')  # pylint: disable=exec-used


class Justify(object):
    """
    Enumerated type for justification options

    .. py:attribute:: CENTER

        Justify center

    .. py:attribute:: LEFT

        Justify left

    .. py:attribute:: RIGHT

        Justify right

    """

    CENTER = 'center'
    LEFT = 'ljust'
    RIGHT = 'rjust'
