# FINAL PRESENTATION — SPEAKER NOTES

## Suitability Analysis for Rainwater Harvesting Site Planning Using GIS
**Group 11** · Yesha Palan · Akshay Khandor · Aditya Dubey · Arya Chimurkar
**Guide:** Mr. Chirag Ramesh Desai

**Deck this covers:** `RWH_Review_Presentation.pptx.pdf` — 33 slides, as exported 27 August 2026.
**Prepared:** 27 August 2026. Every number cross-checked against a live run of the codebase.

---

## HOW TO USE THIS DOCUMENT

This is **source material for a speaking script**, not the script itself. It is
deliberately over-supplied: each slide carries more than you will say, split
into three tiers so the script writer knows what to keep.

| Tier | Meaning |
|---|---|
| **MUST SAY** | If you skip this, the slide has not been explained. |
| **USEFUL CONTEXT** | Include if the pace allows. Drop first when running late. |
| **ONLY IF ASKED** | Do not say this aloud. It is here so you can answer a question. |

**Verification tags used below:**
- **[VERIFIED]** — re-measured by running the code on 26–27 August 2026.
- **[DOC]** — recorded in `CHANGELOG.md` / `docs/METHODOLOGY.md`; describes something no longer re-measurable (usually a "before the fix" figure).
- **[EXTERNAL]** — not in the repository at all. Know your source before you say it.

### ⚠ Read this before anything else

**Two structural problems in the deck are still present.** They are not about
your work — the technical content is sound — they are about the literature
review contradicting the rest of the deck. Full detail in **Slide 4** and in
*Overall Review §5*. Decide what to do about them tonight, not in the room.

---

# SLIDE 1 — Title Slide

### What the slide shows
Project title, four team members with roll numbers, guide's name, Group ID 11,
department and college branding.

### Main speaking points
Introduce the team, the guide, and the project title. That is all this slide is for.

**MUST SAY**
- Project title in full.
- Who is presenting and who guided the work.
- One sentence of orientation so the audience knows the domain before slide 2 —
  something like: *"This is a GIS-based decision-support system for choosing
  where to build rainwater harvesting structures in Chandrapur district."*

**Do not** start explaining methodology here. Slide 2 does that.

**Estimated speaking time:** 20–30 seconds

**Transition to next slide:**
"Let me start with the problem we set out to solve — and there are actually two of them."

---

# SLIDE 2 — Problem Definition

### What the slide shows
Two columns — the practical problem and the methodological problem — over four
statistic tiles: 11,443 km², 123,555 grid cells, 6 criteria, 1 ranked shortlist.

### Main speaking points

**Point: The practical problem — rain arrives, then leaves**
Chandrapur is not short of rain. It averages **1,493 mm a year** over 2014–2024
[VERIFIED — this is the district mean stored in `data/rainfall.tif`'s own
metadata]. The scarcity comes from *timing and retention*: the rain falls in a
short monsoon window and most of it runs off. Groundwater is under additional
pressure from urban and industrial demand.

Say plainly why siting matters: a structure on steep ground, in unsuitable soil,
or far from where water is needed delivers no recharge and wastes public money.

**Point: Choosing well is infeasible by hand**
The district is 11,443 km². Making six separate judgements about every location
across that area is not something a person can do manually — this is the reason
the problem needs a computational method at all.

**Point: The methodological problem — this is your real contribution**
This is the more important half of the slide and the one that distinguishes your
project from a typical undergraduate GIS exercise. Say that GIS-based
Multi-Criteria Decision Analysis is a well-established technique, **but** three
weaknesses recur in how it is applied:

1. Criterion scores are stretched to fit whatever data is at hand — which can
   flatten a layer until it carries no information.
2. Expert weights are asserted, never tested.
3. The choice of mathematical method is never isolated from the data.

Then set the expectation for the rest of the talk: *"We identified all three in
our own first implementation, and the rest of this presentation is largely about
how we fixed them."*

**Point: The four statistics**
- **11,443 km²** — the official district area. You analysed 11,412.5 km² of it,
  99.7%. Don't explain that here; slide 10 does.
- **123,555 grid cells** — the number of ~300 m cells inside the district. This
  is the unit of analysis. [VERIFIED]
- **6 criteria** — slope, rainfall, soil, drainage density, land cover,
  settlement proximity.
- **1 ranked shortlist** — the deliverable: 25 sites in priority order.

**Why:** The problem is framed as both practical and methodological because a
purely practical framing would make this an application exercise, and the
methodological corrections are what the project actually contributes.

**MUST SAY:** both halves of the slide; the fact that you found the three
weaknesses in your *own* earlier work.
**USEFUL CONTEXT:** the four statistics as orientation.
**ONLY IF ASKED:** where the 1,493 mm figure comes from (CHIRPS satellite
rainfall, 11 annual rasters averaged — slide 22 covers it).

### Likely reviewer questions

**Likely Question:** Why Chandrapur specifically?
**Short Answer:** It has the defining contradiction — high monsoon rainfall but
genuine water scarcity — and complete open data coverage, so the work is
reproducible.
**Reasoning:** All seven datasets are free and global, so nothing about the
method is specific to this district.
**Evidence:** Data sources table, slide 11.
**Caveat:** [EXTERNAL] The groundwater-decline claim is context from the domain,
not something measured in this project. Do not present it as your finding.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"So why does this matter enough to build a system for it?"

---

# SLIDE 3 — Motivation and Necessity

### What the slide shows
Six numbered motivation points in a two-column grid.

### Main speaking points

Do **not** read all six aloud. Pick three, mention the rest as a group. The
strongest three are 1, 5 and 6.

**Point 1: Rainwater is lost as runoff — with a number attached**
This is the only motivation point backed by your own computation, so lead with
it. At a **100 mm design storm** the district mean runoff coefficient is
**0.354**, and built-up land reaches **0.61** [VERIFIED — recomputed:
0.354 district mean, 0.610 for built-up at CN 85].

Explain the coefficient simply: *"a runoff coefficient of 0.61 means 61% of the
rain that falls on built-up land leaves as surface runoff instead of soaking
in."*

**Why a 100 mm design storm rather than the annual total:** SCS-CN is an event
model — feeding it the annual total collapses every land-cover class to nearly
the same value and the map carries no information. [VERIFIED: at 1,493 mm,
forest gives 0.85 and built-up 0.965 — almost indistinguishable.] Keep this in
reserve; it belongs on slide 23.

**Point 5 and 6: Public money, and reasons rather than a map**
These two set up your explainability work. Point 6 is the sentence that justifies
half the system: *"A recommendation that cannot be challenged cannot be
trusted."* That is why every site carries its own justification.

**Point 4: Open data is now sufficient**
Worth one sentence because it supports transferability — the method moves to any
district without buying data.

**MUST SAY:** points 1, 5, 6.
**USEFUL CONTEXT:** point 4 (transferability), point 3 (traditional methods
consider factors one at a time).
**ONLY IF ASKED:** the derivation of the runoff coefficient; why runoff is
computed but deliberately *not* used as a weighted criterion (slide 23).

### Likely reviewer questions

**Likely Question:** Where does 0.354 come from?
**Short Answer:** From the SCS Curve Number model applied per cell using our land
cover and soil layers, for a 100 mm storm, then averaged over the district.
**Evidence:** `derived_maps.py`; reproducible with `python derived_maps.py`.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"To position our work, we reviewed the existing literature in two groups."

---

# SLIDE 4 — Literature Review (LLM / GIS-agent papers)

## ⚠ SPECIAL HANDLING — READ THIS CAREFULLY

### The problem

This slide presents four papers — GIS Copilot, GIScience in the Era of AI,
Barrier-free GeoQA, GPT-Based Text-to-SQL — and says they provide *"the technical
foundation for the query-to-action transformation used in this project"* and
*"influences the query interpretation layer, enabling intuitive planning queries
in natural language."*

**That layer does not exist in your project.** The natural-language query
component was removed from scope on 29 July 2026 [DOC — `CHANGELOG.md`, Sprint 1
§M]. Three separate contradictions follow:

1. **Slide 20 of this same deck says so explicitly** — "Natural-language layer
   removed from scope."
2. **These four papers do not appear in your References slide at all.** Slide 33
   lists ten references, none of them these.
3. Slides 5–6 number the real RWH papers **[5]–[12]** precisely because these
   four occupy [1]–[4] — but slide 33 numbers those same papers **[1]–[8]**. The
   citations are off by four.

An examiner who reads slide 4 will ask about your NLP component, and slide 20
will contradict whatever you answer.

### Recommendation: delete this slide

Slides 5 and 6 already carry eight genuine GIS-MCDA papers, and slide 7 does the
analytical work a literature review actually needs. Deleting slide 4 also fixes
the citation mismatch — renumber slides 5–6 to [1]–[8] and everything aligns
with slide 33 and with slide 7, which already uses the new numbering.

**This also saves ~30 seconds of a presentation that is already long.**

### If you keep the slide anyway

Do not describe these papers as foundations of your system. Reframe them as
scope history, in one sentence and then move on:

> "Our original proposal included a natural-language query interface, and these
> four papers supported that. We removed that component in July to concentrate on
> methodological correctness — so we include them here for scope history, not as
> a foundation of the final system."

That is honest, it pre-empts the contradiction, and it takes ten seconds. **Do
not** read the "Relation to This Topic" column aloud — every entry in it
describes a component you do not have.

**Estimated speaking time:** 0 seconds if deleted (recommended) · 20–30 seconds
if retained with the reframing above.

**Transition to next slide:**
If deleted: go straight from slide 3 to "We reviewed eight studies that apply
GIS-MCDA to rainwater harvesting specifically."
If retained: "The papers that actually shaped the final system are these eight."

---

# SLIDE 5 — Literature Review (RWH studies, part 1)

### What the slide shows
Four GIS-MCDA rainwater-harvesting studies in a table: purpose, key conclusions,
and relevance to your work. Currently numbered [5]–[8].

### Main speaking points

Do **not** read the table. Summarise the pattern, then pull out the two numbers
you will reuse later.

**Point: The common pattern**
All four use GIS-MCDA with AHP weighting and weighted overlay. That is the
mainstream approach and it is what you implemented as your baseline. Say that
explicitly — your baseline is the standard method, which is what makes your
comparisons meaningful.

**Point: Seif et al. — 18.85% area suitable**
Remember this figure. It is the lower bound of the suitability range you compare
against on slide 18. Your own result is 18.51%.

**Point: Mustapha et al. — AUC up to 0.93**
This is the validation benchmark you *cannot* match yet, and being upfront about
that is better than being caught. It shows a validated model is achievable when
ground-truth data exists. Slide 29 explains why yours does not.

**Point: Al-Hasani et al. — climate projections**
Relevant because it is the closest thing in the reviewed set to temporal
analysis, which appears in your future work.

