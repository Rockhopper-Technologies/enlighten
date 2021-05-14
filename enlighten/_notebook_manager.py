# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten manager submodule**

Provides Manager class
"""

from IPython.display import DisplayHandle, HTML

from enlighten._basemanager import BaseManager
from enlighten._util import HTMLConverter


class NotebookManager(BaseManager):
    """
    Args:
        counter_class(:py:term:`class`): Progress bar class (Default: :py:class:`Counter`)
        status_bar_class(:py:term:`class`): Status bar class (Default: :py:class:`StatusBar`)
        enabled(bool): Status (Default: True)
        width(int): Static output width (Default: 100)
        kwargs(Dict[str, Any]): Any additional :py:term:`keyword arguments<keyword argument>`
            will be used as default values when :py:meth:`counter` is called.

    Manager class for outputting progress bars to Jupyter notebooks

    The following keyword arguments are set if provided, but ignored:

      * *stream*
      * *set_scroll*
      * *companion_stream*
      * *no_resize*
      * *threaded*

    """

    def __init__(self, **kwargs):

        # Force terminal to xterm-256color because it should have broad support
        kwargs['term'] = 'xterm-256color'

        super(NotebookManager, self).__init__(**kwargs)

        # Force 24-bit color
        self.term.number_of_colors = 1 << 24

        self._converter = HTMLConverter(self.term)
        self._output = []
        self._display = DisplayHandle()
        self._html = HTML('')
        self._primed = False

        # Default width to 100 unless specified
        self.width = self._width or 100

    def __repr__(self):
        return '%s()' % self.__class__.__name__

    def _flush_streams(self):
        """
        Display buffered output
        """

        if not self.enabled:
            return

        self._html.data = '%s<div class="enlighten">\n%s\n</div>\n' % (
                          self._converter.style, '\n'.join(reversed(self._output)))

        if self._primed:
            self._display.update(self._html)
        else:
            self._primed = True
            self._display.display(self._html)

    def stop(self):
        # See parent class for docstring

        if not self.enabled:
            return

        positions = self.counters.values()

        for num in range(max(positions), 0, -1):
            if num not in positions:
                self._output[num - 1] = '  <br>'

        for counter in self.counters:
            counter.enabled = False

        self._flush_streams()

    def write(self, output='', flush=True, counter=None, **kwargs):
        # See parent class for docstring

        if not self.enabled:
            return

        position = self.counters[counter] if counter else 1

        # If output is callable, call it with supplied arguments
        if callable(output):
            output = output(**kwargs)

        # If there is space between this bar and the last, fill with blank lines
        for _ in range(position - len(self._output)):
            self._output.append('  <br>')

        # Set output
        self._output[position - 1] = (
            '  <div class="enlighten-bar">\n    %s\n  </div>' % self._converter.to_html(output)
        )

        if flush:
            self._flush_streams()
