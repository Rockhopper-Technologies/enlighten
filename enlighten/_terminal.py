# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten terminal submodule**

Provides Terminal class
"""

from blessed import Terminal as _Terminal


class Terminal(_Terminal):
    """
    Subclass of :py:class:`blessings.Terminal`

    Adds convenience methods and caching for width and height
    """

    def __init__(self, *args, **kwargs):

        super(Terminal, self).__init__(*args, **kwargs)
        self._cache = {}

    def reset(self):
        """
        Reset scroll window and cursor to default
        """

        self.stream.write(self.normal_cursor)
        self.stream.write(self.csr(0, self.height))
        self.stream.write(self.move(self.height, 0))

    def feed(self):
        """
        Feed a single line
        """

        self.stream.write(self.cud1 or '\n')

    def change_scroll(self, position):
        """
        Args:
            position (int): Vertical location to end scroll window

        Change scroll window
        """

        self.stream.write(self.hide_cursor)
        self.stream.write(self.csr(0, position))
        self.stream.write(self.move(position, 0))

    def move_to(self, xpos, ypos):
        """
        Move cursor to specified position
        """

        self.stream.write(self.move(ypos, xpos))

    def _height_and_width(self):
        """
        Override for blessings.Terminal._height_and_width
        Adds caching
        """

        try:
            return self._cache['height_and_width']
        except KeyError:
            handw = self._cache['height_and_width'] = super(Terminal, self)._height_and_width()
            return handw

    def clear_cache(self):
        """
        Clear cached terminal returns
        """

        self._cache.clear()
