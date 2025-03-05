# -*- coding: utf-8 -*-
# Copyright 2017 - 2025 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for subcounter operations
"""

import time

from enlighten._counter import Counter, SubCounter, SERIES_STD

from tests import TestCase, mock, MockManager, MockTTY


# pylint: disable=protected-access


BLOCK = SERIES_STD[-1]


class CounterSubclass(Counter):
    """
    Subclass of Counter to support mocking
    """


class TestSubCounter(TestCase):
    """
    Test the BaseCounter class
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)
        self.parent = CounterSubclass(total=10, desc='Test', unit='ticks', manager=self.manager)

    def tearDown(self):
        self.tty.close()

    def test_init(self):
        """
        Ensure initial values are set
        """

        counter = SubCounter(self.parent)
        self.assertIsNone(counter.color)
        self.assertEqual(counter.count, 0)
        self.assertFalse(counter.all_fields)
        self.assertIs(counter.parent, self.parent)
        self.assertIs(counter.manager, self.manager)

        self.parent.count = 4
        counter = SubCounter(self.parent, color='green',
                                                count=4, all_fields=True)
        self.assertEqual(counter.color, 'green')
        self.assertEqual(counter.count, 4)
        self.assertTrue(counter.all_fields)

        with self.assertRaisesRegex(ValueError, 'Invalid count: 6'):
            counter = SubCounter(self.parent, count=6)

    def test_update(self):
        """
        Increment and update parent
        """

        counter = SubCounter(self.parent)
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
        """
        Must be peer or parent
        """

        counter = SubCounter(self.parent)

        notparent = Counter(manager=self.manager)
        with self.assertRaisesRegex(ValueError, 'source must be parent or peer'):
            counter.update_from(notparent)

        notpeer = SubCounter(notparent)
        with self.assertRaisesRegex(ValueError, 'source must be parent or peer'):
            counter.update_from(notpeer)

    def test_update_from_invalid_incr(self):
        """
        Increment can't make source negative
        """

        counter = SubCounter(self.parent)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 1'):
            counter.update_from(self.parent)

        self.parent.count = 4
        peer = SubCounter(self.parent, count=3)
        self.parent._subcounters.append(peer)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 4'):
            counter.update_from(peer, 4)

        with self.assertRaisesRegex(ValueError, 'Invalid increment: 2'):
            counter.update_from(self.parent, 2)

    def test_update_from_parent(self):
        """
        subcounter should gain increment, parent should remain unchanged
        """

        counter = SubCounter(self.parent)
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

        counter = SubCounter(self.parent)
        self.parent.count = 6
        peer = SubCounter(self.parent, count=4)

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


