# Validation Protocol

**How to actually validate the suitability map.** Written 25 September 2026.

The code is finished. `validation.py` implements everything needed and returns
`missing_data` because one file does not exist. This document covers how to
produce that file defensibly, the mistakes that would make the result
meaningless, and what to run afterwards.

---

## 1. What the harness already does

| Function | What it answers |
|---|---|
| `validate()` | Do known structures score higher than random locations? → **ROC-AUC** |
| `candidate_proximity()` | Do our 25 proposed sites land near known structures? → Mann-Whitney probability |
| `validate_all_algorithms()` | Which of the four algorithms scores known structures best? → per-algorithm AUC ranking |

**Input contract** — this is all it needs:

- File at `data/rwh_structures.geojson`
- **Point** geometries (polygons are ignored — take centroids first)
- Any CRS, provided the file declares one; it is reprojected to EPSG:4326
- Optional `type` and `year` attributes are carried through
- Nothing else is required

**Defaults:** 5 background points per positive, 1 km exclusion buffer around
positives, random seed 42.

**What ROC-AUC means here.** The probability that a randomly chosen real
structure scores higher on the map than a randomly chosen background location.
1.0 = perfect separation, 0.5 = no better than chance, below 0.5 = inverted.

---

## 2. The only blocker: 150–300 verified structure locations

Three routes, cheapest first.

### Route A — Verify the OSM candidates you already have ⭐ start here

`data/osm_water_candidates_UNVERIFIED.geojson` holds 158 OpenStreetMap points
inside the district: **99 tagged `reservoir`, 48 `pond`, 11 `dam`**. The file
already has empty `verified` and `notes` columns — it was built as a worksheet.

**Why this is the fastest path:** 158 points to inspect visually is perhaps 3–5
hours, versus days of de-novo digitising. It converts a dataset that is
currently invalid into one that may be usable.

**Procedure:**

1. Open the file in QGIS over a high-resolution imagery basemap (Esri World
   Imagery, or Google Satellite via QuickMapServices).
2. For each point, classify it into one of:
   - **Include** — a constructed water-harvesting structure: farm pond,
     percolation tank, check dam, nala bund, small earthen embankment.
   - **Exclude** — natural water body, quarry or mine pit, irrigation canal,
     major dam reservoir, river pool, sewage or industrial pond.
   - **Uncertain** — cannot tell. Record it, exclude it from the primary run,
     and report how many there were.
3. Write `yes` / `no` / `unsure` into `verified`, and the structure type into
   `notes`.
4. Export only the `yes` rows as `data/rwh_structures.geojson`.

⚠ **Realistic expectation.** Of 158 points, 99 are tagged `reservoir` — in a
district with significant mining and irrigation infrastructure, many of these
will be neither small nor purpose-built for harvesting. The 48 `pond` features
are the most promising. **You may end up with 40–80 usable points, not 150.**
That is still worth running; see §5 on sample size.

### Route B — Government asset records

Named in the project docs as candidate sources. Higher quality if obtainable,
but availability is not something I can verify from here.

- **MGNREGS asset records** — water conservation assets created under the
  employment guarantee scheme are geotagged as part of the asset-tagging
  initiative. Attributes typically include asset type and year, which would give
  you the `type` and `year` fields.
- **Jalyukt Shivar Abhiyan** — Maharashtra's water conservation programme;
  district-level records of structures.
- **District Water Conservation Office / GSDA** (Groundwater Surveys and
  Development Agency, Maharashtra) — may hold inventories.

⚠ I cannot confirm current portal URLs, data formats or access conditions.
Treat this route as "worth a week of enquiry", not a guaranteed dataset. If
records come as a table of village names rather than coordinates, you will need
to geocode, which introduces its own positional error — record that if so.

### Route C — Blind digitising from imagery

De-novo identification of structures from satellite imagery. Highest effort,
most control over sampling design.

Only do this if Routes A and B are insufficient, and if you do, follow the
stratified protocol in §3.2 — otherwise it is the easiest route to a worthless
result.

