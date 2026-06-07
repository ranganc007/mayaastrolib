Installation
============

mayaastrolib requires Python 3.10 or later and installs from source. A PyPI release will be
made available once the public API stabilises, at which point these instructions will be updated.

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
   '0.3.0'

If you don't get an import error, mayaastrolib is installed in your system.

Migrating from flatlib
----------------------

mayaastrolib ships a compatibility shim, so existing ``import flatlib`` calls keep working
(with a ``DeprecationWarning``). Update your imports to ``mayaastrolib`` at your convenience;
the shim is removed in version 1.0.

Upgrading
---------

Pull the latest changes and reinstall::

   git pull
   pip install -e .

Uninstalling
------------

Run ``pip uninstall mayaastrolib``.
