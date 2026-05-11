# Birth Chart Primer

A practical, opinion-light reference covering: how a birth chart is calculated, what the twelve houses are and traditionally signify, and what each planet is conventionally read to mean when placed in each house.

> **Scope note.** This document is *educational reference content* about astrological tradition. mayaastrolib computes the geometry; it does **not** generate interpretations. The interpretive material below is the standard Western traditional/modern hybrid view summarised so that consumers of the library know what the numbers they are computing have historically been read to mean. Astrology is not a science. Use this content for context, education, or building interpretive layers — not as truth claims.

---

## Part 1 — How a birth chart is calculated

A birth chart is the answer to the question: **"At a specific moment, from a specific point on Earth, where was each celestial body and which part of the local sky was it in?"** The calculation has six stages.

### Stage 1 — Collect the inputs

Three pieces of information are required, and a fourth is conventional:

| Input | Why it matters | Precision |
|---|---|---|
| Date (YYYY/MM/DD) | Anchors the year, month, day | Exact |
| Time of day (HH:MM, local) | The Earth rotates ~15°/hour, so wall-clock minute precision matters | **Critical** — see below |
| UTC offset (e.g. `+05:30`, `-08:00`) | Converts local time to a universal moment | Exact |
| Geographic location (lat, lon) | Determines the local horizon | Within ~1 km is plenty |
| House system (optional) | How to slice the local sky into 12 houses | Conventional choice |

#### Why time precision matters

The Ascendant — the degree of the zodiac rising at the eastern horizon — moves through one full zodiac sign (30°) every roughly two hours, which is **1° every ~4 minutes**. A 10-minute error in the recorded birth time can shift the Ascendant by 2°–3°, which is small within a sign but catastrophic if the time was near a sign boundary. House cusps inherit this same sensitivity. For this reason, professional astrologers ask for the recorded hospital time and, if unavailable, do "rectification" against known life events.

Planet positions, in contrast, are far less sensitive — the Moon moves ~0.5° per hour and outer planets barely budge over a day. So the Sun-sign and most planet-sign placements are robust against time uncertainty, while the rising sign and house placements are not.

#### What about timezones with DST?

`Datetime` accepts a fixed UTC offset, not an IANA timezone like `Europe/Dublin`. If the birth was during summer time, you must resolve "10:30 AM Dublin" to either `+00:00` (UTC, winter) or `+01:00` (BST, summer) yourself before constructing the `Datetime`. mayaastrolib will not do this for you — see `IDEAS.md` for the deferred plan to add IANA support.

### Stage 2 — Convert to a universal moment

The local time and UTC offset are folded into a single number called the **Julian Date** — a continuous count of days since 4713 BCE, the reference clock that the underlying astronomy library (Swiss Ephemeris) speaks. From this point on, the calculation is purely geometric.

### Stage 3 — Get the planet positions

For each celestial body in the requested object list, Swiss Ephemeris returns:

- **Ecliptic longitude** — the angle around the zodiac wheel, 0° to 360°, measured from the spring equinox point (in the tropical zodiac)
- **Latitude** — small deviation north or south of the ecliptic plane (mostly ignored in mainstream astrology)
- **Speed** — apparent angular velocity, in degrees per day; negative speed means apparent retrograde motion as seen from Earth

The sign placement is then trivial arithmetic: `int(longitude // 30)` gives a number 0–11 corresponding to Aries through Pisces. The position **within** the sign is `longitude % 30`.

### Stage 4 — Compute the Ascendant and Midheaven

These two angles define the local sky:

- **Ascendant (ASC, "rising sign")** — the degree of the zodiac rising at the eastern horizon at the birth moment, as seen from the birth location. Calculated from the geographic latitude, the Earth's axial tilt at the moment, and the local sidereal time.
- **Midheaven (MC, *medium coeli*)** — the degree of the zodiac on the local meridian (the imaginary north–south line directly overhead). The Sun reaches the MC at solar noon.

The two derived points (Descendant and Imum Coeli) are exactly opposite the ASC and MC.

