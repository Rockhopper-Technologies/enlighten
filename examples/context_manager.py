# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Progress bar example with context managers
"""
import random
import time

import enlighten

SPLINES = 15
LLAMAS = 20


def process_files():
    """
    Use Manager and Counter as context managers
    """

    with enlighten.Manager() as manager:
        with manager.counter(total=SPLINES, desc='Reticulating:', unit='splines') as retic:
            for num in range(SPLINES):  # pylint: disable=unused-variable
                time.sleep(random.uniform(0.1, 0.5))  # Random processing time
                retic.update()

        with manager.counter(total=LLAMAS, desc='Herding:', unit='llamas') as herd:
            for num in range(SPLINES):  # pylint: disable=unused-variable
                time.sleep(random.uniform(0.1, 0.5))  # Random processing time
                herd.update()


if __name__ == '__main__':

    process_files()
