# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten base manager submodule**

Provides BaseManager class
"""

import sys
import time
from collections import OrderedDict

from blessed import Terminal

from enlighten._counter import Counter
from enlighten._statusbar import StatusBar


class BaseManager(object):
    """

    Args:
        stream(:py:term:`file object`): Output stream. If :py:data:`None`,
            defaults to :py:data:`sys.stdout`
        status_bar_class(:py:term:`class`): Status bar class (Default: :py:class:`StatusBar`)
        counter_class(:py:term:`class`): Progress bar class (Default: :py:class:`Counter`)
        set_scroll(bool): Enable scroll area redefinition (Default: :py:data:`True`)
        companion_stream(:py:term:`file object`): See :ref:`companion_stream <companion_stream>`
            below. (Default: :py:data:`None`)
        enabled(bool): Status (Default: True)
        no_resize(bool): Disable resizing support
        term(str): Terminal type passed to Blessed
        threaded(bool): When True resize handling is deferred until next write (Default: False
            unless multiple threads or multiple processes are detected)
        width(int): Static output width. If unset, width is determined dynamically
        kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
            will be used as default values when :py:meth:`counter` is called.

        Base manager class
    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, **kwargs):

        self.enabled = kwargs.get('enabled', True)  # Double duty for counters

        self.companion_stream = kwargs.pop('companion_stream', None)
        self.counter_class = kwargs.pop('counter_class', Counter)
        self.no_resize = kwargs.pop('no_resize', False)
        self.set_scroll = kwargs.pop('set_scroll', True)
        self.status_bar_class = kwargs.pop('status_bar_class', StatusBar)
        self.stream = kwargs.pop('stream', sys.stdout)
        self.threaded = kwargs.pop('threaded', None)
        self._width = kwargs.pop('width', None)

        self.counters = OrderedDict()

        self.autorefresh = []
        self._buffer = []
        self._companion_buffer = []
        self.process_exit = False
        self.refresh_lock = False
        self._resize = False
        self.resize_lock = False
        self.scroll_offset = 1

        # If terminal is kind is given, force styling
        kind = kwargs.pop('term', None)
        self.term = Terminal(stream=self.stream, kind=kind, force_styling=bool(kind))

        self.height = self.term.height
        self.width = self._width or self.term.width

        self.defaults = kwargs  # Counter defaults

    def write(self, output='', flush=True, counter=None, **kwargs):
        """
        Args:
            output(str): Output string or callable
            flush(bool): Flush the output stream after writing
            counter(:py:class:`Counter`): Bar being written (for position and auto-refresh)
            kwargs(dict): Additional arguments passed when output is callable

        Write to the stream.

        The position is determined by the counter or defaults to the bottom of the terminal

        If ``output`` is callable, it will be called with any additional keyword arguments
        to produce the output string
        """

        raise NotImplementedError()

    def stop(self):
        """
        Clean up and reset terminal

        This method should be called when the manager and counters will no longer be needed.

        Any progress bars that have ``leave`` set to :py:data:`True` or have not been closed
        will remain on the console. All others will be cleared.

        Manager and all counters will be disabled.
        """

        raise NotImplementedError()

    def _flush_streams(self):
        """
        Flush output buffers
        """

        raise NotImplementedError()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()

    def counter(self, position=None, **kwargs):
        """
        Args:
            position(int): Line number counting from the bottom of the screen
            autorefresh(bool): Refresh this counter when other bars are drawn
            replace(:py:class:`PrintableCounter`): Replace given counter with new. Position ignored.
            kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
                are passed to :py:class:`Counter`

        Returns:
            :py:class:`Counter`: Instance of counter class

        Get a new progress bar instance

        If ``position`` is specified, the counter's position will be pinned.
        A :py:exc:`ValueError` will be raised if ``position`` exceeds the screen height or
        has already been pinned by another counter.

        If ``autorefresh`` is :py:data:`True`, this bar will be redrawn whenever another bar is
        drawn assuming it had been ``min_delta`` seconds since the last update. This is usually
        unnecessary.

        .. note:: Counters are not automatically drawn when created because fields may be missing
                  if subcounters are used. To force the counter to draw before updating,
                  call :py:meth:`~Counter.refresh`.

        """

        return self._add_counter(self.counter_class, position=position, **kwargs)

    def status_bar(self, *args, **kwargs):
        """
        Args:
            position(int): Line number counting from the bottom of the screen
            autorefresh(bool): Refresh this counter when other bars are drawn
            replace(:py:class:`PrintableCounter`): Replace given counter with new. Position ignored.
            kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
                are passed to :py:class:`StatusBar`

        Returns:
            :py:class:`StatusBar`: Instance of status bar class

        Get a new status bar instance

        If ``position`` is specified, the counter's position can change dynamically if
        additional counters are called without a ``position`` argument.

        If ``autorefresh`` is :py:data:`True`, this bar will be redrawn whenever another bar is
        drawn assuming it had been ``min_delta`` seconds since the last update. Generally,
        only need when ``elapsed`` is used in :ref:`status_format <status_format>`.

        """

        position = kwargs.pop('position', None)

        return self._add_counter(self.status_bar_class, *args, position=position, **kwargs)

    def _add_counter(self, counter_class, *args, **kwargs):  # pylint: disable=too-many-branches
        """
        Args:
            counter_class(:py:class:`PrintableCounter`): Class to instantiate
            position(int): Line number counting from the bottom of the screen
            autorefresh(bool): Refresh this counter when other bars are drawn
            replace(:py:class:`PrintableCounter`): Replace given counter with new. Position ignored.
            kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
                are passed to :py:class:`Counter`

        Returns:
            :py:class:`Counter`: Instance of counter class

        Get a new instance of the given class and add it to the manager

        If ``position`` is specified, the counter's position can change dynamically if
        additional counters are called without a ``position`` argument.

        """

        position = kwargs.pop('position', None)
        autorefresh = kwargs.pop('autorefresh', False)
        replace = kwargs.pop('replace', None)

        # List of counters to refresh due to new position
        toRefresh = []

        # Add default values to kwargs
        for key, val in self.defaults.items():
            if key not in kwargs:
                kwargs[key] = val
        kwargs['manager'] = self

        # Create counter
        new = counter_class(*args, **kwargs)
        if autorefresh:
            self.autorefresh.append(new)

        # Get pinned counters
        # pylint: disable=protected-access
        pinned = {pos: ctr for ctr, pos in self.counters.items() if ctr._pinned}

        # Manage replacement
        if replace is not None:
            if replace not in self.counters:
                raise ValueError('Counter to replace is not currently managed: %r' % replace)

            # Remove old counter
            position = self.counters[replace]
            replace.leave = False
            replace.close()

            # Replace old counter with new counter
            self.counters[new] = position
            if replace._pinned:
                new._pinned = True
                pinned[position] = new

        # Position specified
        elif position is not None:
            if position < 1:
                raise ValueError('Counter position %d is less than 1.' % position)
            if position in pinned:
                raise ValueError('Counter position %d is already occupied.' % position)
            if position > self.height:
                raise ValueError('Counter position %d is greater than terminal height.' % position)
            new._pinned = True  # pylint: disable=protected-access
            self.counters[new] = position
            pinned[position] = new

        # Dynamic placement
        else:
            # Set for now, but will change
            self.counters[new] = 0

        # Refresh status bars only, counters may have subcounters
        if counter_class is self.status_bar_class:
            toRefresh.append(new)

        # Iterate through all counters in reverse order
        pos = 1
        for ctr in reversed(self.counters):

            if ctr in pinned.values():
                continue

            old_pos = self.counters[ctr]

            while pos in pinned:
                pos += 1

            if pos != old_pos:

                # Don't refresh new counter, already accounted for
                if ctr is not new:
                    ctr.clear(flush=False)
                    toRefresh.append(ctr)

                self.counters[ctr] = pos

            pos += 1

        self._set_scroll_area()
        for ctr in reversed(toRefresh):
            ctr.refresh(flush=False)
        self._flush_streams()

        return new

    def _set_scroll_area(self, force=False):
        """
        In the base class this is a no-op
        It is called when adding counters for managers which manage scrollable regions
        """

    def remove(self, counter):
        """
        Args:
            counter(:py:class:`Counter`): Progress bar or status bar instance

        Remove bar instance from manager

        Does not error if instance is not managed by this manager

        Generally this method should not be called directly,
        instead used :py:meth:`Counter.close`.
        """

        if not counter.leave:
            try:
                del self.counters[counter]
                self.autorefresh.remove(counter)
            except (KeyError, ValueError):
                pass

    def _autorefresh(self, exclude):
        """
        Args:
            exclude(list): Iterable of bars to ignore when auto-refreshing

        Refresh any bars specified for auto-refresh
        """

        self.refresh_lock = True
        current_time = time.time()

        for counter in self.autorefresh:

            if counter in exclude or counter.min_delta > current_time - counter.last_update:
                continue

            counter.refresh()

        self.refresh_lock = False
