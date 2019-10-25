# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._terminal
"""

from enlighten import _terminal

from tests import TestCase, mock, MockTTY


# pylint: disable=missing-docstring, protected-access

class TestTerminal(TestCase):
    """
    This is hard to test, so, for most tests, we'll just
    make sure the codes get passed through a tty
    """

    def setUp(self):
        self.tty = MockTTY()
        self.terminal = _terminal.Terminal(stream=self.tty.stdout, kind='xterm-256color')

    def tearDown(self):
        self.tty.close()

    def test_caching(self):
        """
        Make sure cached values are held.
        Return values aren't accurate for blessed, but are sufficient for this test
        """

        handw = 'enlighten._terminal._Terminal._height_and_width'

        with mock.patch(handw, return_value=(1, 2)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))

        with mock.patch(handw, return_value=(5, 6)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))
            self.terminal.clear_cache()
            self.assertEqual(self.terminal._height_and_width(), (5, 6))

    def test_reset(self):
        self.terminal.reset()
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         self.terminal.normal_cursor + self.terminal.csr(0, 25) +
                         self.terminal.move(25, 0) + 'X\n')

    def test_feed(self):

        self.terminal.feed()
        self.assertEqual(self.tty.stdread.readline(), self.terminal.cud1)

    def test_change_scroll(self):

        self.terminal.change_scroll(4)
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         self.terminal.hide_cursor + self.terminal.csr(0, 4) +
                         self.terminal.move(4, 0) + 'X\n')

    def test_move_to(self):

        self.terminal.move_to(5, 10)
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         self.terminal.move(10, 5) + 'X\n')
