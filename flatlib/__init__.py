"""Compatibility shim — flatlib has been renamed to mayaastrolib.

This module re-exports everything from `mayaastrolib` and emits a
DeprecationWarning. Marked for removal in version 1.0.

Update your imports:
    from flatlib import const     →  from mayaastrolib import const
    from flatlib.chart import Chart  →  from mayaastrolib.chart import Chart
"""

import sys
import warnings

warnings.warn(
    "The 'flatlib' package has been renamed to 'mayaastrolib'. "
    "Update your imports: 'from flatlib import X' → 'from mayaastrolib import X'. "
    "The 'flatlib' shim will be removed in version 1.0.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything from mayaastrolib at the package level.
import mayaastrolib  # noqa: E402
from mayaastrolib import *  # noqa: F401, F403, E402
from mayaastrolib import (  # noqa: F401, E402
    PATH_LIB,
    PATH_RES,
    __version__,
    angle,
    aspects,
    chart,
    const,
    datetime,
    geopos,
    lists,
    object,  # noqa: A004 — shim must re-export the public-API `object` namespace
    props,
    utils,
)

# Make `from flatlib.<submodule> import …` resolve to mayaastrolib.<submodule>.
# Without this, Python's import system would look for a flatlib/<submodule>.py
# file on disk (which doesn't exist for the top-level modules — only the
# subpackages have their own __init__.py files).
for _submod in (
    "angle",
    "aspects",
    "chart",
    "const",
    "datetime",
    "geopos",
    "lists",
    "object",
    "props",
    "utils",
):
    sys.modules[f"flatlib.{_submod}"] = getattr(mayaastrolib, _submod)
del _submod
