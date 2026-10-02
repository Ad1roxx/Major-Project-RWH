# FINAL PROJECT DOCUMENTATION

## Suitability Analysis for Rainwater Harvesting Site Planning Using GIS
### Chandrapur District, Maharashtra, India

**Group 11** · Yesha Palan · Akshay Khandor · Aditya Dubey · Arya Chimurkar
**Guide:** Mr. Chirag Ramesh Desai
**Document prepared:** 26 August 2026

---

## How to read this document

This is written for someone who knows nothing about geography, mapping software,
or decision mathematics. Every technical term is explained in plain language
before it is used technically.

**Verification tags.** Because this document will be used for a research paper
and a viva, every important claim is tagged with how it was checked:

| Tag | Meaning |
|---|---|
| **[VERIFIED]** | I ran the code on 26 August 2026 and measured this. Reproducible — see §19.5. |
| **[CODE]** | Directly readable in the source. The file and function are named. |
| **[DOC]** | Recorded in project documentation (`CHANGELOG.md`, `docs/METHODOLOGY.md`) but describes something no longer re-measurable — usually a historical measurement whose code has since been replaced. |
| **[INFERRED]** | My reasoning from the code. Sensible, but not stated anywhere. **Do not present as established fact.** |
| **[NOT PRESENT]** | Does not exist in the project. Named explicitly so it is never described as if it does. |

**Three things this project does not have.** State these plainly rather than
letting an examiner discover them:

1. **No machine learning.** No model is trained. See §7.6 — this is a deliberate
   design choice with a good justification, not an omission.
2. **No accuracy figure.** No AUC, precision, recall or similar exists, because
   no ground-truth dataset of existing structures was assembled. See §15.
3. **No version control history.** The project folder is not a Git repository
   [VERIFIED — `git rev-parse` fails; no `.git` directory]. `CHANGELOG.md` was
   maintained by hand as a substitute and is the source for §10.

---

# 1. EXECUTIVE PROJECT OVERVIEW

## 1.1 Project name

**RWH SiteFinder** — Suitability Analysis for Rainwater Harvesting Site Planning
Using GIS, Chandrapur District.

## 1.2 One-paragraph summary

Chandrapur district covers about 11,400 square kilometres. Somewhere in it are
good places to build rainwater harvesting structures — small dams, ponds and pits
that catch monsoon rain instead of letting it run away. Finding those places by
hand means looking at maps of slope, soil, rainfall, rivers, land use and
settlements, and somehow combining six different judgements about every location.
This project automates that. It divides the district into 123,555 small cells of
roughly 300 × 300 metres, scores each cell on all six factors, combines those
scores using a structured expert-judgement method called the Analytic Hierarchy
Process, and produces a colour-coded suitability map plus a ranked shortlist of
25 specific candidate sites — each with a plain explanation of why it scored as
it did. The whole analysis runs in about one and a half seconds inside a web
application.

## 1.3 The problem being solved

**The surface problem.** Chandrapur receives plenty of monsoon rain but suffers
water scarcity, because the rain arrives in a short season and much of it leaves
as runoff. Rainwater harvesting captures some of it. But a structure built in the
wrong place — on steep ground, in impermeable clay, far from where water is
needed, or where no runoff concentrates — wastes public money.

**The deeper problem, and the one this project genuinely contributes to.**
Combining six different map layers into one decision is a well-known technique
(GIS-based Multi-Criteria Decision Analysis). But the standard workflow has three
weaknesses that this project identified and fixed:

- Scores are usually stretched to fit whatever data is at hand, which can destroy
  the information in a layer entirely (§9.1).
- Expert weights are asserted rather than tested (§9.9).
- The choice of mathematical method is rarely isolated from the data, so nobody
  knows how much of the answer is the method rather than the terrain (§9.7).

## 1.4 Proposed solution

A six-criterion GIS-MCDA model implemented in Python with a browser-based
interface, where:

- every score comes from a fixed, published, physically justified table rather
  than the observed data range,
- weights come from AHP with a verified consistency check,
- and the result is stress-tested four independent ways — none of which requires
  data the project does not have.

## 1.5 Main objectives — all achieved

| # | Objective | Status |
|---|---|---|
| 1 | Integrate multi-source spatial data onto a common analysis grid | ✅ Achieved |
| 2 | Derive six thematic criterion layers | ✅ Achieved |
| 3 | Assign weights by AHP with a verified consistency ratio | ✅ Achieved (CR = 0.0235) |
| 4 | Produce a classified Low/Medium/High suitability map | ✅ Achieved |
| 5 | Extract and rank candidate sites with per-site justification | ✅ Achieved (25 sites) |
| 6 | Quantify robustness to weighting and method choices | ✅ Achieved (4 analyses) |
| 7 | Validate against existing structures | ❌ **Not achieved** — code written, data unavailable (§15.4) |

## 1.6 What the final system does

1. Reads seven source datasets and puts them on one common grid.
2. Scores every grid cell 0–1 on six criteria.
3. Combines them into a single suitability score using AHP weights.
4. Classifies the district into High / Medium / Low suitability.
5. Extracts 25 ranked candidate sites, at least 5 km apart.
6. Explains every site — factor by factor.
7. Lets the user switch between **5 planning scenarios** and **4 algorithms** and
   see the map update in about 0.15 seconds.
8. Runs **three sensitivity analyses** and a **cross-method consensus** analysis
   on demand.
9. Exports everything as CSV, GeoJSON, GeoTIFF and PNG, with the settings that
   produced it embedded in every file.

## 1.7 What makes it useful

It converts a subjective, unrepeatable manual exercise into a transparent and
repeatable one. Anyone can re-run it, change a judgement and see exactly what
moves. More importantly, it does not just produce an answer — it produces a
**measurement of how much that answer can be trusted**, which most comparable
work omits.

---

# 2. BACKGROUND AND PROBLEM DOMAIN

## 2.1 Starting from zero: what is GIS?

A **Geographic Information System (GIS)** is software for handling information
that has a location attached. Two kinds of data matter here:

**Raster data** — a picture made of a grid of cells, where each cell holds a
number instead of a colour. A rainfall raster is a grid where each cell holds
"millimetres of rain per year at this spot". Like a spreadsheet laid over a map.

**Vector data** — shapes: points, lines, polygons. The district boundary is a
polygon; the rivers are lines.

**Resolution** is how big each raster cell is on the ground. A 500 m raster has
cells 500 m across — anything smaller is invisible to it.

**Coordinate Reference System (CRS)** is the rulebook for turning positions on a
curved Earth into numbers. Two matter here:

- **EPSG:4326** — plain latitude/longitude in degrees. Convenient and universal,
  but a degree of longitude is not a fixed distance: it shrinks as you move away
  from the equator.
- **EPSG:32644** — UTM Zone 44N, a flat projection where coordinates are in
  metres. Distances are easy but it only works for one strip of the world.

This project computes on EPSG:4326 and converts to kilometres where needed. Why —
and how the "degrees are not distances" problem is handled — is §9.3.

**NoData** is a special value meaning "no measurement here". If it is mistaken
for a real number, it poisons every calculation downstream. This causes a real
trap in one of our datasets (§6.4).

## 2.2 What is rainwater harvesting, and what makes a site good?

Rainwater harvesting (RWH) captures rain where it falls instead of letting it
run off. In a rural district this means check dams, percolation tanks, farm
ponds and recharge pits. The goal here is **groundwater recharge** — getting
water into the ground so wells refill.

Six factors decide whether a location is suitable:

| Factor | Why it matters | Better when |
|---|---|---|
| **Slope** | Steep ground makes water run away before it soaks in; it also raises construction cost | Flatter |
| **Soil texture** | Controls how fast water soaks in and whether an embankment will hold | Moderate infiltration — see §9.2 |
| **Rainfall** | The water supply itself | More |
| **Drainage density** | How much river channel exists per unit area — indicates where runoff concentrates | Denser |
| **Land use / land cover** | Determines whether you may build there, land cost, and runoff generation | Cropland best |
| **Settlement proximity** | Water must serve people, but you cannot build inside a town | 1–5 km away — see §9.5 |

## 2.3 What is Multi-Criteria Decision Analysis?

You have six opinions about every location and need one answer. **MCDA** is the
family of methods for combining them. Two steps:

**Step 1 — normalisation.** Put everything on one comparable scale. Slope is in
degrees, rainfall in millimetres, soil in category names. All must become a
number from 0 (worst) to 1 (best). *This step is where most of this project's
methodological contribution lies* (§9.1).

**Step 2 — aggregation.** Combine the six 0–1 scores into one, respecting that
some factors matter more than others. That requires **weights**.

## 2.4 What is AHP?

The **Analytic Hierarchy Process** (Saaty) turns human judgement into numbers. It
never asks "how important is rainfall, out of 100?" — people are bad at that.
Instead it asks only **pairwise** questions: *"Compared with slope, how much more
important is rainfall?"* answered on a 1–9 scale where 1 = equal and 9 = extreme.

Answer all 15 pairs for six criteria, and AHP extracts a consistent set of
weights from them.

**The consistency ratio (CR).** Humans contradict themselves — you might say A is
twice B, B twice C, but A is *five* times C, which is impossible. AHP measures
this. **CR below 0.10 is the accepted threshold.** Our matrix scores
**CR = 0.0235** [VERIFIED], comfortably consistent.

⚠ **An honest point for the viva:** CR measures *internal consistency*, not
*correctness*. You can be perfectly consistent and perfectly wrong. This is
exactly why we built the sensitivity analyses (§7.5).

## 2.5 Why the problem is difficult

1. **Scale.** 123,555 cells × 6 criteria is not a manual task.
2. **Incommensurability.** Degrees, millimetres and soil-class names must be made
   comparable without inventing meaning.
3. **Mismatched inputs.** The seven datasets have different resolutions,
   projections and NoData conventions.
4. **Subjectivity.** Weights come from human judgement. The honest response is to
   measure the consequence, not to pretend otherwise.
5. **No ground truth.** There is no public register of RWH structures in
   Chandrapur to check against. This shaped the entire evaluation strategy (§15).

## 2.6 Limitations of existing approaches

From the project's literature review [DOC — the review itself is in the
presentation, not the repository; **verify the individual paper claims yourself
before citing them**]: most published RWH suitability studies stop at "we built a
weighted overlay, here is the map". Common weaknesses:

- Min–max normalisation, which makes results non-transferable between districts.
- Weights asserted with only a CR to defend them.
- One method reported, with no way to know how much the method chose the answer.
- Validation often absent or informal.

This project addresses the first three directly and is honest about the fourth.

---

# 3. PROJECT OBJECTIVES AND REQUIREMENTS

## 3.1 Original objectives (project proposal)

From the original scope [DOC]: collect and integrate spatial datasets; generate
thematic layers; reclassify parameters into suitability categories; assign
weights using MCDA; perform weighted overlay; produce a final suitability map.

## 3.2 Final objectives

The original six remain, plus four that emerged during development:

7. Make every scoring decision explicit and transferable rather than data-derived.
8. Quantify the robustness of the result to weight and method choices.
9. Support multiple planning scenarios and multiple MCDA algorithms.
10. Provide site-level explainability.

## 3.3 Objectives that changed

| Change | What happened | Why |
|---|---|---|
| **Natural-language query layer removed** | An NLP interface for querying the map was in the original scope. **Removed 29 July 2026** [DOC — `CHANGELOG.md` §M] | It added no analytical value. Effort redirected to methodological correctness. **Do not present this as a feature.** |
| **Drainage redefined** | Was *distance to nearest river*; became *drainage density* [DOC — 4 Aug 2026] | Distance to a river is a convenience measure, not a hydrological one (§9.4) |
| **Population direction inverted** | Was "lower population is better"; became "1–5 km from a settlement is best" | The original logic would site structures where nobody could use them (§9.5) |
| **Classification changed** | Was a 33rd/67th percentile split; became fixed thresholds | A percentile split always reports ~33% suitable regardless of the data (§9.6) |
| **Validation deferred** | Planned for Sprint 3; harness written, never run | Ground-truth data could not be obtained (§15.4) |
| **Machine-learning layer deferred** | Planned as "Sprint 4" | Blocked on the same missing data [DOC — `TODO.md` §C2] |

## 3.4 Functional requirements — final status

| Requirement | Status | Where |
|---|---|---|
| Integrate spatial datasets of Chandrapur | ✅ | `gis_analysis.build_criteria_stack()` |
| Generate thematic layers | ✅ | `criteria.py` + `gis_analysis.py` |
| Reclassify parameters into suitability scores | ✅ | `criteria.py` |
| Assign weights using MCDA | ✅ | `ahp.py`, `algorithms.py` |
| Perform weighted overlay | ✅ | `algorithms.aggregate_wlc()` |
| Produce final suitability map | ✅ | `utils/map_renderer.py`, `exports.map_png()` |
| Rank candidate sites | ✅ | `gis_analysis._extract_top_locations()` |
| Explain each site | ✅ | `score_stack()` details block |
| Export results | ✅ | `exports.py` — 5 formats |
| Compare algorithms | ✅ | `algorithms.compare_algorithms()` |
| Sensitivity analysis | ✅ | `sensitivity.py` — 3 methods |
| Consensus across methods | ✅ | `consensus.py` |
| Validate against known structures | ❌ | Harness exists; data does not |

## 3.5 Non-functional requirements

| Requirement | How met | Evidence |
|---|---|---|
| **Accurate spatial processing** | True per-row cell areas; exact anisotropic distance transforms; correct resampling per data type | §9.3, §7.2 |
| **Consistent projection and resolution** | All inputs reprojected onto one grid before any computation | `_load_raster_to_grid()` |
| **Interpretable and reproducible** | Every parameter is a named constant in one file; every export embeds its settings | `criteria.py`, `exports._provenance()` |
| **Efficient on medium-scale data** | Cached weight-independent stage; ~1.5 s full run, ~0.15 s re-score | §4.2 [DOC for timings] |

---

# 4. FINAL SYSTEM ARCHITECTURE

## 4.1 Shape of the system

There is **no database, no server API, no authentication, no cloud service and no
external network call at run time** [VERIFIED — no such code exists]. This is a
**single-process desktop-style scientific application** with a browser interface.

That is a deliberate and defensible choice (§9.13), not a shortcut: the analysis
is a pure function of files on disk, so the simplest correct architecture is one
process reading files and computing.

```
┌──────────────────────────────────────────────────────────────┐
│ PRESENTATION LAYER                                            │
│   app.py           Streamlit UI — runs in the browser         │
│   utils/map_renderer.py   Folium interactive map (HTML)       │
└───────────────────────────┬──────────────────────────────────┘
                            │ Python function calls (in-process)
┌───────────────────────────▼──────────────────────────────────┐
│ ANALYSIS LAYER                                                │
│                                                               │
│   ┌─── STAGE 1 — weight-INDEPENDENT (cached, ~0.90 s) ────┐   │
│   │  gis_analysis.build_criteria_stack()                   │   │
│   │    grid → mask → reproject → gap-fill →                │   │
│   │    derive drainage density & settlement distance →     │   │
│   │    score all six criteria to 0–1 (criteria.py)         │   │
│   └────────────────────────┬───────────────────────────────┘   │
│                            │ criteria stack (in memory)         │
│   ┌─── STAGE 2 — weight-DEPENDENT (~0.15 s) ─────────────┐    │
│   │  gis_analysis.score_stack(stack, weights, aggregator) │    │
│   │    aggregate (WLC | TOPSIS) → coverage gate →         │    │
│   │    classify → area stats → extract & rank sites →     │    │
│   │    build per-site explanations                        │    │
│   └────────────────────────┬──────────────────────────────┘    │
└────────────────────────────┼───────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│ SUPPORTING MODULES (all re-score the SAME cached stack)         │
│   ahp.py         weights + consistency + 5 scenarios            │
│   algorithms.py  4 engines + cross-algorithm comparison         │
│   sensitivity.py 3 sensitivity analyses                         │
│   consensus.py   Borda consensus + agreement raster             │
│   validation.py  AUC harness (written, blocked on data)         │
│   exports.py     5 output formats with provenance               │
└─────────────────────────────────────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│ STORAGE — the filesystem                                        │
│   data/     7 source datasets (read-only at run time)           │
│   outputs/  generated artefacts                                 │
└─────────────────────────────────────────────────────────────────┘

SEPARATE, RUN MANUALLY (not part of the interactive path):
   build_rainfall.py   11 CHIRPS globals → data/rainfall.tif
   derived_maps.py     runoff / Curve Number surfaces → outputs/
```

## 4.2 The central architectural decision

**Splitting the pipeline into a cached weight-independent stage and a cheap
weight-dependent stage is the most consequential design decision in the
codebase** [CODE — `build_criteria_stack()` / `score_stack()`, cache in
`_STACK_CACHE`].

Everything expensive — reading rasters, reprojecting, distance transforms, the
drainage convolution — depends only on the *data*, never on the *weights*. So it
is done once and cached, keyed on `(absolute data path, grid size)`.

**Two benefits, and the second is the important one:**