### Stage 5 — Compute house cusps

The twelve house cusps divide the local sky into 12 numbered slices. Different *house systems* divide it differently. The four most common:

| House system | How it divides | Trade-off |
|---|---|---|
| **Placidus** | Time-based; divides the diurnal/nocturnal arcs each into thirds | Most popular in modern Western practice; breaks down at high latitudes |
| **Whole Sign** | Each entire zodiac sign = one house; 1st house = whole sign of Ascendant | Oldest known system; works at any latitude; simplest interpretively |
| **Equal** | 12 equal 30° wedges starting from the Ascendant | Simple; 10th house cusp is **not** the Midheaven |
| **Alcabitus** | Trisected semi-arcs (variant of Placidus method) | mayaastrolib's default (`HOUSES_DEFAULT`); medieval origin |

**Polar regions break Placidus.** Above ~66° latitude near the solstices, the dividing arcs become undefined. For births near the polar circles, use Whole Sign.

After this stage you know the longitude of each house cusp.

### Stage 6 — Cross-link planets to houses

Each planet's longitude is compared against the house cusps to find which house contains it. mayaastrolib does this once at chart construction (in `Chart._link_objects_to_houses`) and stamps `obj.house` on every Object and `house.objects` on every House. After this, no further calculation is needed — these are attribute lookups.

**Aspects** are computed lazily on demand: `aspects.getAspect(obj1, obj2, aspList)` returns an `Aspect` instance if the pair forms one of the requested angular relationships within orb, or `None` otherwise.

### A finished chart contains:

- 7–13 **objects** (planets and points) with absolute longitude, sign, sign-relative longitude, speed, retrograde state, and house assignment
- 12 **house cusps** with starting longitude, sign, size, and list of resident objects
- 2 **angles** (Ascendant, Midheaven)
- A computed **Moon phase**, **diurnal/nocturnal** designation, and other derived qualities
- **Aspects** — computable on demand between any pair of objects

---

## Part 2 — What is a house?

The celestial sphere is divided into the same 360° wheel by **two independent slicing schemes** that produce different but complementary information:

| Slicing | Anchored to | What it tells you |
|---|---|---|
| **Zodiac signs** | The seasons (tropical) or fixed stars (sidereal) | Which constellation/sign a planet is *absolutely* in |
| **Houses** | Your local horizon at the moment of birth | Which part of *your* sky a planet is in |

The two are orthogonal: a planet can be in any sign and any house. A given sign can span multiple houses (when a sign is "intercepted" inside a house). A given house can span multiple signs (more often). They answer different questions.

### What signs answer

"What is the *quality* of this energy?" Signs are read as flavours, temperaments, modes — fiery vs watery, fixed vs mutable, etc.

### What houses answer

"What *area of life* does this energy operate in?" Houses are read as domains — work, family, partnership, money, etc. — relative to the native (the person whose chart it is).

### The 12 houses, in standard Western reading

| House | Common name | Traditional domain | Modern reading |
|---|---|---|---|
| **1st** | House of Self | The body, appearance, vitality, the rising of the day | Identity, persona, "how others see you" |
| **2nd** | House of Substance | Movable goods, livelihood | Personal finances, possessions, values, self-worth |
| **3rd** | House of Brethren | Siblings, short journeys, communication | Communication, learning, neighbours, immediate environment |
| **4th** | House of Parents | The home, the father, ancestral land | Home, family of origin, roots, private life, the mother (modern) |
| **5th** | House of Children | Children, pleasures, gambling | Creativity, romance, children, play, self-expression |
| **6th** | House of Health | Illness, slaves, small animals, daily labour | Health, daily work, routine, service, pets |
| **7th** | House of Marriage | Spouse, open enemies, contracts | Partnership (romantic/business), one-on-one relationships |
| **8th** | House of Death | Death, inheritance, the spouse's money, the occult | Shared resources, transformation, intimacy, taboo, psychology |
| **9th** | House of Travel | Long journeys, religion, philosophy | Higher education, foreign cultures, beliefs, publishing |
| **10th** | House of Reign | Career, the king/government, the mother (traditional) | Career, public reputation, authority, the father (modern) |
| **11th** | House of Friends | Friends, hopes, allies | Friendships, networks, communities, future hopes |
| **12th** | House of Self-Undoing | Imprisonment, exile, large animals, hidden enemies | The unconscious, hidden things, isolation, spirituality, places of confinement |

