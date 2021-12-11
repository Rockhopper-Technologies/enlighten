# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._counter and enlighten.counter
"""

import time

from enlighten import Counter, EnlightenWarning, Manager
import enlighten._counter

from tests import TestCase, mock, MockManager, MockTTY, MockCounter, PY2, unittest


# pylint: disable=missing-docstring, protected-access, too-many-public-methods
SERIES_STD = u' ▏▎▍▌▋▊▉█'
BLOCK = enlighten._counter.SERIES_STD[-1]


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

    def test_repr(self):
        self.assertEqual(repr(self.ctr), "Counter(desc='Test', total=10, count=0, unit='ticks')")

    def test_repr_subcounter(self):
        self.ctr.count = 2
        subcounter = self.ctr.add_subcounter('green', count=1)
        self.assertEqual(repr(subcounter), "SubCounter(count=1, color='green', all_fields=False)")

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
        self.ctr.last_update = 0
        self.ctr.refresh()
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=True, position=3\)' % self.output)
        self.assertAlmostEqual(self.ctr.last_update, time.time(), delta=0.3)

        self.manager.output = []
        self.ctr.refresh(flush=False)
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=False, position=3\)' % self.output)

        self.manager.output = []
        self.ctr.enabled = False
        self.ctr.refresh()
        self.assertEqual(len(self.manager.output), 0)

    def test_clear(self):
        self.ctr.last_update = 100
        self.ctr.clear()
        self.assertRegex(self.manager.output[0], r'write\(output=, flush=True, position=3\)')
        self.assertEqual(self.ctr.last_update, 0)

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

        fields = {'count': self.ctr.count, 'percentage': 60.0}
        subcounters = self.ctr._get_subcounters(8, fields)
        self.assertEqual(subcounters, [(subcounter1, 0.0), (subcounter2, 0.4), (subcounter3, 0.1)])
        self.assertEqual(fields, {'count': 6, 'count_0': 1, 'count_00': 5,
                                  'percentage': 60.0, 'percentage_0': 10.0, 'percentage_00': 50.0,
                                  'percentage_1': 0.0, 'percentage_2': 40.0, 'percentage_3': 10.0,
                                  'count_1': 0, 'count_2': 4, 'count_3': 1,
                                  'interval_0': 4.0, 'interval_00': 2.0,
                                  'interval_2': 2.0, 'interval_3': 0.0,
                                  'rate_0': 0.25, 'rate_00': 0.5,
                                  'rate_2': 0.5, 'eta_2': '00:12', 'rate_3': 0.0, 'eta_3': '?'})

        fields = {'count': self.ctr.count, 'percentage': 60.0}
        subcounters = self.ctr._get_subcounters(0, fields)
        self.assertEqual(subcounters, [(subcounter1, 0.0), (subcounter2, 0.4), (subcounter3, 0.1)])
        self.assertEqual(fields, {'count': 6, 'count_0': 1, 'count_00': 5,
                                  'percentage': 60.0, 'percentage_0': 10.0, 'percentage_00': 50.0,
                                  'percentage_1': 0.0, 'percentage_2': 40.0, 'percentage_3': 10.0,
                                  'count_1': 0, 'count_2': 4, 'count_3': 1,
                                  'interval_0': 0.0, 'interval_00': 0.0,
                                  'interval_2': 0.0, 'interval_3': 0.0,
                                  'rate_0': 0.0, 'rate_00': 0.0,
                                  'rate_2': 0.0, 'eta_2': '?', 'rate_3': 0.0, 'eta_3': '?'})

        self.ctr = Counter(total=0, desc='Test', unit='ticks', manager=self.manager)
        subcounter1 = self.ctr.add_subcounter('red', all_fields=True)

        fields = {'count': self.ctr.count, 'percentage': 0.0}
        subcounters = self.ctr._get_subcounters(8, fields)
        self.assertEqual(subcounters, [(subcounter1, 0.0)])
        self.assertEqual(fields, {'count': 0, 'count_0': 0, 'count_00': 0,
                                  'percentage': 0.0, 'percentage_0': 0.0, 'percentage_00': 0.0,
                                  'percentage_1': 0.0, 'count_1': 0,
                                  'interval_0': 0.0, 'interval_00': 0.0,
                                  'rate_0': 0.0, 'rate_00': 0.0,
                                  'interval_1': 0.0, 'rate_1': 0.0, 'eta_1': '00:00'})

    def test_get_subcounter_counter_format(self):
        self.ctr.count = 12
        subcounter1 = self.ctr.add_subcounter('green')
        subcounter2 = self.ctr.add_subcounter('red', all_fields=True)
        subcounter2.count = 6
        subcounter3 = self.ctr.add_subcounter('white', count=1, all_fields=True)

        fields = {'count': self.ctr.count}
        subcounters = self.ctr._get_subcounters(8, fields, bar_fields=False)
        self.assertEqual(subcounters, [(subcounter1, 0.0), (subcounter2, 0.0), (subcounter3, 0.0)])
        self.assertEqual(fields, {'count': 12, 'count_0': 5, 'count_00': 7,
                                  'count_1': 0, 'count_2': 6, 'count_3': 1,
                                  'interval_0': 0.75 ** -1, 'interval_00': 0.75 ** -1,
                                  'interval_2': 0.75 ** -1, 'interval_3': 0.0,
                                  'rate_0': 0.75, 'rate_00': 0.75,
                                  'rate_2': 0.75, 'rate_3': 0.0})

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

        ctr = Counter(stream=self.tty.stdout, total=10, desc='Test',
                      unit='ticks', series=SERIES_STD)
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

        ctr = Counter(stream=self.tty.stdout, total=0, desc='Test', unit='ticks', series=SERIES_STD)
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

        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=barFormat)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        barLen1 = formatted1.count(BLOCK)

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=blueBarFormat)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        barLen2 = formatted2.count(BLOCK)

        self.assertTrue(barLen2 == barLen1)

    def test_offset(self):
        """
        Offset reduces count of printable characters when formatting
        """

        barFormat = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d} ' + \
                    u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        barFormat = self.manager.term.blue(barFormat)

        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=barFormat, offset=0)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        barLen1 = formatted1.count(BLOCK)

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=barFormat, offset=offset)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        barLen2 = formatted2.count(BLOCK)

        self.assertTrue(barLen2 == barLen1 + offset)

        # Test in counter format
        ctr = self.manager.counter(total=10, count=50, offset=0)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)

        ctr = self.manager.counter(total=10, count=50, offset=10)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 90)

    def test_partial_bar(self):

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test',
                      unit='ticks', series=SERIES_STD)
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
        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test',
                      unit='ticks', series=SERIES_STD)
        self.assertIsInstance(ctr.manager, Manager)
        ctr.start = time.time() - 50
        ctr.update(50, force=True)

        self.tty.stdout.write(u'X\n')
        value = self.tty.stdread.readline()

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

        ctr = Counter(stream=self.tty.stdout, total=100.2, desc='Test',
                      unit='ticks', min_delta=500, series=SERIES_STD)
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

    def test_floats_prefixed(self):
        """
        Floats should support prefixed formatting
        """
        bar_format = u'{count:!.2j}B / {total:!.2j}B | {rate:!.2j}B/s | {interval:!.2j} s/B'

        ctr = Counter(stream=self.tty.stdout, total=3.2 * 2 ** 20, bar_format=bar_format)
        ctr.count = 2048.0

        formatted = ctr.format(elapsed=2, width=80)
        self.assertEqual(formatted, '2.00 KiB / 3.20 MiB | 1.00 KiB/s | 0.00 s/B')

        # Counter_format
        counter_format = u'{count:!.2j}B | {rate:!.2j}B/s | {interval:!.2j} s/B'

        ctr = Counter(stream=self.tty.stdout, counter_format=counter_format)
        ctr.count = 2048.0

        formatted = ctr.format(elapsed=2, width=80)
        self.assertEqual(formatted, '2.00 KiB | 1.00 KiB/s | 0.00 s/B')

    def test_color(self):
        """
        Only bar characters should be colorized
        """

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=u'|{bar}|',
                      count=50, color='red')
        terminal = ctr.manager.term
        formatted = ctr.format(width=80)
        self.assertEqual(formatted, '|' + terminal.red(BLOCK * 39 + ' ' * 39) + '|')

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
        bartext = terminal.blue(BLOCK*8) + terminal.yellow(BLOCK*4) + BLOCK*28 + ' ' * 40
        self.assertEqual(formatted, bartext)

        ctr.bar_format = u'{count_0} {percentage_0} | {count_1} {percentage_1} {rate_1} {eta_1}' + \
                         u' | {count_2} {percentage_2} | {count_00} {percentage_00:.1f}'

        formatted = ctr.format(elapsed=5, width=80)
        self.assertEqual(formatted, u'35 35.0 | 5 5.0 1.0 01:35 | 10 10.0 | 15 15.0')

    def test_subcounter_field_not_populated(self):
        """
        Exception raised when reserved field is invalid
        """

        ctr = Counter(stream=self.tty.stdout, total=100, count=50)
        ctr.add_subcounter('yellow')
        ctr.add_subcounter('blue', count=10)

        ctr.bar_format = u'{count_3}'
        with self.assertRaisesRegex(ValueError, 'subcounter 3 is not defined'):
            ctr.format(elapsed=5, width=80)

        for fmt in (u'{rate_1}', u'{eta_1}', u'{interval_1}'):
            ctr.bar_format = fmt
            with self.assertRaisesRegex(ValueError, "'all_fields' not specified for subcounter"):
                ctr.format(elapsed=5, width=80)

        ctr = Counter(stream=self.tty.stdout, total=100, count=50,)
        for fmt in (u'{count_0}', u'{rate_0}', u'{percentage_0}',
                    u'{count_00}', u'{rate_00}', u'{percentage_00}'):
            ctr.bar_format = fmt
            with self.assertRaisesRegex(ValueError, 'no subcounters are configured'):
                ctr.format(elapsed=5, width=80)

        # Counter fields
        ctr = Counter(stream=self.tty.stdout, count=50)
        ctr.add_subcounter('yellow')
        for field in ('percentage_1', 'eta_1'):
            ctr.counter_format = u'|{%s}|' % field
            with self.assertRaisesRegex(ValueError, 'unavailable for counter_format'):
                ctr.format(elapsed=5, width=80)

    def test_subcounter_count_gt_total(self):
        """
        When total is exceeded, subcounter fields are still populated
        """
        counter_format = u'{count_0} | {count_1} {rate_1} | {count_2} | {count_00}'
        ctr = Counter(stream=self.tty.stdout, total=100, counter_format=counter_format)

        ctr.count = 500
        subcounter1 = ctr.add_subcounter('yellow', all_fields=True)
        subcounter1.count = 50
        ctr.add_subcounter('blue', count=100)
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(formatted, u'350 | 50 1.0 | 100 | 150')

    def test_subcounter_count_0(self):
        """
        When all of count is covered by subcounters, nothing should print for main counter
        """

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=u'{bar}')
        term = ctr.manager.term
        ctr.count = 50
        ctr.add_subcounter('yellow', count=44)
        ctr.add_subcounter('blue', count=4)
        ctr.add_subcounter('red', count=2)

        formatted = ctr.format(width=80)
        bartext = term.red(BLOCK*2) + term.blue(BLOCK*3) + term.yellow(BLOCK*35) + ' ' * 40
        self.assertEqual(formatted, bartext)

    def test_subcounter_prefixed(self):
        """
        Subcounter float fields should support prefixed formatting
        """

        bar_format = (u'{count:!.2j}B / {total:!.2j}B | {rate:!.2j}B/s | {interval:!.2j} s/B'
                      u' | {count_0:!.2j}B | {count_00:!.2j}B'
                      u' | {count_1:!.2j}B | {rate_1:!.2j}B/s | {interval_1:!.2j} s/B'
                      u' | {count_2:!.2j}B | {rate_2:!.2j}B/s | {interval_2:!.2j} s/B'
                      u' | {count_3:!.2j}B | {rate_3:!.2j}B/s | {interval_3:!.2j} s/B'
                      )
        ctr = Counter(stream=self.tty.stdout, total=3.2 * 2 ** 20,
                      bar_format=bar_format, all_fields=True)

        ctr.count = 2.0 ** 20
        subcounter1 = ctr.add_subcounter('yellow')
        subcounter2 = ctr.add_subcounter('blue')
        subcounter3 = ctr.add_subcounter('red')

        subcounter1.count = 512.0 * 2 ** 10
        subcounter2.count = 256.0 * 2 ** 10
        subcounter3.count = 128.0 * 2 ** 10

        formatted = ctr.format(elapsed=1, width=80)
        self.assertEqual(
            formatted, (
                '1.00 MiB / 3.20 MiB | 1.00 MiB/s | 0.00 s/B'
                ' | 128.00 KiB | 896.00 KiB'
                ' | 512.00 KiB | 512.00 KiB/s | 0.00 s/B'
                ' | 256.00 KiB | 256.00 KiB/s | 0.00 s/B'
                ' | 128.00 KiB | 128.00 KiB/s | 0.00 s/B'
            )
        )

    def test_close(self):
        manager = MockManager()

        # Clear is False
        ctr = MockCounter(manager=manager)
        ctr.close()
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove_calls, 1)

        # Clear is True, leave is True
        ctr = MockCounter(manager=manager, leave=True)
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove_calls, 2)

        # Clear is True, leave is False
        ctr = MockCounter(manager=manager, leave=False)
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['clear(flush=True)'])
        self.assertEqual(manager.remove_calls, 3)

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

    def test_reserve_field_unavailable(self):
        """
        Exception raised when reserved field is invalid
        """

        msg1 = "Reserve field '%s' specified in format, but unavailable for bar_format"
        msg2 = "Reserve field '%s' specified in format, but unavailable for counter_format"

        ctr = Counter(stream=self.tty.stdout, total=100, count=50)
        ctr.bar_format = u'{fill}'
        with self.assertRaisesRegex(ValueError, msg1 % 'fill'):
            ctr.format(elapsed=5, width=80)

        ctr = Counter(stream=self.tty.stdout, count=50)

        for field in ('bar', 'eta', 'percentage'):
            ctr.counter_format = u'{%s}' % field
            with self.assertRaisesRegex(ValueError, msg2 % field):
                ctr.format(elapsed=5, width=80)

    def test_fields_curly_braces(self):
        """
        Ensure curly braces work in fields
        """

        ctr_format = u'{desc} {count:d} {unit}{fill}'
        bar_format = u'{desc} {count:d} {unit}{bar}'

        ctr = Counter(stream=self.tty.stdout, total=1, desc='open{', unit='dudes',
                      counter_format=ctr_format, bar_format=bar_format)
        self.assertEqual(ctr.format(width=80), 'open{ 0 dudes' + ' ' * 67)
        ctr.count = 4
        self.assertEqual(ctr.format(width=80), 'open{ 4 dudes' + ' ' * 67)

        ctr.desc = 'normal'
        ctr.unit = 'close}'
        ctr.count = 0

        self.assertEqual(ctr.format(width=80), 'normal 0 close}' + ' ' * 65)
        ctr.count = 4
        self.assertEqual(ctr.format(width=80), 'normal 4 close}' + ' ' * 65)

    def test_additional_fields(self):
        """
        Add additional fields to format
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      fields={'arg1': 'hello'})
        self.assertEqual(ctr.format(), 'hello 1')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      fields={'arg1': 'hello'})
        self.assertEqual(ctr.format(), 'hello 1')

    def test_additional_fields_missing(self):
        """
        Raise a ValueError when a keyword is missing
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format)
        with self.assertRaisesRegex(ValueError, "'arg1' specified in format, but not provided"):
            ctr.format()

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format)
        with self.assertRaisesRegex(ValueError, "'arg1' specified in format, but not provided"):
            ctr.format()

    def test_additional_fields_changed(self):
        """
        Change additional fields
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'
        additional_fields = {'arg1': 'hello'}

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      fields=additional_fields)
        self.assertEqual(ctr.format(), 'hello 1')
        additional_fields['arg1'] = 'goodbye'
        self.assertEqual(ctr.format(), 'goodbye 1')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      fields=additional_fields)
        self.assertEqual(ctr.format(), 'goodbye 1')
        additional_fields['arg1'] = 'hello'
        self.assertEqual(ctr.format(), 'hello 1')

    def test_additional_fields_no_overwrite(self):
        """
        Additional fields can not overwrite dynamic fields
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'
        additional_fields = {'arg1': 'hello'}

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      fields=additional_fields)
        self.assertEqual(ctr.format(), 'hello 1')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      fields=additional_fields)
        self.assertEqual(ctr.format(), 'hello 1')

    def test_kwarg_fields(self):
        """
        Additional fields to format via keyword arguments
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      arg1='hello')
        self.assertEqual(ctr.format(), 'hello 1')

        ctr.update(arg1='goodbye')
        self.assertEqual(ctr.format(), 'goodbye 2')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      arg1='hello')
        self.assertEqual(ctr.format(), 'hello 1')

        ctr.update(arg1='goodbye')
        self.assertEqual(ctr.format(), 'goodbye 2')

    def test_kwarg_fields_precedence(self):
        """
        Keyword arguments take precedence over fields
        """

        bar_format = u'{arg1:s} {count:d}'
        additional_fields = {'arg1': 'hello'}

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      fields=additional_fields)

        self.assertEqual(ctr.format(), 'hello 1')

        ctr.update(arg1='goodbye')
        self.assertEqual(ctr.format(), 'goodbye 2')

    def test_fill_setter(self):
        """Fill must be one printable character"""

        ctr = Counter(stream=self.tty.stdout, fill='a')

        with self.assertRaisesRegex(ValueError, 'fill character must be a length of 1'):
            ctr.fill = 'hello'

        with self.assertRaisesRegex(ValueError, 'fill character must be a length of 1'):
            ctr.fill = ''

    def test_fill(self):
        """
        Fill uses remaining space
        """

        ctr_format = u'{fill}HI'
        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format, fill=u'-')
        self.assertEqual(ctr.format(), u'-' * 78 + 'HI')

        ctr_format = u'{fill}HI{fill}'
        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format, fill=u'-')
        self.assertEqual(ctr.format(), u'-' * 39 + 'HI' + u'-' * 39)

    @unittest.skipIf(PY2, 'Skip warnings tests in Python 2')
    def test_reserved_fields(self):
        """
        When reserved fields are used, a warning is raised
        """

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, fields={'elapsed': 'reserved'})
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, fields={'elapsed': 'reserved'})
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, elapsed='reserved')
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, elapsed='reserved')
        with self.assertWarns(EnlightenWarning) as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

    def test_builtin_bar_fields(self):
        """
        Ensure all built-in fields are populated as expected
        """

        bar_fields = tuple(field for field in enlighten._counter.RESERVED_FIELDS if field != 'fill')
        bar_format = u', '.join(u'%s: {%s}' % (field, field) for field in sorted(bar_fields))

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=bar_format,
                      unit='parsecs', desc='Kessel runs')

        ctr.count = 50
        fields = 'bar: , count: 50, desc: Kessel runs, desc_pad:  , elapsed: 00:50, eta: 00:50, ' \
                 'interval: 1.0, len_total: 3, percentage: 50.0, rate: 1.0, total: 100, ' \
                 'unit: parsecs, unit_pad:  '
        self.assertEqual(ctr.format(elapsed=50, width=80), fields)