1. **Speed.** Changing a scenario re-scores in ~0.15 s instead of ~1.5 s [DOC].
   A twelve-run sensitivity sweep costs ~2 s [DOC].
2. **Scientific validity.** Every algorithm, scenario and sensitivity run is
   guaranteed to be scored on **byte-identical criterion rasters**. Any
   difference between them is therefore attributable to the method alone —
   which is precisely what the comparison in §14.3 claims. Without this
   structure, the comparison would be confounded.

## 4.3 Data flow, end to end

```
data/boundary.geojson ──► bounding box ──► common grid (450 × 422)
                     └──► rasterise ─────► district mask (123,555 cells)

data/slope.tif ──────┐
data/rainfall.tif ───┤
data/soil_texture.tif├─► reproject onto grid ─► fill gaps inside district ─┐
data/lulc.tif ───────┤   (bilinear / nearest)                              │
data/population.tif ─┘                                                     │
                                                                           │
data/rivers.geojson ─► densify 100 m ─► length per cell ─► 2.5 km window ──┤
                                                    = drainage density     │
population raster ─► cells ≥400 people/km² ─► distance transform ──────────┤
                                            = km to nearest settlement     │
                                                                           ▼
                                      criteria.py: score every layer to 0–1
                                                                           │
                                                    ┌──────────────────────┘
                                                    ▼
ahp.py: pairwise matrix ─► weights + CR ─► aggregate (WLC or TOPSIS)
                                                    │
                                          per-pixel renormalisation
                                          + ≥80 % coverage gate
                                                    ▼
                                        suitability surface (0–1)
                                                    │
                        ┌───────────────────────────┼───────────────────────┐
                        ▼                           ▼                       ▼
                 classify 0.65/0.85          extract 25 sites        area statistics
                 Low/Medium/High             (5×5 tiles, then
                        │                     global maxima,
                        │                     5 km separation,
                        │                     re-rank by score)
                        │                           │
                        └────────────┬──────────────┘
                                     ▼
                    Folium map · site cards · exports · analyses
```

## 4.4 How components communicate

Plain Python function calls inside one process. Data moves as NumPy arrays and
dictionaries. There is no serialisation, no network protocol, no message queue.

The **only shared state** is `gis_analysis._STACK_CACHE` (module-level dict) and
Streamlit's `st.session_state`, which holds the last result so the UI survives
re-renders.

---

# 5. TECHNOLOGY STACK

Every entry states what it is, what it does here, why it was chosen, and where it
appears. All from `requirements.txt` [CODE].

### Python 3.11
**What:** general-purpose programming language.
**Role:** everything.
**Why:** it has the strongest scientific-geospatial ecosystem of any language;
all of GeoPandas, Rasterio and SciPy are Python-first.
**Where:** all 5,286 lines [VERIFIED].

### NumPy (≥1.24)
**What:** library for fast array arithmetic.
**Role:** every raster is a NumPy array; every score, weight and aggregation is
array arithmetic.
**Why:** operating on 123,555 cells one at a time in a Python loop would take
minutes; NumPy does it in milliseconds by pushing the loop into compiled code.
**Where:** every module.

### Rasterio (≥1.3, **<1.5**)
**What:** reads and writes geographic raster files (GeoTIFF).
**Role:** loading source rasters, reprojecting them onto the common grid,
rasterising the boundary, converting cell positions to coordinates, writing
outputs.
**Why:** it is the standard Python interface to GDAL, the underlying C library
that virtually all GIS software uses.
**Where:** `_load_raster_to_grid()`, `_rasterize_boundary()`, `exports.py`.
**Why the version cap:** rasterio 1.5.0 installed with missing compiled
extensions on Windows and broke the environment. Pinned below it; 1.4.4 verified
working [CODE — comment in `requirements.txt`]. This is a real
constraint-driven decision worth mentioning if asked about dependency management.

### GeoPandas (≥0.14)
**What:** tables where one column holds a geographic shape.
**Role:** loading the boundary polygon and 776 river lines; building output site
tables.
**Why:** it makes vector data behave like a spreadsheet while handling CRS
conversions correctly.
**Where:** `build_criteria_stack()`, `exports.sites_geojson()`.

### Shapely (≥2.0) · Fiona (≥1.9) · PyProj (≥3.5)
The three libraries GeoPandas is built on: geometry operations, file reading, and
coordinate-system transformation respectively. Used indirectly, plus
`shapely.geometry.Point` when building the site layer.

### SciPy (≥1.11)
**What:** scientific computing library.
**Role:** three specific jobs —
1. `distance_transform_edt` — exact distance from every cell to the nearest
   settlement, with **anisotropic sampling** so the differing N–S and E–W cell
   sizes are respected;
2. the same function with `return_indices=True` — nearest-neighbour gap filling;
3. `convolve` — the 2.5 km moving window behind drainage density;
4. `stats.spearmanr` — rank correlation between algorithms.
**Why:** these are exact, well-tested implementations. Writing them by hand would
be slower and less reliable.
**Where:** `_distance_km()`, `_fill_nearest()`, `_drainage_density()`,
`algorithms._spearman()`.
**Note:** the project includes a hand-written chamfer distance fallback
(`_distance_transform_chamfer()`) if SciPy is missing — an *approximation*, which
is why SciPy is a listed dependency rather than optional.

### Streamlit (≥1.32)
**What:** turns a Python script into a web app without any web programming.
**Role:** the entire user interface.
**Why:** the alternative — Flask/Django plus a JavaScript frontend — would have
meant building an API layer, a frontend build system and state management, for a
tool with one user at a time and no database. Streamlit removes all of it.
**Where:** `app.py`.
**Trade-off:** Streamlit re-runs the whole script on every interaction. This is
why results are cached in `st.session_state` and why the stack cache matters so
much.

### Folium (≥0.16)
**What:** generates interactive Leaflet.js maps from Python.
**Role:** the pan/zoom map with layer toggles and clickable site markers.
**Why:** a static image cannot be explored. Folium produces a self-contained HTML
map with no frontend code.
**Where:** `utils/map_renderer.render_map()`.

### Matplotlib (≥3.8)
**What:** plotting library.
**Role:** static figures for the report — the classified map PNG, the four-panel
hydrology figure, the agreement maps.
**Why:** interactive maps cannot go in a printed paper.
**Where:** `exports.map_png()`, `derived_maps.py`, `consensus.agreement_png()`.

### Pandas (≥2.0)
**What:** data tables.
**Role:** the editable pairwise-matrix widget, results tables in the UI, CSV
export.
**Where:** `app.py`, `exports.sites_csv()`.

### QGIS (external, manual)
**What:** desktop GIS application.
**Role:** the upstream preparation — clipping source layers to the district,
reprojecting, and deriving slope from elevation using GDAL's Slope tool.
**Why:** these are one-time interactive tasks better done visually.
**Limitation:** this step is **not scripted and not reproducible from the
repository** (§16.9).

### Not used — state clearly if asked
`scikit-learn`, `PyTorch`, `TensorFlow` [NOT PRESENT] — there is no machine
learning. `ReportLab` [NOT PRESENT] — no automated PDF report. `pytest`
[NOT PRESENT] — testing is a standalone script (§15.1).

---

# 6. DATASET AND DATA PROCESSING

## 6.1 The seven sources

| Layer | Source | Native resolution | CRS | Role |
|---|---|---|---|---|
| District boundary | GADM India, ADM2 level | vector (1 polygon) | EPSG:4326 | Study-area mask |
| Drainage network | HydroRIVERS v1.0 (HydroSHEDS), Asia | vector, 776 lines | EPSG:4326 | Drainage density |
| Rainfall | CHIRPS v3.0 annual, 2014–2024 | 0.05° (~5.3 km) | EPSG:4326 | Rainfall criterion |
| Slope | HydroSHEDS CONDEM → GDAL Slope | 88 × 91 m | EPSG:32644 | Slope criterion |
| Soil texture | SoilGrids 250 m | 220 × 228 m | EPSG:32644 | Soil criterion |
| Land cover | MODIS MCD12Q1 `LC_Type1` (IGBP) | ~463 m | EPSG:4326 | Land-cover criterion |
| Population | WorldPop India 2020 | 881 × 912 m | EPSG:32644 | Settlement proximity |

Resolutions and CRSs are [VERIFIED] via `tools/inspect.py`; source attributions
are [DOC].

**Seven datasets, six criteria** — population is not used directly. It is
converted into "distance to the nearest settlement" first (§7.3).

**Why these sources:** all are free, global, peer-reviewed and independently
documented. That matters for a research paper — a reader can obtain them and
re-run the work. It also means the method transfers to any other district.

## 6.2 What the data represents

- **Slope** — steepness in degrees at each point, computed from elevation.
- **Soil texture** — a category code per cell (1 = Sand, 4 = Silt Loam,
  6 = Sandy Clay Loam, 7 = Silt Clay Loam). Only these four occur in Chandrapur
  [VERIFIED].
- **Rainfall** — average millimetres per year over 2014–2024, from a
  satellite-plus-station product.
- **Land cover** — an IGBP category code per cell (cropland, forest, urban…).
  11 of the 17 classes occur here [VERIFIED].
- **Population** — estimated people per square kilometre.
- **Rivers** — line geometry with attributes including Strahler stream order.
- **Boundary** — the district outline.

## 6.3 There is no train/validation/test split

**[NOT PRESENT]** — and this needs explaining rather than apologising for.

Splitting data into training and test sets is a *machine-learning* concept: you
withhold data so you can check whether a model learned a real pattern. This
project has no model that learns from data. It has a set of published,
physically justified rules applied uniformly to every cell. There is nothing to
withhold and nothing to overfit.

**This is a very likely viva question — see §18, Q14.**

The one place a data split *would* apply is validation against known structures
(§15.4), which requires data the project does not have. The harness that would
use it is written and uses a **presence-only** design with random background
sampling (`validation._background_points()`), which is the standard approach when
you have known positives but no known negatives.

## 6.4 Building the rainfall layer

This is the only source layer the project builds itself, in `build_rainfall.py`
[CODE]:

1. Read only the district bounding box **+ 0.20° margin** as a window from each
   of 11 global CHIRPS rasters. The globals are 7200 × 2400 cells each; reading
   windows avoids ever loading them.
2. **Treat any value ≤ −100 as NoData.** CHIRPS ships −9999 as its fill value but
   **does not declare it in the file header**, so standard readers treat it as a
   real measurement of −9999 mm of rain. This would have destroyed every
   statistic. A genuine data trap worth mentioning in the paper.
3. Sum monthly files into annual totals if monthly files are supplied; use annual
   files directly otherwise.
4. Average the 11 annual totals.
5. Sanity-check the result against 1,245 mm ± 20%.
6. Write the output with its provenance stored in the file's metadata tags.

**Verified tags on the shipped file** [VERIFIED]: `SOURCE=CHIRPS annual
precipitation`, `YEARS=2014-2024`, `N_YEARS=11`, `AGGREGATION=mean of annual
totals`, `UNITS=mm/year`, `DISTRICT_MEAN_MM=1492.9`.

**The wet-decade finding.** The 11-year mean sits ~20% above the commonly cited
long-term normal of ≈1,245 mm. Per project records this is a real signal, not a
unit error: 2014, 2015 and 2017 sit near 1,220–1,260 mm while every other year
runs 1,425–1,930 mm [DOC — recorded from the original build run; **re-run
`build_rainfall.py` to reconfirm the per-year figures before publishing them**].

## 6.5 Preprocessing pipeline

**Step 1 — build one common grid.** The boundary's bounding box is divided so the
longer side is 450 cells and the shorter preserves aspect ratio. Result:
**450 × 422 cells, 123,555 inside the district, ≈0.31 × 0.30 km each**
[VERIFIED].

**Step 2 — reproject everything onto it.** With **different resampling rules by
data type** [CODE — `raster_config`]:

| Type | Method | Reason |
|---|---|---|
| slope, rainfall, population | **bilinear** (smooth averaging) | Continuous quantities — averaging is meaningful |
| soil, LULC | **nearest neighbour** | Categorical codes — averaging class 4 and class 6 gives class 5, a category that may not exist and certainly does not mean "halfway between" |

This is a correctness issue, not a preference. **Likely viva question — §18, Q9.**

**Step 3 — mask to the district.** The polygon is rasterised into a
true/false grid.

**Step 4 — fill gaps inside the district.** Source layers stop short of the
boundary in different places, because they were clipped in QGIS beforehand.
Rather than discard the rim, gaps *inside* the district are filled from the
nearest valid cell [CODE — `_fill_nearest()`].

Measured [VERIFIED]:

| Layer | Cells filled | Share of district |
|---|---|---|
| Soil | 2,675 | 2.2% |
| Population | 2,510 | 2.0% |
| Slope | 1,303 | 1.1% |
| LULC | 138 | 0.1% |
| **Rainfall** | **0** | **0.0%** |

Rainfall needs no filling because `build_rainfall.py` reads a margin — a direct
benefit of building that layer in code rather than clipping it by hand.

**Justification for filling:** these layers vary slowly in space, so the nearest
valid value is a reasonable estimate over a few hundred metres. The alternative —
dropping ~2% of the district — would shrink the study area and bias it toward the
interior. **Trade-off:** filled cells carry a value that was not measured there.
The affected share is small and confined to the rim.

**Step 5 — no cleaning, deduplication or augmentation was needed** [VERIFIED —
no such code exists]. The sources are pre-processed scientific products. There
are no duplicate records and no outlier removal.

## 6.6 Files present but not used

| File | Status |
|---|---|
| `data/dem.tif` (38 MB) | ⚠ **Contains no valid pixels — 100% NoData** [VERIFIED at four separate windows]. No analysis module reads it. See §16.9 and "Information Requiring Confirmation". |
| `data/rainfall_previous.tif` | Superseded placeholder |
| `data/Clipped_rivers.*` | Shapefile fallback if `rivers.geojson` is absent |
| `data/osm_water_candidates_UNVERIFIED.geojson` | 158 OpenStreetMap points. **Not RWH structures** — see §15.5 |
| `data/chirps-v3.0.YYYY.tif` × 11 | Inputs to `build_rainfall.py` only |

---

# 7. CORE METHODOLOGY

## 7.1 Overview: five stages

1. **Normalise** each criterion to 0–1 using fixed tables (`criteria.py`).
2. **Weight** the criteria using AHP (`ahp.py`).
3. **Aggregate** into one score (`algorithms.py`).
4. **Classify and extract** sites (`gis_analysis.py`).
5. **Stress-test** the result (`sensitivity.py`, `consensus.py`).

## 7.2 Stage 1 — Normalisation

Four mathematical forms, chosen to match the physical behaviour of each factor
[CODE — all in `criteria.py`]:

**(a) Anchored interpolated ramp** — `score_ramp()`. Used for **slope** and
**drainage density**. A list of (value, score) anchor points; anything between
them is linearly interpolated.

*Slope* (`SLOPE_RAMP_DEG`): 0° → 1.00, 1° → 0.95, 3° → 0.85, 5° → 0.68,
10° → 0.42, 15° → 0.20, 25° → 0.08, 90° → 0.05.

*Drainage density* (`DRAINAGE_DENSITY_RAMP`, km/km²): 0.00 → 0.10, 0.10 → 0.25,
0.20 → 0.50, 0.30 → 0.72, 0.40 → 0.88, 0.90 → 1.00.

**(b) Categorical lookup** — `score_categorical()`. Used for **soil** and
**land cover**. An explicit dictionary from class code to score, with a default
of 0.30 for unrecognised codes. Values are rounded to the nearest integer first,
because reprojection can introduce tiny floating-point drift in class codes.

*Soil*: Sand 0.55, **Silt Loam 1.00**, Sandy Clay Loam 0.80, Silt Clay Loam 0.50.

*Land cover* (all 17 IGBP classes are tabulated so the table transfers beyond
Chandrapur): **Cropland 1.00**, Cropland/Natural Mosaic 0.90, Grassland 0.85,
Open Shrubland 0.70, Savanna 0.70, Barren 0.65, Woody Savanna 0.60, Closed
Shrubland 0.55, Mixed Forest 0.35, Forest classes 0.30, Wetland 0.20, Urban 0.10,
Water 0.00, Snow/Ice 0.00.

**(c) Continuous percentile rank** — `score_percentile_benefit()`. Used for
**rainfall** only.

```
score = 0.20 + 0.80 × (rank of this cell among all district cells)
```

The driest cell scores 0.20 (`RAINFALL_FLOOR`); the wettest scores 1.00.

**(d) Moderate-optimal curve** — `moderate_optimal()`. Used for **settlement
proximity**, where both extremes are bad. Piecewise-linear: 0.05 at 0 km, rising
to 0.97 at 1 km, peaking at **1.00 at 3 km**, back to 0.97 at 5 km, falling to
0.10 at 15 km.

**Why the peak is gentle rather than flat.** A flat top across 1–5 km would give
every location in that band an identical 1.00, which was a major source of tied
sites. The band still reads as "1–5 km is optimal" — everything inside scores at
least 0.97 — but the centre is strictly preferred, so ranking is possible [CODE
— docstring].

