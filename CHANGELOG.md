# Changelog

Dated record of changes to the project. This file stands in for git history
until the repository is initialised — **every change from here on should get an
entry**, so that the work is traceable when the project is written up.

Earlier history, reconstructed before this file existed, is in
[docs/archive/CHANGES_SINCE_INITIAL_ZIP.md](docs/archive/CHANGES_SINCE_INITIAL_ZIP.md).

---

## 2026-10-02 — Soil texture legend corrected: the dominant class was mis-identified

The open item carried since 29 July in `criteria.py`, `docs/METHODOLOGY.md` §3
and `TODO.md` §A2 is resolved. **The legend was wrong.** This is the largest
correction since Sprint 1 and it changes every reported result.

### How it was found

Asked where the soil data came from. `data/soil_texture.tif` carries no legend
metadata — QGIS stripped it on re-export, the `.aux.xml` holds only statistics,
and the QGIS project's palette labels are bare numbers (`label="1"`). None of
the artefacts in the repository could answer the question.

The **original download** survives outside the repo at
`Documents/Major Project Research Papers/Chandrapur_SoilTexture.tif` and retains
its full SoilGrids metadata, including an explicit `LEGEND` tag.

### Provenance, now established

ISRIC SoilGrids250m, product `TEXMHT_M_sl1` — *Texture class (USDA system) at
depth 0.00 m*, published 2017-03-10, `TEXMHT_M_sl1_250m_ll.tif`.
**Cite Hengl et al. 2017, doi:10.1371/journal.pone.0169748.**

Legend, verbatim from the file:
`1:Cl 2:SiCl 3:SaCl 4:ClLo 5:SiClLo 6:SaClLo 7:Lo 8:SiLo 9:SaLo 10:Si 11:LoSa 12:Sa`

### The error

| Code | Was read as | Score | Actually | Share |
|---|---|---|---|---|
| 1 | Sand | 0.55 | **Clay** | 18.6% |
| 4 | Silt Loam | **1.00** | **Clay Loam** | **77.8%** |
| 6 | Sandy Clay Loam | 0.80 | Sandy Clay Loam ✅ | 3.2% |
| 7 | Silt Clay Loam | 0.50 | **Loam** | 0.4% |

Three of four wrong; codes 1 and 4 cover 96.4% of the district. The two
consequential errors ran in opposite directions — Clay Loam scored at the
maximum as if it were Silt Loam, while Loam, the best texture for recharge,
scored 0.50. Clay out-scored Loam.

The `⚠ VERIFY BEFORE SUBMISSION` comment written on 29 July named this exact
failure mode and was correct.

### Where the wrong legend came from

Checked, because the code claimed a source. `criteria.py` attributed the legend
to "the project's soil slide". **Slide 22 contains no legend** — it records the
dataset (SoilGrids250m 2017-03), period, resolution and CRS, and says only that
the layer was *"reclassified into suitability ranks based on the project's soil
interpretation"*. Slide 17 offers only generic prose ("Clay retains water, Sand
drains quickly").

No file predating `criteria.py` contains the mapping. The April `docs/archive/AHP_*.md`
documents mention soil only in general terms. **The four labels were assumed
when `criteria.py` was written on 2026-07-29, and the attribution to the slide
was incorrect** — which made an assumption look sourced and is the reason it
survived two months of review. That misattribution has been corrected in
`criteria.py` and `docs/METHODOLOGY.md` §3.

### Changed

- **`criteria.py`** — `SOIL_TEXTURE_SCORES` and `SOIL_TEXTURE_LABELS` rewritten
  against the real legend, all 12 classes tabulated so the table transfers.
  Scores follow the reasoning already in `docs/METHODOLOGY.md` §3: Loam 1.00,
  Silt Loam 0.95, Sandy Loam 0.85, Sandy Clay Loam 0.80, Loamy Sand 0.70,
  Clay Loam 0.60, Silt 0.60, Silty Clay Loam 0.55, Sand 0.55, Sandy Clay 0.40,
  Silty Clay 0.30, Clay 0.25.
- **`derived_maps.py`** — `HSG_FROM_SOIL` carried the same error and assigned
  Clay to hydrologic group A (highest infiltration) when it belongs in group D.
  Remapped to the standard USDA-NRCS assignment across all 12 classes.
- **`docs/METHODOLOGY.md` §3** — table, provenance and resolved warning.
- **`tools/paper_figures.py`** — two hardcoded commentary lines asserted "all 25
  sites are Silt Loam" and "77.8% is Silt Loam". Both replaced with computed
  output so they cannot go stale again.
- **`docs/SOIL_LEGEND_CORRECTION.md`** (new) — full record.

### Result change

| | Before | After |
|---|---|---|
| High suitability | 18.51% — 2,112.6 km² | **6.44% — 735.0 km²** |
| Medium | 54.79% | 52.48% |
| Low | 26.70% | 41.08% |
| Score range / mean | 0.256–0.984 / 0.729 | 0.210–0.957 / 0.673 |
| Sites, rank 1 → 25 | 0.984 → 0.866 | 0.957 → 0.854 |
| Top-10 retained vs before | — | **2 / 10** |
| Soil criterion mean score | 0.908 | 0.543 |
| Curve Number (mean) | 70.5 | **85.97** |
| Runoff depth, 100 mm storm | 35.4 mm | **63.65 mm** |
| Runoff coefficient | 0.354 | **0.637** |

### Two findings the correction produced

**1. The shortlist-concentration limitation is materially weaker.** Before, all
25 candidate sites sat on a single soil class scoring 1.00. Now they span three
textures — Clay Loam 10, Loam 9, Sandy Clay Loam 6 — and land cover spreads to
24 Cropland + 1 Grassland. The model is no longer selecting the most common soil
in the district; it is discriminating between textures.

**2. The headline "aggregation dominates weighting" claim must be restated.**
On *area* it has weakened sharply: WLC→TOPSIS now moves the High share by
0.79 pp and AHP→Fuzzy-AHP by 0.40 pp, a ratio of about 2× where it was 26×.
On *ranking* it is stronger and cleaner than before:

| Algorithm | High % | Top-10 shared | Spearman ρ | Class agreement |
|---|---|---|---|---|
| AHP + WLC | 6.44 | 10/10 | 1.000 | 100.0% |
| AHP + TOPSIS | 5.65 | **5/10** | 0.964 | 87.2% |
| Fuzzy-AHP + WLC | 6.04 | **10/10** | 1.000 | 99.0% |
| Fuzzy-AHP + TOPSIS | 4.92 | **5/10** | 0.967 | 87.3% |

Changing the aggregation rule now replaces **half the shortlist**; changing the
weighting method replaces **none of it**. State the finding on shortlist overlap
and class agreement, not on class area.

### Other figures that moved

- **Sensitivity ±20%:** 88% of top-10 retained (60% worst case), max shift 3.
  Most influential criterion is now **soil** (1.42 pp), not drainage.
- **Map removal:** rainfall removal now retains **0/10**; drainage 3/10,
  soil 4/10, slope 5/10, population 5/10, lulc 9/10.
- **Effective weights:** soil flipped from over-contributing (1.260) to
  under-contributing (**0.812**); slope rose to **1.404**.
- **Consensus across algorithms:** 35 distinct locations, 15 unanimous,
  4/4 High **4.63% — 528.5 km²** (was 12.41% — 1,416.8 km²).
- **Consensus across scenarios:** 61 distinct, only **2** unanimous (was 7);
  5/5 High 2.10% — 239.9 km².
- The §9 weighted-dispersion ordering **still predicts map-removal retention**
  (rainfall > drainage > soil > population ≈ slope > lulc), so that corrected
  claim survives.

### Verification
`tools/smoke_test.py` — **11/11 passing** after the change, including rank
ordering. All figures regenerated via `tools/paper_figures.py --csv-dir
outputs/paper`, plus `exports.py`, `derived_maps.py`, `sensitivity.py`,
`algorithms.py`, `consensus.py --write`.

### Still to do
Every downstream document now carries superseded numbers: `CLAUDE.md`,
`docs/PAPER_DATA_HANDOFF.md`, `docs/presentation/FINAL_PROJECT_DOCUMENTATION.md`,
`docs/presentation/FINAL_PRESENTATION_SPEAKER_NOTES.md`, `docs/PAPER_GUIDE.md`, `README.md`,
`docs/archive/PROGRESS_UPDATE.md` and the slide deck. `CLAUDE.md` and
`docs/PAPER_DATA_HANDOFF.md` are updated in this pass; the rest are flagged.

