"""Concurrency / thread-safety + async tests — Task 047 (0.5.0 #3).

These prove the engine is safe to drive from a thread pool (the basis of
the async helpers): the same inputs computed concurrently must produce
byte-for-byte the same serialized report as computed serially. Because
every Swiss Ephemeris call is serialised behind one reentrant lock, mixed
tropical/sidereal concurrent computation cannot corrupt the global
``set_sid_mode`` state.
"""

import asyncio
import unittest
from concurrent.futures import ThreadPoolExecutor

# tests/ is not a package; pytest puts it on sys.path (importmode=prepend).
from fixstar_support import requires_fixstar_data

from mayaastrolib import const
from mayaastrolib.aio import achart, afull_report, afull_report_json
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos
from mayaastrolib.report import full_report

# A spread of (date, time, offset, lat, lon, zodiac) work items, mixing
# tropical and sidereal so concurrent set_sid_mode races would show up.
_CASES = [
    ("1990/06/15", "14:30", "+05:30", "28n36", "77e12", const.ZODIAC_TROPICAL),
    ("1990/06/15", "14:30", "+05:30", "28n36", "77e12", const.ZODIAC_SIDEREAL),
    ("1879/03/14", "11:30", "+00:00", "48n24", "10e00", const.ZODIAC_TROPICAL),
    ("1879/03/14", "11:30", "+00:00", "48n24", "10e00", const.ZODIAC_SIDEREAL),
    ("2001/09/11", "08:46", "-04:00", "40n42", "74w00", const.ZODIAC_TROPICAL),
    ("2001/09/11", "08:46", "-04:00", "40n42", "74w00", const.ZODIAC_SIDEREAL),
]


def _report_for(case):
    date_s, time_s, off, lat, lon, zodiac = case
    return full_report(
        Datetime(date_s, time_s, off),
        GeoPos(lat, lon),
        zodiac=zodiac,
        vedic=True,  # exercises the sidereal calc path heavily
    )


class ThreadSafetyTests(unittest.TestCase):
    def test_serial_reference_is_stable(self):
        # Sanity: computing the same case twice serially is identical.
        a = _report_for(_CASES[1])
        b = _report_for(_CASES[1])
        self.assertEqual(a, b)

    def test_concurrent_matches_serial(self):
        # Build a serial reference, then hammer the same work-list across
        # many threads in shuffled, repeated order and require identical
        # results — no cross-talk between tropical/sidereal computations.
        reference = {i: _report_for(c) for i, c in enumerate(_CASES)}
        work = [(i, c) for _ in range(8) for i, c in enumerate(_CASES)]

        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(lambda item: (item[0], _report_for(item[1])), work))

        self.assertEqual(len(results), len(work))
        for idx, report in results:
            self.assertEqual(report, reference[idx], f"case {idx} diverged under threads")

    @requires_fixstar_data
    def test_fixedstar_under_threads(self):
        # sweFixedStar nests _fixstar_mag inside the same lock (RLock
        # reentrancy); pull stars concurrently to exercise it.
        def grab():
            d = Datetime("2000/01/01", "12:00", "+00:00")
            chart = Chart(d, GeoPos("0n00", "0e00"))
            return chart.getFixedStar(const.STAR_ALGOL).lon

        with ThreadPoolExecutor(max_workers=8) as ex:
            lons = list(ex.map(lambda _: grab(), range(32)))
        self.assertEqual(len(set(round(x, 9) for x in lons)), 1)


class AsyncHelperTests(unittest.TestCase):
    def test_achart_returns_chart(self):
        async def main():
            return await achart(Datetime("1990/06/15", "14:30", "+05:30"), GeoPos("28n36", "77e12"))

        chart = asyncio.run(main())
        self.assertIsInstance(chart, Chart)

    def test_afull_report_matches_sync(self):
        date = Datetime("1990/06/15", "14:30", "+05:30")
        pos = GeoPos("28n36", "77e12")
        sync = full_report(date, pos, zodiac=const.ZODIAC_SIDEREAL)

        async def main():
            return await afull_report(date, pos, zodiac=const.ZODIAC_SIDEREAL)

        self.assertEqual(asyncio.run(main()), sync)

    def test_afull_report_json_is_json(self):
        import json

        async def main():
            return await afull_report_json(
                Datetime("1990/06/15", "14:30", "+05:30"), GeoPos("28n36", "77e12")
            )

        self.assertEqual(json.loads(asyncio.run(main()))["schema_version"], 1)

    def test_gather_many_reports_concurrently(self):
        # asyncio.gather over the executor-backed helpers must match the
        # serial results for each case.
        async def main():
            tasks = []
            for date_s, time_s, off, lat, lon, zodiac in _CASES:
                tasks.append(
                    afull_report(
                        Datetime(date_s, time_s, off),
                        GeoPos(lat, lon),
                        zodiac=zodiac,
                        vedic=True,
                    )
                )
            return await asyncio.gather(*tasks)

        results = asyncio.run(main())
        for case, report in zip(_CASES, results, strict=True):
            self.assertEqual(report, _report_for(case))


if __name__ == "__main__":
    unittest.main()