**Result** [VERIFIED], in-district score distributions:

| Criterion | Min | Mean | Max | Distinct values |
|---|---|---|---|---|
| Slope | 0.066 | 0.924 | 1.000 | 6,276 |
| Rainfall | 0.200 | 0.600 | 1.000 | 8,001 |
| Soil | 0.500 | 0.908 | 1.000 | **4** |
| Land cover | 0.000 | 0.855 | 1.000 | **10** |
| Settlement | 0.050 | 0.643 | 1.000 | 1,740 |
| Drainage | 0.100 | 0.517 | 0.988 | 8,354 |

The two categorical layers have few distinct values by nature — that is what
categorical means.

## 7.3 Two criteria are computed, not loaded

**Drainage density** [CODE — `_river_length_grid()` then `_drainage_density()`]:

1. Reproject rivers to metres (EPSG:32644), split every line into ~100 m
   segments, reproject back.
2. For each segment compute its true length using local degree-to-kilometre
   scaling at the segment's midpoint latitude, and add it to the cell containing
   that midpoint.
3. Convolve the resulting length grid with a **circular kernel of radius 2.5 km**
   and divide by the true window area.

**Why not just rasterise the lines?** That would give a yes/no "channel present"
mask, which cannot produce a density in km/km². The densify-and-accumulate
approach measures actual length.

Verified: **2,766 km of channel over 11,414 km² = 0.242 km/km²** district-wide;
local values range 0.00–0.85 [VERIFIED].

**Settlement distance** [CODE]: cells with population ≥ **400 people/km²** are
marked as settlement (6.6% of the district [VERIFIED]); SciPy's exact distance
transform then gives every cell its distance in kilometres, using anisotropic
sampling so the differing N–S and E–W cell sizes are handled correctly.

## 7.4 Stage 2 and 3 — Weighting and aggregation

### AHP (baseline)

The pairwise matrix [CODE — `ahp.py`], criteria order slope, rainfall, drainage,
soil, lulc, population:

|  | slope | rainfall | drainage | soil | lulc | pop |
|---|---|---|---|---|---|---|
| **slope** | 1 | 1/3 | 3 | 2 | 4 | 5 |
| **rainfall** | 3 | 1 | 5 | 3 | 6 | 7 |
| **drainage** | 1/3 | 1/5 | 1 | 1/2 | 2 | 3 |
| **soil** | 1/2 | 1/3 | 2 | 1 | 3 | 4 |
| **lulc** | 1/4 | 1/6 | 1/2 | 1/3 | 1 | 2 |
| **pop** | 1/5 | 1/7 | 1/3 | 1/4 | 1/2 | 1 |

Weights are the **normalised geometric mean of each row** — the standard AHP
priority vector.

**Result** [VERIFIED]: rainfall **0.4285**, slope **0.2254**, soil **0.1535**,
drainage **0.0932**, land cover **0.0597**, settlement **0.0397**.
**λ_max = 6.1460, CI = 0.0292, RI = 1.24, CR = 0.0235.** ✓

### Fuzzy-AHP (alternative)

Acknowledges that human judgements are imprecise: each judgement becomes a range
rather than a point. A judgement of 3 becomes (2, 3, 4); its reciprocal 1/3
becomes (1/4, 1/3, 1/2), clipped at the ends of the 1–9 scale. Weights are then
computed by Buckley's geometric-mean method and defuzzified by centroid.

Two important method choices are documented in the code and defended in §9.8.

**Result** [VERIFIED]: rainfall 0.417, slope 0.224, soil 0.159, drainage 0.097,
land cover 0.062, settlement 0.041 — close to crisp AHP but not identical.

### WLC — Weighted Linear Combination

```
S = Σ(wᵢ × rᵢ) / Σwᵢ    over criteria that have data at this cell
```

**Fully compensatory**: a high rainfall score can fully offset a poor slope score
in direct proportion to their weights.

**Per-pixel renormalisation** is important: a cell missing one criterion is scored
on the rest with weights rescaled to sum to 1, so the score stays on a true 0–1
scale instead of being artificially depressed.

**Coverage gate:** a cell is scored only if at least **80%** of the total weight
has data there (`MIN_WEIGHT_COVERAGE`). Without it, an edge cell holding only
rainfall and land cover could score 1.00 from two criteria and outrank a genuine
site evaluated on all six.

### TOPSIS

Ranks each cell by how close it is to an ideal and how far from an anti-ideal:

```
d⁺ = √( Σ wᵢ²(1 − rᵢ)² )     distance from the ideal
d⁻ = √( Σ wᵢ² rᵢ²      )     distance from the worst case
C  = d⁻ / (d⁺ + d⁻)          0–1, higher is better
```

**Less compensatory than WLC** — squaring the shortfall means being weak on any
high-weight criterion hurts disproportionately.

**Our ideals are theoretical** (1 and 0 on the criterion scale), not the observed
best and worst cell. This is a deliberate deviation from textbook TOPSIS,
justified in §9.7.

### The four algorithms

| Algorithm | Weighting | Aggregation |
|---|---|---|
| AHP + WLC (baseline) | crisp Saaty | fully compensatory |
| AHP + TOPSIS | crisp Saaty | closeness to ideal |
| Fuzzy-AHP + WLC | Buckley TFN | fully compensatory |
| Fuzzy-AHP + TOPSIS | Buckley TFN | closeness to ideal |

## 7.5 Stage 5 — Four robustness analyses

All designed to work **without ground-truth data**, which is what makes them
usable here.

1. **One-way ±20% weight perturbation** (`one_way_sensitivity`) — scale each
   weight up and down, rescale the rest, measure how far the shortlist moves.
2. **Map removal** (`map_removal_sensitivity`, after Lodwick, Monson & Svoboda
   1990) — delete each criterion entirely and re-score. Answers "does this layer
   earn its place?" and "what if a neighbouring district lacks this data?"
3. **Single-parameter / effective weight** (`single_parameter_sensitivity`, after
   Napolitano & Fabbri 1996) — compare the weight a criterion was *assigned* with
   the share of the final score it *actually contributed*.
4. **Cross-method consensus** (`consensus.py`) — run all four algorithms (and
   separately all five scenarios) and find the sites and areas they all agree on.

Results in §14.

## 7.6 There is no machine learning — and that is a design choice

**[NOT PRESENT]** — no model is trained, fitted or optimised. No loss function,
optimizer, learning rate, batch size, epoch count, dropout or early stopping
exists. `scikit-learn`, PyTorch and TensorFlow are not installed.

The only "learned" quantity in the whole system is the AHP priority vector, and
that is a **closed-form geometric mean of a hand-specified 6 × 6 matrix** —
deterministic arithmetic, not estimation from data.

**The correct framing:** this is a **knowledge-driven** model, as opposed to a
**data-driven** one. The distinction is standard in the suitability-mapping
literature:

| | Knowledge-driven (ours) | Data-driven (ML) |
|---|---|---|
| Needs labelled examples | **No** | Yes — often hundreds |
| Where the rules come from | Published science + expert judgement | Learned from the examples |
| Transparency | Every rule inspectable and citable | Often opaque |
| Main weakness | Subjectivity of the weights | Needs data that may not exist |

**Why it is the right choice here:** a data-driven model would need a register of
existing RWH structures to learn from. That register does not exist for
Chandrapur (§15.4). A knowledge-driven model works precisely where inventories
are unavailable — which is most of rural India. Its weakness is subjectivity,
and that is exactly what §7.5 measures.

A learned model was scoped as future work [DOC — `TODO.md` §C2] and is blocked on
the same missing data.

---

# 8. DETAILED IMPLEMENTATION

Organised by module. Each entry: purpose, inputs, processing, outputs,
dependencies.

## 8.1 `criteria.py` — 451 lines

**Purpose:** owns every 0–1 scoring rule in the project.
**Inputs:** raw criterion arrays.
**Outputs:** scored arrays, 0–1, NaN preserved.
**Depends on:** NumPy only.

**Architectural invariant** [CODE, stated as a project convention in
`CLAUDE.md`]: **no threshold, class break or lookup table appears anywhere else
in the pipeline.** Every other module imports it as `C` and reads constants from
it. This is what makes the parameter table in §19 complete and auditable, and
what makes the model transferable — retargeting to another district means editing
one file.

Key functions: `score_ramp`, `score_categorical`, `score_percentile_benefit`,
`moderate_optimal`, plus thin wrappers `score_slope`, `score_drainage_density`,
`score_settlement_distance`.

## 8.2 `gis_analysis.py` — 983 lines

**Purpose:** the analysis pipeline.
**Inputs:** a data directory path, a weight dictionary.
**Outputs:** a result dictionary containing the suitability surface, classified
raster, area statistics, ranked sites with explanations, and human-readable notes.

Two public entry points, plus `run_ahp_analysis()` as a convenience wrapper:

| Function | Job |
|---|---|
| `build_criteria_stack()` | Stage 1 — everything weight-independent, cached |
| `score_stack()` | Stage 2 — aggregate, classify, extract, explain |

Internal helpers worth knowing:

| Function | Job |
|---|---|
| `_make_common_grid()` | Grid from bounding box, longest side 450 |
| `_pixel_size_km()` / `_pixel_area_km2_per_row()` | Degree→km conversion; **true cell area per row** |
| `_load_raster_to_grid()` | Reprojection with per-type resampling |
| `_rasterize_boundary()` | District mask |
| `_fill_nearest()` | Gap filling |
| `_river_length_grid()` / `_drainage_density()` | Drainage density |
| `_distance_km()` | Settlement distance (+ chamfer fallback) |
| `_weighted_overlay()` | WLC with coverage gate |
| `_classify_suitability()` | Fixed-threshold classification |
| `_area_statistics()` | Area per class, latitude-corrected |
| `_tiebreak_raster()` | Continuous surface for ordering tied cells |
| `_extract_top_locations()` | Three-stage site selection |
| `_rank_by_score()` | Final renumbering (see §10.7) |

## 8.3 `ahp.py` — 155 lines

**Purpose:** weights, consistency, scenario presets.
**Class:** `AHPEngine`, instantiated once as `ahp_engine`.

`calculate_weights(matrix=None)` returns `({criterion: weight},
consistency_ratio)`. `matrix_from_levels(levels)` builds a reciprocal matrix from
an importance ranking, snapping each ratio to the nearest Saaty value — which
keeps scenario matrices **consistent by construction**.

Holds the full Saaty random-index table for n = 1…10.

## 8.4 `algorithms.py` — 320 lines

**Purpose:** alternative MCDA engines and their comparison.
**Key functions:** `aggregate_wlc`, `aggregate_topsis`, `_to_tfn`,
`fuzzy_ahp_weights`, `weights_for_algorithm`, `compare_algorithms`, `_spearman`.

`compare_algorithms()` runs all four on one stack and reports, per algorithm:
High-class share, mean score, top-10 overlap with the baseline, Pearson
correlation, Spearman rank correlation, and class agreement percentage.

## 8.5 `sensitivity.py` — 309 lines

**Purpose:** three sensitivity analyses.
**Key functions:** `perturb_weights`, `one_way_sensitivity`,
`map_removal_sensitivity`, `single_parameter_sensitivity`, `_match_sites`,
`summary_sentence`.

`_match_sites()` pairs sites between runs **by geographic position within 2 km**,
not by rank — because each run extracts candidates independently and coordinates
shift slightly. 2 km sits well inside the 5 km minimum separation, so a match is
never ambiguous.

## 8.6 `consensus.py` — 357 lines

**Purpose:** which sites and areas survive a change of method.
**Key functions:** `variants_by_algorithm`, `variants_by_scenario`,
`consensus_sites`, `agreement_raster`, `agreement_stats`, `agreement_png`,
`consensus_report`, `consensus_csv`.

`consensus_sites()` clusters candidate sites greedily (strongest first) within
2 km, allowing at most one site per variant per cluster, then ranks clusters by
Borda count.

## 8.7 `validation.py` — 378 lines

**Purpose:** the accuracy harness. **Written and its arithmetic verified; never
run on real data.**
**Key functions:** `roc_auc` (Mann-Whitney U with tie handling, implemented
directly so no scikit-learn is needed), `sample_raster_at_points`,
`_background_points`, `validate`, `candidate_proximity`, `validate_all_algorithms`.

Every entry point returns `{"status": "missing_data"}` when
`data/rwh_structures.geojson` is absent, and the module docstring states
explicitly that it *"will not invent a number"*.

## 8.8 `exports.py` — 249 lines

**Purpose:** serialise a result to the formats a planner needs.
Every function returns `bytes`, so the same code backs both Streamlit download
buttons and command-line export.

Five artefacts: sites CSV, sites GeoJSON, suitability GeoTIFF, classified
GeoTIFF, map PNG.

**Provenance is embedded in every one** [CODE — `_provenance()`]: the weights,
consistency ratio, classification thresholds and generation date. The rationale
in the source: *"A CSV without its weights is not reproducible."*

## 8.9 `build_rainfall.py` (229) and `derived_maps.py` (260)

Standalone command-line tools, run manually, not part of the interactive path.
The first builds the rainfall surface (§6.4); the second produces drainage
density, Curve Number, runoff depth and runoff coefficient surfaces (§12.9).

## 8.10 `app.py` (781) and `utils/map_renderer.py` (345)

The user interface — see §13.

## 8.11 `tools/` — inspection and testing

`inspect.py` (232) profiles any data file in ~20 lines of output instead of
dumping it. `smoke_test.py` (118) is the end-to-end test — see §15.1.

**An engineering detail worth knowing:** `tools/inspect.py` strips its own
directory from Python's module search path at the top of the file. Without this,
`import inspect` anywhere in NumPy resolves to *our* file instead of Python's
standard-library `inspect` module, and the whole environment breaks [CODE].

---

# 9. TECHNICAL DECISIONS AND JUSTIFICATIONS

This is the section to study before the viva. Fourteen decisions, each in the
same structure.

---

## 9.1 Fixed reclassification tables instead of min–max normalisation

**Decision.** Score every criterion using explicit, physically anchored tables
and ramps stored in `criteria.py`, rather than rescaling each layer between its
own minimum and maximum.

**Reason.** Min–max normalisation makes a cell's score depend on what else is in
the raster. Measured on our data before the change, it left **97.4% of slope
cells and 97.7% of population cells scoring above 0.90** [DOC — the defective
code has been replaced, so this is not re-measurable]. One steep escarpment and
one city stretched each range so far that both criteria became nearly constant —
despite carrying 26.5% of the combined weight. Worse, applied to categorical
layers it scored classes **by their code number**, so IGBP class 17 (water)
scored 1.00 and class 13 (urban) 0.75 while forest scored 0.00. Roughly **48% of
the total decision weight was flat or semantically inverted** [DOC].

**Alternatives.** (a) Min–max rescaling — standard in the literature.
(b) Z-score standardisation — same data-dependence problem. (c) Fuzzy membership
functions — more flexible, but the parameters still have to come from somewhere.

**Comparison.** Fixed tables give a cell the same score regardless of which
district it is in, or which subset of a district is analysed. That makes the
model transferable and every score citable to a physical reason.

**Trade-offs.** *Advantage:* reproducible, transferable, defensible, immune to
outliers. *Disadvantage:* someone must justify every break point — which is the
work in `docs/METHODOLOGY.md` — and a poorly chosen table is a systematic error
that the data will not correct.

**Consequences of reverting.** Two criteria would go nearly flat again, the
categorical layers would become meaningless, and results would not be comparable
with any other study area.

**Evidence.** The measured 97.4%/97.7% figures [DOC]; the code itself [CODE —
`criteria.py`]; every break point justified in `docs/METHODOLOGY.md`.
**Evidence type: measured during development.**

---

## 9.2 Silt Loam scores highest, not Sand

**Decision.** Soil scores: Silt Loam 1.00 > Sandy Clay Loam 0.80 > Sand 0.55 >
Silt Clay Loam 0.50.

**Reason.** The objective is groundwater **recharge**, not drainage. Pure sand
infiltrates fastest but retains nothing and gives poor structural stability for
an embankment; heavy clay impedes the recharge we are trying to achieve. The best
soil is one that lets water in at a useful rate *and* holds a structure up.

**Alternatives.** Rank purely by infiltration rate — which would put Sand first.

**Comparison.** Ranking by infiltration alone optimises for water disappearing
quickly, not for storing it or for a structure that survives. It also ignores
that RWH structures need to hold water for days.

**Trade-offs.** *Advantage:* matches the actual engineering objective.
*Disadvantage:* a reviewer expecting the naive infiltration ranking will
challenge it — which is why it is documented.

**Consequences.** Reversing it would push candidate sites toward sandy areas
where structures are harder to build and retention is poor.

**Evidence.** Reasoning documented in `criteria.py` and
`docs/METHODOLOGY.md` §3. ⚠ **Caveat:** the class-code-to-name mapping itself is
**unverified** against SoilGrids documentation — see §16.7 and "Information
Requiring Confirmation".
**Evidence type: reasoned engineering decision from domain principles.**

