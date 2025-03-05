# -*- coding: utf-8 -*-
# Copyright 2017 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._counter and enlighten.counter
"""

import time

from enlighten import Counter as CounterDirect, EnlightenWarning, Manager
from enlighten._counter import Counter, RESERVED_FIELDS, SERIES_STD as _SERIES_STD

from tests import TestCase, MockManager, MockTTY, MockCounter, PY2, unittest


# pylint: disable=protected-access


SERIES_STD = u' ▏▎▍▌▋▊▉█'
BLOCK = _SERIES_STD[-1]


class TestCounter(TestCase):
    """
    Test the Counter classes
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
        """
        Representation format for Counter
        """

        self.assertEqual(repr(self.ctr), "Counter(desc='Test', total=10, count=0, unit='ticks')")

    def test_no_manager(self):
        """
        Raise an error if there is no manager specified
        """

        with self.assertRaisesRegex(TypeError, 'manager must be specified'):
            Counter()
        Counter(manager=self.manager)

    def test_increment(self):
        """
        Count increments on update
        """

        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.count, 1)
        counter.update(5)
        self.assertEqual(counter.count, 6)

    def test_enabled(self):
        """
        Does not refresh when enabled is False
        """

        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.enabled = False
        counter.update()
        self.assertEqual(counter.output, [1, 2])

    def test_delta(self):
        """
        Does not update if minimum time delta has not passed
        """

        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.min_delta = 0.01
        counter.last_update -= 0.01
        counter.update()
        self.assertEqual(counter.output, [1, 2, 4])

    def test_force(self):
        """
        Force update even if minimum time delta has not passed
        """

        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update(force=True)
        self.assertEqual(counter.output, [1, 3])

    def test_refresh_total(self):
        """
        Update when total is reached even if minimum time delta has not passed
        """

        counter = MockCounter(total=100, min_delta=0, manager=self.manager)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update(98)
        self.assertEqual(counter.output, [1, 100])

    def test_position(self):
        """
        Position is returned from manager
        """

        self.assertEqual(self.ctr.position, 3)

    def test_elapsed(self):
        """
        Elapsed property
        """

        ctr = self.ctr
        ctr.start -= 5.0
        ctr._count_updated = ctr.start + 3.0

        self.assertEqual(int(ctr.elapsed), 5)

        # Uses last time count was updated when closed
        ctr.close()
        self.assertEqual(int(ctr.elapsed), 3)

        # Used last time count was updated when count equals total
        ctr._closed = 0.0
        ctr.count = ctr.total
        self.assertEqual(int(ctr.elapsed), 5)

    def test_refresh(self):
        """
        Refresh counter if enabled
        """

        self.ctr.last_update = 0
        self.ctr.refresh()
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=True, position=3\)' % self.output)
        self.assertAlmostEqual(self.ctr.last_update, self.ctr.start, delta=0.3)

        self.manager.output = []
        self.ctr.refresh(flush=False)
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=False, position=3\)' % self.output)

        self.manager.output = []
        self.ctr.enabled = False
        self.ctr.refresh()
        self.assertEqual(len(self.manager.output), 0)

    def test_clear(self):
        """
        Clear counter if enabled
        """

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

    def test_remove(self):
        """
        Counter is removed from manager on close when leave is False
        """

        self.ctr.leave = False
        self.assertTrue(self.ctr in self.manager.counters)

        self.ctr.close()
        self.assertRegex(self.manager.output[0],
                         r'write\(output=%s, flush=True, position=3\)' % self.output)
        self.assertFalse(self.ctr in self.manager.counters)

    def test_direct(self):
        """
        Use Counter directly without specifying manager
        """

        ctr = CounterDirect(stream=self.tty.stdout, total=100, desc='Test',
                            unit='ticks', series=SERIES_STD)
        self.assertIsInstance(ctr.manager, Manager)
        ctr.start -= 50.0
        ctr.update(50, force=True)

        formatted = ctr.format()
        self.assertRegex(formatted, r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

        self.assertIs(ctr.manager.stream, self.tty.stdout)

        # Uses manager that is supplied if given
        ctr = CounterDirect(total=100, manager=self.manager)
        self.assertIs(ctr.manager, self.manager)

    def test_close(self):
        """
        Counter closing behavior
        """

        manager = MockManager(stream=self.tty.stdout)

        # Clear is False
        ctr = MockCounter(manager=manager, leave=False)
        manager.counters[ctr] = 1
        ctr.close()
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove_calls, 1)

        # Manager is already closed
        del ctr.calls[:]  # Python 2.7 does not support list.clear()
        if not PY2:  # Skip warnings tests in Python 2
            with self.assertWarnsRegex(EnlightenWarning, 'already closed') as warn:
                ctr.close()
            self.assertRegex(__file__, warn.filename)
            self.assertEqual(ctr.calls, [])
            self.assertEqual(manager.remove_calls, 2)

        manager = MockManager(stream=self.tty.stdout)

        # Clear is True, leave is True
        ctr = MockCounter(manager=manager, leave=True)
        manager.counters[ctr] = 1
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['refresh(flush=True, elapsed=None)'])
        self.assertEqual(manager.remove_calls, 1)

        # Clear is True, leave is False
        ctr = MockCounter(manager=manager, leave=False)
        ctr.close(clear=True)
        self.assertEqual(ctr.calls, ['clear(flush=True)'])
        self.assertEqual(manager.remove_calls, 2)

    def test_context_manager(self):
        """
        Use counter as a context manager
        """

        mgr = Manager(stream=self.tty.stdout, enabled=False)
        with mgr.counter(total=10, leave=False) as ctr:
            self.assertTrue(ctr in mgr.counters)
            ctr.update()

        self.assertFalse(ctr in mgr.counters)

    def test_reset(self):
        """
        Counter can be reset
        """

        ctr = self.ctr
        ctr.start_count = 1
        ctr.start -= 5.0
        ctr._count_updated = ctr.start + 3.0
        ctr.count = 9

        ctr.reset()
        self.assertAlmostEqual(ctr.start, time.time(), delta=0.1)
        self.assertEqual(ctr.start, ctr._count_updated)
        self.assertEqual(ctr.start, ctr.last_update)
        self.assertEqual(ctr.count, 1)


