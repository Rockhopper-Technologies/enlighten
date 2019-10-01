# -*- coding: utf-8 -*-
# Copyright 2017 - 2019 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
**Windows 10 terminal submodule**

Provides a terminal class for consoles in Windows 10.0.10586 or higher
https://docs.microsoft.com/en-us/windows/console/console-virtual-terminal-sequences
"""

from collections import namedtuple
import ctypes
from ctypes import wintypes
import io
import msvcrt  # pylint: disable=import-error
import os
import platform
import sys


COLORS = {'black': 30,
          'red': 31,
          'green': 32,
          'yellow': 33,
          'blue': 34,
          'magenta': 35,
          'cyan': 36,
          'white': 37,
          'bright_black': 90,
          'bright_red': 91,
          'bright_green': 92,
          'bright_yellow': 93,
          'bright_blue': 94,
          'bright_magenta': 95,
          'bright_cyan': 96,
          'bright_white': 97}

GTS_SUPPORTED = hasattr(os, 'get_terminal_size')
TerminalSize = namedtuple('TerminalSize', ('columns', 'lines'))
LPDWORD = ctypes.POINTER(wintypes.DWORD)
COORD = wintypes._COORD  # pylint: disable=protected-access


class ConsoleScreenBufferInfo(ctypes.Structure):
    """
    CONSOLE_SCREEN_BUFFER_INFO structure
    https://docs.microsoft.com/en-us/windows/console/console-screen-buffer-info-str
    """

    _fields_ = [('dwSize', COORD),
                ('dwCursorPosition', COORD),
                ('wAttributes', wintypes.WORD),
                ('srWindow', wintypes.SMALL_RECT),
                ('dwMaximumWindowSize', COORD)]


CSBIP = ctypes.POINTER(ConsoleScreenBufferInfo)


def _check_bool(result, func, args):  # pylint: disable=unused-argument
    """
    Used as an error handler for Windows calls
    Gets last error if call is not successful
    """

    if not result:
        raise ctypes.WinError(ctypes.get_last_error())
    return args


KERNEL32 = ctypes.WinDLL('kernel32', use_last_error=True)

KERNEL32.GetConsoleMode.errcheck = _check_bool
KERNEL32.GetConsoleMode.argtypes = (wintypes.HANDLE, LPDWORD)

KERNEL32.SetConsoleMode.errcheck = _check_bool
KERNEL32.SetConsoleMode.argtypes = (wintypes.HANDLE, wintypes.DWORD)

KERNEL32.GetConsoleScreenBufferInfo.errcheck = _check_bool
KERNEL32.GetConsoleScreenBufferInfo.argtypes = (wintypes.HANDLE, CSBIP)


def get_csbi(filehandle=None):
    """
    Returns a CONSOLE_SCREEN_BUFFER_INFO structure for the given console or stdout
    """

    if filehandle is None:
        filehandle = msvcrt.get_osfhandle(sys.__stdout__.fileno())

    csbi = ConsoleScreenBufferInfo()
    KERNEL32.GetConsoleScreenBufferInfo(filehandle, ctypes.byref(csbi))
    return csbi


def enable_vt_mode(filehandle=None):
    """
    Enables virtual terminal processing mode for the given console or stdout
    """

    if filehandle is None:
        filehandle = msvcrt.get_osfhandle(sys.__stdout__.fileno())

    current_mode = wintypes.DWORD()
    KERNEL32.GetConsoleMode(filehandle, ctypes.byref(current_mode))
    new_mode = 0x0004 | current_mode.value
    KERNEL32.SetConsoleMode(filehandle, new_mode)


class Terminal(object):
    """
    Blessed-inspired terminal class for Windows 10+ with virtual terminal processing
    """

    hide_cursor = u'\x1B[?25l'
    show_cursor = u'\x1B[?25h'
    normal_cursor = show_cursor
    cud1 = u'\x1B[1B'
    clear_eol = u'\x1B[0K'
    clear_eos = u'\x1B[0J'

    # pylint: disable=unused-argument
    def __init__(self, kind=None, stream=None, force_styling=False):

        if stream is None:
            stream = sys.__stdout__

        try:
            stream_fd = (stream.fileno() if hasattr(stream, 'fileno') and
                         callable(stream.fileno) else None)
        except io.UnsupportedOperation:
            stream_fd = None

        self.stream = stream
        self.stream_fd = stream_fd
        self.stream_fh = msvcrt.get_osfhandle(self.stream_fd)

        # Use built-in virtual terminal processing for Windows 10.0.10586 and newer
        if tuple(int(num) for num in platform.version().split('.')) >= (10, 0, 10586):
            enable_vt_mode(self.stream_fh)
        else:
            # Use ansicon for older versions of Windows
            import ansicon  # pylint: disable=import-error,import-outside-toplevel
            ansicon.load()
    # pylint: enable=unused-argument

    @staticmethod
    def _apply_color(code, content):
        """
        Apply a color code to text
        """

        normal = u'\x1B[0m'
        seq = u'\x1B[%sm' % code

        # Replace any normal sequences with this sequence to support nested colors
        return seq + (normal + seq).join(content.split(normal)) + normal

    def color(self, code):
        """
        When color is given as a number, apply that color to the content
        While this is designed to support 256 color terminals, Windows will approximate
        this with 16 colors
        """

        def func(content=''):
            return self._apply_color(u'38;5;%d' % code, content)
        return func

    @staticmethod
    def csr(top, bottom):
        """
        Set scroll area (DECSTBM)
        """
        return u'\x1B[%d;%dr' % (top, bottom)

    @staticmethod
    def move(ypos, xpos):
        """
        Move cursor (CUP)
        """
        return u'\x1B[%d;%dH' % (ypos, xpos)

    def _height_and_width(self):
        """
        Query console for dimensions
        Returns named tuple (columns, lines)
        """

        size = None

        # In Python 3.3+ we can let the standard library handle this
        if GTS_SUPPORTED:
            try:
                size = os.get_terminal_size(self.stream_fd)
            except (ValueError, OSError):
                pass

        else:
            try:
                window = get_csbi(self.stream_fh).srWindow
                size = TerminalSize(window.Right - window.Left + 1, window.Bottom - window.Top + 1)
            except OSError:
                pass

        if size is None:
            size = TerminalSize(int(os.getenv('COLUMNS', '80')), int(os.getenv('LINES', '25')))

        return size

    @property
    def height(self):
        """
        Returns terminal height
        """
        return self._height_and_width().lines

    @property
    def width(self):
        """
        Returns terminal width
        """
        return self._height_and_width().columns


# The following code dynamically creates the color methods for the Terminal class

def create_color_method(color, code):
    """
    Create a function for the given color
    Done inside this function to keep the variables out of the main scope
    """

    def func(self, content=''):
        return self._apply_color(code, content)  # pylint: disable=protected-access

    setattr(Terminal, color, func)


def create_color_methods():
    """
    Creates a function for each of the 16 main colors
    Done inside this function to keep the variables out of the main scope
    """

    for color, code in COLORS.items():

        create_color_method(color, code)


create_color_methods()