---

## 9.3 Compute in EPSG:4326 with explicit kilometre conversion

**Decision.** Run the analysis in geographic coordinates (degrees), converting to
kilometres where distance or area is needed, rather than projecting everything to
UTM metres.

**Reason.** The inputs arrive in a mix of EPSG:4326 and EPSG:32644 and must be
unified anyway. Working in 4326 keeps the grid aligned with the raw latitude /
longitude outputs users expect, and avoids a second resampling step.

**The problem this creates, and how it is solved.** In degrees, a cell is not
square on the ground: north–south spacing is constant but east–west spacing
shrinks with latitude. The code handles this in three places [CODE]:
- `_pixel_size_km()` evaluates east–west size at the grid's **centre latitude**;
- `_pixel_area_km2_per_row()` computes true cell area **per raster row**, so area
  statistics are not cell-count × a constant;
- `_distance_km()` passes `sampling=(dy_km, dx_km)` to SciPy so the distance
  transform is **anisotropic**.

**Alternatives.** Project everything to EPSG:32644 and work in metres — simpler
distance arithmetic, but a second resampling of every raster and a grid that no
longer matches the boundary's native CRS.

**Trade-offs.** *Advantage:* one resampling, native output coordinates.
*Disadvantage:* every distance and area calculation needs explicit correction —
easy to get wrong, and a reviewer should check it. We did the correction.

**Evidence.** District area measured at **11,412.5 km²** against the official
11,443 km² — a **99.7% match** [VERIFIED for our figure; the official figure is
[DOC]]. That is a strong independent check that the area arithmetic is right.
**Evidence type: verified against an external reference value.**

---

## 9.4 Drainage *density*, not distance to the nearest river

**Decision.** Score the drainage criterion as channel length per unit area within
a 2.5 km moving window.

**Reason.** Distance to the nearest channel is a **siting-convenience** measure —
it tells you how far you must carry water. Drainage density is a **hydrological**
measure — it tells you where runoff concentrates, which is what determines
whether there is water to harvest. Density is also the variable the RWH
literature uses and the one named on the project's own criteria list.

**Alternatives.** (a) Distance to river — the original implementation.
(b) Stream order weighting. (c) Flow accumulation from the DEM.

**Comparison.** (a) answers the wrong question. (c) would be more rigorous and
would capture small channels HydroRIVERS omits, but requires a working DEM —
which we do not have (§16.9).

**Trade-offs.** *Advantage:* hydrologically meaningful, matches the literature.
*Disadvantage:* depends on the completeness of the river network. HydroRIVERS is
thresholded to larger channels, giving **0.242 km/km²** [VERIFIED] against the
0.5–2.0 km/km² typical of DEM-derived networks. Our class breaks are calibrated
to *this* network and would need recalibration for another.

**Consequences.** Reverting to distance would change which sites are selected and
would no longer match the stated methodology.

**Evidence.** During implementation, the densify-and-accumulate step was checked
by comparing total binned length against total input geometry: **2,765.6 km
binned against 2,767.7 km of input, a 0.08% loss** [DOC]. Independently,
`map_removal_sensitivity` shows drainage removal destroys 8 of the top 10 sites
[VERIFIED] — it is doing real work.
**Evidence type: literature-driven, plus a numerical conservation check.**

---

## 9.5 Settlement proximity as a moderate-optimal band, not "less population is better"

**Decision.** Peak suitability **1–5 km** from any cell with ≥400 people/km²;
score 0.05 inside a settlement, 0.10 beyond 15 km.

**Reason.** The original criterion rewarded remoteness, which would site
structures where nobody could use the water. The corrected intent is a site in
suitable terrain but *set back* from the settlement it serves — close enough to
serve real demand, far enough to avoid built-up impervious land, high land
acquisition cost, and greywater contamination.

**Alternatives.** (a) Population density directly, higher is better — sites
structures in towns. (b) Population density, lower is better — the original
error. (c) A distance-decay curve — monotonic, so it cannot express "too close is
also bad".

**Comparison.** Only a moderate-optimal form can express a factor where **both
extremes are bad**. This is a genuinely different mathematical shape from the
other five criteria and worth pointing out.

**Trade-offs.** *Advantage:* expresses the real siting logic. *Disadvantage:*
three extra parameters (threshold, band, falloff), none formally optimised.

**Consequences.** Widening the band would flatten the criterion; narrowing it
would concentrate sites in a ring around villages.

**Evidence — and an honest caveat.** The 400 people/km² threshold classifies
**6.6% of the district as settlement** [VERIFIED], which matches the built-up
footprint reasonably. But the 1–5 km band is **expert judgement, not fitted to
data**. A diagnostic against 158 OpenStreetMap water features suggested real
structures sit *closer* to villages than this band assumes (§15.5). That is a
hypothesis, not a finding — the points are not RWH structures — but it is an
open question, logged in `TODO.md` §A3.
**Evidence type: reasoned design intent; parameters not formally optimised.
Be upfront about this.**

---

## 9.6 Fixed classification thresholds, not percentiles

**Decision.** High > 0.85, Medium 0.65–0.85, Low ≤ 0.65 — absolute cut-offs on
the 0–1 score.

**Reason.** A percentile split is **self-fulfilling**. A 33rd/67th split always
reports about 33% of any district as highly suitable, no matter how good or bad
the underlying scores are — so the reported percentage is a property of the
method, not a finding about the district. The earlier percentile implementation
duly returned 32.9 / 34.0 / 33.1 [DOC].

**Alternatives.** (a) Percentile split. (b) Natural breaks (Jenks) — data-driven,
so the same non-comparability problem. (c) Equal intervals at 0.33/0.67.

**Comparison.** Only fixed thresholds make the reported area a **real,
comparable result** — comparable between scenarios, between algorithms, and
between districts.

**Trade-offs.** *Advantage:* the percentages mean something. *Disadvantage:* the
thresholds themselves are a judgement, and a district that scores uniformly low
would report almost no High area. That is arguably the correct behaviour.

**Consequences.** With percentiles, every scenario and every algorithm would
report ~33% High and the comparison in §14.3 would be impossible — the finding
that TOPSIS produces a 5-point smaller High class would be invisible.

**Evidence.** Verified: the fixed thresholds produce **18.51 / 54.79 / 26.70**
[VERIFIED] — clearly not a percentile artefact. The percentile mode is still
available via `CLASSIFICATION_MODE` for comparison.
⚠ **A stale comment in `criteria.py` claims these thresholds give "roughly 31%
High / 46% Medium / 23% Low". That comment is out of date — do not quote it.**
**Evidence type: measured comparison against the previous implementation.**

---

## 9.7 Theoretical ideals in TOPSIS

**Decision.** TOPSIS ideals are A⁺ = wᵢ (rᵢ = 1) and A⁻ = 0 — the best and worst
*attainable* values on the 0–1 scale — not the best and worst observed cell.

**Reason.** Using observed extremes would make the score depend on the data
range, reintroducing exactly the defect removed in §9.1, and would stop scores
being comparable between scenarios or districts.

**Alternatives.** Textbook TOPSIS uses observed extremes.

**Comparison.** With observed ideals, running TOPSIS on a different scenario
would shift the ideal points, so the resulting scores could not be compared —
which would break the algorithm comparison entirely.

**Trade-offs.** *Advantage:* comparability and internal consistency.
*Disadvantage:* a deviation from the textbook method that must be declared. If no
cell scores near 1 on anything, all closeness values sit lower than a
textbook implementation would give.

**Evidence.** Documented in the `aggregate_topsis` docstring [CODE]. The
comparison in §14.3 is only meaningful *because* of this choice.
**Evidence type: reasoned methodological decision, documented in code.**

---

## 9.8 Buckley's method for Fuzzy-AHP, with an additive fuzzy scale

**Two decisions, both worth knowing.**

**Decision A — Buckley, not Chang.** Chang's extent analysis is more commonly
cited but is known to assign **zero weight** to criteria that are genuinely
relevant — a documented criticism of the method. Buckley's geometric mean cannot
produce a zero weight [CODE — docstring].

**Decision B — additive fuzzification, not multiplicative.** A judgement of 3
becomes (2, 3, 4), *not* (3/s, 3, 3·s).

**Reason for B, and this is a real finding.** A uniform *multiplicative* spread
scales every row's fuzzy geometric mean by the same constant, so the fuzziness
**cancels exactly during normalisation** and Fuzzy-AHP returns weights identical
to crisp AHP. An earlier implementation in this project did exactly that and
reproduced the crisp weights to three decimal places [DOC — caught during
development, recorded in `CHANGELOG.md` 2026-08-12 §B]. The additive form is
asymmetric at the ends of the 1–9 scale, and that asymmetry is what makes the
fuzzy weights genuinely differ.

**Comparison.** Without this fix, the "Fuzzy-AHP" algorithms would have been
identical to crisp AHP — the comparison would have been vacuous and the paper
would have contained a false claim.

**Evidence.** The bug was found, diagnosed and fixed during development; the
warning is preserved in the source as a `⚠` comment. Fuzzy weights now
measurably differ (rainfall 0.417 vs 0.4285) [VERIFIED].
**Evidence type: a real defect found and fixed during development. Few papers
mention this trap — it is worth a footnote in ours.**

---

## 9.9 Three sensitivity analyses rather than one

**Decision.** Implement one-way perturbation, map removal, and effective-weight
analysis.

**Reason.** Each answers a different question, and together they gave a result
that no single one would have revealed:

| Method | Question |
|---|---|
| ±20% perturbation | "What if this criterion mattered somewhat more or less?" |
| Map removal | "What if we did not have this layer at all?" |
| Effective weight | "How much did this criterion actually contribute?" |

**Comparison.** One-way perturbation alone is what most papers report. Map
removal is what a reviewer means when they doubt a criterion earns its place, and
what a practitioner means when a neighbouring district lacks the data. Effective
weight is the formal answer to "are your weights meaningful?"

**The payoff.** Two independent methods agreed on a non-obvious result: **drainage
carries only 9.3% of the weight but its removal destroys 8 of the top 10 sites**
[VERIFIED]. Weight magnitude and actual influence are different quantities.
Neither method alone would have made that convincing.

**Evidence.** All three run in ~3.7 s via `python sensitivity.py`; full results in
§14.4 [VERIFIED].
**Evidence type: implemented experiments, reproducible.**

---

## 9.10 An index adaptation in map removal sensitivity — declare this

**Decision.** Use `S_i = mean over district cells of |V − V′ᵢ| / V × 100` rather
than the original Lodwick et al. formulation `S = |V/N − V′/n| / V × 100`.

**Reason.** The `/N` and `/n` terms in the original convert a weighted **sum**
over N (then n) parameters into a per-parameter average. Our aggregation
**already divides by the sum of the weights present**, so V and V′ are both on a
0–1 scale and directly comparable. Applying `/N` and `/n` again would normalise
twice and distort the index.

**Trade-offs.** *Advantage:* correct for our aggregation. *Disadvantage:* it is a
deviation from the cited formulation and must be stated explicitly in the paper —
a reviewer comparing our numbers with another study's would otherwise be
comparing different quantities.

**Evidence.** The reasoning is documented in the `map_removal_sensitivity`
docstring [CODE].
**Evidence type: reasoned mathematical adaptation, documented.**

---

## 9.11 Consensus analysis as the answer to blocked validation

**Decision.** Build a cross-method consensus layer instead of leaving the
robustness question unanswered.

**Reason.** Validation is blocked on data we do not have. Rather than either
fabricating a number or having nothing to say, consensus provides **robustness
evidence that requires no ground truth**: a site chosen by one configuration might
be an artefact of that configuration; a site chosen by all of them is not.

**Comparison.** "More accurate than TOPSIS" is unfalsifiable without ground
truth. "Selected independently by all four methods" is a claim we can make today
and defend completely.

**Trade-offs.** *Advantage:* a defensible, honest robustness claim.
*Disadvantage:* consensus is **agreement, not correctness** — four methods can
agree and all be wrong together. Say this before an examiner does.

**Evidence.** 15 of 36 proposed locations selected by all four algorithms;
1,416.8 km² classed High by all four [VERIFIED].
**Evidence type: implemented analysis, reproducible.**

---

## 9.12 The three-stage candidate extraction

**Decision.** Best-per-tile on a 5 × 5 grid, then separated global maxima, then
renumber by score. Minimum 5 km separation, 25 sites.

**Reason for stage 1.** Taking the top 25 cells outright would cluster them all
in one favourable belt, which is useless for district-level planning. Tiling
forces geographic spread.

**Reason for stage 3.** The two selection stages each emit their own descending
run, so a stage-2 site routinely outscores a late stage-1 site. Numbering in
selection order **published rank #22 with a higher score than rank #13** — a real
defect that shipped and was later fixed (§10.7).

**Reason for the 5 km separation.** Two structures 500 m apart harvest the same
catchment. 5 km makes the shortlist genuinely a set of distinct options.

**Trade-offs.** *Advantage:* spread, distinctness, correct ordering.
*Disadvantage:* a large High-suitability zone may show only one or two markers, so
a reader sees High areas with no site in them. That is the constraint operating,
not a bug — worth explaining during the demo.

**Evidence.** Verified: ranks are 1…25 with strictly descending scores from 0.984
to 0.866, and the smoke test asserts this on every run [VERIFIED].
**Evidence type: a defect found in the running system, fixed, and now guarded by
an automated test.**

---

## 9.13 Streamlit and a single-process architecture

**Decision.** A Streamlit web app with no database, no API layer and no
authentication.

**Reason.** The analysis is a pure function of files on disk. There is one user at
a time, no persistent state worth storing, and no multi-user access to control.
A Flask/React stack would add an API layer, a build system and state management
without adding capability.

**Alternatives.** (a) A QGIS plugin — deep GIS integration, but users must install
QGIS and the plugin API is restrictive. (b) Flask + React. (c) A Jupyter notebook
— excellent for analysis, poor as a deliverable for a non-technical planner. (d) A
command-line tool — no map.

**Comparison.** Streamlit gives a browser UI with an interactive map from pure
Python. For a research prototype aimed at demonstrating a method, that is the
right trade.

**Trade-offs.** *Advantage:* minimal code, fast to build, easy to run.
*Disadvantage:* Streamlit re-runs the entire script on every interaction, so
results must be cached in `st.session_state`; it is single-user; and it is not a
production deployment.

**Consequences.** With a database and API this could serve many users — but
nothing in the current requirements needs that.
**Evidence type: constraint-driven engineering decision, appropriate to scope.**

---

## 9.14 Provenance embedded in every exported file

**Decision.** Every export carries the weights, consistency ratio, classification
thresholds and generation date.

**Reason.** *"A CSV without its weights is not reproducible"* [CODE — `exports.py`
docstring]. A site table with no record of how it was produced cannot be checked,
compared or reused.

**Trade-offs.** *Advantage:* every artefact is self-describing. *Disadvantage:*
slightly larger files and a header row in the CSV that spreadsheet software may
need told to skip.

**Evidence.** `_provenance()` [CODE]; GeoTIFF metadata tags verified on
`data/rainfall.tif` [VERIFIED].
**Evidence type: engineering best practice, applied consistently.**

---

# 10. PROJECT EVOLUTION AND MAJOR CHANGES

**No Git history exists** [VERIFIED]. `CHANGELOG.md` was maintained by hand as a
deliberate substitute and states this at the top. All dates below come from it
[DOC]. `docs/archive/CHANGES_SINCE_INITIAL_ZIP.md` records the earliest phase.

## 10.1 Phase 0 — initial prototype (April 2026)

An AHP weighted-overlay pipeline with a Streamlit UI already existed: common
grid, candidate extraction with tiling and 5 km separation, Folium map with
per-criterion popups, and a side-by-side compare panel.

**But it had three methodological defects** that later work found and fixed:
min–max normalisation, percentile classification, and drainage as
distance-to-river.

## 10.2 Sprint 1 — methodological correctness (29 July 2026)

**The largest single change.** Fourteen sub-changes [DOC — `CHANGELOG.md` §A–N]:

- **New file `criteria.py`** — all scoring extracted into explicit tables (§9.1).
- **Population redefined** as settlement proximity, moderate-optimal (§9.5).
- **Drainage converted to kilometres** (a precursor to §9.4).
- **District boundary masking** added.
- **Gap filling at the rim** added.
- **Per-pixel weight renormalisation + the 80% coverage gate** added.
- **Classification switched to fixed thresholds** (§9.6).
- **Area statistics** corrected to use true per-row cell area.
- **Candidate tie-breaking** added.
- **Explainability extended** to include raw measured values.
- **Natural-language query layer removed from scope.**
- Repository cleanup.

## 10.3 Real rainfall data (4 August 2026)

**Before:** a placeholder single-month raster whose units were unresolved, with
blocky edges extending outside the district.

**Change:** `build_rainfall.py` written; 11 CHIRPS v3.0 annual rasters
(2014–2024) averaged into a mean annual surface, read with a 0.20° margin so no
gap filling is needed.

