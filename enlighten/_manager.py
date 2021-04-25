# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten manager submodule**

Provides Manager class
"""

import atexit
import multiprocessing
import signal
import sys
import threading

from blessed import Terminal

from enlighten._basemanager import BaseManager


RESIZE_SUPPORTED = hasattr(signal, 'SIGWINCH')


class Manager(BaseManager):
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
        threaded(bool): When True resize handling is deferred until next write (Default: False
            unless multiple threads or multiple processes are detected)
        width(int): Static output width. If unset, terminal width is determined dynamically
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
    def __init__(self, **kwargs):

        super(Manager, self).__init__(**kwargs)

        # Set up companion stream
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

        if not self.no_resize and RESIZE_SUPPORTED:
            self.sigwinch_orig = signal.getsignal(signal.SIGWINCH)

    def __repr__(self):
        return '%s(stream=%r)' % (self.__class__.__name__, self.stream)

    def _stage_resize(self, *args, **kwarg):  # pylint: disable=unused-argument
        """
        Called when a window resize signal is detected
        """

        # Set semaphore to trigger resize on next write
        self._resize = True

        if self.threaded:
            # Reset update time to avoid any delay in resize
            for counter in self.counters:
                counter.last_update = 0

        else:
            # If not threaded, handle resize now
            self._resize_handler()

    def _resize_handler(self):
        """
        Called when a window resize has been detected

        Resets the scroll window
        """

        # Make sure only one resize handler is running
        if self.resize_lock:
            return

        self.resize_lock = True
        buffer = self._buffer
        term = self.term

        oldHeight = self.height
        newHeight = self.height = term.height

        if newHeight < oldHeight:
            buffer.append(term.move(max(0, newHeight - self.scroll_offset), 0))
            buffer.append(u'\n' * (2 * max(self.counters.values())))
        elif newHeight > oldHeight and self.threaded:
            buffer.append(term.move(newHeight, 0))
            buffer.append(u'\n' * (self.scroll_offset - 1))

        buffer.append(term.move(max(0, newHeight - self.scroll_offset), 0))
        buffer.append(term.clear_eos)

        self.width = self._width or term.width
        self._set_scroll_area(force=True)

        for counter in self.counters:
            counter.refresh(flush=False)
        self._flush_streams()

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
                if self.threaded is None:
                    self.threaded = (
                        threading.active_count() > 1  # Multiple threads
                        or multiprocessing.active_children()  # Main process with children
                        or multiprocessing.current_process().name != 'MainProcess'  # Child process
                    )
                signal.signal(signal.SIGWINCH, self._stage_resize)
            self.process_exit = True

        if self.set_scroll:

            buffer = self._buffer
            term = self.term
            scrollPosition = max(0, self.height - self.scroll_offset)

            if force or use_new:

                # Add line feeds so we don't overwrite existing output
                if use_new:
                    buffer.append(term.move(max(0, self.height - oldOffset), 0))
                    buffer.append(u'\n' * (newOffset - oldOffset))

                # Reset scroll area
                buffer.append(term.hide_cursor)
                buffer.append(term.csr(0, scrollPosition))

            # Always reset position
            buffer.append(term.move(scrollPosition, 0))
            if self.companion_term is not None:
                self._companion_buffer.append(term.move(scrollPosition, 0))

    def _flush_streams(self):
        """
        Flush stream and companion buffers
        """

        buffer = self._buffer
        companion_buffer = self._companion_buffer

        if buffer:
            self.stream.write(u''.join(buffer))

        self.stream.flush()

        if self.companion_stream is not None:
            if companion_buffer:
                self.companion_stream.write(u''.join(companion_buffer))
            self.companion_stream.flush()

        del buffer[:]  # Python 2.7 does not support list.clear()
        del companion_buffer[:]

    def _at_exit(self):
        """
        Resets terminal to normal configuration
        """

        if not self.process_exit:
            return

        try:
            term = self.term
            buffer = self._buffer

            if self.set_scroll:
                buffer.append(self.term.normal_cursor)
                buffer.append(self.term.csr(0, self.height - 1))

            buffer.append(term.move(term.height, 0))
            buffer.append(term.cud1 or u'\n')

            self._flush_streams()

        except ValueError:  # Possibly closed file handles
            pass

    def stop(self):
        # See parent class for docstring

        if not self.enabled:
            return

        buffer = self._buffer
        term = self.term
        height = term.height
        positions = self.counters.values()

        if not self.no_resize and RESIZE_SUPPORTED:
            signal.signal(signal.SIGWINCH, self.sigwinch_orig)

        try:
            for num in range(self.scroll_offset - 1, 0, -1):
                if num not in positions:
                    buffer.append(term.move(height - num, 0))
                    buffer.append(term.clear_eol)

        finally:

            # Reset terminal
            if self.set_scroll:
                buffer.append(term.normal_cursor)
                buffer.append(term.csr(0, self.height - 1))
                if self.companion_term:
                    self._companion_buffer.extend((term.normal_cursor,
                                                   term.csr(0, self.height - 1),
                                                   term.move(height, 0)))

            # Re-home cursor
            buffer.append(term.move(height, 0))

            self.process_exit = False
            self.enabled = False
            for counter in self.counters:
                counter.enabled = False

        # Feed terminal if lowest position isn't cleared
        if 1 in positions:
            buffer.append(term.cud1 or '\n')

        self._flush_streams()

    def write(self, output='', flush=True, counter=None, **kwargs):
        # See parent class for docstring

        if not self.enabled:
            return

        # If resize signal was caught, handle resize
        if self._resize and not self.resize_lock:
            try:
                self._resize_handler()
            finally:
                self._resize = False

            return

        position = self.counters[counter] if counter else 0
        term = self.term

        # If output is callable, call it with supplied arguments
        if callable(output):
            output = output(**kwargs)

        try:
            self._buffer.extend((term.move(self.height - position, 0),
                                 u'\r',
                                 term.clear_eol,
                                 output))

        finally:
            # Reset position and scrolling
            if not self.refresh_lock:
                if self.autorefresh:
                    self._autorefresh(exclude=(counter,))
                self._set_scroll_area()
                if flush:
                    self._flush_streams()
