# CLAUDE.md

## Project

RWH SiteFinder selects rainwater harvesting sites in Chandrapur district,
Maharashtra. It scores an 11,412 km² area on a 450 × 422 grid (~0.30 × 0.31 km
per cell, 123,555 in-district cells) against **6 criteria** from **7 source
datasets**, combines them by AHP-weighted linear combination (CR **0.0235**),
and returns a Low/Medium/High map plus 25 ranked candidate sites.

## Pipeline

| # | Stage | Module |
|---|---|---|
| 1 | AHP (or Fuzzy-AHP) matrix → weights + consistency ratio | `ahp.py`, `algorithms.py` |
| 2 | Common grid + district mask from `boundary.geojson` | `gis_analysis.py` |
| 3 | Reproject rasters onto grid; nearest-fill gaps inside district | `gis_analysis.py` |
| 4 | Score each criterion to 0–1 (ramps, categorical lookups, moderate-optimal) | `criteria.py` |
| 5 | Derive drainage density (2.5 km window) and settlement distance (km) | `gis_analysis.py` |
| 6 | Aggregation (WLC or TOPSIS); per-pixel weight renormalisation; ≥80% coverage gate | `algorithms.py` |
| 7 | Classify by fixed thresholds (0.65 / 0.85); area statistics | `gis_analysis.py` |
| 8 | Candidate extraction: best-per-tile, then global maxima, 5 km separation | `gis_analysis.py` |
| 9 | Folium map + per-site explainability | `utils/map_renderer.py` |
| 10 | Streamlit UI | `app.py` |

Stages 2–5 are weight-independent (`build_criteria_stack()`, cached); 6–9 are
`score_stack(weights, aggregator)`, ~0.15 s — that split makes scenarios,
algorithms and sensitivity cheap. Side branch: `derived_maps.py` → hydrology surfaces.

## Key files

| Path | Owns |
|---|---|
| `criteria.py` | All 0–1 scoring. Every threshold, ramp anchor and lookup table lives here and nowhere else |
| `gis_analysis.py` | Grid, masking, reprojection, gap fill, distance/density, overlay, classification, candidates |
| `ahp.py` | Pairwise matrix, geometric-mean weights, consistency ratio, `SCENARIOS` presets |
| `exports.py` | Result → CSV / GeoJSON / GeoTIFF / PNG bytes, provenance embedded |
| `sensitivity.py` | ±delta perturbation, map removal (Lodwick), effective weights |
| `algorithms.py` | WLC/TOPSIS aggregators, Fuzzy-AHP weights, cross-algorithm comparison |
| `validation.py` | ROC-AUC of the surface against known structures (needs data) |
| `consensus.py` | Consensus sites (Borda) + agreement raster across algorithms/scenarios |
| `app.py` | Streamlit entry point |
| `utils/map_renderer.py` | Folium map, legend, site popups |
| `build_rainfall.py` | CHIRPS annual/monthly → `data/rainfall.tif` |
| `derived_maps.py` | SCS-CN runoff and drainage surfaces → `outputs/` |
| `tools/inspect.py` | Data profiling CLI · `tools/smoke_test.py` end-to-end app test |
| `tools/paper_figures.py` | Every number cited in the paper, by section · `tools/ahp_audit.py` AHP matrix audit |
| `docs/METHODOLOGY.md` | Justification for every number in `criteria.py` |
| `docs/PAPER_GUIDE.md` | Verified figures + plan for the research paper |
| `CHANGELOG.md` | Dated change record (no git) · `TODO.md` backlog · `docs/SOIL_LEGEND_CORRECTION.md` |
| `RUNBOOK.md` | Every command: purpose, outputs, runtime, troubleshooting |
| `data/boundary.geojson` | District polygon, EPSG:4326. Study-area mask |
| `data/rivers.geojson` | HydroRIVERS, 776 features, 2,768 km, `ORD_STRA` 1–7 |
| `data/rainfall.tif` | Mean annual mm/yr, 1,184–1,713. Built from the 11 `chirps-v3.0.YYYY.tif` globals |
| `data/slope.tif` | Degrees, 0–72.4 (HydroSHEDS → GDAL Slope). `data/dem.tif` is 100% NoData and unused |
| `data/soil_texture.tif` | SoilGrids TEXMHT USDA texture; {1,4,6,7} = Clay / Clay Loam / Sandy Clay Loam / Loam |
| `data/lulc.tif` · `data/population.tif` | MODIS IGBP `LC_Type1`, 11 of 17 present · WorldPop people/km² |

