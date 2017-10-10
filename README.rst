
.. start-badges
|docs| |travis|

.. |docs| image:: https://readthedocs.org/projects/python-enlighten/badge/
    :target: https://python-enlighten.readthedocs.org
    :alt: Documentation Status
.. |travis| image:: https://img.shields.io/Rockhopper-Technologies/enlighten.svg
    :alt: Travis-CI Build Status
    :target: https://travis-ci.org/Rockhopper-Technologies/enlighten

.. end-badges

Overview
========

Enlighten Progress Bar is a console progress bar module for Python. (Yes, another one.)

The main advantage of Enlighten is it allows writing to stdout and stderr without any
redirection.

.. image:: doc/_static/multiple_logging.gif

Documentation
=============

https://python-enlighten.readthedocs.io

Examples
========

Basic
-----

For a basic status bar, invoke the Counter_ class directly.

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

Advanced output will only work when the output stream, ``sys.stdout`` by default,
is attached to a TTY. get_manager_ can be used to get a manager instance.
It will return a disabled Manager_ instance if the stream is not attached to a TTY
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

The Counter_ class has two output formats, progress bar and counter.

The progress bar format is used when a total is not ``None`` and the count is less than the
total. If neither of these conditions are met, the counter format is used:

.. code-block:: python

    import time
    import enlighten

    counter = enlighten.Counter(desc='Basic', unit='ticks')
    for num in range(100):
        time.sleep(0.1)  # Simulate work
        counter.update()


Additional Examples
-------------------
* `basic <examples/basic.py>`_ - Basic progress bar
* `floats <examples/floats.py>`_ - Support totals and counts that are ``floats``
* `multiple with logging <examples/multiple_logging.py>`_ - Nested progress bars and logging

Customization
-------------

Enlighten is highly configurable. For information on modifying the output, see the
Series_ and Format_ sections of the Counter_ documentation.

.. _Counter: http://python-enlighten.readthedocs.io/en/latest/api.html#enlighten.Counter
.. _Manager: http://python-enlighten.readthedocs.io/en/latest/api.html#enlighten.Manager
.. _get_manager: http://python-enlighten.readthedocs.io/en/latest/api.html#enlighten.get_manager
.. _Format: http://python-enlighten.readthedocs.io/en/latest/api.html#counter-format
.. _Series: http://python-enlighten.readthedocs.io/en/latest/api.html#series