**MUST SAY:** that all four use AHP + weighted overlay, which is your baseline.
**USEFUL CONTEXT:** the 18.85% figure and the 0.93 AUC as benchmarks.
**ONLY IF ASKED:** details of individual papers.

⚠ **Citation numbering:** if you have not renumbered, be aware that when you say
"reference 5", the References slide shows that paper as [1].

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"The remaining four studies add sensitivity analysis and runoff modelling."

---

# SLIDE 6 — Literature Review (RWH studies, part 2)

### What the slide shows
Four more studies: Wadi Sarkhar (Iraq), Awi Zone (Ethiopia), semi-arid Ethiopia,
Western Desert (Iraq). Currently numbered [9]–[12].

### Main speaking points

**Point: Resen et al. — 34.33% suitable, and sensitivity analysis**
Two things to take from this. First, 34.33% is the upper bound of the range you
compare against on slide 18. Second, it is the paper in your set that performed
sensitivity analysis to confirm robustness — which is the precedent for your
three sensitivity tests on slide 28. Point that connection out; it shows you read
the literature rather than listing it.

**Point: Fetene et al. — the five biophysical parameters**
Slope, rainfall, soil, drainage density and LULC. These are five of your six
criteria. This is the direct evidence for your criterion selection.
**Why these six criteria:** five of them recur across the reviewed studies, and
settlement proximity was added because demand determines whether a technically
good site is actually useful.

**Point: Alene et al. — runoff and slope most influential**
Interesting because your own sensitivity analysis found something different —
drainage density has the largest effect on your shortlist. Worth one sentence: it
shows influence is study-area dependent, which is exactly why you measured it
rather than assumed it.

**MUST SAY:** that these papers establish the standard criterion set and the
precedent for sensitivity analysis.
**USEFUL CONTEXT:** the 34.33% upper bound; the Alene contrast.
**ONLY IF ASKED:** individual study areas and methods.

**Estimated speaking time:** 40–50 seconds

**Transition to next slide:**
"Reading these together, seven gaps stood out — and the project is essentially
organised around answering them."

---

# SLIDE 7 — Research Gaps and How This Project Responds

### What the slide shows
A two-column table: seven gaps from the literature, each paired with this
project's response.

### Main speaking points

**This is one of the two or three most important slides in the deck.** It is where
you stop describing other people's work and start justifying your own. Spend time
here.

Do not read all seven rows. Take three in depth and gesture at the rest.

**Gap 1: AHP weights are asserted and never tested → three sensitivity analyses**
The single most common criticism of AHP is that the answer is whatever the
analyst decided. Your response is not a defence, it is a measurement.
**Why three analyses rather than one:** each asks a different question — what if
this weight were somewhat different, what if this layer did not exist at all, and
how much did this criterion actually contribute.

**Gap 2: A single method is used → four MCDA engines on one byte-identical stack**
Explain "byte-identical" in plain terms: all four algorithms score exactly the
same input rasters, so any difference between their outputs is caused by the
method and nothing else.
**Why this matters:** without it, a difference between two algorithms could just
be a reprocessing artefact, and the comparison would prove nothing.

**Gap 3: Scores are normalised against the local data range → fixed breakpoints**
The transferability claim: *"a 4° slope scores the same in Chandrapur as in any
other district."* This is the heart of your first contribution and slide 14
develops it.

**Gap 4: Field validation is limited or absent → harness built, not yet run**
Say this one plainly and without hedging. You implemented the validation
framework, verified its mathematics, and it has never run on real data because
the structure inventory does not exist. **Claiming nothing here is a strength, not
a weakness** — and volunteering it before you are asked is much better than
being caught.

**MUST SAY:** gaps 1, 2, 3 in reasonable depth; gap 4 stated honestly.
**USEFUL CONTEXT:** gaps 5 (five scenarios), 6 (open data and provenance), 7
(socio-economic dimension partly addressed, cost data still absent).
**ONLY IF ASKED:** how each gap maps to a specific module in the code.

### Likely reviewer questions

**Likely Question:** You claim your scores are transferable. Are they all?
**Short Answer:** Five of six are. Rainfall is the exception — it is scored by
percentile rank within the district, so it is district-relative by design.
**Reasoning:** The whole district gets adequate monsoon rain, so what
discriminates between sites is *relative* rainfall; fixed millimetre bands would
collapse the district into one or two bands and lose all discrimination.
**Evidence:** `criteria.score_percentile_benefit()`; the trade-off is documented
in `docs/METHODOLOGY.md` §5.
**This is a genuinely sharp question — knowing the answer will impress.**

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"Those gaps became our objectives — here is where each one stands."

---

# SLIDE 8 — Objectives and Current Status

### What the slide shows
Seven objectives with status, six marked Achieved in green and one marked Not
achieved in red, plus a non-functional requirements line.

### Main speaking points

**Point: Six of seven achieved**
Walk the list briskly. The status column carries the detail — grid dimensions,
CR value, thresholds, site count — so you do not need to repeat those numbers.

**Point: Objective 7 is red, and you should draw attention to it**
Validation against existing structures: **not achieved**. Do not skip past this
row hoping nobody reads it. Say it directly:

> "The harness is written and its mathematics is verified. It has never run,
> because a register of existing rainwater harvesting structures for Chandrapur
> does not exist. We report no accuracy figure — and we would rather report
> nothing than report a number we cannot support."

**Why leaving it red:** an honest red row is more credible than seven greens, and
it sets up slide 29 where you explain what you did instead.

**Point: Non-functional requirements**
One sentence. The four that matter: one common CRS and grid, categorical layers
never averaged, ~1.5 s full analysis, and provenance embedded in every export.

⚠ **[DOC] caveat:** the 1.5 s and 0.15 s timings come from development notes and
were never formally benchmarked. If asked how you measured them, say you timed
them during development — do not claim a benchmark.

**MUST SAY:** six achieved, one not, and why the one is not.
**USEFUL CONTEXT:** the non-functional requirements line.
**ONLY IF ASKED:** what "categorical layers never averaged" means (slide 11).

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"So how is the system actually built?"

---

# SLIDE 9 — Proposed System and Architecture

### What the slide shows
A layered architecture — interface, Stage 1, Stage 2, supporting modules,
storage — with a right-hand panel explaining why the two-stage split matters.

### Main speaking points

**Follow the data, top to bottom.** That is the order a listener can follow.

**Point: The interface layer**
A Streamlit web application with a Folium interactive map. The user picks a
scenario and an algorithm and presses one button.
**Why Streamlit:** the analysis is a pure function of files on disk with one user
at a time and no database — a Flask/React stack would add an API layer and a
build system without adding capability.

**Point: Stage 1 — weight-independent, cached, ~0.90 s**
Walk the chain: build the grid → mask to the district → reproject every layer →
fill gaps at the rim → derive drainage density and settlement distance → score
all six criteria to 0–1.
The defining property: **none of this depends on the weights.**

**Point: Stage 2 — weight-dependent, ~0.15 s**
Apply AHP weights → aggregate → coverage gate → classify → area statistics →
extract and rank 25 sites → build per-site explanations.

**Point: Why the split matters — say both reasons, in this order**

*Speed* is the obvious one: changing a scenario re-scores in about 0.15 s instead
of 1.5 s, so the map updates while you are still looking at it.

*Scientific validity* is the one that matters more, and it is the better answer
in a viva: **every algorithm, scenario and sensitivity run is scored on
byte-identical criterion rasters.** Any difference between them is therefore
caused by the method alone. Without this structure, the four-algorithm comparison
on slide 27 would be confounded.

**Why:** The expensive work depends only on the data and never on the weights, so
computing it once is both faster and a guarantee that method comparisons are
fair.

**Point: No database, no API, no network calls**
State it as a deliberate decision, not an omission. The analysis reads files and
computes; there is no persistent state worth storing and no multi-user access to
manage.

**MUST SAY:** the two stages and both reasons for splitting them.
**USEFUL CONTEXT:** the supporting-module list; the cache key.
**ONLY IF ASKED:** that the cache is keyed on data path and grid size, so
replacing a source layer invalidates it automatically.

### Likely reviewer questions

**Likely Question:** Why no database?
**Short Answer:** There is no persistent state to store — the analysis is a pure
function of seven read-only files, and adding a database would add operational
complexity without adding capability.
**Reasoning:** Single user, no authentication requirement, results exported as
files.

**Likely Question:** Would this scale to a whole state?
**Short Answer:** The pipeline would work but would need re-tuning — the grid is
capped at 450 cells on the longest side, and the drainage class breaks are
calibrated to this district's river network.
**Caveat:** [Not tested — do not claim it scales.]

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"Let me put that architecture on the ground — this is the district we applied it to."

---

# SLIDE 10 — Study Area: Chandrapur District

### What the slide shows
India → Maharashtra → Chandrapur location maps, a geographic-context panel of
eight facts, and an analysis-grid explanation.

### Main speaking points

**Point: Area and the 99.7% cross-check**
The official district area is 11,443 km²; you measured 11,412.5 km² — **99.7%**.
Do not present this as trivia. It is an **independent verification** that your
boundary mask and your area arithmetic are correct.
**Why this check matters:** the grid is in latitude/longitude, where cells are
not square on the ground, so cell area is computed per raster row; matching the
official area to 99.7% confirms that correction works. [VERIFIED]

**Point: The district is very flat — mean slope 1.47°**
This is worth flagging because it explains a result later: slope contributes
*more* than its assigned weight (1.29×) precisely because almost the whole
district scores well on it. [VERIFIED]

**Point: Rainfall — 1,493 mm/yr against a long-term normal of ≈1,245 mm**
Do not hide the discrepancy; explain it in one sentence: the recent decade is
genuinely wetter than the older baseline. Slide 22 gives the detail.

**Point: The analysis grid**
450 × 422 cells of roughly 0.31 × 0.30 km, of which 123,555 fall inside the
district. Mention the cell size in plain terms — *"about 300 metres, roughly
three football pitches across."*

**Why 450 cells:** it gives ~300 m cells, fine enough to resolve slope and
drainage variation while keeping a full analysis at interactive speed.

**MUST SAY:** the 99.7% cross-check and what it proves; the grid and cell size.
**USEFUL CONTEXT:** flatness (1.47°), rainfall vs normal, drainage density.
**ONLY IF ASKED:** why EPSG:4326 rather than a projected system (see below).

### Likely reviewer questions

**Likely Question:** Why work in latitude/longitude rather than metres?
**Short Answer:** The inputs arrive in mixed projections and must be unified
anyway; working in 4326 avoids a second resampling, and we correct explicitly for
the fact that degrees are not distances.
**Reasoning:** Three corrections — cell size evaluated at the grid's centre
latitude, cell area computed per row, and distance transforms made anisotropic.
**Evidence:** The 99.7% area match is the proof that the correction works.

