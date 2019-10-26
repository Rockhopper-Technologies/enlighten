# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._counter and enlighten.counter
"""

import time
from types import GeneratorType

from enlighten import Counter, Manager
import enlighten._counter
from enlighten._manager import NEEDS_UNICODE_HELP

from tests import TestCase, mock, MockManager, MockTTY, MockCounter, MockBaseCounter


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


class TestBaseCounter(TestCase):
    """
    Test the BaseCounter class
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)

    def tearDown(self):
        self.tty.close()

    def test_init_default(self):
        """Ensure default values are set"""
        counter = enlighten._counter.BaseCounter(manager=self.manager)
        self.assertIsNone(counter.color)
        self.assertIsNone(counter.color)
        self.assertIs(counter.manager, self.manager)
        self.assertEqual(counter.count, 0)
        self.assertEqual(counter.start_count, 0)

    def test_no_manager(self):
        """Raise an error if there is no manager specified"""
        with self.assertRaisesRegex(TypeError, 'manager must be specified'):
            enlighten._counter.BaseCounter()

    def test_color(self):
        """Color must be a valid string or int 0 - 255"""
        # Unsupported type
        with self.assertRaisesRegex(TypeError, 'color must be a string or integer'):
            enlighten._counter.BaseCounter(manager=self.manager, color=[])

        # Color is a string
        counter = enlighten._counter.BaseCounter(manager=self.manager, color='red')
        self.assertEqual(counter.color, 'red')
        with self.assertRaisesRegex(ValueError, 'Unsupported color: banana'):
            enlighten._counter.BaseCounter(manager=self.manager, color='banana')

        # Color is an integer
        counter = enlighten._counter.BaseCounter(manager=self.manager, color=15)
        self.assertEqual(counter.color, 15)
        with self.assertRaisesRegex(ValueError, 'Unsupported color: -1'):
            enlighten._counter.BaseCounter(manager=self.manager, color=-1)
        with self.assertRaisesRegex(ValueError, 'Unsupported color: 256'):
            enlighten._counter.BaseCounter(manager=self.manager, color=256)

    def test_colorize_none(self):
        """If color is None, return content unchanged"""
        counter = enlighten._counter.BaseCounter(manager=self.manager)
        self.assertEqual(counter._colorize('test'), 'test')

    def test_colorize(self):
        """Return string formatted with color"""
        # Color is a string
        counter = enlighten._counter.BaseCounter(manager=self.manager, color='red')
        self.assertIsNone(counter._color)
        self.assertNotEqual(counter._colorize('test'), 'test')
        cache = counter._color
        self.assertEqual(counter._colorize('test'), self.manager.term.red('test'))
        self.assertEqual(counter._color[0], 'red')
        self.assertIs(counter._color[1], self.manager.term.red)
        self.assertIs(counter._color, cache)

        # Color is an integer
        counter = enlighten._counter.BaseCounter(manager=self.manager, color=40)
        self.assertIsNone(counter._color)
        self.assertNotEqual(counter._colorize('test'), 'test')
        cache = counter._color
        self.assertEqual(counter._colorize('test'), self.manager.term.color(40)('test'))
        self.assertEqual(counter._color[0], 40)
        # New instance is generated each time, so just compare strings
        self.assertEqual(counter._color[1], self.manager.term.color(40))
        self.assertIs(counter._color, cache)

    def test_call(self):
        """Returns generator when used as a function"""

        # Bad arguments
        counter = MockBaseCounter(manager=self.manager)
        with self.assertRaisesRegex(TypeError, 'Argument type int is not iterable'):
            list(counter(1))
        with self.assertRaisesRegex(TypeError, 'Argument type bool is not iterable'):
            list(counter([1, 2, 3], True))

        # Expected
        counter = MockBaseCounter(manager=self.manager)
        rtn = counter([1, 2, 3])
        self.assertIsInstance(rtn, GeneratorType)
        self.assertEqual(list(rtn), [1, 2, 3])
        self.assertEqual(counter.count, 3)

        # Multiple arguments
        counter = MockBaseCounter(manager=self.manager)
        rtn = counter([1, 2, 3], (3, 2, 1))
        self.assertIsInstance(rtn, GeneratorType)
        self.assertEqual(tuple(rtn), (1, 2, 3, 3, 2, 1))
        self.assertEqual(counter.count, 6)


