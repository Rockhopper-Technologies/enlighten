..
  Copyright 2017 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten


Examples
=========

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


Additional Examples
-------------------

* :download:`basic <../examples/basic.py>` - Basic progress bar
* :download:`floats <../examples/floats.py>` - Support totals and counts that are :py:class:`floats<float>`
* :download:`multiple with logging <../examples/multiple_logging.py>` - Nested progress bars and logging

Customization
-------------

Enlighten is highly configurable. For information on modifying the output, see the
:ref:`Series <series>` and :ref:`Format <counter_format>`
sections of the :py:class:`~enlighten.Counter` documentation.