⚠ **Two facts on this slide are [EXTERNAL] and appear nowhere in the repository:**
the **~27.7 °C mean temperature** and the **Census 2011** attribution for the
population figure. Both are probably fine — but know your source before you say
them, because you cannot check them from the project.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"Everything the system knows about that district comes from seven datasets."

---

# SLIDE 11 — Data Sources

### What the slide shows
A seven-row table of datasets with source, native resolution and role, plus two
explanation panels on resampling and gap filling.

### Main speaking points

**Point: Seven datasets, six criteria — and why the numbers differ**
Population does not enter the model directly. It is converted into *distance from
the nearest settlement* first. Flag this now; slide 13 explains why.

**Point: All sources are free, global and peer-reviewed**
**Why these sources:** they are open and globally available, so the method
transfers to any district and anyone can reproduce the work — which directly
answers the "results are region-specific and hard to reproduce" gap from slide 7.

**Point: Resampling is a correctness issue, not a preference**
This is a good place to show technical judgement in one sentence.

**Simple explanation:** When you change the size of map cells, you have to decide
what value the new cell gets. Averaging works for measurements but not for
categories.
**Technical explanation:** Continuous layers — slope, rainfall, population — use
bilinear interpolation. Categorical layers — soil and land cover — use nearest
neighbour, because averaging class 4 and class 6 gives class 5, a category that
may not exist and certainly does not mean "halfway between".

**Why:** Averaging category codes invents classes that are not in the data, which
would silently corrupt two of the six criteria.

**Point: Gap filling at the rim**
The layers were clipped in QGIS and stop at slightly different places. Gaps
*inside* the district are filled from the nearest valid cell — soil 2.2%,
population 2.0%, slope 1.1%, land cover 0.1%, **rainfall 0.0%** [VERIFIED].

The zero is the interesting one: rainfall needs no filling because you built that
layer in code with a margin, rather than clipping it by hand. That is a concrete
argument for scripting data preparation.

**MUST SAY:** the seven-to-six mapping; the resampling rule and why.
**USEFUL CONTEXT:** gap-fill percentages and the rainfall zero.
**ONLY IF ASKED:** native resolutions; that gap filling requires SciPy's
nearest-value distance transform.

### Likely reviewer questions

**Likely Question:** Isn't gap filling making up data?
**Short Answer:** It is nearest-neighbour interpolation over a few hundred metres
on layers that vary slowly in space, affecting at most 2.2% of the district at
the rim.
**Reasoning:** The alternative — discarding the rim — would shrink the study area
and bias it toward the interior.
**Evidence:** Per-layer percentages printed by the pipeline on every run.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"Here is what those datasets look like once they are on the common grid."

---

# SLIDE 12 — Criterion Layers

### What the slide shows
Six thumbnail maps — boundary, slope, soil texture, land use, population,
drainage — with one-line captions, plus a panel explaining that two criteria are
computed rather than downloaded.

### Main speaking points

This is a visual slide. Point at the maps; do not narrate every caption.

**Point: Walk the six quickly**
Boundary is the mask. Slope is dark almost everywhere because the district is
flat. Soil shows four classes with **Silt Loam covering 77.8% of the district**
[VERIFIED] — worth mentioning because it explains why the top sites all share the
same soil type. Land cover shows 11 of the 17 IGBP classes. Population is
concentrated around Chandrapur city. The drainage network is 776 river lines
totalling 2,766 km.

**Point: Two criteria are computed, not downloaded — this is the real content**

*Drainage density:* river lines are split into ~100 m segments, each segment's
true length is added into the cell containing its midpoint, and the grid is
convolved with a circular 2.5 km window.
**Why not just rasterise the lines:** that gives a yes/no "channel present" mask,
which cannot produce a density in kilometres per square kilometre.

*Settlement proximity:* cells above 400 people/km² form a settlement mask, then
an exact distance transform gives every cell its distance in kilometres.

**MUST SAY:** that two criteria are derived, and roughly how.
**USEFUL CONTEXT:** Silt Loam dominance; the flatness visible in the slope map.
**ONLY IF ASKED:** the 100 m densification; that segment lengths use local
degree-to-kilometre scaling so the result is in true kilometres.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"Those six layers become six criteria — with these weights."

---

# SLIDE 13 — The Six Criteria

### What the slide shows
Six cards, each with a criterion name, its AHP weight, and a one-line scoring
description. A footer gives λmax, CI, RI and the consistency ratio.

### Main speaking points

**Point: The weights, in order**
Rainfall **0.4285**, slope **0.2254**, soil **0.1535**, drainage **0.0932**, land
cover **0.0597**, settlement **0.0397** [all VERIFIED].

Give the logic rather than reading the numbers:
> "Rainfall is the water source, so it dominates. Slope governs whether the water
> can be retained at all. Soil controls infiltration. Drainage tells us where the
> runoff concentrates. Land cover and settlement proximity are feasibility and
> demand modifiers rather than primary physical drivers."

**Point: Settlement proximity peaks at 3 km — the one that surprises people**
Explain the shape: **both extremes are bad.** Inside a settlement you cannot
build — the land is impervious, expensive, and contaminated. Too far away and
there is no demand to serve. The optimum is a setback band.

**Why 1–5 km:** close enough that harvested water serves real demand, far enough
to avoid built-up land and acquisition cost.
⚠ **Be honest if pressed:** this band is expert judgement, not fitted to data.

**Point: The consistency ratio — 0.0235**
**Simple explanation:** a check that our judgements do not contradict each other.
If we say rainfall is twice as important as slope, and slope twice as important
as soil, we should not then say rainfall is only three times soil.
**Technical explanation:** CR = CI / RI, where CI = (λmax − n)/(n − 1). Accepted
below 0.10; ours is 0.0235.

**MUST SAY:** the top three weights with reasoning; the settlement band and why
it is shaped that way; CR = 0.0235 passes.
**USEFUL CONTEXT:** the scoring method for each criterion.
**ONLY IF ASKED:** exact λmax, CI, RI values (6.1460, 0.0292, 1.24).

### Likely reviewer questions

**Likely Question:** Why is rainfall weighted so heavily when it barely varies
across the district?
**Short Answer:** Because it is the source of the water — but you are right that
its *realised* influence is lower, and we measured exactly that: it contributes
0.80× its assigned weight.
**Reasoning:** Percentile-rank scoring fixes rainfall's mean near 0.6, which caps
its effective contribution.
**Evidence:** Effective-weight analysis, slide 28. **This question walks straight
into one of your best results — welcome it.**

**Likely Question:** Why not weight population directly?
**Short Answer:** Because population density alone cannot express "too close is
also bad" — we needed a criterion that peaks in the middle.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"How each criterion gets converted into a 0–1 score is where our first
contribution lies."

---

# SLIDE 14 — Criterion Scoring Methodology

### What the slide shows
Four scoring forms on the left, a "why this replaced min–max" panel on the right,
and a table of the resulting score spread per criterion.

### Main speaking points

**This is your first major contribution. Give it proper time.**

**Point: The four normalisation forms**
Match each to why the criterion needs that shape:
- **Anchored interpolated ramp** — slope, drainage density. Continuous quantities
  with physically meaningful break points.
- **Categorical lookup** — soil, land cover. Explicit score per class. All 17
  IGBP classes are tabulated even though only 11 occur here, so the table
  transfers to other districts.
- **Continuous percentile rank** — rainfall. `score = 0.20 + 0.80 × rank`.
- **Moderate-optimal curve** — settlement proximity. The only criterion where
  both extremes are bad.

**Point: Why this replaced min–max — the headline evidence**
Explain min–max simply first: *"stretch each layer so its lowest value becomes 0
and its highest becomes 1."* Then give what it did to your data:

- **97.4% of slope cells and 97.7% of population cells scored above 0.90** — one
  steep escarpment and one city stretched each range so far that both criteria
  became effectively constant [DOC].
- Categorical layers were scored **by the numeric value of their class code**, so
  water ranked best and forest worst.
- **About 48% of the decision weight was flat or semantically inverted** [DOC].

**Why fixed breakpoints:** a given slope always maps to the same score regardless
of what else is in the raster, which makes the model reproducible and
transferable.

⚠ These "before" figures are [DOC] — measured during development on code that has
since been replaced. Say *"when we measured it at the time"*, not *"you can run
it and see"*.

**Point: The resulting score spread table**
Every one of these is [VERIFIED]. The point of the table is that all six criteria
now **discriminate** — slope spans 0.066–1.000 across 6,276 distinct values where
before it was nearly constant.

The two small numbers are not a problem: soil has 4 distinct values and land
cover 10 because they are categorical. Say that before someone asks.

**MUST SAY:** the four forms; the min–max failure with at least one number; that
all six criteria now discriminate.
**USEFUL CONTEXT:** the full spread table; why 17 classes are tabulated.
**ONLY IF ASKED:** the exact anchor values.

### Likely reviewer questions

**Likely Question:** Where did your break points come from?
**Short Answer:** From the RWH engineering literature and physical reasoning —
each anchor maps to a stated reason, all documented in our methodology file.
**Caveat:** Be honest — they were not optimised against an objective function.
Say *"chosen by reasoning, not fitted"* if pressed.

**Likely Question:** Isn't a fixed table just as subjective as min–max?
**Short Answer:** It is a judgement, but a *stated and inspectable* one — and
unlike min–max it does not change when the data changes.

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"With the criteria scored, the next question is how much each one should count."

---

# SLIDE 15 — AHP Weighting

### What the slide shows
The AHP working-process diagram (pairwise matrix → geometric mean → consistency
check), the baseline weights table, and a panel on what CR does and does not
prove.

### Main speaking points

**Point: Why AHP rather than assigning weights directly**
**Simple explanation:** People are bad at saying "rainfall is 43% important" but
good at saying "rainfall matters more than slope, quite a lot more."
**Technical explanation:** AHP decomposes the problem into 15 pairwise
comparisons on a 1–9 scale, then extracts the weight vector as the normalised
geometric mean of the matrix rows.

**Why AHP:** it converts judgement into numbers through comparisons people can
actually make, and — unlike direct assignment — it can detect when those
judgements contradict each other.

**Point: Walk the diagram in three steps**
1. Build the pairwise matrix — 6 × 6, reciprocal, Saaty 1–9 scale.
2. Compute the geometric mean of each row and normalise → the weights.
3. Check consistency — λmax, then CI, then CR against the random index.

**Point: The panel on the right is the most important thing on this slide**

> "A low consistency ratio shows the judgements are internally consistent. It
> does **not** show they are correct."

Say this out loud, in your own words. **You can be perfectly consistent and
perfectly wrong.** Then deliver the payoff: *"which is exactly why we then
stress-tested the weights three separate ways."*

Volunteering this pre-empts the single most likely criticism of the entire
project and turns it into a setup for slide 28.

**MUST SAY:** why pairwise rather than direct; that CR proves consistency, not
correctness.
**USEFUL CONTEXT:** the three-step diagram walkthrough.
**ONLY IF ASKED:** the full matrix; that RI = 1.24 for n = 6 from Saaty's table.

