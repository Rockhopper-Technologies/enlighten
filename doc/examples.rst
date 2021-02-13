..
  Copyright 2017 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten


Examples
========

Basic
-----

For a basic status bar, invoke the :py:class:`~enlighten.Counter` class directly.

.. code-block:: python

    import time
    import enlighten

    pbar = enlighten.Counter(total=100, desc='Basic', unit='ticks')
    for num in range(100):
        time.sleep(0.1)  # Simulate work
        pbar.update()

Advanced
--------

To maintain multiple progress bars simultaneously or write to the console, a manager is required.

Advanced output will only work when the output stream, :py:data:`sys.stdout` by default,
is attached to a TTY. :py:func:`~enlighten.get_manager` can be used to get a manager instance.
It will return a disabled :py:class:`~enlighten.Manager` instance if the stream is not attached to a TTY
and an enabled instance if it is.

.. code-block:: python

    import time
    import enlighten

    manager = enlighten.get_manager()
    ticks = manager.counter(total=100, desc='Ticks', unit='ticks')
    tocks = manager.counter(total=20, desc='Tocks', unit='tocks')

    for num in range(100):
        time.sleep(0.1)  # Simulate work
        print(num)
        ticks.update()
        if not num % 5:
            tocks.update()

    manager.stop()

Counters
--------

The :py:class:`~enlighten.Counter` class has two output formats, progress bar and counter.

The progress bar format is used when a total is not :py:data:`None` and the count is less than the
total. If neither of these conditions are met, the counter format is used:

.. code-block:: python

    import time
    import enlighten

    counter = enlighten.Counter(desc='Basic', unit='ticks')
    for num in range(100):
        time.sleep(0.1)  # Simulate work
        counter.update()

Status Bars
-----------
Status bars are bars that work similarly to progress similarly to progress bars and counters,
but present relatively static information.
Status bars are created with :py:meth:`Manager.status_bar <enlighten.Manager.status_bar>`.

.. code-block:: python

    import enlighten
    import time

    manager = enlighten.get_manager()
    status_bar = manager.status_bar('Static Message',
                                    color='white_on_red',
                                    justify=enlighten.Justify.CENTER)
    time.sleep(1)
    status_bar.update('Updated static message')
    time.sleep(1)

Status bars can also use formatting with dynamic variables.

.. code-block:: python

    import enlighten
    import time

    manager = enlighten.get_manager()
    status_format = '{program}{fill}Stage: {stage}{fill} Status {status}'
    status_bar = manager.status_bar(status_format=status_format,
                                    color='bold_slategray',
                                    program='Demo',
                                    stage='Loading',
                                    status='OKAY')
    time.sleep(1)
    status_bar.update(stage='Initializing', status='OKAY')
    time.sleep(1)
    status_bar.update(status='FAIL')

Status bars, like other bars can be pinned. To pin a status bar to the top of all other bars,
initialize it before any other bars. To pin a bar to the bottom of the screen, use
``position=1`` when initializing.

See :py:class:`~enlighten.StatusBar` for more details.

Color
-----

Status bars and the bar component of a progress bar can be colored by setting the
``color`` keyword argument. See :ref:`Series Color <series_color>` for more information
about valid colors.

.. code-block:: python

    import time
    import enlighten

    counter = enlighten.Counter(total=100, desc='Colorized', unit='ticks', color='red')
    for num in range(100):
        time.sleep(0.1)  # Simulate work
    counter.update()

Additionally, any part of the progress bar can be colored using counter
:ref:`formatting <counter_format>` and the
`color capabilities <https://blessed.readthedocs.io/en/stable/colors.html>`_
of the underlying `Blessed <https://blessed.readthedocs.io/en/stable>`_
`Terminal <https://blessed.readthedocs.io/en/stable/terminal.html>`_.

.. code-block:: python

    import enlighten

    manager = enlighten.get_manager()

    # Standard bar format
    std_bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
                     u'{count:{len_total}d}/{total:d} ' + \
                     u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

    # Red text
    bar_format = manager.term.red(std_bar_format)

    # Red on white background
    bar_format = manager.term.red_on_white(std_bar_format)

    # X11 colors
    bar_format = manager.term.peru_on_seagreen(std_bar_format)

    # RBG text
    bar_format = manager.term.color_rgb(2, 5, 128)(std_bar_format)

    # RBG background
    bar_format = manager.term.on_color_rgb(255, 190, 195)(std_bar_format)

    # RGB text and background
    bar_format = manager.term.on_color_rgb(255, 190, 195)(std_bar_format)
    bar_format = manager.term.color_rgb(2, 5, 128)(bar_format)

    # Apply color to select parts
    bar_format = manager.term.red(u'{desc}') + u'{desc_pad}' + \
                 manager.term.blue(u'{percentage:3.0f}%') + u'|{bar}|'

    # Apply to counter
    ticks = manager.counter(total=100, desc='Ticks', unit='ticks', bar_format=bar_format)

