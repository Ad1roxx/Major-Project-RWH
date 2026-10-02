# TODO / Backlog

Parked work, in priority order. Each item has enough detail to act on without
re-deriving the reasoning — the full analysis lives in
[docs/METHODOLOGY.md](docs/METHODOLOGY.md) and [CHANGELOG.md](CHANGELOG.md).

Completed work is recorded in CHANGELOG.md, not here.

---

## A. Before the report / final submission

### A1. Buffered re-export of rivers and population — *deferred 2026-08-04*

**Problem.** Drainage density and settlement proximity measure outward from each
pixel, but `rivers.geojson` and `population.tif` are clipped to the exact
district outline, so a pixel near the border cannot see a river or town just
across it.

**Measured impact:** 25.8% of district pixels could have a nearer
out-of-district settlement; 4.9% a nearer river; drainage density
under-estimated along the rim. **8 of 25 candidate sites affected, including
rank #1.** Bounded at a 0.133 score swing (settlement 0.040 + drainage 0.093),
so the suitability map and class areas barely move — it changes *which sites
rank where* near the border.

**Fix (QGIS, ~15 min):**
1. Reproject `boundary.geojson` to EPSG:32644, then Vector → Geoprocessing
   Tools → **Buffer**, distance **20000 m**.
2. Re-clip against the buffered polygon, *not* the district outline:
   - `rivers` — Vector → Geoprocessing Tools → **Clip** (HydroRIVERS Asia)
   - `population` — Raster → Extraction → **Clip Raster by Mask Layer** (WorldPop)
3. Save over `data/rivers.geojson` and `data/population.tif`, same filenames.

**Why 20 km:** the furthest any criterion looks outward is the settlement score
reaching its floor at 5 + 10 = 15 km. Beyond that nothing outside can change a
score.

**Catch:** needs the *original* unclipped downloads — `data/` holds only clipped
copies, so re-download HydroRIVERS (Asia) and WorldPop India. No code changes;
the pipeline still masks output to the true district.

**Do it before** quoting a final top-10 site list. Can wait if the report leads
with the suitability map and area statistics.

*Optional extra:* the same treatment for `slope.tif`, `soil_texture.tif` and
`lulc.tif` removes the remaining rim gap-fill (2.17% / 2.03% / 1.05% / 0.11%),
but those criteria read only the pixel under them, so accuracy is unaffected.

### A1b. Digitise known RWH structures — *the highest-leverage task*

**Blocks:** AUC validation (Sprint 3) **and** all of Sprint 4 (classifier). One
file unblocks both. Do this in the same QGIS session as A1 above.

**What it is.** A point layer of rainwater harvesting structures that
**already exist on the ground** — check dams, farm ponds, percolation tanks,
nala bunds. Not predictions; things that were actually built.

**Why.** Every number the project currently reports describes the model's own
behaviour. Nothing tests the map against reality. Sampling the suitability
surface at real structures answers "does the model agree with what engineers
actually built?" — that is validation.

**Output:** `data/rwh_structures.geojson`, point geometry, valid CRS.
Optional `type` and `year` attributes are carried into the report.

```json
{"type":"FeatureCollection","features":[
 {"type":"Feature","geometry":{"type":"Point","coordinates":[79.4521,20.1834]},
  "properties":{"type":"check dam","year":2019}}]}
```

**Route 1 — digitise from imagery (most practical).**
1. QGIS → Browser → XYZ Tiles → Google/Esri Satellite; zoom to Chandrapur.
2. Layer → Create Layer → New GeoJSON Layer; geometry **Point**, CRS
   **EPSG:4326**; add text field `type`, integer field `year`.
3. Toggle editing, use the Add Point tool, click each structure, fill `type`.
4. Work systematically — split the district into 4 blocks, one per team member,
   and follow the drainage lines from `rivers.geojson`; structures sit on them.
5. Save as `data/rwh_structures.geojson`.

**What to look for:** a straight embankment across a stream with water pooled
behind it (check dam); a small rectangular or kidney-shaped pond beside
cropland, often with visible bunds (farm pond); a larger irregular impoundment
in a valley (percolation tank). Cross-check with the seasonal difference between
imagery dates where available.

**Target 150–300 points.** 50–100 still yields a usable AUC with wider error
bars. Record the imagery date used.