### Likely reviewer questions

**Likely Question:** Who provided the expert judgement?
**Short Answer:** The team, informed by the criterion importance reported across
the eight reviewed studies, and reviewed with our guide.
**Caveat:** Do not claim an external expert panel. This is worth agreeing on as a
team before the presentation.

**Likely Question:** What if your CR had been above 0.10?
**Short Answer:** The application rejects the matrix and displays "inconsistent —
revise the judgements", so an inconsistent matrix cannot silently produce a map.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"Weights and scores then combine into a single suitability value per cell."

---

# SLIDE 16 — Suitability Calculation

### What the slide shows
Three steps — aggregate, coverage gate, classify — plus a panel on the two
available aggregation rules. The weighted-overlay equation is displayed.

### Main speaking points

**Point: Step 1 — the equation, in words first**
> "For every cell, multiply each criterion's score by its weight, add them up,
> and divide by the total weight."

Then the important refinement: the sum runs **only over criteria that have data
there**, and the weights are renormalised per cell.
**Why renormalise:** otherwise a cell missing one criterion would be scored on a
partial total and look artificially bad, rather than being judged fairly on what
is known about it.

**Point: Step 2 — the coverage gate, with its evidence**
A cell is scored only if at least **80%** of the total AHP weight has real data
there.

Give the concrete reason, because it is compelling: without this gate, an edge
cell holding only rainfall and land cover could score 1.00 from two criteria and
outrank a genuine site evaluated on all six. **13 of the original top 25 sites
were exactly this artefact** [DOC — `CHANGELOG.md`, `docs/METHODOLOGY.md` §8].
All 25 are now scored on all six criteria.

**Why 80%:** high enough to guarantee a site is judged on the great majority of
the evidence, low enough not to discard the district rim.

**Point: Step 3 — fixed thresholds, and why not percentiles**
High ≥ 0.85, Medium 0.65–0.85, Low < 0.65.

**Why fixed and not percentile:** a 33rd/67th percentile split always reports
about a third of any district as highly suitable whatever the scores are — so the
number would be a property of the method, not a finding about Chandrapur.

Add the consequence that makes it matter: fixed thresholds are **what allows
scenarios and algorithms to be compared at all.** With percentiles, every
scenario would report ~33% High and slide 27 would be impossible.

**Point: The two aggregation rules**
WLC is fully compensatory — strong rainfall offsets weak slope.
TOPSIS is not — distance to an ideal punishes weakness on a heavily weighted
criterion disproportionately.
Frame the comparison: *"comparing them shows how much of the answer is the
assumption rather than the terrain."*

**MUST SAY:** the equation in words; the coverage gate with the 13-of-25 evidence;
fixed vs percentile and why it enables comparison.
**USEFUL CONTEXT:** per-cell renormalisation.
**ONLY IF ASKED:** the TOPSIS formulae; that percentile mode still exists in the
code as a fallback.

### Likely reviewer questions

**Likely Question:** Why 0.65 and 0.85 specifically?
**Short Answer:** 0.85 means a cell sits in the upper class of essentially every
criterion — it fails none of them badly. But be honest: the *values* were chosen
by reasoning, not optimised. What matters methodologically is that they are fixed
rather than percentile-based.

**Likely Question:** What happens to cells that fail the coverage gate?
**Short Answer:** They are left unscored rather than guessed at. On the current
inputs, gap filling means no district cell is actually dropped — the gate is a
structural safeguard.

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"That gives us a surface. Turning a surface into an actionable shortlist takes
three more stages."

---

# SLIDE 17 — Candidate Site Selection and Explainability

### What the slide shows
Three numbered selection stages on the left; a list of what every site carries on
the right.

### Main speaking points

**Point: Stage 1 — best per tile**
The district is divided into a 5 × 5 grid and the best cell inside the
high-suitability mask is taken from each tile.
**Why:** taking the top 25 cells outright would cluster them all in one
favourable belt, which is useless for district-level planning.

**Point: Stage 2 — global maxima with 5 km separation**
**Why 5 km:** two structures 500 m apart harvest the same catchment, so they are
not genuinely distinct options.

Flag the visible consequence before a reviewer spots it on the map: *"a large
high-suitability zone may show only one or two markers — that is the separation
constraint operating, not a gap in our results."*

**Point: Stage 3 — re-rank by score, and the honest story behind it**
Ranks are assigned strictly by descending score.

This stage exists because of a real defect: ranking by selection order once
published **rank #22 with a higher score than rank #13**. Tell this story — it is
short, it is honest, and it demonstrates that you test your own output. Finish
with the fix: it is now guarded by an automated test that runs on every check.

**Point: What every site carries — your explainability contribution**
Do not read all six bullets. Emphasise two:
- **Weighted contribution per criterion** — AHP weight × normalised score. This
  shows what actually *drove* the result, not just the total.
- **Raw measured values** — slope in degrees, soil and land-cover class names,
  drainage density, distance to the nearest settlement. A planner can sanity-check
  a recommendation against reality.

**Why explainability:** a recommendation that cannot be challenged cannot be
trusted — most comparable studies report only an aggregate score.

**MUST SAY:** why tiling, why 5 km, the rank-ordering story, and the two
explainability items above.
**USEFUL CONTEXT:** the compare panel; the 0.66 satisfied threshold.
**ONLY IF ASKED:** how ties are broken deterministically.

### Likely reviewer questions

**Likely Question:** Why 25 sites?
**Short Answer:** It is a shortlist a planner can realistically work through;
beyond that you get a long tail of marginal sites.

**Likely Question:** How do you know the ranking is right now?
**Short Answer:** The smoke test asserts on every run that ranks are 1 to 25 and
scores are strictly descending. It passed this morning. [VERIFIED]

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"So — what did the system actually produce?"

---

# SLIDE 18 — Result: Suitability Zones

### What the slide shows
The zone table (High/Medium/Low with thresholds, share, area), a proportion bar,
a comparison panel, and a suitability-surface statistics panel.

### Main speaking points

**Point: The headline result**
**High 18.51% — 2,112.6 km². Medium 54.79% — 6,252.6 km². Low 26.70% —
3,047.3 km².** [All VERIFIED]

Say what it means practically: *"roughly two thousand square kilometres of
Chandrapur are highly suitable for rainwater harvesting under our baseline
weighting."*

**Point: What was evaluated and what the number means**
Be precise about the claim. This is a **model output**, not a validated
prediction. The correct framing:

> "This is what our criteria and weights identify as highly suitable. It has not
> been checked against structures that already exist — we will come to that."

**Point: The comparison panel — and one correction**
The slide says 18.51% *"sits at the lower end of the 19–34% suitable-area range"*
reported in the reviewed studies.

⚠ **18.51% is actually just *below* that range.** The underlying values are from
your own slides 5 and 6: Seif 18.85% and Resen 34.33%. So the honest phrasing is
**"just below the 18.9–34.3% range"**. It is still a good comparison, and it is
exact — say it that way.

The important sentence on this slide is the next one: **the thresholds were not
retuned to reach it.** 18.51% is the honest consequence of continuous scoring
against fixed break points, not a number you tuned toward.

**Point: The surface statistics — the one to highlight**
**108,229 distinct values, exactly one cell at the maximum.** That is the proof
that your scoring produces a genuine ranking rather than a plateau of ties —
slide 24 tells the story of why that mattered.

**MUST SAY:** the three zone figures; that this is a model output not a validated
prediction; that thresholds were not retuned.
**USEFUL CONTEXT:** the surface statistics; the literature comparison (corrected).
**ONLY IF ASKED:** score min/max/mean/median; runtime.

### Likely reviewer questions

**Likely Question:** Is 18.51% good?
**Short Answer:** It is consistent with comparable published studies, but "good"
would require validation against real structures, which we have not done.
**Do not overclaim here.** This is the discipline that makes the rest of your
honesty credible.

**Likely Question:** What would change this percentage?
**Short Answer:** The scenario — it ranges from 18.51% to 30.14% across our five
weightings — and the aggregation rule, which moves it by about 5 points.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"And the shortlist that comes out of that surface."

---

# SLIDE 19 — Result: Top-Ranked Candidate Sites

### What the slide shows
A table of the top five sites with coordinates, score, and the four raw measured
values, plus two honesty panels.

### Main speaking points

**Point: Read one row properly, not all five**
Take rank 1 and narrate it as a planner would read it:

> "Our highest-ranked site scores 0.984. The slope there is 0.22 degrees —
> essentially flat. The soil is Silt Loam, the best infiltration-retention
> balance. It is cropland, so there is demand and land acquisition is realistic.
> Drainage density is 0.72, well above the district average of 0.24. And it is
> 5.9 km from the nearest settlement."

That single sentence demonstrates the explainability contribution better than any
description of it. **[All values VERIFIED.]**

**Point: 25 sites, 0.984 down to 0.866, strictly descending**

**Point: The honesty panel — say this yourself, don't wait**
All five leading sites are Silt Loam cropland on near-flat ground. Address it
head-on:

> "That is the model behaving consistently with its scoring tables — Silt Loam and
> cropland both score 1.00, so cells with both start ahead. But it does
> concentrate the shortlist in one landscape type, and that is a fair criticism of
> fully compensatory aggregation."

**Why this is worth volunteering:** it will be noticed, and pre-empting it shows
you understand your own model's behaviour rather than just reporting its output.
It also sets up TOPSIS on slide 26 as the partial counterweight.

**MUST SAY:** one site narrated in full; the landscape-concentration caveat.
**USEFUL CONTEXT:** the 25-site range; why 5 km separation.
**ONLY IF ASKED:** that Silt Loam covers 77.8% of the district [VERIFIED], which
explains the pattern.

### Likely reviewer questions

**Likely Question:** Have you visited any of these sites?
**Short Answer:** No — no field verification has been done, and we list that as a
limitation.

**Likely Question:** Isn't it suspicious that they are all the same soil type?
**Short Answer:** It follows from Silt Loam covering 78% of the district and
scoring highest. The consensus analysis is our practical mitigation — it shows
which sites survive across both aggregation philosophies.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"Those results are quite different from what we had at the last review — here is
how we got here."

---

# SLIDE 20 — Progress Since the Last Review

### What the slide shows
Six dated milestone cards from April 2026 to 23 August.

### Main speaking points

This is a pace slide. Move briskly; the detail is on slides 21–25.

**Point: The arc, in one sentence**
> "We went from a working AHP overlay that had three methodological defects to a
> stress-tested decision-support system — and most of that work was finding and
> fixing our own mistakes."

**Point: Name the six milestones fast**
April — initial prototype. 29 July — correctness sprint. 4 August — real rainfall
data and hydrology. 8 August — the scoring fix plus decision-support features.
12 August — four algorithms and the validation harness. 23 August — review
feedback: consensus, extra sensitivity tests, the automated test.