## Conventions

- **CRS** EPSG:4326; inputs reprojected at run time. **Grid** `DEFAULT_MAX_GRID_SIZE = 450`.
- **Resampling** bilinear for continuous, nearest for categorical — averaging class codes invents classes.
- **NoData** `-9999`, float32, deflate. CHIRPS ships `-9999` *undeclared*. Gaps inside the district are nearest-filled.
- **Coverage gate** pixel scored only if ≥80% of total AHP weight has data (`MIN_WEIGHT_COVERAGE`).
- **Scoring** belongs in `criteria.py`; never inline thresholds elsewhere. `data/`
  uses fixed short names; generated rasters carry provenance in tags.
- **Outputs** to `outputs/` (gitignored). `data/*.tif` gitignored; the two `.geojson` tracked.

## Commands

Run from the repo root with the project venv (`venv/`).

```powershell
venv\Scripts\Activate.ps1 ; pip install -r requirements.txt   # verified
streamlit run app.py                       # verified — click "Run Suitability Analysis"
python build_rainfall.py                   # verified (full run 2026-08-04)
python derived_maps.py                     # verified (--storm-mm N to change design storm)
python tools/inspect.py <path> [--rows N] [--cols A,B]   # verified
python exports.py                          # verified — 5 artefacts to outputs/
python sensitivity.py                      # verified — 3 analyses, ~3.7 s
python algorithms.py                       # verified — compares all 4 algorithms, ~2.8 s
python consensus.py [--write]              # verified — consensus both axes, ~3 s
python validation.py                       # verified — reports missing_data until structures exist
python tools/smoke_test.py                 # verified — 11 checks, ~40 s
python tools/paper_figures.py [--csv-dir D] # verified — all paper numbers, ~25 s
python tools/ahp_audit.py                  # verified — matrix audit, ~70 s
```

No CLI wrapper — call `run_ahp_analysis('data')` via `python -c`. `setup_data.py`
is **unverified**. No report generation, no ML, no pytest. See `RUNBOOK.md`.

## Current state

Complete: the full pipeline above · exports · editable matrix · 5 scenarios ·
3 sensitivity analyses · 4-algorithm comparison (Spearman ρ) · Borda consensus +
agreement raster · rainfall builder · hydrology maps · AHP matrix audit.

Not complete: ReportLab report. **AUC harness written and verified, but
`data/rwh_structures.geojson` does not exist** → `missing_data`. Blocks
validation and Sprint 4. Never report an AUC until it runs on real data.
Collection protocol: `docs/VALIDATION_PROTOCOL.md`.

Baseline (AHP+WLC): High **6.44%** (735 km²) / Medium 52.5% / Low 41.1%; sites
0.957 → 0.854. Sensitivity ±20%: 88% of top-10 kept, max shift 3; soil most
influential. **Aggregation dominates weighting on RANKING, not area**:
WLC→TOPSIS keeps 5/10 sites (87% class agreement, ρ 0.964), AHP→Fuzzy-AHP keeps
10/10 (99%); the area gap is only 0.79 pp vs 0.40 pp. Consensus: 15/35 sites by
all 4 algorithms (528 km²); 2/61 by all 5 scenarios.

⚠ **Soil legend corrected 2026-10-02** — dominant class is Clay Loam, not Silt
Loam. Numbers above postdate the fix; anything quoting High 18.5% is superseded.

## Working agreements

- Inspect data with `tools/inspect.py`. Never read large rasters or vector files
  into context wholesale; small config files are fine. When debugging, print the
  specific rows — a targeted read is expected, a full dump is not.
- No invented metrics. Any number in a report, README or resume bullet must be
  traceable to a command that can be rerun, and is not a claim until it is.
