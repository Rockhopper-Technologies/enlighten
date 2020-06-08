# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._util
"""

from enlighten._util import format_time

from tests import TestCase


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
