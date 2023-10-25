# Copyright 2019 - 2023 Avram Lubkin, All Rights Reserved

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Example of using Enlighten with multiprocessing

This example uses queues for inter-process communication (IPC)
"""

from multiprocessing import Process, Queue
import random
import time

import enlighten


WORKERS = 4
SYSTEMS = (10, 20)
FILES = (100, 200)
FILE_TIME = (0.01, 0.05)
ERROR_VALUES = (4, )  # 1 - 10, each number is ~10% chance of error


def process_files(queue, count):
    """
    Simple child processor

    Sleeps for a random interval and pushes the current count onto the queue
    """

    for num in range(1, count + 1):
        time.sleep(random.uniform(*FILE_TIME))  # Random processing time
        queue.put(num)

    if random.randint(1, 10) in ERROR_VALUES:
        raise RuntimeError("Simulated Error: I don't think we're in Kansas anymore")


def multiprocess_systems(manager, systems):
    """
    Process a random number of virtual files in subprocesses for the given number of systems
    """

    started = 0
    active = {}
    bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
                 u'S:' + manager.term.yellow2(u'{count_0:{len_total}d}') + u' ' + \
                 u'F:' + manager.term.green3(u'{count_1:{len_total}d}') + u' ' + \
                 u'E:' + manager.term.red2(u'{count_2:{len_total}d}') + u' ' + \
                 u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

    pb_started = manager.counter(
        total=systems, desc='Systems:', unit='systems', color='yellow2', bar_format=bar_format,
    )
    pb_finished = pb_started.add_subcounter('green3', all_fields=True)
    pb_error = pb_started.add_subcounter('red2', all_fields=True)

    # Loop until all systems finish
    while systems > started or active:

        # If there are free workers and tasks left to run, start them
        if systems > started and len(active) < WORKERS:
            queue = Queue()
            files = random.randint(*FILES)
            started += 1
            process = Process(target=process_files, name='System %d' % started, args=(queue, files))
            counter = manager.counter(total=files, desc='  System %d:' % started,
                                      unit='files', leave=False)
            process.start()
            pb_started.update()
            active[started] = (process, queue, counter)

        # Iterate through active subprocesses
        for system in tuple(active.keys()):
            process, queue, counter = active[system]
            alive = process.is_alive()

            # Latest count is the last one on the queue
            count = None
            while not queue.empty():
                count = queue.get()

            # Update counter
            if count is not None:
                counter.update(count - counter.count)

            # Remove any finished subprocesses and update main progress bar
            if not alive:
                counter.close()
                print('Processed %d files on System %d' % (counter.total, system))
                del active[system]

                # Check for failures
                if process.exitcode != 0:
                    print('ERROR: Receive exitcode %d while processing System %d'
                          % (process.exitcode, system))
                    pb_error.update_from(pb_started)
                else:
                    pb_finished.update_from(pb_started)

        # Sleep for 1/10 of a second to reduce load
        time.sleep(0.1)


def main():
    """
    Main function
    """

    with enlighten.get_manager() as manager:
        multiprocess_systems(manager, random.randint(*SYSTEMS))


if __name__ == '__main__':
    main()
