# -*- coding: utf-8 -*-
# Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._manager
"""

import signal
import sys
import time

import enlighten
from enlighten import _manager

from tests import (unittest, TestCase, mock, MockTTY, MockCounter,
                   redirect_output, OUTPUT, STDOUT_NO_FD)


TERMINAL = 'blessed.Terminal'


# pylint: disable=missing-docstring, protected-access, too-many-statements, too-many-public-methods
# pylint: disable=too-many-lines

class TestManager(TestCase):

    def setUp(self):
        self.tty = MockTTY()
        self.resize_sig = signal.getsignal(signal.SIGWINCH)

    def tearDown(self):
        self.tty.close()
        signal.signal(signal.SIGWINCH, self.resize_sig)

    def test_init_safe(self):
        with redirect_output('stdout', self.tty.stdout):
            # Companion stream is stderr if stream is stdout
            manager = enlighten.Manager()
            self.assertIs(manager.stream, sys.stdout)
            self.assertIs(manager.term.stream, sys.stdout)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init(self):
        # Companion stream is __stderr__ if stream is __stdout__

        # Need to mock isatty() for some build and test environments
        with mock.patch.object(sys, '__stderr__') as mock_stderr:
            mock_stderr.isatty.return_value = True
            manager = enlighten.Manager(stream=sys.__stdout__)

        self.assertIs(manager.stream, sys.stdout)
        self.assertIs(manager.term.stream, sys.stdout)
        self.assertIs(manager.companion_stream, mock_stderr)
        self.assertIs(manager.companion_term.stream, mock_stderr)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_companion_hc(self):
        # Hard-coded companion stream always wins
        manager = enlighten.Manager(companion_stream=OUTPUT)
        self.assertIs(manager.companion_stream, OUTPUT)
        self.assertIs(manager.companion_term.stream, OUTPUT)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_stderr(self):
        # Companion stream is __stdout__ if stream is __stderr__

        # Need to mock isatty() for some build and test environments
        with mock.patch.object(sys, '__stdout__') as mock_stdout:
            mock_stdout.isatty.return_value = True
            manager = enlighten.Manager(stream=sys.__stderr__)

        self.assertIs(manager.stream, sys.__stderr__)
        self.assertIs(manager.term.stream, sys.__stderr__)
        self.assertIs(manager.companion_stream, mock_stdout)
        self.assertIs(manager.companion_term.stream, mock_stdout)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_redirect(self):
        # If stdout is redirected, but stderr is still a tty, use it for companion
        with redirect_output('stdout', OUTPUT):

            # Need to mock isatty() for some build and test environments
            with mock.patch.object(sys, 'stderr') as mock_stderr:
                mock_stderr.isatty.return_value = True
                manager = enlighten.Manager()

            self.assertIs(manager.stream, sys.stdout)
            self.assertIs(manager.term.stream, sys.stdout)
            self.assertIs(manager.companion_stream, mock_stderr)
            self.assertIs(manager.companion_term.stream, mock_stderr)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_stderr_redirect(self):
        # If stderr is redirected, but stdout is still a tty, use it for companion
        with redirect_output('stderr', OUTPUT):

            # Need to mock isatty() for some build and test environments
            with mock.patch.object(sys, 'stdout') as mock_stdout:
                mock_stdout.isatty.return_value = True
                manager = enlighten.Manager(stream=sys.stderr)

            self.assertIs(manager.stream, sys.stderr)
            self.assertIs(manager.term.stream, sys.stderr)
            self.assertIs(manager.companion_stream, mock_stdout)
            self.assertIs(manager.companion_term.stream, mock_stdout)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_stderr_companion_hc(self):

        # Hard-coded companion stream always wins
        manager = enlighten.Manager(stream=sys.__stderr__, companion_stream=OUTPUT)
        self.assertIs(manager.companion_stream, OUTPUT)
        self.assertIs(manager.companion_term.stream, OUTPUT)

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_init_hc(self):

        # Nonstandard stream doesn't get a companion stream by default
        manager = enlighten.Manager(stream=OUTPUT)
        self.assertIs(manager.stream, OUTPUT)
        self.assertIs(manager.term.stream, OUTPUT)
        self.assertIsNone(manager.companion_stream)
        self.assertIsNone(manager.companion_term)

    def test_width(self):
        """Width hard-coded"""

        manager = enlighten.Manager(width=100)
        ctr = manager.counter(total=100)

        self.assertEqual(len(ctr.format()), 100)

    def test_repr(self):
        manager = enlighten.Manager()
        self.assertEqual(repr(manager), "Manager(stream=%r)" % sys.stdout)

    def test_counter_and_remove(self):
        # pylint: disable=no-member,assigning-non-slot
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
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

        # Remove again, no error
        manager.remove(counter3)
        self.assertEqual(len(manager.counters), 2)

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

        with self.assertRaisesRegex(ValueError, 'Counter position 0 is less than 1'):
            manager.counter(position=0)

        with self.assertRaisesRegex(ValueError, 'Counter position 4 is already occupied'):
            manager.counter(position=4)

        with self.assertRaisesRegex(ValueError,
                                    'Counter position 200 is greater than terminal height'):
            manager.counter(position=200)

    def test_counter_position_pinned(self):
        """If a position is taken, use next available"""

        manager = enlighten.Manager(stream=self.tty.stdout, set_scroll=False)
        counter1 = manager.counter(position=2)
        self.assertEqual(manager.counters[counter1], 2)

        counter2 = manager.counter()
        self.assertEqual(manager.counters[counter1], 2)
        self.assertEqual(manager.counters[counter2], 1)

        counter3 = manager.counter()
        self.assertEqual(manager.counters[counter1], 2)
        self.assertEqual(manager.counters[counter2], 3)
        self.assertEqual(manager.counters[counter3], 1)

        status1 = manager.status_bar(position=3)
        self.assertEqual(manager.counters[counter1], 2)
        self.assertEqual(manager.counters[counter2], 4)
        self.assertEqual(manager.counters[counter3], 1)
        self.assertEqual(manager.counters[status1], 3)

        status2 = manager.status_bar()
        self.assertEqual(manager.counters[counter1], 2)
        self.assertEqual(manager.counters[counter2], 5)
        self.assertEqual(manager.counters[counter3], 4)
        self.assertEqual(manager.counters[status1], 3)
        self.assertEqual(manager.counters[status2], 1)

    def test_counter_replaced(self):
        """Counter replaces an existing counter"""

        manager = enlighten.Manager(stream=self.tty.stdout, set_scroll=False)

        # Pinned replacement
        counter1 = manager.counter(position=2)
        self.assertEqual(manager.counters[counter1], 2)

        counter2 = manager.counter(replace=counter1)
        self.assertEqual(len(manager.counters), 1)
        self.assertEqual(manager.counters[counter2], 2)
        self.assertTrue(counter2._pinned)

        # Unpinned replacement
        counter3 = manager.counter()
        self.assertEqual(len(manager.counters), 2)
        self.assertEqual(manager.counters[counter3], 1)

        counter4 = manager.counter(replace=counter3)
        self.assertEqual(len(manager.counters), 2)
        self.assertEqual(manager.counters[counter4], 1)
        self.assertFalse(counter4._pinned)

        # Unmanaged counter given
        with self.assertRaisesRegex(ValueError, 'Counter to replace is not currently managed'):
            manager.counter(replace=counter1)

    def test_inherit_kwargs(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
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

        with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
            manager = enlighten.Manager(stream=self.tty.stdout)
            counter = manager.counter(position=3)
            term = manager.term
            manager.write(msg, counter=counter)

        self.tty.stdout.write(u'X\n')
        # Carriage return is getting converted to newline
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(22, 0) + '\r' + term.clear_eol + msg + 'X\n')
        self.assertEqual(ssa.call_count, 2)

    def test_write_no_flush(self):
        """
        Output is stored in buffer, but not flushed to stream
        """

        msg = u'test message'

        with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
            manager = enlighten.Manager(stream=self.tty.stdout, companion_stream=OUTPUT)
            counter = manager.counter(position=3)
            term = manager.term
            manager.write(msg, counter=counter, flush=False)

        self.assertEqual(manager._buffer,
                         [term.move(term.height - 3, 0), '\r', term.clear_eol, msg])
        self.assertEqual(manager._companion_buffer, [])

        self.tty.stdout.write(u'X\n')

        # No output
        self.assertEqual(self.tty.stdread.readline(), 'X\n')
        self.assertEqual(ssa.call_count, 2)

    def test_flush_companion_buffer(self):

        """
        Output is stored in buffer, but only written in companion stream is defined
        """

        manager = enlighten.Manager(stream=self.tty.stdout)
        msg = u'test message'

        manager._companion_buffer = [msg]

        manager._flush_streams()

        # Companion buffer flushed, but not outputted
        self.assertEqual(manager._companion_buffer, [])
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

        # set companion stream and test again
        manager.companion_stream = OUTPUT
        manager._companion_buffer = [msg]
        manager._flush_streams()

        self.assertEqual(manager._companion_buffer, [])
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')
        self.assertEqual(OUTPUT.getvalue(), msg)

    def test_autorefresh(self):
        """
        Ensure auto-refreshed counters are updated when others are
        """

        manager = enlighten.Manager(stream=self.tty.stdout)
        counter1 = manager.counter(count=1, total=0, counter_format=u'counter1', autorefresh=True)
        counter2 = manager.counter(count=1, total=0, counter_format=u'counter2')
        self.tty.clear()

        # Counter 1 in auto-refresh list
        self.assertIn(counter1, manager.autorefresh)

        # If auto-refreshed counter hasn't been refreshed recently, refresh
        counter1.last_update = 0
        counter2.refresh()
        self.tty.stdout.write(u'X\n')
        output = self.tty.stdread.readline()
        self.assertRegex(output, 'counter2.+counter1')

        # If auto-refreshed counter has been refreshed recently, skip
        counter1.last_update = time.time() + 5
        counter2.refresh()
        self.tty.stdout.write(u'X\n')
        output = self.tty.stdread.readline()
        self.assertRegex(output, 'counter2')
        self.assertNotRegex(output, 'counter1')

        # If already auto-refreshing, skip
        manager.refresh_lock = True
        counter1.last_update = 0
        counter2.refresh()
        # Have to explicitly flush
        manager._flush_streams()
        self.tty.stdout.write(u'X\n')
        output = self.tty.stdread.readline()
        self.assertRegex(output, 'counter2')
        self.assertNotRegex(output, 'counter1')

    def test_set_scroll_area_disabled(self):
        manager = enlighten.Manager(stream=self.tty.stdout,
                                    counter_class=MockCounter, set_scroll=False)
        manager.counters['dummy'] = 3

        manager._set_scroll_area()
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

    def test_set_scroll_area_no_change(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        manager.scroll_offset = 4

        manager._set_scroll_area()
        self.assertEqual(manager._buffer, [manager.term.move(21, 0)])

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

        self.assertEqual(manager._buffer, [term.move(21, 0)])
        self.assertEqual(manager._companion_buffer, [term.move(21, 0)])

    def test_set_scroll_area(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        term = manager.term
        stdread = self.tty.stdread
        self.assertEqual(manager.scroll_offset, 1)
        self.assertFalse(manager.process_exit)
        self.assertNotEqual(signal.getsignal(signal.SIGWINCH), manager._stage_resize)
        old_offset = manager.scroll_offset

        with mock.patch('enlighten._manager.atexit') as atexit:
            manager._set_scroll_area()

        self.assertEqual(manager.scroll_offset, 4)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._stage_resize)
        self.assertTrue(manager.process_exit)
        atexit.register.assert_called_with(manager._at_exit)

        offset = manager.scroll_offset
        scroll_position = term.height - offset
        self.assertEqual(manager._buffer,
                         [term.move(term.height - old_offset, 0),
                          '\n' * (offset - old_offset),
                          term.hide_cursor, term.csr(0, scroll_position),
                          term.move(scroll_position, 0)])

        # No companion buffer defined
        self.assertEqual(manager._companion_buffer, [])

        # Make sure nothing was flushed
        self.tty.stdout.write(u'X\n')
        self.assertEqual(stdread.readline(), 'X\n')

        # Run it again and make sure exit handling isn't reset
        del manager._buffer[:]
        del manager._companion_buffer[:]
        with mock.patch('enlighten._manager.atexit') as atexit:
            manager._set_scroll_area(force=True)

        self.assertFalse(atexit.register.called)
        self.assertEqual(manager._buffer,
                         [term.hide_cursor, term.csr(0, scroll_position),
                          term.move(scroll_position, 0)])

        # Set max counter lower and make sure scroll_offset hasn't changed
        manager.counters['dummy'] = 1
        with mock.patch('enlighten._manager.atexit') as atexit:
            manager._set_scroll_area()

        self.assertEqual(manager.scroll_offset, 4)

    def test_set_scroll_area_force(self):
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters['dummy'] = 3
        manager.scroll_offset = 4
        manager.height = 20
        scroll_position = manager.height - manager.scroll_offset
        term = manager.term

        with mock.patch('enlighten._manager.atexit') as atexit:
            manager._set_scroll_area(force=True)

            self.assertEqual(manager.scroll_offset, 4)
            self.assertTrue(manager.process_exit)

            self.assertEqual(manager._buffer,
                             [term.hide_cursor,
                              term.csr(0, scroll_position),
                              term.move(scroll_position, 0)])
            self.assertEqual(manager._companion_buffer, [])
            atexit.register.assert_called_with(manager._at_exit)

    def test_at_exit(self):

        tty = MockTTY()

        try:
            with mock.patch.object(tty, 'stdout', wraps=tty.stdout) as mockstdout:
                manager = enlighten.Manager(stream=tty.stdout, counter_class=MockCounter)
                term = manager.term
                reset = (term.normal_cursor +
                         term.csr(0, term.height - 1) +
                         term.move(term.height, 0))

                # process_exit is False
                manager._at_exit()
                self.assertFalse(mockstdout.flush.called)
                # No output
                tty.stdout.write(u'X\n')
                self.assertEqual(tty.stdread.readline(), 'X\n')

                # process_exit is True, set_scroll False
                manager.process_exit = True
                manager.set_scroll = False
                manager._at_exit()
                self.assertEqual(mockstdout.flush.call_count, 1)
                self.assertEqual(tty.stdread.readline(), term.move(25, 0) + term.cud1)

                # process_exit is True, set_scroll True
                manager.set_scroll = True
                manager._at_exit()
                self.assertEqual(mockstdout.flush.call_count, 2)
                self.assertEqual(tty.stdread.readline(), reset + term.cud1)

                # Ensure companion stream gets flushed
                manager.companion_stream = tty.stdout
                manager._at_exit()
                self.assertEqual(mockstdout.flush.call_count, 4)
                self.assertEqual(tty.stdread.readline(), reset + term.cud1)

                term = manager.term

        finally:
            # Ensure no errors if tty closes before _at_exit is called
            tty.close()
            manager._at_exit()

    def test_stop(self):

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters[MockCounter(manager=manager)] = 3
        manager.counters[MockCounter(manager=manager)] = 4
        term = manager.term
        self.assertIsNone(manager.companion_term)

        with mock.patch('enlighten._manager.atexit'):
            manager._set_scroll_area()

        self.assertEqual(manager.scroll_offset, 5)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._stage_resize)
        self.assertTrue(manager.process_exit)

        # Clear buffer
        del manager._buffer[:]

        manager.enabled = False
        manager.stop()

        # No output, No changes
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')
        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._stage_resize)
        self.assertTrue(manager.process_exit)

        manager.enabled = True
        manager.stop()

        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)

        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(term.height - 2, 0) + term.clear_eol +
                         term.move(term.height - 1, 0) + term.clear_eol +
                         term.normal_cursor + term.csr(0, term.height - 1) +
                         term.move(term.height, 0) + 'X\n')

        self.assertFalse(manager.process_exit)
        self.assertFalse(manager.enabled)
        for counter in manager.counters:
            self.assertFalse(counter.enabled)

    def test_stop_no_set_scroll(self):
        """
        set_scroll is False
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    set_scroll=False)
        manager.counters[MockCounter(manager=manager)] = 3
        manager.counters[MockCounter(manager=manager)] = 4
        term = manager.term

        with mock.patch('enlighten._manager.atexit'):
            with mock.patch.object(term, 'change_scroll'):
                manager._set_scroll_area()

        self.assertEqual(manager.scroll_offset, 5)
        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager._stage_resize)
        self.assertTrue(manager.process_exit)

        # Stream empty
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

        manager.stop()

        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)
        self.assertFalse(manager.process_exit)

        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(),
                         term.move(term.height - 2, 0) + term.clear_eol +
                         term.move(term.height - 1, 0) + term.clear_eol +
                         term.move(25, 0) + 'X\n')

    def test_stop_never_used(self):
        """
        In this case, _set_scroll_area() was never called
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        manager.counters[MockCounter(manager=manager)] = 3
        manager.counters[MockCounter(manager=manager)] = 4
        term = manager.term

        self.assertFalse(manager.process_exit)

        manager.stop()

        self.assertEqual(signal.getsignal(signal.SIGWINCH), manager.sigwinch_orig)

        # Only reset terminal
        self.tty.stdout.write(u'X\n')
        reset = term.normal_cursor + term.csr(0, term.height - 1) + term.move(term.height, 0)
        self.assertEqual(self.tty.stdread.readline(), reset + 'X\n')

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

        with mock.patch('enlighten._manager.atexit'):
            manager._set_scroll_area()

        del manager._buffer[:]
        del manager._companion_buffer[:]

        with mock.patch.object(manager, '_flush_streams'):
            manager.stop()

        self.assertEqual(manager._buffer,
                         [term.move(term.height - 2, 0), term.clear_eol,
                          term.move(term.height - 1, 0), term.clear_eol,
                          term.normal_cursor, term.csr(0, term.height - 1),
                          term.move(term.height, 0)])

        self.assertEqual(manager._companion_buffer,
                         [term.normal_cursor, term.csr(0, term.height - 1),
                          term.move(term.height, 0)])

    def test_stop_position_1(self):
        """
        Ensure a line feed is given if there is a counter at position 1
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        term = manager.term

        manager.counters[MockCounter(manager=manager)] = 3
        with mock.patch.object(manager, '_flush_streams'):
            manager.stop()

        self.assertEqual(manager._buffer,
                         [term.normal_cursor, term.csr(0, term.height - 1),
                          term.move(term.height, 0)])

        del manager._buffer[:]
        manager.enabled = True
        manager.counters[MockCounter(manager=manager)] = 1
        with mock.patch.object(manager, '_flush_streams'):
            manager.stop()

        self.assertEqual(manager._buffer,
                         [term.normal_cursor, term.csr(0, term.height - 1),
                          term.move(term.height, 0), term.cud1 or '\n'])

    def test_resize(self):
        """
        Resize lock must be False for handler to run
        Terminal size is cached unless resize handler runs
        """

        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        counter3 = MockCounter(manager=manager)
        manager.counters[counter3] = 3
        manager.scroll_offset = 4
        term = manager.term

        with mock.patch('%s.width' % TERMINAL, new_callable=mock.PropertyMock) as mockwidth:
            mockwidth.return_value = 70

            manager.resize_lock = True
            with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
                manager._stage_resize()
                self.assertFalse(ssa.called)

            self.assertEqual(manager.width, 80)
            self.assertTrue(manager.resize_lock)

            self.tty.stdout.write(u'X\n')
            self.assertEqual(self.tty.stdread.readline(), 'X\n')

            self.assertEqual(counter3.calls, [])

            manager.resize_lock = False
            with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
                self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.width, 70)
            self.assertFalse(manager.resize_lock)

            self.tty.stdout.write(u'X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(21, 0) + term.clear_eos + 'X\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_threaded_eval(self):
        """
        Dynamic value for threaded determined when scroll area is first set
        """

        # Not dynamic if explicitly True
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    threaded=True)
        self.assertTrue(manager.threaded)
        with mock.patch('threading.active_count', return_value=4):
            manager.counter()
        self.assertTrue(manager.threaded)

        # Not dynamic if explicitly False
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    threaded=False)
        self.assertFalse(manager.threaded)
        with mock.patch('threading.active_count', return_value=4):
            manager.counter()
        self.assertFalse(manager.threaded)

        # False by default
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        self.assertIsNone(manager.threaded)
        manager.counter()
        self.assertFalse(manager.threaded)

        # True if threaded
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        self.assertIsNone(manager.threaded)
        with mock.patch('threading.active_count', return_value=4):
            manager.counter()
        self.assertTrue(manager.threaded)

        # True if has child processes
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        self.assertIsNone(manager.threaded)
        with mock.patch('multiprocessing.active_children', return_value=[1, 2]):
            manager.counter()
        self.assertTrue(manager.threaded)

        # True if is child processes
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
        self.assertIsNone(manager.threaded)
        with mock.patch('multiprocessing.current_process') as c_process:
            c_process.name = 'Process1'
            manager.counter()
        self.assertTrue(manager.threaded)

    def test_resize_threaded(self):
        """
        Test a resize event threading behavior
        """
        manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                    threaded=True)
        counter3 = MockCounter(manager=manager)
        counter3.last_update = time.time()
        manager.counters[counter3] = 3
        manager.scroll_offset = 4
        term = manager.term

        # simulate resize
        manager._stage_resize()
        self.assertTrue(manager._resize)
        self.assertEqual(counter3.last_update, 0)

        with mock.patch('%s.width' % TERMINAL, new_callable=mock.PropertyMock) as mockwidth:
            mockwidth.return_value = 70

            # resize doesn't happen until a write is called
            self.assertEqual(manager.width, 80)

            with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
                manager.write()
                self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.width, 70)

            self.tty.stdout.write(u'X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(21, 0) + term.clear_eos + 'X\n')
            self.assertFalse(manager.resize_lock)
            self.assertFalse(manager._resize)
            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_resize_handler_height_less(self):

        with mock.patch('%s.height' % TERMINAL, new_callable=mock.PropertyMock) as mockheight:
            mockheight.side_effect = [25, 23]

            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter)
            counter3 = MockCounter(manager=manager)
            manager.counters[counter3] = 3
            manager.scroll_offset = 4

            with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
            self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.height, 23)

            self.assertEqual(self.tty.stdread.readline(), manager.term.move(19, 0) + '\n')
            for _ in range(5):
                self.assertEqual(self.tty.stdread.readline(), '\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_resize_handler_height_greater_threaded(self):

        with mock.patch('%s.height' % TERMINAL, new_callable=mock.PropertyMock) as mockheight:
            mockheight.side_effect = [25, 27]

            manager = enlighten.Manager(stream=self.tty.stdout, counter_class=MockCounter,
                                        threaded=True)
            counter3 = MockCounter(manager=manager)
            manager.counters[counter3] = 3
            manager.scroll_offset = 4
            term = manager.term

            with mock.patch('enlighten._manager.Manager._set_scroll_area') as ssa:
                manager._resize_handler()
            self.assertEqual(ssa.call_count, 1)

            self.assertEqual(manager.height, 27)

            self.tty.stdout.write(u'X\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(27, 0) + '\n')
            self.assertEqual(self.tty.stdread.readline(), '\n')
            self.assertEqual(self.tty.stdread.readline(), '\n')
            self.assertEqual(self.tty.stdread.readline(), term.move(23, 0) + term.clear_eos + 'X\n')

            self.assertEqual(counter3.calls, ['refresh(flush=False, elapsed=None)'])

    def test_disable(self):
        mgr = enlighten.Manager(stream=self.tty.stdout, enabled=False)
        self.assertFalse(mgr.enabled)
        ctr = mgr.counter()
        self.assertIsInstance(ctr, enlighten._counter.Counter)
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
        self.tty.stdout.write(u'X\n')
        self.assertEqual(self.tty.stdread.readline(), 'X\n')

    def test_context_manager(self):

        mgr = None

        with enlighten.Manager(stream=self.tty.stdout) as manager:
            self.assertIsInstance(manager, _manager.Manager)
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
        with mock.patch.object(_manager, 'RESIZE_SUPPORTED', False):
            manager = enlighten.Manager(stream=self.tty.stdout)
            self.assertFalse(hasattr(manager, 'sigwinch_orig'))

            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4

        # Test set_scroll_area()
        with mock.patch.object(_manager.signal, 'signal',
                               wraps=_manager.signal.signal) as mocksignal:
            with mock.patch('enlighten._manager.atexit'):

                # Test no resize signal set_scroll_area
                with mock.patch.object(_manager, 'RESIZE_SUPPORTED', False):
                    with mock.patch.object(manager.term, 'change_scroll'):
                        manager._set_scroll_area()

                self.assertFalse(mocksignal.called)

                # Test normal case set_scroll_area
                with mock.patch.object(stdmgr.term, 'change_scroll'):
                    stdmgr._set_scroll_area()
                self.assertTrue(mocksignal.called)

        # Test stop()
        with mock.patch.object(_manager.signal, 'signal',
                               wraps=_manager.signal.signal) as mocksignal:

            # Test no resize signal stop
            with mock.patch.object(_manager, 'RESIZE_SUPPORTED', False):
                manager.stop()
            self.assertFalse(mocksignal.called)

            # Test normal case stop
            stdmgr.stop()
            self.assertTrue(mocksignal.called)

    def test_no_resize(self):

        with mock.patch.object(_manager.signal, 'signal',
                               wraps=_manager.signal.signal) as mocksignal:

            manager = enlighten.Manager(stream=self.tty.stdout, no_resize=True)
            self.assertFalse(hasattr(manager, 'sigwinch_orig'))
            self.assertFalse(mocksignal.called)

            manager.counters[MockCounter(manager=manager)] = 3
            manager.counters[MockCounter(manager=manager)] = 4

            with mock.patch.object(manager.term, 'change_scroll'):
                manager._set_scroll_area()

            self.assertFalse(mocksignal.called)

            manager.stop()

            self.assertFalse(mocksignal.called)


class TestGetManager(TestCase):

    def setUp(self):
        self.tty = MockTTY()

    def tearDown(self):
        self.tty.close()

    def test_get_manager_tty(self):

        # stdout is attached to a tty
        with redirect_output('stdout', self.tty.stdout):
            self.assertTrue(sys.stdout.isatty())
            manager = enlighten.get_manager(unit='knights')
            self.assertIsInstance(manager, _manager.Manager)
            self.assertTrue('unit' in manager.defaults)
            self.assertTrue('enabled' in manager.defaults)
            self.assertTrue(manager.enabled)
            self.assertTrue(manager.defaults['enabled'])

    @unittest.skipIf(STDOUT_NO_FD, 'No file descriptor for stdout')
    def test_get_manager_no_tty(self):

        # stdout is not attached to a tty
        with redirect_output('stdout', OUTPUT):
            self.assertFalse(sys.stdout.isatty())
            manager = enlighten.get_manager(unit='knights')
            self.assertIsInstance(manager, _manager.Manager)
            self.assertTrue('unit' in manager.defaults)
            self.assertFalse(manager.enabled)
            self.assertTrue('enabled' in manager.defaults)
            self.assertFalse(manager.defaults['enabled'])