---

## 3. Five ways to invalidate your own validation

This section matters more than the routes above. A validation exercise done
carelessly produces a number that is worse than no number, because it looks
authoritative.

### 3.1 Confirmation bias — the fatal one

**If whoever collects the structures can see the suitability map, the validation
is void.** You will find structures where the model says High, because that is
where you will look hardest.

**Fix:** the person digitising must not have seen the suitability output. In
practice, on a four-person team: whoever did the least work on `criteria.py` and
the weights does the digitising, with the map closed. Record in the paper that
collection was blind to the model output. If it wasn't, say that instead — an
acknowledged bias is survivable, a hidden one is not.

### 3.2 Spatially biased sampling

Structures near roads and villages are easier to find. So are large ones. If
your sample concentrates there, your AUC measures detectability, not
suitability.

**Fix:** impose a spatial grid — say 10 × 10 km blocks across the district — and
inspect every block, recording a similar number of candidate locations in each,
including blocks where you find nothing. Zero-finds are data: they tell you the
area genuinely has no structures rather than that you stopped looking.

### 3.3 Detectability bias by structure size

Large reservoirs are unmistakable from space. Small recharge pits, gabion
structures and contour trenches are not. Imagery-derived samples therefore
skew large.

**This matters because large and small structures are sited by different
logic.** A major reservoir needs a big catchment and a constricted valley —
criteria your model does not use. A farm pond is sited much more like the model
assumes.

**Fix:** record structure size or type, and report AUC separately for small
structures if you have enough of them. If your sample is dominated by large
reservoirs, say explicitly that the validation applies to large impoundments and
that small-structure validation remains open.

### 3.4 Circularity — the one a good reviewer will find

If the engineers who built the existing structures selected sites using slope,
drainage position and soil — the same variables your model uses — then a high
AUC shows **your model reproduces established siting practice.** It does not
independently show the sites are hydrologically good.

**This is not a reason to skip validation.** Agreement with expert practice is
the standard claim in this literature and it is a legitimate one. But it must be
worded correctly:

> A high AUC indicates the model identifies the same terrain that practitioners
> have historically selected. It does not independently establish recharge
> performance, which would require monitored groundwater response at the
> structures.

Write that sentence into the paper regardless of what AUC you get.

### 3.5 Presence-only background contamination

There are no true negatives. The harness draws random in-district background
points and assumes they are non-structure locations. Some will contain
unmapped structures, which biases AUC **downward**.

**Fix:** none available, it is inherent to presence-only design. State it as a
limitation and note the direction of the bias — it makes your AUC conservative,
which is the favourable direction.

---

## 4. Running it

Once `data/rwh_structures.geojson` exists:

```bash
python validation.py
```

That produces, in one run:

- AUC with counts of structures scored and structures falling outside the grid
- Mean suitability at structures vs at background points
- Percentage of structures falling in High, and in High-or-Medium
- The candidate-proximity comparison (are your 25 sites near real ones?)
- A per-algorithm AUC ranking — which finally answers *which method is best*

Useful flag if the file lives elsewhere:

```bash
python validation.py --structures path/to/file.geojson
python validation.py --background-multiplier 10   # more background points
```

**Before the real run, sanity-check the plumbing** on a synthetic file: take 50
random in-district points, save as a GeoJSON, run the harness. AUC should come
out near 0.5. If it doesn't, something is wrong with coordinates or CRS, not
with your model.

---

## 5. Interpreting the result

### Sample size

With ~60 positives and 5× background, the AUC standard error is roughly ±0.06;
with 150 positives, roughly ±0.04. **Report a confidence interval, not a bare
number.** The harness does not currently compute one — see §7.

Anything below about 30 positives is too thin to report as a headline result.
Report it as preliminary, or not at all.

### What the numbers would mean

