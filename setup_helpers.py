# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Functions to help with build and setup
"""

import io
import os
import re
import sys


RE_VERSION = re.compile(r'__version__\s*=\s*[\'\"](.+)[\'\"]$')


def get_version(filename, encoding='utf8'):
    """
    Get __version__ definition out of a source file
    """

    with io.open(filename, encoding=encoding) as sourcecode:
        for line in sourcecode:
            version = RE_VERSION.match(line)
            if version:
                return version.group(1)

    return None


def readme(filename, encoding='utf8'):
    """
    Read the contents of a file
    """

    with io.open(filename, encoding=encoding) as source:
        return source.read()


def print_spelling_errors(filename, encoding='utf8'):
    """
    Print misspelled words returned by sphinxcontrib-spelling
    """

    filesize = os.stat(filename).st_size
    if filesize:
        sys.stdout.write('Misspelled Words:\n')
        with io.open(filename, encoding=encoding) as wordlist:
            for line in wordlist:
                sys.stdout.write('    ' + line)

    return 1 if filesize else 0


if __name__ == '__main__':

    # Do nothing if no arguments were given
    if len(sys.argv) < 2:
        sys.exit(0)

    # Print misspelled word list
    if sys.argv[1] == 'spelling':
        if len(sys.argv) > 2:
            sys.exit(print_spelling_errors(sys.argv[2]))
        else:
            sys.exit(print_spelling_errors('build/doc/spelling/output.txt'))

    # Unknown option
    else:
        sys.stderr.write('Unknown option: %s' % sys.argv[1])
        sys.exit(1)