**Route 2 — government records.** MGNREGS water-conservation assets are
geotagged under Geo-MGNREGA and NRSC's Bhuvan portal hosts MGNREGA asset layers
by district — the most likely source of ready-made coordinates. Jalyukt Shivar
Abhiyan records and the district Water Conservation / Minor Irrigation office
are the other leads. **Ask the guide** which office holds these. Verify
availability; do not assume.

**State as a limitation in the report:** structures exist where people *chose*
to build, which reflects land ownership, access and budgets, not only physical
suitability. Expect AUC ≈ 0.65–0.80, not 0.95. It is also presence-only data —
absence of a structure does not mean a site is unsuitable, which is why
`validation.py` samples random background points rather than treating empty
cells as negatives.

### A2. Verify the soil class coding

`SOIL_TEXTURE_SCORES` uses the legend from the project's soil slide
(1 = Sand, 4 = Silt Loam, 6 = Sandy Clay Loam, 7 = Silt Clay Loam). Standard
SoilGrids USDA texture coding (TEXMHT) numbers classes differently
(1 = clay … 12 = sand). **Check the exported file's metadata.** If the standard
coding applies, remap that one dictionary in `criteria.py` — nothing else
changes. See METHODOLOGY §3.

### A3. Review assumptions with the project guide

State these as assumptions in the report, or replace with justified values:
- **Settlement threshold 400 people/km²** and the **1–5 km optimal band**
  (METHODOLOGY §7).
- **100 mm design storm** for the runoff map — currently a plausible one-day
  monsoon event, not derived. Firm it up from an IMD one-day-maximum statistic
  or a return-period analysis for Chandrapur, then pass `--storm-mm`
  (METHODOLOGY §6a).
- **Drainage density direction** — treated as a benefit (higher = better) per
  the project's own rationale. Some recharge-focused studies use the opposite
  convention; say why yours differs (METHODOLOGY §6).

### A4. Presentation slides still out of date

Slide numbers below refer to **`docs/BTech Major Project PPT (1).pptx`** (37
slides, added 2026-08-25). The earlier 38-slide deck in `Downloads/` is
superseded — do not edit it. Numbers here were renumbered on 2026-08-25; the
previous list was written against the 38-slide deck and pointed at wrong slides.

**Factually wrong — must fix**

- **Slide 27** ("Our Implemented Methodology") — says *"distance-to-river
  computed using chamfer distance transform"*. It is now **drainage density on a
  2.5 km moving window**. ⚠ The single most wrong statement in the deck.
- **Slide 21** (Precipitation) — says *CHIRPS monthly, 2024 and 2025*. It is now
  **CHIRPS v3.0 annual, 2014–2024** (11 years) averaged to a mean-annual surface,
  1,184–1,713 mm/yr. Also claims reprojection to **EPSG:32644**; the pipeline
  works in **EPSG:4326** throughout.
- **Slide 25** (Rivers) — says drainage density was summarised on a **1 km × 1 km**
  grid. It is a **2.5 km** moving window (`criteria.DRAINAGE_DENSITY_WINDOW_KM`).
- **Slide 17** (Criteria Finalization) — population is described as *"where water
  is actually needed"*. The direction was **inverted** on 2026-07-29: it is now a
  moderate-optimal band peaking **1–5 km** from settlements above 400 persons/km².
- **Slide 35** (Project Progress, Phase 5) — lists **"Complex Query Handling"**.
  The natural-language query layer was **removed from scope** 2026-07-29. Delete
  the row; replace with *Sensitivity Analysis* and *Validation (AUC)*.
- **Slides 34–35** — Phase 2 and Phase 3 marked *Ongoing*, Phase 4 *Pending*. All
  three are complete. Only Phase 5 is genuinely outstanding, and only its
  validation half.

**Out of date rather than wrong**

- **Slide 13** (Technology Details) — no Streamlit, Folium, SciPy or pandas;
  lists *QGIS Layout Manager* as the visualisation route. The deliverable is a
  Streamlit web app with interactive Folium maps.
- **Slide 28** ("Proposed Methodology") — five of its six items are now **built**:
  AHP–TOPSIS, Fuzzy-AHP, scenarios, stakeholder-editable matrix, sensitivity
  analysis. Only AHP–PROMETHEE, Boolean exclusion masks and validation remain.
  Either rewrite as genuinely-remaining work or cut the slide.
- **Slides 11–12** (Features) — predate algorithms, scenarios, consensus,
  sensitivity, explainability and exports.
