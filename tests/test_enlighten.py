# -*- coding: utf-8 -*-
# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test script for enlighten
"""

from contextlib import contextmanager
import fcntl
import os
import pty
import time
import signal
import struct
import sys
import termios

import enlighten

# pylint: disable=import-error

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest  # pylint: disable=wrong-import-order

if sys.version_info[:2] < (3, 3):
    import mock
else:
    import unittest.mock as mock  # noqa: F401  # pylint: disable=no-name-in-module

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

# pylint: enable=import-error

ENVIRON = os.environ.copy()
OUTPUT = StringIO()

# pylint: disable=missing-docstring, protected-access, too-many-lines, too-many-public-methods


# Helpers for tests

class TestCase(unittest.TestCase):
    """
    Subclass of :py:class:`unittest.TestCase` for customization
    """
    pass


# Fix deprecated methods for EL6
def assert_regex(self, text, regex, msg=None):
    """
    Wrapper for assertRegexpMatches
    """

    return self.assertRegexpMatches(text, regex, msg)


def assert_not_regex(self, text, regex, msg=None):
    """
    Wrapper for assertNotRegexpMatches
    """

    return self.assertNotRegexpMatches(text, regex, msg)


def assert_raises_regex(self, exception, regex, *args, **kwargs):
    """
    Wrapper for assertRaisesRegexp
    """

    return self.assertRaisesRegexp(exception, regex, *args, **kwargs)


if not hasattr(TestCase, 'assertRegex'):
    TestCase.assertRegex = assert_regex

if not hasattr(TestCase, 'assertNotRegex'):
    TestCase.assertNotRegex = assert_not_regex

if not hasattr(TestCase, 'assertRaisesRegex'):
    TestCase.assertRaisesRegex = assert_raises_regex


@contextmanager
def redirect_output(stream, target):
    """
    Temporary redirector for stdout and stderr
    """

    original = getattr(sys, stream)
    try:
        setattr(sys, stream, target)
        yield
    finally:
        setattr(sys, stream, original)


class MockTTY(object):

    def __init__(self, height=25, width=80):

        self.master, self.slave = pty.openpty()

        if sys.version_info[0] < 3:
            self.stdout = os.fdopen(self.slave, 'w', 1)
            self.stdread = os.fdopen(self.master, 'r')
        else:
            self.stdout = os.fdopen(self.slave, 'w', 1, newline='\n')  # line buffering for pypy2
            self.stdread = os.fdopen(self.master, 'r', newline='\n')

        # Make sure linefeed behavior is consistent between Python 2 and Python 3
        termattrs = termios.tcgetattr(self.slave)
        termattrs[1] = termattrs[1] & ~termios.ONLCR & ~termios.OCRNL
        termattrs[0] = termattrs[0] & ~termios.ICRNL
        termios.tcsetattr(self.slave, termios.TCSADRAIN, termattrs)

        self.resize(height, width)

    def flush(self):
        self.stdout.flush()

    def close(self):
        self.stdout.flush()
        self.stdout.close()
        self.stdread.close()

    def resize(self, height, width):
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack('hhhh', height, width, 0, 0))


class MockCounter(enlighten.Counter):

    __slots__ = ('output', 'calls')

    def __init__(self, *args, **kwargs):
        super(MockCounter, self).__init__(*args, **kwargs)
        self.output = []
        self.calls = []

    def refresh(self, flush=True, elapsed=None):
        self.output.append(self.count)
        self.calls.append('refresh(flush=%s, elapsed=%s)' % (flush, elapsed))

    def clear(self, flush=True):
        self.calls.append('clear(flush=%s)' % flush)


class MockManager(enlighten.Manager):
    # pylint: disable=super-init-not-called
    def __init__(self, counter_class=enlighten.Counter, **kwargs):
        super(MockManager, self).__init__(counter_class=counter_class, **kwargs)
        self.width = 80
        self.output = []

    def write(self, output='', flush=True, position=0):
        self.output.append('write(output=%s, flush=%s, position=%s)' % (output, flush, position))


def mockhw(*args):
    for item in args:
        yield item


# Begin tests

class TestFormatTime(TestCase):
    """
    Test cases for :py:func:`_format_time`
    """

    def test_seconds(self):

        self.assertEqual(enlighten._format_time(0), '00:00')
        self.assertEqual(enlighten._format_time(6), '00:06')
        self.assertEqual(enlighten._format_time(42), '00:42')

    def test_minutes(self):

        self.assertEqual(enlighten._format_time(60), '01:00')
        self.assertEqual(enlighten._format_time(128), '02:08')
        self.assertEqual(enlighten._format_time(1684), '28:04')

    def test_hours(self):

        self.assertEqual(enlighten._format_time(3600), '1h 00:00')
        self.assertEqual(enlighten._format_time(43980), '12h 13:00')
        self.assertEqual(enlighten._format_time(43998), '12h 13:18')

    def test_days(self):

        self.assertEqual(enlighten._format_time(86400), '1d 0h 00:00')
        self.assertEqual(enlighten._format_time(1447597), '16d 18h 06:37')


class TestTerminal(TestCase):
    """
    This is hard to test, so, for most tests, we'll just
    make sure the codes get passed through a tty
    """

    def setUp(self):
        os.environ['TERM'] = 'vt100'
        self.tty = MockTTY()
        self.terminal = enlighten.Terminal(stream=self.tty.stdout, kind='vt100')

    def tearDown(self):
        self.tty.close()
        if 'TERM' in ENVIRON:
            os.environ['TERM'] = ENVIRON['TERM']
        else:
            del os.environ['TERM']

    def test_caching(self):
        """
        Make sure cached values are held.
        Return values aren't accurate for blessed, but are sufficient for this test
        """

        with mock.patch('enlighten._Terminal._height_and_width', return_value=(1, 2)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))

        with mock.patch('enlighten._Terminal._height_and_width', return_value=(5, 6)):
            self.assertEqual(self.terminal._height_and_width(), (1, 2))
            self.terminal.clear_cache()
            self.assertEqual(self.terminal._height_and_width(), (5, 6))

    def test_feed(self):

        self.terminal.feed()
        self.assertEqual(self.tty.stdread.readline(), self.terminal.cud1)

    def test_change_scroll(self):

        self.terminal.change_scroll(4)
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         self.terminal.hide_cursor + self.terminal.csr(0, 4) +
                         self.terminal.move(4, 0) + 'X\n')

    def test_move_to(self):

        self.terminal.move_to(5, 10)
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         self.terminal.move(10, 5) + 'X\n')


class TestCounter(TestCase):

    def setUp(self):
        os.environ['TERM'] = 'vt100'
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)
        self.ctr = enlighten.Counter(total=10, desc='Test', unit='ticks', manager=self.manager)
        self.manager.counters[self.ctr] = 3
        self.output = r'Test   0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00 ticks/s\]'

    def tearDown(self):
        self.tty.close()
        if 'TERM' in ENVIRON:
            os.environ['TERM'] = ENVIRON['TERM']
        else:
            del os.environ['TERM']

    def test_increment(self):
        counter = MockCounter(total=100, min_delta=0)
        counter.update()
        self.assertEqual(counter.count, 1)
        counter.update(5)
        self.assertEqual(counter.count, 6)

    def test_enabled(self):
        counter = MockCounter(total=100, min_delta=0)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update()
        self.assertEqual(counter.output, [1, 2])
        counter.enabled = False
        counter.update()
        self.assertEqual(counter.output, [1, 2])

    def test_delta(self):
        counter = MockCounter(total=100, min_delta=0)
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
        counter = MockCounter(total=100, min_delta=0)
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.min_delta = 500
        counter.update()
        self.assertEqual(counter.output, [1])
        counter.update(force=True)
        self.assertEqual(counter.output, [1, 3])

    def test_refresh_total(self):
        counter = MockCounter(total=100, min_delta=0)
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
        ctr = enlighten.Counter()
        self.assertRegex(ctr.format(width=80), r'0 \[00:0\d, 0.00/s\]')
        ctr.count = 50
        ctr.start = time.time() - 50
        self.assertRegex(ctr.format(width=80), r'50 \[00:5\d, \d.\d\d/s\]')

        # With unit and description
        ctr = enlighten.Counter(desc='Test', unit='ticks')
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

        ctr = enlighten.Counter(total=10, desc='Test', unit='ticks')
        ctr.count = 50
        ctr.start = time.time() - 50
        rtn = ctr.format(width=80)
        self.assertEqual(len(rtn), 80)
        self.assertRegex(rtn, r'Test 50 ticks \[00:5\d, \d.\d\d ticks/s\]')

    def test_no_count(self):
        """
        Test for an empty counter
        """

        ctr = enlighten.Counter(total=10, desc='Test', unit='ticks')
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test   0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00 ticks/s\]')

        # No unit, no description
        ctr = enlighten.Counter(total=10)
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'  0%\|[ ]+ \|  0/10 \[00:0\d<\?, 0.00/s\]')

    def test_full_bar(self):

        ctr = enlighten.Counter(total=10, desc='Test', unit='ticks')
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

        ctr = enlighten.Counter(total=0, desc='Test', unit='ticks')
        formatted = ctr.format(width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test 100%\|' u'█+' + r'\| 0/0 \[00:0\d<00:00, 0.00 ticks/s\]')

    def test_partial_bar(self):

        ctr = enlighten.Counter(total=100, desc='Test', unit='ticks')
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
        ctr = enlighten.Counter(total=100, desc='Test', unit='ticks', series=[' ', '>', '-'])
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

        ctr = enlighten.Counter(total=100, desc='Test', unit='ticks', series=[u'⭘', u'⬤'])
        ctr.count = 50
        formatted = ctr.format(elapsed=50, width=80)
        self.assertEqual(len(formatted), 80)
        self.assertRegex(formatted, r'Test  50%\|' + u'⬤+⭘+' +
                         r'\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]')

    def test_direct(self):
        ctr = enlighten.Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks')
        self.assertIsInstance(ctr.manager, enlighten.Manager)
        ctr.start = time.time() - 50
        ctr.update(50, force=True)

        self.tty.stdout.write('X\n')
        value = self.tty.stdread.readline()
        if enlighten.NEEDS_UNICODE_HELP:
            value = value.decode('utf-8')

        self.assertRegex(value, r'Test  50%\|' + u'█+[▏▎▍▌▋▊▉]?' +
                         r'[ ]+\|  50/100 \[00:5\d<00:5\d, \d.\d\d ticks/s\]X\n')

        with mock.patch.object(self.tty, 'stdout', wraps=self.tty.stdout) as mockstdout:
            ctr = enlighten.Counter(stream=self.tty.stdout, total=100, desc='Test', unit='ticks')
            ctr.refresh(flush=False)
            self.assertFalse(mockstdout.flush.called)
            ctr.refresh(flush=True)
            self.assertTrue(mockstdout.flush.called)

    def test_floats(self):
        """
        Using floats for total and count is supported by the logic, but not by the
        default format strings
        """

        ctr = enlighten.Counter(total=100.2, desc='Test', unit='ticks', min_delta=500)
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
        mgr = enlighten.Manager(stream=self.tty.stdout, enabled=False)
        with mgr.counter(total=10, leave=False) as ctr:
            self.assertTrue(ctr in mgr.counters)
            ctr.update()

        self.assertFalse(ctr in mgr.counters)


class TestManager(TestCase):

    def setUp(self):
        os.environ['TERM'] = 'vt100'
        self.tty = MockTTY()
        self.resize_sig = signal.getsignal(signal.SIGWINCH)

    def tearDown(self):
        self.tty.close()
        signal.signal(signal.SIGWINCH, self.resize_sig)

        if 'TERM' in ENVIRON:
            os.environ['TERM'] = ENVIRON['TERM']
        else:
            del os.environ['TERM']

    def test_init(self):

        # Companion stream is stderr if stream is stdout
        manager = enlighten.Manager()
        self.assertIs(manager.stream, sys.__stdout__)
        self.assertIs(manager.term.stream, sys.__stdout__)
        # This will fail building rpm packages since stderr is redirected
        if sys.__stderr__.isatty():
            self.assertIs(manager.companion_stream, sys.__stderr__)
            self.assertIs(manager.companion_term.stream, sys.__stderr__)

        # Hard-coded companion stream always wins
        manager = enlighten.Manager(companion_stream=OUTPUT)
        self.assertIs(manager.companion_stream, OUTPUT)
        self.assertIs(manager.companion_term.stream, OUTPUT)

        # Companion stream is stdout if stream is stderr
        manager = enlighten.Manager(stream=sys.__stderr__)
        self.assertIs(manager.stream, sys.__stderr__)
        self.assertIs(manager.term.stream, sys.__stderr__)
        # This will fail building rpm packages since stderr is redirected
        if sys.__stdout__.isatty():
            self.assertIs(manager.companion_stream, sys.__stdout__)
            self.assertIs(manager.companion_term.stream, sys.__stdout__)

        # If stdout is redirected, but stderr is still a tty, use it for companion
        with redirect_output('stdout', OUTPUT):
            manager = enlighten.Manager()
            self.assertIs(manager.stream, sys.stdout)
            self.assertIs(manager.term.stream, sys.stdout)
            # This will fail building rpm packages since stderr is redirected
            if sys.__stderr__.isatty():
                self.assertIs(manager.companion_stream, sys.stderr)
                self.assertIs(manager.companion_term.stream, sys.stderr)

        # If stderr is redirected, but stdout is still a tty, use it for companion
        with redirect_output('stderr', OUTPUT):
            manager = enlighten.Manager(stream=sys.stderr)
            self.assertIs(manager.stream, sys.stderr)
            self.assertIs(manager.term.stream, sys.stderr)
            # This will fail building rpm packages since stderr is redirected
            if sys.__stdout__.isatty():
                self.assertIs(manager.companion_stream, sys.stdout)
                self.assertIs(manager.companion_term.stream, sys.stdout)

        # Hard-coded companion stream always wins
        manager = enlighten.Manager(stream=sys.__stderr__, companion_stream=OUTPUT)
        self.assertIs(manager.companion_stream, OUTPUT)
        self.assertIs(manager.companion_term.stream, OUTPUT)

        # Nonstandard stream doesn't get a companion stream by default
        manager = enlighten.Manager(stream=OUTPUT)
        self.assertIs(manager.stream, OUTPUT)
        self.assertIs(manager.term.stream, OUTPUT)
        self.assertIsNone(manager.companion_stream)
        self.assertIsNone(manager.companion_term)

    def test_counter_and_remove(self):
        # pylint: disable=no-member,assigning-non-slot
        manager = enlighten.Manager(counter_class=MockCounter)
        self.assertEqual(len(manager.counters), 0)

        with mock.patch.object(manager, '_set_scroll_area') as ssa:
            counter1 = manager.counter(leave=True)
        self.assertTrue(counter1.leave)
        self.assertEqual(len(manager.counters), 1)
        self.assertEqual(manager.counters[counter1], 1)
        self.assertEqual(counter1.calls, [])
        self.assertEqual(ssa.call_count, 1)

        with mock.patch.object(manager, '_set_scroll_area') as ssa:
            counter2 = manager.counter(leave=False)
        self.assertFalse(counter2.leave)
        self.assertEqual(len(manager.counters), 2)
        self.assertEqual(manager.counters[counter1], 2)
        self.assertEqual(manager.counters[counter2], 1)
        self.assertEqual(counter1.calls,
                         ['clear(flush=False)', 'refresh(flush=False, elapsed=None)'])
        self.assertEqual(counter2.calls, [])
        self.assertEqual(ssa.call_count, 1)
        counter1.calls = []

        with mock.patch.object(manager, '_set_scroll_area') as ssa:
            counter3 = manager.counter(leave=False)
        self.assertFalse(counter3.leave)
        self.assertEqual(len(manager.counters), 3)
        self.assertEqual(manager.counters[counter1], 3)
        self.assertEqual(manager.counters[counter2], 2)
        self.assertEqual(manager.counters[counter3], 1)
        self.assertEqual(counter1.calls,
                         ['clear(flush=False)', 'refresh(flush=False, elapsed=None)'])
        self.assertEqual(counter2.calls,
                         ['clear(flush=False)', 'refresh(flush=False, elapsed=None)'])
        self.assertEqual(counter3.calls, [])
        self.assertEqual(ssa.call_count, 1)
        counter1.calls = []
        counter2.calls = []

        manager.remove(counter3)
        self.assertEqual(len(manager.counters), 2)
        self.assertFalse(counter3 in manager.counters)

        manager.remove(counter1)
        self.assertEqual(len(manager.counters), 2)
        self.assertTrue(counter1 in manager.counters)

        with mock.patch.object(manager, '_set_scroll_area') as ssa:
            counter4 = manager.counter(leave=False)
        self.assertFalse(counter4.leave)
        self.assertEqual(len(manager.counters), 3)
        self.assertEqual(manager.counters[counter1], 3)
        self.assertEqual(manager.counters[counter2], 2)
        self.assertEqual(manager.counters[counter4], 1)
        self.assertEqual(counter1.calls, [])
        self.assertEqual(counter2.calls, [])
        self.assertEqual(counter4.calls, [])
        self.assertEqual(ssa.call_count, 1)

    def test_counter_position(self):
        manager = enlighten.Manager(stream=self.tty.stdout, set_scroll=False)
        counter1 = manager.counter(position=4)
        self.assertEqual(manager.counters[counter1], 4)

        with self.assertRaisesRegex(ValueError, 'Counter position 4 is already occupied'):
            manager.counter(position=4)

        with self.assertRaisesRegex(ValueError,
                                    'Counter position 200 is greater than terminal height'):
            manager.counter(position=200)

    def test_inherit_kwargs(self):
        manager = enlighten.Manager(counter_class=MockCounter,
                                    unit='knights', not_real=True, desc='Default')

        self.assertTrue('unit' in manager.defaults)
        self.assertTrue('desc' in manager.defaults)
        self.assertTrue('not_real' in manager.defaults)

        with mock.patch.object(manager, '_set_scroll_area'):
            ctr = manager.counter(desc='Huzzah')

        self.assertEqual(ctr.unit, 'knights')
        self.assertEqual(ctr.desc, 'Huzzah')
        self.assertFalse(hasattr(ctr, 'not_real'))

    def test_write(self):
        msg = 'test message'

        with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
            manager = enlighten.Manager(stream=self.tty.stdout)
            term = manager.term
            manager.write(msg, position=3)

        self.tty.stdout.write('X\n')
        # Carriage return is getting converted to newline
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(22, 0) + '\r' + term.clear_eol + msg + 'X\n')
        self.assertEqual(ssa.call_count, 1)

    def test_write_no_flush(self):
        """
        No real difference in our tests because stream is flushed on each new line
        If we don't flush, reading will just hang

        But we added this for coverage and as a framework future tests
        """

        msg = 'test message'

        with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
            manager = enlighten.Manager(stream=self.tty.stdout)
            term = manager.term
            manager.write(msg, position=3, flush=False)

        self.tty.stdout.write('X\n')
        # Carriage return is getting converted to newline
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(22, 0) + '\r' + term.clear_eol + msg + 'X\n')
        self.assertEqual(ssa.call_count, 1)

    def test_set_scroll_area_disabled(self):
        manager = enlighten.Manager(stream=self.tty.stdout,
                                    counter_class=MockCounter, set_scroll=False)
        manager.counters['dummy'] = 3

        manager._set_scroll_area()
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

    def test_set_scroll_area_no_change(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        manager.scroll_offset = 4

        manager._set_scroll_area()
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(), manager.term.move(21, 0) + 'X\n')

    def test_set_scroll_area_companion(self):
        """
        Ensure when no change is made, a term.move is still called for the companion stream
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    companion_stream=self.tty.stdout)
        manager.counters['dummy'] = 3
        manager.scroll_offset = 4
        term = manager.term

        manager._set_scroll_area()
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(21, 0) + term.move(21, 0) + 'X\n')

    def test_set_scroll_area(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        term = manager.term
        stdread = self.tty.stdread
        self.assertEqual(manager.scroll_offset, 1)
        self.assertFalse(manager.process_exit)
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), manager._resize_handler)

        with mock.patch('enlighten.atexit') as atexit:
            with mock.patch.object(term, 'change_scroll'):
                manager._set_scroll_area()
                self.assertEqual(term.change_scroll.call_count, 1)  # pylint: disable=no-member

            self.assertEqual(manager.scroll_offset, 4)
            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._resize_handler)

            self.assertEqual(stdread.readline(), term.move(24, 0) + '\n')
            self.assertEqual(stdread.readline(), '\n')
            self.assertEqual(stdread.readline(), '\n')

            self.assertTrue(manager.process_exit)

            atexit.register.assert_called_with(manager._at_exit)

        self.tty.stdout.write('X\n')
        self.assertEqual(stdread.readline(), term.move(21, 0) + 'X\n')

        # Run it again and make sure exit handling isn't reset
        with mock.patch('enlighten.atexit') as atexit:
            with mock.patch.object(term, 'change_scroll'):
                manager._set_scroll_area(force=True)
                self.assertEqual(term.change_scroll.call_count, 1)  # pylint: disable=no-member

            self.assertFalse(atexit.register.called)

    def test_set_scroll_area_height(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        manager.scroll_offset = 4
        manager.height = 20
        term = manager.term

        with mock.patch('enlighten.atexit') as atexit:
            with mock.patch.object(term, 'change_scroll'):
                manager._set_scroll_area()
                self.assertEqual(term.change_scroll.call_count, 1)  # pylint: disable=no-member

            self.assertEqual(manager.scroll_offset, 4)
            self.assertEqual(manager.height, 25)
            self.assertTrue(manager.process_exit)

            term.stream.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(21, 0) + 'X\n')
            atexit.register.assert_called_with(manager._at_exit)

    def test_at_exit(self):

        tty = MockTTY()

        with mock.patch('enlighten.Terminal.reset') as reset:
            manager = enlighten.Manager(stream=tty.stdout, counter_class=MockCounter)
            term = manager.term

            # process_exit is False
            manager._at_exit()
            self.assertFalse(reset.called)
            # No output
            tty.stdout.write('X\n')
            self.assertEqual(tty.stdread.readline(), 'X\n')

            # process_exit is True, set_scroll False
            manager.process_exit = True
            manager.set_scroll = False
            manager._at_exit()
            self.assertFalse(reset.called)
            self.assertEqual(tty.stdread.readline(), term.move(25, 0) + term.cud1)

            # process_exit is True, set_scroll True
            manager.set_scroll = True
            manager._at_exit()
            self.assertEqual(reset.call_count, 1)
            self.assertEqual(tty.stdread.readline(), term.cud1)

            tty.close()
            manager._at_exit()

    def test_stop(self):

        with mock.patch('enlighten.Terminal.reset') as reset:
            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4
            term = manager.term
            self.assertIsNone(manager.companion_term)

            with mock.patch('enlighten.atexit'):
                with mock.patch.object(term, 'change_scroll'):
                    manager._set_scroll_area()

            self.assertEqual(manager.scroll_offset, 5)
            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._resize_handler)
            self.assertTrue(manager.process_exit)

            # Clear stream
            self.tty.stdout.write('X\n')
            for num in range(4 + 1):  # pylint: disable=unused-variable
                self.tty.stdread.readline()

            self.assertFalse(reset.called)
            manager.enabled = False
            manager.stop()

            # No output, No changes
            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')
            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._resize_handler)
            self.assertTrue(manager.process_exit)

            manager.enabled = True
            manager.stop()

            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)
            self.assertEqual(reset.call_count, 1)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(23, 0) + term.clear_eol +
                             term.move(24, 0) + term.clear_eol + 'X\n')
            self.assertFalse(manager.process_exit)
            self.assertFalse(manager.enabled)
            for counter in manager.counters:
                self.assertFalse(counter.enabled)

    def test_stop_no_set_scroll(self):
        """
        set_scroll is False
        """

        with mock.patch('enlighten.Terminal.reset') as reset:
            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                        set_scroll=False)
            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4
            term = manager.term

            with mock.patch('enlighten.atexit'):
                with mock.patch.object(term, 'change_scroll'):
                    manager._set_scroll_area()

            self.assertEqual(manager.scroll_offset, 5)
            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._resize_handler)
            self.assertTrue(manager.process_exit)

            # Stream empty
            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')

            manager.stop()

            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)
            self.assertFalse(reset.called)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(23, 0) + term.clear_eol +
                             term.move(24, 0) + term.clear_eol + term.move(25, 0) + 'X\n')
            self.assertFalse(manager.process_exit)

    def test_stop_never_used(self):
        """
        In this case, _set_scroll_area() was never called
        """

        with mock.patch('enlighten.Terminal.reset') as reset:
            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4
            self.assertFalse(manager.process_exit)

            manager.stop()

            self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)
            self.assertEqual(reset.call_count, 1)

        # No output
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

    def test_stop_companion(self):
        """
        In this case, we have a companion terminal
        Just make sure we have an extra reset
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    companion_stream=self.tty.stdout)
        manager.counters[MockCounter(manager=manager)] = 3
        manager.counters[MockCounter(manager=manager)] = 4
        term = manager.term

        with mock.patch('enlighten.atexit'):
            with mock.patch.object(term, 'change_scroll'):
                manager._set_scroll_area()

        with mock.patch.object(manager.companion_term, 'reset') as compReset:
            manager.stop()

            self.assertEqual(compReset.call_count, 1)

    def test_stop_position_1(self):
        """
        Ensure a line feed is given if there is a counter at position 1
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)

        manager.counters[MockCounter(manager=manager)] = 3
        with mock.patch.object(manager.term, 'feed') as termfeed:
            manager.stop()
            self.assertFalse(termfeed.called)

        manager.enabled = True
        manager.counters[MockCounter(manager=manager)] = 1
        with mock.patch.object(manager.term, 'feed') as termfeed:
            manager.stop()
            self.assertTrue(termfeed.called)

    def test_resize_handler(self):

        with mock.patch('enlighten._Terminal.width', new_callable=mock.PropertyMock) as mockheight:
            mockheight.side_effect = [80, 85, 87, 70, 70]

            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            counter3 = MockCounter()
            manager.counters[counter3] = 3
            manager.scroll_offset = 4
            term = manager.term

            manager.resize_lock = True
            with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
                self.assertFalse(ssa.called)

            self.assertEqual(manager.width, 80)
            self.assertTrue(manager.resize_lock)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')

            self.assertEqual(counter3.calls, [])

            manager.resize_lock = False
            mockheight.side_effect = [80, 85, 87, 70, 70]
            with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
                self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.width, 70)
            self.assertFalse(manager.resize_lock)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(19, 0) + term.clear_eos + 'X\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_resize_handler_no_change(self):

        with mock.patch('enlighten._Terminal.width', new_callable=mock.PropertyMock) as mockheight:
            mockheight.side_effect = [80, 85, 87, 80, 80]

            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            counter3 = MockCounter()
            manager.counters[counter3] = 3
            manager.scroll_offset = 4

            with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
                self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.width, 80)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_resize_handler_height_only(self):

        with mock.patch('enlighten._Terminal.height', new_callable=mock.PropertyMock) as mockheight:
            mockheight.side_effect = [25, 23, 28, 30, 30]

            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            counter3 = MockCounter()
            manager.counters[counter3] = 3
            manager.scroll_offset = 4

            with mock.patch('enlighten.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
            self.assertEqual(ssa.call_count, 1)

            # Height is set in _set_scroll_area which is mocked
            self.assertEqual(manager.height, 25)

            self.tty.stdout.write('X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_disable(self):
        mgr = enlighten.Manager(stream=self.tty.stdout, enabled=False)
        self.assertFalse(mgr.enabled)
        ctr = mgr.counter()
        self.assertIsInstance(ctr, enlighten.Counter)
        self.assertFalse(ctr.enabled)

        # Make sure this doesn't error
        ctr.update()
        ctr.update(4)
        ctr.refresh()
        ctr.close()
        ctr.leave = False
        ctr.close()

        mgr.write()
        mgr.stop()

        # No Output
        self.tty.stdout.write('X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

    def test_context_manager(self):

        mgr = None

        with enlighten.Manager(stream=self.tty.stdout) as manager:
            self.assertIsInstance(manager, enlighten.Manager)
            self.assertTrue(manager.enabled)
            mgr = manager

        self.assertFalse(mgr.enabled)

    def test_no_resize_signal(self):

        # Test normal case initialization
        stdmgr = enlighten.Manager(stream=self.tty.stdout)
        self.assertTrue(hasattr(stdmgr, 'sigwinch_orig'))
        stdmgr.counters[MockCounter(manager=stdmgr)] = 3
        stdmgr.counters[MockCounter(manager=stdmgr)] = 4

        # Test no resize signal initialization
        with mock.patch.object(enlighten, 'RESIZE_SUPPORTED', False):
            manager = enlighten.Manager(stream=self.tty.stdout)
            self.assertFalse(hasattr(manager, 'sigwinch_orig'))

            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4

        # Test set_scroll_area()
        with mock.patch.object(enlighten.signal, 'signal',
                               wraps=enlighten.signal.signal) as mocksignal:
            with mock.patch('enlighten.atexit'):

                # Test no resize signal set_scroll_area
                with mock.patch.object(enlighten, 'RESIZE_SUPPORTED', False):
                    with mock.patch.object(manager.term, 'change_scroll'):
                        manager._set_scroll_area()

                self.assertFalse(mocksignal.called)

                # Test normal case set_scroll_area
                with mock.patch.object(stdmgr.term, 'change_scroll'):
                    stdmgr._set_scroll_area()
                self.assertTrue(mocksignal.called)

        # Test stop()
        with mock.patch.object(enlighten.signal, 'signal',
                               wraps=enlighten.signal.signal) as mocksignal:

            with mock.patch('enlighten.Terminal.reset'):

                # Test no resize signal stop
                with mock.patch.object(enlighten, 'RESIZE_SUPPORTED', False):
                    manager.stop()
                self.assertFalse(mocksignal.called)

                # Test normal case stop
                stdmgr.stop()
                self.assertTrue(mocksignal.called)


class TestGetManager(TestCase):

    def setUp(self):
        os.environ['TERM'] = 'vt100'
        self.tty = MockTTY()

    def tearDown(self):
        self.tty.close()
        if 'TERM' in ENVIRON:
            os.environ['TERM'] = ENVIRON['TERM']
        else:
            del os.environ['TERM']

    def test_get_manager(self):

        # stdout is attached to a tty
        with redirect_output('stdout', self.tty.stdout):
            self.assertTrue(sys.stdout.isatty())
            manager = enlighten.get_manager(unit='knights')
            self.assertIsInstance(manager, enlighten.Manager)
            self.assertTrue('unit' in manager.defaults)

        # stdout is not attached to a tty
        with redirect_output('stdout', OUTPUT):
            self.assertFalse(sys.stdout.isatty())
            manager = enlighten.get_manager(unit='knights')
            self.assertIsInstance(manager, enlighten.Manager)
            self.assertTrue('unit' in manager.defaults)