class TestCounterFormat(TestCase):
    """
    Test the Counter classes
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)

    def tearDown(self):
        self.tty.close()

    def test_str(self):
        """
        Printing counter as string should show formatted output
        """

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test',
                      unit='ticks', series=SERIES_STD, manager=self.manager)
        ctr.start -= 50.0
        ctr.count = 50

        if PY2:
            self.assertRegex(str(ctr).decode('utf-8'), r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                             r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

        else:
            self.assertRegex(str(ctr), r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                             r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

    def test_format_no_total(self):
        """
        Counter format is used when no total is given
        """

        # No unit, No desc
        ctr = Counter(stream=self.tty.stdout, manager=self.manager)
        self.assertRegex(ctr.format(width=80), r'0 \[00:0\d, 0.00/s\]')
        ctr.count = 50
        ctr.start -= 50.0
        self.assertRegex(ctr.format(width=80), r'50 \[00:5\d, \d.\d\d/s\]')

        # With unit and description
        ctr = Counter(stream=self.tty.stdout, desc='Test', unit='ticks', manager=self.manager)
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 0 ticks \[00:0\d, 0.00 ticks/s\]')
        ctr.count = 50
        ctr.start -= 50.0
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 50 ticks \[00:5\d, \d.\d\d ticks/s\]')

    def test_format_count_gt_total(self):
        """
        Counter should fall back to no-total format if count is greater than total
        """

        ctr = Counter(
            stream=self.tty.stdout, total=10, desc='Test', unit='ticks', manager=self.manager
        )
        ctr.count = 50
        ctr.start -= 50.0
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 50 ticks \[00:5\d, \d.\d\d ticks/s\]')

    def test_no_count(self):
        """
        Test for an empty counter
        """

        ctr = Counter(
            stream=self.tty.stdout, total=10, desc='Test', unit='ticks', manager=self.manager
        )
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test   0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00 ticks/s\]')

        # No unit, no description
        ctr = Counter(stream=self.tty.stdout, total=10, manager=self.manager)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'  0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00/s\]')

    def test_full_bar(self):
        """
        Bar format when total has been reached
        """

        ctr = Counter(stream=self.tty.stdout, total=10, desc='Test',
                      unit='ticks', series=SERIES_STD, manager=self.manager)
        ctr.count = 10
        ctr.start -= 10.0
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted,
                         r'Test 100%\|' + u'█+' + r'\| 10/10 \[00:\d\d<00:00, \d.\d\d ticks/s\]')

    def test_zero_total(self):
        """
        If the total is 0, the bar should be full
        """

        ctr = self.manager.counter(stream=self.tty.stdout, total=0, desc='Test', unit='ticks',
                                   series=SERIES_STD, manager=self.manager)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test 100%\|' u'█+' + r'\| 0/0 \[00:0\d<00:00, 0.00 ticks/s\]')

    def test_auto_offset(self):
        """
        If offset is not specified, terminal codes should be automatically ignored
        when calculating bar length
        """

        bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d} ' + \
                     u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        bar_format_blue = self.manager.term.blue(bar_format)
        self.assertNotEqual(len(bar_format), len(bar_format_blue))

        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=bar_format)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        bar_len_1 = formatted1.count(BLOCK)

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=bar_format_blue)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        bar_len_2 = formatted2.count(BLOCK)

        self.assertTrue(bar_len_2 == bar_len_1)

    def test_offset(self):
        """
        Offset reduces count of printable characters when formatting
        """

        bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}|{count:{len_total}d}/{total:d} ' + \
                     u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
        bar_format = self.manager.term.blue(bar_format)

        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=bar_format, offset=0)
        formatted1 = ctr.format(width=80)
        self.assertEqual(len(formatted1), 80)
        bar_len_1 = formatted1.count(BLOCK)

        offset = len(self.manager.term.blue(''))
        ctr = self.manager.counter(total=10, desc='Test', unit='ticks',
                                   count=10, bar_format=bar_format, offset=offset)
        formatted2 = ctr.format(width=80)
        self.assertEqual(len(formatted2), 80 + offset)
        bar_len_2 = formatted2.count(BLOCK)

        self.assertTrue(bar_len_2 == bar_len_1 + offset)

        # Test in counter format
        ctr = self.manager.counter(total=10, count=50, offset=0)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)

        ctr = self.manager.counter(total=10, count=50, offset=10)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 90)

    def test_partial_bar(self):
        """
        Bar format when total has not been reached
        """

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test',
                      unit='ticks', series=SERIES_STD, manager=self.manager)
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
        """
        Specify custom series for bar formatting
        """

        ctr = Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks',
                      series=[' ', '>', '-'], manager=self.manager)
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
                      series=[u'⭘', u'⬤'], manager=self.manager)
        ctr.count = 50
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'⬤+⭘+' +
                         r'\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

    def test_floats(self):
        """
        Using floats for total and count is supported by the logic, but not by the
        default format strings
        """

        ctr = Counter(stream=self.tty.stdout, total=100.2, desc='Test',
                      unit='ticks', min_delta=500, series=SERIES_STD, manager=self.manager)
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

        bar_format = u'{count:!.2j}B / {total:!.2j}B | {rate:!.2j}B/s | {interval:!.2j}s/B'

        ctr = Counter(
            stream=self.tty.stdout, total=3.2 * 2 ** 20, bar_format=bar_format, manager=self.manager
        )
        ctr.count = 2048.0

        formatted = ctr.format(elapsed=2, width=80)
        self.assertEqual(formatted, '2.00 KiB / 3.20 MiB | 1.00 KiB/s | 0.00 s/B')

        # Counter_format
        counter_format = u'{count:!.2j}B | {rate:!.2j}B/s | {interval:!.2j}s/B'

        ctr = Counter(stream=self.tty.stdout, counter_format=counter_format, manager=self.manager)
        ctr.count = 2048.0

        formatted = ctr.format(elapsed=2, width=80)
        self.assertEqual(formatted, '2.00 KiB | 1.00 KiB/s | 0.00 s/B')

    def test_color(self):
        """
        Only bar characters should be colorized
        """

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=u'|{bar}|',
                      count=50, color='red', manager=self.manager)
        terminal = ctr.manager.term
        formatted = ctr.format(width=80)
        self.assertEqual(formatted, '|' + terminal.red(BLOCK * 39 + ' ' * 39) + '|')


class TestCounterFields(TestCase):
    """
    Test the Counter classes
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)

    def tearDown(self):
        self.tty.close()

    def test_reserve_field_unavailable(self):
        """
        Exception raised when reserved field is invalid
        """

        msg1 = "Reserve field '%s' specified in format, but unavailable for bar_format"
        msg2 = "Reserve field '%s' specified in format, but unavailable for counter_format"

        ctr = Counter(stream=self.tty.stdout, total=100, count=50, manager=self.manager)
        ctr.bar_format = u'{fill}'
        with self.assertRaisesRegex(ValueError, msg1 % 'fill'):
            ctr.format(elapsed=5, width=80)

        ctr = Counter(stream=self.tty.stdout, count=50, manager=self.manager)

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

        ctr = self.manager.counter(stream=self.tty.stdout, total=1, desc='open{', unit='dudes',
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

        ctr = self.manager.counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                                   fields={'arg1': 'hello'})
        self.assertEqual(ctr.format(), 'hello 1')

        ctr = self.manager.counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                                   fields={'arg1': 'hello'})
        self.assertEqual(ctr.format(), 'hello 1')

    def test_additional_fields_missing(self):
        """
        Raise a ValueError when a keyword is missing
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'

        ctr = Counter(
            stream=self.tty.stdout, total=10, count=1, bar_format=bar_format, manager=self.manager
        )
        with self.assertRaisesRegex(ValueError, "'arg1' specified in format, but not provided"):
            ctr.format()

        ctr = Counter(
            stream=self.tty.stdout, count=1, counter_format=ctr_format, manager=self.manager
        )
        with self.assertRaisesRegex(ValueError, "'arg1' specified in format, but not provided"):
            ctr.format()

    def test_additional_fields_changed(self):
        """
        Change additional fields
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'
        additional_fields = {'arg1': 'hello'}

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      fields=additional_fields, manager=self.manager)
        self.assertEqual(ctr.format(), 'hello 1')
        additional_fields['arg1'] = 'goodbye'
        self.assertEqual(ctr.format(), 'goodbye 1')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      fields=additional_fields, manager=self.manager)
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
                      fields=additional_fields, manager=self.manager)
        self.assertEqual(ctr.format(), 'hello 1')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      fields=additional_fields, manager=self.manager)
        self.assertEqual(ctr.format(), 'hello 1')

    def test_kwarg_fields(self):
        """
        Additional fields to format via keyword arguments
        """

        bar_format = ctr_format = u'{arg1:s} {count:d}'

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, bar_format=bar_format,
                      arg1='hello', manager=self.manager)
        self.assertEqual(ctr.format(), 'hello 1')

        ctr.update(arg1='goodbye')
        self.assertEqual(ctr.format(), 'goodbye 2')

        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format,
                      arg1='hello', manager=self.manager)
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
                      fields=additional_fields, manager=self.manager)

        self.assertEqual(ctr.format(), 'hello 1')

        ctr.update(arg1='goodbye')
        self.assertEqual(ctr.format(), 'goodbye 2')

    def test_fill_setter(self):
        """Fill must be one printable character"""

        ctr = Counter(stream=self.tty.stdout, fill='a', manager=self.manager)

        with self.assertRaisesRegex(ValueError, 'fill character must be a length of 1'):
            ctr.fill = 'hello'

        with self.assertRaisesRegex(ValueError, 'fill character must be a length of 1'):
            ctr.fill = ''

    def test_fill(self):
        """
        Fill uses remaining space
        """

        ctr_format = u'{fill}HI'
        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format, fill=u'-',
                      manager=self.manager)
        self.assertEqual(ctr.format(), u'-' * 78 + 'HI')

        ctr_format = u'{fill}HI{fill}'
        ctr = Counter(stream=self.tty.stdout, count=1, counter_format=ctr_format, fill=u'-',
                      manager=self.manager)
        self.assertEqual(ctr.format(), u'-' * 39 + 'HI' + u'-' * 39)

    @unittest.skipIf(PY2, 'Skip warnings tests in Python 2')
    def test_reserved_fields(self):
        """
        When reserved fields are used, a warning is raised
        """

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, fields={'elapsed': 'reserved'},
                      manager=self.manager)
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, fields={'elapsed': 'reserved'},
                      manager=self.manager)
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, count=1, elapsed='reserved',
                      manager=self.manager)
        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

        ctr = Counter(stream=self.tty.stdout, total=10, elapsed='reserved', manager=self.manager)
        with self.assertWarns(EnlightenWarning) as warn:
            ctr.format()
        self.assertRegex(__file__, warn.filename)

    def test_builtin_bar_fields(self):
        """
        Ensure all built-in fields are populated as expected
        """

        bar_fields = tuple(field for field in RESERVED_FIELDS if field != 'fill')
        bar_format = u', '.join(u'%s: {%s}' % (field, field) for field in sorted(bar_fields))

        ctr = Counter(stream=self.tty.stdout, total=100, bar_format=bar_format,
                      unit='parsecs', desc='Kessel runs', manager=self.manager)

        ctr.count = 50
        fields = 'bar: , count: 50, desc: Kessel runs, desc_pad:  , elapsed: 00:50, eta: 00:50, ' \
                 'interval: 1.0, len_total: 3, percentage: 50.0, rate: 1.0, total: 100, ' \
                 'unit: parsecs, unit_pad:  '
        self.assertEqual(ctr.format(elapsed=50, width=80), fields)
