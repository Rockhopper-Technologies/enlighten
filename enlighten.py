# -*- coding: utf-8 -*-
# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten Progress Bar**

Provides progress bars and counters which play nice in a TTY console
"""

import atexit
import signal
import sys
import time

from blessed import Terminal as _Terminal

try:
    from collections import OrderedDict
except ImportError:  # pragma: no cover (Python 2.6)
    from ordereddict import OrderedDict

# Flag to support unicode in Python 2
NEEDS_UNICODE_HELP = sys.version_info[:2] <= (2, 7)

COUNTER_FMT = u'{desc}{desc_pad}{count:d} {unit}{unit_pad}' + \
              u'[{elapsed}, {rate:.2f}{unit_pad}{unit}/s]{fill}'

BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} ' + \
          u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

SERIES_STD = u' ▏▎▍▌▋▊▉█'

RESIZE_SUPPORTED = hasattr(signal, 'SIGWINCH')

__version__ = '1.0.7'


def _format_time(seconds):
    """
    Args:
        seconds (float): amount of time

    Format time string for eta and elapsed
    """

    # Always do minutes and seconds in mm:ss format
    minutes = seconds // 60
    hours = minutes // 60
    rtn = '{0:02.0f}:{1:02.0f}'.format(minutes % 60, seconds % 60)

    #  Add hours if there are any
    if hours:

        rtn = '{0:d}h {1}'.format(int(hours % 24), rtn)

        #  Add days if there are any
        days = int(hours // 24)
        if days:
            rtn = '{0:d}d {1}'.format(days, rtn)

    return rtn


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


class Counter(object):
    """
    .. spelling::
        desc
        len

    Args:
        bar_format(str): Progress bar format, see :ref:`Format <counter_format>` below
        count(int): Initial count (Default: 0)
        counter_format(str): Counter format, see :ref:`Format <counter_format>` below
        desc(str): Description
        enabled(bool): Status (Default: True)
        leave(True): Leave progress bar after closing (Default: :py:data:`True`)
        manager(:py:class:`Manager`): Manager instance. Creates instance if not specified
        min_delta(float): Minimum time, in seconds, between refreshes (Default: 0.1)
        series(:py:term:`sequence`): Progression series, see :ref:`Series <series>` below
        stream(:py:term:`file object`): Output stream. Not used when instantiated through a manager
        total(int): Total count when complete
        unit(str): Unit label

    Progress bar and counter class

    A :py:class:`Counter` instance can be created with the :py:meth:`Manager.counter` method
    or, when a standalone progress bar for simple applications is required, the :py:class:`Counter`
    class can be called directly. The output stream will default to :py:data:`sys.stdout` unless
    ``stream`` is set.

    .. note::

        With the default values for ``bar_format`` and ``counter_format``,
        :py:class:`floats <float>` can not be used for ``total``, ``count``, or provided to
        :py:meth:`~Counter.update`. In order to use :py:class:`floats <float>`, provide custom
        formats to ``bar_format`` and ``counter_format``. See :ref:`Format <counter_format>` below.

    .. _series:

    **Series**

        The progress bar is constructed from the characters in ``series``. ``series`` must be a
        :py:term:`sequence` (:py:class:`str`, :py:class:`list`, :py:class:`tuple`) containing
        single characters.

        Default progress series (``series``):

        .. code-block:: python

            ' ▏▎▍▌▋▊▉█'

        The first character is the fill character. When the ``count`` is 0,
        the bar will be made up of only this character.
        In the example below, characters 5 through 9 are fill characters.


        The last character is the full character. When the ``count`` is equal to ``total``,
        the bar will be made up of only this character.
        In the example below, characters 0 through 3 are fill characters.


        The remaining characters are fractional characters used to more accurately represent the
        transition between the full and fill characters.
        In the example below, character 4 is a fractional character.

        .. code-block:: python

            '45% |████▋     |'
                 '0123456789'

    .. _counter_format:

    **Format**

        If ``total`` is :py:data:`None` or ``count`` becomes higher than ``total``,
        the counter format will be used instead of the progress bar format.

        Default counter format (``counter_format``):

        .. code-block:: python

            '{desc}{desc_pad}{count:d} {unit}{unit_pad}{elapsed}, \
{rate:.2f}{unit_pad}{unit}/s]{fill}'

            # Example output
            'Loaded 30042 Files [00:01, 21446.45 Files/s]                                    '

        Default progress bar format (``bar_format``):

        .. code-block:: python

            '{desc}{desc_pad}{percentage:3.0f}%|{bar}| \
{count:{len_total}d}/{total:d} [{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

            # Example output
            'Processing    22%|█████▊                   |  23/101 [00:27<01:32, 0.84 Files/s]'


        Available fields:

        - count(:py:class:`int`) - Current value of ``count``
        - desc(:py:class:`str`) - Value of ``desc``
        - desc_pad(:py:class:`str`) - A single space if ``desc`` is set, otherwise empty
        - elapsed(:py:class:`str`) - Time elapsed since instance was created
        - rate(:py:class:`float`) - Average increments per second since instance was created
        - unit(:py:class:`str`) - Value of ``unit``
        - unit_pad(:py:class:`str`) - A single space if ``unit`` is set, otherwise empty

        Addition fields for ``bar_format`` only:

        - bar(:py:class:`str`) - Progress bar draw with characters from ``series``
        - eta(:py:class:`str`) - Estimated time to completion
        - len_total(:py:class:`int`) - Length of ``total`` when converted to a string
        - percentage(:py:class:`float`) - Percentage complete
        - total(:py:class:`int`) - Value of ``total``

        Addition fields for ``counter_format`` only:

        - fill(:py:class:`str`) - blank spaces, number needed to fill line

    **Instance Attributes**

        .. py:attribute:: count

            :py:class:`int` - Current count

        .. py:attribute:: desc

            :py:class:`str` - Description

        .. py:attribute:: elapsed

            :py:class:`float` - Time since start
            (since last update if :py:attr:`count`equals :py:attr:`total`)

        .. py:attribute:: enabled

            :py:class:`bool` - Current status

        .. py:attribute:: manager

            :py:class:`Manager` - Manager Instance

        .. py:attribute:: position

            :py:class:`int` - Current position

        .. py:attribute:: total

            :py:class:`int` - Total count when complete

        .. py:attribute:: unit

            :py:class:`str` - Unit label

    """
    # pylint: disable=too-many-instance-attributes

    __slots__ = ('bar_format', 'count', 'counter_format', 'desc', 'enabled', 'last_update',
                 'leave', 'manager', 'min_delta', 'series', 'start', 'start_count', 'total', 'unit')

    # pylint: disable=too-many-arguments
    def __init__(self, **kwargs):

        self.bar_format = kwargs.get('bar_format', BAR_FMT)
        self.count = kwargs.get('count', 0)
        self.counter_format = kwargs.get('counter_format', COUNTER_FMT)
        self.desc = kwargs.get('desc', None)
        self.enabled = kwargs.get('enabled', True)
        self.leave = kwargs.get('leave', True)
        self.min_delta = kwargs.get('min_delta', 0.1)
        self.series = kwargs.get('series', SERIES_STD)
        self.total = kwargs.get('total', None)
        self.unit = kwargs.get('unit', None)

        self.last_update = time.time()
        self.start = self.last_update
        self.start_count = self.count
        self.manager = kwargs.get('manager', None)
        if self.manager is None:
            self.manager = Manager(stream=kwargs.get('stream', sys.stdout),
                                   counter_class=self.__class__, set_scroll=False)
            self.manager.counters[self] = 1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def position(self):
        """
        Fetch position from the manager
        """

        return self.manager.counters.get(self, 0)

    @property
    def elapsed(self):
        """
        Get elapsed time is seconds (float)
        """

        # Clock stops running when total is reached
        if self.count == self.total:
            elapsed = self.last_update - self.start
        else:
            elapsed = time.time() - self.start

        return elapsed

    def clear(self, flush=True):
        """
        Args:
            flush(bool): Flush stream after clearing progress bar (Default:True)

        Clear progress bar
        """

        if self.enabled:
            self.manager.write(flush=flush, position=self.position)

    def close(self, clear=False):
        """
        Do final refresh and remove from manager

        If ``leave`` is True, the default, the effect is the same as :py:meth:`refresh`.
        """

        if clear and not self.leave:
            self.clear()
        else:
            self.refresh()

        self.manager.remove(self)

    def format(self, width=None, elapsed=None):
        """
        Args:
            width (int): Width in columns to make progress bar
            elapsed(float): Time since started. Automatically determined if :py:data:`None`

        Returns:
            :py:class:`str`: Formatted progress bar or counter

        Format progress bar or counter
        """

        width = width or self.manager.width

        iterations = abs(self.count - self.start_count)

        fields = {'bar': '{0}',
                  'count': self.count,
                  'desc': self.desc or '',
                  'total': self.total,
                  'unit': self.unit or '',
                  'desc_pad': ' ' if self.desc else '',
                  'unit_pad': ' ' if self.unit else ''}

        # Get elapsed time
        if elapsed is None:
            elapsed = self.elapsed

        fields['elapsed'] = _format_time(elapsed)

        # Get rate. Elapsed could be 0 if counter was not updated and has a zero total.
        if elapsed:
            # Use iterations so a counter running backwards is accurate
            fields['rate'] = iterations / elapsed
        else:
            fields['rate'] = 0

        # Only process bar if total was given and n doesn't exceed total
        if self.total is not None and self.count <= self.total:

            fields['len_total'] = len(str(self.total))

            # Get percentage
            if self.total == 0:
                # If total is 0, force to 100 percent
                percentage = 1
                fields['eta'] = '00:00'
            else:
                # Use float to force to float in Python 2
                percentage = self.count / float(self.total)

                # Get eta
                if fields['rate']:
                    # Use iterations so a counter running backwards is accurate
                    eta = (self.total - iterations) / fields['rate']
                    fields['eta'] = _format_time(eta)
                else:
                    fields['eta'] = '?'

            fields['percentage'] = percentage * 100

            # Partially format
            rtn = self.bar_format.format(**fields)

            # Format the bar
            barWidth = width - len(rtn) + 3  # 3 is for the bar placeholder
            complete = barWidth * percentage
            barLen = int(complete)
            partial = fill = ''
            if barLen < barWidth:
                partial = self.series[int(round((complete - barLen) * (len(self.series) - 1)))]
                fill = self.series[0] * (barWidth - barLen - 1)
            return rtn.format(u'{0}{1}{2}'.format(self.series[-1] * barLen, partial, fill))

        else:
            fields['fill'] = '{0}'
            rtn = self.counter_format.format(**fields)
            return rtn.format(' ' * (width - len(rtn) + 3))

    def refresh(self, flush=True, elapsed=None):
        """
        Args:
            flush(bool): Flush stream after writing progress bar (Default:True)
            elapsed(float): Time since started. Automatically determined if :py:data:`None`

        Redraw progress bar
        """

        if self.enabled:
            self.manager.write(output=self.format(elapsed=elapsed),
                               flush=flush, position=self.position)

    def update(self, incr=1, force=False):
        """
        Args:
            incr(int): Amount to increment ``count`` (Default: 1)
            force(bool): Force refresh even if ``min_delta`` has not been reached

        Increment progress bar and redraw

        Progress bar is only redrawn if ``min_delta`` seconds past since the last update
        """

        self.count += incr
        if self.enabled:
            currentTime = time.time()
            # Update if force, 100%, or minimum delta has been reached
            if force or self.count == self.total or \
                    currentTime - self.last_update >= self.min_delta:
                self.last_update = currentTime
                self.refresh(elapsed=currentTime - self.start)


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

        self.stream = stream or sys.stdout
        self.counter_class = counter_class
        self.counters = OrderedDict()
        self.enabled = kwargs.get('enabled', True)  # Double duty for counters
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
        if RESIZE_SUPPORTED:
            self.sigwinch_orig = signal.getsignal(signal.SIGWINCH)

        self.defaults = kwargs  # Counter defaults

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
                cter.refresh(flush=False)
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
            if RESIZE_SUPPORTED:
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
                    self.stream.write('\n' * (newOffset - oldOffset))

                # Reset scroll area
                self.term.change_scroll(scrollPosition)

            # Always reset position
            term.move_to(0, scrollPosition)
            if self.companion_term:
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

            if RESIZE_SUPPORTED:
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
                    stream.write(('\r' + term.clear_eol + output).encode('utf-8'))
                else:  # pragma: no cover (Version dependent >= 2.7)
                    stream.write('\r' + term.clear_eol + output)

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

    stream = stream or sys.stdout
    isatty = hasattr(stream, 'isatty') and stream.isatty()
    kwargs['enabled'] = isatty and kwargs.get('enabled', True)
    return Manager(stream=stream, counterclass=counterclass, **kwargs)