**Improvement:** the highest-weighted criterion (0.428) went from provisional to
reproducible, with provenance in the file's own metadata. The edge-blockiness
problem was solved by the boundary mask plus the margin.

## 10.4 Drainage density and runoff maps (4 August 2026)

**Before:** distance to the nearest river.
**Change:** drainage density on a 2.5 km moving window (§9.4), plus a new
`derived_maps.py` producing Curve Number and runoff surfaces.
**Improvement:** the criterion now matches its stated definition and the
literature.

## 10.5 Fixing tied sites (8 August 2026)

**The problem, reported from the running app:** every top site showed the same
score and the comparison panel showed 100% on every row. Diagnosis: every
criterion had a **flat top**, so **973 cells scored exactly 1.000 on
everything** [DOC].

**Change:** step classes replaced by interpolated ramps between the *same*
anchors; the settlement plateau replaced by a gentle peak; rainfall quintiles
replaced by continuous percentile rank.

**Improvement:** distinct score values rose from 47,495 to **108,229**, and cells
sharing the maximum fell from **973 to 1** [DOC for the before-figures;
**108,229 and "1 cell at maximum" are [VERIFIED] today**].

Also in this window: the Python environment was rebuilt after seven packages were
found with missing compiled extensions, and `matplotlib` was discovered to be
missing from `requirements.txt` entirely.

## 10.6 Sprint 2 — decision support (8 August 2026)

- **Pipeline split** into `build_criteria_stack()` + `score_stack()` (§4.2) —
  architecturally the most important change of the project.
- **`exports.py`** — five artefacts with provenance.
- **Editable pairwise matrix** in the sidebar.
- **Scenario presets** (initially four).
- **`sensitivity.py`** — one-way perturbation.

## 10.7 Sprint 3 and two bug fixes (12 August 2026)

- **`algorithms.py`** — four algorithms over one stack; the Fuzzy-AHP
  multiplicative-cancellation bug found and fixed (§9.8).
- **`validation.py`** — AUC harness written.
- **Bug: read-only matrix editor.** `st.data_editor` returns a DataFrame backed
  by a read-only buffer; editing it in place raised
  `ValueError: assignment destination is read-only`. Fixed with
  `np.array(..., copy=True)`.
  **Process lesson recorded honestly in the changelog:** launching
  `streamlit run app.py` proves nothing, because the script body does not execute
  until a browser connects. This led directly to `tools/smoke_test.py`.
- **Bug: candidate ranks did not follow score.** Rank #22 showed 0.948 while rank
  #13 showed 0.866. Cause: ranks followed selection order across the two
  extraction stages. Fixed by `_rank_by_score()` (§9.12), with a regression check
  added to the smoke test.

## 10.8 Professor feedback round (23 August 2026)

Following a review meeting:

- **Fifth scenario "Fertile farmland"** added.
- **Spearman's rank correlation** added to the algorithm comparison.
- **`consensus.py`** written (§9.11).
- **Map removal and single-parameter sensitivity** added (§9.9, §9.10).
- **`validate_all_algorithms()` and `candidate_proximity()`** completed.

## 10.9 Approaches abandoned, and why

| Abandoned | Why |
|---|---|
| **Natural-language query interface** | No analytical value; effort better spent on correctness. Removed 29 July 2026. |
| **Min–max normalisation** | Destroyed two criteria and inverted two others (§9.1). |
| **Percentile classification** | Self-fulfilling (§9.6). |
| **Distance-to-river drainage** | Wrong hydrological question (§9.4). |
| **"Population, lower is better"** | Sites structures where nobody can use them (§9.5). |
| **Step classes / quintile bands** | Produced 973 tied cells (§10.5). |
| **Multiplicative fuzzification** | Mathematically cancels; Fuzzy-AHP became identical to AHP (§9.8). |
| **Machine-learning layer** | Blocked on ground-truth data that could not be obtained. Remains future work. |
| **Automated PDF report (ReportLab)** | Scoped, never implemented. Exports cover the need. |

---

# 11. COMPLETE END-TO-END WORKFLOW

Written for a non-technical reader. Follow one run from start to finish.

**Step 1 — The user opens the application.** They run one command and a page
opens in their browser: a dark map of Chandrapur, a sidebar, and one button.

**Step 2 — The system checks its data.** The sidebar lists the seven required
datasets with a green tick or red cross each. Nothing runs until they are present.

**Step 3 — The user chooses how to weight the decision.** A dropdown offers five
planning scenarios ("Baseline", "Maximise recharge", "Community-focused",
"Low-earthwork siting", "Fertile farmland"), each with a one-line explanation.
Advanced users can expand the pairwise matrix and edit the underlying judgements
directly. The sidebar immediately shows the resulting weights and the consistency
ratio, with a green tick if it is below 0.10.

**Step 4 — The user chooses the mathematics.** A second dropdown offers the four
algorithms, each with a one-line note on what it does differently.

**Step 5 — The user presses "Run Suitability Analysis".** Everything below happens
in about one and a half seconds.

**Step 6 — Building the map grid.** The system reads the district outline, draws
a bounding box around it, and divides it into 450 × 422 cells of roughly 300
metres. It marks which cells fall inside the district: 123,555 of them.

**Step 7 — Putting every layer on the same grid.** Five raster files, each in its
own projection and resolution, are re-sampled onto that grid. Continuous data is
smoothly averaged; category data is copied from the nearest cell so no fake
categories are invented.

**Step 8 — Filling small holes.** Where a layer stops just short of the boundary,
the missing cells are filled from the nearest measured value — about 2% of the
district at worst.

**Step 9 — Computing the two derived layers.** The river lines are chopped into
100-metre pieces and their lengths added up cell by cell; a 2.5 km circular window
then converts that into "kilometres of channel per square kilometre". Separately,
every cell with more than 400 people per square kilometre is marked as a
settlement, and the distance from every other cell to the nearest one is measured.

**Step 10 — Scoring.** Each of the six layers is converted to a score between 0
and 1 using its own fixed rule — a ramp for slope and drainage, a lookup table for
soil and land cover, a percentile rank for rainfall, and a "best in the middle"
curve for settlement distance.

**Step 11 — Combining into one number.** The six scores are averaged using the
AHP weights. If a cell is missing a criterion, the remaining weights are rescaled
so the score stays on a fair 0–1 scale — but only if at least 80% of the total
weight has data there. Otherwise the cell is left blank rather than guessed at.

**Step 12 — Classifying.** Cells scoring above 0.85 are High, 0.65–0.85 Medium,
below 0.65 Low. The true area of each class is added up, correcting for the fact
that cells shrink slightly toward the north.

**Step 13 — Choosing the shortlist.** The district is divided into 25 tiles and
the best cell in each is picked, so the shortlist is spread out. Remaining slots
are filled with the highest-scoring cells anywhere, provided each is at least 5 km
from every site already chosen. Finally, all 25 are renumbered strictly by score.

**Step 14 — Explaining each site.** For every chosen site the system records its
score on each of the six factors, how much each contributed, which factors it
comfortably satisfies, and the real measured values behind them — the slope in
degrees, the soil name, the land-cover name, the drainage density, the distance
to the nearest village.

**Step 15 — The user sees the result.** An interactive map with colour-coded
zones, river lines and clickable markers. Four summary boxes give the area of
each class. Below that, cards for the top ten sites in plain language.

**Step 16 — The user explores.** They can compare any two sites side by side with
arrows showing which wins on each factor; switch scenario or algorithm and watch
the map update in a fraction of a second; run the sensitivity analyses; compute
the consensus across methods; and download the results in four formats.

---

# 12. FINAL FEATURES

Only what exists in the final implementation.

## 12.1 Six-criterion suitability mapping
**What:** produces a Low/Medium/High map of the district.
**Why:** the core deliverable.
**Interaction:** press one button.
**Internally:** the full pipeline of §11.
**Output:** classified raster + area statistics.

## 12.2 Twenty-five ranked candidate sites
**What:** specific coordinates, ranked by score, at least 5 km apart.
**Why:** a map alone does not tell a planner where to go.
**Output:** ranked list with coordinates and scores, top ten shown as cards.

## 12.3 Per-site explainability
**What:** for every site — per-criterion score, weighted contribution, the
criteria it satisfies (≥0.66), and the raw measured values.
**Why:** a planner must be able to challenge a recommendation. A bare score
cannot be argued with.
**Output:** site cards in the UI, map popups, and full detail in the CSV export.

## 12.4 Side-by-side site comparison
**What:** pick two sites; see each factor compared with an arrow showing which
wins, plus an overall winner.
**Why:** the real decision is usually between two shortlisted options.

## 12.5 Five planning scenarios
**What:** preset weightings for different planning objectives.
**Why:** "best site" depends on what you are optimising for. Making that explicit
is more honest than pretending one weighting is universal.
**Internally:** each scenario is a different pairwise matrix over the same six
criteria; all pass CR < 0.10.
⚠ **Two are explicitly labelled PROXY in the source and must be described as
such:** "Low-earthwork siting" is *not* a cost model (no land-value data);
"Fertile farmland" is *not* a fertility model (no soil-chemistry data).

## 12.6 Editable pairwise matrix
**What:** users can edit the AHP judgements directly in a table.
**Why:** the weights are expert judgement — a different expert should be able to
supply their own.
**Internally:** only the upper triangle is edited; the lower triangle is rebuilt
as its reciprocal automatically, so the matrix always stays valid. The consistency
ratio updates live.

## 12.7 Four selectable MCDA algorithms
**What:** switch between AHP/Fuzzy-AHP × WLC/TOPSIS.
**Why:** to show how much of the answer is the method.
**Note:** for Fuzzy-AHP the app reports the CR **of the crisp matrix**, and says
so, because Fuzzy-AHP has no standard consistency ratio [CODE].

## 12.8 Algorithm comparison panel
**What:** one button runs all four and tabulates High-class share, mean score,
top-10 overlap, Pearson and Spearman correlation, and class agreement.

## 12.9 Three sensitivity analyses
**What:** ±10/20/30% one-way perturbation (user-selectable), map removal, and
effective weights — all from one button.

## 12.10 Consensus analysis
**What:** choose "Algorithms" or "Scenarios"; get the consensus site table ranked
by Borda count, the agreement map, and downloads.

## 12.11 Five export formats
Sites CSV, sites GeoJSON, suitability GeoTIFF, classified GeoTIFF, map PNG — all
with provenance embedded.

## 12.12 Derived hydrological surfaces
**What:** drainage density, SCS Curve Number, runoff depth and runoff coefficient
as GeoTIFFs plus a four-panel figure.
**How:** `python derived_maps.py` (command line, not in the app).
⚠ **Runoff is deliberately NOT an AHP criterion.** Curve Number is a function of
land cover and soil, and runoff additionally of rainfall — all three are already
weighted criteria, so including runoff would silently double-weight them [CODE].
⚠ **Reported per 100 mm design storm only, never as an annual volume** (§9 note
and §16.10).

## 12.13 Data inspection tool
`python tools/inspect.py <file>` profiles any dataset in ~20 lines.

## 12.14 End-to-end smoke test
`python tools/smoke_test.py` — 11 automated checks (§15.1).

---

# 13. USER INTERFACE AND USER EXPERIENCE

## 13.1 Layout

A single scrolling page with a persistent sidebar — a deliberate choice over
multiple tabs, because the analysis is one continuous story: map → statistics →
sites → comparison → export → robustness.

**Sidebar (always visible):** Data Status · Weighting (scenario, matrix editor,
algorithm, live CR and weights) · About.

**Main panel (top to bottom):** Run button → interactive map → zone statistics →
top-ten site cards → compare panel → export buttons → sensitivity → consensus →
algorithm comparison → analysis notes → collapsible AHP weights and scoring
methodology.

## 13.2 Key design decisions

**Single-button workflow.** One "Run Suitability Analysis" button, not a
multi-step wizard. The system either has its data or it does not.

**Automatic re-scoring on weight change.** If the user changes scenario or
algorithm after a run, the app detects that the weight vector no longer matches
the displayed result and silently re-scores [CODE — the `stale` check]. Because
the criteria stack is cached, this takes ~0.15 s, so it feels instant. Without the
architectural split of §4.2 this would take 1.5 s and would have needed a
progress bar.

**Data status before anything else.** Green ticks and red crosses at the top of
the sidebar, so a missing file is diagnosed before it becomes a confusing error.

**Explanation next to every control.** Each scenario shows its rationale; each
algorithm shows what it does differently; the sensitivity panel states what it is
for in one line — *"This is the answer to 'your AHP weights are subjective'."*

**Map layer control.** Boundary, rivers, high-suitability zones and candidate
sites are separate toggleable layers, with explicit z-ordering so the boundary
does not steal mouse events from the site markers [CODE —
`utils/map_renderer.py`, `CustomPane`].

**Transparency panels.** Two collapsible sections show the AHP weights with their
CR verdict, and a plain-language description of how each criterion is scored,
ordered by weight. The analysis notes list is printed verbatim — including
warnings — so the user sees what the pipeline actually did.

## 13.3 Feedback and error states

- Spinner with a context-appropriate message during computation.
- Green/red status markers for data files and for the consistency ratio.
- If the CR exceeds 0.10, an explicit *"inconsistent, revise the judgements"*
  message.
- If no sites can be extracted, an informational message rather than an empty
  panel.
- If analysis fails, an error plus the notes explaining why.
- A provisional-input banner appears automatically if `RAINFALL_SOURCE_NOTE` is
  set — currently `None`, because the rainfall input is now real.

---

# 14. RESULTS AND FINAL OUTCOME

All figures [VERIFIED] on 26 August 2026 unless marked otherwise.

## 14.1 The suitability map

Continuous score across 123,555 cells: minimum 0.256, maximum 0.984, mean 0.729,
median 0.742. **108,229 distinct values; exactly one cell at the maximum** — the
tied-sites problem of §10.5 is fully resolved.

| Class | Threshold | Share | Area |
|---|---|---|---|
| **High** | > 0.85 | **18.51%** | **2,112.6 km²** |
| **Medium** | 0.65 – 0.85 | 54.79% | 6,252.6 km² |
| **Low** | ≤ 0.65 | 26.70% | 3,047.3 km² |

Total analysed: **11,412.5 km²** — 99.7% of the official district area, an
independent check that the geometry and area arithmetic are correct.

## 14.2 The candidate sites

25 sites, scores **0.984 down to 0.866**, strictly descending, minimum 5 km apart.

| Rank | Lon | Lat | Score | Slope | Soil | Land cover | Drainage density | To settlement |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 km |
| 2 | 79.7673 | 19.6664 | 0.982 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 km |
| 3 | 79.4195 | 20.4775 | 0.977 | 0.26° | Silt Loam | Cropland | 0.62 | 2.1 km |
| 4 | 79.3262 | 20.4549 | 0.977 | 0.35° | Silt Loam | Cropland | 0.40 | 4.7 km |
| 5 | 79.6570 | 20.3532 | 0.976 | 0.12° | Silt Loam | Cropland | 0.58 | 5.9 km |

**Worth noting honestly:** all five are Silt Loam cropland on near-flat ground.
That is the model behaving consistently with its scoring tables — but it also
means the shortlist is concentrated in one landscape type, which is a legitimate
point of discussion about compensatory aggregation.

## 14.3 The headline finding — aggregation dominates weighting

| Algorithm | High % | Mean | Top-10 shared | Pearson | Spearman | Class agreement |
|---|---|---|---|---|---|---|
| AHP + WLC (baseline) | 18.51 | 0.729 | 10/10 | 1.000 | 1.000 | 100.0% |
| AHP + TOPSIS | 13.62 | 0.669 | 9/10 | 0.961 | 0.964 | 74.5% |
| Fuzzy-AHP + WLC | 18.32 | 0.731 | 7/10 | 1.000 | 1.000 | 98.7% |
| Fuzzy-AHP + TOPSIS | 12.92 | 0.671 | 9/10 | 0.964 | 0.967 | 74.9% |

**Finding 1 — how you combine matters far more than how you weight.** Changing
the aggregation (WLC → TOPSIS) moves the highly-suitable area by ~5 percentage
points and drops class agreement to ~75%. Changing the weighting (AHP →
Fuzzy-AHP) moves it 0.2 points at 98.7% agreement. **Papers that compare only
weighting methods may be comparing the less consequential choice.** This is the
project's most novel result.

**Finding 2 — surface correlation is the wrong metric for ranking stability.**
Fuzzy-AHP + WLC correlates **1.000** with the baseline surface yet shares only
**7 of the top 10 sites**. Correlation and shortlist agreement measure different
things; report both.

## 14.4 Robustness

**One-way ±20% perturbation.** Retains **90% of the top-10 sites on average**
(70% worst case), maximum rank shift **3**. Influence on the High-class share
(mean absolute change, percentage points): drainage **1.66** > slope 1.55 > soil
1.17 > rainfall 0.48 > settlement 0.35 > land cover 0.04.

**Map removal.**