---

## 2026-08-25 — Deck review against the current build; OSM structure diagnostic recorded

No pipeline code changed. This entry exists because three things happened that
would otherwise have gone unrecorded.

### A. Diagnostic: OSM water features as a stand-in for ground truth

While looking for anything that could stand in for `data/rwh_structures.geojson`,
158 OpenStreetMap features tagged as artificial water bodies inside the district
were pulled via the Overpass API and pushed through the AUC harness.

**This is not a validation result and must not be reported as one.** OSM
artificial water polygons are not RWH structures — they include farm ponds,
quarry pits, tanks and mine water. The exercise was run to exercise the code path
and to see whether the surface behaves sensibly against *any* real point set.

Indicative numbers, for internal use only:

| Measure | Value |
|---|---|
| Overall AUC against the 158 points | 0.482 |
| AUC of the settlement-proximity criterion alone | 0.379 |

The overall figure is indistinguishable from chance (0.5), but the breakdown is
the informative part: **the entire deficit comes from settlement proximity.**
Every other criterion scored these locations at or above chance. Real water
structures sit closer to villages than the current 1–5 km moderate-optimal band
assumes — people build tanks where they live.

This is empirical evidence bearing on **TODO §A3** (review assumptions with the
guide). It does not justify changing `criteria.SETTLEMENT_PEAK_KM` on its own,
because the point set is the wrong population. It does justify raising the
question, and it predicts what real ground truth is likely to show.

### B. Presentation reviewed against the current build

The user added the current deck at `docs/BTech Major Project PPT (1).pptx`
(37 slides, superseding the 38-slide version in `Downloads/`). It was inspected
as a zip archive and via `python-pptx`; **nothing in it was modified.**

Every slide-number reference in **TODO §A4 was stale** — written against the old
38-slide deck, and off by one or pointing at the wrong slide entirely after the
deck lost a slide. §A4 has been renumbered against the file now in `docs/`.

The comparative material the guide asked for (four algorithms, five scenarios,
consensus, three sensitivity methods) was delivered as a written change list in
conversation rather than as slide edits, at the user's direction. All figures in
that list were re-run in this session: baseline area statistics, `algorithms.py`,
`consensus.py`, `sensitivity.py`.

### C. `python-pptx` 1.0.2 installed into the venv

Installed to read the deck. **Deliberately not added to `requirements.txt`** — no
module in the project imports it, and it is not needed to run any part of the
pipeline. Recorded here so that a future venv rebuild dropping it is understood
rather than investigated. (Contrast with `matplotlib`, which *was* a real
dependency missing from the file — fixed 2026-08-08.)

---

## 2026-08-23 — Professor feedback: fertile-land scenario, consensus view, Spearman

### A. New scenario: "Fertile farmland"
Requested in review — a weighting aimed at land that benefits farmers while
still suiting rainwater harvesting. Soil texture (0.257) and cropland cover
(0.229) lead, then rainfall (0.204). **CR 0.0146**; High 28.19%; it selects a
different top site (79.3432, 20.4493) from the other four, so it is genuinely
distinct rather than a relabelling.

⚠ Named a **proxy** in its rationale string: it reweights the existing six
criteria and no soil-fertility dataset (organic carbon, N/P/K, pH) is held.
SoilGrids publishes those at 250 m if a real fertility model is wanted later.

Five scenarios now: baseline 0.0235 / recharge 0.0044 / community 0.0059 /
low-earthwork 0.0078 / fertile farmland 0.0146 — all CR < 0.10.

### B. Spearman's rank correlation added to the algorithm comparison

| Algorithm | Pearson r | Spearman ρ | Class agreement |
|---|---|---|---|
| AHP + WLC | 1.000 | 1.000 | 100.0% |
| AHP + TOPSIS | 0.961 | 0.964 | 74.5% |
| Fuzzy-AHP + WLC | 1.000 | 1.000 | 98.7% |
| Fuzzy-AHP + TOPSIS | 0.964 | 0.967 | 74.9% |

Both are reported because they answer different questions: Pearson asks whether
two scores move together linearly, **Spearman asks whether they rank locations
the same way** — which is what a site-selection method is for.

### C. New file: `consensus.py` — which sites survive a change of method

Two independent axes, computed separately as agreed:

- **algorithms** — the 4 engines, weighting held fixed
- **scenarios** — the 5 weightings, algorithm held fixed

Three outputs per axis: a consensus site table, a **Borda-aggregated ranking**,
and an **agreement raster** counting how many variants class each pixel High.

Sites are matched across variants **by position (2 km)**, not by rank — each
variant extracts candidates independently, so a location shifts a pixel or two.
The tolerance sits inside the 5 km minimum separation, so a cluster can never
absorb two distinct sites from one variant.

Borda: within a variant a site at rank r of N scores N − r + 1; a variant that
did not select it contributes 0. The zero is deliberate — silence is not
evidence in a site's favour.

| Axis | Locations proposed | Selected by all | District High in all |
|---|---|---|---|
| 4 algorithms | 36 | **15** | **12.41%** — 1,416.8 km² |
| 5 scenarios | 54 | **7** | **10.66%** — 1,217.1 km² |

**Why this matters now.** Consensus is method-agnostic robustness evidence that
needs **no ground truth**. "Fifteen sites selected independently by four MCDA
methods, and 1,417 km² classed High by all of them" is defensible today, which
partly covers the gap while validation remains blocked.

App: new **Consensus Sites** panel with an axis radio, headline metrics, the
Borda table, the agreement map and two downloads. CLI: `python consensus.py`,
plus `--write` for `outputs/consensus_{axis}.csv` and `agreement_{axis}.png`.

### D. Paper guide extended for the review requests

- **§4.0** complete parameter table — every tunable constant, its value and
  where it lives (28 rows). Reviewers ask for this.
- **§4.10** all five scenarios with their full weight vectors, and an explicit
  warning that "low-earthwork" and "fertile farmland" are proxies.
- **§4.11** consensus results for both axes.
- **§5** Spearman and Borda formulas.
- **§6.9 drawbacks of Euclidean distance in TOPSIS** — orthogonality assumption
  violated by correlated criteria; weak compensation as an imported assumption;
  dependence on the choice of ideal points; middle-range compression that
  explains the lower mean (0.669 vs 0.729) and smaller High class.
- **§6.10 which method outperforms** — it cannot be answered without validation.
  Naming an outperformer needs an external standard; the methods can only be
  said to *differ* until per-algorithm AUC exists.
- **§9** two new figures: the agreement maps for both axes.

### E. Map removal + single-parameter sensitivity (added after follow-up)

The review also asked for **map removal techniques**; confirmed as **map removal
sensitivity analysis** (Lodwick, Monson & Svoboda, 1990), a named GIS-MCDA
method. Implemented in `sensitivity.py` together with its usual companion,
single-parameter sensitivity (Napolitano & Fabbri, 1996).

**Map removal** drops each criterion layer entirely (weight set to zero; the
per-pixel renormalisation redistributes it) and measures how far the map moves:

| Criterion | Weight | S index % | Top-10 retained | Δ High % |
|---|---|---|---|---|
| Rainfall | 0.428 | **17.374** | **1/10** | +23.95 |
| Slope | 0.225 | 8.979 | 9/10 | −5.24 |
| Soil | 0.154 | 5.301 | 10/10 | −4.39 |
| Drainage | 0.093 | 4.280 | **2/10** | +8.36 |
| Land cover | 0.060 | 2.501 | 10/10 | +0.56 |
| Settlement | 0.040 | 1.780 | 9/10 | +2.24 |

⚠ **Index adapted.** The original S = |V/N − V′/n| / V × 100 carries /N and /n
to turn a weighted *sum* into a per-parameter average. This project's
aggregation already divides by the sum of weights present, so V and V′ are both
0–1 and applying /N and /n again would normalise twice. The index used is the
relative variation |V − V′| / V × 100. Documented in the function and flagged in
the paper guide as a stated adaptation.

**Two findings.** (1) The S index follows weight order, but **site retention does
not**: removing drainage changes the surface least among the top four (4.28%) yet
leaves only **2 of 10** sites standing — worse than removing slope. Drainage
barely moves the map but reorders the shortlist, because it has the highest
spatial variance and is what separates near-identical candidates. This
independently corroborates the ±20% finding. (2) Removing rainfall **inflates**
High to 42.46%: percentile-rank scoring fixes its mean near 0.6, so it acts as a
brake on the composite. A criterion can be restrictive rather than merely
important — which its weight alone does not reveal.

