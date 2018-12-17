# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten counter submodule**

Provides Counter base class
"""

import time


COUNTER_FMT = u'{desc}{desc_pad}{count:d} {unit}{unit_pad}' + \
              u'[{elapsed}, {rate:.2f}{unit_pad}{unit}/s]{fill}'

BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} ' + \
          u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

SERIES_STD = u' ▏▎▍▌▋▊▉█'


def _format_time(seconds):
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
        In the example below, characters 0 through 3 are full characters.


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
            raise TypeError('manager must be specified')

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

        fields = {'bar': u'{0}',
                  'count': self.count,
                  'desc': self.desc or u'',
                  'total': self.total,
                  'unit': self.unit or u'',
                  'desc_pad': u' ' if self.desc else u'',
                  'unit_pad': u' ' if self.unit else u''}

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
                fields['eta'] = u'00:00'
            else:
                # Use float to force to float in Python 2
                percentage = self.count / float(self.total)

                # Get eta
                if fields['rate']:
                    # Use iterations so a counter running backwards is accurate
                    eta = (self.total - iterations) / fields['rate']
                    fields['eta'] = _format_time(eta)
                else:
                    fields['eta'] = u'?'

            fields['percentage'] = percentage * 100

            # Partially format
            rtn = self.bar_format.format(**fields)

            # Format the bar
            barWidth = width - len(rtn) + 3  # 3 is for the bar placeholder
            complete = barWidth * percentage
            barLen = int(complete)
            partial = fill = u''
            if barLen < barWidth:
                partial = self.series[int(round((complete - barLen) * (len(self.series) - 1)))]
                fill = self.series[0] * (barWidth - barLen - 1)
            return rtn.format(u'{0}{1}{2}'.format(self.series[-1] * barLen, partial, fill))

        else:
            fields['fill'] = u'{0}'
            rtn = self.counter_format.format(**fields)
            return rtn.format(u' ' * (width - len(rtn) + 3))

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
