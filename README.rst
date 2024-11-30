.. start-badges

| |docs| |gh_actions| |codecov|
| |linux| |windows| |mac| |bsd|
| |pypi| |supported-versions| |supported-implementations|
| |Fedora| |EPEL| |Debian| |Ubuntu| |Anaconda|
| |Python-Bytes|

.. |docs| image:: https://img.shields.io/readthedocs/python-enlighten.svg?style=plastic&logo=read-the-docs
    :target: https://python-enlighten.readthedocs.org
    :alt: Documentation Status

.. |gh_actions| image:: https://img.shields.io/github/actions/workflow/status/Rockhopper-Technologies/enlighten/tests.yml?event=push&logo=github-actions&style=plastic
    :target: https://github.com/Rockhopper-Technologies/enlighten/actions/workflows/tests.yml
    :alt: GitHub Actions Status

.. |travis| image:: https://img.shields.io/travis/com/Rockhopper-Technologies/enlighten.svg?style=plastic&logo=travis
    :target: https://travis-ci.com/Rockhopper-Technologies/enlighten
    :alt: Travis-CI Build Status

.. |codecov| image:: https://img.shields.io/codecov/c/github/Rockhopper-Technologies/enlighten.svg?style=plastic&logo=codecov
    :target: https://codecov.io/gh/Rockhopper-Technologies/enlighten
    :alt: Coverage Status

.. |pypi| image:: https://img.shields.io/pypi/v/enlighten.svg?style=plastic&logo=pypi
    :alt: PyPI Package latest release
    :target: https://pypi.python.org/pypi/enlighten

.. |supported-versions| image:: https://img.shields.io/pypi/pyversions/enlighten.svg?style=plastic&logo=pypi
    :alt: Supported versions
    :target: https://pypi.python.org/pypi/enlighten

.. |supported-implementations| image:: https://img.shields.io/pypi/implementation/enlighten.svg?style=plastic&logo=pypi
    :alt: Supported implementations
    :target: https://pypi.python.org/pypi/enlighten

.. |linux| image:: https://img.shields.io/badge/Linux-yes-success?style=plastic&logo=linux
    :alt: Linux supported
    :target: https://pypi.python.org/pypi/enlighten

.. |windows| image:: https://img.shields.io/badge/Windows-yes-success?style=plastic&logo=windows
    :alt: Windows supported
    :target: https://pypi.python.org/pypi/enlighten

.. |mac| image:: https://img.shields.io/badge/MacOS-yes-success?style=plastic&logo=apple
    :alt: MacOS supported
    :target: https://pypi.python.org/pypi/enlighten

.. |bsd| image:: https://img.shields.io/badge/BSD-yes-success?style=plastic&logo=freebsd
    :alt: BSD supported
    :target: https://pypi.python.org/pypi/enlighten

.. |Fedora| image:: https://img.shields.io/fedora/v/python3-enlighten?color=lightgray&logo=Fedora&style=plastic&label=Fedora
    :alt: Latest Fedora Version
    :target: https://src.fedoraproject.org/rpms/python-enlighten

.. |EPEL| image:: https://img.shields.io/fedora/v/python3-enlighten/epel9?color=lightgray&label=EPEL&logo=EPEL
    :alt: Latest EPEL Version
    :target: https://src.fedoraproject.org/rpms/python-enlighten

.. |Debian| image:: https://img.shields.io/debian/v/enlighten/sid?color=lightgray&logo=Debian&style=plastic&label=Debian
    :alt: Latest Debian Version
    :target: https://packages.debian.org/source/sid/enlighten

.. |Ubuntu| image:: https://img.shields.io/ubuntu/v/enlighten?color=lightgray&logo=Ubuntu&style=plastic&label=Ubuntu
    :alt: Latest Ubuntu Version
    :target: https://launchpad.net/ubuntu/+source/enlighten

.. |Anaconda| image:: https://img.shields.io/conda/vn/conda-forge/enlighten?color=lightgrey&label=Anaconda&logo=Conda%20Forge&style=plastic
    :alt: Latest Conda Forge Version
    :target: https://anaconda.org/conda-forge/enlighten

.. |Python-Bytes| image:: https://img.shields.io/badge/Python_Bytes_Podcast-Episode_184-D7F9FF?logo=podcastindex&labelColor=blue&style=plastic
    :alt: Featured on Python Bytes
    :target: https://pythonbytes.fm/episodes/show/184/too-many-ways-to-wait-with-await

.. end-badges

Overview
========

Enlighten Progress Bar is a console progress bar library for Python.

The main advantage of Enlighten is it allows writing to stdout and stderr without any
redirection or additional code. Just print or log as you normally would.

Enlighten also includes experimental support for Jupyter Notebooks.

|

.. image:: https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/doc/_static/demo.gif
    :target: http://python-enlighten.readthedocs.io/en/stable/examples.html

The code for this animation can be found in
`demo.py <https://github.com/Rockhopper-Technologies/enlighten/blob/master/examples/demo.py>`__
in
`examples <https://github.com/Rockhopper-Technologies/enlighten/tree/master/examples>`__.

Documentation
=============

https://python-enlighten.readthedocs.io

Installation
============

PIP
---

.. code-block:: console

    $ pip install enlighten


RPM
---

