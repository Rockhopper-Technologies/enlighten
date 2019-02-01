# Copyright 2017 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Multiple progress bars example
"""

import logging
import random
import sys
import time

import enlighten

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger("enlighten")

TESTS = 100


def complete_tests(pbar):
    print(pbar)
    for num in range(TESTS):  # pylint: disable=unused-variable
        time.sleep(random.uniform(0.1, 0.5))  # Random processing time
        test_result = random.choices(["passed", "failed", None], weights=[50, 10, 1])[0]
        if test_result in ["passed", "failed"]:
            LOGGER.info("Test {test_result}".format(test_result=test_result))
        if test_result is None:
            LOGGER.info("Test completed but result is unclear.")
        pbar.update(subcount=test_result)


def run_tests():
    with enlighten.get_manager(counter_class=enlighten.MultiCounter) as manager, \
        manager.counter(
            total=TESTS,
            desc="Completed",
            unit="Tests",
            subcounts=[("failed", "red"), ("passed", "green")],
        ) as pbar:
        complete_tests(pbar)


if __name__ == "__main__":
    run_tests()
