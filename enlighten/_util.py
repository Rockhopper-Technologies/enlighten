
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten utility submodule**

Provides utility functions and objects
"""

try:
    BASESTRING = basestring
except NameError:
    BASESTRING = str


def format_time(seconds):
    """
    Args:
        seconds (float): amount of time

    Format time string for eta and elapsed
    """

    # Always do minutes and seconds in mm:ss format
    minutes = seconds // 60
    hours = minutes // 60
    rtn = u'{0:02.0f}:{1:02.0f}'.format(minutes % 60, seconds % 60)

    #  Add hours if there are any
    if hours:

        rtn = u'{0:d}h {1}'.format(int(hours % 24), rtn)

        #  Add days if there are any
        days = int(hours // 24)
        if days:
            rtn = u'{0:d}d {1}'.format(days, rtn)

    return rtn


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
