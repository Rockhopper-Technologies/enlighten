..
  Copyright 2017 Avram Lubkin, All Rights Reserved

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

Enlighten also works relatively well in Linux-like subsystems for Windows such as
`Cygwin <https://cygwin.com/>`_ or
`Windows Subsystem for Linux <https://en.wikipedia.org/wiki/Windows_Subsystem_for_Linux>`_.


.. spelling::
    csr
    eos
    eol

Can you add support for _______ terminal?
---------------------------------------------------

We are happy to add support for as many terminals as we can.
However, not all terminals can be supported. There a few requirements.

  1. The terminal must be detectible programmatically

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

  3. Terminal dimensions must be detectible

      The height and width of the terminal must be available to the running process.
