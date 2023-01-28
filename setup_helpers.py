# Copyright 2017 - 2023 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Functions to help with build and setup
"""

import datetime
import io
import os
import re
import subprocess
import sys


RE_VERSION = re.compile(r'__version__\s*=\s*[\'\"](.+)[\'\"]$')
DIR_SPELLING = 'build/doc/spelling/'


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
    try:
        filesize = os.stat(filename).st_size
    except FileNotFoundError:
        filesize = 0

    if filesize:
        sys.stdout.write('Misspelled Words:\n')
        with io.open(filename, encoding=encoding) as wordlist:
            for line in wordlist:
                sys.stdout.write('    ' + line)

    return 1 if filesize else 0


def print_all_spelling_errors(path):
    """
    Print all spelling errors in the path
    """

    rtn = 0
    for filename in os.listdir(path):
        if print_spelling_errors(os.path.join(path, filename)):
            rtn = 1

    return rtn


def spelling_clean_dir(path):
    """
    Remove spelling files from path
    """
    if not os.path.isdir(path):
        return
    for filename in os.listdir(path):
        os.unlink(os.path.join(path, filename))


def check_rst2html(path):
    """
    Checks for warnings when doing ReST to HTML conversion
    """

    # pylint: disable=import-error,import-outside-toplevel
    from contextlib import redirect_stderr  # Import here because it breaks <= Python 3.4
    from docutils.core import publish_file  # Import here because only available in doc tests

    stderr = io.StringIO()

    # This will exit with status if there is a bad enough error
    with redirect_stderr(stderr):
        output = publish_file(source_path=path, writer_name='html',
                              enable_exit_status=True, destination_path='/dev/null')

    warning_text = stderr.getvalue()

    if warning_text or not output:
        print(warning_text)
        return 1

    return 0


def _get_changed_files():
    """
    Get files in current repository that have been changed
    Ignore changes to copyright lines
    """

    changed = []

    # Get list of changed files
    process = subprocess.run(
        ('git', 'status', '--porcelain=1'), stdout=subprocess.PIPE, check=True, text=True
    )
    for entry in process.stdout.splitlines():

        # Ignore deleted files
        if entry[1] == 'D':
            continue

        # Construct diff command
        filename = entry[3:].strip()
        diff_cmd = ['git', 'diff', filename]
        if entry[0].strip():
            diff_cmd.insert(-1, '--cached')

        # Find files with changes that aren't only for copyright
        process = subprocess.run(diff_cmd, stdout=subprocess.PIPE, check=True, text=True)
        for line in process.stdout.splitlines():
            if line[0] != '+' or line[:3] == '+++':  # Ignore everything but the new contents
                continue

            if re.search(r'copyright.*20\d\d', line, re.IGNORECASE):  # Ignore copyright line
                continue

            changed.append(filename)
            break

    return changed


def check_copyrights():
    """
    Check files recursively to ensure year of last change is in copyright line
    """

    this_year = str(datetime.date.today().year)
    changed_now = _get_changed_files()

    # Look for copyright lines
    process = subprocess.run(
        ('git', 'grep', '-i', 'copyright'), stdout=subprocess.PIPE, check=True, text=True
    )

    rtn = 0
    for entry in process.stdout.splitlines():

        modified = None

        # Get the year in the copyright line
        filename, text = entry.split(':', 1)
        match = re.match(r'.*(20\d\d)', text)
        if match:
            year = match.group(1)

            # If file is in current changes, use this year
            if filename in changed_now:
                modified = this_year

            # Otherwise, try to get the year of last commit that wasn't only updating copyright
            else:
                git_log = subprocess.run(
                    ('git', '--no-pager', 'log', '-U0', filename),
                    stdout=subprocess.PIPE, check=True, text=True
                )

                for line in git_log.stdout.splitlines():

                    # Get year
                    if line.startswith('Date: '):
                        modified = line.split()[5]

                    # Skip blank line and lines that aren't changes
                    if not line.strip() or line[0] != '+' or line[:3] == '+++':
                        continue

                    # Stop looking on the first line we hit that isn't a copyright
                    if re.search(r'copyright.*20\d\d', line, re.IGNORECASE) is None:
                        break

            # Special case for Sphinx configuration
            if filename == 'doc/conf.py' and modified != this_year:

                # Get the latest change date for docs
                process = subprocess.run(
                    ('git', 'log', '-1', '--pretty=format:%cs', 'doc/*.rst'),
                    stdout=subprocess.PIPE, check=True, text=True
                )
                modified = process.stdout[:4]

            # Compare modified date to copyright year
            if modified and modified != year:
                rtn = 1
                print('%s: %s [%s]' % (filename, text, modified))

    return rtn


if __name__ == '__main__':

    # Do nothing if no arguments were given
    if len(sys.argv) < 2:
        sys.exit(0)

    # Print misspelled word list
    if sys.argv[1] == 'spelling-clean':
        spelling_clean_dir(DIR_SPELLING)
        sys.exit(0)

    # Print misspelled word list
    if sys.argv[1] == 'spelling':
        if len(sys.argv) > 2:
            sys.exit(print_spelling_errors(sys.argv[2]))
        else:
            sys.exit(print_all_spelling_errors(DIR_SPELLING))

    # Check file for Rest to HTML conversion
    if sys.argv[1] == 'rst2html':
        if len(sys.argv) < 3:
            sys.exit('Missing filename for ReST to HTML check')
        sys.exit(check_rst2html(sys.argv[2]))

    # Print misspelled word list
    if sys.argv[1] == 'copyright':
        sys.exit(check_copyrights())

    # Unknown option
    else:
        sys.stderr.write('Unknown option: %s' % sys.argv[1])
        sys.exit(1)
