# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._util
"""

from textwrap import dedent

import blessed

from enlighten._util import format_time, Lookahead, HTMLConverter

from tests import TestCase, MockTTY


class TestFormatTime(TestCase):
    """
    Test cases for :py:func:`_format_time`
    """

    def test_seconds(self):
        """Verify seconds formatting"""

        self.assertEqual(format_time(0), '00:00')
        self.assertEqual(format_time(6), '00:06')
        self.assertEqual(format_time(42), '00:42')

    def test_minutes(self):
        """Verify minutes formatting"""

        self.assertEqual(format_time(60), '01:00')
        self.assertEqual(format_time(128), '02:08')
        self.assertEqual(format_time(1684), '28:04')

    def test_hours(self):
        """Verify hours formatting"""

        self.assertEqual(format_time(3600), '1h 00:00')
        self.assertEqual(format_time(43980), '12h 13:00')
        self.assertEqual(format_time(43998), '12h 13:18')

    def test_days(self):
        """Verify days formatting"""

        self.assertEqual(format_time(86400), '1d 0h 00:00')
        self.assertEqual(format_time(1447597), '16d 18h 06:37')


class TestLookahead(TestCase):
    """
    Test cases for Lookahead
    """

    def test_iteration(self):
        """Verify normal iteration"""

        wrapped = Lookahead(iter(range(10)))

        self.assertEqual([next(wrapped) for _ in range(10)], list(range(10)))

    def test_lookahead(self):
        """Verify lookahead() behavior"""

        wrapped = Lookahead(iter(range(10)))

        self.assertEqual(wrapped.lookahead(0), 0)
        self.assertEqual(wrapped.lookahead(4), 4)
        self.assertEqual(wrapped.lookahead(2, 4), [2, 3])
        self.assertEqual(wrapped.lookahead(8, 12), [8, 9])

    def test_lookahead_iteration(self):
        """lookahead() output changes as iteration proceeds"""

        wrapped = Lookahead(iter(range(10)))

        self.assertEqual(next(wrapped), 0)
        self.assertEqual(wrapped.lookahead(0), 1)
        self.assertEqual(next(wrapped), 1)
        self.assertEqual(wrapped.lookahead(4), 6)
        self.assertEqual(next(wrapped), 2)
        self.assertEqual(wrapped.lookahead(2, 4), [5, 6])
        self.assertEqual(next(wrapped), 3)
        self.assertEqual(wrapped.lookahead(8, 12), [])


class TestHTMLConverter(TestCase):
    """
    Test cases for HTMLConverter
    """

    # pylint: disable=protected-access

    @classmethod
    def setUpClass(cls):
        cls.tty = MockTTY()
        cls.term = blessed.Terminal(
            stream=cls.tty.stdout, kind='xterm-256color', force_styling=True
        )
        cls.term.number_of_colors = 1 << 24

    @classmethod
    def tearDownClass(cls):
        cls.tty.close()

    def setUp(self):
        self.converter = HTMLConverter(term=self.term)

    def test_color(self):
        """Verify color conversion"""

        # CGA color on RGB color
        out = self.converter.to_html(self.term.blue_on_aquamarine('blue_on_aquam'))
        self.assertEqual(
            out,
            '<pre><span class="enlighten-fg-blue enlighten-bg-7fffd4">blue_on_aquam</span></pre>'
        )

        self.assertEqual(self.converter._styles['enlighten-fg-blue'], {'color': '#0000ee'})
        self.assertEqual(
            self.converter._styles['enlighten-bg-7fffd4'], {'background-color': '#7fffd4'}
        )

        # RGB color on CGA color
        out = self.converter.to_html(self.term.aquamarine_on_blue('aquam_on_blue'))
        self.assertEqual(
            out,
            '<pre><span class="enlighten-fg-7fffd4 enlighten-bg-blue">aquam_on_blue</span></pre>'
        )

        self.assertEqual(self.converter._styles['enlighten-fg-7fffd4'], {'color': '#7fffd4'})
        self.assertEqual(
            self.converter._styles['enlighten-bg-blue'], {'background-color': '#0000ee'}
        )

        # On RGB color
        out = self.converter.to_html(self.term.on_color_rgb(80, 4, 13)('on_color_rgb'))
        self.assertEqual(out, '<pre><span class="enlighten-bg-50040d">on_color_rgb</span></pre>')

        self.assertEqual(
            self.converter._styles['enlighten-bg-50040d'], {'background-color': '#50040d'}
        )

        # 256 Color
        out = self.converter.to_html(self.term.color(90)('color_90'))
        self.assertEqual(out, '<pre><span class="enlighten-fg-870087">color_90</span></pre>')

        self.assertEqual(self.converter._styles['enlighten-fg-870087'], {'color': '#870087'})

        # On 256 Color
        out = self.converter.to_html(self.term.on_color(90)('on_color_90'))
        self.assertEqual(out, '<pre><span class="enlighten-bg-870087">on_color_90</span></pre>')

        self.assertEqual(
            self.converter._styles['enlighten-bg-870087'], {'background-color': '#870087'}
        )

        # CGA Bright Color
        out = self.converter.to_html(self.term.bright_red('bright_red'))
        self.assertEqual(out, '<pre><span class="enlighten-fg-bright-red">bright_red</span></pre>')

        self.assertEqual(self.converter._styles['enlighten-fg-bright-red'], {'color': '#ff0000'})

        # On CGA Bright Color
        out = self.converter.to_html(self.term.on_bright_red('on_bright_red'))
        self.assertEqual(
            out,
            '<pre><span class="enlighten-bg-bright-red">on_bright_red</span></pre>'
        )

        self.assertEqual(
            self.converter._styles['enlighten-bg-bright-red'], {'background-color': '#ff0000'}
        )

    def test_style(self):
        """Verify style conversion"""

        # Italics
        out = self.converter.to_html(self.term.italic('italic'))
        self.assertEqual(out, '<pre><span class="enlighten-italic">italic</span></pre>')

        self.assertEqual(self.converter._styles['enlighten-italic'], {'font-style': 'italic'})

        # Bold
        out = self.converter.to_html(self.term.bold('bold'))
        self.assertEqual(out, '<pre><span class="enlighten-bold">bold</span></pre>')

        self.assertEqual(self.converter._styles['enlighten-bold'], {'font-weight': 'bold'})

        # Underline
        out = self.converter.to_html(self.term.underline('underline'))
        self.assertEqual(out, '<pre><span class="enlighten-underline">underline</span></pre>')

        self.assertEqual(
            self.converter._styles['enlighten-underline'], {'text-decoration': 'underline'}
        )

        # Blink
        out = self.converter.to_html(self.term.blink('blink'))
        self.assertEqual(out, '<pre><span class="enlighten-blink">blink</span></pre>')

        self.assertEqual(
            self.converter._additional_styles,
            {'@keyframes enlighten-blink-animation {\n  to {\n    visibility: hidden;\n  }\n}'}
        )

        self.assertEqual(
            self.converter._styles['enlighten-blink'],
            {'animation': 'enlighten-blink-animation 1s steps(5, start) infinite'}
        )

    def test_unsupported(self):
        """Verify unsupported does not produce classes"""

        # Unsupported capability
        out = self.converter.to_html(self.term.move(5, 6) + 'unsupported_move')
        self.assertEqual(out, '<pre>unsupported_move</pre>')

        # Unsupported text attribute
        out = self.converter.to_html(self.term.reverse('unsupported_reverse'))
        self.assertEqual(out, '<pre>unsupported_reverse</pre>')

    def test_link(self):
        """Verify link creates hyperlink"""

        out = self.converter.to_html(
            self.term.link('https://pypi.org/project/enlighten/', 'enlighten')
        )
        self.assertEqual(
            out,
            '<pre><a href="https://pypi.org/project/enlighten/">enlighten<a></pre>'
        )

    def test_empty_span(self):
        """Empty Spans are ignored"""

        out = self.converter.to_html(self.term.underline('') + 'empty')
        self.assertEqual(out, '<pre>empty</pre>')

    def test_class_not_unique(self):
        """Repeated classes are dropped within the same span"""

        out = self.converter.to_html(self.term.blue_on_aquamarine(self.term.blue('blue_on_aquam')))
        self.assertEqual(
            out,
            '<pre><span class="enlighten-fg-blue enlighten-bg-7fffd4">blue_on_aquam</span></pre>'
        )

    def test_style_output(self):
        """Verify style section output"""

        out = self.converter.to_html(self.term.red_on_slategrey('red_on_slategrey'))

        self.assertEqual(
            out,
            '<pre><span class="enlighten-fg-red enlighten-bg-708090">red_on_slategrey</span></pre>'
        )

        style = '''\
        <style>
        .enlighten-fg-red {
          color: #cd0000;
        }
        .enlighten-bg-708090 {
          background-color: #708090;
        }
        </style>
        '''

        self.assertEqual(self.converter.style, dedent(style))

    def test_style_output_additional(self):
        """Verify style section output with additional sections"""

        out = self.converter.to_html(self.term.blink('blink'))
        self.assertEqual(out, '<pre><span class="enlighten-blink">blink</span></pre>')

        style = '''\
        <style>
        .enlighten-blink {
          animation: enlighten-blink-animation 1s steps(5, start) infinite;
        }
        @keyframes enlighten-blink-animation {
          to {
            visibility: hidden;
          }
        }
        </style>
        '''

        self.assertEqual(self.converter.style, dedent(style))
