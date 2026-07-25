"""Sphinx configuration for the mayaastrolib API reference.

Rewritten in Task v1.0-06. The previous file was the 2015 flatlib
``sphinx-quickstart`` output: no extensions (so no API docs were generated at
all), a hard-coded version string that had drifted to 0.3.1, and a number of
options that modern Sphinx warns about. The build now runs under ``-W``, so a
warning is a build failure.
"""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

# -- Project information -----------------------------------------------------

project = "mayaastrolib"
copyright = (  # noqa: A001 — Sphinx requires this exact name
    "2015 João Ventura; fork modifications 2026 Rangan C."
)
author = "João Ventura; Rangan C. (fork)"

# Read the version from installed package metadata rather than hard-coding it.
# The old conf.py pinned "0.3.1" and had drifted three releases behind.
try:
    release = _pkg_version("mayaastrolib")
except PackageNotFoundError:  # building from a source tree without an install
    release = "0.0.0+unknown"
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",  # Google-style docstrings (see CLAUDE.md code style)
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "myst_parser",  # so the Markdown docs under docs/ can be included
]

source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
exclude_patterns: list[str] = []
pygments_style = "sphinx"

# -- autodoc -----------------------------------------------------------------

# Document the frozen public surface, not everything importable. Each module
# declares __all__ (Task v1.0-05, see docs/API-STABILITY.md) and autodoc
# honours it, so the reference and the contract cannot drift apart.
autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
}
autodoc_member_order = "bysource"
# "signature" rather than "description": with "description", autodoc emits the
# frozen dataclasses' fields (YogaResult, UpagrahaResult, TajikaAspect, ...)
# both as attributes and as constructor parameters, producing 33 "duplicate
# object description" warnings — which are build failures under -W.
autodoc_typehints = "signature"

# swisseph is a C extension without stubs; importing it during a docs build on
# ReadTheDocs is neither necessary nor reliable.
autodoc_mock_imports = ["swisseph"]

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
# The frozen dataclasses (DashaPeriod, YogaResult, UpagrahaResult,
# TajikaAspect, ...) document their fields in a Google-style ``Attributes:``
# block *and* carry the annotation autodoc documents. By default napoleon
# renders that block as ``.. attribute::`` directives, so each field is
# described twice — 33 "duplicate object description" warnings, which are
# failures under -W. ``use_ivar`` renders them as ``:ivar:`` fields on the
# class instead, which reads the same and collides with nothing.
napoleon_use_ivar = True

intersphinx_mapping = {"python": ("https://docs.python.org/3", None)}

# -- HTML output -------------------------------------------------------------

html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
htmlhelp_basename = "mayaastrolibdoc"