| AUC | Reading |
|---|---|
| > 0.75 | Strong agreement with existing siting practice. Reportable as the headline result. |
| 0.65 – 0.75 | Moderate agreement. Reportable with the circularity caveat prominent. |
| 0.55 – 0.65 | Weak. Report honestly, and investigate which criterion drags. |
| ≈ 0.50 | No better than chance. **Do not bury this.** |
| < 0.50 | Inverted — the model prefers terrain practitioners avoid. |

### If the result is poor — this is not a disaster

A low AUC is a finding, and the project is unusually well set up to diagnose it.
Run the per-criterion breakdown: sample each criterion's score surface at the
structure locations and compute AUC per criterion. That localises the problem.

**You already have a preview of this.** The OSM diagnostic — not a validation,
but informative — gave an overall 0.482 with settlement proximity alone at
0.379, while every other criterion sat at or above chance. If real data
reproduces that pattern, the finding is that the 1–5 km settlement band is wrong:
real structures sit closer to villages than the model assumes. That is a
publishable, specific, actionable result, and it is more interesting than a bland
0.8.

**Do not retune the model to improve AUC and then report that AUC.** That is
fitting to the test set. If you adjust the settlement band in response, you must
either report both the pre-adjustment and post-adjustment figures, or hold out
a portion of the structures and validate the adjusted model only on the held-out
set.

---

## 6. Validation that needs no structure inventory

If the inventory cannot be assembled in time, these remain available and are
genuinely publishable.

**Expert assessment.** Show the classified map and the 25 candidate sites to the
district water conservation office or your guide's contacts, and ask them to
rate each site as plausible / implausible / unsure, blind to the ranking. Report
agreement rate. Semi-quantitative, but it is external evidence and it is more
than most comparable student work has.

**Field verification of a sample.** Visit 8–12 of the 25 candidate sites.
Record: actual slope, evidence of runoff concentration, current land use,
accessibility, distance to habitation, whether a structure already exists there.
Compare against what the model asserted. This does not give an AUC, but "we
visited 10 sites and the model's slope and land-cover assertions held at 9 of
them" is real verification of the input data, and it is honest.

**Cross-validation against an independent published map.** If any government
groundwater-potential or watershed-priority map exists for Chandrapur, compare
class agreement. Weaker evidence — you are comparing two models — but it is a
recognised approach and it needs no fieldwork.

**Spatial block cross-validation** *(once you have any structures at all)*.
Split the district into blocks, hold out whole blocks rather than individual
points, and compute AUC per fold. This is the correct treatment for clustered
point data and it guards against the autocorrelation inflation in §3.2. Standard
in species-distribution modelling, rare in GIS-MCDA — including it would be a
methodological contribution in its own right.

---

## 7. Code that would need adding

The harness covers the core. Three additions would materially strengthen a
validation section, and none is large:

1. **Bootstrap confidence interval on AUC** — resample positives and background
   with replacement, report the 2.5th and 97.5th percentiles. ~20 lines.
2. **Per-criterion AUC breakdown** — sample each of the six score surfaces at
   the structure points and compute AUC individually. This is the diagnostic
   described in §5 and it is what turns a bad result into a finding. ~25 lines.
3. **Spatial block cross-validation** — partition the district into k blocks,
   hold each out in turn, report mean and spread of AUC across folds. ~50 lines.

Say the word and I will write them into `validation.py`. They are useful before
the data arrives, because they can be exercised against a synthetic point set.

---

## 8. Realistic assessment

Route A is achievable in a weekend and will probably yield 40–80 usable points.
That is enough for a *preliminary* validation with a wide confidence interval,
reported as such. It is not enough to claim a robust accuracy figure.

Route B could yield a proper dataset but depends on institutional access that
may take weeks and may not come through at all.

**If neither lands before submission, the current position is defensible and
already written up** — the harness exists, its mathematics is verified, the
inventory does not, and no number is claimed. The consensus analysis carries the
robustness argument in the meantime. Do not let a deadline turn into a
temptation to report the OSM 0.482 as if it were validation.
