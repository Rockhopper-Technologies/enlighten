# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten counter submodule**

Provides Counter base class
"""

import platform
import sys
import time

try:
    from collections.abc import Iterable
except ImportError:  # pragma: no cover(Python 2)
    from collections import Iterable

from blessed.colorspace import X11_COLORNAMES_TO_RGB

from enlighten._util import Justify

COUNTER_FMT = u'{desc}{desc_pad}{count:d} {unit}{unit_pad}' + \
              u'[{elapsed}, {rate:.2f}{unit_pad}{unit}/s]{fill}'

BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} ' + \
          u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

STATUS_FMT = u'{message}'

# Even with cp65001, Windows doesn't seem to support all unicode characters
if platform.system() == 'Windows':  # pragma: no cover(Windows)
    SERIES_STD = u' ▌█'
else:
    SERIES_STD = u' ▏▎▍▌▋▊▉█'

# Test for non-unicode terminals
try:
    SERIES_STD.encode(sys.__stdout__.encoding)
except UnicodeEncodeError:  # pragma: no cover(Non-unicode Terminal)
    SERIES_STD = u' |'
except (AttributeError, TypeError):  # pragma: no cover(Non-standard Terminal)
    pass

COLORS_16 = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white',
             'bright_black', 'bright_red', 'bright_green', 'bright_yellow',
             'bright_blue', 'bright_magenta', 'bright_cyan', 'bright_white')

try:
    BASESTRING = basestring
except NameError:
    BASESTRING = str


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


class BaseCounter(object):
    """
    Args:
        manager(:py:class:`Manager`): Manager instance. Required.
        color(str): Color as a string or RGB tuple (Default: None)

    Base class for counters
    """

    __slots__ = ('_color', 'count', 'manager', 'start_count')
    _repr_attrs = ('count', 'color')

    def __repr__(self):

        params = []
        for attr in self._repr_attrs:
            value = getattr(self, attr)
            if value is not None:
                params.append('%s=%r' % (attr, value))

        return '%s(%s)' % (self.__class__.__name__, ', '.join(params))

    def __init__(self, **kwargs):

        self.count = self.start_count = kwargs.get('count', 0)
        self._color = None

        self.manager = kwargs.get('manager', None)
        if self.manager is None:
            raise TypeError('manager must be specified')

        self.color = kwargs.get('color', None)

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
        elif isinstance(value, int) and 0 <= value <= 255:
            self._color = (value, self.manager.term.color(value))
        elif isinstance(value, BASESTRING):
            if value not in COLORS_16 or value not in X11_COLORNAMES_TO_RGB:
                raise AttributeError('Invalid color specified: %s' % value)
            self._color = (value, getattr(self.manager.term, value))
        elif isinstance(value, Iterable) and \
                len(value) == 3 and \
                all(isinstance(_, int) and 0 <= _ <= 255 for _ in value):
            self._color = (value, self.manager.term.color_rgb(*value))
        else:
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

        # No color specified
        if self._color is None:
            return content

        # Used spec cached by color.setter
        return self._color[1](content)

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


class SubCounter(BaseCounter):
    """
    A child counter for multicolored progress bars.

    This class tracks a portion of multicolored progress bar and should be initialized
    through :py:meth:`Counter.add_subcounter`

    **Instance Attributes**

        .. py:attribute:: count

            :py:class:`int` - Current count

        .. py:attribute:: parent

            :py:class:`Counter` - Parent counter

    """

    __slots__ = ('all_fields', 'parent')
    _repr_attrs = ('count', 'color', 'all_fields')

    def __init__(self, parent, color=None, count=0, all_fields=False):
        """
        Args:
            color(str): Series color as a string or RGB tuple see :ref:`Series Color <series_color>`
            count(int): Initial count (Default: 0)
            all_fields(bool): Populate ``rate`` and ``eta`` fields (Default: False)
        """

        if parent.count - parent.subcount - count < 0:
            raise ValueError('Invalid count: %s' % count)

        super(SubCounter, self).__init__(manager=parent.manager, color=color, count=count)

        self.parent = parent
        self.all_fields = all_fields

    def update(self, incr=1, force=False):  # pylint: disable=arguments-differ
        """
        Args:
            incr(int): Amount to increment ``count`` (Default: 1)
            force(bool): Force refresh even if ``min_delta`` has not been reached

        Increment progress bar and redraw

        Both this counter and the parent are incremented.

        Progress bar is only redrawn if min_delta seconds past since the last update on the parent.
        """

        self.count += incr
        self.parent.update(incr, force)

    def update_from(self, source, incr=1, force=False):
        """
        Args:
            source(:py:class:`SubCounter`): :py:class:`SubCounter` or :py:class:`Counter`
                to increment from
            incr(int): Amount to increment ``count`` (Default: 1)
            force(bool): Force refresh even if ``min_delta`` has not been reached

        Move a value to this counter from another counter.

        ``source`` must be the parent :py:class:`Counter` instance or a :py:class:`SubCounter` with
        the same parent

        """

        # Make sure source is a parent or peer
        if source is self.parent or getattr(source, 'parent', None) is self.parent:

            if self.count + incr < 0 or source.count - incr < 0:
                raise ValueError('Invalid increment: %s' % incr)

            if source is self.parent:
                if self.parent.count - self.parent.subcount - incr < 0:
                    raise ValueError('Invalid increment: %s' % incr)

            else:
                source.count -= incr

            self.count += incr
            self.parent.update(0, force)

        else:
            raise ValueError('source must be parent or peer')


class PrintableCounter(BaseCounter):
    """
    Base class for printable counters
    """

    __slots__ = ('enabled', 'last_update', 'leave', 'min_delta', 'start')

    def __init__(self, **kwargs):

        super(PrintableCounter, self).__init__(**kwargs)

        self.enabled = kwargs.get('enabled', True)
        self.leave = kwargs.get('leave', True)
        self.min_delta = kwargs.get('min_delta', 0.1)
        self.last_update = self.start = time.time()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    @property
    def elapsed(self):
        """
        Get elapsed time is seconds (float)
        """

        return time.time() - self.start

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
            self.manager.write(output=self.format(elapsed=elapsed),
                               flush=flush, position=self.position)


class StatusBar(PrintableCounter):
    """
    Args:
        enabled(bool): Status (Default: :py:data:`True`)
        color(str): Color as a string or RGB tuple see :ref:`Status Color <status_color>`
        fields(dict): Additional fields used for :ref:`formating <status_format>`
        fill(str): Fill character used when justifying text (Default: ' ')
        justify(str):
            One of :py:attr:`Justify.CENTER`, :py:attr:`Justify.LEFT`, :py:attr:`Justify.RIGHT`
        leave(True): Leave status bar after closing (Default: :py:data:`True`)
        min_delta(float): Minimum time, in seconds, between refreshes (Default: 0.1)
        status_format(str): Status bar format, see :ref:`Format <status_format>`

    Status bar class

    A :py:class:`StatusBar` instance should be created with the :py:meth:`Manager.status_bar`
    method.

    .. _status_color:

    **Status Color**

    Color works similarly to color on :py:class:`Counter`, except it affects the entire status bar.
    See :ref:`Series Color <series_color>` for more information.

    .. _status_format:

    **Format**

    There are two ways to populate the status bar, direct and formatted. Direct takes
    precedence over formatted.

    .. _status_format_direct:

    **Direct Status**

    Direct status is used when arguments are passed to :py:meth:`Manager.status_bar` or
    :py:meth:`StatusBar.update`. Any arguments are coerced to strings and joined with a space.
    For example:

    .. code-block:: python


        status_bar.update('Hello', 'World!')
        # Example output: Hello World!

        status_bar.update('Hello World!')
        # Example output: Hello World!

        count = [1, 2, 3, 4]
        status_bar.update(*count)
         # Example output: 1 2 3 4

    .. _status_format_formatted:

    **Formatted Status**

        Formatted status uses the format specified in the ``status_format`` parameter to populate
        the status bar.

        .. code-block:: python

            'Current Stage: {stage}'

            # Example output
            'Current Stage: Testing'

        Available fields:

            - elapsed(:py:class:`str`) - Time elapsed since instance was created

        .. note::

            The status bar is only updated when :py:meth:`StatusBar.update` or
            :py:meth:`StatusBar.refresh` is called, so fields like ``elapsed``
            will need additional calls to appear dynamic.

        User-defined fields:

            Users can define fields in two ways, the ``fields`` parameter and by passing keyword
            arguments to :py:meth:`Manager.status_bar` or :py:meth:`StatusBar.update`

            The ``fields`` parameter can be used to pass a dictionary of additional
            user-defined fields. The dictionary values can be updated after initialization to allow
            for dynamic fields. Any fields that share names with available fields are ignored.

            If fields are passed as keyword arguments to :py:meth:`Manager.status_bar` or
            :py:meth:`StatusBar.update`, they take precedent over the ``fields`` parameter.


    **Instance Attributes**

        .. py:attribute:: elapsed

            :py:class:`float` - Time since start

        .. py:attribute:: enabled

            :py:class:`bool` - Current status

        .. py:attribute:: manager

            :py:class:`Manager` - Manager Instance

        .. py:attribute:: position

            :py:class:`int` - Current position

    """

    __slots__ = ('fields', 'fill', '_justify', 'status_format', '_static', '_fields')

    def __init__(self, *args, **kwargs):
        super(StatusBar, self).__init__(**kwargs)

        self.fields = kwargs.pop('fields', {})
        self.fill = kwargs.pop('fill', u' ')
        self._justify = None
        self.justify = kwargs.pop('justify', Justify.LEFT)
        self.status_format = kwargs.pop('status_format', STATUS_FMT)
        self._fields = kwargs
        self._static = ' '.join(str(arg) for arg in args) if args else None

    @property
    def justify(self):
        """
        Maps to justify method determined by ``justify`` parameter
        """
        return self._justify

    @justify.setter
    def justify(self, value):

        if value in (Justify.LEFT, Justify.CENTER, Justify.RIGHT):
            self._justify = getattr(self.manager.term, value)

        else:
            raise ValueError("justify must be one of Justify.LEFT, Justify.CENTER, ",
                             "Justify.RIGHT, not: '%r'" % value)

    def format(self, width=None, elapsed=None):
        """
        Args:
            width (int): Width in columns to make progress bar
            elapsed(float): Time since started. Automatically determined if :py:data:`None`

        Returns:
            :py:class:`str`: Formatted status bar

        Format status bar
        """

        width = width or self.manager.width
        justify = self.justify

        # If static message was given, just return it
        if self._static is not None:
            return justify(self._static, width=width, fillchar=self.fill)
        fields = self.fields.copy()
        fields.update(self._fields)
        elapsed = elapsed if elapsed is not None else self.elapsed
        fields['elapsed'] = _format_time(elapsed)

        # Format
        try:
            rtn = self.status_format.format(**fields)
        except KeyError as e:
            raise ValueError('%r specified in format, but not provided' % e.args[0])

        return justify(rtn, width=width, fillchar=self.fill)

    def update(self, *objects, **fields):  # pylint: disable=arguments-differ
        """
        Args:
            objects(list): Values for :ref:`Direct Status <status_format_direct>`
            force(bool): Force refresh even if ``min_delta`` has not been reached
            fields(dict): Fields for for :ref:`Formatted Status <status_format_formatted>`

        Update status and redraw

        Status bar is only redrawn if ``min_delta`` seconds past since the last update
        """

        force = fields.pop('force', False)

        self._static = ' '.join(str(obj) for obj in objects) if objects else None
        self._fields.update(fields)

        if self.enabled:
            currentTime = time.time()
            if force or currentTime - self.last_update >= self.min_delta:
                self.last_update = currentTime
                self.refresh(elapsed=currentTime - self.start)


class Counter(PrintableCounter):
    """
    .. spelling::
        desc
        len

    Args:
        additional_fields(dict): Additional fields used for :ref:`formating <counter_format>`
        bar_format(str): Progress bar format, see :ref:`Format <counter_format>` below
        count(int): Initial count (Default: 0)
        counter_format(str): Counter format, see :ref:`Format <counter_format>` below
        color(str): Series color as a string or RGB tuple see :ref:`Series Color <series_color>`
        desc(str): Description
        enabled(bool): Status (Default: :py:data:`True`)
        leave(True): Leave progress bar after closing (Default: :py:data:`True`)
        manager(:py:class:`Manager`): Manager instance. Creates instance if not specified.
        min_delta(float): Minimum time, in seconds, between refreshes (Default: 0.1)
        offset(int): Number of non-printable characters to account for when formatting
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

    .. _series_color:

    **Series Color**

        The characters specified by ``series`` will be displayed in the terminal's current
        foreground color. This can be overwritten with the ``color`` argument.

        ``color`` can be specified as :py:data:`None`, a :py:mod:`string` or, an :py:term:`iterable`
        of three integers, 0 - 255, describing an RGB color.

        For backward compatibility, a color can be expressed as an integer 0 - 255, but this
        is deprecated in favor of named or RGB colors.

        If a terminal is not capable of 24-bit color, and is given a color outside of its
        range, the color will be downconverted to a supported color.

        Valid colors for 8 color terminals:

            - black
            - blue
            - cyan
            - green
            - magenta
            - red
            - white
            - yellow

        Additional colors for 16 color terminals:

            - bright_black
            - bright_blue
            - bright_cyan
            - bright_green
            - bright_magenta
            - bright_red
            - bright_white
            - bright_yellow

        See this `chart <https://blessed.readthedocs.io/en/stable/colors.html#id3>`_
        for a complete list of supported color strings.

        .. note::
            If an invalid color is specified, an :py:exc:`AttributeError` will be raised

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

        Additional fields for ``bar_format`` only:

        - bar(:py:class:`str`) - Progress bar draw with characters from ``series``
        - eta(:py:class:`str`) - Estimated time to completion
        - len_total(:py:class:`int`) - Length of ``total`` when converted to a string
        - percentage(:py:class:`float`) - Percentage complete
        - total(:py:class:`int`) - Value of ``total``

        Addition fields for ``counter_format`` only:

        - fill(:py:class:`str`) - blank spaces, number needed to fill line

        Additional fields when subcounters are used:

        - count_n (:py:class:`int`) - Current value of ``count``
        - count_0(:py:class:`int`) - Remaining count after deducting counts for all subcounters
        - percentage_n (:py:class:`float`) - Percentage complete (``bar_format`` only)
        - percentage_0(:py:class:`float`) - Remaining percentage after deducting percentages
          for all subcounters (``bar_format`` only)

        .. note::

            **n** denotes the order the subcounter was added starting at 1.
            For example, **count_1** is the count for the first subcounter added
            and **count_2** is the count for the second subcounter added.

        Additional fields when :py:meth:`add_subcounter` is called with
        ``all_fields`` set to :py:data:`True`:

        - eta_n (:py:class:`str`) - Estimated time to completion (``bar_format`` only)
        - rate_n (:py:class:`float`) - Average increments per second since parent was created

        User-defined fields:

            The ``additional_fields`` parameter can be used to pass a dictionary of additional
            user-defined fields. The dictionary values can be updated after initialization to allow
            for dynamic fields. Any fields that share names with built-in fields are ignored.


    .. _counter_offset:

    **Offset**

        When ``offset`` is :py:data:`None`, the width of the bar portion of the progress bar and
        the fill characters for counter will be automatically determined,
        taking into account terminal escape sequences that may be included in the string.

        Under special circumstances, and to permit backward compatibility, ``offset`` may be
        explicitly set to an :py:class:`int` value. When explicitly set, automatic detection of
        escape sequences is disabled.


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

    __slots__ = ('additional_fields', 'bar_format', 'counter_format', 'desc',
                 'manager', 'offset', 'series', 'total', 'unit', '_subcounters')
    _repr_attrs = ('desc', 'total', 'count', 'unit', 'color')

    # pylint: disable=too-many-arguments
    def __init__(self, **kwargs):

        super(Counter, self).__init__(**kwargs)

        self.additional_fields = kwargs.get('additional_fields', {})
        self.bar_format = kwargs.get('bar_format', BAR_FMT)
        self.counter_format = kwargs.get('counter_format', COUNTER_FMT)
        self.desc = kwargs.get('desc', None)
        self.offset = kwargs.get('offset', None)
        self.series = kwargs.get('series', SERIES_STD)
        self.total = kwargs.get('total', None)
        self.unit = kwargs.get('unit', None)
        self._subcounters = []

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

    @property
    def subcount(self):
        """
        Sum of counts from all subcounters
        """

        return sum(subcounter.count for subcounter in self._subcounters)

    def _get_subcounters(self, elapsed, bar_fields=True):
        """
        Args:
            elapsed(float): Time since started.
            bar_fields(bool): When False, only set fields for basic counter

        Returns:
            :py:class:`tuple`: list of subcounters and dictionary of additional fields

        Each subcounter in the list will be in a tuple of (subcounter, percentage)
        Fields in the dictionary are addressed in the Format documentation of this class

        When `bar_fields` is False, only subcounter count and rate fields are set.
        percentage will be set to 0.0
        """

        fields = {}
        subcounters = []

        for num, subcounter in enumerate(self._subcounters, 1):

            fields['count_{0}'.format(num)] = subcounter.count

            if self.total and bar_fields:
                subPercentage = subcounter.count / float(self.total)
            else:
                subPercentage = 0.0

            if bar_fields:
                fields['percentage_{0}'.format(num)] = subPercentage * 100

            # Save in tuple: count, percentage
            subcounters.append((subcounter, subPercentage))

            if subcounter.all_fields:

                interations = abs(subcounter.count - subcounter.start_count)

                if elapsed:
                    # Use float to force to float in Python 2
                    rate = fields['rate_{0}'.format(num)] = interations / float(elapsed)
                else:
                    rate = fields['rate_{0}'.format(num)] = 0.0

                if not bar_fields:
                    continue

                if self.total == 0:
                    fields['eta_{0}'.format(num)] = u'00:00'
                elif rate:
                    fields['eta_{0}'.format(num)] = _format_time((self.total - interations) / rate)
                else:
                    fields['eta_{0}'.format(num)] = u'?'

        return subcounters, fields

    # pylint: disable=too-many-locals,too-many-branches,too-many-statements
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

        fields = self.additional_fields.copy()
        fields.update({'bar': u'{0}',
                       'count': self.count,
                       'desc': self.desc or u'',
                       'total': self.total,
                       'unit': self.unit or u'',
                       'desc_pad': u' ' if self.desc else u'',
                       'unit_pad': u' ' if self.unit else u''})

        # Get elapsed time
        if elapsed is None:
            elapsed = self.elapsed

        fields['elapsed'] = _format_time(elapsed)

        # Get rate. Elapsed could be 0 if counter was not updated and has a zero total.
        if elapsed:
            # Use iterations so a counter running backwards is accurate
            fields['rate'] = iterations / elapsed
        else:
            fields['rate'] = 0.0

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
                    fields['eta'] = _format_time((self.total - iterations) / fields['rate'])
                else:
                    fields['eta'] = u'?'

            fields['percentage'] = percentage * 100

            # Have to go through subcounters here so the fields are available
            subcounters, subFields = self._get_subcounters(elapsed)

            # Calculate count and percentage for remainder
            if subcounters:
                fields.update(subFields)
                fields['count_0'] = self.count - sum(sub[0].count for sub in subcounters)
                fields['percentage_0'] = (percentage - sum(sub[1] for sub in subcounters)) * 100

            # Partially format
            try:
                rtn = self.bar_format.format(**fields)
            except KeyError as e:
                raise ValueError('%r specified in format, but not present in additional_fields' %
                                 e.args[0])

            # Format the bar
            if self.offset is None:
                barWidth = width - self.manager.term.length(rtn) + 3  # 3 is for the bar placeholder
            else:
                # Offset was explicitly given
                barWidth = width - len(rtn) + self.offset + 3  # 3 is for the bar placeholder

            complete = barWidth * percentage
            barLen = int(complete)
            barText = u''
            subOffset = 0

            for subcounter, subPercentage in reversed(subcounters):
                subLen = int(barWidth * subPercentage)
                # pylint: disable=protected-access
                barText += subcounter._colorize(self.series[-1] * subLen)
                subOffset += subLen

            barText += self.series[-1] * (barLen - subOffset)

            if barLen < barWidth:
                barText += self.series[int(round((complete - barLen) * (len(self.series) - 1)))]
                barText += self.series[0] * (barWidth - barLen - 1)

            return rtn.format(self._colorize(barText))

        # Otherwise return a counter

        # Update fields from subcounters
        fields['fill'] = u'{0}'
        subcounters, subFields = self._get_subcounters(elapsed, bar_fields=False)
        if subcounters:
            fields.update(subFields)
            fields['count_0'] = self.count - sum(sub[0].count for sub in subcounters)

        try:
            rtn = self.counter_format.format(**fields)
        except KeyError as e:
            raise ValueError('%r specified in format, but not present in additional_fields' %
                             e.args[0])

        if self.offset is None:
            ret = rtn.format(u' ' * (width - self.manager.term.length(rtn) + 3))
        else:
            # Offset was explicitly given
            ret = rtn.format(u' ' * (width - len(rtn) + self.offset + 3))

        return ret

    def update(self, incr=1, force=False):  # pylint: disable=arguments-differ
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

    def add_subcounter(self, color, count=0, all_fields=False):
        """
    Args:
        color(str): Series color as a string or RGB tuple see :ref:`Series Color <series_color>`
        count(int): Initial count (Default: 0)
        all_fields(bool): Populate ``rate`` and ``eta`` formatting fields (Default: False)

    Returns:
        :py:class:`SubCounter`: Subcounter instance

    Add a subcounter for multicolored progress bars
        """

        subcounter = SubCounter(self, color=color, count=count, all_fields=all_fields)
        self._subcounters.append(subcounter)
        return subcounter
