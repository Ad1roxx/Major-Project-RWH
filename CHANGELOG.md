# Changelog

Dated record of changes to the project. This file stands in for git history
until the repository is initialised — **every change from here on should get an
entry**, so that the work is traceable when the project is written up.

Earlier history, reconstructed before this file existed, is in
[docs/archive/CHANGES_SINCE_INITIAL_ZIP.md](docs/archive/CHANGES_SINCE_INITIAL_ZIP.md).

---

## 2026-10-20 (night) — Draft v5 checks

- **Printed figure numbers updated** to the v5 numbering, and the figures
  regenerated:
  - fig04 "(Fig. 15)" is now "(Fig. 8)";
  - fig12 "see Fig. 21" is now "see Fig. A8", with values unchanged;
  - fig03 "(Fig. 5)" is now "(Fig. A2)".
- **CGWB parse fix:** shaft #94 wrapped across two PDF lines. Now 418 sites
  (150/112/156, matching the report). Validation re-run:
  - AUC 0.362 [0.341, 0.382] (was 0.361 [0.341, 0.383]);
  - shafts 0.337 (was 0.336);
  - everything else unchanged.
- **The v5 "unverified numbers" were recomputed** (`paper_pack_v5/V5_VERIFICATION.md`):
  - all match except the top latitude (20.730, not 20.731);
  - the §4.2.1 sentence attributes the 40–63 percentiles to the 200 pipeline
    runs, when they come from the 1,013 accepted matrices.

---

## 2026-10-20 (evening) — CGWB check, 2023 assessment, Table 2 coding, MODIS citation

- **CGWB NAQUIM report for Chandrapur (2021)**, downloaded to
  `data/raw/cgwb/` (PDF git-ignored; `PROVENANCE.md` has the facts and where
  they are):
  - the district is **Safe** at 19.35% (2017);
  - significant water-level decline over only 7% of the area;
  - artificial recharge judged **not feasible** in Jiwati, Mul, Nagbhir,
    Pombhurna, Saoli and Sindewahi.
  - Its 417 proposed recharge structures were parsed to
    `cgwb_proposed_ar_sites.csv`.
- **`tools/validate_mgnrega.py` now compares the model with those sites:**
  - AUC **0.361** [0.341, 0.383], below chance;
  - 70.3% of sites in Low, 1.0% in High;
  - the six infeasible blocks hold 43.1% of the High area and 13 of the
    top 25 sites.

  **The model disagrees with hydrogeological recharge siting** while
  agreeing with where MGNREGA works were built.
- **GSDA & CGWB, Dynamic Groundwater Resources of Maharashtra 2023,**
  downloaded to `data/raw/gsda/`: all 15 Chandrapur blocks Safe (17.7–44.6%);
  district **29.3%**, computed from the block rows.
- **Table 2 coded** against the full text of all eight papers
  (`paper_pack_v5/TABLE2_CODING.md`):
  - slope and land cover 8/8;
  - soil 6/8 explicit (7 incl. infiltration rate);
  - rainfall 5/8 explicit (7 incl. via runoff);
  - drainage density 5/8 (8 as any stream measure);
  - settlement 1/8 (2 incl. as a constraint).

  **The v4 "8 of 8" claims are false** for rainfall and for "five criteria".
- **MODIS citation:** Friedl & Sulla-Menashe (**2022**), doi
  10.5067/MODIS/MCD12Q1.061 (from the NASA Earthdata catalogue).
- **paper_pack_v5 updated:**
  - new `CGWB_FINDINGS.md`, which recommends reframing the objective as
    surface RWH suitability (decision pending);
  - new `TABLE2_CODING.md`;
  - the brief, reviewer responses, provenance and validation findings
    revised.
- **Decided:** Fig 6 keeps viridis. The target journal is deferred.
- **Later the same evening, pack updated with confirmed points only:**
  - **`CGWB_FINDINGS.md` §3b:** how CGWB chose its sites (depth-to-water
    filter > 3 m bgl, specific-yield space, surplus runoff budget, unit
    capacities; placement of individual points unpublished), and why the
    model should not be fitted to them.
  - **The structure-type table** for combining the two maps.
  - **The soil-ordering limitation.**
  - **Brief rules:** the weights are expert judgement, not literature
    frequency.
- **Clay-best soil test** run in memory only. Nothing saved, and by the
  authors' decision it is not reported in this draft.

---

## 2026-10-20 (later) — MGNREGA validation run; paper_pack_v5

### Validation (`tools/validate_mgnrega.py`, new)
- **Scope:** reads only. 20 surfaces (4 methods × 5 scenarios) against 3,119
  MGNREGA water works (WC/WH segments) and 10,000 uniform background cells.
  Every random step uses seed 42. Outputs go to `outputs/validation/`:
  - the numbers file, with provenance;
  - the filter ledger;
  - the category decisions;
  - the point tables (git-ignored);
  - the presences GeoPackage;
  - a summary JSON.
- **Metrics:**
  - ROC AUC with 2,000 bootstraps;
  - paired bootstrap and DeLong;
  - PR AUC;
  - Boyce (its null spread checked: mean 0.03, sd 0.26);
  - gain table, area-weighted;
  - robustness: 1 km thinning, settlement removal, single criteria,
    cropland-only, photo-confirmed subsets, permutation control.
- **Implementation:** metrics are implemented locally, with no scikit-learn
  dependency. They were checked against the trapezoid ROC area, the DeLong
  self-comparison (p = 1), and kappa on a known case.
- **Results:**
  - **Agreement:** baseline AUC 0.661 [0.650, 0.672]; all 20 surfaces
    0.629–0.715.
  - **Gain:** High holds 1.93× its area share of works, Low 0.52×.
  - **Methods:** WLC beats TOPSIS by 0.03, but all four tie at 0.670 within
    cropland. The weighting method moves AUC by 0.002, the scenarios by up
    to 0.049.
  - **Confounds:** removing settlement costs ≤ 0.004; works lie *farther*
    from settlements than background.
  - **Negative control:** 0.496.
- **Deviations, recorded in the output:**
  - no asset-type or status field exists;
  - PNG only.
- **New figures:**
  - `fig_val_roc`, `fig_val_scores`, `fig_val_gain` (matplotlib);
  - `fig_val_map` (QGIS, `tools/qgis_figures.py fig_val_map`).

### paper_pack_v5/ (new; `paper_pack/` kept as v4)
- `DRAFTING_BRIEF` (changes since v4, section edits, rules, placeholders).
- `VALIDATION_FINDINGS`, `FIGURE_INDEX` (28 figures, order, caption
  checklists), `REVIEWER_RESPONSES`, `DATA_PROVENANCE`.
- Regenerated `PAPER_NUMBERS.txt`, identical to v4's.
- The validation outputs, all figures, and the supporting documents.
- Every validation number the documents cite was checked against
  `VALIDATION_NUMBERS.txt` by script.

---

## 2026-10-20 — QGIS figures begin (Figure 7); taluka and river-name data

- **New `tools/qgis_figures.py`** builds print layouts with QGIS's own Python:

  ```
  "C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" -P tools/qgis_figures.py fig07
  ```

  It writes `outputs/figures/figNN.png` (300 dpi, 174 mm wide) and an editable
  `outputs/figures/qgis/figNN.qgz` with relative layer paths.
- **Two QGIS pitfalls found and handled:**
  - the offscreen Qt platform has no fonts on Windows and draws every glyph
    as a box, so the normal platform is used;
  - `QgsLayerTreeGroup.addChildNode` returns `None`, which crashed the legend
    code, so `addLayer` is used.
- **Figure 7, done** (spec in `docs/FIGURE_SPECS.md`):
  - (a) the classified surface in `CLASS_COLOURS`, rivers drawn thicker by
    Strahler order, the boundary, and the 25 sites labelled by rank, all
    shown;
  - (b) an inset on rank 1 (0.957) with the 5 km separation circle;
  - a graticule, scale bars, a north arrow, and a legend without the raster's
    band entry.
