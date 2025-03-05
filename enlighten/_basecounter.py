# -*- coding: utf-8 -*-
# Copyright 2017 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten base counter submodule**

Provides BaseCounter and PrintableCounter classes
"""

import time

from enlighten._util import BASESTRING, EnlightenWarning, lru_cache, warn_best_level

try:
    from collections.abc import Iterable
except ImportError:  # pragma: no cover(Python 2)
    from collections import Iterable  # pylint: disable=deprecated-class


class BaseCounter(object):
    """
    Args:
        manager(:py:class:`Manager`): Manager instance. Required.
        color(str): Color as a string or RGB tuple (Default: None)

    Base class for counters
    """

    __slots__ = ('_color', '_count', 'manager', 'start_count')
    _repr_attrs = ('count', 'color')
    _placeholder_ = u'___ENLIGHTEN_PLACEHOLDER___'
    _placeholder_len_ = len(_placeholder_)

    def __repr__(self):

        params = []
        for attr in self._repr_attrs:
            value = getattr(self, attr)
            if value is not None:
                params.append('%s=%r' % (attr, value))

        return '%s(%s)' % (self.__class__.__name__, ', '.join(params))

    def __init__(self, keywords=None, **kwargs):

        if keywords is not None:
            kwargs = keywords

        self._count = self.start_count = kwargs.pop('count', 0)
        self._color = None

        self.manager = kwargs.pop('manager', None)
        if self.manager is None:
            raise TypeError('manager must be specified')

        self.color = kwargs.pop('color', None)

    @property
    def count(self):
        """
        Running count
        A property so additional logic can be added in children
        """

        return self._count

    @count.setter
    def count(self, value):

        self._count = value

    @property
    def color(self):
        """
        Color property

        Preferred to be a string or iterable of three integers for RGB.
        Single integer supported for backwards compatibility
        """

        color = self._color
        return color if color is None else color[0]

    @color.setter
    def color(self, value):

        if value is None:
            self._color = None

        elif isinstance(value, list):
            self._color = (value, self._resolve_color(tuple(value)))

        else:
            self._color = (value, self._resolve_color(value))

    @lru_cache(maxsize=512)
    def _resolve_color(self, value):
        """
        Caching method to resolve a color to terminal code
        """

        # Color provided as an int form 0 to 255
        if isinstance(value, int) and 0 <= value <= 255:
            return self.manager.term.color(value)

        # Color provided as a string
        if isinstance(value, BASESTRING):
            term = self.manager.term
            color_cap = self.manager.term.formatter(value)
            if not color_cap and term.does_styling and term.number_of_colors:
                raise AttributeError('Invalid color specified: %s' % value)
            return color_cap

        # Color provided as an RGB iterable
        if isinstance(value, Iterable) and \
                len(value) == 3 and \
                all(isinstance(_, int) and 0 <= _ <= 255 for _ in value):
            return self.manager.term.color_rgb(*value)

        # Invalid format given
        raise AttributeError('Invalid color specified: %s' % repr(value))

    def _colorize(self, content):
        """
        Args:
            content(str): Color as a string or number 0 - 255 (Default: None)

        Returns:
            :py:class:`str`: content formatted with color

        Format ``content`` with the color specified for this progress bar

        If no color is specified for this instance, the content is returned unmodified
        """

        # Used spec cached by color.setter if available
        return content if self._color is None else self._color[1](content)

    def update(self, *args, **kwargs):
        """
        Placeholder for update method
        """

        raise NotImplementedError

    def __call__(self, *args):

        for iterable in args:
            if not isinstance(iterable, Iterable):
                raise TypeError('Argument type %s is not iterable' % type(iterable).__name__)

            for element in iterable:
                yield element
                self.update()


class PrintableCounter(BaseCounter):  # pylint: disable=too-many-instance-attributes
    """
    Base class for printable counters
    """

    __slots__ = ('_closed', '_count_updated', 'enabled', '_fill', 'last_update',
                 'leave', 'min_delta', '_pinned', 'start')

    def __init__(self, keywords=None, **kwargs):

        if keywords is not None:  # pragma: no branch
            kwargs = keywords
        super(PrintableCounter, self).__init__(keywords=kwargs)

        self._closed = 0.0  # Time when closed, 0 indicates it's open
        self.enabled = kwargs.pop('enabled', True)
        self._fill = u' '
        self.fill = kwargs.pop('fill', u' ')
        self.leave = kwargs.pop('leave', True)
        self.min_delta = kwargs.pop('min_delta', 0.1)
        self._pinned = False
        self.last_update = self.start = self._count_updated = time.time()

    def __str__(self):

        # format() returns Unicode so encode if Python 2
        return self.format() if BASESTRING is str else self.format().encode('utf-8')

    def __unicode__(self):  # pragma: no cover(Python 2)
        return self.format()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def count(self):
        """
        Running count
        """

        return self._count

    @count.setter
    def count(self, value):

        self._count = value
        self._count_updated = time.time()

    @property
    def elapsed(self):
        """
        Get elapsed time is seconds (float)
        """

        return (self._closed or time.time()) - self.start

    @property
    def fill(self):
        """
        Fill character used in formatting
        """
        return self._fill

    @fill.setter
    def fill(self, value):

        char_len = self.manager.term.length(value)
        if char_len != 1:
            raise ValueError('fill character must be a length of 1 '
                             'when printed. Length: %d, Value given: %r' % (char_len, value))

        self._fill = value

    @property
    def position(self):
        """
        Fetch position from the manager
        """

        return self.manager.counters.get(self, 0)

    def clear(self, flush=True):
        """
        Args:
            flush(bool): Flush stream after clearing bar (Default:True)

        Clear bar
        """

        if self.enabled:
            self.manager.write(flush=flush, counter=self)
            self.last_update = 0

    def close(self, clear=False):
        """
        Do final refresh and remove from manager

        If ``leave`` is True, the default, the effect is the same as :py:meth:`refresh`.

        When closed, elapsed time will stop even when refreshed
        """

        # Warn if counter is already closed
        if self._closed:
            warn_best_level('Closing already closed counter: %r' % self, EnlightenWarning)
        else:
            self._closed = time.time()

        if clear and not self.leave:
            self.clear()

        # If counter was already closed we may not know the position
        elif self in self.manager.counters:
            self.refresh()

        self.manager.remove(self)

    def format(self, width=None, elapsed=None):
        """
        Format counter for printing
        """

        raise NotImplementedError

    def refresh(self, flush=True, elapsed=None):
        """
        Args:
            flush(bool): Flush stream after writing bar (Default:True)
            elapsed(float): Time since started. Automatically determined if :py:data:`None`

        Redraw bar
        """

        if self.enabled:
            self.last_update = time.time()
            self.manager.write(output=self.format, flush=flush, counter=self, elapsed=elapsed)

    def _fill_text(self, text, width, offset=None):
        """
        Args:
            text (str): String to modify
            width (int): Width in columns to make progress bar
            offset(int): Number of non-printable characters to account for when formatting

        Returns:
            :py:class:`str`: String with ``self._placeholder_`` replaced with fill characters

        Replace ``self._placeholder_`` in string with appropriate number of fill characters
        """

        fill_count = text.count(self._placeholder_)
        if not fill_count:
            return text

        if offset is None:
            remaining = width - self.manager.term.length(text) + self._placeholder_len_ * fill_count
        else:
            remaining = width - len(text) + offset + self._placeholder_len_ * fill_count

        # If only one substitution is required, make it
        if fill_count == 1:
            return text.replace(self._placeholder_, self.fill * remaining)

        # Determine even fill size and number of extra characters to fill
        fill_size, extra = divmod(remaining, fill_count)

        # Add extra fill is needed, add extra fill evenly starting from the end
        if extra:
            text = text.replace(self._placeholder_, self.fill * fill_size, fill_count - extra)
            return text.replace(self._placeholder_, self.fill * (fill_size + 1))

        # If fill is even, replace evenly
        return text.replace(self._placeholder_, self.fill * fill_size)

    def reset(self):
        """
        Reset to initial state
        """

        self.last_update = self.start = self._count_updated = time.time()
        self._count = self.start_count
        self._closed = 0.0