**Point: Note the scope removal explicitly**
The 29 July card says the natural-language layer was removed from scope. Say it
out loud: *"We removed the natural-language query component to concentrate on
methodological correctness."* If you kept slide 4, this is where the two slides
must agree — say the same thing both times.

**MUST SAY:** the arc; the scope removal.
**USEFUL CONTEXT:** the individual milestone contents.
**ONLY IF ASKED:** that there is no Git history — the project used a
hand-maintained changelog, which is where these dates come from.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"The most useful way to show that progress is to show what was wrong before."

---

# SLIDE 21 — What Was Corrected, and Why It Mattered

### What the slide shows
An eight-row before/after table, with an impact line underneath.

### Main speaking points

**Do not read eight rows.** Pick three and summarise the rest as "the same
pattern".

**The three strongest rows:**

1. **Normalisation** — min–max left 97.4% of slope cells above 0.90. Two criteria
   carrying a quarter of the weight had almost no effect.
2. **Categorical layers scored by class code** — water ranked best, forest worst.
   This is the most vivid one; it is immediately obvious to any audience that
   ranking open water as the best place to build is wrong.
3. **Site ranking** — #22 outscored #13.

Then: *"The other five rows follow the same pattern — each was a defect we found
by checking our own output against what it should logically produce."*

**Point: The impact line — deliver this properly**
**Sites scored on all six criteria rose from 12 of 25 to 25 of 25**, and the
analysed area now matches the official district area to 99.7% [DOC for the first;
VERIFIED for the second].

**Point: Frame this as rigour, not as apology**
The natural instinct is to be defensive about a list of your own bugs. Resist it:

> "We think this slide is the strongest evidence that the current results can be
> trusted. Each of these was found by testing our own output, and the two that
> could recur are now guarded by automated checks."

**MUST SAY:** three rows; the impact line; the framing sentence.
**USEFUL CONTEXT:** the remaining rows as a group.
**ONLY IF ASKED:** how each was found; that "before" figures are from development
records and are not re-measurable now.

### Likely reviewer questions

**Likely Question:** How do you know there aren't more bugs?
**Short Answer:** We don't — but we now have an automated end-to-end test with
eleven checks, and several internal cross-checks like the 99.7% area match and a
0.08% river-length conservation check.
**This is the right answer. Do not claim the code is bug-free.**

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"Two of those corrections are worth showing in detail. The first is our rainfall
input."

---

# SLIDE 22 — Real Rainfall Data: CHIRPS v3.0, 2014–2024

### What the slide shows
Four statistic tiles, a "built in code" panel, a data-trap panel, and the
wet-decade explanation.

### Main speaking points

**Point: Why this layer mattered most**
Rainfall carries the largest weight — 0.4285 — so the provenance of that layer
had to be reproducible. It moved from a single-month placeholder with unresolved
units to an 11-year mean built in code.

**Point: Built in code, not by hand**
Only the district window plus a 0.20° margin is read from each of eleven global
rasters, so 7200 × 2400 files are never loaded whole.

**Why the margin:** it is the reason rainfall needs **0% gap filling** while every
manually-clipped layer needs some [VERIFIED]. That is a concrete argument for
scripting data preparation rather than clicking through it.

Provenance — source, years, aggregation method, units, district mean, generation
date — is written into the output file's own metadata tags.

**Point: The data trap — a good story, tell it**
CHIRPS ships **−9999** as its fill value but **does not declare it in the GeoTIFF
header**, so a standard reader treats it as a real measurement of minus 9,999
millimetres of rain. On one global file that produces a raw mean of **−6,947 mm
against a true 889.6 mm** [DOC — `CHANGELOG.md`]. Treating anything below −100 as
NoData is what prevents it.

**Why this is worth 15 seconds:** it shows you validated your input data rather
than trusting it, which is exactly the kind of thing reviewers look for.

**Point: The wet-decade finding**
Your 11-year mean is ~20% above the ≈1,245 mm long-term normal quoted on your own
study-area slide. State that it is not a unit error — 2014, 2015 and 2017 sit near
the normal while the remaining years run substantially higher.

**Why say it at all:** because slide 10 shows both figures and someone will notice
the disagreement. Explaining it first is much stronger than being asked.

⚠ **Two accuracy notes:**
- The in-district range tile says **1,184–1,713 mm/yr**. Measured on the analysis
  grid it is **1,189–1,714**; the whole raster including the margin is
  1,140–1,823. The tile figure reproduces neither exactly. It is a small
  discrepancy, but if you quote a range, quote **1,189–1,714 in-district**.
- The per-year figures behind the wet-decade claim are [DOC] from the original
  build run and were not re-derived. Speak about the pattern, not exact years,
  unless you re-run `build_rainfall.py` first.

**MUST SAY:** why this layer mattered; built in code with provenance; the
wet-decade explanation.
**USEFUL CONTEXT:** the NoData trap.
**ONLY IF ASKED:** the ±20% sanity check that fails the build loudly.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"The second correction changed what we were measuring altogether."

---

# SLIDE 23 — Drainage Density and Derived Hydrology

### What the slide shows
A "from distance to density" panel, a window-size justification, the derived
surfaces table, and two deliberate decisions.

### Main speaking points

**Point: The conceptual correction — lead with this**
The original implementation measured **distance to the nearest river**. That is a
*siting-convenience* measure — how far you have to carry water. **Drainage
density** — channel length per unit area — is a *hydrological* measure: it tells
you where runoff concentrates, which is what determines whether there is water to
harvest at all.

**Why the change:** distance to a river answers the wrong question, and density is
the variable the RWH literature actually uses.

**Point: How it is computed**
Three steps, briefly: split river lines into ~100 m segments → accumulate each
segment's true length into its cell → convolve with a circular 2.5 km window and
divide by the true window area.

**Point: The conservation check**
**2,765.6 km binned against 2,767.7 km of input geometry — 0.08% loss** [DOC].
This is a verification that the length accumulation is correct, and it is the kind
of internal check worth mentioning once.

**Point: Why 2.5 km**
A 1 km window spans roughly three cells and produces a speckled surface; a much
larger one converges towards the district mean and stops discriminating.
**Why:** 2.5 km is smooth enough to be usable and small enough to still vary
meaningfully across the district.
⚠ Honest caveat if pressed: no formal window-size sweep was performed.

**Point: The two deliberate decisions — both are good viva material**

*Runoff is not an AHP criterion.* Curve Number is a function of land cover and
soil, and runoff additionally of rainfall — all three are already weighted
criteria, so including runoff would silently double-weight them.
**Why:** avoiding double-counting is a correctness issue in weighted overlay.

*Runoff is reported per 100 mm design storm, never as an annual volume.* SCS-CN is
an event model; feeding it the annual total collapses every land-cover class into
the 0.85–0.96 range and the map carries no information. [VERIFIED: forest 0.850,
built-up 0.965 at 1,493 mm — versus 0.128 and 0.610 at 100 mm.]

**MUST SAY:** the distance-to-density correction and why; both deliberate
decisions.
**USEFUL CONTEXT:** the computation steps; the 2.5 km justification.
**ONLY IF ASKED:** the surfaces table; the conservation check; that class breaks
are calibrated to HydroRIVERS and would need recalibration for a DEM-derived
network.

### Likely reviewer questions

**Likely Question:** Your drainage density of 0.242 km/km² seems low.
**Short Answer:** It is, and we say so — HydroRIVERS is thresholded to larger
channels, so it sits an order of magnitude below DEM-derived networks. Our class
breaks are calibrated to this source, and a different network would need
recalibration.
**This is a well-informed question and having the answer ready will land well.**

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"The third correction came from the application itself telling us something was
wrong."

---

# SLIDE 24 — Continuous Scoring and Meaningful Rankings

### What the slide shows
Cause and fix panels on the left, a five-row before/after table on the right, and
a note that thresholds were not retuned.

### Main speaking points

**Point: The symptom — start here, it is a story**
> "Running the application, we noticed every top-ranked site was showing a score
> of 1.000, and the comparison panel showed 100% on every row. You could not tell
> any two sites apart."

**Point: The cause**
Every criterion had a **flat top**. Slope scored 1.00 below 1°, drainage 1.00
above 0.40, rainfall 1.00 for the wettest quintile, settlement 1.00 across a
4 km band, soil and land cover 1.00 for their best class. Any cell landing in the
best band of all six scored exactly 1.000 — and **973 cells did** [DOC].

**Point: The fix — and why it did not cost reproducibility**
Flat tops were replaced with linear interpolation **between the same anchors**.
Emphasise: *"the anchor values did not move — only the behaviour between them."*
So a given slope still maps to a fixed score independent of the data range, and
the transferability claim survives.

**Point: The before/after table**
Two rows carry the argument:
- **Cells sharing the maximum: 973 → 1** [after VERIFIED]
- **Distinct suitability scores: 47,495 → 108,229** [after VERIFIED]

And the one that shows it fixed the actual user-facing problem: **distinct scores
among the top 25 sites: 8 → 22** [VERIFIED].

**Point: The thresholds were not retuned — say this explicitly**
The High share fell from 25.6% to 18.51%. Explain why: ramps score lower than a
step class that awards 1.00 across a whole band. **18.51% is the honest
consequence of continuous scoring, not a tuned number.**

**Why this matters:** it pre-empts a reasonable suspicion that you adjusted
thresholds to land on a favourable figure.

**MUST SAY:** the symptom, the cause, and the 973 → 1 result.
**USEFUL CONTEXT:** the full table; that anchors did not move.
**ONLY IF ASKED:** the pre-fix High share of 25.6% / 2,922 km².

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"With the analysis correct, we built the layer that makes it usable as a planning
tool."

---

# SLIDE 25 — Decision-Support Layer

### What the slide shows
The five-scenario table with CR and High %, a proxies caveat, and three feature
panels — editable matrix, five export formats, reproducibility documentation.

### Main speaking points

**Point: Why scenarios exist at all**
> "There is no single 'best site' — it depends on what you are optimising for. A
> recharge-maximising planner and a community-water planner want different
> places. Making that explicit is more honest than pretending one weighting is
> universal."

**Why scenarios rather than a single weighting:** the answer genuinely depends on
the planning objective, and hiding that behind one weight vector would be
misleading.

**Point: The table — and the one demonstration worth making**
All five scenarios pass their consistency check, with CR from 0.0044 to 0.0146.
High % ranges from 18.51% to 30.14%. [All VERIFIED]

Then the concrete proof that scenarios do real work: **community-focused weighting
selects a different top-ranked site** — baseline picks the site at 79.3658,
20.4295; community-focused picks 79.7673, 19.6664 [VERIFIED]. Fertile farmland
picks a third one. Scenarios change the answer materially, not cosmetically.

**Point: The proxies caveat — say it, don't let them find it**
"Low-earthwork siting" is **not** a cost model — the project holds no land-value
or unit-rate data, so weighting slope and land cover is a proxy for construction
difficulty. "Fertile farmland" is **not** a fertility model — there is no
soil-chemistry data.

