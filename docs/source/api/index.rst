API reference
=============

Everything documented here is part of the frozen public surface — each
module declares ``__all__`` and autodoc honours it, so this reference and
the stability contract in ``docs/API-STABILITY.md`` cannot drift apart.

Core
----

.. toctree::
   :maxdepth: 1

   chart
   object
   aspects
   datetime
   geopos
   const
   angle
   lists
   utils
   props
   report
   aio

Vedic (Jyotisha)
----------------

See ``docs/API-STABILITY.md`` for the fidelity tiering: some of these
modules compute a determinate classical result, others ship a documented
approximation whose values may be refined in a minor release.

.. toctree::
   :maxdepth: 1

   vedic_ayanamsa
   vedic_nakshatras
   vedic_divisional
   vedic_dasha
   vedic_ashtakavarga
   vedic_sadesati
   vedic_kp
   vedic_shadbala
   vedic_tajika
   vedic_tajika_bala
   vedic_tajika_aspects
   vedic_upagrahas
   vedic_yogas
