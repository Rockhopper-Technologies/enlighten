..
  Copyright 2017 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten

Common Patterns
===============

enable / disable
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

    import sys
    import enlighten

    # Example configuration object
    config = {'stream': None,  # Defaults to sys.stdout
              'useCounter': False}

    manager = enlighten.get_manager(stream=config['stream'], enabled=config['useCounter'])


