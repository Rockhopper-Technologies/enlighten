..
  Copyright 2017 - 2024 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten

API Reference
=============

Classes
-------

.. py:module:: enlighten

.. autoclass:: Manager(stream=None, counter_class=Counter, **kwargs)
   :inherited-members:
   :exclude-members: write, remove

.. autoclass:: NotebookManager(stream=None, counter_class=Counter, **kwargs)
   :inherited-members:
   :exclude-members: write, remove

.. autoclass:: Counter
    :members:
    :inherited-members:
    :exclude-members: count, elapsed, position

.. autoclass:: StatusBar
    :members:
    :inherited-members:
    :exclude-members: count, elapsed, position

.. autoclass:: SubCounter
    :members:

Functions
---------

.. autofunction:: enlighten.get_manager(stream=None, counter_class=Counter, **kwargs)
.. autofunction:: format_time

Constants
---------

.. autoclass:: enlighten.Justify