**Single-parameter sensitivity** compares each criterion's effective weight,
mean of (w_i·r_i)/V × 100, against its theoretical weight:

| Criterion | Theoretical % | Effective % | Ratio |
|---|---|---|---|
| Rainfall | 42.85 | 34.11 | 0.796 |
| Slope | 22.54 | 29.11 | **1.292** |
| Soil | 15.35 | 19.35 | 1.260 |
| Land cover | 5.97 | 7.25 | 1.214 |
| Drainage | 9.32 | 6.61 | **0.710** |
| Settlement | 3.97 | 3.57 | 0.901 |

Criteria that score uniformly well across the district contribute more than
their assigned weight (slope 1.29× — the district is flat; soil 1.26× — Silt
Loam dominates at 1.00); those that score uniformly poorly contribute less
(drainage 0.71× — district density only 0.242 km/km²). The gap is explained by
each criterion's distribution over the study area, not by the AHP judgements.

App: both tables render under the Sensitivity panel on the same button press.
Paper guide: §4.7b, §4.7c, formulas added to §5.

---

### F. Validation harness completed on the code side

Two gaps closed, both flagged by re-reading TODO for work that was mine rather
than manual:

- **`validate_all_algorithms()`** — runs every algorithm against the same
  structures and ranks them by AUC. Previously I had said this "is just a loop
  over the four" without writing it; now it exists, so the moment ground truth
  arrives the outperformance question is answered by running one command.
- **`candidate_proximity()`** — a different question from the AUC. The AUC asks
  whether the *surface* scores known structures highly; this asks whether the
  *shortlist* lands near them. For each candidate the distance to the nearest
  known structure is measured and compared against random in-district points,
  summarised as the probability that a random candidate is closer than a random
  background point (0.5 = chance). This is the "existing versus candidate sites"
  comparison asked for in review.

Both dry-run against a synthetic point set in a scratch directory to exercise
the code paths — **not results**, and nothing was written to `data/`. With the
real file absent, `python validation.py` still reports `missing_data` and
produces no number.

New `TODO.md` §D5 separates outstanding **code-side** work (Streamlit
deprecation tidy, fixed-mm rainfall band comparison, `docs/archive/AHP_*.md` consolidation)
from the manual GIS and download tasks, so the two are no longer interleaved.

---

### Verification
15 modules compile · smoke test extended to 11 checks including consensus, all
passing · consensus runs both axes in ~2.8 s · 14 artefacts in `outputs/`.

---

## 2026-08-12 (e) — Bug fix: candidate ranks did not follow score

### The failure
Reported from the running app: **rank #22 showed suitability 0.948 while rank
#13 showed 0.866.** Across the 25 sites, ranks 1–13 descended, then rank 14
jumped back up to 0.977 and descended again.

**Cause.** `_extract_top_locations()` numbered sites in *selection* order.
Selection runs in two stages — best-pixel-per-tile (for district-wide spread),
then global-maxima fill — and **each stage emits its own descending run**. A
stage-2 global maximum routinely outscores a late stage-1 site, which is the
best pixel of a mediocre tile. So the published ranking contradicted the
documented rule, "final ranks assigned strictly by suitability score
descending".

### The two selection stages, and why they differ

| Stage | Question it asks | Purpose |
|---|---|---|
| 1 — best pixel per tile | *"What is the best site near here?"* | Geographic spread — one seat per tile, however good or poor that tile is |
| 2 — global maxima | *"What is the best site left anywhere?"* | Quality — ignores tile boundaries |

A tile winner is only a **local** best. A tile covering thin, marginal terrain
still gets a seat in stage 1; a tile packed with excellent land also gets exactly
one, and its runners-up — often better than another tile's winner — must wait for
stage 2.

### Why the break landed at rank 13/14

The 450 × 422 grid is split 5 × 5 into tiles of 90 × 84 px (~698 km² of the
bounding box). Best score per tile, with the count of high-suitability pixels in
brackets:

```
  --        0.911(166)   0.977(3018)  0.904(393)   0.866(92)
  --        0.915(271)   0.984(4193)  0.976(4938)  0.931(1481)
  --          --         0.876(33)    0.928(485)   0.967(3450)
  --          --           --         0.920(2464)  0.925(563)
  --          --           --         0.970(834)   0.982(507)
```

Only **15 of 25 tiles** contain any high-suitability pixels — the whole western
column is the low-suitability west. Sorted, those 15 tile winners were:

> 0.984, 0.982, 0.977, 0.976, 0.970, 0.967, **0.931, 0.928, 0.925, 0.920, 0.915,
> 0.911, 0.904, 0.876, 0.866**

Thirteen survived the 5 km separation rule and became ranks 1–13, ending at
0.866. Stage 2 then restarted from the global maximum — where scores run 0.984,
0.983, 0.982, 0.982, 0.982 … — so its first pick (0.977) immediately outscored
the tail of stage 1.

The contrast that produced the bug: the tile with **92** high pixels (best 0.866)
got a seat in stage 1, while the tile with **4,938** high pixels contributed one
site in stage 1 and left ~4,900 pixels — many above 0.97 — to stage 2. Ranks
1–6 were tile winners that were also globally excellent; ranks 7–13 were tile
winners from thin tiles; ranks 14–25 were runners-up from the rich tiles.

**Fix.** New `_rank_by_score()` stage: after selection completes, sort by score
descending (ties broken by the same continuous ranker used during selection) and
renumber 1..N. Applied at both exit points, including the early return when
stage 1 alone fills the quota.

**The two-stage selection is deliberate and was left unchanged.** Without stage 1
all 25 sites would cluster in the north-central cropland belt, since that is
where every top score lives; with the 5 km separation that is a tight cluster
over roughly a sixth of the district, which is far less useful to a planning
authority than options spread across talukas. Selection order still controls
**which** sites are chosen. It no longer controls what they are called.

### Verified
0 out-of-order ranks across all four algorithms and all four scenarios; ranks
contiguous 1..25; site count unchanged; exports and the app reflect the new
numbering.

| | Before | After |
|---|---|---|
| Out-of-order ranks | 1 of 25 | **0 of 25** |
| Rank #13 / #22 scores | 0.866 / 0.948 | 0.955 / 0.904 |
| Rank #1 / #25 | 0.984 / 0.936 | 0.984 / 0.866 |

### Regression guard
`tools/smoke_test.py` now asserts ranks are 1..N with non-increasing scores.
This is the second bug in a row that only appeared in the running app, so the
check belongs in the smoke test rather than in a one-off verification.

### How it went unnoticed

Worth recording, because the same failure mode could hide another bug.

1. **It predates every change in this changelog.** `'rank': len(locations) + 1`
   was in `_extract_top_locations()` in the original code. That function was then
   rewritten four times — Sprint 1 scoring, the tie-break, drainage density, and
   the Sprint 2 stack/score split — and the line survived each rewrite unexamined.
2. **Only the first few sites were ever printed.** Development checks used
   `[:3]`, `[:5]` or `[:8]`, and every one of those prefixes is correctly
   descending. The break is at position 14. Checking a prefix is not checking the
   list.
3. **The tie plateau masked it until recently.** Before the ramp fix of
   2026-08-08 (a), 973 pixels shared a score of exactly 1.000, so the leading
   sites were identical and nothing could look out of order. Making the scores
   continuous is what exposed it.
4. **The invariant was documented but never asserted.** "Final ranks assigned
   strictly by suitability score descending" appears in the methodology slide and
   in `docs/PAPER_GUIDE.md`; nothing tested it against actual output.

### Documents corrected
`docs/PAPER_GUIDE.md` §4.6 — the top-five site table changed from rank 4 down
(rank 4 is now 79.3262, 20.4549 at 0.977). Anyone who had already copied that
table into a draft must regenerate it; `outputs/rwh_sites.csv` is authoritative.

Dated entries earlier in this changelog quote site details that were true when
written and are left as historical record.

---

## 2026-08-12 (d) — Bug fix: read-only matrix in the sidebar editor

### The failure
Running the app raised, on load, before anything rendered:

```
ValueError: assignment destination is read-only
  app.py line 243 → matrix[i, i] = 1.0
```

**Cause.** `st.data_editor` returns a DataFrame backed by a **read-only** buffer.
The matrix editor used `np.asarray(edited, dtype=float)`, which does not copy, so
enforcing reciprocity by writing to the diagonal wrote into that read-only
buffer. Fixed with `np.array(edited, dtype=float, copy=True)`, with a comment
naming the failure so it is not "simplified" back.