| Removed | Weight | S index (%) | Top-10 retained | High % | Δ |
|---|---|---|---|---|---|
| Rainfall | 0.428 | 17.374 | **1/10** | 42.46 | +23.95 |
| Slope | 0.225 | 8.979 | 9/10 | 13.27 | −5.24 |
| Soil | 0.154 | 5.301 | 10/10 | 14.12 | −4.39 |
| Drainage | 0.093 | 4.280 | **2/10** | 26.87 | +8.36 |
| Land cover | 0.060 | 2.501 | 10/10 | 19.07 | +0.56 |
| Settlement | 0.040 | 1.780 | 9/10 | 20.75 | +2.24 |

**Finding 3 — the index tracks weight order, but site retention does not.**
Removing drainage changes the surface by only 4.28% — fourth of six — yet leaves
just **2 of the top 10 sites standing**, worse than removing slope. Drainage
barely moves the *map* but almost completely reorders the *shortlist*, because it
has the highest spatial variance of the six criteria and is what separates
otherwise near-identical candidates. This independently corroborates the ±20%
result.

**Finding 4 — a criterion can be restrictive rather than merely important.**
Removing rainfall *inflates* High to 42.46%. Rainfall is scored by percentile
rank, so it averages ~0.6 and acts as a **brake** on the composite; remove it and
everything else — mostly high-scoring across the district — pushes scores up. The
weight alone does not tell you this.

**Effective weights.**

| Criterion | Assigned % | Effective % | Ratio |
|---|---|---|---|
| Rainfall | 42.85 | 34.11 | 0.796 |
| Slope | 22.54 | 29.11 | **1.292** |
| Soil | 15.35 | 19.35 | 1.260 |
| Land cover | 5.97 | 7.25 | 1.214 |
| Drainage | 9.32 | 6.61 | **0.710** |
| Settlement | 3.97 | 3.57 | 0.901 |

**Finding 5 — assigned weight and realised influence differ, and the gap is
explainable.** Criteria that score uniformly well across Chandrapur contribute
more than assigned — slope (1.29×) because the district is very flat (mean
1.47°), soil (1.26×) because Silt Loam dominates. Criteria scoring uniformly
poorly contribute less — drainage (0.71×) because density is only 0.242 km/km².
Rainfall (0.80×) is a special case: percentile-rank scoring mechanically fixes
its mean near 0.6, capping its contribution regardless of its 0.428 weight.
**This is the formal answer to "are your weights meaningful?"**

## 14.5 Consensus

**Across the four algorithms:** 36 distinct locations proposed, **15 selected by
all four**. **1,416.8 km² (12.41%) classed High by all four**; 80.77% by none.

**Across the five scenarios:** 54 distinct locations, **7 selected by all five**.
1,217.1 km² (10.66%) High under every scenario.

**The defensible headline:** *"Fifteen sites were selected independently by four
different MCDA methods, and 1,417 km² was classed highly suitable by all of
them."* No ground truth required.

## 14.6 Scenario outcomes

| Scenario | CR | High % |
|---|---|---|
| Baseline (balanced) | 0.0235 | 18.51 |
| Maximise recharge | 0.0044 | 30.14 |
| Community-focused | 0.0059 | 18.77 |
| Low-earthwork siting | 0.0078 | 29.91 |
| Fertile farmland | 0.0146 | 28.19 |

## 14.7 Derived hydrology (100 mm design storm)

| Surface | Min | Max | Mean |
|---|---|---|---|
| Drainage density (km/km²) | 0.000 | 0.848 | 0.233 |
| SCS Curve Number | 30 | 100 | 70.5 |
| Runoff depth (mm) | 0.00 | 100.00 | 35.4 |
| Runoff coefficient | 0.000 | 1.000 | 0.354 |

## 14.8 Improvements over earlier versions

| Aspect | Before | Now |
|---|---|---|
| Cells tied at maximum score | 973 [DOC] | **1** [VERIFIED] |
| Distinct score values | 47,495 [DOC] | **108,229** [VERIFIED] |
| Slope cells scoring > 0.90 | 97.4% [DOC] | Slope now spans 0.066–1.000 with 6,276 distinct values [VERIFIED] |
| Rank ordering | Broken — #22 outscored #13 [DOC] | Strictly descending, guarded by an automated test [VERIFIED] |
| Reported class shares | ~33/34/33 by construction [DOC] | 18.5/54.8/26.7, a real measurement [VERIFIED] |
| Rainfall input | Placeholder, unresolved units | 11-year CHIRPS mean with provenance in metadata |
| Fuzzy-AHP | Identical to crisp AHP (bug) [DOC] | Measurably different weights [VERIFIED] |

---

# 15. VALIDATION AND EVALUATION

## 15.1 System testing — what we did do

`tools/smoke_test.py` uses Streamlit's `AppTest` harness to drive the real
application headlessly. **11 checks, all passing** [VERIFIED, run 26 August 2026]:

```
ok  script loads
ok  run analysis (High 18.5%)
ok  scenario -> Maximise recharge (High 30.1%)
ok  algorithm -> AHP + TOPSIS (High 17.7%)
ok  algorithm -> Fuzzy-AHP + WLC
ok  back to baseline (High 18.5%)
ok  rank ordering (1..25, scores descending)
ok  export buttons (4)
ok  Run sensitivity
ok  Compute consensus
ok  Compare all algorithms
all checks passed
```

**Why this test exists, and why the design matters.** During development a bug
shipped because `streamlit run app.py` starting successfully proves nothing — the
script body does not execute until a browser connects. `AppTest` executes it
properly. The **rank-ordering check is a regression guard** for the specific
defect described in §10.7.

*(A note on reading that output: the 17.7% for AHP + TOPSIS is measured while the
scenario is still set to "Maximise recharge" from the previous step — the checks
run sequentially. Under the baseline weighting AHP + TOPSIS gives 13.62%. Both
figures independently confirmed [VERIFIED].)*

## 15.2 Internal verification

- **Area cross-check:** 11,412.5 km² measured vs 11,443 km² official = 99.7%.
- **Length conservation:** 2,765.6 km binned vs 2,767.7 km input = 0.08% loss
  [DOC].
- **Consistency ratio:** 0.0235, and all five scenarios below 0.0235.
- **Rainfall sanity check:** built into `build_rainfall.py`, ±20% against 1,245 mm.
- **Rank monotonicity:** asserted on every smoke-test run.

## 15.3 Robustness evaluation

The four analyses of §14.4–14.5. **These evaluate the model's stability, not its
accuracy** — an important distinction to make before an examiner does.

## 15.4 What we did NOT do — accuracy validation

**There is no accuracy figure, and there will not be one before the
presentation.**

The harness is complete: `validation.py` implements ROC-AUC via the Mann-Whitney
U statistic with proper tie handling, presence-only sampling with a 1 km
exclusion buffer around positives, 5 background points per positive, and a fixed
random seed. `validate_all_algorithms()` would rank all four methods by AUC.

**It has never run on real data**, because `data/rwh_structures.geojson` — a
register of existing RWH structures in Chandrapur — does not exist. Every entry
point returns `{"status": "missing_data"}`, and the module docstring states it
*"will not invent a number."*

**What ROC-AUC would mean if we had it:** the probability that a randomly chosen
real structure scores higher on our map than a randomly chosen random location.
1.00 = perfect, 0.50 = no better than chance, below 0.50 = inverted.

**Why we could not get the data:** it would require MGNREGS asset records,
Jalyukt Shivar records, district water-conservation office data, or manually
digitising visible check dams and farm ponds from satellite imagery. Target
150–300 points [DOC].

## 15.5 The OSM diagnostic — read this before someone asks

`data/osm_water_candidates_UNVERIFIED.geojson` holds **158 OpenStreetMap points**
tagged as artificial water features inside the district [VERIFIED]. These were
pushed through the harness **as a code-path exercise**.

Indicative figures, **for internal reasoning only**: overall AUC **0.482**;
settlement-proximity criterion alone **0.379** [DOC].

**These must not appear in the paper or the presentation as validation.** OSM
artificial water polygons are not RWH structures — they mix farm ponds, quarry
pits, tanks and mine water. 0.482 is indistinguishable from chance.

**But the breakdown is informative and honest to mention as future work:** the
entire deficit came from settlement proximity; every other criterion scored at or
above chance. That suggests real water structures sit *closer* to villages than
our 1–5 km band assumes. It is a hypothesis about a parameter, logged in
`TODO.md` §A3 — not a finding.

## 15.6 The honest position on "which method is best"

> The four algorithms differ measurably, but *differing* is not *being better*.
> Naming an outperformer requires an external standard, and the only one available
> is agreement with structures that already exist. Until that inventory is
> assembled, we report that the methods **differ**, quantify by how much, and
> state that ranking them by accuracy is future work.

What we *can* claim today is consensus: 15 of 36 locations selected by all four
methods, 1,417 km² classed High by all four.

---

# 16. LIMITATIONS

Stated plainly. A limitations section that names real constraints reads far
stronger than one listing generic caveats.

**16.1 No accuracy validation.** Every number describes the model's internal
behaviour; none tests the map against built structures. This is the single
largest limitation.

**16.2 Input resolution is uneven.** The analysis grid is ~300 m but land cover is
~463 m, population ~900 m and rainfall ~5.3 km. **The map is drawn finer than
three of its six inputs.** Finer output does not mean finer information.

**16.3 Edge effects from pre-clipped inputs.** Distance- and density-based criteria
see only in-district features, so a river or town just across the boundary is
invisible. Measured [DOC — `docs/METHODOLOGY.md` §12]: 24.4% of the district lies
within 5 km of the border; **25.8% of cells could have a nearer out-of-district
settlement**; 4.9% a nearer river; **8 of the 25 candidate sites, including
rank #1**, lie in the exposed zone. **Bounded:** the two affected criteria carry
combined weight 0.133, so class areas barely move; the effect is on near-border
*ranking*. Fixing it requires re-exporting inputs clipped to a 20 km buffered
boundary — **no code change needed**.

**16.4 HydroRIVERS understates the drainage network.** 0.242 km/km² against the
0.5–2.0 km/km² typical of DEM-derived networks. Our class breaks are calibrated
to this network and would need recalibration for another.

**16.5 AHP weights remain expert judgement.** CR = 0.0235 establishes internal
consistency, not correctness. The sensitivity analyses bound the consequence but
do not remove the subjectivity.

**16.6 No socio-economic or cost dimension.** No land value, acquisition or
construction-cost data. "Low-earthwork siting" is a slope and land-cover proxy.

**16.7 Soil class coding is unverified** against SoilGrids documentation. The
source file carries an explicit warning that standard SoilGrids texture coding
numbers classes differently. If the coding is wrong, the soil criterion (weight
0.154) is wrong. **This is the highest-priority item to confirm.**

**16.8 Rainfall scoring is district-relative.** Percentile rank maximises
within-district discrimination but is not transferable — the same 1,400 mm cell
would score differently in a wetter district. This partially contradicts the
transferability claim made for the other five criteria. **Be honest about this
tension; it is a legitimate reviewer question** [INFERRED — the trade-off is
documented, this specific tension is my observation].

**16.9 Upstream preprocessing is manual.** QGIS clipping and slope derivation are
not reproducible from the repository. Compounded by `data/dem.tif` containing no
valid data [VERIFIED], the slope layer's stated provenance cannot be
independently verified from what is in the project.

**16.10 Runoff is per design storm only.** SCS-CN is an event model. A defensible
annual runoff volume would require running it per month on monthly rainfall and
summing — data the project does not hold.

**16.11 Single study area, single time slice.** No temporal analysis, no
cross-district transfer test. Transferability is argued from construction, not
demonstrated [INFERRED].

**16.12 No formal parameter optimisation.** Several parameters — the 2.5 km
window, the 400 people/km² threshold, the 1–5 km band, the 5 km separation, the
0.80 coverage gate — were chosen by reasoning, not by fitting. Each has a stated
justification, but none was optimised against an objective. **Say this if asked
rather than implying otherwise.**

---

# 17. FUTURE IMPROVEMENTS

## 17.1 Already implemented — do not list these as future work

Multiple algorithms · scenario planning · editable weights · sensitivity analysis
(three methods) · consensus analysis · site-level explainability · exports with
provenance · derived hydrological surfaces · automated smoke test.

## 17.2 Possible future work

**Priority 1 — Ground-truth validation.** Assemble 150–300 RWH structure
locations and run `validation.py`. This is the single highest-value addition: it
would unblock the accuracy figure, the per-algorithm ranking, and the ML layer
simultaneously. *The code is already written.*

**Priority 2 — Buffered re-export of inputs.** Re-clip rivers and population to a
20 km buffered boundary in QGIS to remove the edge effect of §16.3. **No code
change required** — cheap, and it fixes a real limitation affecting 8 of 25 sites.

**Priority 3 — Verify the soil class coding** against SoilGrids documentation
(§16.7). If wrong, only the lookup table in `criteria.py` needs changing.

**Priority 4 — Finer input layers.** Sentinel-2-derived land cover at 10 m
instead of MODIS at 500 m would be the largest single quality improvement.

**Priority 5 — DEM-derived drainage network** by flow accumulation, replacing
HydroRIVERS. Would capture the smaller channels that matter for small structures
— but requires a working DEM and recalibration of the density class breaks.

**Priority 6 — A learned suitability model.** Using the same criteria stack as
features and the structure inventory as labels, compared against AHP. Blocked on
Priority 1. Scoped in `TODO.md` §C2 as "Sprint 4".

**Priority 7 — Additional MCDA methods** — PROMETHEE, VIKOR — to extend the
comparison.

**Priority 8 — Land value and construction-cost data** to turn "low-earthwork
siting" into a genuine cost scenario.

**Priority 9 — Automated PDF report generation.** Scoped but never implemented;
the export functions cover most of the need.

**Priority 10 — Temporal analysis.** Running per-decade rainfall to see how
suitability shifts under changing climate.

---

# 18. VIVA / FINAL PRESENTATION QUESTION PREPARATION

Twenty-five questions likely to be asked about *this* implementation.

---

### Q1. Why AHP? Why not just assign weights directly?

**Short answer.** Because people are bad at assigning weights directly but good at
pairwise comparison. AHP asks only "is rainfall more important than slope, and by
how much?" and derives the weights mathematically — plus it gives a consistency
check that direct assignment cannot.

**Detailed.** With six criteria, direct assignment means holding six numbers in
mind simultaneously and making them sum to 1. AHP decomposes this into 15 binary
judgements, each cognitively simple. The geometric-mean priority vector then
extracts a weight vector. Critically, AHP can *detect* contradiction: if you say A
is twice B, B twice C, but A five times C, the consistency ratio rises. Direct
assignment has no such check.

**Evidence.** `ahp.py` — the matrix, `calculate_weights()`,
`_calculate_consistency_ratio()`. Our CR = 0.0235, well under 0.10.

**Confidence.** High. Standard, well-supported by literature.

---

### Q2. Your CR is 0.0235. Does that mean your weights are correct?

**Short answer.** No — and this is an important distinction. CR measures internal
*consistency*, not *correctness*. You can be perfectly consistent and perfectly
wrong. That is exactly why we built three sensitivity analyses.

**Detailed.** CR checks whether your judgements contradict each other
transitively. It says nothing about whether rainfall really should outrank slope.
The honest answer to "your weights are subjective" is not a defence — it is a
measurement. Ours shows ±20% variation retains 90% of the top-10 sites, and map
removal shows which criteria actually drive the result.

**Evidence.** `sensitivity.py` — all three analyses. §14.4.

**Confidence.** High. This is the strongest answer in the project — volunteer it
rather than waiting to be pushed.

---

### Q3. What was your learning rate / batch size / number of epochs?

**Short answer.** None of those exist. Our system contains no trained model — it
is a knowledge-driven model, not a data-driven one. That is a deliberate choice,
not an omission.

**Detailed.** Learning rate, batch size and epochs are parameters of gradient-based
optimisation, which requires labelled training examples. We have none — there is
no register of existing RWH structures in Chandrapur to learn from. A
knowledge-driven model encodes published science and expert judgement directly, so
it works precisely where inventories are unavailable, which is most of rural
India. Its weakness is subjectivity, which is what our sensitivity analyses
measure. The only "learned" quantity is the AHP priority vector, and that is a
closed-form geometric mean of a hand-specified matrix — deterministic arithmetic.

**Evidence.** No ML library is installed [VERIFIED]. §7.6 explains the framing.
A learned model is scoped as future work in `TODO.md` §C2, blocked on the same
missing data.

**Confidence.** High. Answer it confidently — the framing is standard in
suitability-mapping literature.

---

### Q4. How do you know your system works, if you have no accuracy figure?

**Short answer.** We separate two questions. *Does the software do what we
designed?* — yes, verified by an 11-check automated end-to-end test and several
internal cross-checks. *Is the map accurate against reality?* — we cannot say,
because the ground-truth data does not exist, and we refuse to report a number we
cannot support.

