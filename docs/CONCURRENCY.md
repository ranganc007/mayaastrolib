# Concurrency & async

`mayaastrolib`'s calculation engine is synchronous and CPU-bound — it
calls into the Swiss Ephemeris C library via `pyswisseph`. This page
explains how to use it safely from threads and from async code.

## Thread safety

The Swiss Ephemeris C library is **not** fully thread-safe:

- `swe_set_sid_mode` (used for sidereal/Vedic charts) mutates
  process-global state. Two threads computing sidereal charts for
  different ayanamsas could interleave a `set_sid_mode` between another
  thread's `set_sid_mode` and its `calc_ut`.
- The library keeps internal static buffers and caches across calls.

- On some platforms the library's global state struct (`swed`) lives in
  **thread-local storage** — the Linux `pyswisseph` wheels are built this
  way, the macOS ones are not. On those builds `swe_set_ephe_path` applies
  only to the calling thread.

To make the engine safe, **every** `swisseph` entry point in
`mayaastrolib.ephem.swe` runs inside `_ephe_session()`, which does two
things: it takes a single reentrant lock (`_SWE_LOCK` — an `RLock` because
a few helpers nest calls, e.g. `sweFixedStar` → `_fixstar_mag`), and it
(re)applies the configured ephemeris path if the calling thread has not
seen it yet.

That second part is not optional. Setting the path once at import — on the
main thread — left worker threads on Linux with **no** ephemeris path, so
they silently fell back to the built-in Moshier ephemeris (positions off
by roughly 0.02″) and could not open the fixed-star catalogue at all.
Results from a thread pool therefore disagreed with the same computation
run synchronously. Fixed in Task v1.0-01b; pinned by
`EphemerisPathPerThreadTests` in `tests/test_concurrency.py`.

New code inside `swe.py` should use `_ephe_session()` rather than taking
`_SWE_LOCK` directly, so the path guarantee is never accidentally skipped.

The practical guarantee: **you can build charts from multiple threads
concurrently** (mixing tropical and sidereal) and every result is exactly
what you'd get computing them one at a time. This is verified in
`tests/test_concurrency.py`, which hammers a mixed work-list across a
thread pool and asserts byte-for-byte equality with the serial reference.

The trade-off is that the swisseph calls themselves run one at a time. They
are fast (microseconds to a few milliseconds each), so for typical
chart-per-request workloads the lock is not a bottleneck. If you need true
CPU parallelism for a large batch, run separate **processes** (each gets
its own swisseph state), e.g. via `concurrent.futures.ProcessPoolExecutor`.

## Async usage

Running a synchronous, CPU-bound chart computation directly on an asyncio
event loop would block every other coroutine for its duration. Use the
helpers in `mayaastrolib.aio`, which run the work in a thread-pool executor
(`loop.run_in_executor`) so the event loop stays responsive:

```python
from mayaastrolib.aio import afull_report, achart, afull_report_json
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

async def handler():
    report = await afull_report(
        Datetime("1990/06/15", "14:30", "+05:30"),
        GeoPos("28n36", "77e12"),
        zodiac="Sidereal",
    )
    return report
```

- `achart(date, pos, **kwargs)` → a `Chart` (same kwargs as `Chart`).
- `afull_report(date, pos, **kwargs)` → the full report dict.
- `afull_report_json(date, pos, **kwargs)` → the JSON string.

Because the executor threads contend on `_SWE_LOCK`, many concurrent
`afull_report` calls remain correct (proven in the test suite). For a
FastAPI endpoint, simply `await afull_report(...)` — the event loop is free
to serve other requests while each computation runs on a worker thread.

### FastAPI example

```python
from fastapi import FastAPI
from mayaastrolib.aio import afull_report
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

app = FastAPI()

@app.get("/chart")
async def chart(date: str, time: str, offset: str, lat: str, lon: str):
    return await afull_report(Datetime(date, time, offset), GeoPos(lat, lon))
```