Fedora and EL8 (RHEL/CentOS)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(For EPEL_ repositories must be configured_)

.. code-block:: console

    $ dnf install python3-enlighten


DEB
---

Debian and Ubuntu
^^^^^^^^^^^^^^^^^
.. code-block:: console

    $ apt-get install python3-enlighten


Conda
-----

.. code-block:: console

    $ conda install -c conda-forge enlighten


.. _EPEL: https://fedoraproject.org/wiki/EPEL
.. _configured: https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F


How to Use
==========

Managers
--------

The first step is to create a manager. Managers handle output to the terminal and allow multiple
progress bars to be displayed at the same time.

get_manager_ can be used to get a Manager_ instance.
Managers will only display output when the output stream, ``sys.__stdout__`` by default,
is attached to a TTY. If the stream is not attached to a TTY, the manager instance returned will be
disabled.

In most cases, a manager can be created like this.

.. code-block:: python

    import enlighten
    manager = enlighten.get_manager()

If you need to use a different output stream, or override the defaults, see the documentation for
get_manager_


Progress Bars
-------------

For a basic progress bar, invoke the Manager.counter_ method.

.. code-block:: python

    import time
    import enlighten

    manager = enlighten.get_manager()
    pbar = manager.counter(total=100, desc='Basic', unit='ticks')

    for num in range(100):
        time.sleep(0.1)  # Simulate work
        pbar.update()

Additional progress bars can be created with additional calls to the
Manager.counter_ method.

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

The Counter_ class has two output formats, progress bar and counter.

The progress bar format is used when a total is not ``None`` and the count is less than the
total. If neither of these conditions are met, the counter format is used:

.. code-block:: python

    import time
    import enlighten

    manager = enlighten.get_manager()
    counter = manager.counter(desc='Basic', unit='ticks')

    for num in range(100):
        time.sleep(0.1)  # Simulate work
        counter.update()

Status Bars
-----------
Status bars are bars that work similarly to progress bars and counters, but present relatively
static information. Status bars are created with
Manager.status_bar_.

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

See StatusBar_ for more details.

Color
-----

Status bars and the bar component of a progress bar can be colored by setting the
``color`` keyword argument. See
`Series Color <https://python-enlighten.readthedocs.io/en/stable/api.html#series-color>`_ for more
information about valid colors.

.. code-block:: python

    import time
    import enlighten

    manager = enlighten.get_manager()
    counter = manager.counter(total=100, desc='Colorized', unit='ticks', color='red')

    for num in range(100):
        time.sleep(0.1)  # Simulate work
    counter.update()

Additionally, any part of the progress bar can be colored using `counter
formatting <https://python-enlighten.readthedocs.io/en/stable/api.html#counter-format>`_ and the
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

If the ``color`` option is applied to a Counter_,
it will override any foreground color applied.



Multicolored
------------

The bar component of a progress bar can be multicolored to track multiple categories in a single
progress bar.

The colors are drawn from right to left in the order they were added.

By default, when multicolored progress bars are used, additional fields are available for
``bar_format``:

    - count_n (``int``) - Current value of ``count``
    - count_0(``int``) - Remaining count after deducting counts for all subcounters
    - count_00 (``int``) - Sum of counts from all subcounters
    - percentage_n (``float``) - Percentage complete
    - percentage_0(``float``) - Remaining percentage after deducting percentages
      for all subcounters
    - percentage_00 (``float``) - Total of percentages from all subcounters

When Counter.add_subcounter_ is called with ``all_fields`` set to ``True``,
the subcounter will have the additional fields:

    - eta_n (``str``) - Estimated time to completion
    - rate_n (``float``) - Average increments per second since parent was created

More information about ``bar_format`` can be found in the Format_ section of the API.

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

    manager = enlighten.get_manager()
    success = manager.counter(total=100, desc='Testing', unit='tests',
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

    manager = enlighten.get_manager()
    initializing = manager.counter(total=services, desc='Starting', unit='services',
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
* `basic <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/basic.py>`__ - Basic progress bar
* `context manager <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/context_manager.py>`__ - Managers and counters as context managers
* `floats <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/floats.py>`__ - Support totals and counts that are ``floats``
* `multicolored <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/multicolored.py>`__ - Multicolored progress bars
* `multiple with logging <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/multiple_logging.py>`__ - Nested progress bars and logging
* `FTP downloader <https://raw.githubusercontent.com/Rockhopper-Technologies/enlighten/master/examples/ftp_downloader.py>`__ - Show progress downloading files from FTP

Customization
-------------

Enlighten is highly configurable. For information on modifying the output, see the
Series_ and Format_ sections of the Counter_ documentation.

.. _Counter: http://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Counter
.. _Counter.add_subcounter: https://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Counter.add_subcounter
.. _StatusBar: https://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.StatusBar
.. _Manager: http://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Manager
.. _Manager.counter: https://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Manager.counter
.. _Manager.status_bar: https://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Manager.status_bar
.. _get_manager: http://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.get_manager
.. _Format: http://python-enlighten.readthedocs.io/en/stable/api.html#counter-format
.. _Series: http://python-enlighten.readthedocs.io/en/stable/api.html#series
.. _EPEL: https://fedoraproject.org/wiki/EPEL
.. _configured: https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F
