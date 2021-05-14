
# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Enlighten utility submodule**

Provides utility functions and objects
"""

from collections import OrderedDict
import inspect
import os
import re
import sys
import warnings

from blessed.colorspace import RGB_256TABLE
from blessed.sequences import iter_parse


try:
    BASESTRING = basestring
except NameError:
    BASESTRING = str

BASE_DIR = os.path.basename(os.path.dirname(__file__))
FORMAT_MAP_SUPPORT = sys.version_info[:2] >= (3, 2)
RE_COLOR_RGB = re.compile(r'\x1b\[38;2;(\d+);(\d+);(\d+)m')
RE_ON_COLOR_RGB = re.compile(r'\x1b\[48;2;(\d+);(\d+);(\d+)m')
RE_COLOR_256 = re.compile(r'\x1b\[38;5;(\d+)m')
RE_ON_COLOR_256 = re.compile(r'\x1b\[48;5;(\d+)m')
RE_SET_A = re.compile(r'\x1b\[(\d+)m')
RE_LINK = re.compile(r'\x1b]8;.*;(.*)\x1b\\')

CGA_COLORS = ('black', 'red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white')
HTML_ESCAPE = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '?': '&#63;'}


class EnlightenWarning(Warning):
    """
    Generic warning class for Enlighten
    """


def warn_best_level(message, category):
    """
    Helper function to warn at first frame stack outside of library
    """

    level = 5  # Unused default
    for level, frame in enumerate(inspect.stack(), 1):  # pragma: no cover
        if os.path.basename(os.path.dirname(frame[1])) != BASE_DIR:
            break

    warnings.warn(message, category=category, stacklevel=level)


def format_time(seconds):
    """
    Args:
        seconds (float): amount of time

    Format time string for eta and elapsed
    """

    # Always do minutes and seconds in mm:ss format
    minutes = seconds // 60
    hours = minutes // 60
    rtn = u'%02.0f:%02.0f' % (minutes % 60, seconds % 60)

    #  Add hours if there are any
    if hours:

        rtn = u'%dh %s' % (int(hours % 24), rtn)

        #  Add days if there are any
        days = int(hours // 24)
        if days:
            rtn = u'%dd %s' % (days, rtn)

    return rtn


def raise_from_none(exc):  # pragma: no cover
    """
    Convenience function to raise from None in a Python 2/3 compatible manner
    """
    raise exc


if sys.version_info[0] >= 3:  # pragma: no branch
    exec('def raise_from_none(exc):\n    raise exc from None')  # pylint: disable=exec-used


class Justify(object):
    """
    Enumerated type for justification options

    .. py:attribute:: CENTER

        Justify center

    .. py:attribute:: LEFT

        Justify left

    .. py:attribute:: RIGHT

        Justify right

    """

    CENTER = 'center'
    LEFT = 'ljust'
    RIGHT = 'rjust'


class Lookahead:
    """
    Args:
        iterator(:py:term:`iterator`): Instance of an iterator

    Wrapper for an iterator supporting look ahead
    """

    def __init__(self, iterator):
        self.iterator = iterator
        self.buffer = []

    def __iter__(self):
        return self

    def __next__(self):
        if self.buffer:
            return self.buffer.pop(0)
        return next(self.iterator)

    # Python 2
    next = __next__

    def lookahead(self, start, stop=None):
        """
        Args:
            start(int): Positive integer index of first value
            stop(int): Positive integer index to end before (not returned)

        Retrieve next value(s) in iterator.

        start and stop roughly behave like slice notation, but must be positive
        """

        last = max(start, (stop or 0) - 1)

        while last >= len(self.buffer):
            try:
                self.buffer.append(next(self.iterator))
            except StopIteration:
                break

        if stop is None:
            return self.buffer[start]

        return self.buffer[start:stop]


class Span(list):
    """
    Container for span classes

    A list is used to preserve order
    """
    def __str__(self):
        return '<span class="%s">' % ' '.join(self)

    def append_unique(self, item):
        """
        Append only if value is unique
        """

        if item not in self:
            self.append(item)


class HTMLConverter(object):
    """
    Args:
        term(:py:class:`blessed.Terminal`): Blessed terminal instance

    Blessed-based ANSI terminal code to HTML converter
    """

    def __init__(self, term):

        self.term = term
        self.caps = self.term.caps
        self.normal = [elem[0] for elem in iter_parse(term, term.normal)]
        self.normal_rem = len(self.normal) - 1
        self._styles = OrderedDict()
        self._additional_styles = set()

    @property
    def style(self):
        """
        Formatted style section for an HTML document

        Styles are cumulative for the life of the instance
        """

        out = '<style>\n'

        for style, props in self._styles.items():
            out += '.%s {\n%s}\n' % (style, ''.join('  %s: %s;\n' % item for item in props.items()))

        if self._additional_styles:
            out += '%s\n' % '\n'.join(self._additional_styles)
        out += '</style>\n'

        return out

    def to_html(self, text):
        """
        Args:
            text(str): String formatted with ANSI escape codes

        Convert text to HTML

        Formatted text is enclosed in an HTML span and classes are available in HTMLConverter.style

        Supported formatting:
            - Blink
            - Bold
            - Color (8, 16, 256, and RGB)
            - Italic
            - Links
            - Underline
        """

        out = '<pre>'
        open_spans = 0
        to_out = []
        parsed = Lookahead(iter_parse(self.term, text))
        normal = self.normal

        # Iterate through parsed text
        for value, cap in parsed:

            # If there's no capability, it's just regular text
            if cap is None:

                # Add in any previous spans
                out += ''.join(str(item) for item in to_out)
                del to_out[:]  # Python 2 compatible .clear()

                # Append character and continue
                out += HTML_ESCAPE.get(value, value)
                continue

            # Parse links
            if cap is self.caps['link']:
                url = RE_LINK.match(value).group(1).strip()
                out += '<a href="%s">' % url if url else '<a>'
                continue

            last_added = to_out[-1] if to_out else None

            # Look for normal to close span
            if value == normal[0] and \
               normal[1:] == [val[0] for val in parsed.lookahead(0, self.normal_rem or None)]:

                # Clear rest of normal
                for _ in range(self.normal_rem):
                    next(parsed)

                # Ignore empty spans
                if isinstance(last_added, Span):
                    to_out.pop()
                    open_spans -= 1

                # Only add if there are open spans
                elif open_spans:
                    to_out.append('</span>')
                    open_spans -= 1

                continue  # pragma: no cover  # To be fixed in PEP 626 (3.10)

            # Parse styles
            key, value = self._parse_style(value, cap)

            # If not parsed, ignore
            if not key:
                continue

            # Update style sheet
            self._styles[key] = value

            # Update span classes
            if isinstance(last_added, Span):
                last_added.append_unique(key)
            else:
                to_out.append(Span([key]))
                open_spans += 1

        # Process any remaining caps
        out += ''.join(str(item) for item in to_out)

        # Close any spans that didn't get closed
        out += '</span>' * open_spans

        out += '</pre>'

        return out

    set_a_codes = {
            1: ('enlighten-bold', {'font-weight': 'bold'}),
            3: ('enlighten-italic', {'font-style': 'italic'}),
            5: ('enlighten-blink',
                {'animation': 'enlighten-blink-animation 1s steps(5, start) infinite'}),
            4: ('enlighten-underline', {'text-decoration': 'underline'}),
        }

    def _parse_style(self, value, cap):  # pylint: disable=too-many-return-statements
        r"""
        Args:
            value (str): VT100 terminal code
            cap(term(:py:class:`~blessed.sequences.Termcap`): Blessed terminal capability

        Parse text attributes of the form '\x1b\[\d+m' into CSS styles
        """

        caps = self.caps

        # Parse RGB color foreground
        if cap is caps['color_rgb']:
            rgb = '#%02x%02x%02x' % tuple(int(num) for num in RE_COLOR_RGB.match(value).groups())
            return 'enlighten-fg-%s' % rgb[1:], {'color': rgb}

        # Parse RGB color background
        if cap is caps['on_color_rgb']:
            rgb = '#%02x%02x%02x' % tuple(int(num) for num in RE_ON_COLOR_RGB.match(value).groups())
            return 'enlighten-bg-%s' % rgb[1:], {'background-color': rgb}

        # Weird and inconsistent bug that seems to affect Python <= 3.5
        # Matches set_a_attributes3 instead of more specific color 256 patterns
        if cap is caps['set_a_attributes3']:  # pragma: no cover
            if caps['color256'].re_compiled.match(value):
                cap = caps['color256']
            elif caps['on_color256'].re_compiled.match(value):
                cap = caps['on_color256']

        # Parse 256 color foreground
        if cap is caps['color256']:
            rgb = str(RGB_256TABLE[int(RE_COLOR_256.match(value).group(1))])
            return 'enlighten-fg-%s' % rgb[1:], {'color': rgb}

        # Parse 256 color background
        if cap is caps['on_color256']:
            rgb = str(RGB_256TABLE[int(RE_ON_COLOR_256.match(value).group(1))])
            return 'enlighten-bg-%s' % rgb[1:], {'background-color': rgb}

        # Parse text attributes
        if cap is caps['set_a_attributes1']:
            code = int(RE_SET_A.match(value).group(1))
        else:
            return None, None

        # Blink needs additional styling
        if code == 5:
            self._additional_styles.add(
                '@keyframes enlighten-blink-animation {\n  to {\n    visibility: hidden;\n  }\n}'
            )

        if code in self.set_a_codes:
            return self.set_a_codes[code]

        if 30 <= code <= 37:
            idx = code - 30
            return 'enlighten-fg-%s' % CGA_COLORS[idx], {'color': str(RGB_256TABLE[idx])}

        if 40 <= code <= 47:
            idx = code - 40
            return 'enlighten-bg-%s' % CGA_COLORS[idx], {'background-color': str(RGB_256TABLE[idx])}

        if 90 <= code <= 97:
            idx = code - 90
            return 'enlighten-fg-bright-%s' % CGA_COLORS[idx], {'color': str(RGB_256TABLE[idx + 8])}

        if 100 <= code <= 107:
            idx = code - 100
            return (
                'enlighten-bg-bright-%s' % CGA_COLORS[idx],
                {'background-color': str(RGB_256TABLE[idx + 8])}
            )

        return None, None