**Why declare this:** an examiner who thinks you built a cost model and then
discovers you did not will distrust everything else. Declaring it costs ten
seconds and buys credibility.

**Point: Editable pairwise matrix**
Users edit the upper triangle; the lower triangle is rebuilt as its reciprocal so
the matrix is always valid, and the CR updates live with an accept/reject verdict.
**Why:** the weights are expert judgement, so a different expert should be able to
supply their own and immediately see whether it is consistent.

**Point: Five export formats with provenance**
Each carries the weights, CR, thresholds and date that produced it.
**Why:** a site table without its weights is not reproducible.

**MUST SAY:** why scenarios exist; that they change the top-ranked site; the
proxies caveat.
**USEFUL CONTEXT:** the editable matrix; provenance in exports.
**ONLY IF ASKED:** individual scenario weight vectors; that scenario matrices are
generated from an importance ranking snapped to the Saaty scale, so they are
consistent by construction.

### Likely reviewer questions

**Likely Question:** How did you decide the scenario weightings?
**Short Answer:** Each is an importance ranking over the same six criteria,
reflecting a stated planning objective, converted to a Saaty matrix and checked
for consistency.
**Caveat:** These are expert judgement like the baseline — no data distinguishes
them. That is exactly why two are labelled proxies.

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"The bigger question was how much of our answer came from the method itself."

---

# SLIDE 26 — Four MCDA Algorithms on One Criteria Stack

### What the slide shows
Two choice panels (weighting, aggregation), a 2 × 2 matrix of the four
algorithms, and two implementation decisions.

### Main speaking points

**Point: The 2 × 2 design — explain the logic, not the cells**
Two independent choices multiply into four algorithms: *how weights are derived*
(AHP or Fuzzy-AHP) and *how scores are combined* (WLC or TOPSIS).

**Why this design:** it isolates the two choices, so you can see which one
actually drives the result — which is what slide 27 reports.

**Point: Fuzzy-AHP in one sentence**
**Simple explanation:** instead of saying "rainfall is exactly 3 times as
important as slope", you say "somewhere between 2 and 4" — acknowledging that
expert judgement is imprecise.
**Technical explanation:** each judgement becomes a triangular fuzzy number,
weights follow Buckley's geometric-mean method, and are defuzzified by centroid.

**Point: WLC versus TOPSIS**
WLC is fully compensatory. TOPSIS measures distance to a theoretical ideal, and
because distance is not a linear sum, weakness on a heavily weighted criterion is
punished disproportionately and cannot be fully bought back.
**Why include both:** they encode genuinely different planning philosophies, and
comparing them shows whether the ranking depends on that assumption.

**Point: The line under the matrix — do not skip it**
*"Same six criteria, same data, same grid — so any difference is attributable to
the method alone."* This is what the architecture on slide 9 was built to
guarantee. Connect the two explicitly.

**Point: The two implementation decisions — both are strong viva material**

*Theoretical ideals in TOPSIS.* Using the observed best and worst cell would make
every score depend on the data range — the same defect you removed from
normalisation — and would break comparability across scenarios.

*The Fuzzy-AHP cancellation bug.* Your first implementation used a uniform
multiplicative spread and returned weights **identical to crisp AHP to three
decimal places**, because such a spread cancels during normalisation. The additive
Saaty scale is required for fuzziness to have any effect at all.

**Why tell them about the bug:** had you not caught it, your algorithm comparison
would have contained a false claim. It is a real trap that few papers mention, and
it demonstrates that you understood the mathematics rather than calling a library.

**MUST SAY:** the 2 × 2 logic; WLC vs TOPSIS in plain terms; the byte-identical
stack.
**USEFUL CONTEXT:** the Fuzzy-AHP explanation; theoretical ideals.
**ONLY IF ASKED:** the cancellation bug detail; why Buckley rather than Chang's
extent analysis (Chang can assign zero weight to a genuinely relevant criterion;
Buckley cannot).

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"Running all four produced our most interesting finding."

---

# SLIDE 27 — Algorithm Comparison Results

### What the slide shows
A four-row comparison table (High %, mean score, top-10 shared, Pearson,
Spearman, class agreement) and two findings panels.

### Main speaking points

**This is your headline result. Give it the most emphasis of any slide.**

**Point: What was evaluated and why**
All four algorithms scored the identical criteria stack, so any difference is
caused by the method. You compared them four ways: how much area each classes
High, how many of the baseline's top 10 sites each also selects, how correlated
the surfaces are, and how often they agree on the class of a given cell.

**Point: Finding 1 — the headline**
> "Changing the aggregation rule moves the highly suitable area by about five
> percentage points and drops class agreement to roughly 75%. Changing the
> weighting method moves it by 0.2 points at almost 99% agreement. **How you
> combine the criteria matters far more than how you weight them.**"

[VERIFIED: WLC 18.51% → TOPSIS 13.62%; AHP → Fuzzy-AHP 18.51% → 18.32%.]

Then the implication, which is what makes it a contribution: *"studies that
compare only weighting methods may be comparing the less consequential of the two
choices."*

**Point: Finding 2 — a methodological warning**
Fuzzy-AHP + WLC correlates **1.000** with the baseline surface, yet shares only
**7 of the baseline's top 10 sites**.

Explain why: many candidate sites score very close together, so a small weight
change reshuffles their order without visibly changing the map. **Surface
correlation and shortlist agreement measure different things.** If your question
is about ranking stability, report top-N overlap — not correlation.

**Point: Spearman versus Pearson — one sentence if asked**
**Simple explanation:** Pearson asks whether two scores move together; Spearman
asks whether they *rank* locations the same way.
**Why report both:** ranking is the question a site-selection method actually
answers, so Spearman is the more relevant one — and they agree closely here,
which is itself worth stating.

**Point: What you can and cannot conclude — be disciplined**
> "These methods differ measurably. But differing is not being better — we cannot
> say which is more accurate without ground truth."

Do not let a good result tempt you into an overclaim. Slide 29 handles it.

**MUST SAY:** Finding 1 with numbers; Finding 2; that differing ≠ better.
**USEFUL CONTEXT:** Spearman vs Pearson.
**ONLY IF ASKED:** the Fuzzy-AHP weights (rainfall 0.417 vs 0.4285 — close but
genuinely different).

### Likely reviewer questions

**Likely Question:** So which algorithm is best?
**Short Answer:** We cannot say — that requires an external standard, and the
only one available is agreement with structures that already exist. What we can
say is that fifteen sites were selected by all four.
**This is the most likely question of the entire presentation. Have this answer
ready verbatim.**

**Likely Question:** Why is TOPSIS's High class smaller?
**Short Answer:** Its closeness formula compresses mediocre cells toward 0.5, so
fewer cells clear the 0.85 threshold.

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"The same question applies to our weights — so we tested those three ways."

---

# SLIDE 28 — Sensitivity Analysis: Three Independent Tests

### What the slide shows
Three test panels across the top, the six-row map-removal table, and an agreement
panel.

### Main speaking points

**Point: Frame it as the answer to the standing criticism**
> "The standard criticism of AHP is that the weights are subjective, so the
> answer is whatever the analyst decided. Our response is not a defence — it is a
> measurement."

**Point: Test 1 — one-way perturbation**
Each weight scaled by ±20%, the rest renormalised. Result: **90% of the top-10
sites retained on average, 70% worst case, maximum rank shift 3.** [VERIFIED]
Meaning: the shortlist is not an artefact of the exact weights.

**Point: Test 2 — map removal**
Each criterion deleted entirely and the surface re-scored, after Lodwick, Monson
and Svoboda (1990).
**Why this test:** it answers two questions at once — does this layer earn its
place, and what happens in a district where it is unavailable?

**Point: Test 3 — effective weights**
Assigned weight versus the share of the final score a criterion actually
contributed, after Napolitano and Fabbri (1996).
Rainfall 0.80×, slope 1.29×, soil 1.26×, land cover 1.21×, settlement 0.90×,
drainage 0.71×. [VERIFIED]

**Point: The convergent finding — this is the payoff, deliver it clearly**

> "Drainage density carries only 9.3% of the weight. But remove it, and **only 2
> of the top 10 sites survive** — worse than removing slope, which carries more
> than twice the weight. It barely moves the map, yet it almost entirely reorders
> the shortlist, because it has the highest spatial variance of the six criteria
> and is what separates otherwise near-identical candidates."

Then the general lesson: **assigned weight and realised influence are different
quantities.** Two independent tests found this, which is what makes it credible.

**Point: The second finding — a criterion can be restrictive**
Removing rainfall *inflates* the High class to 42.46%. Rainfall is scored by
percentile rank, so it averages around 0.6 and acts as a **brake** on the
composite. Remove it and everything else pushes scores up. A criterion can be
*restrictive* rather than merely *important* — and the weight alone does not tell
you that.

**MUST SAY:** the framing; the ±20% headline; the drainage finding.
**USEFUL CONTEXT:** the rainfall-as-brake finding; the effective-weight ratios.
**ONLY IF ASKED:** the S-index formula, and that you adapted it — your
aggregation already divides by the weight sum, so the original's extra
normalisation terms would normalise twice. **If you mention the index at all,
mention the adaptation.**

### Likely reviewer questions

**Likely Question:** Why ±20%?
**Short Answer:** It represents a meaningful but plausible disagreement between
experts. The application also offers ±10% and ±30% so the effect of the choice is
visible.

**Likely Question:** Doesn't drainage's low weight mean you got the weights wrong?
**Short Answer:** Not necessarily — weight expresses judged importance, while
influence depends on how the criterion varies across the study area. Our
effective-weight analysis quantifies exactly that gap.

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"That covers robustness. Accuracy is a different question, and this is where we
are most careful."

---

# SLIDE 29 — Validation Status and Cross-Method Consensus

### What the slide shows
Two left panels — the framework is built, but it has never run — and a right panel
with four consensus statistics and two honesty statements.

### Main speaking points

**This slide is where your credibility is won or lost. Deliver it confidently,
not apologetically.**

**Point: The framework is built and its mathematics verified**
ROC-AUC computed via the Mann-Whitney U statistic with proper tie handling — no
external ML library needed. Presence-only sampling with a 1 km exclusion buffer,
five background points per positive, fixed random seed.

The mathematics was checked against five known cases: perfect separation 1.0,
perfect inversion 0.0, all tied 0.5, interleaved 0.25, and two normal
distributions giving ≈0.76 against a theoretical 0.760. **[VERIFIED — I re-ran all
five: 1.0000, 0.0000, 0.5000, 0.2500, 0.7614.]**

⚠ The slide says 0.765 for the last case. That value is random-seed dependent —
say **"about 0.76"** rather than a precise figure.

**Point: Explain what AUC means before saying you don't have one**
**Simple explanation:** the probability that a real existing structure scores
higher on our map than a random location. 1.0 is perfect, 0.5 is no better than
chance.