> Notice the swap: the traditional 4th was the **father** and 10th was the **mother**; modern Western practice flipped them. Both readings are in current circulation. mayaastrolib does not pick one — it returns geometry; the consumer chooses the interpretive lens.

### Angular, succedent, cadent

Houses are also classified by their relationship to the four cardinal points (ASC, IC, DESC, MC):

| Class | Houses | Strength | Meaning |
|---|---|---|---|
| **Angular** | 1, 4, 7, 10 | Strong | Active, immediate, defining |
| **Succedent** | 2, 5, 8, 11 | Medium | Stabilising, consolidating |
| **Cadent** | 3, 6, 9, 12 | Weak | Mutable, distributing, transitional |

A planet in an angular house is traditionally considered to be at full strength; the same planet in a cadent house is considered weakened in expression (though not in skill or significance — the *expression* is muted, not the underlying nature).

### When houses go missing

If the birth time is unknown, the Ascendant cannot be computed reliably, so neither can the houses. In that case astrologers fall back to a **solar chart** (the Sun's position is treated as the 1st-house cusp) or skip house analysis entirely. mayaastrolib will compute houses from any time you give it; ensuring the time is right is your concern.

---

## Part 3 — A planet in a house: importance and traditional reading

Each planet has a **natural significance** (what kind of energy it is). Each house has a **natural domain** (what area of life it governs). A planet placed in a house is conventionally read as that planet's energy *expressing itself in* that area of life.

### The natural significance of each body

| Body | Traditional title | Core themes |
|---|---|---|
| **Sun** | Light of day | Identity, vitality, life force, ego, the father (modern) |
| **Moon** | Light of night | Emotions, instincts, habits, the body, the mother |
| **Mercury** | Messenger | Mind, speech, learning, commerce, siblings, short trips |
| **Venus** | Lesser benefic | Love, beauty, harmony, art, money, pleasure |
| **Mars** | Lesser malefic | Action, drive, anger, conflict, courage, sexuality |
| **Jupiter** | Greater benefic | Expansion, fortune, wisdom, philosophy, opportunity |
| **Saturn** | Greater malefic | Structure, limits, discipline, time, authority, fear |
| **Uranus** *(modern)* | The awakener | Sudden change, individuality, innovation, disruption |
| **Neptune** *(modern)* | The dissolver | Imagination, dreams, illusion, spirituality, escapism |
| **Pluto** *(modern)* | The transformer | Power, depth, death and rebirth, compulsion, the hidden |
| **Chiron** *(modern, asteroid)* | The wounded healer | Wound and healing, ancestral pain, mentorship |
| **North Node** | Rahu (Vedic) | Direction of growth, future task, what to develop |
| **South Node** | Ketu (Vedic) | Past patterns, gifts already known, what to release |

Outer planets and Chiron are 19th–20th century additions; classical astrology operated with the seven visible bodies (Sun through Saturn) only.

### The 10×12 grid: planet × house

Read these as **traditional starting points**, not verdicts. Real interpretation also weighs the sign, dignity, and aspects of the planet — "Mars in the 7th in Libra trine Jupiter" is a very different statement from "Mars in the 7th in Aries square Saturn." This grid gives the bare bones of "where the energy lives" before sign and aspect refine it.

#### Sun (identity, vitality)

| House | Reading |
|---|---|
| 1 | Strong sense of self; visible, central, leader-prone. |
| 2 | Identity tied to resources and self-worth; talent for earning. |
| 3 | Identity expressed through communication and learning. |
| 4 | Identity rooted in home and family lineage. |
| 5 | Identity expressed through creativity, performance, children. |
| 6 | Identity expressed through work, service, daily craft. |
| 7 | Identity formed through partnership; attracted to charismatic others. |
| 8 | Identity tested by transformation, shared resources, deep change. |
| 9 | Identity expressed through travel, study, belief systems. |
| 10 | Identity tied to public role, career, status — classic "career native." |
| 11 | Identity expressed through community, ideals, friendships. |
| 12 | Identity drawn to inner life, retreat, hidden service. |

#### Moon (emotions, instinct, body)

| House | Reading |
|---|---|
| 1 | Emotional life is highly visible; mood-driven persona. |
| 2 | Emotional security tied to material stability. |
| 3 | Strong emotional connection to siblings, immediate environment. |
| 4 | Deep attachment to home, mother, family — the Moon's natural house. |
| 5 | Emotional expression through play, romance, children. |
| 6 | Emotional patterns shape health and daily routine. |
| 7 | Emotional needs project onto partners; relationships are nurturing. |
| 8 | Emotional life is intense, secretive, transformative. |
| 9 | Emotional connection to foreign cultures, philosophies, travel. |
| 10 | Public-facing emotionality; career may involve the public, women, food. |
| 11 | Emotional fulfilment through community and chosen family. |
| 12 | Sensitive, private, sometimes overwhelmed; intuitive depth. |

#### Mercury (mind, communication)

| House | Reading |
|---|---|
| 1 | Quick, articulate, mentally restless persona. |
| 2 | Mind applied to money, value, material thinking. |
| 3 | Mercury's natural house — sharp communication, learning, networking. |
| 4 | Mental life rooted in family, home, ancestral stories. |
| 5 | Creative or playful expression of mind; teaching, performing. |
| 6 | Detailed, analytical mind; suited to craft, editing, healing. |
| 7 | Communication-driven partnerships; possible verbal sparring. |
| 8 | Investigative, depth-seeking mind; research, psychology, finance. |
| 9 | Big-picture thinker; philosophy, languages, publishing. |
| 10 | Mind directed at career and reputation; public communicator. |
| 11 | Mental life shared with networks; ideas-driven friendships. |
| 12 | Reflective, private mind; gifted in imagination, sometimes anxious. |

#### Venus (love, beauty, value)

| House | Reading |
|---|---|
| 1 | Charming, attractive, art-inclined persona. |
| 2 | Pleasure in beautiful things; potential earning through art or beauty. |
| 3 | Affectionate communication; harmony with siblings and neighbours. |
| 4 | A beautiful or harmonious home; love of family. |
| 5 | Romantic, creative, playful — Venus thrives here. |
| 6 | Pleasure in daily craft, service, pets. |
| 7 | Strong relationship orientation; charm in partnership — Venus's other natural house. |
| 8 | Intense attachments; possibly inheritance or shared wealth. |
| 9 | Love of foreign cultures, art, philosophy. |
| 10 | Public charm; possible career in art, beauty, diplomacy. |
| 11 | Many friends; alliances that are warm and supportive. |
| 12 | Private romantic life; secret loves, devotion, hidden generosity. |

#### Mars (drive, action, conflict)

| House | Reading |
|---|---|
| 1 | Direct, energetic, possibly combative persona. |
| 2 | Aggressive about resources; can earn through forceful effort. |
| 3 | Sharp speech; possible conflict with siblings or in transit. |
| 4 | Tension or activity in the home; restlessness with family. |
| 5 | Energetic creativity, sport, romantic pursuit. |
| 6 | Hardworking; possibly accident-prone or work-conflicted. |
| 7 | Conflict-prone partnerships; passionate matches. |
| 8 | Strong sexual energy; intensity around shared resources, transformation. |
| 9 | Crusading beliefs; argumentative philosophy; adventurous travel. |
| 10 | Career-driven, ambitious, possibly contentious in public role. |
| 11 | Activist friend groups; energetic alliances. |
| 12 | Hidden anger; covert action; energy needed for inner work. |

#### Jupiter (expansion, fortune, wisdom)

| House | Reading |
|---|---|
| 1 | Generous, optimistic, large-spirited persona. |
| 2 | Lucky with money; expansive resources, possibly excess. |
| 3 | Wisdom in everyday speech; teaching neighbours, siblings. |
| 4 | Blessed home or large family; lucky in property. |
| 5 | Joyful creativity, fortunate children, pleasure. |
| 6 | Lucky at work; healing professions favoured. |
| 7 | Beneficent partnerships; foreign-born or wise spouse. |
| 8 | Inheritance, shared wealth, depth of insight. |
| 9 | Jupiter's natural house — wisdom, travel, higher learning thrive. |
| 10 | Public success, expansive career, mentor-figure status. |
| 11 | Wide network, generous friends, fulfilled hopes. |
| 12 | Hidden generosity; spiritual depth; protection unseen. |

#### Saturn (structure, limits, time)

| House | Reading |
|---|---|
| 1 | Serious, reserved, possibly burdened persona; matures with time. |
| 2 | Slow-built resources; financial discipline or hardship. |
| 3 | Cautious, deliberate communication; possibly distant siblings. |
| 4 | Heavy or austere home; difficult relationship with parents. |
| 5 | Restrained creativity; serious about children; delayed pleasures. |
| 6 | Disciplined work life; chronic-health concerns possible. |
| 7 | Serious, committed partnerships; possibly older partner; or delays in marriage. |
| 8 | Slow but lasting transformation; cautious with shared resources. |
| 9 | Conservative beliefs; structured education; delayed long journeys. |
| 10 | Saturn's natural house — career through long labour; eventual authority. |
| 11 | Few but loyal friends; structured community ties. |
| 12 | Hidden burdens; karmic depth; potential for solitary discipline. |

#### Uranus (sudden change, individuality)

| House | Reading |
|---|---|
| 1 | Unconventional, electric, unpredictable persona. |
| 2 | Income comes and goes; non-traditional value system. |
| 3 | Disruptive ideas; unconventional siblings or learning. |
| 4 | Restless home; unconventional family. |
| 5 | Unusual creative gifts; possibly child-free by choice. |
| 6 | Erratic work patterns; technology in daily life. |
| 7 | Unconventional partnerships; sudden meetings and partings. |
| 8 | Sudden transformations; unusual relationship to shared resources. |
| 9 | Radical beliefs; sudden travel; iconoclastic philosophy. |
| 10 | Unconventional career; reputation for innovation or rebellion. |
| 11 | Innovative communities; technology- or activism-oriented friends. |
| 12 | Sudden insight; unusual spiritual experiences; freedom-via-solitude. |

#### Neptune (imagination, dissolution, spirituality)

| House | Reading |
|---|---|
| 1 | Dreamy, charismatic, sometimes elusive persona. |
| 2 | Confused or intuitive about money; vulnerable to financial illusion. |
| 3 | Poetic communicator; siblings shrouded in mystery. |
| 4 | Idealised or unclear family origins; strong intuition about home. |
| 5 | Imaginative creativity; possibly idealised romance or children. |
| 6 | Sensitive to work environment; chronic vague-symptom health issues possible. |
| 7 | Idealised partner; risk of projection or deception. |
| 8 | Permeable boundaries; mystical or addictive intensities. |
| 9 | Mystical philosophy; spiritual travel; visionary beliefs. |
| 10 | Public role tied to art, music, image — or scandal/illusion. |
| 11 | Idealistic communities; spiritual or artistic friends. |
| 12 | Neptune's natural house — strong mystical, imaginative, or escapist tendencies. |

#### Pluto (power, transformation, depth)

| House | Reading |
|---|---|
| 1 | Intense, magnetic, transformative persona. |
| 2 | Power dynamics around money and self-worth; financial rebirths. |
| 3 | Depth-seeking mind; intense sibling or neighbourhood dynamics. |
| 4 | Deep family wounds and transformations; ancestral patterns surface. |
| 5 | Intense creative or romantic life; transformative parenting. |
| 6 | Total reinvention of work, body, or routine. |
| 7 | Power dynamics in partnership; transformative relationships. |
| 8 | Pluto's natural house — depth psychology, taboo, profound change. |
| 9 | Transformative beliefs; obsession with truth or hidden knowledge. |
| 10 | Power-driven career; reputation built and remade. |
| 11 | Intense friendships; transformative communities or movements. |
| 12 | Hidden compulsions; deep unconscious work; psychological depth. |

#### Lunar Nodes — direction, not position

The Nodes are not bodies but mathematical points (where the Moon's orbit crosses the ecliptic). Always **exactly opposite** each other (180° apart).

- **North Node in a house** = the area of life where you are growing into something new; what is asked of this lifetime.
- **South Node in a house** = the area of life where past patterns are familiar but no longer the work; what to honour and release.

For example, North Node in the 10th / South Node in the 4th is read as "this lifetime asks you to step into public role and visibility, away from the comfort of family and home base." The opposite axis swaps the reading.

#### Chiron in a house

The "wound-and-healing" theme settles into the area of the chart it occupies. Chiron in the 1st = a wound around identity; in the 7th = a wound around partnership; in the 4th = a wound around home or parent. The same placement is also where the native typically becomes a healer for others.

---

## Part 4 — A worked example

Consider a person born **1985-03-14, 21:30 IST, Chennai (13°5′N 80°16′E)**.

```python
from mayaastrolib import const
from mayaastrolib.chart import Chart
from mayaastrolib.datetime import Datetime
from mayaastrolib.geopos import GeoPos

date = Datetime("1985/03/14", "21:30", "+05:30")
pos = GeoPos("13n05", "80e16")
chart = Chart(date, pos, hsys=const.HOUSES_PLACIDUS, IDs=const.LIST_TROPICAL_DEFAULT)
```

Reading the result:

| Body | Sign | House | Plain reading (rough sketch) |
|---|---|---|---|
| Sun | Pisces | 5th | Identity expressed through creativity, romance, play; Piscean flavour adds intuitive, artistic colouring. |
| Moon | Capricorn | 3rd | Emotional life ties to communication, siblings, learning; Capricorn adds restraint, structure to the feeling life. |
| Mercury | Pisces | 5th | Mind plays in creative/imaginative space; speech is poetic, less literal. |
| Mars | Aries | 10th | Drive directed at public role/career; Aries gives bold, pioneering quality. |
| Jupiter | Aquarius | 8th | Wisdom or expansion through depth-work and shared resources; Aquarian, unconventional quality. |
| North Node | Pisces | 9th | Growth direction: intuitive, expansive belief; toward higher meaning, away from analytical 3rd-house comfort (South Node). |

**A reading is not just "planet in house."** Each line above starts with the geometry mayaastrolib gives you. To go further you'd weigh:

1. **Sign** — does the planet like its sign? (See *dignities*: rulership, exaltation, etc.)
2. **Aspects** — what other planets is it talking to? A trine to Jupiter sweetens; a square to Saturn complicates.
3. **House ruler** — what's happening to the planet that rules the house's sign? (Traditional technique: "the lord of the 5th, by sign and by aspect, also describes the 5th.")
4. **The bigger pattern** — angles, stelliums, chart shape, etc.

mayaastrolib supplies the ingredients for all of these. The cooking is the consumer's craft.

---

## Where this leaves you

- For the layperson view — **[FAQ.md](FAQ.md)**.
- For the calculation walkthrough at code level — **[HOW-IT-WORKS.md](HOW-IT-WORKS.md)**.
- For the demo that exercises this — **[`mayaastro-demo`](../../mayaastro-demo)**.
- For migrating method-style code to property-style — **[PROPERTY-MIGRATION.md](PROPERTY-MIGRATION.md)**.

If you want to build an interpretive layer on top of mayaastrolib, this primer is the contract: house meanings, planet meanings, and the convention for combining them. Sign meanings, dignity scoring, and aspect interpretation are the natural next layers — the dignity numbers are computable directly via `mayaastrolib.dignities.essential`; sign and aspect interpretation remain your design.
