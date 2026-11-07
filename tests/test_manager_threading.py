# -*- coding: utf-8 -*-
# Copyright 2026 WhyTan00
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Deterministic tests for manager operation serialization."""

from __future__ import unicode_literals

import io
import sys
import threading
import warnings

from enlighten import Manager
try:
    from enlighten._notebook_manager import NotebookManager
except ImportError:
    NotebookManager = None

from tests import TestCase, mock, unittest


class PausingStream(io.StringIO):
    """Pause one synthetic write without writing to a terminal."""

    def __init__(self):
        super(PausingStream, self).__init__()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.pause = False

    def write(self, output):
        if self.pause:
            self.pause = False
            self.entered.set()
            if not self.release.wait(5):
                raise RuntimeError('Timed out waiting for stream release')
        return super(PausingStream, self).write(output)


class ObservedLock(object):
    """Report a worker's lock attempt before it blocks."""

    def __init__(self, reached):
        self.lock = threading.RLock()
        self.reached = reached

    def acquire(self, blocking=True):
        """Acquire the observed lock."""
        if threading.current_thread().name == 'second-writer':
            if self.lock.acquire(False):  # pylint: disable=consider-using-with
                return True
            self.reached.set()
        return self.lock.acquire(blocking)

    def release(self):
        """Release the observed lock."""
        self.lock.release()

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