- **Slide 14** (Gaps Identified) — the *"No real-time/IoT systems"* gap cites
  [1], [2], [3], which are the LLM/GIS-agent papers supporting the removed query
  layer. Re-cite or cut. Several other listed gaps are ones the project now
  addresses (subjective AHP weighting → sensitivity analysis) and could be
  marked as such.
- **Slides 5–7** (Literature Review) — LLM/GIS-agent papers supporting a layer
  that no longer exists. Replace with GIS-MCDA/RWH work. **These slides are
  screenshot images, not text** — they cannot be edited programmatically and must
  be rebuilt by hand.
- **Slide 36** (Conclusion) — describes the method but reports no result. Add the
  baseline zone split and the cross-method agreement figure.

**Missing entirely — the comparative material the guide asked for**

Six slides' worth, all backed by commands that can be re-run:

1. **Results** — High 18.51 % (2,112.6 km²) / Medium 54.79 % / Low 26.70 %;
   CR 0.0235; 25 sites scoring 0.866–0.984.
2. **Algorithm comparison** — 4 variants, Spearman ρ, class agreement.
   *Aggregation dominates weighting:* WLC→TOPSIS moves High ~5 pp (ρ 0.964),
   AHP→Fuzzy-AHP moves it 0.2 pp.
3. **Scenarios** — the 5 presets including Fertile farmland.
4. **Sensitivity** — ±20 % perturbation, map removal (Lodwick), effective weights
   (Napolitano & Fabbri). Key point: drainage carries 9.3 % of the weight but its
   removal destroys 8 of the top 10 sites.
5. **Consensus** — 15/36 sites chosen by all four algorithms; 1,416.8 km²
   (12.41 %) High under every variant. Figures: `outputs/agreement_algorithms.png`,
   `outputs/agreement_scenarios.png`.
6. **Validation status** — harness written and verified, AUC blocked on §A1b. Say
   this plainly rather than implying a result exists.

Consider also adding `outputs/derived_hydrology.png` and
`outputs/rwh_suitability_map.png`.

**Still accurate:** slides 1–4, 8–10, 15–16, 18–20, 22–24, 26, 29–33, 37.

**Note on editing:** every slide uses the *Blank* layout with hand-placed shapes,
so `python-pptx` can safely rewrite existing text but cannot generate new slides
that match the design. New slides are best made by duplicating slide 26 or 28 in
PowerPoint and replacing the body text.


---

## B. Sprint 2 — decision-support features ✅ **DONE 2026-08-08**

- [x] **Exports** — `exports.py`: sites CSV + GeoJSON, suitability GeoTIFF,
      classified GeoTIFF, report PNG. Provenance embedded in every artefact.
- [x] **Editable AHP matrix** — sidebar `st.data_editor` with reciprocity
      enforcement, live CR, automatic re-score (~0.15 s).
- [x] **Scenario presets** — 4 in `ahp.SCENARIOS`, all CR < 0.10.
- [x] **Sensitivity analysis** — `sensitivity.py`. Result: ±20% retains 90% of
      the top-10 on average (70% worst case), max rank shift 3; most sensitive
      to drainage.

Remaining from this thread:
- [ ] Put the sensitivity result and the scenario comparison table in the report
      — they answer the "subjective AHP weighting" gap on slide 14 directly.
- [ ] Consider adding the scenario comparison as a slide (4 maps side by side).

---

## C. Sprint 3 — validation and contribution

- [x] **Method comparison** ✅ **DONE 2026-08-12** — `algorithms.py`: 4 engines
      (AHP/Fuzzy-AHP × WLC/TOPSIS) with a comparison panel. Finding: the
      aggregation choice dominates the weighting choice.
- [ ] **Validation** — ⚠ **BLOCKED on `data/rwh_structures.geojson`.** The harness
      is complete on the code side: ROC-AUC, **per-algorithm ranking**
      (`validate_all_algorithms`) and **candidate-vs-existing proximity**
      (`candidate_proximity`) all implemented and dry-run against synthetic
      points. Drop the file in and `python validation.py` prints all three.
      `validation.py` is written and its ROC-AUC maths verified against five
      known cases; it reports `missing_data` until the file exists. Collect
      known RWH / check-dam locations (MGNREGS asset records, Jalyukt Shivar
      records, district water conservation office, or digitised from satellite
      imagery). Target 150–300 points, point geometry, valid CRS; optional
      `type` and `year` attributes. **This one file also unblocks all of
      Sprint 4** — chase it first.