**Point: But it has never run — and why**
> "A register of existing rainwater harvesting structures for Chandrapur does not
> exist. Every entry point in the module returns 'missing data', and it will not
> invent a number. We therefore report no AUC, no accuracy figure, and no claim
> that one algorithm outperforms another."

Say it once, clearly, without hedging or repeating. Then move to what you did
instead — do not dwell.

**Point: Consensus — what you built instead**
> "A site chosen by one configuration might be an artefact of that configuration.
> A site chosen by all of them is not."

The four numbers [all VERIFIED]:
- **15 of 36** locations selected by all four algorithms
- **1,417 km²** classed High by all four — 12.41% of the district
- **7 of 54** locations selected under all five scenarios
- **1,217 km²** High under every scenario

**The defensible headline, worth delivering as one sentence:**
> "Fifteen sites were selected independently by four different MCDA methods, and
> 1,417 square kilometres was classed highly suitable by every one of them — a
> claim that requires no ground truth at all."

**Point: The concession — say it before they do**
> "Consensus is agreement, not correctness. Four methods can agree and still be
> wrong together, because they share the same criteria and the same scoring
> tables."

**Why volunteer this:** it is the obvious counter, and conceding it yourself is
far stronger than being corrected.

**MUST SAY:** framework built, never run, no number claimed; the consensus
headline; the agreement-is-not-correctness concession.
**USEFUL CONTEXT:** what AUC means; the five verification cases.
**ONLY IF ASKED:** where structure data would come from (MGNREGS asset records,
Jalyukt Shivar records, the district water conservation office, or digitising
from satellite imagery — target 150–300 points).

### Likely reviewer questions

**Likely Question:** Why didn't you just get the data?
**Short Answer:** There is no public register, and the alternative — manually
digitising 150–300 structures from satellite imagery — was more time than
remained. It is our first priority for future work and the code is already
written.

**Likely Question:** Couldn't you use OpenStreetMap water features as a proxy?
**Short Answer:** We tested that path and it is not valid — OSM artificial water
mixes farm ponds, quarry pits and mine water, so it is not an RWH structure
inventory. We treated it as a code-path exercise only.
⚠ **Do not quote the 0.482 figure from that exercise.** It is a diagnostic, not a
result, and quoting it invites exactly the overclaim you have avoided everywhere
else.

**Estimated speaking time:** 75–90 seconds

**Transition to next slide:**
"All of this runs inside a single application — and here is how we know it works."

---

# SLIDE 30 — The Application and How It Was Verified

### What the slide shows
Four UI panels on the left, the smoke-test panel and performance figures on the
right.

### Main speaking points

**If you are giving a live demo, this is the slide to do it on.** Notes below
assume you describe rather than demo; compress heavily if demoing.

**Point: Walk the interface in the order a user experiences it**
Sidebar — data status ticks, scenario picker with a rationale line, editable
pairwise matrix, algorithm selector, live weights and CR. Then the map with
toggleable layers and numbered sites. Then site cards. Then the analysis panels.

**Point: A design principle worth one sentence**
Every control carries its explanation beside it — each scenario shows its
rationale, each algorithm shows what it does differently.
**Why:** the tool is for planners, not GIS specialists; a control nobody
understands will not be used.

**Point: The automated smoke test — the strongest verification evidence you have**
Eleven checks drive the real application headlessly. **All passing** [VERIFIED —
re-run this morning]. They cover: script loads, analysis runs, scenario switch,
each algorithm, return to baseline, **rank ordering strictly descending**, export
buttons, sensitivity, consensus, algorithm comparison.

**Point: Why the test exists — a genuinely good engineering story**
> "Launching a Streamlit app successfully proves nothing — the script body does
> not execute until a browser connects. A bug once shipped for exactly that
> reason, so we built a test that actually drives the application."

**Why:** it demonstrates that you understood *why* your earlier verification was
inadequate, which is a more mature answer than "we tested it".

**Point: Performance**
Stack built once ~0.90 s, re-score ~0.15 s, full analysis ~1.5 s, four-algorithm
comparison ~2.8 s. Connect back: the cached split is what makes switching a
scenario feel instant, and what makes the method comparison valid.

⚠ [DOC] These timings were not formally benchmarked. If asked, say you timed them
during development.

**MUST SAY:** the interface walkthrough; eleven checks passing; why the test
exists.
**USEFUL CONTEXT:** performance figures; the design principle.
**ONLY IF ASKED:** that there is no pytest framework — the test is a standalone
script.

**Estimated speaking time:** 60–75 seconds (or 2–3 minutes with a live demo)

**Transition to next slide:**
"Which brings us to what we have not established."

---

# SLIDE 31 — Limitations and Future Work

### What the slide shows
Six limitations on the left, six prioritised future-work items on the right.

### Main speaking points

**Point: Frame it before listing**
> "A limitations section that names real constraints is stronger than one listing
> generic caveats — so these are specific, and several are quantified."

**Point: The three limitations worth stating aloud**

1. **No accuracy validation.** Every figure describes the model's internal
   behaviour. This is the single largest limitation. (Already covered on slide 29
   — one sentence here, do not repeat the whole thing.)

2. **Input resolution is uneven.** The grid is ~300 m but land cover is ~463 m,
   population ~900 m and rainfall ~5.3 km. **"Finer output does not mean finer
   information."** That sentence is worth saying exactly as written.

3. **Distance and density criteria see only in-district features.** Quantified:
   25.8% of cells could have a nearer out-of-district settlement, and **8 of the
   25 sites — including rank 1 — sit in that zone**. But bounded: those two
   criteria carry combined weight 0.133, so the map barely moves; the effect is on
   near-border ranking.

**Why quantifying a limitation is stronger than admitting one:** it shows you
measured the consequence rather than gesturing at it.

Then: *"the remaining three — the drainage network source, the weights remaining
expert judgement, and the absent cost dimension — are on the slide."*

**Point: Future work — lead with priority 1 and say why it is first**
> "Assembling 150 to 300 known structure locations is the highest-value single
> step. One dataset unblocks the accuracy figure, the per-algorithm ranking, and a
> learned model simultaneously — and the code is already written."

**Point: Priority 2 is worth a sentence because it is nearly free**
Re-export rivers and population clipped to a 20 km buffered boundary. **No code
change required** — it fixes a real limitation with a QGIS operation.

**MUST SAY:** limitations 1, 2, 3 (with the quantification); future priorities 1
and 2.
**USEFUL CONTEXT:** the remaining limitations; priorities 3–6.
**ONLY IF ASKED:** that the soil class coding is still to be confirmed against
SoilGrids documentation — **know this one, it is a real open item.**

### Likely reviewer questions

**Likely Question:** Your soil coding is unverified? Isn't that serious?
**Short Answer:** It is a real open item — soil carries 15.4% of the weight. Our
source file carries an explicit warning that standard SoilGrids coding numbers
classes differently. If it needs remapping, only one lookup table changes and
nothing else in the pipeline is affected.
**Do not be defensive. You flagged it yourself, in the code.**

**Estimated speaking time:** 60–75 seconds

**Transition to next slide:**
"To close."

---

# SLIDE 32 — Conclusion and Next Steps

### What the slide shows
A framing statement, a one-line summary of headline figures, and three columns:
what is established, what is not, immediate next steps.

### Main speaking points

**Point: The framing sentence — this is your closing line, deliver it well**
> "Most comparable work produces a map. This produces a map, a ranked shortlist,
> an explanation for every site, and a measurement of how far the whole result can
> be trusted."

**Point: The headline figures, said once**
Six criteria over 123,555 cells · CR 0.0235 · High suitability 18.51%, about
2,113 km² · 25 ranked sites from 0.984 to 0.866 · four MCDA engines, five
scenarios and four robustness analyses on one identical criteria stack.

**Point: What is established — pick two**
The strongest are: *the aggregation rule reshapes the result far more than the
weighting rule does*, and *fifteen sites and 1,417 km² are agreed on by all four
methods*.

**Point: What is not — say it, briefly, without apologising**
No accuracy figure, no AUC, no field verification, no cost analysis, no
machine-learning result. **Being different is not being better.**

**Point: Immediate next steps**
Digitise structures and validate · re-export with a buffered boundary · confirm
the soil coding, then finalise the paper.

**Point: The close**
End on the honesty as a strength, not a deficit:
> "We are confident about what we have established, and we are precise about what
> we have not. We think that combination is what makes the result usable."

**MUST SAY:** the framing sentence; two established findings; the "what is not"
column; the close.
**USEFUL CONTEXT:** the full headline figure list.
**ONLY IF ASKED:** anything — this is the handoff to Q&A.

**Estimated speaking time:** 45–60 seconds

**Transition to next slide:**
"Our references — and we're happy to take questions."

---

# SLIDE 33 — References

### What the slide shows
Ten numbered IEEE-format references plus a data-sources line.

### Main speaking points

Do not read references aloud. One sentence:

> "Eight GIS-MCDA rainwater-harvesting studies, plus the two sensitivity-analysis
> methods we implemented — Lodwick for map removal and Napolitano and Fabbri for
> effective weights. Our data sources are listed underneath."

**Worth knowing:** references [9] and [10] are the two sensitivity methods you
implemented, not background reading. If a reviewer asks whether your sensitivity
analysis is standard practice, these are your citations.

⚠ **The citation-numbering problem lands here.** If slides 5–6 still use [5]–[12],
this slide numbers those same papers [1]–[8], and the four LLM papers cited on
slide 4 appear nowhere. See *Overall Review §5*.

**Estimated speaking time:** 10–15 seconds

---

---

# OVERALL PRESENTATION REVIEW

## 1. Key Technical Decisions to Understand Before Presenting

Everyone presenting should be able to explain these without notes. They are the
decisions a reviewer is most likely to probe.

| # | Decision | One-line justification |
|---|---|---|
| 1 | **Fixed reclassification tables, not min–max** | Min–max left 97.4% of slope cells above 0.90 and scored categories by their code number — about 48% of the weight was flat or inverted. |
| 2 | **Interpolated ramps, not step classes** | Flat tops gave 973 cells an identical score of 1.000; interpolating between the same anchors restored a genuine ranking without losing transferability. |
| 3 | **Fixed thresholds, not percentiles** | A percentile split always reports ~33% suitable, so the number would describe the method rather than the district — and comparison between scenarios would be impossible. |
| 4 | **Drainage density, not distance to river** | Distance is a siting-convenience measure; density tells you where runoff concentrates, which is what the literature uses. |
| 5 | **Settlement proximity as a moderate-optimal band** | Both extremes are bad — you cannot build inside a town, and a remote site serves nobody. |
| 6 | **80% coverage gate** | Without it, a cell scored on two criteria could outrank a site scored on all six — 13 of the original top 25 were this artefact. |
| 7 | **Theoretical ideals in TOPSIS** | Observed extremes would make scores data-range dependent and break comparability across scenarios. |
| 8 | **Buckley Fuzzy-AHP with an additive scale** | A multiplicative spread cancels under normalisation and returns crisp AHP weights exactly; Chang's method can zero out a relevant criterion. |
| 9 | **Two-stage cached architecture** | It makes scenario switching instant *and* guarantees every method comparison runs on byte-identical inputs. |
| 10 | **Streamlit, no database or API** | The analysis is a pure function of files on disk with one user at a time. |
| 11 | **Consensus instead of validation** | Method-agnostic robustness evidence that requires no ground truth. |
| 12 | **Three sensitivity analyses, not one** | Each answers a different question, and two of them independently found the drainage result. |

