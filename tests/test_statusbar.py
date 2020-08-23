# -*- coding: utf-8 -*-
# Copyright 2017 - 2020 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._statusbar
"""

from enlighten import EnlightenWarning, Justify

import tests
from tests import TestCase, MockManager, MockTTY, MockStatusBar, PY2, unittest


class TestStatusBar(TestCase):
    """
    Test the StatusBar class
    """

    def setUp(self):
        self.tty = MockTTY()
        self.manager = MockManager(stream=self.tty.stdout)

    def tearDown(self):
        self.tty.close()

    def test_static(self):
        """
        Basic static status bar
        """

        sbar = self.manager.status_bar('Hello', 'World!')
        self.assertEqual(sbar.format(), 'Hello World!' + ' ' * 68)

        sbar.update('Goodbye, World!')
        self.assertEqual(sbar.format(), 'Goodbye, World!' + ' ' * 65)

    def test_static_justify(self):
        """
        Justified static status bar
        """

        sbar = self.manager.status_bar('Hello', 'World!', justify=Justify.LEFT)
        self.assertEqual(sbar.format(), 'Hello World!' + ' ' * 68)

        sbar = self.manager.status_bar('Hello', 'World!', justify=Justify.RIGHT)
        self.assertEqual(sbar.format(), ' ' * 68 + 'Hello World!')

        sbar = self.manager.status_bar('Hello', 'World!', justify=Justify.CENTER)
        self.assertEqual(sbar.format(), ' ' * 34 + 'Hello World!' + ' ' * 34)

    def test_formatted(self):
        """
        Basic formatted status bar
        """

        sbar = self.manager.status_bar(status_format=u'Stage: {stage}, Status: {status}', stage=1,
                                       fields={'status': 'All good!'})
        self.assertEqual(sbar.format(), 'Stage: 1, Status: All good!' + ' ' * 53)
        sbar.update(stage=2)
        self.assertEqual(sbar.format(), 'Stage: 2, Status: All good!' + ' ' * 53)
        sbar.update(stage=3, status='Meh')
        self.assertEqual(sbar.format(), 'Stage: 3, Status: Meh' + ' ' * 59)

    def test_formatted_justify(self):
        """
        Justified formatted status bar
        """

        sbar = self.manager.status_bar(status_format=u'Stage: {stage}, Status: {status}', stage=1,
                                       fields={'status': 'All good!'}, justify=Justify.LEFT)
        self.assertEqual(sbar.format(), 'Stage: 1, Status: All good!' + ' ' * 53)

        sbar = self.manager.status_bar(status_format=u'Stage: {stage}, Status: {status}', stage=1,
                                       fields={'status': 'All good!'}, justify=Justify.RIGHT)
        self.assertEqual(sbar.format(), ' ' * 53 + 'Stage: 1, Status: All good!')

        sbar = self.manager.status_bar(status_format=u'Stage: {stage}, Status: {status}', stage=1,
                                       fields={'status': 'All good'}, justify=Justify.CENTER)
        self.assertEqual(sbar.format(), ' ' * 27 + 'Stage: 1, Status: All good' + ' ' * 27)

    def test_formatted_missing_field(self):
        """
        ValueError raised when a field is missing when updating status bar
        """

        fields = {'status': 'All good!'}
        sbar = self.manager.status_bar(status_format=u'Stage: {stage}, Status: {status}', stage=1,
                                       fields=fields)
        del fields['status']

        sbar.last_update = sbar.start - 5.0
        with self.assertRaisesRegex(ValueError, "'status' specified in format, but not provided"):
            sbar.update()

    def test_bad_justify(self):
        """
        ValueError raised when justify is given an invalid value
        """

        with self.assertRaisesRegex(ValueError, 'justify must be one of Justify.LEFT, '):
            self.manager.status_bar('Hello', 'World!', justify='justice')

    def test_update(self):
        """
        update() does not refresh is bar is disabled or min_delta hasn't passed
        """

        self.manager.status_bar_class = MockStatusBar
        sbar = self.manager.status_bar('Hello', 'World!')

        self.assertEqual(sbar.called, 1)
        sbar.last_update = sbar.start - 1.0
        sbar.update()
        self.assertEqual(sbar.called, 2)

        sbar.last_update = sbar.start + 5.0
        sbar.update()
        self.assertEqual(sbar.called, 2)

        sbar.last_update = sbar.last_update - 10.0
        sbar.enabled = False
        sbar.update()
        self.assertEqual(sbar.called, 2)

        sbar.enabled = True
        sbar.update()
        self.assertEqual(sbar.called, 3)

    def test_fill(self):
        """
        Fill uses remaining space
        """

        sbar = self.manager.status_bar(status_format=u'{fill}HI', fill='-')
        self.assertEqual(sbar.format(), u'-' * 78 + 'HI')

        sbar = self.manager.status_bar(status_format=u'{fill}HI{fill}', fill='-')
        self.assertEqual(sbar.format(), u'-' * 39 + 'HI' + u'-' * 39)

    def test_fill_uneven(self):
        """
        Extra fill should be equal
        """

        sbar = self.manager.status_bar(
            status_format=u'{fill}Helloooo!{fill}Woooorld!{fill}', fill='-'
        )
        self.assertEqual(sbar.format(),
                         u'-' * 20 + 'Helloooo!' + u'-' * 21 + 'Woooorld!' + u'-' * 21)

    @unittest.skipIf(PY2, 'Skip warnings tests in Python 2')
    def test_reserve_fields(self):
        """
        When reserved fields are used, a warning is raised
        """

        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            self.manager.status_bar(status_format=u'Stage: {stage}, Fill: {fill}', stage=1,
                                    fields={'fill': 'Reserved field'})
        self.assertRegex(tests.__file__, warn.filename)

        with self.assertWarnsRegex(EnlightenWarning, 'Ignoring reserved fields') as warn:
            self.manager.status_bar(status_format=u'Stage: {stage}, elapsed: {elapsed}', stage=1,
                                    elapsed='Reserved field')
        self.assertRegex(tests.__file__, warn.filename)