---

## C2. Sprint 4 — Multiple suitability algorithms, including a learned model

**Goal.** The proposed-methodology slide already commits to comparing MCDA
variants (AHP-TOPSIS, AHP-PROMETHEE, Fuzzy-AHP). Extend that into a pluggable
*scoring engine* comparison in which one engine is a **machine-learning model
trained on known structures**, so the project reports not one suitability map
but several, produced by different reasoning, evaluated on the same ground truth.

This directly attacks the "subjective AHP weighting" gap on slide 14: instead of
only asserting weights from expert judgement, the project shows what weights the
data itself implies and whether the two agree.

### S4.1 — Label dataset (blocking prerequisite)

Everything below needs ground truth. Collect locations of **existing rainwater
harvesting / water conservation structures** in Chandrapur:

- MGNREGS asset records, Jalyukt Shivar Abhiyan records, district water
  conservation / minor irrigation department data (ask the guide — they may know
  which office holds these);
- or digitise visible check dams, percolation tanks and farm ponds from
  high-resolution satellite imagery.

Target **150–300 positive points** minimum. Save as
`data/rwh_structures.geojson` with an attribute for structure type and, if
known, year built. The same dataset serves the Sprint 3 AUC validation (C above).

Negatives: sample random background points inside the district, excluding a
buffer around known positives. Keep the positive:negative ratio explicit and
documented; expect class imbalance.

### S4.2 — Feature matrix

Sample every criterion layer at each labelled point into a pandas DataFrame.

⚠ **Use the RAW measured values as features, not the 0–1 reclassified scores.**
Feeding the model the hand-made scoring tables would mean it learns from our
judgement rather than from the data, which defeats the entire purpose of the
comparison. Features: slope in degrees, mean annual rainfall in mm, drainage
density in km/km², distance to settlement in km, plus soil texture and IGBP land
cover as one-hot encoded categoricals.

### S4.3 — Models

Train in scikit-learn:

- **Logistic regression** as an interpretable baseline (its coefficients are
  directly comparable to AHP weights);
- **Random forest** and **gradient boosting** as the main models;
- handle class imbalance via `class_weight` or resampling, and state which.

### S4.4 — Validation

⚠ **Use spatial block cross-validation, not random k-fold.** Neighbouring pixels
are strongly autocorrelated, so a random split puts near-identical points in
both train and test and returns an optimistically biased score. Split the
district into spatial blocks and hold out whole blocks.

Report **ROC-AUC, PR-AUC** (more informative than ROC under class imbalance),
accuracy and a confusion matrix. This choice of validation is itself a defensible
methodological point worth a paragraph in the report.

### S4.5 — Comparison against AHP

- Permutation importance from the trained model vs the AHP weight vector — do
  they rank the criteria in the same order?
- Agreement between the ML suitability surface and the WLC surface: Pearson/
  Spearman correlation, plus percentage class agreement across Low/Medium/High.
- Side-by-side maps and a difference map.

### S4.6 — Pluggable scoring engines

Refactor to a common interface so each engine consumes the same normalised
criteria stack and returns a comparable 0–1 suitability raster plus ranked sites:

1. **WLC** (current, AHP weights)
2. **AHP-TOPSIS** — ranking by distance from the ideal solution
3. **Fuzzy-AHP** — handles uncertainty in the pairwise judgements
4. **ML model** — the trained classifier's predicted probability surface

Deliverable: one comparison table of all four scored against the same labels
(AUC, top-N overlap, class agreement).

### S4.7 — Automated report generation

Generate the formal technical report as a PDF with **ReportLab**: methodology,
criteria and scoring tables, AHP matrix with consistency ratio, area statistics,
embedded maps, the ranked site table with per-criterion attribution, and the
validation/comparison results. Runs from the pipeline so the report regenerates
whenever the analysis changes.

---

## C3. Data-quality upgrades — finer input layers

**Why.** The analysis grid is ~300 m, but three of the six input layers are
coarser than that, so the map is drawn finer than the information it contains:

| Layer | Native resolution | vs the 300 m grid |
|---|---|---|
| Slope (HydroSHEDS CONDEM) | ~90 m | finer ✓ |
| Soil texture (SoilGrids) | 250 m | about equal |
| **Land cover (MODIS MCD12Q1)** | **500 m** | coarser ✗ |
| **Population (WorldPop)** | **~1 km** | much coarser ✗ |
| **Rainfall (CHIRPS)** | **5.3 km** | much coarser ✗ |

