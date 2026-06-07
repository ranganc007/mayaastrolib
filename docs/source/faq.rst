Frequently Asked Questions
==========================


**Can everyone use it?**

mayaastrolib is open-source software so everyone is free to install and use it.
However, since it is a programming library, some people may not be particularly inclined to use it since it
requires some learning.

**So is it not an end-user tool?**

mayaastrolib should really be seen as traditional and Vedic astrology software without a graphical user interface.
Therefore, it is really powerful, since users can experiment without the "chains" of a graphical user interface.

**How can I install it?**

You should install Python 3.10 or later and install mayaastrolib from source (see :doc:`installation`).
This will install mayaastrolib and its dependency, ``pyswisseph``. A PyPI release will follow once the API stabilises.

**What does it add over flatlib?**

mayaastrolib keeps flatlib's traditional-astrology core and adds a complete Vedic (Jyotisha) subsystem
(ayanamsas, nakshatras, the 16 divisional charts, Vimshottari dasha, ashtakavarga, yogas, KP, Tajika, and more),
modern packaging and type hints, and a much larger test suite (94% coverage, with golden tests anchored against an
independent ephemeris). See the project ``README.md`` and ``CHANGELOG.md`` for the full list.

**Is there a project page?**

You can check the code and documentation on the GitHub page at https://github.com/ranganc007/mayaastrolib.
The upstream project this fork is based on lives at https://github.com/flatangle/flatlib.

**Are there any sample code?**

There's a "recipes" folder with some source code at https://github.com/ranganc007/mayaastrolib/tree/master/recipes.
You can start with "aspects.py" at https://github.com/ranganc007/mayaastrolib/blob/master/recipes/aspects.py.

**Can I use it in my own work?**

Absolutely yes, you are free to use it in your own projects.
The mayaastrolib source code is released under an MIT License, which allows it to be used also on commercial projects.
There is a caveat though: mayaastrolib uses the Swiss Ephemeris which is licensed GPL.
Therefore, if you want to use mayaastrolib in your commercial projects, you must adhere to the GPL license or buy a
Swiss Ephemeris commercial license. See ``LICENSING.md`` in the repository root.

**Can I contribute to the project?**

Contributions such as code and documentation are welcome. See ``docs/CONTRIBUTION-PLAN.md`` for the
current roadmap and working agreements.
