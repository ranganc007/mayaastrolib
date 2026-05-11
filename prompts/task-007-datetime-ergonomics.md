# Task 007: Datetime Ergonomics

## Context

You are working in the `mayaastrolib` repository. Before doing anything:

1. Read `CLAUDE.md` in full.
2. Read the existing `mayaastrolib/datetime.py` carefully — understand the `Date`, `Time`, `Datetime` classes and the JDN conversion logic.
3. Read `docs/PROJECT-LOG.md` for recent task entries.
4. Confirm Task 006 has been merged to `development`:

   ```
   git log --oneline development -5
   ```

   Should show Task 006 commits at the top (Object–Chart integration). If not, STOP.

5. Confirm `pytest tests/` passes cleanly. The 33+ test baseline must hold.

## Why this task exists

The demo webapp surfaced this friction: every consumer with a Python `datetime.datetime` object has to do a string round-trip to construct a `mayaastrolib.Datetime`:

```python
# What every consumer does today
import datetime as pydt
now = pydt.datetime.now(pydt.timezone.utc)
mdate = Datetime(now.strftime("%Y/%m/%d"), now.strftime("%H:%M"), "+00:00")
```

This is dumb. Three problems:
1. The strftime dance is boilerplate everyone writes
2. Going through strings drops sub-second precision (Datetime supports seconds, but the strftime `%H:%M` doesn't)
3. There's no `Datetime.now()` so "what's the sky doing right now" requires the `import datetime as pydt` pattern just to get the current moment

Fixing this is small, non-breaking, and removes the most common friction point in the library.

## Task scope

Add three classmethods to `Datetime`:

### 1. `Datetime.from_pydatetime(dt, utcoffset=None)`

Construct a `Datetime` from a Python `datetime.datetime` object.

```python
@classmethod
def from_pydatetime(cls, dt, utcoffset=None):
    """Construct a Datetime from a Python datetime.datetime.

    Args:
        dt: A datetime.datetime instance. May be naive or timezone-aware.
        utcoffset: UTC offset string like "+05:30" or "-08:00".
            Required if `dt` is naive (no tzinfo).
            If `dt` is aware AND utcoffset is None, derived from dt.tzinfo.
            If `dt` is aware AND utcoffset is given, utcoffset wins (but
            verify they match and warn if they don't).

    Returns:
        A new Datetime instance.

    Raises:
        ValueError: if dt is naive and utcoffset is not provided, or
            if utcoffset format is invalid.

    Example:
        >>> import datetime as pydt
        >>> now = pydt.datetime.now(pydt.timezone.utc)
        >>> mdate = Datetime.from_pydatetime(now)
    """
    ...
```

Implementation notes:
- Handle `dt.microsecond` properly — round or truncate to whole seconds (the existing `Time` class supports floats; preserve precision if the underlying type allows)
- For aware datetimes, extract the offset as `timedelta` from `dt.utcoffset()` and convert to the `+HH:MM` string format
- For naive datetimes without explicit `utcoffset`, raise `ValueError` with a clear message — DO NOT default silently to UTC

### 2. `Datetime.now(utcoffset='+00:00')`

Get the current moment as a `Datetime`.

```python
@classmethod
def now(cls, utcoffset='+00:00'):
    """Return a Datetime representing the current moment.

    Args:
        utcoffset: UTC offset for the returned Datetime. Defaults to UTC.
            Note that the underlying time is always wall-clock UTC; the
            offset only affects how times are displayed when subsequently
            formatted. To get a chart for "right now in Dublin," use
            utcoffset="+01:00" (BST) or "+00:00" (GMT) depending on
            current DST state — this method does not handle DST.

    Returns:
        A Datetime for the current UTC moment, labelled with the given offset.

    Example:
        >>> mdate = Datetime.now()                  # UTC
        >>> mdate = Datetime.now(utcoffset='-05:00') # US Eastern (no DST awareness)
    """
    import datetime as _pydt
    now_utc = _pydt.datetime.now(_pydt.timezone.utc)
    return cls.from_pydatetime(now_utc, utcoffset=utcoffset)
```

The DST disclaimer in the docstring is important. We're not solving timezone awareness in this task (that's a bigger discussion — see "Out of scope" below).

### 3. `Datetime.to_pydatetime()`

The inverse of `from_pydatetime`. Round-tripping is a basic invariant we should support.

