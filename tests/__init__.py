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
import os
import pty
import struct
import sys
import termios

from enlighten import Manager
from enlighten._counter import Counter

# pylint: disable=import-error

if sys.version_info[:2] < (2, 7):
    import unittest2 as unittest
else:
    import unittest  # pylint: disable=wrong-import-order

if sys.version_info[:2] < (3, 3):
    import mock
else:
    from unittest import mock  # noqa: F401  # pylint: disable=no-name-in-module

if sys.version_info[0] < 3:
    from StringIO import StringIO
else:
    from io import StringIO

# pylint: enable=import-error


OUTPUT = StringIO()
os.environ['TERM'] = 'vt100'  # Default to VT100


# pylint: disable=missing-docstring

class TestCase(unittest.TestCase):
    """
    Subclass of :py:class:`unittest.TestCase` for customization
    """


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

        if sys.version_info[0] < 3:
            self.stdout = os.fdopen(self.slave, 'w', 1)
            self.stdread = os.fdopen(self.master, 'r')
        else:
            self.stdout = os.fdopen(self.slave, 'w', 1, encoding='UTF-8',
                                    newline='\n')  # line buffering for pypy2
            self.stdread = os.fdopen(self.master, 'r', encoding='UTF-8', newline='\n')

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


class MockManager(Manager):
    # pylint: disable=super-init-not-called
    def __init__(self, counter_class=Counter, **kwargs):
        super(MockManager, self).__init__(counter_class=counter_class, **kwargs)
        self.width = 80
        self.output = []

    def write(self, output='', flush=True, position=0):
        self.output.append('write(output=%s, flush=%s, position=%s)' % (output, flush, position))