### Why it was not caught earlier
Every previous check ran `streamlit run app.py --server.headless` and treated a
clean startup as verification. **That proves almost nothing:** Streamlit starts
the server but does not execute the script body until a browser session
connects, so the sidebar code never ran. The underlying functions were tested
directly and passed; the app-level path was never exercised.

### New file: `tools/smoke_test.py`
Runs the app through Streamlit's `AppTest` harness — which *does* execute the
script — and exits non-zero on any failure. Nine checks: script loads, run
analysis, switch scenario, switch algorithm (×2), return to baseline, export
buttons present, run sensitivity, compare algorithms. Takes ~40 s. No pytest;
the project has no test framework and this deliberately does not add one.

Verified passing, with the values it reports along the way:

| Step | Result |
|---|---|
| run analysis | High 18.5% |
| scenario → Maximise recharge | High 30.1% |
| algorithm → AHP + TOPSIS | High 17.7% |
| back to baseline | High 18.5% |
| export buttons | 4 present |
| sensitivity / comparison buttons | both run clean |

### Docs
`RUNBOOK.md` gains the smoke test in the command table, a troubleshooting entry
for this error, and a note that a successful `streamlit run` is not evidence the
app works. `CLAUDE.md` corrected — it previously said no tests exist.

### Known deprecation warnings (not errors)
Streamlit 1.61 warns about `use_container_width` (→ `width=`) and
`st.components.v1.html` (→ `st.iframe`). Both still function. Left alone rather
than risk the map rendering during a bug fix; worth a tidy pass later.

---

## 2026-08-12 (c) — Runbook, paper guide, and the structure-collection task

### `RUNBOOK.md` (new)
Single reference for every command: what it does, what it writes, how long it
takes, plus common workflows and troubleshooting. Covers the failure modes hit
during this project — the damaged-venv rebuild, the `rasterio` 1.5.0 pin, the
`tools/inspect.py` stdlib shadowing, and PowerShell execution policy. Also lists
what deliberately does **not** exist (tests, report generation, ML, validation
results) so nobody hunts for them.

### `docs/PAPER_GUIDE.md` (new)
Self-contained brief for drafting the research paper in a separate session
without repository access: section plan with a page budget, every verified
number pre-formatted as tables, the equations, the eight methodological
decisions a reviewer will probe, seven honest limitations, the figure list, and
the commands that regenerate each figure.

Includes an explicit **"must not claim"** list — no AUC, no accuracy metric, no
machine learning, no field verification, no cost analysis, no annual runoff
volume. None of those exist, and a methodology section forces specifics that
would have to be invented and kept mutually consistent.

Notes the accepted alternative if the ML layer is to be mentioned: the group's
own Multimodal-DL paper labels its numbers "projected evaluation targets… not
finalized empirical results". Framework-with-targets is honest; describing
training that did not happen is not.

### `TODO.md` §A1b — digitise known RWH structures
Promoted to its own task next to the buffered re-export, since both are QGIS
jobs. Full walkthrough: QGIS layer setup, what a check dam versus a farm pond
looks like in satellite imagery, splitting the district four ways, target
150–300 points, the expected GeoJSON schema, and the Geo-MGNREGA / Bhuvan route
as the alternative to digitising.

**This is the highest-leverage task in the backlog** — one file unblocks both
the AUC validation (Sprint 3) and all of Sprint 4.

---

## 2026-08-12 (b) — Sprint 3: pluggable MCDA engines + validation harness

### A. New file: `algorithms.py` — four algorithms over one criteria stack

Two orthogonal choices, combined into a single selectable algorithm:

- **Weighting** — AHP (crisp Saaty matrix) or **Fuzzy-AHP** (triangular fuzzy
  numbers, Buckley geometric mean).
- **Aggregation** — **WLC** (weighted linear combination) or **TOPSIS**
  (closeness to the ideal solution).

`score_stack()` now takes an `aggregator` callable, so every engine consumes the
same stack and the same 0–1 criterion scores. Any difference between outputs is
attributable to the method alone.

**The distinction worth reporting:** WLC is *fully compensatory* — a high
rainfall score offsets a poor slope score in direct proportion. TOPSIS is *not* —
it measures Euclidean distance to the ideal, so a site weak on any high-weight
criterion is penalised harder. Comparing them shows whether the ranking depends
on that assumption.

**TOPSIS uses theoretical ideals** (best attainable = 1, worst = 0 on the
criterion scale), not the observed best and worst pixel. Observed extremes would
make the score depend on the data range — the same defect as the min–max
normalisation removed in Sprint 1 — and would stop scores being comparable
between scenarios or districts.

### B. Fuzzy-AHP — a bug caught during implementation

The first implementation used a uniform **multiplicative** spread,
a → (a/s, a, a·s). It returned weights **identical to crisp AHP to three
decimal places.**

Not a coincidence: a uniform multiplicative spread scales every row's fuzzy
geometric mean by the same constant, so the fuzziness cancels exactly during
normalisation. Replaced with the standard additive fuzzy Saaty scale — 3 becomes
(2, 3, 4), 1/3 becomes (1/4, 1/3, 1/2), clipped at the ends so 1 becomes (1,1,2)
and 9 becomes (8,9,9). The asymmetry at the scale ends is what makes the fuzzy
weights genuinely differ. Documented in `_to_tfn()` so it is not "simplified"
back.

Buckley's geometric mean is used rather than Chang's extent analysis, which is
more commonly cited but can assign zero weight to a genuinely relevant criterion.

### C. Comparison results (baseline matrix, same stack)

| Algorithm | High % | Mean score | Top-10 shared | Surface corr | Class agreement |
|---|---|---|---|---|---|
| AHP + WLC (baseline) | 18.51 | 0.729 | 10/10 | 1.000 | 100.0% |
| AHP + TOPSIS | 13.62 | 0.669 | 9/10 | 0.961 | 74.5% |
| Fuzzy-AHP + WLC | 18.32 | 0.731 | 7/10 | 1.000 | 98.7% |
| Fuzzy-AHP + TOPSIS | 12.92 | 0.671 | 9/10 | 0.964 | 74.9% |

Fuzzy-AHP weights: rainfall 0.417 (vs 0.428), soil 0.159 (0.154), drainage 0.097
(0.093), slope 0.224 (0.225), lulc 0.062 (0.060), population 0.041 (0.040).

Two findings worth writing up:

1. **The choice of aggregation matters far more than the choice of weighting.**
   Switching WLC → TOPSIS moves the highly-suitable area by ~5 percentage points
   and drops class agreement to ~75%. Switching AHP → Fuzzy-AHP moves it by 0.2
   points with 98.7% class agreement.
2. **Surface correlation of 1.000 does not mean the same sites are picked.**
   Fuzzy-AHP + WLC correlates perfectly with the baseline surface yet shares only
   7 of the top 10 sites — small weight changes reshuffle near-tied candidates.
   Correlation is the wrong metric for ranking stability; top-N overlap is the
   right one.

### D. New file: `validation.py` — ROC-AUC against known structures

Samples the suitability surface at known RWH structure locations and at random
in-district background points (default 5× the positives, excluding a 1 km buffer
around positives), then computes ROC-AUC via the Mann-Whitney U statistic — no
scikit-learn needed. Also reports the share of known structures falling in High
and in Medium-or-High.

**AUC maths verified** against known cases: perfect separation 1.0, perfect
inversion 0.0, all-tied 0.5, interleaved 0.25, and N(1,1) vs N(0,1) → 0.765
against a theoretical 0.760.

⚠ **`data/rwh_structures.geojson` does not exist**, so validation currently
reports `missing_data` and exits without producing a number. It will not invent
one. The end-to-end path was exercised against a synthetic point set written to
a scratch directory — that was a code test, **not a result**, and nothing was
written into `data/`.

### E. App

Sidebar gains an **Algorithm** selector with a one-line explanation of each
choice; the active algorithm and scenario are shown beside the map title. New
**Algorithm Comparison** panel runs all four and tabulates High %, mean score,
top-N overlap, surface correlation, class agreement, plus the per-algorithm
weights.

The consistency ratio is labelled "(of the crisp matrix)" when Fuzzy-AHP is
selected, because fuzzy AHP has no standard CR.

### Verification

All 12 modules compile · four algorithms run end to end and render maps ·
comparison completes in ~2.8 s · AUC verified against five known cases ·
validation correctly reports missing data · Streamlit starts.

---

## 2026-08-12 (a) — Context management: `CLAUDE.md` + `tools/inspect.py`

Added so that long working sessions survive context compaction without
re-deriving facts or guessing at project state.

