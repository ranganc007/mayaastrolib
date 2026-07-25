Installation
============

mayaastrolib requires Python 3.10 or later. The simplest way to install it is from PyPI::

   pip install mayaastrolib

To install from source instead (for development), see "Installing from source" below.

Prerequisites
-------------

mayaastrolib depends on *pyswisseph* — the Python port of the Swiss Ephemeris, which is
implemented in C. Installing it requires a C compiler:

* **Windows** — install the *Microsoft C++ Build Tools* (Visual Studio Build Tools).
* **macOS** — install the *Xcode Command Line Tools* with ``xcode-select --install``.
* **Linux** — install your distribution's ``python3-dev`` and ``gcc`` packages.

In most cases ``pip`` will fetch a prebuilt ``pyswisseph`` wheel and no compiler is needed.

Installing from source
----------------------

Clone the repository and install it in editable mode::

   git clone https://github.com/ranganc007/mayaastrolib.git
   cd mayaastrolib
   pip install -e .

To install the development dependencies (pytest, ruff, mypy, skyfield) as well::

   pip install -e ".[dev]"

Testing the installation
------------------------

Start the Python interpreter and execute::

   >>> import mayaastrolib
   >>> mayaastrolib.__version__
   '0.3.1'

If you don't get an import error, mayaastrolib is installed in your system.

Migrating from flatlib
----------------------

Rewrite ``flatlib`` imports to ``mayaastrolib``; the module layout is otherwise unchanged::

    from flatlib import const          ->  from mayaastrolib import const
    from flatlib.chart import Chart    ->  from mayaastrolib.chart import Chart

Versions 0.3.0-0.5.0 shipped a ``flatlib`` compatibility package that re-exported
``mayaastrolib`` with a ``DeprecationWarning``. It was removed in 1.0, so ``import flatlib``
now raises ``ModuleNotFoundError``. Pin ``mayaastrolib<1.0`` if you need the shim while
migrating.

Upgrading
---------

Pull the latest changes and reinstall::

   git pull
   pip install -e .

Uninstalling
------------

Run ``pip uninstall mayaastrolib``.
