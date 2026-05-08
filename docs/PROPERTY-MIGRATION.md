# Method-to-Property Migration

This document tracks the methods that were converted to `@property_with_method_compat` in Task 006. The decorator (in `mayaastrolib/_compat.py`) makes both `obj.thing` (preferred) and `obj.thing()` (deprecated, with `DeprecationWarning`) return the same value. Both styles work until version 1.0, when the decorator and the method-style access will be removed.

## Why this exists

A consumer wrote `if obj.movement:` expecting it to test whether the planet was moving in a non-default state. The expression was always `True` because `obj.movement` returned a *bound method object*, not the movement string — and bound methods are always truthy. Real bugs hid behind methods that looked like properties.

The conversion fixes that bug class without breaking existing code.

## Methods converted

| Class | Method | Returns | Notes |
|---|---|---|---|
| `GenericObject` | `orb` | `float` | Always `-1.0` for the base class. |
| `Object` | `orb` | `float` | Per-planet orb from `props.object.orb`. |
| `Object` | `meanMotion` | `float` | Daily motion in degrees from `props.object.meanMotion`. |
| `Object` | `movement` | `str` | One of `const.DIRECT`, `const.RETROGRADE`, `const.STATIONARY`. The bug case. |
| `Object` | `gender` | `str` | From `props.object.gender`. |
| `Object` | `faction` | `str` | From `props.object.faction`. |
| `Object` | `element` | `str` | From `props.object.element`. |
| `House` | `num` | `int` | Parsed from `self.id` (`House5` → `5`). |
| `House` | `condition` | `str` | Angular / Succedent / Cadent. |
| `House` | `gender` | `str` | From `props.house.gender`. |
| `Aspect` | `movement` | `str` | Composite of active object's movement plus exact-orb override. |
| `FixedStar` | `orb` | `float` | Magnitude-derived orb. |

12 methods total.

## Task 010 update: None passthrough on `_DualAccess`

`_DualAccess` (the wrapper that powers `property_with_method_compat`)
originally wrapped every value, including `None`, so that
`obj.thing()` could still emit `DeprecationWarning`. Task 010 added a
None passthrough: if the underlying value is `None`, the property
returns `None` directly, unwrapped. This is required so that
`obj.movement is None` works — a check that's now meaningful for
symbolic-chart objects whose speed-derived attributes are undefined.

Tradeoff: calling `obj.movement()` on a symbolic object raises
`TypeError("'NoneType' object is not callable")` instead of emitting
the deprecation warning. Symbolic objects are new in Task 010; no
existing code does this, and the new code never should.

## Methods NOT converted

| Class | Method | Reason |
|---|---|---|
| `Aspect.direction` | (n/a) | Already a stored attribute set via `Aspect.__init__` from the properties dict. Not a method. |
| `Object.isPlanet`, `Object.isDirect`, `Object.isRetrograde`, `Object.isStationary`, `Object.isFast` | These have `is` prefix — they read like predicates and the convention is to keep them as methods. |
| `House.isAboveHorizon`, `House.inHouse`, `House.hasObject` | `is` / `has` / `in` prefix — predicates, not getters. |
| `FixedStar.aspects` | Takes an argument; not a getter. |
| `Object.relocate`, `Object.antiscia`, `Object.cantiscia` | Have side effects or transform the object — semantically methods. As of Task 010, all three are deprecated and slated for 1.0 removal. Migrate to `obj.with_longitude(lon)` / `obj.antiscion()` / `obj.cantiscion()`. |
| `Object.eqCoords` | Takes an argument (`zerolat`). |
| `GenericObject.copy` | Constructs a new object — semantically a method. |

## How the wrapper works

`_compat.py` defines `property_with_method_compat`. When applied to a method, it produces a descriptor whose `__get__` returns a `_DualAccess` wrapper around the method's return value. The wrapper:

- `__call__` returns the value AND emits a `DeprecationWarning`.
- `__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__` delegate to the value (with reflected comparisons handled via the `_unwrap` helper).
- `__bool__` reflects the value's truthiness (the regression fix).
- `__hash__`, `__str__`, `__repr__`, `__int__`, `__float__` delegate to the value.

Internal library code uses bare property access (`obj.movement`, no parens) so it never emits warnings against itself. External code keeps both styles working through 1.0.

## Removal plan (1.0)

When the migration is removed:

1. Delete `mayaastrolib/_compat.py`.
2. Replace each `@property_with_method_compat` decorator with `@property` in `mayaastrolib/object.py` and `mayaastrolib/aspects.py`.
3. Search for any remaining `obj.movement()` / `obj.orb()` etc. in tests, recipes, and dependent code, and rewrite to bare access.
4. Drop this document.
