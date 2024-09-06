..
  Copyright 2017 - 2024 Avram Lubkin, All Rights Reserved

  This Source Code Form is subject to the terms of the Mozilla Public
  License, v. 2.0. If a copy of the MPL was not distributed with this
  file, You can obtain one at http://mozilla.org/MPL/2.0/.

:github_url: https://github.com/Rockhopper-Technologies/enlighten

Frequently Asked Questions
==========================

Why is Enlighten called Enlighten?
----------------------------------

A progress bar's purpose is to inform the user about an ongoing process.
Enlighten, meaning "to inform", seems a fitting name.
(Plus any names related to progress were already taken)


Is Windows supported?
---------------------

Enlighten has supported Windows since version 1.3.0.

Windows does not currently support resizing.

Enlighten also works in Linux-like subsystems for Windows such as
`Cygwin <https://cygwin.com/>`_ or
`Windows Subsystem for Linux <https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux>`_.

Is Jupyter Notebooks Supported?
-------------------------------

Support for Jupyter notebooks was added in version 1.10.0.

Jupyter Notebook support is provide by the :py:class:`~enlighten.NotebookManager` class.
If running inside a Jupyter Notebook, :py:func:`~enlighten.get_manager` will return a
:py:class:`~enlighten.NotebookManager` instance.

There is currently no support for detecting the width of a Jupyter notebook so output width has been
set statically to 100 characters. This can be overridden by passing the ``width`` keyword argument
to :py:func:`~enlighten.get_manager`.

Is PyCharm supported?
---------------------

PyCharm uses multiple consoles and the behavior differs depending on how the code is called.

Enlighten works natively in the PyCharm command terminal.

To use Enlighten with Run or Debug, terminal emulation must be enabled.
Navigate to `Run -> Edit Configurations -> Templates -> Python`
and select `Emulate terminal in output console`.

The PyCharm Python console is currently not supported because :py:data:`sys.stdout`
does not reference a valid TTY.

We are also tracking an `issue with CSR <https://youtrack.jetbrains.com/issue/IDEA-252747>`_
in the PyCharm terminal.

.. spelling:word-list::
    csr
    eos
    eol

Can you add support for _______ terminal?
-----------------------------------------

We are happy to add support for as many terminals as we can.
However, not all terminals can be supported. There a few requirements.

  1. The terminal must be detectable programmatically

      We need to be able to identify the terminal in some reasonable way
      and differentiate it from other terminals. This could be through environment variables,
      the :py:mod:`platform` module, or some other method.

  2. A subset of terminal codes must be supported

      While these codes may vary among terminals, the capability must be
      provided and activated by printing a terminal sequence.
      The required codes are listed below.

        * move / CUP - Cursor Position
        * hide_cursor / DECTCEM - Text Cursor Enable Mode
        * show_cursor / DECTCEM - Text Cursor Enable Mode
        * csr / DECSTBM - Set Top and Bottom Margins
        * clear_eos / ED - Erase in Display
        * clear_eol / EL - Erase in Line
        * feed / CUD - Cursor Down (Or scroll with linefeed)

  3. Terminal dimensions must be detectable

      The height and width of the terminal must be available to the running process.

Why does ``RuntimeError: reentrant call`` get raised sometimes during a resize?
-------------------------------------------------------------------------------

This is caused when another thread or process is writing to a standard stream (STDOUT, STDERR)
at the same time the resize signal handler is writing to the stream.

Enlighten tries to detect when a program is threaded or running multiple processes and defer
resize handling until the next normal write event. However, this condition is evaluated when
the scroll area is set, typically when the first counter is added. If no threads or processes
are detected at that time, and the value of threaded was not set explicitly, resize events will not
be deferred.

In order to guarantee resize handling is deferred, it is best to pass ``threaded=True`` when
creating a manager instance.

Why isn't my progress bar displayed until :py:meth:`~enlighten.Counter.update` is called?
-----------------------------------------------------------------------------------------

Progress bars and counters are not automatically drawn when created because some fields may be
missing if subcounters are used. To force the counter to draw before updating, call
:py:meth:`~enlighten.Counter.refresh`

Why does the output get scrambled when the number of progress bars exceeds the terminal height?
-----------------------------------------------------------------------------------------------

Enlighten draws progress bars in a non-scrolling region at the bottom of the terminal. This
areas is limited to the size of the terminal. In some terminals, the output
is cut off to the size of the terminal. In others, lines will be overwritten and appear scrambled.

We advise you to close progress bars when they are complete and do not add additional value for the
user. However, if you have a need to create a lot of progress bars, you may want to check the size
of the terminal and resize it if needed. How this is accomplished will depend on the platform and
terminal you are using.
