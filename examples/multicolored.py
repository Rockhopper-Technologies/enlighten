# Copyright 2019 - 2021 Avram Lubkin, All Rights Reserved

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

BAR_FMT = u'{desc}{desc_pad}{percentage_2:3.0f}%|{bar}| {count_2:{len_total}d}/{total:d} ' + \
          u'[{elapsed}<{eta_2}, {rate_2:.2f}{unit_pad}{unit}/s]'


class Node(object):
    """
    Simulated service node
    """

    def __init__(self, iden):
        self.iden = iden
        self._connected = None
        self._loaded = None

    def connect(self):
        """
        Connect to node
        """

        self._connected = False

    def load(self):
        """
        Load service
        """

        self._loaded = False

    @property
    def connected(self):
        """
        Connected state
        """

        return self._state('_connected', 3)

    @property
    def loaded(self):
        """
        Loaded state
        """

        return self._state('_loaded', 5)

    def _state(self, variable, num):
        """
        Generic method to randomly determine if state is reached
        """

        value = getattr(self, variable)

        if value is None:
            return False

        if value is True:
            return True

        if random.randint(1, num) == num:
            setattr(self, variable, True)
            return True

        return False


def run_tests(manager, tests=100):
    """
    Simulate a test program
    Tests will error (yellow), fail (red), or succeed (green)
    """

    terminal = manager.term
    bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
                 u'S:' + terminal.green3(u'{count_0:{len_total}d}') + u' ' + \
                 u'F:' + terminal.red2(u'{count_2:{len_total}d}') + u' ' + \
                 u'E:' + terminal.yellow2(u'{count_1:{len_total}d}') + u' ' + \
                 u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

    with manager.counter(total=tests, desc='Testing', unit='tests', color='green3',
                         bar_format=bar_format) as success:
        errors = success.add_subcounter('yellow2')
        failures = success.add_subcounter('red2')

        for num in range(tests):
            time.sleep(random.uniform(0.1, 0.3))  # Random processing time
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


def load(manager, units=80):
    """
    Simulate loading services from a remote node
    States are connecting (red), loading (yellow), and loaded (green)
    """

    pb_connecting = manager.counter(total=units, desc='Loading', unit='services',
                                    color='red2', bar_format=BAR_FMT)
    pb_loading = pb_connecting.add_subcounter('yellow2')
    pb_loaded = pb_connecting.add_subcounter('green3', all_fields=True)

    connecting = []
    loading = []
    loaded = []
    count = 0

    while pb_loaded.count < units:
        time.sleep(random.uniform(0.05, 0.15))  # Random processing time

        for idx, node in enumerate(loading):
            if node.loaded:
                loading.pop(idx)
                loaded.append(node)
                LOGGER.info('Service %d loaded', node.iden)
                pb_loaded.update_from(pb_loading)

        for idx, node in enumerate(connecting):
            if node.connected:
                connecting.pop(idx)
                node.load()
                loading.append(node)
                LOGGER.info('Service %d connected', node.iden)
                pb_loading.update_from(pb_connecting)

        # Connect to up to 5 units at a time
        for _ in range(min(units - count, 5 - len(connecting))):
            node = Node(count)
            node.connect()
            connecting.append(node)
            LOGGER.info('Connection to service %d', node.iden)
            pb_connecting.update()
            count += 1


def main():
    """
    Main function
    """

    manager = enlighten.get_manager()
    run_tests(manager, 100)
    load(manager, 80)


if __name__ == "__main__":
    main()
