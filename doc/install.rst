..
  Copyright 2017 - 2021 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten


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

(EPEL_ repositories must be configured_ for EL8)

.. code-block:: console

    $ dnf install python3-enlighten

EL7 (RHEL/CentOS)
^^^^^^^^^^^^^^^^^

(EPEL_ repositories must be configured_)

.. code-block:: console

    $ yum install python2-enlighten
    $ yum install python36-enlighten


PKG
---

Arch Linux
^^^^^^^^^^

.. code-block:: console

    $ pacman -S python-enlighten


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
