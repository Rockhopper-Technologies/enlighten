# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Basic progress bar example
"""

from __future__ import print_function

import time

import enlighten

# Use float formatting for count and total in bar_format
BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}.1f}/{total:.1f} ' + \
          u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

COUNTER_FMT = u'{desc}{desc_pad}{count:.1f} {unit}{unit_pad}' + \
              u'[{elapsed}, {rate:.2f}{unit_pad}{unit}/s]{fill}'


def process_files(count=None):
    """
    Process files with a single progress bar
    """

    pbar = enlighten.Counter(total=count, desc='Simple', unit='ticks',
                             bar_format=BAR_FMT, counter_format=COUNTER_FMT)

    for _ in range(100):
        time.sleep(0.05)
        pbar.update(1.1)


if __name__ == '__main__':

    # Progress bar
    process_files(110.0)

    print()

    # No total, so we just get a counter
    process_files()