# pylint: disable=missing-docstring, protected-access
class TestManagerThreading(TestCase):

    def setUp(self):
        self.stream = PausingStream()
        self.manager = Manager(stream=self.stream, no_resize=True,
                               set_scroll=False, preserve_column=False, threaded=True)
        self.addCleanup(self.manager.stop)

    def run_concurrent(self, operation, expect_blocked=True, first_operation=None):
        reached = threading.Event()
        finished = threading.Event()
        errors = []
        self.manager._lock = ObservedLock(reached)
        self.stream.pause = first_operation is None

        def first():
            try:
                if first_operation is None:
                    self.manager.write('FIRST-MARKER')
                else:
                    first_operation()
            except Exception as error:  # pylint: disable=broad-except
                errors.append(error)

        def second():
            try:
                operation()
            except Exception as error:  # pylint: disable=broad-except
                errors.append(error)
            finally:
                finished.set()
                # Baseline code does not acquire the injected lock.
                reached.set()

        workers = [threading.Thread(target=first),
                   threading.Thread(target=second, name='second-writer')]
        for worker in workers:
            worker.daemon = True
        workers[0].start()
        try:
            self.assertTrue(self.stream.entered.wait(5))
            workers[1].start()
            self.assertTrue(reached.wait(5))
            finished_before_release = finished.is_set()
            if not expect_blocked:
                self.assertTrue(finished.wait(5),
                                'Resize signal handler blocked on the manager lock')
        finally:
            self.stream.release.set()
            for worker in workers:
                if worker.ident is not None:
                    worker.join(5)
        self.assertFalse(any(worker.is_alive() for worker in workers))
        self.assertEqual(errors, [])
        if expect_blocked:
            self.assertFalse(finished_before_release,
                             'Concurrent manager operation was not serialized')

    def test_buffered_write(self):
        self.run_concurrent(lambda: self.manager.write('SECOND-MARKER', flush=False))
        self.manager.write('')
        self.assertIn('FIRST-MARKER', self.stream.getvalue())
        self.assertIn('SECOND-MARKER', self.stream.getvalue())

    def test_add_counter(self):
        self.run_concurrent(self.manager.counter)
        self.assertEqual(list(self.manager.counters.values()), [1])

    def test_remove_counter(self):
        counter = self.manager.counter(leave=False)
        self.run_concurrent(lambda: self.manager.remove(counter))
        self.assertNotIn(counter, self.manager.counters)

    def test_add_remove_layout(self):
        removed = self.manager.counter(leave=False)
        moved = self.manager.counter()
        original_clear = type(moved).clear
        paused = []

        def clear(counter, *args, **kwargs):
            if counter is moved and not paused:
                paused.append(True)
                self.stream.entered.set()
                if not self.stream.release.wait(5):
                    raise RuntimeError('Timed out while moving counter')
            return original_clear(counter, *args, **kwargs)

        with mock.patch.object(type(moved), 'clear', autospec=True, side_effect=clear):
            self.run_concurrent(lambda: self.manager.remove(removed),
                                first_operation=self.manager.counter)
        self.assertNotIn(removed, self.manager.counters)
        self.assertEqual(sorted(self.manager.counters.values()), [1, 2])
        self.assertEqual(self.manager.counters[moved], 2)

    def run_close_race(self, close_again=False, clear=False):
        counter = self.manager.counter(leave=False)
        method = 'clear' if clear else 'refresh'
        original = getattr(type(counter), method)
        paused = []

        def render(current, *args, **kwargs):
            if current is counter and not paused:
                paused.append(True)
                self.stream.entered.set()
                if not self.stream.release.wait(5):
                    raise RuntimeError('Timed out during counter close')
            return original(current, *args, **kwargs)

        def close():
            counter.close(clear=clear)

        with warnings.catch_warnings(record=True):
            warnings.simplefilter('always')
            with mock.patch.object(type(counter), method, autospec=True, side_effect=render):
                operation = close if close_again else lambda: self.manager.remove(counter)
                self.run_concurrent(operation, first_operation=close)
        self.assertNotIn(counter, self.manager.counters)

    def test_close_while_removing(self):
        self.run_close_race()

    def test_concurrent_close(self):
        self.run_close_race(close_again=True)

    def test_concurrent_close_clear(self):
        self.run_close_race(close_again=True, clear=True)

    def test_close_clear_after_removal(self):
        counter = self.manager.counter(leave=False)
        self.manager.remove(counter)
        counter.close(clear=True)
        self.assertNotIn(counter, self.manager.counters)

    def test_clear_queued_behind_remove(self):
        counter = self.manager.counter(leave=False)
        original_flush = self.manager._flush_streams
        paused = []

        def flush():
            if not paused:
                paused.append(True)
                self.stream.entered.set()
                if not self.stream.release.wait(5):
                    raise RuntimeError('Timed out during counter removal')
            return original_flush()

        with mock.patch.object(self.manager, '_flush_streams', side_effect=flush):
            self.run_concurrent(counter.clear,
                                first_operation=lambda: self.manager.remove(counter))
        self.assertNotIn(counter, self.manager.counters)

    def test_position_during_registration(self):
        moved = self.manager.counter()
        original_clear = type(moved).clear
        registered = []
        positions = []

        def clear(current, *args, **kwargs):
            if current is moved and not registered:
                registered.extend(counter for counter in self.manager.counters
                                  if counter is not moved)
                self.stream.entered.set()
                if not self.stream.release.wait(5):
                    raise RuntimeError('Timed out during counter registration')
            return original_clear(current, *args, **kwargs)

        with mock.patch.object(type(moved), 'clear', autospec=True, side_effect=clear):
            try:
                self.run_concurrent(lambda: positions.append(moved.position),
                                    first_operation=self.manager.counter)
            finally:
                self.assertEqual(positions, [2])

    def test_stop(self):
        self.run_concurrent(self.manager.stop)
        self.assertFalse(self.manager.enabled)

    def test_signal_during_write(self):
        self.manager.threaded = False

        def output():
            self.manager._stage_resize()
            return 'OUTPUT'

        with mock.patch.object(self.manager, '_resize_handler') as resize:
            self.manager.write(output)
            resize.assert_not_called()
            self.assertTrue(self.manager._resize)
            self.manager.write('')
            resize.assert_called_once_with()
            self.assertFalse(self.manager._resize)

    def test_signal_while_worker_holds_lock(self):
        with mock.patch.object(self.manager, '_resize_handler') as resize:
            self.manager.threaded = False
            self.run_concurrent(self.manager._stage_resize, expect_blocked=False)
            resize.assert_not_called()
            self.assertTrue(self.manager._resize)

    def test_signal_during_resize_stays_pending(self):
        self.manager._resize = True
        with mock.patch.object(self.manager, '_resize_handler',
                               side_effect=self.manager._stage_resize) as resize:
            self.manager.write('')
            resize.assert_called_once_with()
        self.assertTrue(self.manager._resize)

    @unittest.skipUnless(hasattr(threading, '_RLock'), 'Pure-Python lock unavailable')
    def test_signal_during_python_lock_transitions(self):
        lock = self.manager._lock = threading._RLock()
        transitions = []

        def trace(frame, event, arg):  # pylint: disable=unused-argument
            if (event == 'line' and frame.f_locals.get('self') is lock
                    and frame.f_code.co_name in ('acquire', 'release')):
                transitions.append(frame.f_code.co_name)
                self.manager._stage_resize()
            return trace

        previous_trace = sys.gettrace()
        try:
            sys.settrace(trace)
            self.manager.write('SIGNALS-DURING-LOCK')
            self.assertTrue(self.manager._resize)
            # The handler's own non-blocking acquisition must also be protected.
            self.manager._stage_resize()
        finally:
            sys.settrace(previous_trace)
        self.assertIn('acquire', transitions)
        self.assertIn('release', transitions)
        self.assertEqual(self.manager._local.depth, 0)

        acquired = []

        def other_thread():
            # A non-blocking probe cannot use a context manager.
            acquired.append(lock.acquire(False))  # pylint: disable=consider-using-with
            if acquired[-1]:
                lock.release()

        worker = threading.Thread(target=other_thread)
        worker.daemon = True
        worker.start()
        worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(acquired, [True])

    def test_lock_released_on_error(self):
        def output():
            raise ValueError('synthetic formatting error')

        with self.assertRaises(ValueError):
            self.manager.write(output)
        self.assertEqual(self.manager._local.depth, 0)
        self.run_concurrent(lambda: self.manager.write('AFTER-ERROR'))

    def test_recursive_autorefresh(self):
        counter = self.manager.counter(autorefresh=True, min_delta=0)
        counter.update()
        self.run_concurrent(lambda: self.manager.write('WITH-AUTOREFRESH'))
        self.assertIn('WITH-AUTOREFRESH', self.stream.getvalue())