**Detailed.** Verification evidence: the smoke test drives the real application
and asserts rank monotonicity, export availability and every analysis panel;
measured district area matches the official figure to 99.7%; river length is
conserved to 0.08% through the density computation; the consistency ratio passes.
For the accuracy question, the harness is written and its arithmetic verified —
it reports `missing_data` and refuses to invent a value. What we offer instead is
consensus: 15 of 36 locations chosen independently by all four methods.

**Evidence.** `tools/smoke_test.py` — 11/11 passing [VERIFIED]. §15.

**Confidence.** High for verification, and the honesty about validation is a
strength. Do not be defensive.

---

### Q5. Why six criteria? Why not more or fewer?

**Short answer.** These six were selected by combining frequency across the
reviewed literature with real-world applicability, and they span all the relevant
dimensions: terrain, soil, climate, hydrology, land use and human demand.

**Detailed.** Slope and rainfall appear in nearly every reviewed paper; soil,
land cover and drainage density in most; population in fewer but it is what makes
a site useful rather than merely feasible. Adding more criteria that correlate
with existing ones would double-count — which is exactly why runoff is computed
but deliberately excluded from the weighting (it is a function of land cover, soil
and rainfall, all already weighted).

**Evidence.** `ahp.py` criteria list; `derived_maps.py` docstring explains the
runoff exclusion explicitly.

**Confidence.** Medium-high on the mechanism. ⚠ The literature-frequency claim is
[DOC] from the presentation's review — **verify the individual papers before
asserting counts.**

---

### Q6. Why is drainage density weighted only 0.093 if it is so important?

**Short answer.** That is exactly the interesting finding. Its assigned weight is
fourth of six, but removing it destroys 8 of the top 10 sites — the largest
shortlist disruption of any criterion. Weight magnitude and actual influence are
different quantities.

**Detailed.** Two independent analyses agree. Map removal: dropping drainage
changes the surface by only 4.28% (fourth of six) but leaves 2/10 sites standing,
worse than dropping slope (8.98% surface change, 9/10 retained). Effective-weight
analysis: drainage contributes 6.61% against its assigned 9.32%, a ratio of 0.71,
because district density is low. The explanation is spatial variance — drainage
varies most across the district, so it is what separates otherwise near-identical
candidates. It barely moves the *map* but almost completely reorders the
*shortlist*.

**Evidence.** §14.4, both tables [VERIFIED]. `python sensitivity.py`.

**Confidence.** High. Two independent methods agree. This is one of the project's
best findings — lead with it.

---

### Q7. Why fixed thresholds of 0.65 and 0.85? Were they optimised?

**Short answer.** They were chosen by reasoning, not optimised — and we should say
so. What matters is that they are *fixed* rather than percentile-based, because a
percentile split always reports about a third of any district as suitable
regardless of the data.

**Detailed.** The reasoning: High ≥ 0.85 means a weighted average sitting in the
upper class of essentially every criterion — a site there fails none badly. The
alternative we replaced, a 33rd/67th percentile split, returned 32.9/34.0/33.1 —
a number that is a property of the method, not a finding. With fixed thresholds
the reported 18.51% is a real, comparable measurement, and it is comparable across
scenarios (which range 18.5–30.1%) and algorithms (12.9–18.5%).

**Evidence.** `criteria.SUITABILITY_THRESHOLDS`; the percentile mode is still
available via `CLASSIFICATION_MODE` for comparison. §9.6.

**Confidence.** High on the fixed-vs-percentile argument. ⚠ **Be honest: the
specific values 0.65 and 0.85 were not optimised against any objective.**

---

### Q8. Why a 2.5 km window for drainage density?

**Short answer.** A 1 km window over a 300 m grid is only about 3×3 cells, which
produces a noisy speckled surface. 2.5 km covers roughly 20 km² — smooth enough to
be a usable field, small enough to still resolve variation within the district.

**Detailed.** Window size is a smoothing choice. Too small and you get noise
driven by whether one river happens to clip a cell; too large and the whole
district converges to its mean, destroying discrimination. 2.5 km was chosen by
reasoning about the ratio to cell size.

**Evidence.** Reasoning documented in `criteria.py`
(`DRAINAGE_DENSITY_WINDOW_KM`). Resulting field has local values 0.00–0.85 around
a district mean of 0.242 — good discrimination [VERIFIED].

**Confidence.** Medium. ⚠ **The reasoning is sound and documented but no formal
window-size sweep was performed. Say that if pushed.**

---

### Q9. Why do you use different resampling for different layers?

**Short answer.** Because averaging category codes is meaningless. Averaging soil
class 4 and class 6 gives 5, which may not exist and certainly does not mean
"halfway between Silt Loam and Sandy Clay Loam". Continuous layers use bilinear;
categorical layers use nearest neighbour.

**Detailed.** Bilinear interpolation is correct for slope, rainfall and population
because those are genuinely continuous quantities where an intermediate value is
meaningful. For soil and land cover the numbers are labels, not magnitudes.
Nearest-neighbour copies the label of the closest source cell, which preserves
category validity. Getting this wrong invents classes that do not exist in the
data.

**Evidence.** `gis_analysis.build_criteria_stack()` — `raster_config` sets
`'resampling'` per criterion, with the reason in a code comment. `score_categorical`
additionally rounds to the nearest integer to absorb floating-point drift.

**Confidence.** High. This is a correctness issue with a clear right answer.

---

### Q10. Why is Silt Loam scored higher than Sand? Sand drains fastest.

**Short answer.** Because our objective is groundwater recharge, not drainage.
Sand infiltrates fastest but retains nothing and gives poor structural stability
for an embankment. Silt Loam gives the best balance of infiltration and retention.

**Detailed.** An RWH structure needs to hold water long enough for it to percolate,
and needs ground that will support a bund. Pure sand fails both: water passes
through too fast to be captured usefully by a surface structure, and sandy ground
makes poor embankment material. Heavy clay fails the opposite way — it impedes the
recharge we are trying to achieve. The middle textures win.

**Evidence.** `criteria.SOIL_TEXTURE_SCORES` with reasoning in comments;
`docs/METHODOLOGY.md` §3.

**Confidence.** High on the reasoning. ⚠ **Caveat you should volunteer: the
class-code-to-name mapping itself is unverified against SoilGrids documentation
(§16.7). If the coding is different, the table needs remapping — but nothing else
in the pipeline changes.**

---

### Q11. Why does population peak at 1–5 km rather than being closest-is-best?

**Short answer.** Because both extremes are bad. Inside a settlement you cannot
build — the land is impervious, expensive and contaminated. Too far away and there
is no demand to serve. The optimum is a set-back band.

**Detailed.** This required a different mathematical shape from the other five
criteria: a moderate-optimal curve rather than a monotonic ramp. Score 0.05 inside
a settlement, rising to 0.97 at 1 km, peaking at 1.00 at 3 km, back to 0.97 at
5 km, falling to 0.10 by 15 km. The peak is a gentle curve rather than a flat
plateau specifically so that sites within the band can still be ranked against each
other — a flat top was a major source of tied sites.

**Evidence.** `criteria.moderate_optimal()` and `SETTLEMENT_PEAK_KM`. The original
"lower population is better" logic was corrected on 29 July 2026.

**Confidence.** High on the shape. ⚠ **Medium on the specific 1–5 km values —
expert judgement, not fitted. Our OSM diagnostic actually hints structures may sit
closer to villages than this assumes (§15.5), which we have logged as an open
question. Volunteering this shows rigour.**

---

### Q12. What happens if you change the 400 people/km² settlement threshold?

**Short answer.** It changes what counts as a settlement, which shifts the entire
distance field and therefore the settlement criterion. At 400 it classifies 6.6%
of the district as settlement, which matches the built-up footprint well.

**Detailed.** Lowering the threshold would classify more rural cells as
settlements, shrinking distances everywhere and pushing more of the district into
the low-scoring "too close" region. Raising it would recognise only large towns,
making most of the district appear remote and score near the 0.10 floor. The
criterion carries only 0.040 of the weight, so the effect on the *map* is small —
our map-removal analysis shows removing it entirely changes the surface by 1.78%
and retains 9 of 10 sites. The effect on near-village *ranking* would be larger.

**Evidence.** `criteria.SETTLEMENT_DENSITY_THRESHOLD`; 6.6% measured [VERIFIED];
map removal row for settlement [VERIFIED].

**Confidence.** High on the measured consequences. ⚠ **No threshold sweep was
performed — the 400 value was chosen because it produced a settlement share
matching the built-up footprint.**

---

### Q13. Why TOPSIS as well as WLC? Isn't one method enough?

**Short answer.** Because comparing them produced our most novel finding: the
aggregation rule matters far more than the weighting rule. That would have been
invisible with one method.

**Detailed.** WLC is fully compensatory — high rainfall can fully offset poor
slope. TOPSIS is less compensatory — it squares the shortfall from the ideal, so
being weak on any high-weight criterion hurts disproportionately. These encode
genuinely different planning philosophies. Running both on an identical criteria
stack isolates that choice. The result: WLC → TOPSIS moves the highly-suitable
area ~5 percentage points and drops class agreement to 75%; AHP → Fuzzy-AHP moves
it 0.2 points at 98.7%. Many published papers compare only weighting methods — they
may be comparing the less consequential choice.

**Evidence.** §14.3 [VERIFIED]. `python algorithms.py`. The architectural split
guarantees the stack is identical across methods.

**Confidence.** High. This is the paper's headline.

---

### Q14. Where is your train/test split?

**Short answer.** There isn't one, and there shouldn't be. Splitting data is a
machine-learning concept for checking whether a model learned a real pattern. We
have no model that learns — we have published rules applied uniformly. There is
nothing to overfit and nothing to withhold.

**Detailed.** Every scoring rule comes from literature and physical reasoning, not
from our data. The rules would be identical if we had analysed a different
district. The one place a split *would* apply is accuracy validation against
known structures, which uses a presence-only design with random background
sampling — implemented in `validation._background_points()`, but blocked on data.

**Evidence.** §6.3, §7.6. No ML library installed [VERIFIED].

**Confidence.** High.

---

### Q15. Why did you remove the natural-language query feature from your original scope?

**Short answer.** It added no analytical value. We judged the effort better spent
on methodological correctness, and that judgement produced the findings we are
presenting today.

**Detailed.** The query layer would have been an interface convenience over an
analysis that, at the time, had three serious defects: min–max normalisation had
flattened two criteria and inverted two others, classification was self-fulfilling,
and drainage measured the wrong quantity. Fixing those was the higher-value work.
Removed 29 July 2026 and recorded in the changelog.

**Evidence.** `CHANGELOG.md` 2026-07-29 §M.

**Confidence.** High. Presenting a removed feature as a deliberate scope decision
with a rationale is much stronger than presenting it as unfinished.

---

### Q16. Your top five sites are all the same soil and land-cover type. Isn't that suspicious?

**Short answer.** It is the model behaving consistently — Silt Loam and Cropland
both score 1.00, so cells with both start ahead. But you are right that it
concentrates the shortlist in one landscape type, and that is a legitimate
limitation of compensatory aggregation.

**Detailed.** With WLC, a cell scoring 1.00 on soil (0.154 weight) and 1.00 on land
cover (0.060) has a 0.214-weight head start. If those two classes co-occur
spatially — which they do, in the cropland belt — the top of the ranking will be
dominated by that combination. TOPSIS partially counteracts this by penalising
weakness rather than rewarding strength, which is one reason its High class is
5 points smaller. The consensus analysis is the practical mitigation: it shows
which sites survive across both aggregation philosophies.

**Evidence.** §14.2 [VERIFIED]. Weight table §7.4. Algorithm comparison §14.3.

**Confidence.** High on the mechanism. [INFERRED] on the spatial co-occurrence
claim — it follows from the results but was not separately measured.

---

### Q17. What if one of your data layers were unavailable?

**Short answer.** The system handles it automatically — the criterion is excluded
and the remaining weights renormalise. We also measured exactly what happens for
each layer, which is what the map-removal analysis is.

**Detailed.** Two mechanisms. At load time, a missing file produces a warning note
and the criterion is dropped; `score_stack` renormalises. At cell level, missing
data triggers per-pixel weight renormalisation, subject to the 80% coverage gate
so a cell is never scored from a thin subset. Quantitatively: losing rainfall
would leave 1 of the top 10 sites and inflate the High class to 42%; losing land
cover or soil would leave 10 of 10 standing.

**Evidence.** `build_criteria_stack()` missing-file branches; `_weighted_overlay()`
coverage gate; §14.4 map-removal table [VERIFIED].

**Confidence.** High — this was measured, not speculated.

---

### Q18. Why compute in latitude/longitude rather than a projected system?

**Short answer.** Because the inputs arrive in mixed projections and must be
unified anyway, and 4326 keeps outputs in the coordinates users expect. We then
correct explicitly for the fact that degrees are not distances.

**Detailed.** Three corrections. Cell size in kilometres is evaluated at the
grid's centre latitude. Cell *area* is computed per raster row, so area statistics
account for cells narrowing toward the north. Distance transforms are anisotropic,
with the differing N–S and E–W spacings passed to SciPy explicitly. The check
that this is right: our measured district area is 11,412.5 km² against an official
11,443 km² — 99.7%.

**Evidence.** `_pixel_size_km()`, `_pixel_area_km2_per_row()`, `_distance_km()`
with `sampling=`. Area cross-check [VERIFIED].

**Confidence.** High — validated against an external reference.

---

### Q19. Why Streamlit rather than a proper web framework?

**Short answer.** The analysis is a pure function of files on disk, with one user
at a time and no persistent state. A Flask/React stack would add an API layer, a
build system and state management without adding capability.

**Detailed.** We considered a QGIS plugin (requires users to install QGIS,
restrictive plugin API), Flask + React (substantial extra machinery for no gain
here), and a Jupyter notebook (good for analysis, poor as a deliverable for a
planner). Streamlit gives a browser UI with an interactive map from pure Python.
The trade-off is that it re-runs the whole script on every interaction — which is
why results are cached in session state and why our stack cache matters.

**Evidence.** `app.py`; §9.13.

**Confidence.** High as an engineering decision appropriate to scope. Be clear
this is a research prototype, not a production deployment.

---

### Q20. Your grid is 300 m but rainfall is 5 km. Isn't that misleading?

**Short answer.** Yes, and we list it as a limitation. The output is drawn finer
than three of its six inputs. Finer output does not mean finer information.

**Detailed.** Land cover is ~463 m, population ~900 m, rainfall ~5.3 km. The grid
resolution is set by the need to resolve slope and drainage variation, which are
genuinely fine-scale; the coarser layers are simply resampled up and contribute
smoothly varying values. This is honest as long as it is stated: the rainfall
criterion cannot distinguish two sites 1 km apart, and our effective-weight
analysis shows exactly that — rainfall contributes 0.80× its assigned weight
partly because it is spatially smooth.

**Evidence.** Resolutions [VERIFIED] §6.1. §16.2. Effective weights §14.4.

**Confidence.** High. Volunteer this rather than being caught by it.

---

### Q21. What is the Borda count and why use it for consensus?

**Short answer.** It converts each method's *ranking* into points — a site ranked
r of N gets N − r + 1 points — and sums across methods. It rewards locations that
several methods rank highly, not just locations that appear on several lists.

**Detailed.** A simple count of "how many methods picked this site" treats a
first-place pick the same as a twenty-fifth-place pick. Borda weights by position.
One deliberate detail: a method that did not select a site contributes **zero**,
not a low score — because a method staying silent about a site is not evidence in
its favour. Sites are matched across methods by geographic position within 2 km,
not by rank, because each method extracts candidates independently and coordinates
shift slightly. 2 km sits well inside the 5 km minimum separation, so a cluster can
never absorb two distinct sites from one method.

**Evidence.** `consensus.consensus_sites()` with the reasoning in its docstring.

**Confidence.** High.

---

### Q22. Doesn't consensus just mean the methods share the same bias?

**Short answer.** Yes, that is a fair criticism and we state it. Consensus measures
agreement, not correctness — four methods can agree and all be wrong together,
because they share the same criteria stack and the same scoring tables.

**Detailed.** What consensus does rule out is that a site is an artefact of one
particular aggregation rule or one particular weighting. What it cannot rule out is
a shared error upstream — a wrong soil coding, say, would mislead all four
identically. That is why we are explicit that consensus is a *substitute for*
validation only in the sense of being the strongest ground-truth-free evidence
available, not a replacement for it.

**Evidence.** §9.11 trade-offs; §15.6.

**Confidence.** High. Conceding this properly is stronger than defending it.

---

### Q23. Why 25 sites and 5 km separation?

**Short answer.** 5 km because two structures closer than that harvest overlapping
catchments, so they are not genuinely distinct options. 25 because it is a
shortlist a planner can actually work through.

**Detailed.** The separation constraint is the substantive one. Without it, the top
25 cells would cluster in one favourable belt and offer no real choice. There is a
visible consequence worth explaining during the demo: a large High-suitability
zone may contain only one or two markers, so a viewer sees High areas with no site
in them. That is the constraint operating, not a bug.