One MODIS pixel covers 25 hectares — it cannot separate a village from the
cropland around it.

**Most of these are drop-in replacements.** The pipeline reprojects everything
onto the common grid at run time, so saving a finer file over the existing name
and re-running is enough. Only land cover needs a code change.

### C3.1 Land cover — highest impact
Replace MODIS 500 m with **ESA WorldCover (10 m)** or **Google Dynamic World
(10 m)**. Both free. A 50× resolution gain, and land cover feeds both the
suitability criterion and the Curve Number runoff map.

⚠ **Needs a code change:** these use different class codes from MODIS IGBP, so
`LULC_SCORES` and `LULC_LABELS` in `criteria.py` need a new table, and
`derived_maps.py`'s `CURVE_NUMBERS` needs remapping to match. Roughly an hour.
Keep the old table commented out so the comparison can be reproduced.

### C3.2 Elevation → slope
Replace the ~90 m HydroSHEDS DEM with **Copernicus GLO-30** or **NASADEM**
(30 m), or **ALOS PALSAR (12.5 m)**. Slope carries 22.5% of the total weight and
Chandrapur is very flat (median 0.8°), so the local relief that decides whether a
structure holds water is exactly what a 90 m DEM smooths away. Regenerate
`slope.tif` in QGIS with Raster → Analysis → Slope, as before. Drop-in.

### C3.3 Population
WorldPop publishes the same product at **100 m**. Direct swap for
`data/population.tif`, no code change. Sharpens the settlement mask that is
currently blocky at 1 km. Take the buffered version (A1) while re-downloading.

### C3.4 Drainage network
With a 30 m DEM, deriving streams by flow accumulation in QGIS/GRASS becomes
worthwhile — see item D3. Current HydroRIVERS density (0.242 km/km²) is an order
of magnitude below typical because only larger channels are included.

### C3.5 Rainfall — leave as is
5.3 km is coarse, but rainfall varies smoothly across a district, so it loses
least by being coarse. Not worth the effort.

### C3.6 Raise the analysis grid resolution
After upgrading, increase `DEFAULT_MAX_GRID_SIZE` in `gis_analysis.py` from
**450** to ~900 — otherwise 10 m data is resampled onto a 300 m grid and the
detail is discarded. About 4× the cells; still a few seconds per run.

### C3.7 Report the effect
With fixed classification thresholds the reported percentages now respond to
input quality, so record before/after: *"replacing 500 m MODIS land cover with
10 m ESA WorldCover changed the highly-suitable area from 25.6% to X%."* That is
a real robustness result. It was impossible under the old percentile
classification, which reported ~33% regardless.

---

## D. Optional / if asked

- [ ] **Annual runoff volume.** Needs SCS-CN run per month and summed — download
      12 monthly CHIRPS files for one year. `build_rainfall.py` already handles
      monthly input; `derived_maps.py` would need a monthly mode (~30 lines).
      Only required if the guide wants "X million m³ harvestable per year".
      Note monthly SCS-CN still is not strictly event-based; daily is rigorous.
- [ ] **Fixed mm rainfall bands** instead of quantiles. Now viable since the unit
      is confirmed. Would transfer to another district unchanged, addressing the
      "region-specific models" gap — at some cost in within-district
      discrimination. Good as a comparison, not necessarily a replacement
      (METHODOLOGY §5).
- [ ] **DEM-derived stream network.** HydroRIVERS is thresholded to larger
      channels, so district density is 0.242 km/km² against the 0.5–2.0 km/km²
      typical of DEM-extracted networks. Deriving streams from `dem.tif` by flow
      accumulation (QGIS/GRASS) would be more rigorous — but
      `DRAINAGE_DENSITY_BREAKS` must then be recalibrated, preserving the class
      *shares* rather than the numbers (METHODOLOGY §6).

---

## D4. Land value / acquisition data — to make a real cost scenario possible

The "low-earthwork siting" preset weights slope and land cover as a **proxy** for
construction difficulty. It is not a cost model, and must not be named as one.
A genuine cost or acquisition scenario needs data the project does not hold.
Leads, easiest first — **verify availability before committing**:

