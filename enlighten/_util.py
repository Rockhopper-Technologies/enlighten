
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten utility submodule**

Provides utility functions and objects
"""


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