---

## 2. Most Likely Reviewer Questions — Across the Whole Presentation

Ranked roughly by likelihood.

1. **Which algorithm is best?** → We cannot say without ground truth. They differ measurably; fifteen sites are chosen by all four.
2. **How do you know your map is accurate?** → We don't, and we say so. We verified the software, not the map.
3. **Your weights are subjective — how do you defend them?** → We don't defend them, we measured them: ±20% retains 90% of the top 10.
4. **What was your learning rate / how many epochs?** → No model is trained. This is a knowledge-driven model, which is a deliberate choice because no labelled data exists. *(See §4 below — this question is very likely.)*
5. **Why these six criteria?** → Five recur across the eight reviewed studies; settlement proximity was added because demand determines usefulness.
6. **Why is rainfall weighted highest when it barely varies?** → It is the water source; and its realised influence *is* lower — measured at 0.80× its assigned weight.
7. **Why 0.65 and 0.85?** → Reasoned, not optimised. What matters is that they are fixed rather than percentile-based.
8. **Why 2.5 km for the drainage window?** → 1 km is ~3 cells and produces speckle; much larger converges to the district mean.
9. **Why 400 people/km² for a settlement?** → It classifies 6.6% of the district, matching the built-up footprint.
10. **Where is your train/test split?** → There is no model that learns; nothing to withhold and nothing to overfit.
11. **Why is your suitable area lower than published studies?** → Continuous scoring against fixed break points; thresholds were not retuned.
12. **Have you visited any site?** → No field verification. Listed as a limitation.
13. **What if a data layer were missing?** → Handled automatically by renormalisation, and we measured the consequence for each layer.
14. **Isn't gap filling inventing data?** → Nearest-neighbour over a few hundred metres on slowly varying layers, ≤2.2% of the district.
15. **Why work in lat/long rather than metres?** → Avoids a second resampling; corrections are explicit and validated by the 99.7% area match.
16. **Why 25 sites and 5 km apart?** → A workable shortlist; closer structures share a catchment.
17. **All your top sites are the same soil and land cover — why?** → Silt Loam covers 78% of the district and scores 1.00. A fair criticism of compensatory aggregation.
18. **Your drainage density looks low.** → HydroRIVERS is thresholded to larger channels; our class breaks are calibrated to it.
19. **You found bugs in your own system — doesn't that undermine the results?** → The opposite; finding them is why the current results can be trusted.
20. **What would you do with more time?** → Ground-truth validation first; the code is already written.

---

## 3. Critical Parameters to Memorise

Know these without looking. They come up constantly.

| Value | What it is |
|---|---|
| **0.0235** | Consistency ratio (threshold 0.10) |
| **0.4285 / 0.2254 / 0.1535 / 0.0932 / 0.0597 / 0.0397** | Weights: rainfall, slope, soil, drainage, land cover, settlement |
| **18.51% — 2,112.6 km²** | High suitability, baseline |
| **54.79% / 26.70%** | Medium / Low |
| **123,555** | In-district grid cells |
| **450 × 422, ~0.31 × 0.30 km** | Analysis grid and cell size |
| **11,412.5 km² vs 11,443 km² = 99.7%** | Area cross-check |
| **0.65 / 0.85** | Classification thresholds |
| **80%** | Coverage gate |
| **25 sites, 0.984 → 0.866, 5 km apart** | The shortlist |
| **1,493 mm/yr**, 2014–2024, 11 years | Rainfall |
| **2.5 km** | Drainage density window |
| **0.242 km/km²** | District drainage density |
| **400 people/km², 1–5 km band, peak at 3 km** | Settlement criterion |
| **90% retained, 70% worst, max shift 3** | ±20% sensitivity |
| **15 of 36 · 1,417 km² (12.41%)** | Consensus across algorithms |
| **18.51 → 13.62 (WLC→TOPSIS) vs 18.51 → 18.32 (AHP→Fuzzy)** | The headline finding |
| **11/11** | Smoke-test checks passing |

---

## 4. Potential Weak Points

### 4.1 "Where is the machine learning?"

**Why it could be challenged:** This is an IT department major project, and the
title says GIS, not ML. A reviewer may expect a model.

**How to answer:** *"There is no trained model, and that is a deliberate design
choice. This is a knowledge-driven model rather than a data-driven one. A learned
model needs labelled examples — a register of existing structures — and that does
not exist for Chandrapur. Knowledge-driven models work precisely where inventories
are unavailable, which is most of rural India. Their weakness is subjectivity, and
that is exactly what our three sensitivity analyses measure."*

**Evidence:** No ML library is installed. The learned-model comparison is scoped
as future work, blocked on the same missing data.

**Do not** get defensive or apologise. The framing is standard in the
suitability-mapping literature.

### 4.2 "You have no accuracy figure"

**Why:** It is the most visible gap in the project.

**How to answer:** Separate verification from validation. *"We verified the
software — eleven automated checks, a 99.7% area cross-check, a 0.08% river-length
conservation check. We did not validate the map against reality, because the
ground-truth data does not exist, and we would rather report nothing than report a
number we cannot support. What we offer instead is consensus."*

**Evidence:** Slides 29 and 30.

### 4.3 The literature review contradicting the project

**Why:** Slide 4 describes an NLP component that slide 20 says was removed.

**How to answer:** Best handled by deleting slide 4. If retained, use the
reframing in the Slide 4 notes — and make sure whoever presents slide 20 says the
same thing.

### 4.4 "Your parameters weren't optimised"

**Why:** True — the 2.5 km window, the 400 people/km² threshold, the 1–5 km band,
the 5 km separation and the 0.65/0.85 thresholds were reasoned, not fitted.

**How to answer:** Concede it directly and pivot to what you *did* do. *"None of
these were optimised against an objective function — each was chosen from physical
reasoning and documented. What we did instead was measure how much the result
depends on them, which is what the sensitivity analysis reports."*

**Do not** claim optimisation that did not happen. It is the one thing that would
undermine the honesty the rest of the presentation is built on.

### 4.5 The soil class coding

**Why:** Unverified, and it carries 15.4% of the weight.

**How to answer:** *"It is a real open item, and we flagged it in our own source
code. If the coding needs remapping, only one lookup table changes."*

### 4.6 The presentation is long

See §6.

---

## 5. Things to Verify Before the Presentation

| # | Item | Action |
|---|---|---|
| 1 | **Slide 4 contradicts slide 20** | Delete slide 4, or use the reframing script. Decide tonight. |
| 2 | **Citation numbering** | Slides 5–6 use [5]–[12]; slide 33 uses [1]–[10]; slide 7 already uses the new numbering. Renumber slides 5–6 to [1]–[8]. Deleting slide 4 makes this natural. |
| 3 | **Slide 18 — "19–34% range"** | 18.51% is *below* 19%. Change to "just below the 18.9–34.3% range" (from Seif 18.85% and Resen 34.33%, your own slides 5–6). |
| 4 | **Slide 22 — rainfall range tile** | Says 1,184–1,713. Measured in-district: **1,189–1,714**. Whole raster: 1,140–1,823. Pick one and label it. |
| 5 | **Slide 29 — "0.765"** | Seed-dependent; I got 0.7614. Say "about 0.76". |
| 6 | **Slide 10 — 27.7 °C and "Census 2011"** | Neither is in the repository. Know your source. |
| 7 | **Timing figures** (0.90 / 0.15 / 1.5 / 2.8 s) | Never formally benchmarked. Say "timed during development" if asked. |
| 8 | **Who provided the expert judgement** | Agree the answer as a team. Not recorded anywhere. |
| 9 | **Speaking allocation** | Not decided. See §6. |
| 10 | **Do not quote the OSM 0.482 figure** | Diagnostic only. Agree as a team that nobody mentions it unprompted. |

---

## 6. Presentation Timing

**Estimated total from slide-level figures: ≈33–35 minutes of speaking**, before
questions and before any live demo.

**That is almost certainly too long for a review slot.** Two cut plans:

### 20-minute version (≈ −14 min)

| Slide | Action | Saved |
|---|---|---|
| 4 | **Delete** | 0:30 |
| 5, 6 | Merge into one spoken summary (~40 s total) | 0:45 |
| 12 | Cut to 20 s — point at the maps, name the two derived criteria | 0:30 |
| 20 | Cut to 25 s — the arc sentence plus three dates | 0:30 |
| 21 | Two rows instead of three, drop the framing sentence | 0:25 |
| 22 | Drop the NoData-trap story (keep for Q&A) | 0:25 |
| 23 | Drop the conservation check and window justification | 0:25 |
| 24 | Symptom + 973→1 only | 0:30 |
| 25 | Drop the export/documentation panels | 0:25 |
| 30 | Describe rather than demo; drop performance figures | 0:30 |
| 31 | Three limitations, two future items | 0:25 |
| 2, 3, 10, 11, 13 | Trim ~15 s each | 1:15 |
| **Protect at full length** | **7, 9, 14, 16, 17, 18, 27, 28, 29, 32** | — |

### 15-minute version

Apply the above, then also compress slides 13 and 16 to their essentials, cut
slide 12 entirely, and reduce slide 19 to narrating one site.

**Never cut these five.** They carry the entire contribution:
- **Slide 7** — research gaps and your response
- **Slide 14** — criterion scoring (contribution 1)
- **Slide 27** — algorithm comparison (the headline finding)
- **Slide 28** — sensitivity (the answer to the standing criticism)
- **Slide 29** — validation honesty and consensus

### Suggested speaking split (four presenters)

A reasonable division by theme — adjust to who knows what best:

| Presenter | Slides | Theme |
|---|---|---|
| 1 | 1–8 | Problem, literature, gaps, objectives |
| 2 | 9–17 | Architecture, data, criteria, methodology |
| 3 | 18–25 | Results, progress, corrections, decision support |
| 4 | 26–33 | Algorithms, sensitivity, validation, conclusion |

**Note:** presenter 4 holds the three highest-value slides (27, 28, 29) and will
field most of the questions. Whoever takes that section should be most fluent on
the sensitivity results and the validation position.

**Everyone** should know §3 (critical parameters) and the top five answers in §2,
regardless of which slides they present — questions do not respect section
boundaries.