### `tools/inspect.py` (new)
CLI that profiles a data file without dumping it:
`python tools/inspect.py <path> [--rows N] [--cols A,B]`. Handles vector
(`.geojson`/`.shp`/`.gpkg`), raster (`.tif`) and tabular (`.csv`/`.parquet`).
Raster statistics come from a **decimated read**, never a full load — a 22 MB
global CHIRPS raster profiles in 0.4 s. Output is 11–38 lines across every file
type tested.

Two things worth knowing:

- **The filename shadows the standard library.** Running `tools/inspect.py` as a
  script puts `tools/` at the front of `sys.path`, so numpy's internal
  `import inspect` resolved to this file and every run died with
  `module 'inspect' has no attribute 'cleandoc'`. Fixed by stripping the
  script's own directory from `sys.path` before any third-party import, with a
  comment explaining why. Do not remove those lines.
- **It flags undeclared fill values.** On `chirps-v3.0.2020.tif` it reports the
  raw mean of −6,947, warns that 72% of pixels look like a `-9999` fill with
  nodata undeclared, and gives the corrected mean of 889.6 — the exact trap that
  would have corrupted the rainfall layer.

### `CLAUDE.md` (new, hard-capped at 120 lines)
Project facts, pipeline stage order, key-file table, conventions, verified
commands, current state, and working agreements. Loaded every session, so it is
kept to facts and tables rather than prose.

**Corrections it records**, found by checking the repo rather than accepting the
brief: sensitivity analysis, exports and report generation were described as
complete but **none existed** at the time; `data/rwh_structures.geojson` did not
exist; there were no notebooks, no QGIS project files and no tests. Commands
that could not be verified are marked as such — `setup_data.py` is untested
because it mutates `data/`.

---

## 2026-08-08 (b) — Sprint 2: exports, editable weights, scenarios, sensitivity

### A. Pipeline split — `build_criteria_stack()` + `score_stack()`

`run_ahp_analysis()` did everything in one pass, so trying a different weight
vector meant reloading and reprojecting every raster. Split into:

- **`build_criteria_stack(data_dir)`** — raster loading, gap fill, distance
  transforms, drainage-density convolution, criterion scoring. Weight-independent,
  cached in-process (`clear_stack_cache()` to invalidate).
- **`score_stack(stack, weights)`** — weighted overlay, classification, area
  statistics, candidate extraction, explainability.

`run_ahp_analysis()` remains as a wrapper and now also accepts `weights=` or
`scenario=`. **Verified identical output** before and after the refactor:
suitability raster, area statistics and all 25 site scores match exactly.

| | Cost |
|---|---|
| `build_criteria_stack` (once) | 0.90 s |
| `score_stack` (per weight vector) | **0.15 s** |
| 12-run sensitivity sweep | **1.6 s** |

### B. Scenario presets (`ahp.SCENARIOS`)

Four named weightings over the same six criteria — **no new data required**, only
a different pairwise matrix. Built from an importance ranking snapped to the
Saaty 1–9 scale by `matrix_from_levels()`, which keeps them consistent by
construction.

| Scenario | CR | Dominant criteria | High % |
|---|---|---|---|
| Baseline (balanced) | 0.0235 | rainfall 0.428 | 18.5% |
| Maximise recharge | 0.0044 | soil 0.273, slope 0.266 | 30.1% |
| Community-focused | 0.0059 | settlement 0.245, rainfall 0.245 | 18.8% |
| Low-earthwork siting | 0.0078 | slope 0.367, lulc 0.200 | 29.9% |

⚠ "Low-earthwork siting" is deliberately **not** called a cost scenario. The
project holds no land-value or unit-rate data; weighting slope and land cover is
a proxy for construction difficulty, not a cost model. Data that would support a
real one is scoped in TODO.md §D4.

Scenarios change the answer materially — "community-focused" selects a different
top-ranked site from the other three.

### C. Editable pairwise matrix in the sidebar

`st.data_editor` on the 6×6 matrix. The upper triangle is authoritative; the
lower triangle is rebuilt as its reciprocal and the diagonal forced to 1, so an
edited matrix is always valid. CR recomputes live with an accept/reject verdict,
and the analysis re-scores automatically (~0.15 s) when the weights change.

`AHPEngine.calculate_weights()` and `is_consistent()` now accept an optional
matrix argument.

### D. New file: `exports.py`

Every artefact returns `bytes`, so the same code backs the Streamlit download
buttons and `python exports.py` (which writes all five to `outputs/`).

| Artefact | Notes |
|---|---|
| `rwh_sites.csv` | 25 sites, per-criterion score **and** weighted contribution, raw values, provenance header |
| `rwh_sites.geojson` | Same attributes as points, EPSG:4326 |
| `rwh_suitability.tif` | float32, −9999 nodata, provenance in GeoTIFF tags |
| `rwh_suitability_classified.tif` | uint8 1/2/3, 0 = outside district |
| `rwh_suitability_map.png` | Static report map: classes, rivers, boundary, numbered sites |

Weights, consistency ratio, classification thresholds and date are embedded in
**every** artefact — a CSV without its weights is not reproducible.

### E. New file: `sensitivity.py`

One-way analysis: each weight scaled by (1 ± delta) with the rest rescaled to
keep the sum at 1, then re-scored. Sites are matched between runs **by position**
(2 km tolerance, well inside the 5 km minimum separation) because candidates are
extracted independently each time and coordinates shift slightly.

Baseline result at ±20%:

> Varying each AHP weight by ±20% retains **90% of the top-10 sites on average
> (70% worst case)**, with a maximum rank shift of **3**. The result is most
> sensitive to **drainage** (mean 1.66 pp change in highly-suitable area).

Notable: drainage carries only 0.093 of the weight but moves the classified area
most, because drainage density has the highest spatial variance of the six
criteria. Rainfall, despite carrying 0.428, moves it least in the + direction.

This is the direct answer to the "subjective AHP weighting" gap on slide 14.

### F. App

New sidebar section (scenario picker, rationale caption, matrix editor, live CR,
live weights); Export row with four download buttons; Sensitivity panel with a
±10/20/30% selector, headline metrics, per-run table and an influence ranking.

### Verification

All 10 modules compile · refactor output identical to pre-refactor · 4 scenarios
all CR < 0.10 · reciprocity enforcement verified on an edited matrix (slope 5×
rainfall → CR 0.0969, correctly still under the threshold) · all 5 artefacts
produced for a non-baseline scenario · GeoTIFF round-trips through
`tools/inspect.py` with tags intact · sensitivity 0.4–1.6 s · Streamlit starts.

---

## 2026-08-08 (a) — Fixed tied candidate sites; environment rebuilt

### A. Tied sites — the ranking and comparison panel were meaningless

**Reported from the running app:** every top site showed a score of 1.000 with
100% on all six criteria, so the ranking conveyed nothing and the comparison
panel showed no difference between any two sites.

**Cause.** Every criterion had a *flat top*. Slope scored 1.00 for anything
under 1°; drainage density 1.00 above 0.40 km/km²; rainfall 1.00 for the wettest
quintile — 20% of the district; settlement proximity 1.00 across a 4 km-wide
band; soil and LULC 1.00 for their best class. Any pixel landing in the best
band of all six scored exactly 1.000, and **973 pixels did.**

**Fix.** Flat tops replaced with linear interpolation between the same
physically justified anchors:

| Criterion | Before | After |
|---|---|---|
| Slope | 6 step classes | ramp, 0°=1.00 → 3°=0.85 → 10°=0.42 → 25°+=0.05 |
| Drainage density | 5 step classes | ramp, 0.00=0.10 → 0.40=0.88 → 0.90=1.00 |
| Rainfall | 5 quintile classes | continuous percentile rank, 0.20 → 1.00 |
| Settlement proximity | flat 1–5 km plateau | gentle peak, 1.00 at 3 km, ≥0.97 across 1–5 km |

Soil and LULC remain categorical — correctly, since class membership is
genuinely discrete.

Reproducibility and transferability are unaffected: a given slope still maps to
a fixed score independent of the data range, and the anchors are still the
documented class breakpoints.

**Result:**

| Measure | Before | After |
|---|---|---|
| Distinct suitability scores | 47,495 | **108,229** |
| Pixels sharing the maximum score | 973 | **1** |
| Distinct scores among the top 25 sites | 8 | **22** |

The comparison panel now discriminates — e.g. site #1 vs #2: rainfall 98.8% vs
99.5%, slope 98.9% vs 97.7%, drainage 95.7% vs 88.2%, settlement 88.8% vs 99.5%.

