# -*- coding: utf-8 -*-
# Copyright 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Test module for enlighten._notebook_manager
"""

import unittest

try:
    from nbconvert.preprocessors import ExecutePreprocessor
    import nbformat
    RUN_NOTEBOOK = True
except ImportError:
    RUN_NOTEBOOK = False

from tests import TestCase


def run_notebook(path):
    """
    Run a notebook at the given path
    The notebook's path is set to the current working directory
    """

    with open(path, encoding='utf-8') as notebook_file:
        notebook = nbformat.read(notebook_file, as_version=nbformat.NO_CONVERT)

    process = ExecutePreprocessor(timeout=60, allow_errors=True)
    process.preprocess(notebook, {})

    return notebook


def has_html_output(cell):
    """
    Check if cell has HTML output
    """

    for output in cell.get('outputs', []):
        if output.output_type == 'display_data':
            return 'text/html' in output['data']

    return False


@unittest.skipUnless(RUN_NOTEBOOK, 'Notebook testing packages not installed')
class TestNotebookManager(TestCase):
    """
    Tests for NotebookManager
    """
    maxDiff = None

    def test_notebook(self):
        """
        All the tests run in the notebook. This just runs it and checks for errors.
        """

        notebook = run_notebook('tests/test_notebook_manager.ipynb')

        # Make sure there are no errors
        for cell in notebook.cells:
            for output in cell.get('outputs', []):
                if output.output_type == 'stream' and output.name == 'stderr':
                    errors = ''.join(output.text)
                    print(errors)

                if output.output_type == 'error':
                    raise AssertionError(
                        '%s: %s\n%s' % (output.ename, output.evalue, '\n'.join(output.traceback))
                    )

                self.assertNotEqual(output.output_type, 'error')

        # Setup: should have no output
        self.assertFalse(notebook.cells[0].outputs)

        # test_get_manager: should have no output
        self.assertFalse(notebook.cells[1].outputs)

        # test_standard: should have output
        self.assertTrue(has_html_output(notebook.cells[2]), 'display_data not found in outputs')

        # # test_disabled: should have no output
        self.assertFalse(notebook.cells[3].outputs)

        # test_bare_no_flush: should have no output
        self.assertFalse(notebook.cells[4].outputs)

        # test_advanced: should have output
        self.assertTrue(has_html_output(notebook.cells[5]), 'display_data not found in outputs')

        # test_styles: should have output
        self.assertTrue(has_html_output(notebook.cells[6]), 'display_data not found in outputs')

        # Cleanup: should have no output
        self.assertFalse(notebook.cells[7].outputs)