@unittest.skipIf(NotebookManager is None, 'IPython is not installed')
class TestNotebookManagerThreading(TestCase):
    """Validate manager locking with a fake display and no notebook kernel."""

    def setUp(self):
        self.stream = PausingStream()
        with mock.patch('enlighten._notebook_manager.DisplayHandle'):
            self.manager = NotebookManager()
        self.addCleanup(self.manager.stop)

    def run_concurrent(self, operation, first_operation=None):
        paused = []

        def display(_html):
            if not paused:
                paused.append(True)
                self.stream.entered.set()
                if not self.stream.release.wait(5):
                    raise RuntimeError('Timed out waiting for fake display release')

        self.manager._display.display.side_effect = display
        self.manager._display.update.side_effect = display
        TestManagerThreading.run_concurrent(
            self, operation, first_operation=(first_operation or
                                              (lambda: self.manager.write('FIRST-MARKER'))))

    def test_write(self):
        # pylint: disable=no-member
        self.run_concurrent(lambda: self.manager.write('SECOND-MARKER'))
        self.assertIn('SECOND-MARKER', self.manager._html.data)
        self.manager._display.display.assert_called_once_with(self.manager._html)
        self.manager._display.update.assert_called_once_with(self.manager._html)

    def test_add_counter(self):
        self.run_concurrent(self.manager.counter)
        self.assertEqual(list(self.manager.counters.values()), [1])

    def test_remove_counter(self):
        counter = self.manager.counter(leave=False)
        self.run_concurrent(lambda: self.manager.remove(counter))
        self.assertNotIn(counter, self.manager.counters)

    def test_stop(self):
        counter = self.manager.counter()
        self.run_concurrent(self.manager.stop)
        self.assertFalse(counter.enabled)

    def test_write_queued_behind_stop(self):
        # pylint: disable=no-member
        self.run_concurrent(lambda: self.manager.write('AFTER-SHUTDOWN'),
                            first_operation=self.manager.stop)
        self.assertFalse(self.manager.enabled)
        self.assertNotIn('AFTER-SHUTDOWN', self.manager._html.data)
        self.manager._display.update.assert_not_called()
        self.manager.write('AFTER-RETURN')
        self.assertNotIn('AFTER-RETURN', self.manager._html.data)

    def test_stop_display_error(self):
        counter = self.manager.counter()
        self.manager._display.update.side_effect = ValueError('synthetic display error')
        with self.assertRaises(ValueError):
            self.manager.stop()
        self.assertFalse(self.manager.enabled)
        self.assertFalse(counter.enabled)
        self.manager.write('AFTER-DISPLAY-ERROR')
        self.assertNotIn('AFTER-DISPLAY-ERROR', self.manager._html.data)
