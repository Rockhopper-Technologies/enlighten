# Copyright 2020 - 2021 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Progress bar using binary prefixes
"""

import time
import random

import enlighten

# 64k chunk size
CHUNK_SIZE = 64 * 1024

BAR_FORMAT = '{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:!.2j}{unit} / {total:!.2j}{unit} ' \
             '[{elapsed}<{eta}, {rate:!.2j}{unit}/s]'


def download(manager, size):
    """
    Simulate a download
    """

    pbar = manager.counter(total=size, desc='Downloading',
                           unit='B', bar_format=BAR_FORMAT, color='purple')

    bytes_left = size
    while bytes_left:
        time.sleep(random.uniform(0.05, 0.15))
        next_chunk = min(CHUNK_SIZE, bytes_left)
        pbar.update(next_chunk)
        bytes_left -= next_chunk


if __name__ == '__main__':

    with enlighten.get_manager() as mgr:

        # 1 - 10 MB file size
        total = random.uniform(1.0, 10.0) * 2 ** 20
        download(mgr, total)
