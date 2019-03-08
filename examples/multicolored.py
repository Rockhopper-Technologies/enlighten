# Copyright 2019 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Multicolored progress bar example
"""

import logging
import random
import time

import enlighten

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("enlighten")

BAR_FMT = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
          u'S:{count_0:{len_total}d} F:{count_1:{len_total}d} E:{count_2:{len_total}d} ' + \
          u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

BAR_FMT2 = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| {count:{len_total}d}/{total:d} ' + \
          u'[{elapsed}<{eta_2}, {rate_2:.2f}{unit_pad}{unit}/s]'

MANAGER = enlighten.get_manager()


def run_tests(tests=100):
    """
    Simulate a test program
    Tests will error (white), fail (red), or succeed (green)
    """

    with MANAGER.counter(total=tests, desc='Testing', unit='tests',
                         color='green', bar_format=BAR_FMT) as success:
        errors = success.add_subcounter('white')
        failures = success.add_subcounter('red')

        for num in range(tests):
            time.sleep(random.uniform(0.1, 0.5))  # Random processing time
            result = random.randint(0, 10)
            if result == 7:
                LOGGER.error("Test %d did not complete", num)
                errors.update()
            elif result in (5, 6):
                LOGGER.error("Test %d failed", num)
                failures.update()
            else:
                LOGGER.info("Test %d passed", num)
                success.update()


def startup(services=88):
    """
    Simulate system starting
    Services go through initialization (red), starting (yellow), and started (green) states
    in that order
    """

    initialized = MANAGER.counter(total=services, desc='Starting', unit='services',
                                  color='red', bar_format=BAR_FMT2)
    starting = initialized.add_subcounter('yellow')
    started = initialized.add_subcounter('green', all_fields=True)

    while started.count < services:
        remaining = services - initialized.count
        if initialized.count < services:
            num = random.randint(0, min(3, remaining))
            print('Initializing %d services' % num)
            initialized.update(num)

        ready = initialized.count - starting.count - started.count
        if ready:
            num = random.randint(0, min(3, ready))
            print('Starting %d services' % num)
            starting.update_from(initialized, num)

        if starting.count:
            num = random.randint(0, min(3, starting.count))
            print('Started %d services' % num)
            started.update_from(starting, num)

        time.sleep(random.uniform(0.1, 0.5))  # Random processing time

    initialized.close()


if __name__ == "__main__":
    run_tests(100)
    startup(80)
