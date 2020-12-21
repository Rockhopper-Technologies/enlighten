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

        h_and_w = 'enlighten._terminal._Terminal._height_and_width'

        with mock.patch(h_and_w, return_value=(1, 2)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))

        with mock.patch(h_and_w, return_value=(5, 6)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))
            self.terminal.clear_cache()
            self.assertEqual(self.terminal._height_and_width(), (5, 6))