**Evidence.** `DEFAULT_MIN_SEPARATION_KM = 5.0`, `DEFAULT_TOP_N = 25`;
`_extract_top_locations()` haversine check.

**Confidence.** Medium-high on the reasoning. ⚠ **Neither value was formally
optimised; both are planning judgements.**

---

### Q24. You found bugs in your own system. Doesn't that undermine the results?

**Short answer.** The opposite — finding them is why the current results can be
trusted. Each one was found by checking the system's output against what it should
logically produce, and each is now guarded.

**Detailed.** Three examples. Every top site scored identically, which traced to
flat-topped scoring; fixing it raised distinct scores from 47,495 to 108,229.
Rank #22 outscored rank #13, which traced to ranks following selection order across
two extraction stages; fixed, and the smoke test now asserts rank monotonicity on
every run. Fuzzy-AHP returned weights identical to crisp AHP, which traced to
multiplicative fuzzification cancelling under normalisation — had we not caught it,
our algorithm comparison would have contained a false claim.

**Evidence.** `CHANGELOG.md` entries for 8 and 12 August 2026; the regression check
in `tools/smoke_test.py` [VERIFIED passing].

**Confidence.** High. Present this as evidence of rigour, not as an apology.

---

### Q25. What would you do with another six months?

**Short answer.** Ground-truth validation first — the code is already written and
it would unblock three other things simultaneously. Then re-export the input layers
with a 20 km buffer, which fixes a real limitation and requires no code change at
all.

**Detailed.** Assembling 150–300 structure locations would immediately produce an
accuracy figure, a per-algorithm ranking answering "which method is best", and the
labels needed for the machine-learning comparison. Second priority is the buffered
re-export, which removes the edge effect currently affecting 8 of our 25 candidate
sites including rank #1 — a QGIS operation, no code change. Third is verifying the
soil class coding. Fourth is finer land cover from Sentinel-2 at 10 m instead of
MODIS at 500 m.

**Evidence.** §17.2; `TODO.md`; `validation.py` already complete.

**Confidence.** High.

---

# 19. IMPORTANT PARAMETERS — QUICK REFERENCE

⚠ **None of these was formally optimised against an objective function.** Each was
chosen by reasoning from physical principles, literature, or dataset
characteristics, and each has its justification recorded in `criteria.py` or
`docs/METHODOLOGY.md`. **Say this if asked** — see §16.12.

## 19.1 Scoring parameters (all in `criteria.py`)

| Parameter | Value | Purpose | Why chosen | If changed |
|---|---|---|---|---|
| `SLOPE_RAMP_DEG` | 0°→1.00 … 25°→0.08, 90°→0.05 | Slope score | Break points from RWH engineering practice; interpolated so slopes rank | Flatter ramp reduces slope's discriminating power; slope currently contributes 1.29× its assigned weight |
| `SOIL_TEXTURE_SCORES` | Sand 0.55, Silt Loam 1.00, S.Clay Loam 0.80, Silt Clay Loam 0.50 | Soil score | Recharge needs infiltration **and** stability, not maximum infiltration | Ranking Sand first would push sites to poorly-buildable ground |
| `LULC_SCORES` | Cropland 1.00 … Water/Snow 0.00 | Land-cover score | Demand + acquisition cost + buildability; forest low because Chandrapur's is protected | Raising forest would propose sites where construction is restricted |
| `RAINFALL_FLOOR` | 0.20 | Driest cell's score | Prevents the driest cell scoring 0 and vetoing an otherwise good site | Lower → rainfall behaves closer to a veto |
| `DRAINAGE_DENSITY_WINDOW_KM` | 2.5 | Density smoothing window | 1 km ≈ 3×3 cells → speckle; 2.5 km ≈ 20 km² → smooth but still varying | Smaller → noisy; larger → converges to district mean, losing discrimination |
| `DRAINAGE_DENSITY_RAMP` | 0.00→0.10 … 0.90→1.00 | Density score | **Calibrated to HydroRIVERS**, district density 0.242 km/km² | ⚠ Must be recalibrated if the river network is ever re-derived from a DEM |
| `SETTLEMENT_DENSITY_THRESHOLD` | 400 people/km² | Defines a settlement | Classifies 6.6% of the district, matching the built-up footprint | Lower → more cells "too close"; higher → district appears remote |
| `SETTLEMENT_PEAK_KM` | (1, 5) km | Optimal band | Close enough to serve, far enough to avoid built-up land and cost | Wider flattens the criterion; OSM diagnostic hints it may be too far out |
| `SETTLEMENT_FALLOFF_KM` | 10 km | Decay beyond the band | Reaches the floor at 15 km total | Longer → remote areas stay competitive |
| `band_edge` | 0.97 | Score at band edges | Makes the peak gentle, not flat — enables ranking within the band | 1.00 would restore flat-top ties |
| `SATISFIED_THRESHOLD` | 0.66 | "Criterion satisfied" flag | Roughly two-thirds of the scale — display only, affects no computation | Purely presentational |

## 19.2 Aggregation and classification

| Parameter | Value | Purpose | Why chosen | If changed |
|---|---|---|---|---|
| `MIN_WEIGHT_COVERAGE` | 0.80 | Minimum weight with data before a cell is scored | Stops an edge cell scoring 1.00 from 2 of 6 criteria | Lower → unreliable edge cells enter the ranking; higher → district shrinks |
| `SUITABILITY_THRESHOLDS` | (0.65, 0.85) | Low/Medium/High breaks | Fixed so the reported area is a real measurement, not a method artefact | Raising 0.85 shrinks the High class; percentile mode would force ~33% |
| `CLASSIFICATION_MODE` | `"fixed"` | Threshold type | Percentile splits are self-fulfilling | `"percentile"` makes all scenario/algorithm comparisons meaningless |
| TOPSIS ideals | Theoretical (1 and 0) | Reference points | Observed extremes would make scores data-range dependent | Observed ideals break cross-scenario comparability |
| `FUZZY_DELTA` | 1.0 | ±1 Saaty step in Fuzzy-AHP | Standard fuzzy Saaty scale: 3 → (2,3,4) | Larger → wider fuzzy ranges; **multiplicative spread cancels entirely** |

## 19.3 Grid and site extraction (`gis_analysis.py`)

| Parameter | Value | Purpose | Why chosen | If changed |
|---|---|---|---|---|
| `DEFAULT_MAX_GRID_SIZE` | 450 px | Longest grid side | ~300 m cells — resolves slope/drainage variation at interactive speed | Higher → finer but slower and no more input information; lower → loses detail |
| Analysis CRS | EPSG:4326 | Common grid | Avoids a second resampling; distances corrected explicitly | UTM would simplify distances but add a resampling step |
| Resampling | bilinear / nearest | Continuous / categorical | Averaging class codes invents categories | Bilinear on categories corrupts soil and land cover |
| `DEFAULT_TOP_N` | 25 | Candidate sites | A shortlist a planner can work through | More → longer tail of marginal sites |
| `DEFAULT_MIN_SEPARATION_KM` | 5.0 | Minimum spacing | Closer structures share a catchment | Smaller → clustered, less distinct options |
| Tile grid | 5 × 5 | Stage-1 spread | Forces geographic coverage instead of one favourable belt | Finer → more spread, less score-driven |
| Tie-break coefficient | 1e-3 | Orders tied cells | Large enough to break ties, too small to reorder distinct scores | Larger would let the tie-breaker override real score differences |
| River densification | 100 m | Segment length | Fine enough for true length; verified 0.08% loss | Coarser → length error rises |

## 19.4 Analysis parameters

| Parameter | Value | Purpose | Why chosen | If changed |
|---|---|---|---|---|
| Sensitivity δ | ±20% (UI: 10/20/30) | Perturbation size | A meaningful but plausible expert disagreement | Larger δ → lower retention; the UI lets you see this |
| Sensitivity top-N | 10 | Retention measured on top 10 | The sites a planner would actually act on | Larger N → retention rises as marginal sites shuffle |
| Site match radius | 2.0 km | Cross-run matching | Inside the 5 km separation, so never ambiguous | Larger risks matching two distinct sites |
| `DEFAULT_STORM_MM` | 100 mm | Runoff design storm | ~1-day design event for a monsoon district; annual total collapses all land covers to the same value | Larger → higher coefficients across the board |
| SCS-CN condition | AMC II, good | Curve Number basis | Average antecedent moisture — the standard default | AMC III (wet) would raise runoff substantially |
| `BUFFER_DEG` | 0.20° | CHIRPS read margin | Ensures rainfall reaches the boundary without gap filling | Zero → rainfall needs gap filling like the other layers |
| `NODATA_CUTOFF` | −100.0 | CHIRPS fill detection | CHIRPS ships −9999 **undeclared** in the header | Omitting it makes −9999 a real rainfall value |
| `DEFAULT_BACKGROUND_MULTIPLIER` | 5 | Background points per positive | Standard presence-only practice | Affects AUC variance — **untested, no data** |
| `RANDOM_SEED` | 42 | Reproducible sampling | Same background points every run | Only affects the unused validation path |

## 19.5 Reproducing every number in this document

```bash
python -c "from gis_analysis import run_ahp_analysis; r=run_ahp_analysis('data'); print(r['area_statistics'])"
python sensitivity.py         # §14.4 — all three analyses
python algorithms.py          # §14.3 — four-algorithm comparison
python consensus.py           # §14.5 — both consensus axes
python derived_maps.py        # §14.7 — hydrological surfaces
python exports.py             # site table + map figure
python validation.py          # reports missing_data, by design
python tools/smoke_test.py    # §15.1 — 11 checks
python tools/inspect.py data/<file>
streamlit run app.py
```

---

# 20. FINAL PROJECT SUMMARY

**The problem.** Chandrapur district receives ample monsoon rain yet suffers water
scarcity, because the rain arrives in a short season and most of it runs off.
Rainwater harvesting helps, but a structure in the wrong place wastes money.
Choosing well means combining six different judgements about every location across
11,400 km² — infeasible by hand. Beneath that practical problem sits a
methodological one: the standard way of combining map layers has weaknesses that
make results non-transferable, untested and method-dependent.

**The objectives.** Integrate multi-source spatial data; derive six criterion
layers; weight them by AHP with a verified consistency check; produce a classified
suitability map and a ranked shortlist with per-site justification; and quantify
how much the answer depends on the choices made.

**The solution.** A six-criterion GIS-MCDA system in Python with a browser
interface. Every score comes from a fixed, physically justified table rather than
the observed data range. Weights come from AHP (CR = 0.0235). The result is
stress-tested four independent ways, none of which requires data the project does
not have.

**The architecture.** A single-process scientific application, split into a cached
weight-independent stage (grid, reprojection, gap filling, derived criteria,
scoring — ~0.90 s) and a cheap weight-dependent stage (aggregation,
classification, site extraction — ~0.15 s). That split makes scenario switching
feel instant *and* guarantees every method comparison runs on identical inputs.

**The methodology.** Four normalisation forms matched to the physics of each
criterion; AHP and Fuzzy-AHP weighting; WLC and TOPSIS aggregation with per-pixel
renormalisation and an 80% coverage gate; fixed-threshold classification;
three-stage candidate extraction; and four robustness analyses.

**The final features.** Suitability mapping · 25 ranked sites · per-site
explainability · side-by-side comparison · five scenarios · editable pairwise
matrix · four selectable algorithms · algorithm comparison · three sensitivity
analyses · consensus analysis · five export formats · derived hydrological
surfaces · data inspection tool · automated smoke test.

**The results.** High suitability covers **18.51% (2,112.6 km²)** of the district;
25 sites ranked 0.984 to 0.866. The headline finding: **the aggregation rule
matters far more than the weighting rule** — WLC → TOPSIS moves the highly-suitable
area ~5 percentage points at 75% class agreement, while AHP → Fuzzy-AHP moves it
0.2 points at 98.7%. Robustness: ±20% weight variation retains 90% of the top-10
sites. Two independent analyses agree that **drainage carries only 9.3% of the
weight but its removal destroys 8 of the top 10 sites** — assigned weight and real
influence are different quantities. Fifteen of 36 proposed locations were selected
by all four algorithms, and 1,417 km² was classed highly suitable by every one.

**The major decisions.** Fixed reclassification instead of min–max (fixed a defect
affecting ~48% of the decision weight); drainage density instead of
distance-to-river; a moderate-optimal settlement band instead of a monotonic
population criterion; fixed classification thresholds instead of a self-fulfilling
percentile split; theoretical TOPSIS ideals for comparability; Buckley's Fuzzy-AHP
with an additive scale after discovering that multiplicative fuzzification cancels
entirely; and a cached two-stage architecture that makes the method comparison
scientifically valid rather than merely fast.

**The limitations.** No accuracy validation — the harness is written but the
ground-truth inventory does not exist, and we report no number we cannot support.
Inputs are coarser than the output grid. Distance-based criteria are blind to
features just outside the district, affecting 8 of 25 sites. The drainage network
understates small channels. The soil class coding is unverified. No parameter was
formally optimised. The weights remain expert judgement — bounded by measurement,
not eliminated.

**The significance.** Most comparable work produces a map. This produces a map,
a shortlist, an explanation for every site, and a measurement of how much the whole
thing can be trusted. The scoring tables transfer to any district. The finding that
aggregation dominates weighting is a genuine contribution to how such studies
should be designed. And the project is honest about what it has not established —
which is itself the strongest thing it can say about what it has.

---

# INFORMATION REQUIRING CONFIRMATION

Verify these personally before the presentation. Each could be challenged and none
can be settled from the repository alone.

## Critical — could invalidate a criterion

**1. Soil texture class coding.** `criteria.py` maps codes 1, 4, 6, 7 to Sand,
Silt Loam, Sandy Clay Loam and Silt Clay Loam, and the source file carries an
explicit warning that standard SoilGrids USDA texture coding (TEXMHT) numbers
classes differently (1 = clay … 12 = sand). **If our mapping is wrong, the soil
criterion — 15.4% of the decision weight — is wrong.** Check the metadata of the
file you actually exported from QGIS. If it needs remapping, only the dictionary
in `criteria.py` changes.

**2. `data/dem.tif` contains no valid pixels.** Verified empty at four separate
windows. No analysis module reads it, so nothing is broken — but it means the
documented provenance of `slope.tif` (HydroSHEDS CONDEM → GDAL Slope) **cannot be
verified from the repository.** Confirm where `slope.tif` actually came from, and
either replace or delete the empty DEM. Its cell size (88 × 91 m in EPSG:32644) is
consistent with a ~90 m source, which supports the documented story — but that is
inference, not proof.

## Important — affects what you can claim

**3. Literature review claims.** The statement that slope and rainfall appear in
nearly all reviewed papers, the "19–34% suitable in comparable studies" comparison,
and the eight cited domain papers are all recorded in project documentation but
**cannot be verified from the repository**. Re-read the papers before repeating any
of it. This matters most for §14.1 and Q5.

**4. Official district area (11,443 km²) and population (2,204,307; 193/km²).**
Used as external reference points. Both are [DOC] from the presentation, not
present as data. Confirm the source and year.

**5. Per-year rainfall figures.** The wet-decade argument cites 2014, 2015 and
2017 near 1,220–1,260 mm against other years at 1,425–1,930 mm. Recorded from the
original build run, **not re-derived**. Re-run `python build_rainfall.py` and
capture its per-year output if you intend to quote these.

**6. Historical before-fix measurements.** The 97.4% / 97.7% min–max figures, the
973 tied cells, and the 47,495 distinct scores describe code that has since been
replaced and **are not re-measurable**. The corresponding *after* figures — 108,229
distinct scores, 1 cell at maximum — are verified. Present the before-figures as
"measured at the time" rather than as reproducible.

**7. Runtime figures.** The ~0.90 s / ~0.15 s / ~1.5 s timings come from project
documentation and were **not benchmarked** in this audit. Time one run yourself if
you plan to quote them.

## Housekeeping before the presentation

**8. A stale comment in `criteria.py`** claims the classification thresholds yield
"roughly 31% High / 46% Medium / 23% Low". The real figures are 18.51 / 54.79 /
26.70. Anyone reading the source would quote the wrong numbers. (Left unchanged —
you asked that no source files be modified.)

**9. Which rainfall figure you quote.** Three circulate, all correct for different
domains: **1,471.9 mm** (whole raster including the 0.20° buffer), **1,492.9 mm**
(district mean, in the file's own metadata — *prefer this one*), **1,500.3 mm**
(in-district after reprojection onto the analysis grid). Same for slope maximum:
72.21° whole raster, **56.04° in-district** — quote the in-district figure in
results.

**10. Presentation slides are out of date.** `TODO.md` §A4 lists what needs fixing
in `docs/BTech Major Project PPT (1).pptx`, including one slide that still says
drainage is computed as "distance-to-river using chamfer distance transform" and
another citing CHIRPS monthly 2024–2025 rainfall. Both are wrong in the current
system.

**11. Group member contributions.** Not recorded anywhere in the repository. If
the viva asks who did what, agree it among yourselves beforehand.