class TestCounterSubCounter(TestCase):
    """
    Subcounter operations in the Counter class
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)
        self.ctr = Counter(total=10, desc='Test', unit='ticks', manager=self.manager)
        self.manager.counters[self.ctr] = 3

    def tearDown(self):
        self.tty.close()

    def test_repr_subcounter(self):
        """
        Representation format for SubCounter
        """

        self.ctr.count = 2
        subcounter = self.ctr.add_subcounter('green', count=1)
        self.assertEqual(repr(subcounter), "SubCounter(count=1, color='green', all_fields=False)")

    def test_add_subcounter(self):
        """
        Add a subcounter to parent counter
        """

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

    def test_get_subcounter(self):
        """
        Get fields for subcounters in bar format
        """

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
        """
        Get fields for subcounters in counter format (count exceeds total)
        """

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

    def test_subcounter(self):
        """
        When subcounter is present, bar will be drawn in multiple colors
        """

        ctr = self.manager.counter(stream=self.tty.stdout, total=100, bar_format=u'{bar}')
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

        ctr = Counter(stream=self.tty.stdout, total=100, count=50, manager=self.manager)
        ctr.add_subcounter('yellow')
        ctr.add_subcounter('blue', count=10)

        ctr.bar_format = u'{count_3}'
        with self.assertRaisesRegex(ValueError, 'subcounter 3 is not defined'):
            ctr.format(elapsed=5, width=80)

        for fmt in (u'{rate_1}', u'{eta_1}', u'{interval_1}'):
            ctr.bar_format = fmt
            with self.assertRaisesRegex(ValueError, "'all_fields' not specified for subcounter"):
                ctr.format(elapsed=5, width=80)

        ctr = Counter(stream=self.tty.stdout, total=100, count=50, manager=self.manager)
        for fmt in (u'{count_0}', u'{rate_0}', u'{percentage_0}',
                    u'{count_00}', u'{rate_00}', u'{percentage_00}'):
            ctr.bar_format = fmt
            with self.assertRaisesRegex(ValueError, 'no subcounters are configured'):
                ctr.format(elapsed=5, width=80)

        # Counter fields
        ctr = Counter(stream=self.tty.stdout, count=50, manager=self.manager)
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
        ctr = self.manager.counter(stream=self.tty.stdout, total=100, counter_format=counter_format)

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

        ctr = self.manager.counter(stream=self.tty.stdout, total=100, bar_format=u'{bar}')
        term = ctr.manager.term
        ctr.count = 50
        ctr.add_subcounter('yellow', count=44)
        ctr.add_subcounter('blue', count=4)
        ctr.add_subcounter('red', count=2)

        formatted = ctr.format(width=80)
        bartext = term.red(BLOCK) + term.blue(BLOCK*3) + term.yellow(BLOCK*35) + ' ' * 41
        self.assertEqual(formatted, bartext)

    def test_subcounter_rounding(self):
        """
        Extend subcounters to account for remainders when count reaches total
        """

        ctr = self.manager.counter(stream=self.tty.stdout, total=300, bar_format=u'{bar}')
        term = ctr.manager.term
        ctr.count = 151
        sub1 = ctr.add_subcounter('yellow', count=132)
        sub2 = ctr.add_subcounter('blue', count=12)
        sub3 = ctr.add_subcounter('red', count=7)

        formatted = ctr.format(width=80)
        bartext = term.red(BLOCK) + term.blue(BLOCK * 3) + term.yellow(BLOCK * 35) + ' ' * 41
        self.assertEqual(formatted, bartext)

        # Bar complete
        ctr.count = 300
        sub1.count = 262
        sub2.count = 24
        sub3.count = 14

        formatted = ctr.format(width=80)
        bartext = term.red(BLOCK * 4) + term.blue(BLOCK * 6) + term.yellow(BLOCK * 70)
        self.assertEqual(formatted, bartext)

    def test_subcounter_rounding_with_main(self):
        """
        Extend subcounters and main counter to account for remainders when count reaches total
        """

        ctr = self.manager.counter(stream=self.tty.stdout, total=300, bar_format=u'{bar}')
        term = ctr.manager.term
        ctr.count = 151
        sub1 = ctr.add_subcounter('yellow', count=132)
        sub2 = ctr.add_subcounter('blue', count=12)

        formatted = ctr.format(width=80)
        bartext = term.blue(BLOCK * 3) + term.yellow(BLOCK * 35) + BLOCK + ' ' * 41
        self.assertEqual(formatted, bartext)

        # Bar complete
        ctr.count = 300
        sub1.count = 262
        sub2.count = 24

        formatted = ctr.format(width=80)
        bartext = term.blue(BLOCK * 6) + term.yellow(BLOCK * 70) + BLOCK * 4
        self.assertEqual(formatted, bartext)

    def test_subcounter_prefixed(self):
        """
        Subcounter float fields should support prefixed formatting
        """

        bar_format = (u'{count:!.2j}B / {total:!.2j}B | {rate:!.2j}B/s | {interval:!.2j}s/B'
                      u' | {count_0:!.2j}B | {count_00:!.2j}B'
                      u' | {count_1:!.2j}B | {rate_1:!.2j}B/s | {interval_1:!.2j}s/B'
                      u' | {count_2:!.2j}B | {rate_2:!.2j}B/s | {interval_2:!.2j}s/B'
                      u' | {count_3:!.2j}B | {rate_3:!.2j}B/s | {interval_3:!.2j}s/B'
                      )
        ctr = self.manager.counter(stream=self.tty.stdout, total=3.2 * 2 ** 20,
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

    def test_reset(self):
        """Subcounters can be reset"""

        ctr = self.ctr
        ctr.start_count = 2
        ctr.count = 9
        ctr.start -= 5.0
        ctr._count_updated = ctr.start + 3.0

        subcounter = ctr.add_subcounter('green', count=1)
        subcounter.count = 5

        ctr.reset()
        self.assertAlmostEqual(ctr.start, time.time(), delta=0.1)
        self.assertEqual(ctr.start, ctr._count_updated)
        self.assertEqual(ctr.start, ctr.last_update)
        self.assertEqual(ctr.count, 2)
        self.assertEqual(subcounter.count, 1)
