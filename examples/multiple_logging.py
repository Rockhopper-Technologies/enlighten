# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Multiple progress bars example
"""

import logging
import random
import time

import enlighten


logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger('enlighten')

SPLINES = 15
DATACENTERS = 5
SYSTEMS = (10, 50)  # Range
FILES = (100, 1000)  # Range


def process_files():
    """
    Process a random number of files on a random number of systems across multiple data centers
    """

    # Start with a manager
    manager = enlighten.get_manager()

    # Simulated preparation
    prep = manager.counter(total=SPLINES, desc='Reticulating:', unit='splines')
    for num in range(SPLINES):  # pylint: disable=unused-variable
        time.sleep(random.uniform(0.1, 0.5))  # Random processing time
        prep.update()
    prep.close()

    # Get a top level progress bar
    enterprise = manager.counter(total=DATACENTERS, desc='Processing:', unit='datacenters')

    # Iterate through data centers
    for dnum in range(1, DATACENTERS + 1):
        systems = random.randint(*SYSTEMS)  # Random number of systems
        # Get a child progress bar. leave is False so it can be replaced
        currCenter = manager.counter(total=systems, desc='  Datacenter %d:' % dnum,
                                     unit='systems', leave=False)

        # Iterate through systems
        for snum in range(1, systems + 1):

            # Has no total, so will act as counter. Leave is False
            system = manager.counter(desc='    System %d:' % snum, unit='files', leave=False)
            files = random.randint(*FILES)  # Random file count

            # Iterate through files
            for fnum in range(files):  # pylint: disable=unused-variable
                system.update()  # Update count
                time.sleep(random.uniform(0.0001, 0.0005))  # Random processing time

            system.close()  # Close counter so it gets removed
            # Log status
            LOGGER.info('Updated %d files on System %d in Datacenter %d', files, snum, dnum)
            currCenter.update()  # Update count

        currCenter.close()  # Close counter so it gets removed

        enterprise.update()  # Update count

    enterprise.close()  # Close counter, won't be removed but does a refresh

    manager.stop()  # Clears all temporary counters and progress bars


if __name__ == '__main__':

    process_files()