```python
def to_pydatetime(self):
    """Convert to a Python datetime.datetime with timezone info.

    Returns:
        A timezone-aware datetime.datetime in the offset originally
        specified at construction time.

    Example:
        >>> mdate = Datetime("2015/03/13", "17:00", "+00:00")
        >>> py = mdate.to_pydatetime()
        >>> py.tzinfo.utcoffset(py)  # timedelta(0)
    """
    ...
```

This needs to convert the `Date.year/month/day`, `Time.hour/minute/second`, and the UTC offset string into a Python `datetime.datetime` with `timezone(timedelta(...))` as tzinfo.

## Out of scope (deliberately)

These are tempting and the audit list flagged them, but each is its own task:

- **IANA timezone awareness (`Datetime.from_zoneinfo("Europe/Dublin", date, time)`).** This requires `zoneinfo` (3.9+, fine) plus a real DST-aware conversion. Worthwhile but warrants its own task because it adds a meaningful dependency and changes the mental model of the library from "UTC offset is just a number" to "timezone is a real concept". Defer.

- **Parsing ISO 8601 strings (`Datetime.from_iso("2015-03-13T17:00+00:00")`).** Useful, but not as broadly useful as `from_pydatetime`. Add later if friction surfaces.

- **`Datetime.utcnow()`.** Python deprecated `datetime.utcnow()` in 3.12. Don't propagate the misnamed pattern. `now(utcoffset='+00:00')` already covers it.

## Tests

Add `tests/test_datetime_ergonomics.py`:

```python
"""Tests for Datetime classmethods added in Task 007."""

import datetime as pydt
import unittest
import warnings

from mayaastrolib.datetime import Datetime


class FromPyDatetimeTests(unittest.TestCase):

    def test_aware_datetime_uses_its_own_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0, tzinfo=pydt.timezone.utc)
        mdate = Datetime.from_pydatetime(dt)
        self.assertEqual(str(mdate.date), "2015/03/13")
        self.assertEqual(str(mdate.time), "17:00:00")
        # offset should be +00:00 derived from UTC
        # Exact assertion depends on how Datetime stores offset

    def test_naive_datetime_requires_explicit_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0)  # naive
        with self.assertRaises(ValueError):
            Datetime.from_pydatetime(dt)

    def test_naive_datetime_with_offset(self):
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        mdate = Datetime.from_pydatetime(dt, utcoffset="+00:00")
        self.assertEqual(str(mdate.date), "2015/03/13")

    def test_offset_with_minutes(self):
        # India is +05:30 — half-hour offsets must work
        dt = pydt.datetime(2015, 3, 13, 17, 0)
        mdate = Datetime.from_pydatetime(dt, utcoffset="+05:30")
        # Verify the offset round-trips correctly

    def test_aware_datetime_with_conflicting_offset_warns_or_raises(self):
        # If dt is aware AND utcoffset is given AND they don't match,
        # what happens? Define and test the behaviour.
        dt = pydt.datetime(2015, 3, 13, 17, 0, tzinfo=pydt.timezone.utc)
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            Datetime.from_pydatetime(dt, utcoffset="+05:30")
            # Either: warning is emitted, OR ValueError is raised. Pick one.


class NowTests(unittest.TestCase):

    def test_now_returns_datetime_close_to_actual_now(self):
        before = pydt.datetime.now(pydt.timezone.utc)
        mdate = Datetime.now()
        after = pydt.datetime.now(pydt.timezone.utc)

        # Convert mdate back and check it falls between before/after
        py_mdate = mdate.to_pydatetime()
        self.assertLessEqual(before, py_mdate)
        self.assertLessEqual(py_mdate, after)

    def test_now_with_offset(self):
        mdate = Datetime.now(utcoffset="+05:30")
        # Underlying moment is UTC, but offset is preserved
        # Specific assertion depends on Datetime internals

    def test_now_default_is_utc(self):
        mdate = Datetime.now()
        # Default offset should be +00:00


class RoundTripTests(unittest.TestCase):

    def test_from_pydatetime_to_pydatetime_roundtrip(self):
        original = pydt.datetime(
            2015, 3, 13, 17, 30, 45,
            tzinfo=pydt.timezone(pydt.timedelta(hours=5, minutes=30)),
        )
        mdate = Datetime.from_pydatetime(original)
        result = mdate.to_pydatetime()

        self.assertEqual(original.year, result.year)
        self.assertEqual(original.month, result.month)
        self.assertEqual(original.day, result.day)
        self.assertEqual(original.hour, result.hour)
        self.assertEqual(original.minute, result.minute)
        self.assertEqual(original.second, result.second)
        self.assertEqual(
            original.utcoffset(),
            result.utcoffset(),
        )

    def test_microsecond_precision(self):
        # Decide: do we preserve microseconds or round to seconds?
        # If we round, document. If we preserve, test.
        ...


if __name__ == "__main__":
    unittest.main()
```

