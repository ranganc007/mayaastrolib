"""
This file is part of flatlib - (C) FlatAngle
Author: João Ventura (flatangleweb@gmail.com)

"""

import os
from importlib.metadata import PackageNotFoundError, version as _pkg_version

try:
    __version__ = _pkg_version("mayaastrolib")
except PackageNotFoundError:
    __version__ = "0.0.0+unknown"

# Library and resource paths
PATH_LIB = os.path.dirname(__file__) + os.sep
PATH_RES = PATH_LIB + "resources" + os.sep
