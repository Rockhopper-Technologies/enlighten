.. start-badges

| |docs| |gh_actions| |codecov|
| |linux| |windows| |mac| |bsd|
| |pypi| |supported-versions| |supported-implementations|
| |Fedora| |EPEL| |Arch| |Debian| |Ubuntu| |Anaconda|

.. |docs| image:: https://img.shields.io/readthedocs/python-enlighten.svg?style=plastic&logo=read-the-docs
    :target: https://python-enlighten.readthedocs.org
    :alt: Documentation Status

.. |gh_actions| image:: https://img.shields.io/github/workflow/status/Rockhopper-Technologies/enlighten/Tests?event=push&logo=github-actions&style=plastic
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

.. |EPEL| image:: https://img.shields.io/fedora/v/python3-enlighten/epel8?color=lightgray&label=EPEL&logo=EPEL
    :alt: Latest EPEL Version
    :target: https://src.fedoraproject.org/rpms/python-enlighten

.. |Arch| image:: https://img.shields.io/aur/version/python-enlighten?color=lightgray&logo=Arch%20Linux&style=plastic&label=Arch
    :alt: Latest Arch Linux Version
    :target: https://aur.archlinux.org/packages/python-enlighten

.. |Debian| image:: https://img.shields.io/debian/v/enlighten/sid?color=lightgray&logo=Debian&style=plastic&label=Debian
    :alt: Latest Debian Version
    :target: https://packages.debian.org/source/sid/enlighten

.. |Ubuntu| image:: https://img.shields.io/ubuntu/v/enlighten?color=lightgray&logo=Ubuntu&style=plastic&label=Ubuntu
    :alt: Latest Ubuntu Version
    :target: https://launchpad.net/ubuntu/+source/enlighten

.. |Anaconda| image:: https://img.shields.io/conda/vn/conda-forge/enlighten?color=lightgrey&label=Anaconda&logo=Conda%20Forge&style=plastic
    :alt: Latest Conda Forge Version
    :target: https://anaconda.org/conda-forge/enlighten

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


.. _EPEL: https://fedoraproject.org/wiki/EPEL
.. _configured: https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F


Conda
-----

.. code-block:: console

    $ conda install -c conda-forge enlighten


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
.. _Manager: http://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.Manager
.. _get_manager: http://python-enlighten.readthedocs.io/en/stable/api.html#enlighten.get_manager
.. _Format: http://python-enlighten.readthedocs.io/en/stable/api.html#counter-format
.. _Series: http://python-enlighten.readthedocs.io/en/stable/api.html#series
.. _EPEL: https://fedoraproject.org/wiki/EPEL
.. _configured: https://fedoraproject.org/wiki/EPEL#How_can_I_use_these_extra_packages.3F
