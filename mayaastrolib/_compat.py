"""Compatibility shims for the method-to-property migration.

When a method is converted to a @property, the old method-style access
must keep working with a DeprecationWarning. This module provides the
helper that makes that happen.

Plan: remove this module and all its uses in version 1.0.
"""

from __future__ import annotations

import functools
import warnings
from collections.abc import Callable
from typing import Any, TypeVar

_T = TypeVar("_T")


def property_with_method_compat(func: Callable[[Any], _T]) -> _T:
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

        def __init__(self, value: Any, owner: Any) -> None:
            self._value = value
            self._owner_class = type(owner).__name__

        def __call__(self) -> Any:
            warnings.warn(
                f"{self._owner_class}.{name} is now a property, not a method. "
                f"Use `obj.{name}` instead of `obj.{name}()`. "
                f"Method-style access will be removed in version 1.0.",
                DeprecationWarning,
                stacklevel=2,
            )
            return self._value

        @staticmethod
        def _unwrap(other: Any) -> Any:
            return other._value if isinstance(other, _DualAccess) else other

        def __eq__(self, other: object) -> bool:
            return bool(self._value == self._unwrap(other))

        def __ne__(self, other: object) -> bool:
            return bool(self._value != self._unwrap(other))

        def __lt__(self, other: Any) -> bool:
            return bool(self._value < self._unwrap(other))

        def __le__(self, other: Any) -> bool:
            return bool(self._value <= self._unwrap(other))

        def __gt__(self, other: Any) -> bool:
            return bool(self._value > self._unwrap(other))

        def __ge__(self, other: Any) -> bool:
            return bool(self._value >= self._unwrap(other))

        def __bool__(self) -> bool:
            return bool(self._value)

        def __hash__(self) -> int:
            return hash(self._value)

        def __repr__(self) -> str:
            return repr(self._value)

        def __str__(self) -> str:
            return str(self._value)

        def __float__(self) -> float:
            return float(self._value)

        def __int__(self) -> int:
            return int(self._value)

    @functools.wraps(func)
    def wrapper(self: Any) -> Any:
        value = func(self)
        # Pass None through unwrapped so `obj.x is None` checks work.
        # Used by symbolic-chart Objects whose speed-derived attributes
        # are undefined (Task 010).
        if value is None:
            return None
        return _DualAccess(value, self)

    # At runtime this returns a `property` descriptor whose __get__ yields a
    # _DualAccess wrapper. The declared return type is the *value* type `_T`
    # instead, because that is what attribute access effectively produces for
    # callers: _DualAccess forwards ==, <, bool, str, hash, int and float to
    # the wrapped value, so `obj.movement` behaves as the value everywhere it
    # is used. Typing it this way gives downstream consumers (the package
    # ships py.typed) real types on every migrated property.
    #
    # The deliberate gap: the deprecated method-style call `obj.movement()`
    # is not modelled and will be flagged by a type checker. That is the
    # intended signal — method-style access is slated for removal alongside
    # this module (see docs/PROPERTY-MIGRATION.md).
    #
    # `property(wrapper)` rather than a `@property` decorator on the nested
    # function: identical at runtime, but mypy rejects `@property` applied to
    # something it does not consider a method.
    return property(wrapper)  # type: ignore[return-value]