### B. Stale caption in the app (introduced 2026-08-04)

The statistics panel still read *"Classes are the 33rd/67th percentile split"*
after classification had been switched to fixed thresholds. It now renders the
actual thresholds from `criteria.SUITABILITY_THRESHOLDS`, so it cannot drift
again.

### C. Result change

| Class | Before | After |
|---|---|---|
| High (≥ 0.85) | 25.6% — 2,922 km² | **18.5% — 2,113 km²** |
| Medium (0.65–0.85) | 45.0% — 5,134 km² | 54.8% — 6,253 km² |
| Low (< 0.65) | 29.4% — 3,357 km² | 26.7% — 3,047 km² |

The High share fell because ramps score lower than a step class that awarded
1.00 across a whole band; peak score is now 0.984 rather than 1.000. Thresholds
were **not** retuned — 18.5% is the honest consequence of continuous scoring,
and it sits at the bottom of the 19–34% range reported in the reviewed
literature (one study reports 18.85%).

### D. Virtual environment rebuilt

`rwh_gis_assistant/venv` had missing compiled extensions across **seven**
packages — rasterio, pillow, pandas, shapely, pyproj, fiona, and geopandas via
pandas — each failing as `ModuleNotFoundError: <pkg>._something`. Patching
individually was abandoned and the environment was recreated from
`requirements.txt`. It is now the canonical environment and matches the README;
the outer `../venv` is redundant and can be deleted.

Two real defects surfaced by this:

- **`matplotlib` was missing from `requirements.txt`** — installed ad hoc when
  the derived-map figures were built, so a fresh install would have crashed in
  `derived_maps.py`. Added.
- **rasterio 1.5.0 appears to be the culprit** for the original breakage; the
  working environment had 1.4.4. Pinned `rasterio>=1.3.0,<1.5.0` with an
  explanatory note in `requirements.txt`.

### Verification

13/13 imports clean · all modules compile · pipeline `ok` in ~1.5 s · 6 criteria ·
25 sites with 22 distinct scores · map renders · `derived_maps.py` writes its 4
GeoTIFFs and figure · Streamlit starts.

---

## 2026-08-04 (b) — Drainage density replaces drainage distance; runoff maps added

Two changes, both driven by re-checking the drainage logic against what the
project documentation actually specifies.

### A. Drainage criterion corrected: density, not distance

**The code did not match the documented methodology.** The criteria slide names
*drainage density* ("indicates runoff concentration; helps locate collection
points"), the data slide describes summarising river length in a grid and
converting to length per unit area, and references [5]–[12] all cite drainage
density. The implementation scored **distance to the nearest river** — a
siting-convenience measure, not density. The slides were themselves
inconsistent: the data slide described density, the implemented-methodology
slide described a chamfer distance transform.

Now computed as true drainage density:

1. River lines densified into ~100 m segments.
2. Each segment's length accumulated into the cell containing its midpoint,
   measured in true km via local degree-to-km scaling. Verified: 2,765.6 km
   binned against 2,767.7 km of input geometry (0.08% loss).
3. Circular moving window, radius **2.5 km** (≈20 km²), giving km/km².

District-wide density **0.242 km/km²** (2,766 km of channel over 11,414 km²),
local range 0.00–0.85. Scored as a benefit criterion on five fixed class
breaks giving district shares 30.4 / 16.9 / 17.9 / 14.1 / 20.7%.

The AHP matrix is untouched — the criterion is still called `drainage`, so
weights stay at rainfall 0.428 / slope 0.225 / soil 0.154 / drainage 0.093 /
LULC 0.060 / population 0.040 and **CR remains 0.0235**.

The candidate tie-break now uses drainage density (percentile rank) in place of
river distance, and per-site explainability reports `drainage_density`.

⚠ The class breaks are calibrated to a HydroRIVERS network, which is thresholded
to larger channels and therefore an order of magnitude below the 0.5–2.0 km/km²
bands used in studies working from DEM-extracted streams. Re-deriving the
network from `dem.tif` would require recalibrating the breaks — preserve the
class shares, not the numbers.

### B. New file: `derived_maps.py` — runoff and drainage surfaces

Produces four GeoTIFFs and a four-panel figure (`outputs/derived_hydrology.png`):
drainage density, SCS Curve Number, runoff depth, runoff coefficient.

Curve Number from IGBP land cover × hydrologic soil group (Sand → A, Silt Loam →
B, Sandy Clay Loam → C, Silt Clay Loam → D), AMC II, good condition, TR-55
analogues. District mean CN **70.5**, range 30–100.

**Runoff is computed for a 100 mm design storm, not the annual total.** SCS-CN
is an event model, and feeding it 1,493 mm/yr flattens the map completely:

| Land cover | CN | Runoff coefficient at 1,493 mm | at 100 mm |
|---|---|---|---|
| Forest | 55 | 0.85 | 0.13 |
| Cropland | 78 | 0.94 | — |
| Built-up | 85 | 0.96 | 0.61 |

Every class collapses to 0.85–0.96 at the annual total — the same failure mode
as the min–max normalisation removed in Sprint 1. At the design storm the
district mean runoff is 35.4 mm and the mean coefficient 0.354. A defensible
*annual* runoff needs the model run per month on monthly CHIRPS rasters and
summed; that download is not currently held.

**Runoff is deliberately not an AHP criterion.** Curve Number is a function of
LULC and soil, and runoff additionally of rainfall — all three are already
weighted criteria, so adding runoff would silently double-weight them. If it
must be weighted, the clean form is runoff *replacing* rainfall.

### Result change

| Class | Before (drainage distance) | After (drainage density) |
|---|---|---|
| High (≥ 0.85) | 33.3% — 3,796 km² | **25.6% — 2,922 km²** |
| Medium (0.65–0.85) | 43.8% — 4,994 km² | 45.0% — 5,134 km² |
| Low (< 0.65) | 23.0% — 2,623 km² | 29.4% — 3,357 km² |

Density discriminates more finely than distance did: pixels tied at the maximum
score fell from 3,024 to **973**. All 25 sites still scored on all six criteria;
runtime 1.3 s. 25.6% remains inside the 19–34% "suitable" range in the reviewed
literature.

### Documented limitation: pre-cropped inputs at the district edge

Investigated after the question of whether the already-clipped layers matter.
They do, for the distance- and density-based criteria, which see only
in-district features:

| Effect | Extent |
|---|---|
| District within 5 km of the border | 24.4% |
| Pixels where an out-of-district settlement could be nearer | 25.8% |
| Pixels where an out-of-district river could be nearer | 4.9% |
| Candidate sites in the exposed zone | 8 of 25, including rank #1 |

Bounded: settlement 0.040 + drainage 0.093 = 0.133 maximum score swing, so the
map and class areas barely move — the effect is on candidate *ranking*.
**Fix (user action):** re-export `rivers.geojson`, then `population.tif`, then
the remaining rasters clipped to a **20 km buffered** boundary rather than the
outline. No code change needed. Recorded in docs/METHODOLOGY.md §12.

### Dependency

- **matplotlib added** for the derived-map figures; installed into `../venv`.

### Verification

- All modules compile; pipeline `ok` in 1.3 s; Streamlit app starts.
- `derived_maps.py` writes 4 GeoTIFFs + PNG; figure inspected — drainage density
  follows the dendritic network, Curve Number correctly separates the low-CN
  Tadoba forest in the south-west from high-CN cropland and the urban core.

### Slides affected

- **Slide 18** — drainage density wording is correct; no change needed.
- **Slide 26** — matches the density method now implemented; no change needed.
- **Slide 28 ("Our Implemented Methodology")** — still says "distance-to-river
  computed using chamfer distance transform". **Must be updated** to drainage
  density on a 2.5 km moving window.
- Consider adding the derived-hydrology figure as a new slide.

---

## 2026-08-04 (a) — Real rainfall input: 11-year CHIRPS v3.0 mean annual surface

Closes the highest-priority open item from the Sprint 1 entry below. The
rainfall criterion carries the largest AHP weight (0.428), so until now every
suitability result was provisional.

### New file: `build_rainfall.py`

Builds `data/rainfall.tif` from CHIRPS downloads instead of hand-assembling it
in QGIS, so the layer is reproducible and its provenance is recorded in code.

- Handles both download shapes: annual files (`chirps-v3.0.2014.tif`) averaged
  directly, or monthly files (`…2014.01.tif`) summed per year and then averaged.
  Incomplete years are skipped with a warning.
- Reads **only the district window** from each global raster, so the eleven
  7200 × 2400 px global files never need to be loaded whole or clipped by hand.
- Reads a **0.20° margin** around the district, so the analysis grid has real
  values right to the boundary.
- Handles CHIRPS's undeclared nodata: the files use −9999 as fill but do **not**
  declare it in the GeoTIFF header, so rasterio will not mask it automatically.
  Left unhandled this would have destroyed the average.
- Sanity-checks the district mean against the ≈1245 mm long-term normal and
  fails loudly if the units look wrong.
- Writes provenance into the output's GeoTIFF tags (source, year range,
  aggregation, units, district mean, generation date).
