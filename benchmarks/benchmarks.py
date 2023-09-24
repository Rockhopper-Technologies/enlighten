# -*- coding: utf-8 -*-
# Copyright 2023 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Benchmark for base operations in order to compare between versions

For a basic comparison

asv run main^!
asv run branch^!
asv compare main branch

For more information see https://asv.readthedocs.io/en/stable/index.html

"""

from enlighten import get_manager


class TimeFormat:
    """
    Time-based benchmarks for format operations
    These are emphasized because they will have the greatest impact on end users
    """
    def setup(self):
        """
        General setup functions
        """

        # pylint: disable=attribute-defined-outside-init
        manager = get_manager(disable=True)
        self.pbar = manager.counter(total=1000)
        self.counter = manager.counter()
        self.sbar = manager.status_bar(status_format='Current Count: {num}', num=0)

    def time_format_bar(self):
        """
        Time Counter.format() for progress bar
        Count does not exceed total
        """

        pbar = self.pbar

        for _ in range(1000):
            pbar.update()
            pbar.format()

    def time_format_counter(self):
        """
        Time Counter.format() for counter
        Count exceeds total
        """

        pbar = self.pbar

        for _ in range(1000):
            pbar.update()
            pbar.format()

    def time_format_status_bar(self):
        """
        Time Counter.format() for status bar
        Uses dynamic variable
        """

        sbar = self.sbar

        for num in range(1000):
            sbar.update(num=num)
            sbar.format()