The `test_aware_datetime_with_conflicting_offset_warns_or_raises` test is asking you to make a decision. Either behaviour is defensible — pick one, document it, test it. My recommendation: warn rather than raise. It's friendlier and consistent with how Python's own `datetime` handles overlapping data.

## Update the demo

If the demo webapp at `/opt/homebrew/var/www/mayaastro-demo/app.py` uses the strftime dance, update it to use `Datetime.from_pydatetime()` or `Datetime.now()`. The demo is not in the repo but should benefit from the new API immediately.

If you don't have access to the demo (it's outside the repo), skip this and note in the log.

## Update CHANGELOG.md

Under `[Unreleased]`:

```markdown
### Added
- `Datetime.from_pydatetime(dt, utcoffset=None)` — construct from a Python datetime
- `Datetime.now(utcoffset='+00:00')` — current moment as Datetime
- `Datetime.to_pydatetime()` — convert to a Python datetime.datetime with timezone

### Notes
- DST-aware timezone handling (e.g. via IANA names like 'Europe/Dublin') is
  deliberately deferred. Use a fixed UTC offset for now. See IDEAS.md.
```

Add to `docs/IDEAS.md`:

```markdown
## DST-aware timezone handling for Datetime

**Status:** Deferred. Likely Task 0XX.

Currently `Datetime` takes a fixed UTC offset string ("+05:30"). For
locations with daylight saving, consumers must know the correct offset
for the chart's date.

A future task should add `Datetime.from_zoneinfo("Europe/Dublin", date,
time)` using the stdlib `zoneinfo` module. Decisions to make:
- Add a tzdata dependency, or rely on system tzdb?
- Store the IANA name in Datetime, or convert to fixed offset at construction?
- Backwards compatibility for the existing offset-string API?
```

## Process

1. Branch:

   ```
   git checkout development
   git pull origin development
   git checkout -b task-007-datetime-ergonomics
   ```

2. Commits:
   - `feat: add Datetime.from_pydatetime and to_pydatetime`
   - `feat: add Datetime.now classmethod`
   - `test: add datetime ergonomics tests`
   - `docs: update CHANGELOG and IDEAS for Task 007`

3. Pre-completion checklist:
   - `ruff format --check .` passes
   - `ruff check .` passes
   - `mypy mayaastrolib/` — no new errors
   - `pytest -x` passes — all tests including new ones
   - Round-trip test passes for at least one half-hour offset (India test case)

4. Append PROJECT-LOG.md entry covering:
   - The behaviour chosen for the "conflicting offset" case (warn or raise)
   - Whether microsecond precision is preserved or rounded
   - Whether the demo was updated (yes/no with reason)

5. Push:

   ```
   git push -u origin task-007-datetime-ergonomics
   ```

6. Verify CI green.

7. DO NOT merge. Leave for human review.

## Definition of done

- Three classmethods exist: `from_pydatetime`, `now`, `to_pydatetime`
- All have docstrings with examples
- Round-trip test passes (datetime → Datetime → datetime preserves all fields)
- Half-hour offsets work (India test case)
- Naive-datetime-without-offset raises ValueError clearly
- All existing tests still pass
- CHANGELOG and IDEAS updated
- CI green

## If something goes wrong

Most likely issue: the existing `Datetime` constructor's UTC offset string format is more constrained than expected, and converting from `timedelta(hours=5, minutes=30)` to "+05:30" needs care. If this turns out to need more work than expected:

1. Don't expand scope — get `from_pydatetime` working for whole-hour offsets first
2. Skip half-hour test, document as known issue in PROJECT-LOG.md
3. Add to IDEAS.md as a follow-up

The point of this task is to remove the most common boilerplate, not to perfect timezone handling. Half-hour offsets are nice to have; they're not the primary success metric.