class TestSubCounter(TestCase):
    """
    Test the BaseCounter class
    """
    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)
        self.parent = Counter(total=10, desc='Test', unit='ticks', manager=self.manager)

    def tearDown(self):
        self.tty.close()

    def test_init(self):
        """Ensure initial values are set"""
        counter = enlighten._counter.SubCounter(self.parent)
        self.assertIsNone(counter.color)
        self.assertEqual(counter.count, 0)
        self.assertFalse(counter.all_fields)
        self.assertIs(counter.parent, self.parent)
        self.assertIs(counter.manager, self.manager)

        self.parent.count = 4
        counter = enlighten._counter.SubCounter(self.parent, color='green',
                                                count=4, all_fields=True)
        self.assertEqual(counter.color, 'green')
        self.assertEqual(counter.count, 4)
        self.assertTrue(counter.all_fields)

        with self.assertRaisesRegex(ValueError, 'Invalid count: 6'):
            counter = enlighten._counter.SubCounter(self.parent, count=6)

    def test_update(self):
        """Increment and update parent"""
        counter = enlighten._counter.SubCounter(self.parent)
        self.assertEqual(counter.count, 0)
        self.assertEqual(self.parent.count, 0)
        counter.update()
        self.assertEqual(counter.count, 1)
        self.assertEqual(self.parent.count, 1)
        self.parent.update(3)
        self.assertEqual(counter.count, 1)
        self.assertEqual(self.parent.count, 4)
        counter.update(2)
        self.assertEqual(counter.count, 3)
        self.assertEqual(self.parent.count, 6)

    def test_update_from_invalid_source(self):
        """Must be peer or parent"""
        counter = enlighten._counter.SubCounter(self.parent)

        notparent = Counter(manager=self.manager)
        with self.assertRaisesRegex(ValueError, 'source must be parent or peer'):
            counter.update_from(notparent)

        notpeer = enlighten._counter.SubCounter(notparent)
        with self.assertRaisesRegex(ValueError, 'source must be parent or peer'):
            counter.update_from(notpeer)

    def test_update_from_invalid_incr(self):
        """Increment can't make source negative"""
        counter = enlighten._counter.SubCounter(self.parent)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 1'):
            counter.update_from(self.parent)

        self.parent.count = 4
        peer = enlighten._counter.SubCounter(self.parent, count=3)
        self.parent._subcounters.append(peer)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 4'):
            counter.update_from(peer, 4)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 2'):
            counter.update_from(self.parent, 2)

    def test_update_from_parent(self):
        """
        subcounter should gain increment, parent should remain unchanged
        """
        counter = enlighten._counter.SubCounter(self.parent)
        self.parent.count = 4

        with mock.patch.object(self.parent, 'update', wraps=self.parent.update) as update:
            counter.update_from(self.parent)
            update.assert_called_with(0, False)
            self.assertEqual(self.parent.count, 4)
            self.assertEqual(counter.count, 1)

            counter.update_from(self.parent, 2)
            update.assert_called_with(0, False)
            self.assertEqual(self.parent.count, 4)
            self.assertEqual(counter.count, 3)

    def test_update_from_peer(self):
        """
        Peer should lose increment, subcounter should gain increment
        """
        counter = enlighten._counter.SubCounter(self.parent)
        self.parent.count = 6
        peer = enlighten._counter.SubCounter(self.parent, count=4)

        with mock.patch.object(self.parent, 'update', wraps=self.parent.update) as update:
            counter.update_from(peer)
            update.assert_called_with(0, False)
            self.assertEqual(self.parent.count, 6)
            self.assertEqual(counter.count, 1)
            self.assertEqual(peer.count, 3)

            counter.update_from(peer, 3)
            update.assert_called_with(0, False)
            self.assertEqual(self.parent.count, 6)
            self.assertEqual(counter.count, 4)
            self.assertEqual(peer.count, 0)


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

    def test_get_subcounter(self):
        self.ctr.count = 6
        subcounter1 = self.ctr.add_subcounter('green')
        subcounter2 = self.ctr.add_subcounter('red', all_fields=True)
        subcounter2.count = 4
        subcounter3 = self.ctr.add_subcounter('white', count=1, all_fields=True)

        subcounters, fields = self.ctr._get_subcounters(8)

        self.assertEqual(subcounters, [(subcounter1, 0.0), (subcounter2, 0.4), (subcounter3, 0.1)])
        self.assertEqual(fields, {'percentage_1': 0.0, 'percentage_2': 40.0, 'percentage_3': 10.0,
                                  'count_1': 0, 'count_2': 4, 'count_3': 1,
                                  'rate_2': 0.5, 'eta_2': '00:12', 'rate_3': 0.0, 'eta_3': '?'})

        subcounters, fields = self.ctr._get_subcounters(0)
        self.assertEqual(subcounters, [(subcounter1, 0.0), (subcounter2, 0.4), (subcounter3, 0.1)])
        self.assertEqual(fields, {'percentage_1': 0.0, 'percentage_2': 40.0, 'percentage_3': 10.0,
                                  'count_1': 0, 'count_2': 4, 'count_3': 1,
                                  'rate_2': 0.0, 'eta_2': '?', 'rate_3': 0.0, 'eta_3': '?'})

        self.ctr = Counter(total=0, desc='Test', unit='ticks', manager=self.manager)
        subcounter1 = self.ctr.add_subcounter('red', all_fields=True)
        subcounters, fields = self.ctr._get_subcounters(8)
        self.assertEqual(subcounters, [(subcounter1, 0.0)])
        self.assertEqual(fields, {'percentage_1': 0.0, 'count_1': 0,
                                  'rate_1': 0.0, 'eta_1': '00:00'})

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

    def test_auto_offset(self):
        """
        If offset is not specified, terminal codes should be automatically ignored
        when calculating bar length
        """

        barFormat = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d} ' + \
                    u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        blueBarFormat = self.manager.term.blue(barFormat)
        self.assertNotEqual(len(barFormat), len(blueBarFormat))

        ctr = self.manager.counter(stream=self.tty.stdout, total=10, desc='Test',
                                   unit='ticks', count=10, bar_format=barFormat)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        barLen1 = formatted1.count(u'█')

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(stream=self.tty.stdout, total=10, desc='Test',
                                   unit='ticks', count=10, bar_format=blueBarFormat)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        barLen2 = formatted2.count(u'█')

        self.assertTrue(barLen2 == barLen1)

    def test_offset(self):
        """
        Offset reduces count of printable characters when formatting
        """

        barFormat = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d} ' + \
                    u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        barFormat = self.manager.term.blue(barFormat)

        ctr = self.manager.counter(stream=self.tty.stdout, total=10, desc='Test',
                                   unit='ticks', count=10, bar_format=barFormat, offset=0)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        barLen1 = formatted1.count(u'█')

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(stream=self.tty.stdout, total=10, desc='Test',
                                   unit='ticks', count=10, bar_format=barFormat, offset=offset)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        barLen2 = formatted2.count(u'█')

        self.assertTrue(barLen2 == barLen1 + offset)

        # Test in counter format
        ctr = self.manager.counter(stream=self.tty.stdout, total=10, count=50, offset=0)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)

        ctr = self.manager.counter(stream=self.tty.stdout, total=10, count=50, offset=10)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 90)

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

        self.tty.stdout.write(u'X\n')
        value = self.tty.stdread.readline()
        if NEEDS_UNICODE_HELP:
            value = value.decode('utf-8')

        self.assertRegex(value, r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]X\n')

        with mock.patch.object(self.tty, 'stdout', wraps=self.tty.stdout) as mockstdout:
            mockstdout.encoding = None
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

    def test_color(self):
        """
        Only bar characters should be colorized
        """

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=u'|{bar}|',
                      count=50, color='red')
        terminal = ctr.manager.term
        formatted = ctr.format(width=80)
        self.assertEqual(formatted, '|' + terminal.red(u'█' * 39 + ' ' * 39) + '|')

    def test_subcounter(self):
        """
        When subcounter is present, bar will be drawn in multiple colors
        """

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=u'{bar}')
        terminal = ctr.manager.term
        ctr.count = 50
        subcounter1 = ctr.add_subcounter('yellow', all_fields=True)
        subcounter1.count = 5
        ctr.add_subcounter('blue', count=10)

        formatted = ctr.format(width=80)
        bartext = terminal.blue(u'█'*8) + terminal.yellow(u'█'*4) + u'█'*28 + ' ' * 40
        self.assertEqual(formatted, bartext)

        ctr.bar_format = u'{count_0} {percentage_0} | {count_1} {percentage_1} {rate_1} {eta_1}' + \
                         u' | {count_2} {percentage_2}'

        formatted = ctr.format(elapsed=5, width=80)
        self.assertEqual(formatted, u'35 35.0 | 5 5.0 1.0 01:35 | 10 10.0')

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

    def test_add_subcounter(self):

        self.assertEqual(self.ctr._subcounters, [])
        subcounter1 = self.ctr.add_subcounter('blue')
        self.assertEqual(len(self.ctr._subcounters), 1)
        self.assertEqual(self.ctr.subcount, 0)
        self.assertIs(self.ctr._subcounters[0], subcounter1)
        self.assertEqual(subcounter1.count, 0)
        self.assertFalse(subcounter1.all_fields)

        with self.assertRaisesRegex(ValueError, 'Invalid count: 5'):
            self.ctr.add_subcounter('yellow', count=5, all_fields=True)

        self.ctr.count = 5
        subcounter2 = self.ctr.add_subcounter('yellow', count=5, all_fields=True)
        self.assertEqual(len(self.ctr._subcounters), 2)
        self.assertEqual(self.ctr.subcount, 5)
        self.assertIs(self.ctr._subcounters[1], subcounter2)
        self.assertEqual(subcounter2.count, 5)
        self.assertTrue(subcounter2.all_fields)
