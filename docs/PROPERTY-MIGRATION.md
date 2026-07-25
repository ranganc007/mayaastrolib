# Method-to-Property Migration

> **Status: complete.** The migration finished in 1.0 (Task v1.0-02b). The
> methods below are now plain `@property`; `mayaastrolib/_compat.py` and the
> deprecated method-style access (`obj.movement()`) are **gone**. This document
> is kept as the record of what changed and why.

This document tracks the methods converted to properties in Task 006. From Task 006 through 0.5.0 they used a `property_with_method_compat` decorator so that both `obj.thing` (preferred) and `obj.thing()` (deprecated, with `DeprecationWarning`) returned the same value. 1.0 removed the decorator and the method-style form, as every one of those warnings said it would.

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
| ~~`Object.relocate`, `Object.antiscia`, `Object.cantiscia`~~ | Had side effects or transformed the object — semantically methods, so never converted to properties. Deprecated in Task 010 and **removed in 1.0** (Task v1.0-02). Use `obj.with_longitude(lon)` / `obj.antiscion()` / `obj.cantiscion()`. |
| `Object.eqCoords` | Takes an argument (`zerolat`). |
| `GenericObject.copy` | Constructs a new object — semantically a method. |

## How the wrapper works

`_compat.py` defines `property_with_method_compat`. When applied to a method, it produces a descriptor whose `__get__` returns a `_DualAccess` wrapper around the method's return value. The wrapper:

- `__call__` returns the value AND emits a `DeprecationWarning`.
- `__eq__`, `__ne__`, `__lt__`, `__le__`, `__gt__`, `__ge__` delegate to the value (with reflected comparisons handled via the `_unwrap` helper).
- `__bool__` reflects the value's truthiness (the regression fix).
- `__hash__`, `__str__`, `__repr__`, `__int__`, `__float__` delegate to the value.

Internal library code uses bare property access (`obj.movement`, no parens) so it never emits warnings against itself. External code keeps both styles working through 1.0.

As of Task v1.0-04 the decorator is typed `Callable[[Any], _T] -> _T`, so each migrated property exposes its real value type to downstream type checkers (`Object.movement` reveals as `str | None`, `Object.element` as `str`; both were `Any`). The annotation models *property* access only — the deprecated `obj.movement()` call form is not typed and a type checker will flag it. That is intentional: it is the form being removed.

## Removal (Task v1.0-02b, shipped in 1.0)

Task v1.0-02 removed the *function/method-level* deprecations but deliberately
left this migration alone. The v1.0-08 release gate then caught the
contradiction: `_compat.py` was still emitting *"Method-style access will be
removed in version 1.0"* while 1.0 was about to ship with it intact. Rather
than retarget the warning to 2.0 and extend a deprecation past the version
users were promised, the removal was done.

What changed:

1. The 12 `@property_with_method_compat` decorators (11 in `object.py`, 1 in
   `aspects.py`) became plain `@property`.
2. `mayaastrolib/_compat.py` and `tests/test_compat.py` were deleted.
3. Nothing else needed rewriting — the library, tests and recipes had **no**
   method-style call sites; internal code had always used bare access.

What is preserved, verified after the change:

- `obj.movement`, `obj.element`, `house.num`, ... all read exactly as before.
- The **truthiness fix** that motivated the whole migration: `bool(obj.movement)`
  reflects the value. A plain `@property` gives this natively — it was the
  bound-method object that was always truthy.
- The `None` passthrough for symbolic charts: `obj.movement is None` still
  works when `lonspeed` is `None`.
- Downstream types: `Object.movement` still reveals as `str | None` and
  `Object.element` as `str`. Task v1.0-04 achieved this by annotating the
  decorator `Callable[[Any], _T] -> _T`; a plain `@property` gives the same
  types natively, so that annotation (and its `# type: ignore`) is now
  superseded.

`obj.movement()` now raises `TypeError: 'str' object is not callable`.
