# topical_almuten.py.broken — archived

This file has had a SyntaxError since at least 2021-04-05 (upstream commit "Update topical_almuten.py"). Bracket placement at lines 102 and 103 is wrong:

    TA_LIST.extend([chart.getObject(essential.dayTrip(chart.getHouse(const.HOUSE4).sign])))

The `]` and `)` are swapped — should likely be `…HOUSE4).sign))])`.

Nothing imports this file. It appears to be experimental Persian/Vedic-nativity work (topical almuten is a technique with Vedic parallels) that may be relevant to Phase 2 of the fork (Vedic unification). Archived rather than fixed because we do not yet understand the original author's intent and don't want to silently change behaviour we don't have tests for.

To revisit: rename back to `.py`, fix the brackets, write tests. Until then, ruff and import scanners skip it because of the `.broken` suffix.