- Backs up any existing `rainfall.tif` to `rainfall_previous.tif` rather than
  overwriting silently.

### Data change

| | Before | After |
|---|---|---|
| Source | single month of CHIRPS, test placeholder | CHIRPS v3.0 annual, 2014–2024 (11 years) |
| Units | mm/day for one month (≈144 mm total) | mm/year |
| District mean | — | 1,493 mm/yr |
| District range | — | 1,184 – 1,713 mm/yr |
| Rainfall gap-fill needed | 5.7% of district pixels | **none** — the 0.20° margin covers it |

`RAINFALL_SOURCE_NOTE` set to `None`, which clears the provisional warning
banner in the app and the `⚠️ PROVISIONAL` line in the analysis notes.

### Finding worth reporting

The 11-year mean of **1,493 mm is ~20% above the ≈1245 mm long-term normal**
cited on the project's own geographic-statistics slide. This is not a unit
error — 2014, 2015 and 2017 sit at 1,220–1,260 mm, in line with the normal,
while every other year runs 1,425–1,930 mm (interannual sd 198 mm). The recent
decade is genuinely wetter than the older baseline. Stating this pre-empts the
obvious question about why the two figures disagree.

### Result change

| Class | Before (placeholder) | After (11-year mean) |
|---|---|---|
| High (≥ 0.85) | 30.7% — 3,505 km² | **33.3% — 3,796 km²** |
| Medium (0.65–0.85) | 46.2% — 5,275 km² | 43.8% — 4,994 km² |
| Low (< 0.65) | 23.1% — 2,633 km² | 23.0% — 2,623 km² |

All 25 candidate sites are still scored on all six criteria; the top sites
shifted position as expected given the changed rainfall field. Runtime ~1.4 s.
33.3% remains inside the 19–34% "suitable" range reported by the comparable
GIS-MCDA studies in the literature review.

### Still to note

- Rainfall stays on **quantile** classification. Now that the unit is confirmed,
  fixed mm bands are a viable alternative that would transfer to other districts
  — a worthwhile Sprint 2 comparison. See docs/METHODOLOGY.md §5.
- The eleven CHIRPS global rasters (~264 MB) sit in `data/` and are already
  covered by `.gitignore`. They can be archived outside the project once the
  built surface is accepted; `build_rainfall.py` reproduces the output from them
  at any time.
- `data/rainfall_previous.tif` is the retired single-month placeholder — safe to
  delete.
- The **presentation slides still need the updates listed in §M below**, plus
  slide 22's rainfall description (now CHIRPS v3.0 annual 2014–2024, not
  2024+2025 monthly) and slide 17's rainfall figure.

---

## 2026-07-29 — Sprint 1: methodological correctness + repository cleanup

Largest change since the AHP pipeline was first built. Two independent things
happened: the criterion scoring was rewritten to be defensible, and the
natural-language layer was removed from the project scope.

### Summary of impact

| Measure | Before | After |
|---|---|---|
| Slope pixels scoring > 0.90 | 97.4% (criterion nearly constant) | spread across 6 classes |
| Population pixels scoring > 0.90 | 97.7% (criterion nearly constant) | spread by distance band |
| Soil / LULC scoring | min–max on class codes (meaningless) | explicit class lookups |
| Top-25 sites scored on all 6 criteria | 12 of 25 | 25 of 25 |
| Analysed area vs official 11,443 km² | not measured (unmasked bounding box) | 11,412 km² — 99.7% |
| Reported class split | 32.9 / 34.0 / 33.1 (a percentile artefact) | 30.7 / 46.2 / 23.1 (fixed thresholds) |
| Runtime | ~1.5 s | ~1.6 s |
| Python source files | 10 (4 of them dead) | 5 |

---

### A. Criterion scoring rewritten — **new file `criteria.py`**

