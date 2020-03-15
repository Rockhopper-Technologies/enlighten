#!/usr/bin/env python
# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Enlighten Progress Bar is console progress bar module for Python. (Yes, another one.)
The main advantage of Enlighten is it allows writing to stdout and stderr without any
redirection.
"""

import os

from setuptools import setup, find_packages

from setup_helpers import get_version, readme

INSTALL_REQUIRES = ['blessed>=1.17.2']
TESTS_REQUIRE = ['mock; python_version < "3.3"',
                 'unittest2; python_version < "2.7"']

# Additional requirements
# html requires sphinx, sphinx_rtd_theme
# spelling requires sphinxcontrib-spelling

setup(
    name='enlighten',
    version=get_version(os.path.join('enlighten', '__init__.py')),
    description='Enlighten Progress Bar',
    long_description=readme('README.rst'),
    author='Avram Lubkin',
    author_email='avylove@rockhopper.net',
    maintainer='Avram Lubkin',
    maintainer_email='avylove@rockhopper.net',
    url='https://github.com/Rockhopper-Technologies/enlighten',
    project_urls={'Documentation': 'https://python-enlighten.readthedocs.io'},
    license='MPLv2.0',
    zip_safe=False,
    install_requires=INSTALL_REQUIRES,
    tests_require=TESTS_REQUIRE,
    packages=find_packages(exclude=['tests', 'tests.*', 'examples']),
    test_suite='tests',

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)',
        'Operating System :: POSIX',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Utilities',
    ],
    keywords='progress, bar, progressbar, counter, status, statusbar',
)