If the ``color`` option is applied to a :py:class:`~enlighten.Counter`,
it will override any foreground color applied.



Multicolored
------------

The bar component of a progress bar can be multicolored to track multiple categories in a single
progress bar.

The colors are drawn from right to left in the order they were added.

By default, when multicolored progress bars are used, additional fields are available for
``bar_format``:

    - count_n (:py:class:`int`) - Current value of ``count``
    - count_0(:py:class:`int`) - Remaining count after deducting counts for all subcounters
    - count_00 (:py:class:`int`) - Sum of counts from all subcounters
    - percentage_n (:py:class:`float`) - Percentage complete
    - percentage_0(:py:class:`float`) - Remaining percentage after deducting percentages
      for all subcounters
    - percentage_00 (:py:class:`float`) - Total of percentages from all subcounters

When :py:meth:`add_subcounter` is called with ``all_fields`` set to :py:data:`True`,
the subcounter will have the additional fields:

    - eta_n (:py:class:`str`) - Estimated time to completion
    - rate_n (:py:class:`float`) - Average increments per second since parent was created

More information about ``bar_format`` can be found in the
:ref:`Format <counter_format>` section of the API.

One use case for multicolored progress bars is recording the status of a series of tests.
In this example, Failures are red, errors are white, and successes are green. The count of each is
listed in the progress bar.

.. code-block:: python

    import random
    import time
    import enlighten

    bar_format = u'{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' + \
                u'S:{count_0:{len_total}d} ' + \
                u'F:{count_2:{len_total}d} ' + \
                u'E:{count_1:{len_total}d} ' + \
                u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'

    success = enlighten.Counter(total=100, desc='Testing', unit='tests',
                                color='green', bar_format=bar_format)
    errors = success.add_subcounter('white')
    failures = success.add_subcounter('red')

    while success.count < 100:
        time.sleep(random.uniform(0.1, 0.3))  # Random processing time
        result = random.randint(0, 10)

        if result == 7:
            errors.update()
        if result in (5, 6):
            failures.update()
        else:
            success.update()

A more complicated example is recording process start-up. In this case, all items will start red,
transition to yellow, and eventually all will be green. The count, percentage, rate, and eta fields
are all derived from the second subcounter added.

.. code-block:: python

    import random
    import time
    import enlighten

    services = 100
    bar_format = u'{desc}{desc_pad}{percentage_2:3.0f}%|{bar}|' + \
                u' {count_2:{len_total}d}/{total:d} ' + \
                u'[{elapsed}<{eta_2}, {rate_2:.2f}{unit_pad}{unit}/s]'

    initializing = enlighten.Counter(total=services, desc='Starting', unit='services',
                                    color='red', bar_format=bar_format)
    starting = initializing.add_subcounter('yellow')
    started = initializing.add_subcounter('green', all_fields=True)

    while started.count < services:
        remaining = services - initializing.count
        if remaining:
            num = random.randint(0, min(4, remaining))
            initializing.update(num)

        ready = initializing.count - initializing.subcount
        if ready:
            num = random.randint(0, min(3, ready))
            starting.update_from(initializing, num)

        if starting.count:
            num = random.randint(0, min(2, starting.count))
            started.update_from(starting, num)

        time.sleep(random.uniform(0.1, 0.5))  # Random processing time


Additional Examples
-------------------

* :download:`basic <../examples/basic.py>` - Basic progress bar
* :download:`context manager <../examples/context_manager.py>` - Managers and counters as context managers
* :download:`floats <../examples/floats.py>` - Support totals and counts that are :py:class:`floats<float>`
* :download:`multicolored <../examples/multicolored.py>` - Multicolored progress bars
* :download:`multiple with logging <../examples/multiple_logging.py>` - Nested progress bars and logging
* :download:`FTP downloader <../examples/ftp_downloader.py>` - Show progress downloading files from FTP
* :download:`Multiprocessing queues <../examples/multiprocessing_queues.py>` - Progress bars with queues for IPC

Customization
-------------

Enlighten is highly configurable. For information on modifying the output, see the
:ref:`Series <series>` and :ref:`Format <counter_format>`
sections of the :py:class:`~enlighten.Counter` documentation.
