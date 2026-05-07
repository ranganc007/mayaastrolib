"""Compatibility shims for the method-to-property migration.

When a method is converted to a @property, the old method-style access
must keep working with a DeprecationWarning. This module provides the
helper that makes that happen.

Plan: remove this module and all its uses in version 1.0.
"""

import functools
import warnings


def property_with_method_compat(func):
    """Decorate a method so it works as both a property and a callable.

    Property access (the new way) returns the value directly via a
    transparent wrapper. Method-style access (the old way) returns the
    same value but emits a DeprecationWarning pointing at the call site.

    Usage:
        class Object:
            @property_with_method_compat
            def movement(self):
                return _compute_movement(self)

    Then both ``obj.movement`` and ``obj.movement()`` return the value;
    the latter emits a warning.

    The wrapper forwards comparison, boolean, hash, str/repr, and
    arithmetic-comparison protocols to the wrapped value, so existing
    expressions like ``obj.movement == const.DIRECT`` and
    ``abs(speed) >= obj.meanMotion`` keep working without parentheses.
    """
    name = func.__name__

    class _DualAccess:
        __slots__ = ("_value", "_owner_class")

        def __init__(self, value, owner):
            self._value = value
            self._owner_class = type(owner).__name__

        def __call__(self):
            warnings.warn(
                f"{self._owner_class}.{name} is now a property, not a method. "
                f"Use `obj.{name}` instead of `obj.{name}()`. "
                f"Method-style access will be removed in version 1.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._value

        @staticmethod
        def _unwrap(other):
            return other._value if isinstance(other, _DualAccess) else other

        def __eq__(self, other):
            return self._value == self._unwrap(other)

        def __ne__(self, other):
            return self._value != self._unwrap(other)

        def __lt__(self, other):
            return self._value < self._unwrap(other)

        def __le__(self, other):
            return self._value <= self._unwrap(other)

        def __gt__(self, other):
            return self._value > self._unwrap(other)

        def __ge__(self, other):
            return self._value >= self._unwrap(other)

        def __bool__(self):
            return bool(self._value)

        def __hash__(self):
            return hash(self._value)

        def __repr__(self):
            return repr(self._value)

        def __str__(self):
            return str(self._value)

        def __float__(self):
            return float(self._value)

        def __int__(self):
            return int(self._value)

    @property
    @functools.wraps(func)
    def wrapper(self):
        return _DualAccess(func(self), self)

    return wrapper
