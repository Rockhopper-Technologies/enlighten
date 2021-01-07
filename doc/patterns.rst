..
  Copyright 2017 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten

Common Patterns
===============

Enable / Disable
----------------

A program may want to disable progress bars based on a configuration setting as well as if
output redirection occurs.

.. code-block:: python

    import sys
    import enlighten

    # Example configuration object
    config = {'stream': sys.stdout,
              'useCounter': False}

    enableCounter = config['useCounter'] and stream.isatty()
    manager = enlighten.Manager(stream=config['stream'], enabled=enableCounter)

The :py:func:`~enlighten.get_manager` function slightly simplifies this

.. code-block:: python

    import enlighten

    # Example configuration object
    config = {'stream': None,  # Defaults to sys.stdout
              'useCounter': False}

    manager = enlighten.get_manager(stream=config['stream'], enabled=config['useCounter'])


Context Managers
----------------

Both :py:class:`~enlighten.Counter` and :py:class:`~enlighten.Manager`
can be used as context managers.

.. code-block:: python

    import enlighten

    SPLINES = 100

    with enlighten.Manager() as manager:
        with manager.counter(total=SPLINES, desc='Reticulating:', unit='splines') as retic:
            for num in range(SPLINES + 1):
                retic.update()


Automatic Updating
------------------

Both :py:class:`~enlighten.Counter` and :py:class:`~enlighten.SubCounter` instances can be
called as functions on one or more iterators. A generator is returned which yields each element of
the iterables and then updates the count by 1.

.. note::
    When a :py:class:`~enlighten.Counter` instance is called as a function, type checking is lazy
    and won't validate an iterable was passed until iteration begins.

.. code-block:: python

    import time
    import enlighten

    flock1 = ['Harry', 'Sally', 'Randy', 'Mandy', 'Danny', 'Joe']
    flock2 = ['Punchy', 'Kicky', 'Spotty', 'Touchy', 'Brenda']
    total = len(flock1) + len(flock2)

    manager = enlighten.Manager()
    pbar = manager.counter(total=total, desc='Counting Sheep', unit='sheep')

    for sheep in pbar(flock1, flock2):
        time.sleep(0.2)
        print('%s: Baaa' % sheep)

User-defined fields
-------------------

Both :py:class:`~enlighten.Counter` and :py:class:`~enlighten.StatusBar` accept
user defined fields as keyword arguments at initialization and during an update.
These fields are persistent and only need to be specified when they change.

In the following example, ``source`` is a user-defined field that is periodically updated.

.. code-block:: python

    import enlighten
    import random
    import time

    bar_format = u'{desc}{desc_pad}{source} {percentage:3.0f}%|{bar}| ' + \
                 u'{count:{len_total}d}/{total:d} ' + \
                 u'[{elapsed}<{eta}, {rate:.2f}{unit_pad}{unit}/s]'
    manager = enlighten.get_manager(bar_format=bar_format)

    bar = manager.counter(total=100, desc='Loading', unit='files', source='server.a')
    for num in range(100):
        time.sleep(0.1)  # Simulate work
        if not num % 5:
            bar.update(source=random.choice(['server.a', 'server.b', 'server.c']))
        else:
            bar.update()

For more information, see the :ref:`Counter Format <counter_format>` and
:ref:`StatusBar Format <status_format>` sections.
