# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten status bar submodule**

Provides StatusBar class
"""

import time

from enlighten._basecounter import PrintableCounter
from enlighten._util import (EnlightenWarning, FORMAT_MAP_SUPPORT, format_time,
                             Justify, raise_from_none, warn_best_level)


STATUS_FIELDS = {'elapsed', 'fill'}


class StatusBar(PrintableCounter):
    """
    Args:
        enabled(bool): Status (Default: :py:data:`True`)
        color(str): Color as a string or RGB tuple see :ref:`Status Color <status_color>`
        fields(dict): Additional fields used for :ref:`formating <status_format>`
        fill(str): Fill character used in formatting and justifying text (Default: ' ')
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
            - fill(:py:class:`str`) - Filled with :py:attr:`fill` until line is width of terminal.
              May be used multiple times. Minimum width is 3.

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

    __slots__ = ('fields', '_justify', 'status_format', '_static', '_fields')

    def __init__(self, *args, **kwargs):

        super(StatusBar, self).__init__(keywords=kwargs)

        self.fields = kwargs.pop('fields', {})
        self._justify = None
        self.justify = kwargs.pop('justify', Justify.LEFT)
        self.status_format = kwargs.pop('status_format', None)
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
            rtn = self._static

        # If there is no format, return empty
        elif self.status_format is None:
            rtn = ''

        # Generate from format
        else:
            fields = self.fields.copy()
            fields.update(self._fields)

            # Warn on reserved fields
            reserved_fields = (set(fields) & STATUS_FIELDS)
            if reserved_fields:
                warn_best_level('Ignoring reserved fields specified as user-defined fields: %s' %
                                ', '.join(reserved_fields),
                                EnlightenWarning)

            elapsed = elapsed if elapsed is not None else self.elapsed
            fields['elapsed'] = format_time(elapsed)
            fields['fill'] = self._placeholder_

            # Format
            try:
                if FORMAT_MAP_SUPPORT:
                    rtn = self.status_format.format_map(fields)
                else:  # pragma: no cover
                    rtn = self.status_format.format(**fields)
            except KeyError as e:
                raise_from_none(ValueError('%r specified in format, but not provided' % e.args[0]))

        rtn = self._fill_text(rtn, width)

        return self._colorize(justify(rtn, width=width, fillchar=self.fill))

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
                self.refresh(elapsed=currentTime - self.start)