### D4.1 Protected areas — quick win, do this first
Protected-area boundaries (Tadoba-Andhari Tiger Reserve and buffer, reserved
forest). Effectively non-acquirable, so this is a **hard Boolean exclusion mask**
rather than a weighting — which is exactly the "stronger constraints and
exclusions" item on the proposed-methodology slide. Free from the World Database
on Protected Areas (WDPA/Protected Planet); Forest Survey of India is the
authoritative Indian source. Chandrapur's forest area is ~3,810 km² of 11,443,
so this changes the map materially.

### D4.2 Wasteland classes — cheap-land proxy
Wasteland Atlas of India (NRSC / Department of Land Resources) classifies
degraded and unused land. Government-held wasteland is far cheaper and faster to
acquire than private cropland. The project's own slide already cites ~550 km² of
wasteland in the district. Would enter as a criterion or as a bonus term.

### D4.3 Ready Reckoner / Annual Statement of Rates — real land value
Maharashtra's Department of Registration & Stamps (IGR Maharashtra) publishes
annual circle rates per village / survey zone. This is the standard official land
valuation for the state and would give a genuine ₹/hectare surface.

⚠ Effort is the problem: rates are published per village, not as GIS data, so it
needs joining to village boundaries (Census / Survey of India / OpenStreetMap
admin polygons, or Bhu-Naksha cadastral maps). Realistically a digitising task,
not a download. Scope it before starting.

### D4.4 Construction cost — separate from land cost
Maharashtra Water Conservation Department Schedule of Rates, or MGNREGS unit
cost schedules, give per-structure and per-m³ earthwork rates. Combined with
cut-and-fill volumes derived from `dem.tif`, this would support an actual cost
estimate per candidate site rather than a proxy.

**Recommendation:** D4.1 alone is worth doing — one free download, a real
exclusion mask, and it closes a gap the project has already claimed. D4.2 is a
reasonable second. Treat D4.3 and D4.4 as out of scope unless the timeline
allows, and state them in the report as the data required for a true cost
scenario.

---

## D5. Outstanding code-side work (no new data needed)

Things that are mine to do, tracked separately from the manual GIS/download
tasks above. None of these are blocked.

- [ ] **Streamlit deprecation tidy.** 1.61 warns on `use_container_width`
      (→ `width="stretch"`) and `st.components.v1.html` (→ `st.iframe`). Both
      still work; the warnings clutter every run. Left alone during two bug
      fixes to avoid touching map rendering — worth a dedicated pass with
      `tools/smoke_test.py` as the guard.
- [ ] **Fixed mm rainfall bands as a comparison** (see D2 below). Doable now —
      the unit is confirmed. Would show whether a transferable absolute-band
      scoring changes the result versus the current within-district percentile
      rank, which speaks to the "region-specific models" gap.
- [ ] **Consolidate the seven `docs/archive/AHP_*.md` files** into `docs/METHODOLOGY.md`
      (also listed under Housekeeping). Check for anything worth keeping first.
- [ ] **Monthly SCS-CN runoff mode** in `derived_maps.py` (~30 lines) — only
      worth doing if the monthly CHIRPS rasters are downloaded, so effectively
      blocked on D1.

---

## E. Housekeeping

- [ ] **`git init`.** `.gitignore` is already in place and correct. Do this soon
      — commit history is what makes the project credible on a CV.
- [x] ~~Delete the broken inner venv~~ — **rebuilt 4 Aug 2026.**
      `rwh_gis_assistant/venv` had missing compiled extensions across seven
      packages (rasterio, pillow, pandas, shapely, pyproj, fiona, and geopandas
      via pandas), so it was recreated from `requirements.txt` rather than
      patched. It is now the canonical environment and matches the README.
- [ ] **Delete the redundant outer venv** at
      `Documents/rwh_gis_assistant/venv` (~900 MB), now that the project-local
      one works. Keeping two environments is what caused the original
      confusion. Delete only after confirming the app runs from the project
      venv.
- [ ] **Archive the CHIRPS globals.** The 11 annual rasters in `data/` are
      ~264 MB and already gitignored. `build_rainfall.py` regenerates
      `rainfall.tif` from them at any time, so they can live outside the project.
- [ ] **`data/rainfall_previous.tif`** — the retired single-month placeholder.
      Safe to delete.
- [ ] **Consolidate the seven `docs/archive/AHP_*.md` files.** They predate
      `docs/METHODOLOGY.md` and overlap with it; check for anything worth
      keeping, then fold in and delete.
- [ ] **Rename the project folder** — `rwh_gis_assistant` is a leftover from the
      dropped NLP framing.
