# -*- coding: utf-8 -*-
# Copyright 2017 - 2018 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for Enlighten
"""

from contextlib import contextmanager
import fcntl
import io
import os
import pty
import struct
import sys
import termios
import unittest

from enlighten import Manager
from enlighten._basecounter import BaseCounter
from enlighten._counter import Counter
from enlighten._statusbar import StatusBar

# pylint: disable=import-error
if sys.version_info[:2] < (3, 3):
    import mock
else:
    from unittest import mock  # noqa: F401  # pylint: disable=no-name-in-module

if sys.version_info[0] < 3:
    from StringIO import StringIO
    PY2 = True
else:
    from io import StringIO
    PY2 = False

# pylint: enable=import-error


OUTPUT = StringIO()
os.environ['TERM'] = 'xterm-256color'  # Default to xterm-256color


# pylint: disable=missing-docstring

class TestCase(unittest.TestCase):
    """
    Subclass of :py:class:`unittest.TestCase` for customization
    """


# Fix deprecated methods for 2.7
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


# Some tests fail if "real" stdout is does not have a file descriptor
try:
    sys.__stdout__.fileno()
except ValueError:
    STDOUT_NO_FD = True
else:
    STDOUT_NO_FD = False


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
        # pylint: disable=consider-using-with
        self.stdout = io.open(self.slave, 'w', 1, encoding='UTF-8', newline='')
        self.stdread = io.open(self.master, 'r', encoding='UTF-8', newline='\n')

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

    def clear(self):
        # Using TCIOFLUSH here instead of TCIFLUSH to support MacOS
        termios.tcflush(self.stdread, termios.TCIOFLUSH)

    def resize(self, height, width):
        fcntl.ioctl(self.slave, termios.TIOCSWINSZ, struct.pack('hhhh', height, width, 0, 0))


class MockBaseCounter(BaseCounter):
    """
    Mock version of base counter for testing
    """

    def update(self, *args, **kwargs):
        """
        Simple update that updates the count. We know it's called based on the count.
        """

        self.count += 1


class MockCounter(Counter):

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


class MockStatusBar(StatusBar):

    __slots__ = ('called', 'calls')

    def __init__(self, *args, **kwargs):
        super(MockStatusBar, self).__init__(*args, **kwargs)
        self.called = 0
        self.calls = []

    def refresh(self, flush=True, elapsed=None):
        self.called += 1
        self.calls.append('refresh(flush=%s, elapsed=%s)' % (flush, elapsed))


class MockManager(Manager):
    # pylint: disable=super-init-not-called
    def __init__(self, counter_class=Counter, **kwargs):
        super(MockManager, self).__init__(counter_class=counter_class, **kwargs)
        self.width = 80
        self.output = []
        self.remove_calls = 0

    def write(self, output='', flush=True, counter=None, **kwargs):

        if callable(output):
            output = output(**kwargs)

        self.output.append('write(output=%s, flush=%s, position=%s)' %
                           (output, flush, counter.position))

    def remove(self, counter):
        self.remove_calls += 1
        super(MockManager, self).remove(counter)
