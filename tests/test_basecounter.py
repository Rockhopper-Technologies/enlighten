# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._counter and enlighten.counter
"""

from types import GeneratorType

from enlighten._basecounter import BaseCounter

from tests import TestCase, MockManager, MockTTY, MockBaseCounter


# pylint: disable=protected-access
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
        counter = BaseCounter(manager=self.manager)
        self.assertIsNone(counter.color)
        self.assertIsNone(counter.color)
        self.assertIs(counter.manager, self.manager)
        self.assertEqual(counter.count, 0)
        self.assertEqual(counter.start_count, 0)

    def test_no_manager(self):
        """Raise an error if there is no manager specified"""
        with self.assertRaisesRegex(TypeError, 'manager must be specified'):
            BaseCounter()

    def test_color_invalid(self):
        """Color must be a valid string, RGB, or int 0 - 255"""
        # Unsupported type
        with self.assertRaisesRegex(AttributeError, 'Invalid color specified: 1.0'):
            BaseCounter(manager=self.manager, color=1.0)

        # Invalid String
        with self.assertRaisesRegex(AttributeError, 'Invalid color specified: buggersnot'):
            BaseCounter(manager=self.manager, color='buggersnot')

        # Invalid integer
        with self.assertRaisesRegex(AttributeError, 'Invalid color specified: -1'):
            BaseCounter(manager=self.manager, color=-1)
        with self.assertRaisesRegex(AttributeError, 'Invalid color specified: 256'):
            BaseCounter(manager=self.manager, color=256)

        # Invalid iterable
        with self.assertRaisesRegex(AttributeError, r'Invalid color specified: \[\]'):
            BaseCounter(manager=self.manager, color=[])
        with self.assertRaisesRegex(AttributeError, r'Invalid color specified: \[1\]'):
            BaseCounter(manager=self.manager, color=[1])
        with self.assertRaisesRegex(AttributeError, r'Invalid color specified: \(1, 2\)'):
            BaseCounter(manager=self.manager, color=(1, 2))
        with self.assertRaisesRegex(AttributeError, r'Invalid color specified: \(1, 2, 3, 4\)'):
            BaseCounter(manager=self.manager, color=(1, 2, 3, 4))

    def test_colorize_none(self):
        """If color is None, return content unchanged"""
        counter = BaseCounter(manager=self.manager)
        self.assertEqual(counter._colorize('test'), 'test')

    def test_colorize_string(self):
        """Return string formatted with color (string)"""
        counter = BaseCounter(manager=self.manager, color='red')
        self.assertEqual(counter.color, 'red')
        self.assertEqual(counter._color, ('red', self.manager.term.red))
        self.assertNotEqual(counter._colorize('test'), 'test')
        self.assertEqual(counter._colorize('test'), self.manager.term.red('test'))

    def test_colorize_string_compound(self):
        """Return string formatted with compound color (string)"""
        counter = BaseCounter(manager=self.manager, color='bold_red_on_blue')
        self.assertEqual(counter.color, 'bold_red_on_blue')
        self.assertEqual(counter._color, ('bold_red_on_blue', self.manager.term.bold_red_on_blue))
        self.assertNotEqual(counter._colorize('test'), 'test')
        self.assertEqual(counter._colorize('test'), self.manager.term.bold_red_on_blue('test'))

    def test_colorize_int(self):
        """Return string formatted with color (int)"""
        counter = BaseCounter(manager=self.manager, color=40)
        self.assertEqual(counter.color, 40)
        self.assertEqual(counter._color, (40, self.manager.term.color(40)))
        self.assertNotEqual(counter._colorize('test'), 'test')
        self.assertEqual(counter._colorize('test'), self.manager.term.color(40)('test'))

    def test_colorize_rgb(self):
        """Return string formatted with color (RGB)"""
        counter = BaseCounter(manager=self.manager, color=(50, 40, 60))
        self.assertEqual(counter.color, (50, 40, 60))
        self.assertEqual(counter._color, ((50, 40, 60), self.manager.term.color_rgb(50, 40, 60)))
        self.assertNotEqual(counter._colorize('test'), 'test')
        self.assertEqual(counter._colorize('test'), self.manager.term.color_rgb(50, 40, 60)('test'))

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