- **Figure 7, after external review:**
  - **Checked, not assumed:** all 25 sites sample class 3 (High). The
    "sites on Medium" look came from High patches smaller than the filled
    markers; rank 25 sits on a single High cell. Both map items are in
    EPSG:32644, so the projection note is correct.
  - **Fixes:**
    - hollow ring markers;
    - rivers dark grey (#555555), since blue means High;
    - the north arrow is the plain "N" style of `_add_north`, moved to the
      empty NW corner;
    - the inset box is 5.5 km, and labels near it take the far side;
    - labels are no longer forced. They may not go left (touching boxes read
      "2511"), and the run fails unless all 25 are placed;
    - exterior graticule ticks, a circular legend patch, matplotlib's DejaVu
      Sans, a finding title, and a two-line credit footer.
  - **Caption:** the spec's "one or two markers" sentence is replaced. The
    north-central belt carries seven sites; see `docs/FIGURE_SPECS.md`.
  - **Not done (optional):** marking ranks 23–25 as the non-unanimous sites of
    Fig. 22.
- **Fig 4 replaced by an illustrated framework,** at the professor's request,
  built entirely from model outputs (`tools/prep_map_layers.py` writes
  `score_*`, `raw_*` and `class_*` tifs, `agree4.tif` and `fig04.json`):
  - **Stage 1:** six raw inputs on the grid, in grey; then the six scored
    criteria in viridis, with their weights in the paper's criterion colours.
  - **Stage 2:** the judgement matrix feeds AHP and Fuzzy-AHP, giving a
    weights bar; then the four real method maps with their High shares; then
    the baseline map with 25 sites.
  - **Output cards:** robustness; consensus (all-four-High map, 528.5 km²,
    recomputed from the rasters); explainability (rank 1's contribution bar).
  - Scenarios are labelled as reported under AHP + WLC only, following
    `consensus.variants_by_scenario`.
  - The old box diagram is kept as `fig04_boxes.png` for a supplement.
- **Fig 4, second review:** the figure now carries the paper's finding.
  - **★ marks the three analyst decisions:** rainfall scoring, the judgement
    matrix, and the classification cutoffs.
  - **Panel (c) is a miniature of Fig 12,** with values parsed from
    `FIGURE_DATA.md`: cutoff scheme 36.43, rainfall scoring 31.21 and
    judgements 16.23 pp, against aggregation 0.957 and weighting method
    0.560. The review's "+26.53" for cutoffs is a superseded value.
  - **Pipeline accuracy:**
    - an explicit "aggregate → classify 0.65/0.85" step where the stack and
      the weights meet;
    - the 2 × 2 is labelled TOPSIS | WLC by AHP | Fuzzy-AHP;
    - AHP + WLC is outlined and alone feeds the baseline map;
    - the boundary is named as the seventh dataset.
  - **Scored criteria now in magma:** viridis blue clashed with High blue in
    the same figure.
  - **Consensus panel:** shows only "High under all four" (no grey specks)
    plus the 15 unanimous sites as rings.
  - **Explainability panel:** on an absolute 0–1 axis, with a hatched
    shortfall.
  - **Rank 1 contributions fixed:** they are now taken from the unrounded
    score rasters. The stored `criteria_scores` are 3-dp and summed to
    0.9563 against the true 0.9566, so the shortfall read 0.044; it is
    0.043.
  - The "88% of top 10" line is dropped; panel (c) replaces it.
  - Panels lettered (a)–(e); one-line title.
- **MODIS year found:** `data/lulc.tif` is MCD12Q1 v6.1, **2024**, from AppEEARS.
  It is identical, cell for cell, to the original download in `Downloads/`.
  Figure 3 now names the year, and `docs/METHODOLOGY.md` §4 records the
  provenance.
- **Fig 1, final cosmetics:** the district map moves right 4 mm so its
  latitude labels clear panels (b) and (c). The title now breaks between
  whole phrases.
- **Fig 4, third review** (publishable, pending print size):
  - (c) labels name each quantity: "range of 4", "1 swap", "range of 5",
    "main effect".
  - The "AHP · 6.44%" label is moved clear of its outline box.
  - "reproject" is restored in Stage 1.
  - The colour key in (b) and the redundant line in (e) are cut.
  - (e) labels the soil segment "Loam, 0.38% of district", with a leader.
  - **Open:** text is 5–6 pt at 174 mm. Raise it set-wide once the target
    journal's minimum is known.
- **Review fixes:**
  - **Fig 1:**
    - HQ squares are now label obstacles. "Erai" hid Chandrapur's square and
      "Sindewahi" its own; all 15 are now visible.
    - Cool-grey taluka fill (beige is reserved for Medium).
    - Legend in one row below the map.
    - Panels relettered: (a)–(c) left, (d) district.
    - The HQ source is credited, and the title reads "450 rows × 422 columns".
  - **Fig 3:**
    - GADM feeds the grid build, the five rasters feed reprojection, and
      HydroRIVERS (vector) goes straight to derivation.
    - A new "Score to 0–1" step names each criterion's actual form. It
      replaces the false "fixed, literature-based breakpoints" footer:
      rainfall is percentile-based.
    - Versions are on every source. **MODIS year is not recorded in the
      repo**, so the figure says v6.1 only.
  - **Fig 20:** the footnote moves to the caption.
  - **Verified:** CHIRPS v3.0, 2014–2024.
- **Fig 7, third review:** publishable. Rank labels now sit 1.15 mm from the
  ring. The "far side of the box" rule now applies only to sites outside the
  box, so rank 1 (inside it) labels top-right and its "1" no longer touches the
  ring in (b).
- **The remaining figures** (`docs/FIGURE_SPECS.md` has the status table):
  - **Fig 1:** India, Maharashtra, the talukas and the grid window.
  - **Figs 3, 4, 20:** drawn as QGIS layouts in the same font, with editable
    `.qgz`.
  - **Hydrology** (draft Fig 18): `fig_hydrology.png`.
- **New `tools/prep_map_layers.py`** (venv) writes the inputs to
  `outputs/figures/qgis/inputs/`:
  - the Maharashtra outline and districts (GADM);
  - the India outline (Survey of India, via DataMeet);
  - river label lines, using each name's longest continuous OSM piece;
  - the grid window;
  - `cn_class.tif` with area-weighted class shares.
- **Corrections found while building them:**
  - **Label check was wrong.** It counted labels that QGIS tried and failed
    to place (`isUnplaced`), so it passed with Andhari unlabelled. It now
    reads the labelling results of the export itself and counts placed labels
    only. Fig 7's 25 ranks pass under the corrected check.
  - **Fig 4's sketched flow misdescribed the method.** It had the stack
    feeding Fuzzy-AHP and the scenarios feeding aggregation. Redrawn as the
    code runs (`algorithms.weights_for_algorithm` → `score_stack`).
  - **Hydrology:** Q and C are deterministic in CN for the 100 mm storm, so
    their maps were the CN map relabelled. The figure shows two panels;
    CN 89 covers 62.6% of the area.
  - **Fig 1 grid window:** first placed on the grid's own edge, where a
    negative index wrapped silently. It is now centred inside the grid and
    fails loudly if it would leave it.
  - **Cell size, measured geodesically:** 0.296 km E–W × 0.313 km N–S. The
    paper's "0.31 × 0.30" is N–S × E–W; the figures state the directions.
  - **Extraction verified in code:** a 5 × 5 tile stage, then a fill stage,
    with ≥ 5 km separation in both. Only 12 tiles hold High land, so at least
    13 sites come from the fill stage. Fig 7's title now says "all ≥ 5 km
    apart", not "best per tile".
- **`data/raw/talukas/chandrapur_talukas_filled_to_boundary.geojson`:** the
  64 sliver gaps (97.8 km²) between the Census talukas and our GADM outline
  are each assigned to the taluka sharing the longest border.
- **`data/raw/talukas/`:** Census 2011 sub-districts via
  datta07/INDIAN-SHAPEFILES (MIT).
  - All 15 Chandrapur talukas; GADM has only 10.
  - Chandrapur extracts, plain and clipped to our outline, plus the 15
    headquarters points.
  - Edges differ from our GADM outline by 2% of the area.
  - The statewide files are git-ignored. `PROVENANCE.md` gives the source and
    checksums.
- **`data/raw/osm_rivers/`:** named rivers from the Overpass API
  (© OpenStreetMap contributors, ODbL).
  - 43 named rivers within 3 km of the district, matched to HydroRIVERS.
  - Raw response, checksum and query are in `PROVENANCE.md`.
  - The labels for Figure 1 await the author's check.

---

## 2026-10-18 — Photo audit results; existing MGNREGA works on the map

### Photo audit
- **Protocol** (`docs/PHOTO_LABELLING_PROTOCOL.md`) completed on 2026-10-16,
  after labelling began and before the key was opened. Storage and recharge
  count as positive. A category qualifies at ≥50% positive with a Wilson lower
  bound ≥30%; IF/IAY never qualifies. Disagreements follow the strict rule:
  positive only if both labellers said so. Deviations are logged in the
  protocol.
- **Sheets:** in `reports/photo_audit/returned/`, with the raw copies kept.
  - Labeller A's label column was one row out of step. It was re-aligned on the
    coordinator's instruction, without A's confirmation; the shift held across
    the whole sheet.
  - B's single "toilet" label became `other`.
- **Agreement:** κ = **0.459** (75.8% raw); positive vs not, κ = 0.392.
- **Result:** **no category passes under the strict rule.**
  - WC 16.7% and WH 17.2% positive.
  - Under the lenient rule, WC passes at 50.0% and WH misses at 48.3%.
  - MGNREGA category codes do not reliably identify harvesting structures.
    The planned AUC validation therefore cannot run as specified.

### Map: existing works (display and comparison only)
- **New `utils/structures.py`** loads three things:
  - the 8,243 in-district WC/WH geotags, which are unverified;
  - the 42 photo-confirmed structures (12 strict, 30 lenient);
  - helpers for each point's zone, the enrichment and the 600 m overlap.
- **New `tools/build_structure_layer.py`** writes the confirmed set and the
  thumbnails for the 12 strict structures to `reports/photo_audit/map_layer/`
  (git-ignored).
  - The thumbnails were checked by eye: no people visible.
  - P098's photographer-name watermark is cropped off.
  - Lenient photos are not embedded, because several show fields or a house
    yard.
- **`utils/map_renderer.py`** adds three toggleable layers:
  - **MGNREGA water works:** clustered dots, WC blue and WH white, off by
    default. Each popup gives the category, phase and zone, plus a link to its
    published Bhuvan photo.
  - **Photo-confirmed structures:** off by default. Strict ones embed their
    photo.
  - **A gold star** on every candidate site, across the active result and all
    four algorithms, with a work within its 600 m circle. On by default; 20
    sites have one.
- **The legend and an `app.py` caption** report the zone enrichment, worded as
  agreement with existing practice and not accuracy.
- Observer names and other personal fields are never read.
- **Measured, baseline (AHP + WLC):**

  | Measure | Result |
  |---|---|
  | WC/WH works in High | 11.0%, against High's 6.44% of the area (1.71×) |
  | WC/WH works in Low | 19.6%, against 41.1% (0.48×) |
  | Strict confirmed in High | 3 of 12 |
  | Cropland only, works in High | 12.3%, against 9.3% of cropland area (1.33×) |
  | Sites with a work within 600 m | 11–14 of 25 per algorithm; random in-district point 27.1%, random cropland point 35.9% |
  | Against the cropland baseline | TOPSIS variants p ≈ 0.03; WLC p 0.26 (AHP) and 0.07 (Fuzzy-AHP) |

  88% of works are on cropland, so part of the agreement comes from land
  cover alone.
- Page size about 5 MB (was about 3 MB). `tools/smoke_test.py`: 14/14 pass.

### Same day, later — scenario priorities; farmland site context
- **Sidebar, every scenario:** a "Prioritises" panel lists the scenario's
  weights in order, with ▲/▼ against the baseline. Example: Fertile farmland
  gives soil 0.26 (from 0.15), land cover 0.23 (from 0.06), rainfall 0.20
  (from 0.43).
- **Fertile farmland scenario only:** each candidate site, in its card and its
  map popup, also shows:
  - the nearest MGNREGA water work (unverified), plus the three nearest, each
    linked to its Bhuvan photo so a site's works can be judged by eye;
  - the nearest photo-confirmed structure;
  - the nearest mapped river (HydroRIVERS, larger channels only, measured in
    UTM 44N);
  - whether the site is on cropland, and the cropland area within 1 km.

  This comes from `utils/structures.site_context`, about 3 ms per site, and
  nothing in it feeds the score. Rank 1 under farmland: a WH work 0.51 km
  away, a river 1.27 km away, and 3.4 km² of cropland within 1 km (100%).
- Smoke test 14/14. A separate AppTest run confirmed the farmland panel and
  site cards, and that the baseline cards carry no context block.

---

## 2026-10-07 — Data layers on the browser map

Display only: no analysis result or paper number changes.

- **New `utils/data_layers.py` and `utils/data_layers.js`:** the map now has
  a **Data layer** picker. The layers are:
  - the six criteria: rainfall (2014–2024 mean, mm/yr), slope, drainage
    density, distance to settlement, soil texture and land cover;
  - population density and a population heatmap, a 1.5 km Gaussian-smoothed
    density;
  - the suitability score;
  - Curve Number, runoff depth and runoff coefficient for the 100 mm storm.

  Each layer is drawn as a colour-coded overlay under the zones, boundary,
  rivers and sites, which stay toggleable.
- **Raw values by default; a "Show model score (0–1)" switch** shows the score
  the model gives the criterion instead, on one shared 0–1 ramp. For the two
  population layers it shows the settlement-proximity score, with a note that
  the model scores distance, not density.
- **The legend changes with the layer:**
  - continuous layers get a colour bar with ticks, units and the source;
  - soil and land cover list their classes with the model score.

  Slope is stretched to the 98th percentile, as QGIS does by default, and
  says so. Population uses a log scale and marks the 400 people/km²
  settlement threshold. Suitability marks the 0.65 and 0.85 breakpoints.
- **Click-to-read:** clicking the district shows every layer's value and
  score for that ≈300 m cell, with the displayed layer highlighted. Verified
  at the rank-1 site: 0.957, 1.07°, Loam, 0.44 km/km², 7.2 km, matching the
  paper.
- **Projection:** images are re-sampled onto Mercator rows so they line up
  with the boundary and basemap; cells are drawn crisp, the heatmap smooth.
- **`utils/map_renderer.py`:**
  - `render_map(result, stack=None)` returns the full HTML document instead
    of Folium's base64 iframe, keeping the page at about 3 MB with all layers;
  - the boundary pane moves to z 260, above the data layers;
  - the minimap starts minimised;
  - the basemap changes from CARTO dark_matter, which now shows an "API key
    required" watermark, to Esri dark grey (keyless), with OpenStreetMap as
    an alternative.
- **`app.py`:** passes the cached criteria stack to `render_map`; map height
  500 → 640 px.
- `tools/smoke_test.py`: 14/14 pass.

### Same day, later — candidate sites for all four algorithms

- **The layer box has one overlay per algorithm:** AHP + WLC, AHP + TOPSIS,
  Fuzzy-AHP + WLC and Fuzzy-AHP + TOPSIS. Each shows that algorithm's top 25
  sites under the current scenario and pairwise matrix, is off by default and
  can be toggled on its own.
- **Colour and ring size per algorithm:** orange, pink, yellow and violet;
  ring radius 8, 11, 14 and 17 px. A site chosen by several algorithms shows
  as concentric rings. Smaller rings sit in higher panes, so each stays
  hoverable.
- **Hover text** gives the algorithm, rank, score and coordinates, and lists
  which other algorithms chose a site within 2 km (the consensus matching
  radius), with their ranks, or says "chosen by this algorithm only".
- **Clarity:** the existing green site layer is now labelled "Top Candidate
  Sites (selected: <algorithm>)", and the map legend shows the four ring
  styles.
- **`app.py`:** computes the four site lists with
  `score_stack(..., extract_sites=False)` and caches them in session state.
  They are recomputed only when the pairwise matrix changes (≈0.6 s).
- `tools/smoke_test.py`: 14/14 pass.

---

## 2026-10-04 (tenth entry) — paper_pack/ for drafting v4

- **`paper_pack/`** is what to attach to a fresh Claude to draft v4. It holds
  `DRAFTING_BRIEF.md` (the authority order, the new storyline, rules,
  placeholders and validation wording), `PAPER_REVISIONS.md`, `FIGURE_DATA.md`,
  `PAPER_NUMBERS.txt` (fresh `tools/paper_figures.py` output),
  `SOIL_LEGEND_CORRECTION.md` and the 17 figure PNGs.
- `tools/paper_figures.py` §16: the smoke-test count is now 14 (was 11).

---

## 2026-10-04 (ninth entry) — Blinded photo-labelling set, guide and protocol template

- `reports/photo_audit/blind/` holds the 240 photos as P001–P240 (seed 7),
  `key.csv` (coordinator only), `labels_A.csv` / `labels_B.csv`, and an offline
  `view.html`. `reports/photo_audit/` is git-ignored.
- **`docs/PHOTO_LABELLING_GUIDE.md`:** the order of work, labelling rules, draft
  label definitions with edge cases, disagreement resolution, and what Claude
  Code does afterwards.
- **`docs/PHOTO_LABELLING_PROTOCOL.md`:** a template the authors fill in and sign
  **before** labelling (definitions, edge cases, whether recharge counts, the
  inclusion rule, the kappa threshold).

---

## 2026-10-04 (eighth entry) — MGNREGA follow-up inspection (no filtering)

- **`tools/inspect_mgnrega_2.py`** writes `reports/mgnrega_inspection_2.md`.
  It covers:
  - a 240-photo audit sample in `reports/photo_audit/`, with a `labels.csv` template;
  - the spread of multi-geotag workcodes;
  - the stage-3 FY 2021-22 spike, which is 93.5% IF;
  - the distance of the 639 out-of-district points to the boundary.
- **Mask provenance confirmed:** the mask comes from `data/boundary.geojson`,
  rasterised `all_touched=True`, so 214 of the "outside" points still fall in a
  masked cell.
- `.gitignore`: `data/raw/mgnrega/*.json` and `stage*/*.json` are excluded,
  because they contain observer names.

---

## 2026-10-04 (seventh entry) — MGNREGA geotags pulled for validation (raw + inspection only)

- **`tools/pull_mgnrega.py`:** pulls Bhuvan Bhugram accepted geotags for 15
  blocks × stages 0 and 3 (30 requests, 3 s apart, all HTTP 200) plus two
  block=All checks. Raw responses are byte-for-byte in `data/raw/mgnrega/`;
  provenance and curl commands are in `data/raw/mgnrega/PROVENANCE.md`.
- **`tools/inspect_mgnrega.py`:** writes `data/interim/mgnrega_all.parquet`
  (82,289 records, nothing filtered, observername dropped) and
  `reports/mgnrega_inspection.md`.
- No validation, filtering, category choice or accuracy threshold yet. Those
  wait for the report to be reviewed.

---

## 2026-10-04 (sixth entry) — Fig 18(b) ratio, Fig 12 spacing, specs

- **Fig 18(b):** ratios are now computed from the unrounded shares. Soil's
  variance ratio was stored as 0.635 and printed **0.64**; it is exactly
  0.6348, so **0.63**. The other eleven ratios were unchanged. RESEARCH_CONTEXT
  and PAPER_REVISIONS are corrected.
- **Fig 12:** the "upstream" note moved to the soil row, clear of "range 16.23 pp".
- **Fig 15:** panel (c) is formally dropped. The caption and data label no longer
  mention it, and FIGURE_SPECS records the decision.
- **FIGURE_SPECS Fig 20:** the consensus box now reads "15 sites picked by all 4
  methods · 528.5 km²". A note separates this from Fig 22's "22 of 25".
- **PAPER_REVISIONS:** the "48% of the total weight" claim is verified as slope +
  settlement + land cover + soil = 0.478.
- `exports.py` and `derived_maps.py` were re-run; the outputs are unchanged.

---

## 2026-10-04 (fifth entry) — Paper draft v3 audited; Loam robustness check run

- **`docs/PAPER_REVISIONS.md` rewritten** against `rwh_journal_paper_v3_preview.pdf`.
  It now goes section by section with current replacement values for every
  table (5–21), the abstract and the conclusion, plus a map from the draft's
  figure slots to the generated figures. Tables 12 and 13, empty in the draft,
  are filled.
- **Loam robustness check (Loam 1.00 → 0.80):** High share 6.44 → 6.40%. Top 5
  retained 2/5, top 10 6/10, top 25 20/25. Base rank 2 leaves the top 25, and
  ranks 3 and 5 fall to 17 and 16.
- **`tools/paper_figures.py`:**
  - §6 now reports the unchanged share by area (87.17).
  - §8 reports the High share by area (6.44, not 6.45).
  - §20's netted "recovered by matching" verdict ("mostly a genuine ranking
    difference") is replaced by the three-way partition, which agrees with
    Fig. 21.

---

## 2026-10-04 (fourth entry) — Figure review closed; paper revision list

- **New `docs/PAPER_REVISIONS.md`:** every number, claim and Methods
  description that changed after the soil correction, old → new, plus the
  three outstanding text items (Loam citation, Loam-at-0.80 robustness check,
  37.0/9.8 replacements). Linked from START_HERE and copied to review_pack.
- **RESEARCH_CONTEXT banner:** the Fig 22 band is now 0.817–0.889; the Fig 12
  cutoff bar is now a range (36.43 / 36.00 pp); rainfall ±20% is now 1.24; the
  consensus column "Majority" is now "Half or more".

---

## 2026-10-04 (third entry) — review round 14: Figs 15–18, 21; the generated set is done

- **Fig 21:** label overlap fixed (rows 1.4 apart); added a rounding note.
  `_text_problems` `overlap_frac` 0.22 → 0.03. The old value hid this overlap;
  at 0.03 the full set is still silent.
- **Fig 18 double rounding:** 42.9 → 42.8 (rainfall weight), 37.0 → 36.9
  (rainfall level). `sensitivity.py` rows gain unrounded `theoretical_pct_exact`,
  `effective_pct_exact` and `discrimination_pct_exact`; Fig 18 formats those.
  Fig 6's caption and RESEARCH_CONTEXT now say 36.9, not 37.0.
- `app.py`: the sensitivity table selects its columns by name, because the new
  fields broke a positional rename. The smoke test caught it.
- **Fig 17:** neutral bars in (c); computed finding title.
- **Fig 16:** "half or more" replaces "majority"; finding title. **Fig 15:** 16.23 pp.

All 17 rebuilt; no warnings; smoke test passes.

---

## 2026-10-04 (second entry) — review round 13

- Fig 9: "narrowest raw spread". By w·SD, land cover is narrower than slope.
- Fig 5(f): the truncation note moved to the empty band above the 0.10 floor at
  17–25 km (three short lines); at the bottom it hid the 5–17 km histogram bars.
- Protocol §2: near-black is declared meaning-free ink, like neutral grey.

All 17 rebuilt; no warnings; smoke test passes.

---

## 2026-10-04 — review round 12: Figs 5, 6, 8, 9

- Fig 9: axes in w·SD order; ranks by marker, not hue (no ramp clears the
  palette); `_assert_series_colours` includes the class colours; the
  annotations are re-placed.
- Fig 8: dropped the 18.51% reconstruction from the caption; added a sentence
  on the subset/double counting.
- Fig 6: shorter titles. Fig 5: truncation note nudged.

All 17 rebuilt with `tools/build_figure_data.py`; no warnings; smoke test passes.

---

## 2026-10-03 (eleventh entry) — review round 11: Figs 10 and 13

- Generic series colour `#0072B2` → `#1A1A1A`. It was ΔE 5.5 from the High
  class blue, so Fig 13 used blue for two meanings. Class colours and GENERIC
  are now in `_assert_palette`.
- Fig 13: neutral/dashed series, leaders moved off the curve, 87.17% in the title,
  and the caption describes the footer flows.
- Fig 10: finding title ("at fixed cutoffs"), tighter columns, centred legend,
  and a rounding note.
- FIGURE_SPECS Fig 7 Medium `#F4A582` → `#E8E4DC`.

All 17 rebuilt via `tools/build_figure_data.py`; no warnings; smoke test passes.

---

## 2026-10-03 (tenth entry) — review round 10: Figs 2, 5, 6, 8, 9, 10, 16, 22

Every item was verified in code before it was changed; details are in
docs/FIGURE_REVIEW_PROTOCOL.md §4b "Round 10". Substantive:

- **Fig 8(b) compared across legends.** The ramp series was the current
  composite in both panels. Now each panel holds its legend for both series.
  Ramps on the superseded legend tie 0 cells (18.51% High), so the title
  ("needed both") is now actually shown.
- **Fig 22:** bins anchored at 0.85; band corrected to 0.817–0.889.
- **Fig 9:** the title is now based on weighted spread (soil, rainfall); the rank
  palette no longer imitates semantic colours.
- **Fig 5:** the settlement caption said plateau, but the function is a gentle
  peak; √-scale bars were wrongly floored.
- Graticules on the small-multiple maps; Fig 2 retitle + shared y.
- New: `_assert_series_colours`, `_edges_include`, `_outer_graticule`,
  `tools/build_figure_data.py`.

All 17 rebuilt, no warnings; smoke test passes.

---

## 2026-10-03 (ninth entry) — Fig 10 caption, Fig 13 area weighting, stale docs

Found by the fresh reviewer's consistency pass, not by a figure review.

- **Fig 10 caption contradicted Fig 21.** It still said quantile-matching
  "recovers only part of the disagreement, so it is mostly a genuine ranking
  difference rather than a threshold artefact". Rewritten: the Low shift is a
  cutoff effect (a 0.050 move of the lower cutoff removes it), and the ranking
  disagreement is separate, at about half the reclassified area (Fig. 21).
- **Fig 13's unchanged share was a cell count** (87.16%), while every other
  class share and Fig 21's partition (100 − 12.833 = 87.17) are area-weighted.
  Now area-weighted: **87.17%**.
- **Stale docs:** "under any cutoff scheme" → "under both cutoff schemes
  tested" in CLAUDE.md, RESEARCH_CONTEXT.md and protocol §4. The cutoff bar is
  a 36.43 pp range, not +26.53. "Baseline (balanced)" → "(rainfall-led)" in
  FIGURE_SPECS. Smoke-test count is 14 everywhere. Protocol §4 now points to
  §4b as the current status.

All 17 rebuilt; every check silent. Smoke test passes (run it with the venv
Python and `PYTHONPATH=.`, or app.py cannot import `gis_analysis`).

---

## 2026-10-03 (eighth entry) — Figures 2, 5, 6, 8, 9 and 22; three substantive findings

### Three findings, not layout

**1. The shortlist stands on 43 km² of soil (Fig. 9).** Measured: Loam, the
only texture scored 1.00, covers **0.376% of the district — 42.9 km² of
11,412** — and **4 of the top 5 candidate sites sit on it**. SoilGrids is
250 m resampled nearest to the ~300 m grid, so a class this small is near the
resolution of the input. The top of the shortlist therefore depends on a scarce
class being mapped correctly, which is the exposure that produced the
2026-10-02 legend error in the first place. Now annotated on the figure and in
the Limitations; the obvious robustness check — rescore Loam at 0.80 like
Sandy Clay Loam — is flagged for the Discussion.

**2. Figure 8 was justifying a current choice with retracted data.** It
reconstructed step-class scoring using the pre-correction soil table and used
the resulting 973-cell plateau as evidence. Recomputed under the corrected
legend: the same step scheme leaves **1** cell at exactly 1.000, not 973.

| Soil legend | Step-class cells at exactly 1.000 |
|---|---|
| In use at the time (superseded) | **973** |
| Corrected | **1** |

Rebuilt as a two-panel comparison, which turns the objection into the finding:
**the plateau needed the flat tops AND a dominant class wrongly scored 1.00**;
neither alone produces it. The caption states that 973 is a reconstruction that
must never be quoted as current, and that the case for ramps rests on Fig. 2's
IQR and Fig. 18's discrimination measure, both on current data.

**3. Figure 22's title said the opposite of its data.** "Scoring well is not
the same as every method agreeing" — but every cell above **0.8887** is High
under all four combinations and none below **0.8515** is. Disagreement occupies
a band of about 0.04 straddling the 0.85 breakpoint, the same mechanism Fig. 21
quantifies. Retitled "Method disagreement is confined to a narrow band at the
0.85 breakpoint". Scoring well is almost the same as unanimity; what is
unstable is scoring *just* well enough. Site counts by agreement level
(**22 / 2 / 1**) were hidden by overplotting at y = 4: markers jittered, counts
printed per row, and the non-unanimous three named — ranks 23, 24, 25 at
0.8592, 0.8584, 0.8536, the bottom of the list.

### Figure 6's scale bar was meaningless

It was drawn into a margin axes **0.22 figure-widths wide** while the map
panels are ~0.26, so its length had no relation to the maps it labelled. Now
`_place_furniture(axes[0, 0], ctx)` like every other map. `_add_scalebar`
asserts it is reached only through that helper, and `_map(furniture=True)` now
raises rather than placing a bar in a fixed corner without consulting the mask.
Panel letters and titles also collided ("w = 0.154(e)", and (f)'s title over
the colourbar); titles are two lines now.

### Figure 2: arrows that pointed at nothing

The three class callouts had their tips at a fixed **axes fraction**, so on a
log axis the Water arrow ended around 10⁴ while its bar is **105 cells**. Tips
now sit at the actual bar height in data coordinates. Also: (b) and (c) share
both axes, the bars use each criterion's own colour instead of AHP blue and
rainfall green, and the caption is honest that the ramp is an improvement
rather than a cure — 86.0% of cells still above 0.90, which is why slope takes
0.43× its weight in Fig. 18.

### Figure 5: a footnote contradicted by its own panels

The footer claimed the frequency histograms carry "no numeric axis", but the
two categorical panels had one, because `set_yscale("function", ...)` was
called AFTER `set_yticks([])` and reinstalled a locator. Reordered. Soil and
land cover now show **class names** instead of bare codes — after a legend
error, that panel is exactly where a referee must be able to check that each
score is attached to the right class. The caption states the slope ramp beyond
its 20° truncation, the rainfall formula (floor 0.20 plus 0.80 × percentile
rank, not a raw percentile), the settlement curve, and the SoilGrids citation.

### Checks added

- **`_baked_caption_problems`** — figure-level prose below the axes. Found it
  in Figures 2, 5 and 6; all three moved to `CAPTION`.
- **`_annotation_palette_problems`** — an annotation in a criterion's colour on
  a panel that is not about that criterion. The legend check could not see
  Figure 2, which has no legend on those panels.
- **`_category_axis`** — ticks and names from a class table.
- The artist test now covers **scatter markers**: a `PathCollection` is neither
  a `Line2D` nor a `Patch`, which is how Figure 22's per-row counts came to be
  drawn behind its site markers.

**Two of my own checks were wrong and are fixed.** The leader test transformed
the annotated point with the TEXT's transform (`textcoords`) instead of
`xycoords`, which put the anchor somewhere arbitrary whenever the two differ —
twelve spurious reports on Figure 2 alone. And the annotation-colour test
flagged a land-cover label drawn in land cover's own colour; it now reads each
axes' title to learn what the panel is about.

### Confirmed, from the review's UNVERIFIED list

- **Rainfall's weight is 0.428**, not 0.429: the exact value is 0.4284938,
  below the 0.4285 that would round up.
- **Soil class 7 (Loam) is 0.376%, 42.9 km²** — the estimate of 0.3–0.5% was
  right.
- **Figure 22 site counts are 22 / 2 / 1** — as estimated.
- **Figure 8's terminal bin does not double-count.** numpy closes the final bin
  on both sides, so the tied cells are inside it; the hatched bar is now drawn
  at that bar's own position and width so it reads as a subset rather than a
  neighbour.
- **Figure 6's bar**: not 30 km, but the measurement was right to be
  suspicious — it was drawn against the wrong transform entirely.

### Note on figure identities

There is no separate "rank displacement" figure outstanding. Figure 21 WAS the
rank-displacement scatter; it was replaced on 2026-10-03 by the
ranking-versus-cutoff cell partition. Figures 1, 3, 4, 7 and 20 are QGIS
layouts and drawing-tool diagrams specified in `docs/FIGURE_SPECS.md`. **Every
figure generated by `tools/make_figures.py` has now been reviewed.**

All 17 rebuilt; every check silent. Smoke test 14/14.

---

## 2026-10-03 (seventh entry) — Figure 21's decomposition was netted, not partitioned

### The blocking find, and it changes the headline

The first Figure 21 subtracted the churn under share-matched cutoffs from the
churn under fixed ones and called the remainder a "breakpoint component". That
is wrong twice:

1. **They are different sets of cells, not nested**, so the subtraction is not
   a decomposition. "77% of the disagreement is re-ranking" treated the 9.90 pp
   changing under matched cutoffs as a subset of the 12.83 pp changing under
   fixed ones. It is not.
2. **For the Low class the difference is negative**, −2.970 pp: fixed cutoffs
   SUPPRESS re-ranking there, because the TOPSIS surface sits lower and the
   fixed 0.65 holds cells in Low that a matched cutoff releases. A stacked bar
   cannot draw a negative segment, and the code had `max(..., 0.0)` — **my
   clamp** — so the row silently showed 3.99 pp under a total labelled 1.02 pp.
   The rows summed to 15.80 against a stated total of 12.833, and the Low row
   contradicted Figure 13's Sankey (1.02 pp = Low→Medium 116 km²).

Rebuilt as a **three-way partition of cells**, which sums correctly by
construction and has no negative segment:

| Category | pp | km² |
|---|---|---|
| Re-ranked under **both** cutoff schemes | **6.457** | **736.9** |
| Changes only under the **fixed** cutoffs | 6.376 | 727.7 |
| Re-ranked but **masked** by the fixed cutoffs | 3.445 | 393.2 |

robust + induced = 12.833 (what actually changes class);
robust + masked = 9.902 (what changes under matched cutoffs).

**The headline is 50.3%, not 77%** — half the cells that change class would
change under any cutoff scheme. Per origin class the rows now reconcile with
Figure 13: High 1.283, Medium 10.533, Low 1.018, summing to 12.833.

Panel (b) was also a tautology: share-matched cutoffs are DEFINED to reproduce
WLC's class shares, so its "0.00 pp" bars were zero by construction and its
legend had an entry with no bars. Replaced with the evidence that is not
circular — the cutoff displacement itself. Removing the +9.027 pp Low shift
takes a **0.050** move of the lower cutoff; removing the −0.795 pp High shift
takes **0.005**. That asymmetry, in score units, is the mechanism.

### Figure 12 follows from it

The old title, "of the algorithm choices only aggregation matters, and only for
Low", was contradicted by the paper's own Figure 21. Took the stronger of the
two options offered: **the classification cutoffs are now their own bar in the
upstream group**, swapping the fixed 0.65/0.85 for the 33rd/67th percentile
split (`criteria.CLASSIFICATION_MODE`, the project's pre-Sprint-1 scheme):
**+26.53 pp on High, −8.04 pp on Low** — the second-largest effect in the
figure. Retitled "Analyst decisions dominate — and the one large algorithm
effect is itself a cutoff effect (Fig. 21)", and the Low aggregation bar is
annotated on the figure rather than only in the caption.

### A palette fault the constants check could not see

`_assert_palette` compares colour CONSTANTS, so it could not see Figure 21
passing `OKABE[0]` and `OKABE[4]` straight to `barh` — AHP's method colour and
Slope's criterion colour. Added **`_legend_palette_problems`**, which reads the
legend, where a colour is bound to a meaning in front of the reader, and
flags a handle drawn in a criterion's or a weighting method's colour whose
label does not name it.

It immediately found a real one: **vermilion meant three things** — Fuzzy-AHP
in Fig. 11, the tied scoring scheme in Fig. 8, the variance share in Fig. 18.
Root cause: `OKABE[0]` and `OKABE[1]` were the house generic two-series pair
AND the two weighting-method colours. The generic pair is used in four figures,
the methods in one, so **the methods moved**: AHP `#293241`, Fuzzy-AHP
`#E56B6F`, separated in luminance (0.19 against 0.56) as well as hue, so
Figure 11's two lines stay distinguishable without colour vision. `GENERIC` is
now a named constant.

### Also

- **`check_transition_partition`** in the smoke test asserts the partition
  identities and that no component is negative. 14/14 passing.
- Figure 13's High-class label is three lines, which fits the 0.14-unit gap
  between the 0.85 rule and the frame with a short leader; on two lines it
  needed 0.16 and had to sit far left with a 0.34-unit leader.
- Figures 1, 3, 4, 7 and 20 are **not generated by this tool** — three QGIS
  layouts and two drawing-tool diagrams, specified in `docs/FIGURE_SPECS.md`.
  Figure 22 is the only generated figure still unreviewed.

All 17 rebuilt; every check silent. Smoke test 14/14.

---

## 2026-10-03 (sixth entry) — Figure 21 answers the ranking-versus-breakpoints question

### The result

Built the decomposition the seventh review round proposed. Share-matched
breakpoints are the quantiles of the TOPSIS surface — **0.5998** and
**0.8452**, against the fixed 0.65 and 0.85 — that reproduce WLC's own class
shares exactly. With the class sizes equalised, any cell that still changes
class has been re-ranked.

| | pp of district area |
|---|---|
| Total changing class, WLC → TOPSIS | **12.833** |
|  re-ranking (survives share-matching) | **9.902 — 77.2%** |
|  breakpoint placement | 2.931 — 22.8% |

| Class | Shift, fixed breakpoints | Shift, share-matched |
|---|---|---|
| High | −0.795 pp | −0.000 pp |
| Medium | −8.232 pp | −0.000 pp |
| Low | **+9.027 pp** | **+0.001 pp** |

**The question has two halves and they answer differently**, which is why no
single number was going to settle it:

- The **+9.03 pp Low-class shift is a breakpoint artefact.** It is zero by
  construction once the class sizes are matched — which is the point: nothing
  about the ordering of cells had to change for that headline number to appear.
  It comes from applying one fixed pair of cutoffs to two differently scaled
  quantities, a weighted mean and a closeness coefficient.
- The **cell-level disagreement underneath is 77% genuine re-ranking**, which
  is the structure Figure 14(a) maps.

So the class-share statistic is the fragile one and the ranking is
comparatively robust — the opposite of how comparative-MCDA papers usually
report this, and worth stating as a finding rather than a caveat. Consistent
with `tools/paper_figures.py --section 20`, which found quantile-matching
recovers ~23% of the disagreement.

Spearman ρ = **0.9643**; shortlist retention **5/10** and **18/25**.

### A trap found while writing it

**Shortlist overlap depends on how many sites were extracted.** Candidate
extraction is best-per-tile with a 5 km separation rule and is **not nested**:
the top 10 of a 10-site run is not the first 10 of a 25-site run. Reporting the
first 10 of a 25-site extraction gives **8/10**, which would have contradicted
`algorithms.py`'s **5/10** in the same paper. Figure 21 extracts at the size it
reports, and the caption says so. Recorded in `docs/RESEARCH_CONTEXT.md`.

### The two remaining review items

- **Figure 14(b)** — the y-axis said "district area reclassified (%)", which
  reads as each bar's share OF the district; if it meant that the bars would
  sum to 12.83%. They are within-band rates. Now "% of band area
  reclassified", and the per-bar annotation gives each band's area in km²
  rather than a cell count, so the units match the bars.
- **Figure 13(a)** — the "High class: 6.44% vs 5.65%" label overhung the axes.
  Between the 0.85 rule and the frame there are only 0.15 data units and the
  label needs 0.16, so moving it left put it on the rule instead. Relocated to
  the empty region left of the rising curves, where the leader runs above both
  curves the whole way.

### Status

Figures 2, 5, 6, 8, 9, 10–19 and 21 complete; **22 is the only generated
figure still unreviewed**. Figures 1, 3, 4, 7 and 20 are QGIS and drawing-tool
work (`docs/FIGURE_SPECS.md`).

All 17 rebuilt, no collisions, smoke test 13/13.

---

## 2026-10-03 (fifth entry) — Onboarding for a session with no history

The figure work has run across six rounds of external review, and the standard
that emerged lived only in the conversation. A new session — a different
account, a later day, anyone else — would have had to re-derive it, and would
have re-opened decisions that are already closed. Two new files fix that.

### `START_HERE.md` (repo root)

The cheap entry point, ~700 tokens. Six lines on what the project is, then
numbered steps routing to the right file per task, each with its token cost,
and an explicit list of what **not** to read: `CHANGELOG.md`,
`docs/RESEARCH_CONTEXT.md` and `tools/make_figures.py` are ~19k, ~20k and ~21k
tokens and should be grepped, never read end to end. Carries the four traps
that cost the most time, the user's standing instructions, and a
question-to-file table.

Budget to be useful on figures: **~4,300 tokens** across two files.

### `docs/FIGURE_REVIEW_PROTOCOL.md`

The reference, ~2,700 tokens:

- **What the automated checks cover and what they don't.** The four tests in
  `_text_problems`, the three refinements it needs that look like redundancy
  and are not, `_assert_palette`, and the two smoke-test assertions — then
  the four classes of defect nothing checks, which is where the real findings
  came from.
- **Settled decisions, with the reason each cost a round.** Area-weighted
  shares, `percent_exact` for differences, the class breaks, decimals follow
  provenance, half-up rounding, PNG only, furniture from `_clear_corner`, one
  colour per criterion, shared axes, computed titles.
- **The project's two headline distinctions**, which a new session gets wrong
  by default: weighting METHOD (0.560 pp) against weighting JUDGEMENTS
  (16.23 pp range), and contribution to LEVEL against contribution to
  VARIATION.
- **A seven-class defect taxonomy** drawn from the rounds, so a new figure can
  be checked against it.
- **Per-figure status**, 15 publishable and 2 unreviewed, with why Figure 21 is
  next and why the answer is probably "both".
- **Four codebase traps**: the `tools/inspect.py` stdlib shadow, heredoc
  backslash collapsing, `FancyArrowPatch` coordinate spaces, and `fill_between`
  bounding boxes.
- The working agreements, including that two review findings across six rounds
  were wrong and were corrected rather than accepted.

### Cross-links and one stale fact

`CLAUDE.md` opens with a pointer to both; `README.md`'s tree lists them.

`docs/FIGURE_SPECS.md` still told its reader to produce "PDF plus PNG" and to
name files `fig01.pdf`, from before the 3 October switch to PNG-only — which
would have had someone hand-producing the five QGIS figures in a format the
generated set no longer uses. Corrected, and pointed at the review protocol so
the five external figures are held to the same standard.

### Also

Figure 15's caption hard-coded the weighting-method effect as 0.565 pp, which
the `percent_exact` fix had moved to 0.560. Now computed from `_main_effects`
rather than written in, so it cannot go stale again.

All 17 figures rebuilt, no collisions. Smoke test 13/13.

---

## 2026-10-03 (fourth entry) — The rounding bug was wider than Figure 12; the checker was blind to straight lines

### The rounding bug, traced to the rest of the codebase

Last entry fixed the factorial effects. An audit for the same pattern found
`sensitivity.py` doing it too, in **both** analyses that feed Figure 17:
`one_way_sensitivity` and `map_removal_sensitivity` each differenced
`_area_statistics`'s 2-dp `percent` field. Both now read `class_share_pct`, and
their deltas are stored at 3 dp.

Measured effect: soil's map-removal change moved **+7.68 → +7.67 pp**. The
other five are unchanged at 2 dp, and the ±20% perturbation figures are
unchanged at 2 dp. Small — but the value was wrong, and nothing in the code
would have said so.

**`tools/smoke_test.py` now asserts this cannot come back**, two ways. A static
scan flags any module that differences a `["percent"]` lookup, which is the
only thing that catches a *new* call site before it reaches a figure. And a
behavioural check recomputes every derived effect and fails if all of them are
exact multiples of 0.01 pp, which is what quantisation looks like on a set.
Verified by reintroducing the bug: *"all 18 derived effects are exact multiples
of 0.01 pp"*. 13/13 passing.

### A number that did NOT change

Rainfall's level contribution is **36.95%** and always was. It reads as 36.9 in
one place and 37.0 in another purely because of display precision — the half-up
formatter gives 37.0 at 1 dp. `single_parameter_sensitivity` was never altered
beyond its docstring. Worth recording because it is a per-cell mean of ratios,
not an area share, so the area-weighting convention does not apply to it; the
same is true of the Pratt index. Both are per-cell statistics over the
composite, and the paper should say so.

### The checker was blind to straight lines

`_text_problems` tested a line's *vertices* against each text box. An `axvline`
has two vertices, at the ends of the axes, so **any label it crosses in between
was invisible** — which is why Figure 18's 1.0 reference line through "0.86×"
survived a round. The same blind spot covered the Figure 14 reference line and
the 1:1 diagonals.

Rebuilt on `Path.intersects_bbox`, which tests segments:

- **Lines** are tested as paths, so a two-vertex rule is caught.
- **`fill_between` ribbons** are now tested too, against the real curved path
  with `filled=True` rather than the bounding rectangle. The bbox test had to
  be abandoned last round because a ribbon's bounding box covers most of the
  panel; the Sankey can now be checked automatically instead of by eye.
- **Leaders against other text**, which was the Figure 13 case: a leader may
  touch the curve it points at, but not another label. Built from the explicit
  anchor→label segment rather than `FancyArrowPatch.get_path()`, because
  whether that returns data or display coordinates varies by artist —
  transforming it put Figure 2's four class arrows across the x-axis label and
  Figure 10's north arrow across panel (c)'s letter.

The upgraded check found both of this round's blocking defects on its own.

### Figures

- **13** — at the 0.85 breakpoint the two curves are within a point of each
  other, so two labels meant two leaders fanning from nearly one point and the
  second crossed the first's text. Replaced with a single label giving the
  **High share directly** ("High class: 6.44% vs 5.65%"), which also removes a
  subtraction the reader should not have to do. The y-axis said "cumulative %
  of in-district cells" — the curve became area-weighted when it was reconciled
  with `class_share_pct` and the label had not followed; now "cumulative % of
  district area", with n in the caption.
- **14** — the distance bins are **area-weighted** too. The panel had been
  counting cells while Figures 10 and 13 weighted by area, leaving two
  conventions in one paper. Overall rate 12.84% → **12.83%**, which now
  reconciles exactly with the Sankey: 1,146 + 146 + 116 + 56 = 1,464 km² of
  11,412 km² = 12.83%, so 87.17% unchanged.
- **18** — a ratio label for a bar ending within 0.18 of 1.0 goes inside the
  bar, right-aligned, in white. Outside, a label is about 0.12 wide on that
  axis and reaches the reference line.

### Generator

- **`_assert_palette` now uses CIEDE2000**, not exact equality, at ΔE ≥ 10.
  The exact test caught the scenario bar borrowing Slope's hex; it would not
  have caught a near-miss. Measured: `OTHER_COLOUR` against Land cover is
  **ΔE 16.6**, so the reddish-brown/grey-brown pair raised in review is
  distinguishable; the closest genuine pair in the set is AHP against
  `NEUTRAL_BAR` at 14.8. `MEANING["method"]` is now literally `NEUTRAL_BAR`,
  since both mean "a magnitude with no further meaning", and the pair is
  exempted by name rather than by coincidence. CIEDE2000 is written out in the
  module: one assertion does not justify a colour-science dependency.

All 17 figures rebuilt; every check silent. Smoke test 13/13.

### Docs

`CLAUDE.md` and `docs/RESEARCH_CONTEXT.md` updated for −0.560 (was −0.565),
−0.957, −0.162, −39.51 and soil's +7.67; added the map-removal table, the
36.95 clarification, and the area-weighted edge-effect figures.

---

## 2026-10-03 (third entry) — One class-share function; the factorial effects were quantised

### The blocking find: two code paths, two answers

Figures 10 and 13 reported different shares for the **same surface** — Low
41.08% against 41.04%, and 6.44% against 6.45% at the High end. Cause: `_area_
statistics` weights by cell area, the ECDF counted cells. The analysis grid is
EPSG:4326, so a cell's ground area falls with latitude and the largest cell in
Chandrapur is **0.81%** bigger than the smallest; the Low class sits mostly in
the south, where cells are larger, so counting understates it by ~0.05 pp.

- **`gis_analysis.class_share_pct`** is now the single source of truth, and
  **`area_weighted_ecdf`** its cumulative counterpart. Every figure, table and
  caption reads shares through one of them.
- **`tools/smoke_test.py` asserts it** across all four algorithms and three
  reporting paths — rounded field, exact field, area-weighted ECDF — to within
  0.005 pp. 12/12 passing. This turns the defect into a test failure rather
  than a referee comment.
- Shares are **area-weighted**, and the Methods must say so.

### The second blocking find: the effects were built from rounded inputs

`_area_statistics` rounds `percent` to 2 dp for display, and the factorial
effects differenced that field — so every effect was quantised to 0.01 pp. The
Low-class values +9.030, −0.100 and 0.000 all ending in zero was the giveaway.
`_area_statistics` now also returns **`percent_exact`**, unrounded, and all
effects are computed from it:

| | was | now |
|---|---|---|
| Aggregation, Low | +9.030 | **+9.032** |
| Weighting method, Low | −0.100 | **−0.103** |
| Interaction, Low | 0.000 | **+0.005** |
| Aggregation, High | −0.955 | **−0.957** |
| Weighting method, High | −0.565 | **−0.560** |
| Interaction, High | −0.165 | **−0.162** |
| Simple effect, AHP (Fig. 11) | −0.790 | **−0.795** |
| Simple effect, Fuzzy-AHP (Fig. 11) | −1.120 | **−1.119** |

The third decimal is now real. Fig. 11's padded values were a symptom of this,
not of the formatter.

### Figure 18's title was factually wrong

It named slope as least discriminating. Per unit of assigned weight, **land
cover** takes 0.08× the variance against slope's 0.43× — five times less — while
also taking 1.32× the level. Retitled from the data rather than asserted, so it
cannot go stale. Both panels are now paired bars: (a) the three shares
absolutely, (b) the two ratios. The scatter had pushed four of six criteria
into a cluster below 10% where their labels could not be placed.

Caption gained the two caveats the measure needs: the Pratt index partitions
the variance of the **continuous** composite, not membership of the High class;
and it is defined only for a linear aggregator, so AHP+WLC only.

### Other figures

- **12** — the scenario bar reads "range 16.23 pp", unsigned, with a caption
  clause saying a range over five scenarios is not the same kind of quantity as
  a pairwise change and would grow with more scenarios. Group label "what the
  analyst decides" → "upstream", which no longer contradicts the soil bar's own
  "data error, not a choice". Scenario colour moved to `OTHER_COLOUR`; it had
  been `OKABE[4]`, which `CRIT_COLOUR` assigns to Slope in Figure 15 — the
  consistency fix had created a fresh clash one figure over.
- **13** — ECDF labels moved into genuinely empty space with leaders (the
  TOPSIS curve ran through its own "50.1%" and "94.3%"); the big Sankey label
  moved to the solid left end of its band, where no flow has crossed yet; the
  two small flows summarised under the panel rather than called out across it;
  "(band width ∝ area)" moved to the caption so the title clears the frame.
- **14** — the reference-line label moved to the left end, above the two short
  bars, on a white background.
- **16** — caption defines "majority" for an even number of variants: 2 of 4
  counts as majority, so (a)'s band is "at least half".
- **17** — retitled "Weight perturbation and map removal": three panels, two
  analyses, since map removal is shown twice. Caption now reconciles it with
  Figure 18 explicitly rather than leaving a referee to find the apparent
  contradiction.
- **15** — x-limit 20 → 22 so the 18.77% label clears the frame.
- **5, 9** — three more text-on-curve overprints found by the new check.
- **2 needs no change.** It shows min–max *and* the anchored ramp side by side,
  each panel carrying its own statistic, so the 95.8% is correctly attributed
  to the scoring that was replaced and 86.0% to the one in use.

### Generator-level

- **`_text_problems` extended from text–text to text–artist.** It tests each
  label against Line2D vertices and bar patches. All three blocking overprints
  this round were text-on-artist and invisible to a text-only test. Three
  refinements were needed to make it usable: measure the glyph box with
  `mtext.Text.get_window_extent` rather than `Annotation`'s, which unions in the
  leader arrow and so reported every correctly-placed leader as a collision;
  skip text outside the panels, which are axis labels and titles by design; and
  skip a label whose colour contrasts with the patch beneath it, which is a
  label deliberately set inside its own bar. `fill_between` bands are not
  tested — a curved ribbon's bounding box covers most of the panel, so a bbox
  test fires on exactly the labels that are right.
- **`_r(x, dp)` and `_fx`** — one half-up rounding path for every formatter.
  Figure 18 printed 15.35 as "15.3" and 42.85 as "42.9" because it bypassed
  `_pp`; both now go through `_r`.
- **`_assert_palette`**, run at startup: no non-criterion element may use a
  `CRIT_COLOUR` value. Rainfall and soil are exempt by design.

All 17 figures rebuilt; both checks silent across the set. Smoke test 12/12.

### Still open

Figures 1, 3, 4, 7, 20 (QGIS and drawing tool), 21 and 22 unreviewed.
**21 is the priority** — it decides whether the 9 pp Low shift is a ranking
effect or a breakpoint effect.

---

## 2026-10-03 (second entry) — Figures 13–19 reviewed; a measure renamed, a thesis sharpened

### Two substantive findings, not layout

**1. "Effective weight" was measuring the wrong thing.**
`sensitivity.single_parameter_sensitivity` computes the mean over pixels of
wᵢ·rᵢ/V — the share of the score's **level** each criterion supplies. It was
labelled "realised influence" on Figure 17(d) and "effective weight" on Figure
18, which claims something it does not measure: a criterion that scores high
almost everywhere supplies a lot of level and separates nothing.

Added **`sensitivity.discrimination_weights`**, the Pratt index
βᵢ·corr(rᵢ,V) with βᵢ = wᵢ·sd(rᵢ)/sd(V). The baseline composite is an exact
linear combination, so this partitions var(V) and sums to 100% exactly
(verified). The two measures disagree sharply:

| Criterion | Assigned % | Level (ratio) | Variance (ratio) |
|---|---|---|---|
| Rainfall | 42.85 | 36.95 (0.86×) | **71.98 (1.68×)** |
| Slope | 22.54 | **31.64 (1.40×)** | 9.72 (**0.43×**) |
| Land cover | 5.97 | 7.89 (1.32×) | 0.46 (**0.08×**) |

Slope supplies the most level per unit of weight in the set and almost the
least discrimination. Figure 18 now shows both, titled for that finding, and
the old label is gone. Only defined for a linear aggregator, so computed on
AHP + WLC.

**2. The thesis needed one distinction it was not making.**
"Weighting barely matters (0.565 pp)" is true of the weighting **method** —
AHP against Fuzzy-AHP on one fixed set of judgements. The weighting
**judgements** span **16.23 pp** on High and **24.83 pp** on Low across the five
scenarios, which is larger than the soil correction and about 17× the
aggregation effect. Set side by side without that distinction, Figure 15 reads
as refuting Figure 12.

Figure 12 now carries a "weighting judgements (range across 5 scenarios)" bar
in its upstream group, so both are on one axis and the distinction is visible
rather than argued. Retitled "Analyst decisions dominate; of the algorithm
choices only aggregation matters, and only for Low" — which is a stronger
claim than the one it replaced, not a weaker one.

### Also corrected

- **A claim of mine was wrong.** Figure 18's text said 95.8% of cells score
  above 0.90 on slope. That is the **min–max** figure from Figure 2, for the
  version that was replaced. Under the anchored ramp the model actually uses it
  is **86.0%**. Corrected in three places.
- **The review's premise on slope ties was wrong, and the figure now says so.**
  Figure 19's caveat was asked to name slope as the worst tied case. Measured,
  slope's largest exact tied value covers **0.1%** of cells; soil covers 77.8%
  and land cover 65.6%. Slope is not tied, it is *concentrated*. Both pull ρ
  away from r but for different reasons, and the caption now separates them.
- **Breakpoint convention.** `_classify_suitability` assigns Low at score
  ≤ 0.65 and High at > 0.85. Figure 13 had labelled it "Medium ≥ 0.65",
  contradicting Figure 10. Every legend and label now matches the code.
- **Scenario renamed**, `ahp.py`: "Baseline (balanced)" → **"Baseline
  (rainfall-led)"**. The baseline matrix gives rainfall 0.428, more than the
  bottom four criteria together; "balanced" described the intent, not the
  vector. `tools/smoke_test.py` updated; 11/11 still passing.

### Figures

- **13** — panel (a) rebuilt as empirical CDFs. Two translucent histograms
  produced a third colour that was in the plot but not the legend, and the
  quantity the argument needs had to be estimated from bar heights; on a CDF
  the class share is the curve's height at the breakpoint. WLC 41.04% vs TOPSIS
  50.06% below 0.65, against 93.55% vs 94.35% below 0.85 — which is *why*
  aggregation moves Low an order of magnitude more than High. Alluvial bands
  recoloured by destination at one opacity: the Medium→Low flow, the whole 9 pp
  story, had been drawn in near-white on white. Off-diagonal flows labelled in
  km² (Medium→Low 1,146 km²). Axis relabelled "WLC score / TOPSIS closeness
  coefficient" — they are different quantities and that is the point.
- **14** — panel (a) now maps the difference in **percentile rank**, not in raw
  score. The raw difference is dominated by the level offset visible in 13(a),
  so it painted the district one colour; ranking both surfaces removes the
  offset by construction and the genuine spatial structure appears. Round
  graticule values with degree symbols (the corner labels "19.459"/"78.796"
  had collided). Reference line at the 12.84% district rate and n per bin.
- **15** — legend moved below the panel (it was printing on the title); CR
  moved to the weight-vector row labels where it belongs; (b) clipped to 0–20%
  and neutral grey; criterion colours from the new fixed table.
- **16** — both panels collapsed onto one four-category scale (unanimous /
  majority / minority / never High). The raw counts were not comparable: with
  denominators of 4 and 5, a count of 4 was unanimous in (a) and a majority in
  (b). Unanimous area now stated: **528.5 km²** across method combinations
  against **239.9 km²** across scenarios — the Figure 12 finding in map form.
- **17** — panel (d) dropped; it duplicated Figure 18(b) value for value.
  Colour given one meaning per figure: neutral where a bar is a magnitude, sign
  colours only in the panel whose bars are signed. (c) labelled (removing soil
  moves High by +7.68 pp). Caption states the perturbation and renormalisation
  methods. "Three independent analyses" → "complementary"; they share one
  criteria stack and cannot be independent.
- **19** — title leads with the finding (max |r| = 0.45, rainfall–soil;
  ρ = 0.44), diagonal masked to white, negatives through `_mn`.
- **10** — scale bar 25 → 20 km and the north arrow moved clear of it.
- **5, 8, 9** — three collisions the new check found that no review had
  reached.

### Generator-level

- **`_text_problems`** replaces `_text_overruns`: adds a pairwise bounding-box
  overlap test across every Text artist. It found all five collisions the
  review listed as blocking, plus three more, in about a second each. Tick
  labels excluded — matplotlib parks a Text for every tick it has ever laid
  out, including ones outside the view limits that are never drawn.
- **`_place_furniture`** puts the scale bar and north arrow in whichever frame
  corner the district mask says is emptiest. Figure 10 was fixed by hand last
  round and 14 and 16 promptly repeated the defect; all three now call the one
  helper.
- **`CRIT_COLOUR`** fixes one colour per criterion across the whole set.
  Rainfall had been vermilion in Figure 15 and green in Figure 12, and the blue
  that meant "AHP" in Figure 11 meant "Slope" in Figure 15. Plus `NEUTRAL_BAR`
  and `SIGN_COLOUR` so colour means one thing within a figure.
- **`HIGH_LABEL`** — one name for the High class. "Highly suitable share",
  "High-class share" and "highly suitable area" were all in use for it.
- **`_pp(x, dp)`** no longer pads. Three decimals only for the factorial
  effects, which are differences of cell counts; two for anything derived from
  a share `_area_statistics` already rounded to two. "+31.210 pp" was inventing
  a digit.
- **`_graticule`** takes round degree values with symbols instead of a linspace
  of the extent.
- Reference lines drawn at `zorder=1` and value labels at `zorder=4+`, so a
  dashed line can no longer cross a number.

All 17 generated figures rebuilt; the collision and edge checks are silent on
the set. Smoke test 11/11.

### Docs

`docs/RESEARCH_CONTEXT.md` — added the scenario table, the correlation
results, both effective-weight measures, the ECDF breakpoint shares, the
edge-effect test and the consensus areas, all under the 2026-10-02 banner.

### Still open from this review

- Figures 1, 3, 4, 7, 20 (QGIS and drawing tool), 21 and 22 not yet reviewed.
  **21 is the priority**: it decides whether the 9 pp Low shift is a ranking
  effect or a breakpoint effect.
- Effect sizes in km² on the figures themselves.
- The eight-paper criterion coding for Table 3 still needs human work.

---

## 2026-10-03 — Figure review round 3; PNG-only output; generator-level guards

### Output

- **PDFs dropped.** `_save()` writes PNG only and the 17 vector copies in
  `outputs/figures/` were deleted. The comment in `_save()` says how to add
  `fig.savefig(stem + ".pdf")` back if a journal asks for vector art.

### Figure 10 — four-method classified surfaces

- **Map furniture no longer prints over the data.** `_clear_corner()` measures
  the district mask and returns the emptiest corner. Measured occupancy:
  upper-left **0.0%**, lower-right 4.7%, lower-left 21.1%, upper-right 59.2%.
  The two previous attempts — figure coordinates outside every panel, then
  panel (a)'s lower-left — both overprinted.
- **Scale bar 25 km → 20 km.** The frame is 124.8 km wide, so a 25 km bar is
  exactly 0.20 of it and the north arrow beside it landed on the district
  outline. At 20 km both fit inside the empty block.
- Subtitles carry percentages only; km² moved to the caption, which was what
  pushed panels (b) and (d) to the image edge.

### Figure 11 — factorial interaction

- Annotation is sans-serif in two right-aligned columns. Space-padding a
  monospace string did not line up, and it was the only monospace text in the
  set. All three values now at one precision.

### Figure 12 — effect magnitudes

- **Retitled.** Was "What moves the result depends on which class you look at",
  which claims the ranking of drivers changes between classes. It does not —
  both panels order them rainfall, soil, aggregation, weighting, interaction.
  Only the aggregation magnitude changes, 0.96 pp on High against 9.03 pp on
  Low. Now "Scoring dominates both classes; aggregation matters for Low, not
  High".
- **Shared x-axis**, fixed 0–46 pp. The panels had autoscaled to 0–40 and
  0–50, which drew the 9.03 pp bar barely longer than the 0.96 pp one.
- Three decimals throughout via `_pp` (round-half-up), so the interaction on
  High reads −0.165 pp rather than a signed-zero "+0.00 pp", and the Low
  interaction reads "0.000 pp" unsigned.
- Caption states the shared axis and the breakpoint dependence.

### Generator-level

- **`_text_overruns()`**, run on every `_save`, reports any Text artist
  reaching the image edge. It found two real clips that had survived three
  review rounds: Figure 2's footnote at `y=-0.055` and its suptitle at
  `y=1.02`, and Figure 5's footnote at `y=-0.035`. All three were placed off
  the canvas, which renders only under `bbox_inches="tight"` — which `_save`
  does not use. Fixed with `tight_layout(rect=...)`. Tick labels are excluded:
  matplotlib parks a Text for every tick it has ever laid out, including ones
  outside the view limits that are never drawn.
- **`_pp(x, dp)`** formats a percentage-point effect with `ROUND_HALF_UP`.
  Python's round-half-even printed −0.565 as −0.56, where a reader checking
  the text against the figure expects −0.57.
- Module docstring now records the conventions figures are reviewed against:
  shared axes for panels plotting the same quantity (and explicitly NOT for
  Figures 17 and 18, whose panels plot different ones), text inside the canvas,
  furniture from `_clear_corner`, one precision per figure.

All 17 generated figures rebuilt; the overrun check is now silent on the set.

### Docs

- **`docs/RESEARCH_CONTEXT.md` carried no notice of the soil correction.** It
  was audited 2026-08-26 and every [RUN] result in it is superseded, including
  the abstract headline in §25 claiming aggregation moves highly-suitable area
  by ~5 pp. Added a banner with the corrected headline figures, the restated
  finding (ranking, not area), and the factorial effects on both class shares.
  §26 discrepancy items 1 and 8 updated — item 8, "soil class coding
  unverified", is now resolved and was wrong.

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
