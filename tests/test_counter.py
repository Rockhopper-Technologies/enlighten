# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._counter and enlighten.counter
"""

import time

from enlighten import Counter, Manager
import enlighten._counter
from enlighten._manager import NEEDS_UNICODE_HELP

from tests import TestCase, mock, MockManager, MockTTY, MockCounter


# pylint: disable=missing-docstring, protected-access, too-many-public-methods

class TestFormatTime(TestCase):
    """
    Test cases for :py:func:`_format_time`
    """

    def test_seconds(self):

        self.assertEqual(enlighten._counter._format_time(0), '00:00')
        self.assertEqual(enlighten._counter._format_time(6), '00:06')
        self.assertEqual(enlighten._counter._format_time(42), '00:42')

    def test_minutes(self):

        self.assertEqual(enlighten._counter._format_time(60), '01:00')
        self.assertEqual(enlighten._counter._format_time(128), '02:08')
        self.assertEqual(enlighten._counter._format_time(1684), '28:04')

    def test_hours(self):

        self.assertEqual(enlighten._counter._format_time(3600), '1h 00:00')
        self.assertEqual(enlighten._counter._format_time(43980), '12h 13:00')
        self.assertEqual(enlighten._counter._format_time(43998), '12h 13:18')

    def test_days(self):

        self.assertEqual(enlighten._counter._format_time(86400), '1d 0h 00:00')
        self.assertEqual(enlighten._counter._format_time(1447597), '16d 18h 06:37')


class TestCounter(TestCase):
    """
    Test the Counter classes
    We default to using enlighten.Counter and only use enlighten._counter.Counter when necessary
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)
        self.ctr = Counter(total=10, desc='Test', unit='ticks', manager=self.manager)
        self.manager.counters[self.ctr] = 3
        self.output = r'Test   0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00 ticks/s\]'

    def tearDown(self):
        self.tty.close()

    def test_no_manager(self):
        """Raise an error if there is no manager specified"""
        with self.assertRaisesRegex(TypeError, 'manager must be specified'):
            enlighten._counter.Counter()
        enlighten._counter.Counter(manager=self.manager)

    def test_increment(self):
        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.count, 1)
        counter.update(5)
        self.assertEqual(counter.count, 6)

    def test_enabled(self):
        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.enabled = False
        counter.update()
        self.assertEqual(counter.output, [1, 2])

    def test_delta(self):
        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.min_delta = .01
        time.sleep(.01)
        counter.update()
        self.assertEqual(counter.output, [1, 2, 4])

    def test_force(self):
        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update(force=True)
        self.assertEqual(counter.output, [1, 3])

    def test_refresh_total(self):
        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update(98)
        self.assertEqual(counter.output, [1, 100])

    def test_position(self):
        self.assertEqual(self.ctr.position, 3)

    def test_elapsed(self):
        ctr = self.ctr
        ctr.start = time.time() - 5.0
        ctr.last_update = ctr.start + 3.0

        self.assertEqual(int(ctr.elapsed), 5)

        # Clock stops running when total is reached
        ctr.count = ctr.total
        self.assertEqual(int(ctr.elapsed), 3)

    def test_refresh(self):
        self.ctr.refresh()
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=True, position=3\)' % self.output)

        self.manager.output = []
        self.ctr.refresh(flush=False)
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=False, position=3\)' % self.output)

        self.manager.output = []
        self.ctr.enabled = False
        self.ctr.refresh()
        self.assertEqual(len(self.manager.output), 0)

    def test_clear(self):
        self.ctr.clear()
        self.assertRegex(self.manager.output[0], r'write\(output=, flush=True, position=3\)')

        self.manager.output = []
        self.ctr.clear(flush=False)
        self.assertRegex(self.manager.output[0], r'write\(output=, flush=False, position=3\)')

        self.manager.output = []
        self.ctr.enabled = False
        self.ctr.clear()
        self.assertEqual(len(self.manager.output), 0)

    def test_remove(self):
        self.ctr.leave = False
        self.assertTrue(self.ctr in self.manager.counters)

        self.ctr.close()
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=True, position=3\)' % self.output)
        self.assertFalse(self.ctr in self.manager.counters)

        # If it runs again, it shouldn't throw an error
        self.ctr.close()

    def test_format_no_total(self):

        # No unit, No desc
        ctr = Counter(stream=self.tty.stdout, )
        self.assertRegex(ctr.format(width=80), r'0 \[00:0\d, 0.00/s\]')
        ctr.count = 50
        ctr.start = time.time() - 50
        self.assertRegex(ctr.format(width=80), r'50 \[00:5\d, \d.\d\d/s\]')

        # With unit and description
        ctr = Counter(stream=self.tty.stdout, desc='Test', unit='ticks')
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 0 ticks \[00:0\d, 0.00 ticks/s\]')
        ctr.count = 50
        ctr.start = time.time() - 50
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 50 ticks \[00:5\d, \d.\d\d ticks/s\]')

    def test_format_count_gt_total(self):
        """
        Counter should fall back to no-total format if count is greater than total
        """

        ctr = Counter(stream=self.tty.stdout, total=10, desc='Test', unit='ticks')
        ctr.count = 50
        ctr.start = time.time() - 50
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 50 ticks \[00:5\d, \d.\d\d ticks/s\]')

    def test_no_count(self):
        """
        Test for an empty counter
        """

        ctr = Counter(stream=self.tty.stdout, total=10, desc='Test', unit='ticks')
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test   0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00 ticks/s\]')

        # No unit, no description
        ctr = Counter(stream=self.tty.stdout, total=10)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'  0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00/s\]')

    def test_full_bar(self):

        ctr = Counter(stream=self.tty.stdout, total=10, desc='Test', unit='ticks')
        ctr.count = 10
        ctr.start = time.time() - 10
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted,
                         r'Test 100%\|' + u'█+' + r'\| 10/10 \[00:\d\d<00:00, \d.\d\d ticks/s\]')

    def test_zero_total(self):
        """
        If the total is 0, the bar should be full
        """

        ctr = Counter(stream=self.tty.stdout, total=0, desc='Test', unit='ticks')
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test 100%\|' u'█+' + r'\| 0/0 \[00:0\d<00:00, 0.00 ticks/s\]')

    def test_partial_bar(self):

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks')
        ctr.count = 50
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

        ctr.count = 13
        formatted = ctr.format(elapsed=13, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  13%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  13/100 \[00:1\d<01:\d\d, \d.\d\d ticks/s\]')

        # Explicit test
        ctr.bar_format = u'{bar}'
        ctr.count = 50
        formatted = ctr.format(width=10)
        self.assertEqual(formatted, u'█████     ')

        ctr.count = 13
        formatted = ctr.format(width=10)
        self.assertEqual(formatted, u'█▎        ')

    def test_custom_series(self):
        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks',
                      series=[' ', '>', '-'])
        ctr.count = 50
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'-+[>]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

        ctr.count = 13
        formatted = ctr.format(elapsed=13, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  13%\|' + u'---->' +
                         r'[ ]+\|  13/100 \[00:1\d<01:\d\d, \d.\d\d ticks/s\]')

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks',
                      series=[u'⭘', u'⬤'])
        ctr.count = 50
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'⬤+⭘+' +
                         r'\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

    def test_direct(self):
        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks')
        self.assertIsInstance(ctr.manager, Manager)
        ctr.start = time.time() - 50
        ctr.update(50, force=True)

        self.tty.stdout.write('X\n')
        value = self.tty.stdread.readline()
        if NEEDS_UNICODE_HELP:
            value = value.decode('utf-8')

        self.assertRegex(value, r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]X\n')

        with mock.patch.object(self.tty, 'stdout', wraps=self.tty.stdout) as mockstdout:
            ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks')
            ctr.refresh(flush=False)
            self.assertFalse(mockstdout.flush.called)
            ctr.refresh(flush=True)
            self.assertTrue(mockstdout.flush.called)

    def test_floats(self):
        """
        Using floats for total and count is supported by the logic, but not by the
        default format strings
        """

        ctr = Counter(stream=self.tty.stdout, total=100.2, desc='Test', unit='ticks', min_delta=500)
        ctr.update(50.1)
        self.assertEqual(ctr.count, 50.1)

        # Won't work with default formatting
        with self.assertRaises(ValueError):
            formatted = ctr.format(elapsed=50.1)

        ctr.bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:.1f}/{total:.1f} ' + \
                         u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

        formatted = ctr.format(elapsed=50.1, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'█+' +
                         r'[ ]+\| 50.1/100.2 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

    def test_close(self):
        manager = mock.Mock()

        # Clear is False
        ctr = MockCounter(manager=manager)
        ctr.close()
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove.call_count, 1)

        # Clear is True, leave is True
        ctr = MockCounter(manager=manager, leave=True)
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove.call_count, 2)

        # Clear is True, leave is False
        ctr = MockCounter(manager=manager, leave=False)
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['clear(flush=True)'])
        self.assertEqual(manager.remove.call_count, 3)

    def test_context_manager(self):
        mgr = Manager(stream=self.tty.stdout, enabled=False)
        with mgr.counter(total=10, leave=False) as ctr:
            self.assertTrue(ctr in mgr.counters)
            ctr.update()

        self.assertFalse(ctr in mgr.counters)
