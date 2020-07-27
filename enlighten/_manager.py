# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten manager submodule**

Provides Manager class
"""

import atexit
from collections import OrderedDict
import signal
import sys
import time

from enlighten._counter import Counter
from enlighten._statusbar import StatusBar
from enlighten._terminal import Terminal

RESIZE_SUPPORTED = hasattr(signal, 'SIGWINCH')


class Manager(object):
    """

    Args:
        stream(:py:term:`file object`): Output stream. If :py:data:`None`,
            defaults to :py:data:`sys.stdout`
        counter_class(:py:term:`class`): Progress bar class (Default: :py:class:`Counter`)
        set_scroll(bool): Enable scroll area redefinition (Default: :py:data:`True`)
        companion_stream(:py:term:`file object`): See :ref:`companion_stream <companion_stream>`
            below. (Default: :py:data:`None`)
        enabled(bool): Status (Default: True)
        no_resize(bool): Disable resizing support
        kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
            will be used as default values when :py:meth:`counter` is called.

    Manager class for outputting progress bars to streams attached to TTYs

    Progress bars are displayed at the bottom of the screen
    with standard output displayed above.

    .. _companion_stream:

    **companion_stream**

        A companion stream is a :py:term:`file object` that shares a TTY with
        the primary output stream. The cursor position in the companion stream will be
        moved in coordination with the primary stream.

        If the value is :py:data:`None`, :py:data:`sys.stdout` and :py:data:`sys.stderr` will
        be used as companion streams. Unless explicitly
        specified, a stream which is not attached to a TTY (the case when
        redirected to a file), will not be used as a companion stream.

    """

    # pylint: disable=too-many-instance-attributes
    def __init__(self, stream=None, counter_class=Counter, **kwargs):

        self.stream = sys.stdout if stream is None else stream
        self.counter_class = counter_class
        self.status_bar_class = StatusBar

        self.counters = OrderedDict()
        self.enabled = kwargs.get('enabled', True)  # Double duty for counters
        self.no_resize = kwargs.pop('no_resize', False)
        self.set_scroll = kwargs.pop('set_scroll', True)
        self.term = Terminal(stream=self.stream)

        # Set up companion stream
        self.companion_stream = kwargs.pop('companion_stream', None)
        if self.companion_stream is None:

            # Account for calls with original output
            if self.stream is sys.__stdout__ and sys.__stderr__.isatty():
                self.companion_stream = sys.__stderr__
            elif self.stream is sys.__stderr__ and sys.__stdout__.isatty():
                self.companion_stream = sys.__stdout__

            # Account for output redirection
            elif self.stream is sys.stdout and sys.stderr.isatty():
                self.companion_stream = sys.stderr
            elif self.stream is sys.stderr and sys.stdout.isatty():
                self.companion_stream = sys.stdout

        # Set up companion terminal
        if self.companion_stream:
            self.companion_term = Terminal(stream=self.companion_stream)
        else:
            self.companion_term = None

        self.autorefresh = []
        self.height = self.term.height
        self.process_exit = False
        self.refresh_lock = False
        self.resize_lock = False
        self.scroll_offset = 1
        self.width = self.term.width

        if not self.no_resize and RESIZE_SUPPORTED:
            self.sigwinch_orig = signal.getsignal(signal.SIGWINCH)

        self.defaults = kwargs  # Counter defaults

    def __repr__(self):
        return '%s(stream=%r)' % (self.__class__.__name__, self.stream)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.stop()

    def counter(self, position=None, **kwargs):
        """
        Args:
            position(int): Line number counting from the bottom of the screen
            autorefresh(bool): Refresh this counter when other bars are drawn
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

    def _add_counter(self, counter_class, *args, **kwargs):
        """
        Args:
            counter_class(:py:class:`PrintableCounter`): Class to instantiate
            position(int): Line number counting from the bottom of the screen
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

        # Check position
        if position is not None:
            if position in pinned:
                raise ValueError('Counter position %d is already occupied.' % position)
            if position > self.height:
                raise ValueError('Counter position %d is greater than terminal height.' % position)
            new._pinned = True  # pylint: disable=protected-access
            self.counters[new] = position
            pinned[position] = new
            if counter_class is self.status_bar_class:
                toRefresh.append(new)
        else:
            # Set for now, but will change
            self.counters[new] = 0

        # Iterate through all counters in reverse order
        pos = 1
        for ctr in reversed(self.counters):

            if ctr in pinned.values():
                continue

            old_pos = self.counters[ctr]

            while pos in pinned:
                pos += 1

            if pos != old_pos:

                # Don't refresh new counter in case it will have subcounters
                if ctr is not new or counter_class is self.status_bar_class:
                    ctr.clear(flush=False)
                    toRefresh.append(ctr)

                self.counters[ctr] = pos

            pos += 1

        self._set_scroll_area()
        for ctr in reversed(toRefresh):
            ctr.refresh()
        self.stream.flush()

        return new

    def _resize_handler(self, *args, **kwarg):  # pylint: disable=unused-argument
        """
        Called when a window resize signal is detected

        Resets the scroll window
        """

        # Make sure only one resize handler is running
        try:
            assert self.resize_lock
        except AssertionError:

            self.resize_lock = True
            term = self.term

            term.clear_cache()
            newHeight = term.height
            newWidth = term.width
            lastHeight = lastWidth = 0

            while newHeight != lastHeight or newWidth != lastWidth:
                lastHeight = newHeight
                lastWidth = newWidth
                time.sleep(.2)
                term.clear_cache()
                newHeight = term.height
                newWidth = term.width

            if newWidth < self.width:
                offset = (self.scroll_offset - 1) * (1 + self.width // newWidth)
                term.move_to(0, max(0, newHeight - offset))
                self.stream.write(term.clear_eos)

            self.width = newWidth
            self._set_scroll_area(force=True)

            for counter in self.counters:
                counter.refresh(flush=False)
            self.stream.flush()

            self.resize_lock = False

    def _set_scroll_area(self, force=False):
        """
        Args:
            force(bool): Set the scroll area even if no change in height and position is detected

        Sets the scroll window based on the counter positions
        """

        # Save scroll offset for resizing
        oldOffset = self.scroll_offset
        newOffset = max(self.counters.values()) + 1
        if newOffset > oldOffset:
            self.scroll_offset = newOffset
            use_new = True
        else:
            use_new = False

        if not self.enabled:
            return

        # Set exit handling only once
        if not self.process_exit:
            atexit.register(self._at_exit)
            if not self.no_resize and RESIZE_SUPPORTED:
                signal.signal(signal.SIGWINCH, self._resize_handler)
            self.process_exit = True

        if self.set_scroll:

            term = self.term
            newHeight = term.height
            scrollPosition = max(0, newHeight - self.scroll_offset)

            if force or use_new or newHeight != self.height:
                self.height = newHeight

                # Add line feeds so we don't overwrite existing output
                if use_new:
                    term.move_to(0, max(0, newHeight - oldOffset))
                    self.stream.write(u'\n' * (newOffset - oldOffset))

                # Reset scroll area
                self.term.change_scroll(scrollPosition)

            # Always reset position
            term.move_to(0, scrollPosition)
            if self.companion_term is not None:
                self.companion_term.move_to(0, scrollPosition)

    def _at_exit(self):
        """
        Resets terminal to normal configuration
        """

        if not self.process_exit:
            return

        try:
            term = self.term

            if self.set_scroll:
                term.reset()
            else:
                term.move_to(0, term.height)

            self.term.feed()

            self.stream.flush()
            if self.companion_stream is not None:
                self.companion_stream.flush()

        except ValueError:  # Possibly closed file handles
            pass

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

    def stop(self):
        """
        Clean up and reset terminal

        This method should be called when the manager and counters will no longer be needed.

        Any progress bars that have ``leave`` set to :py:data:`True` or have not been closed
        will remain on the console. All others will be cleared.

        Manager and all counters will be disabled.

        """

        if not self.enabled:
            return

        term = self.term
        stream = self.stream
        positions = self.counters.values()

        if not self.no_resize and RESIZE_SUPPORTED:
            signal.signal(signal.SIGWINCH, self.sigwinch_orig)

        try:
            for num in range(self.scroll_offset - 1, 0, -1):
                if num not in positions:
                    term.move_to(0, term.height - num)
                    stream.write(term.clear_eol)

            stream.flush()

        finally:

            if self.set_scroll:

                self.term.reset()

                if self.companion_term:
                    self.companion_term.reset()

            else:
                term.move_to(0, term.height)

            self.process_exit = False
            self.enabled = False
            for counter in self.counters:
                counter.enabled = False

        # Feed terminal if lowest position isn't cleared
        if 1 in positions:
            term.feed()

    def write(self, output='', flush=True, counter=None):
        """
        Args:
            output(str): Output string
            flush(bool): Flush the output stream after writing
            counter(:py:class:`Counter`): Bar being written (for position and auto-refresh)

        Write to stream at a given position
        """

        if not self.enabled:
            return

        position = self.counters[counter] if counter else 0
        stream = self.stream
        term = self.term

        try:
            term.move_to(0, term.height - position)
            # Include \r and term call to cover most conditions
            stream.write(u'\r' + term.clear_eol + output)

        finally:
            # Reset position and scrolling
            if not self.refresh_lock:
                if self.autorefresh:
                    self._autorefresh(exclude=(counter,))
                self._set_scroll_area()
                if flush:
                    stream.flush()

    def _autorefresh(self, exclude):
        """
        Args:
            exclude(list): Iterable of bars to ignore when auto-refreshing

        Refresh any bars specified for auto-refresh
        """

        # Make sure this is only running once
        try:
            assert self.refresh_lock
        except AssertionError:

            self.refresh_lock = True
            current_time = time.time()

            for counter in self.autorefresh:

                if counter in exclude or counter.min_delta > current_time - counter.last_update:
                    continue

                counter.refresh()

            self.refresh_lock = False


def get_manager(stream=None, counterclass=Counter, **kwargs):
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
    return Manager(stream=stream, counterclass=counterclass, **kwargs)
