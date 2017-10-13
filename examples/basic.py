# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Basic progress bar example
"""

import time

import enlighten


def process_files():
    """
    Process files with a single progress bar
    """

    with enlighten.Counter(total=100, desc='Simple', unit='ticks') as pbar:
        for num in range(100):  # pylint: disable=unused-variable
            time.sleep(0.05)
            pbar.update()


if __name__ == '__main__':

    process_files()