Every criterion is now reclassified with explicit, documented breakpoints
instead of a min–max rescale of the observed raster values. Full justification
for every number is in [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

**Why this was necessary.** Measured on the project's own data, min–max
normalisation left slope at a mean of 0.98 with 97.4% of pixels above 0.90, and
population at a mean of 0.98 with 97.7% above 0.90 — both effectively constant,
contributing nothing to site discrimination despite slope holding 22.5% of the
AHP weight. The categorical layers were scored by the numeric value of their
class code, so IGBP class 17 (Water) scored 1.00 and class 13 (Urban) scored
0.75, while deciduous forest scored 0.00. About 48% of the total AHP weight was
either flat or semantically inverted.

Added to `criteria.py`:

- `SLOPE_CLASS_BREAKS_DEG` — six classes from ≤1° (1.00) to >15° (0.05).
- `SOIL_TEXTURE_SCORES` — explicit lookup for codes {1, 4, 6, 7}, ranked by
  infiltration/retention balance for recharge, plus `SOIL_TEXTURE_LABELS`.
- `LULC_SCORES` — all 17 IGBP classes, Cropland highest, Water and Urban
  effectively excluded, plus `LULC_LABELS`.
- `RAINFALL_QUANTILE_*` — quintile classification within the district.
- `moderate_optimal()` — one trapezoidal helper shared by both distance
  criteria, replacing the old mean ± 3σ "moderate" branch.
- `score_continuous_breaks()`, `score_categorical()`, `score_quantiles()`,
  `score_drainage_distance()`, `score_settlement_distance()`.
- `CRITERION_METHOD` — human-readable description of each scoring method,
  surfaced in the app.

### B. Population criterion redefined as settlement proximity

The code scored population as `lower_better`, which contradicted the project's
own stated rationale ("where water is actually needed"). Reworked to match the
actual design intent — *a site in suitable terrain but set back from the
settlement it serves*:

- pixels with density ≥ 400 people/km² form a settlement mask (6.6% of the
  district; district mean density is 193);
- distance from that mask is computed in km;
- scored moderate-optimal, peaking at 1–5 km.

Justification for the report: *close enough that harvested water serves real
demand, far enough to avoid built-up impervious land, land-acquisition cost and
greywater contamination.*

The old `'moderate'` normalisation branch centred on the mean and scaled by 3σ,
which is meaningless on a distribution running 1.9 – 9101 people/km².

### C. Drainage criterion converted to kilometres

Previously scored distance-to-river in **pixel units** through the same mean ± 3σ
path. Now an exact distance in km, scored moderate-optimal with a 0.3–2.0 km
peak band.

### D. District boundary masking

The analysis grid is the boundary's bounding box, and nothing previously
restricted results to the district itself. The boundary polygon is now
rasterised onto the analysis grid, every criterion is clipped to it, and the
suitability raster is masked — so no candidate site can fall outside Chandrapur
and the percentile/area statistics are computed over district pixels only.

### E. Gap filling at the district rim

The source layers stop at slightly different places near the boundary (CHIRPS
rainfall reached only 94.3% of boundary pixels). Gaps inside the district are
now filled from the nearest valid pixel: rainfall 5.7%, soil 2.2%, population
2.0%, slope 1.1%, LULC 0.1%.

Result: analysed area 11,412 km² against the official 11,443 km² — a 99.7%
match, which also validates the boundary mask and the pixel-area calculation.

### F. Weighted overlay — per-pixel renormalisation + coverage gate

- Weights are renormalised per pixel over the criteria that actually have data
  there, so the output stays on a true 0–1 scale instead of being depressed
  wherever a layer is missing.
- **New:** a pixel is scored only if at least 80% of the total AHP weight has
  data there (`MIN_WEIGHT_COVERAGE`). Without this, edge pixels holding only
  rainfall and LULC could score 1.000 from two criteria and outrank genuine
  sites evaluated on all six — 13 of the original top 25 sites were exactly this
  artefact. All 25 are now scored on all six criteria.

### G. Classification switched from percentiles to fixed thresholds

The 33rd/67th percentile split is self-fulfilling — it reports ≈33% of the
district as highly suitable whatever the scores are, which is why the earlier
run returned 32.9 / 34.0 / 33.1. Replaced with fixed thresholds on the 0–1
score: High ≥ 0.85, Medium 0.65–0.85, Low < 0.65.

New result: **High 30.7% (3,505 km²), Medium 46.2% (5,275 km²), Low 23.1%
(2,633 km²)** — comparable to the 19–34% "suitable" shares in the reviewed
literature. `CLASSIFICATION_MODE = "percentile"` restores the old behaviour for
comparison.

### H. Area statistics

New `_area_statistics()` computes km² and share per class, with pixel area
calculated per raster row so the latitude-dependent shrinking of longitude
degrees is handled correctly. Surfaced as metric tiles in the app — this is the
project's headline result and it did not previously exist.

### I. Candidate ranking tie-break

Discrete reclassification means 2,727 pixels share the maximum score of 1.000,
so ordering within that plateau was arbitrary. Added a continuous tie-break
score (gentler slope, higher rainfall percentile, distances nearer the centre of
each optimal band), applied at weight 1e-3 so it only separates exact ties and
can never reorder genuinely different scores. The published map and reported
per-site scores stay discrete.

### J. Per-site explainability extended

Candidate details now also carry the **raw measured values** behind the scores —
slope in degrees, soil class name, land-cover class name, distance to nearest
settlement in km — shown on the site cards. Example, current rank 1: 0.46°
slope, Silt Loam, Cropland, 2.83 km from a settlement.

### K. `ahp.py` simplified

- Removed `_adjust_weights()` and the `preferences` argument. They existed only
  for the natural-language layer, were never fed by the app, and contained a
  latent bug (the renormalisation was assigned to a local variable, so adjusted
  weights would not have summed to 1).
- Replaced the hard-coded `RI = 1.24` with the full Saaty random-index table.
- Documented the priority-vector method as the normalised geometric mean of the
  raw matrix rows. *(Note: the previous implementation column-normalised first
  and then took row geometric means. That is mathematically equivalent after
  renormalisation — verified identical to 4 decimal places — so weights did not
  change. It is now written the way the methodology slide describes it.)*
- Added `is_consistent()`.

Weights are unchanged: rainfall 0.428, slope 0.225, soil 0.154, drainage 0.093,
LULC 0.060, population 0.040. **CR = 0.0235**, well under the 0.10 threshold.

### L. Application UI

- New **Suitability Zone Statistics** panel — district area analysed plus area
  and share per class.
- New **"How each criterion is scored"** expander listing the method per
  criterion in AHP priority order.
- Site cards now show the raw measured values.
- Consistency Ratio now displayed to 4 dp with an explicit accept/reject verdict.
- `run_ahp_analysis({}, data_dir)` → `run_ahp_analysis(data_dir)`.

---

### M. Scope change: natural-language query layer removed

Decided that an NLP layer was not necessary for this project. Deleted
`query_parser.py` and `utils/query_parser.py` — they were already dead code, as
`app.py` called `run_ahp_analysis({}, data_dir)` with permanently empty
preferences and never imported the parser.

> **⚠ Presentation slides still need updating to match.** Outstanding:
> - **Slide 5** — all four papers are LLM/GIS-agent work ([1]–[4]) and the
>   "Relation to This Topic" column claims they ground a query-to-action layer
>   that no longer exists. Replace with four more GIS-MCDA/RWH papers.
> - **Slide 14** — the gap "No real-time/IoT systems" is cited to [1], [2], [3].
>   Re-cite or cut.
> - **Slide 15** — "NLP Query Module Development" spans Apr–Jul on the Gantt.
>   Replace with *Criterion Reclassification & Normalisation Design*, then
>   *Sensitivity Analysis*, then *Validation (AUC)*.
> - Slides 10 and 27–34 never mention NLP and stand as-is.
> - Slides 18 and 22 need the population-direction and rainfall-unit
>   corrections recorded in docs/METHODOLOGY.md §5 and §7.

### N. Repository cleanup

**Deleted — dead code:**

| File | Reason |
|---|---|
| `ui.py` | Byte-for-byte copy of `app.py` apart from the docstring and four comment lines; `app.py` is the entry point |
| `map_renderer.py` (root) | Superseded duplicate — an older 290-line version of the 345-line `utils/map_renderer.py` that `app.py` actually imports |
| `query_parser.py`, `utils/query_parser.py` | NLP layer, removed from scope; never imported by the app |
| `gis_engine.py`, `utils/gis_engine.py` | Superseded by `gis_analysis.py`; only referenced by the two dead scripts below |
| `test_queries.py` | Only existed to import `parse_query` and `gis_engine.run_analysis` |
| `debug_data.py` | Only existed to import `gis_engine.run_analysis` |
| `.env`, `.env.example` | OpenAI key template for the removed NLP layer. **The `.env` contained an empty `OPENAI_API_KEY=` — no real credential was ever present, so nothing was exposed.** |
| `__pycache__/`, `utils/__pycache__/` | Build artefacts |

**Added `.gitignore`** covering `.env`, `venv/`, `__pycache__/`, editor
directories, and the large `data/` rasters (with `boundary.geojson` and
`rivers.geojson` kept). Written *before* any `git init` so that no secret or
50 MB raster can enter the first commit.

**`requirements.txt`** — removed the commented `openai` / `python-dotenv`
entries; added `scipy>=1.11.0`.

**`README.md`** — rewritten: removed the "+ LLM" framing and the NLP
architecture section, documented the current pipeline, the criteria/weights
table, the current result, and the Sprint 2/3 roadmap.

---

### O. Coarse-rainfall edge overshoot — resolved by the boundary mask

Recorded because it was an open problem before today. CHIRPS pixels are 5.28 km
across (27.9 km² each), so clipping in QGIS follows the pixel grid rather than
the district outline and leaves blocky edges extending past Chandrapur. On the
analysis grid, 4,352 rainfall pixels overshoot the boundary.

The district mask added in §D discards all of them. Verified: the final
suitability raster has **0 pixels outside the boundary and 0 unscored pixels
inside**. The coarse source resolution now affects only the appearance of a
standalone QGIS figure, not the analysis.

For a clean-edged rainfall figure for the report, resample before clipping —
Warp (Reproject) with bilinear resampling to 250 m, then Clip Raster by Mask
Layer with "match the extent of the clipped raster to the extent of the mask
layer". This is cosmetic only; resampling adds no information.

---

### Dependency and environment notes

- **SciPy added.** Used for the exact Euclidean distance transform behind both
  distance criteria and for nearest-value gap filling. Installed into
  `../venv` (the working environment) during this session.
  `gis_analysis.py` falls back to the existing chamfer approximation for
  distances if SciPy is unavailable; gap filling simply does not run, and the
  80% coverage gate handles the rim instead.
- ⚠ **Two virtual environments exist.** `rwh_gis_assistant/venv` has a broken
  Rasterio install (`ModuleNotFoundError: rasterio._base`); the outer
  `../venv` works and is what this session used. Worth deleting the broken one
  to avoid confusion.

### Verification performed

- All modules byte-compile.
- Full pipeline runs end-to-end in ~1.6 s, status `ok`, all six criteria loaded.
- Suitability raster: 123,555 district pixels, range 0.288 – 1.000, mean 0.770.
- AHP weights sum to 1.000000; CR = 0.0235; consistency check passes.
- Folium map renders (1.1 MB HTML) with legend and per-site popups intact.
- 25 candidate sites extracted, all scored on all six criteria.

### Known open items

1. **Rainfall input is provisional — highest-priority data task.**
   `data/rainfall.tif` is a **single month** of CHIRPS data used to test the
   pipeline, not the mean annual surface. Rainfall carries the largest AHP
   weight (0.428), so every result above is provisional until it is replaced.
   Swapping it in needs no code change: drop the new raster in as
   `data/rainfall.tif` and clear `RAINFALL_SOURCE_NOTE` in `criteria.py`.
   Quantile scoring keeps the placeholder usable because it depends only on the
   ordering of values, not their unit — but that assumes the district's spatial
   rainfall pattern is stable between one month and the annual total, which
   should be verified by Spearman rank correlation once the monthly rasters are
   available. A warning banner now appears in the app so the current map is
   never mistaken for a final result.
2. **Soil class coding unverified** — the project legend differs from the
   standard SoilGrids TEXMHT coding. Confirm against the exported file.
3. **Settlement threshold (400 people/km²) and 1–5 km band** are reasoned
   starting values; review with the project guide and state as assumptions.
4. No exports, no editable weights, no sensitivity analysis, no validation —
   Sprints 2 and 3.
