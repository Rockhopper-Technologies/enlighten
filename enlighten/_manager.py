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
import signal
import sys
import time

try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover (Python 2.6)
    from ordereddict import OrderedDict


from enlighten._counter import Counter
from enlighten._terminal import Terminal


# Flag to support unicode in Python 2.6
NEEDS_UNICODE_HELP = sys.version_info[:2] < (2, 7)

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
        kwargs(dict): Any additional :py:term:`keyword arguments<keyword argument>`
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
        self.counters = OrderedDict()
        self.enabled = kwargs.get('enabled', True)  # Double duty for counters
        self.no_resize = kwargs.get('no_resize', False)
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

        self.scroll_offset = 1
        self.process_exit = False
        self.height = self.term.height
        self.width = self.term.width
        self.set_scroll = kwargs.pop('set_scroll', True)
        self.resize_lock = False
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
            kwargs(dict): Any additional :py:term:`keyword arguments<keyword argument>`
                are passed to :py:class:`Counter`

        Returns:
            :py:class:`Counter`: Instance of counter class

        Get a new progress bar instance

        If ``position`` is specified, the counter's position can change dynamically if
        additional counters are called without a ``position`` argument.

        """

        for key, val in self.defaults.items():
            if key not in kwargs:
                kwargs[key] = val
        kwargs['manager'] = self

        counter = self.counter_class(**kwargs)

        if position is None:
            toRefresh = []
            if self.counters:
                pos = 2
                for cter in reversed(self.counters):
                    if self.counters[cter] < pos:
                        toRefresh.append(cter)
                        cter.clear(flush=False)
                        self.counters[cter] = pos
                        pos += 1

            self.counters[counter] = 1
            self._set_scroll_area()
            for cter in reversed(toRefresh):
                cter.refresh()
            self.stream.flush()

        elif position in self.counters.values():
            raise ValueError('Counter position %d is already occupied.' % position)
        elif position > self.height:
            raise ValueError('Counter position %d is greater than terminal height.' % position)
        else:
            self.counters[counter] = position

        return counter

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

            for cter in self.counters:
                cter.refresh(flush=False)
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
        self.scroll_offset = newOffset = max(self.counters.values()) + 1

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
            scrollPosition = max(0, newHeight - newOffset)

            if force or newOffset > oldOffset or newHeight != self.height:
                self.height = newHeight

                # Add line feeds so we don't overwrite existing output
                if newOffset - oldOffset > 0:
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

        if self.process_exit:

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
            counter(:py:class:`Counter`): Progress bar instance

        Remove progress bar instance from manager

        Does not error if instance is not managed by this manager

        Generally this method should not be called directly,
        instead used :py:meth:`remove`.
        """

        if not counter.leave:
            try:
                del self.counters[counter]
            except KeyError:
                pass

    def stop(self):
        """
        Clean up and reset terminal

        This method should be called when the manager and counters will no longer be needed.

        Any progress bars that have ``leave`` set to :py:data:`True` or have not been closed
        will remain on the console. All others will be cleared.

        Manager and all counters will be disabled.

        """

        if self.enabled:

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
                for cter in self.counters:
                    cter.enabled = False

            # Feed terminal if lowest position isn't cleared
            if 1 in positions:
                term.feed()

    def write(self, output='', flush=True, position=0):
        """
        Args:
            output(str: Output string
            flush(bool): Flush the output stream after writing
            position(int): Position relative to the bottom of the screen to write output

        Write to stream at a given position
        """

        if self.enabled:

            term = self.term
            stream = self.stream

            try:
                term.move_to(0, term.height - position)
                # Include \r and term call to cover most conditions
                if NEEDS_UNICODE_HELP:  # pragma: no cover (Version dependent 2.6)
                    encoding = getattr(stream, 'encoding', None) or 'UTF-8'
                    stream.write(('\r' + term.clear_eol + output).encode(encoding))
                else:  # pragma: no cover (Version dependent >= 2.7)
                    stream.write(u'\r' + term.clear_eol + output)

            finally:
                # Reset position and scrolling
                self._set_scroll_area()
                if flush:
                    stream.flush()


def get_manager(stream=None, counterclass=Counter, **kwargs):
    """
    Args:
        stream(:py:term:`file object`): Output stream. If :py:data:`None`,
            defaults to :py:data:`sys.stdout`
        counter_class(:py:term:`class`): Progress bar class (Default: :py:class:`Counter`)
        kwargs(dict): Any additional :py:term:`keyword arguments<keyword argument>`
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
