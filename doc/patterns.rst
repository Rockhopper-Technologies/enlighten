..
  Copyright 2017 - 2023 Avram Lubkin, All Rights Reserved

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
    config = {'stream': None,  # Defaults to sys.__stdout__
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
            for num in range(1, SPLINES + 1):
                time.sleep(.1)
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


Human-readable numeric prefixes
-------------------------------

Enlighten supports automatic `SI (metric)`_ and `IEC (binary)`_ prefixes using the Prefixed_
library.

All ``rate`` and ``interval`` formatting fields are of the type :py:class:`prefixed.Float`.
``total`` and all ``count`` fields default to :py:class:`int`.
If :py:attr:`~Counter.total` or or :py:attr:`~Counter.count` are set to a :py:class:`float`,
or a :py:class:`float` is provided to :py:meth:`~Counter.update`,
these fields will be :py:class:`prefixed.Float` instead.

.. code-block:: python

    import time
    import random
    import enlighten

    size = random.uniform(1.0, 10.0) * 2 ** 20  # 1-10 MiB (float)
    chunk_size = 64 * 1024  # 64 KiB

    bar_format = '{desc}{desc_pad}{percentage:3.0f}%|{bar}| ' \
                 '{count:!.2j}{unit} / {total:!.2j}{unit} ' \
                 '[{elapsed}<{eta}, {rate:!.2j}{unit}/s]'

    manager = enlighten.get_manager()
    pbar = manager.counter(total=size, desc='Downloading', unit='B', bar_format=bar_format)

    bytes_left = size
    while bytes_left:
        time.sleep(random.uniform(0.05, 0.15))
        next_chunk = min(chunk_size, bytes_left)
        pbar.update(next_chunk)
        bytes_left -= next_chunk


.. code-block:: python

    import enlighten

    counter_format = 'Trying to get to sleep: {count:.2h} sheep'

    manager = enlighten.get_manager()
    counter = manager.counter(counter_format=counter_format)
    counter.count = 0.0
    for num in range(10000000):
        counter.update()


For more information, see the :ref:`Counter Format <counter_format>`
and the `Prefixed`_ documentation.

.. _SI (metric): https://en.wikipedia.org/wiki/Metric_prefix
.. _IEC (binary): https://en.wikipedia.org/wiki/Binary_prefix
.. _Prefixed: https://prefixed.readthedocs.io/en/stable/index.html

Manually Printing
-----------------

By default, if the manager's stream is connected to a TTY, bars and counters are automatically
printed and updated. There may, however be cases where manual output is desired in addition to or
instead of the automatic output. For example, to send to other streams or print to a file.

The output for an individual bar can be retrieved from the :py:meth:`~Counter.format` method. This
supports optional arguments to specify width and elapsed time.

.. code-block:: python

    import enlighten

    manager = enlighten.get_manager(enabled=False)
    pbar = manager.counter(desc='Progress', total=10)

    pbar.update()
    print(pbar.format(width=100))


As a shortcut, the counter object will call the :py:meth:`~Counter.format` method with the default
arguments when coerced to a string.

.. code-block:: python

    import enlighten

    manager = enlighten.get_manager(enabled=False)
    pbar = manager.counter(desc='Progress', total=10)

    pbar.update()
    print(pbar)


While Enlighten's default output provides more advanced capability, A basic refreshing progress bar
can be created like so.

.. code-block:: python

    import enlighten
    import time

    manager = enlighten.get_manager(enabled=False)
    pbar = manager.counter(desc='Progress', total=10)

    print()

    for num in range(10):
        time.sleep(0.2)
        pbar.update()
        print(f'\r{pbar}', end='', flush=True)

    print()
