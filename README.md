# 💧 RWH Site Suitability Planner
### Suitability Analysis for Rainwater Harvesting Site Planning Using GIS
**BTech Major Project — Chandrapur District, Maharashtra**

A GIS-based Multi-Criteria Decision Analysis (MCDA) tool that identifies and ranks
candidate rainwater harvesting sites. Criterion weights come from the Analytic
Hierarchy Process (AHP); criterion scores come from explicit, documented
reclassification tables; the two are combined by Weighted Linear Combination.

---

## 🗂 Project Structure

```
.
├── app.py                 ← Streamlit application (entry point)
├── ahp.py                 ← AHP pairwise matrix, weights, consistency ratio
├── criteria.py            ← Criterion reclassification tables + scoring functions
├── gis_analysis.py        ← Analysis pipeline (grid, scoring, overlay, candidates)
├── algorithms.py          ← WLC / TOPSIS / Fuzzy-AHP engines + comparison
├── sensitivity.py         ← Weight perturbation, map removal, effective weights
├── consensus.py           ← Consensus sites + agreement across variations
├── validation.py          ← ROC-AUC harness (needs a structure inventory)
├── exports.py             ← Result → CSV / GeoJSON / GeoTIFF / PNG
├── build_rainfall.py      ← Builds the mean annual rainfall surface from CHIRPS
├── derived_maps.py        ← Drainage density, Curve Number and runoff surfaces
├── setup_data.py          ← Standardises QGIS export filenames (unverified)
│
├── tools/
│   ├── inspect.py         ← Data profiling CLI
│   ├── smoke_test.py      ← End-to-end application test, 11 checks
│   ├── paper_figures.py   ← Every number cited in the paper, by section
│   ├── ahp_audit.py       ← Audit of the pairwise comparison matrix
│   └── make_figures.py    ← The paper's figures, PDF + PNG at 300 dpi
│
├── utils/map_renderer.py  ← Folium interactive map builder
│
├── data/                  ← Source layers. Rasters are NOT in the repository
│   ├── boundary.geojson   ← Chandrapur district boundary (tracked)
│   ├── rivers.geojson     ← HydroRIVERS drainage network (tracked)
│   └── *.tif              ← ~297 MB, gitignored — see "Getting the data" below
│
├── outputs/
│   ├── figures/           ← The paper's 17 figures, PDF + PNG (tracked)
│   ├── paper/             ← Machine-readable number tables, CSV (tracked)
│   └── *.tif, *.png       ← Regenerable artefacts (gitignored)
│
├── docs/
│   ├── METHODOLOGY.md     ← Every scoring table, with justification
│   ├── AHP_MATRIX_AUDIT.md        ← Why the pairwise matrix is defensible
│   ├── SOIL_LEGEND_CORRECTION.md  ← The 2026-10-02 correction, in full
│   ├── VALIDATION_PROTOCOL.md     ← How to validate, and how not to
│   ├── PAPER_GUIDE.md             ← Plan and verified figures for the paper
│   ├── PAPER_DATA_HANDOFF.md      ← Numbers handed to the paper draft
│   ├── RESEARCH_CONTEXT.md        ← Full audited context, fact-vs-inference tagged
│   ├── FIGURE_SPECS.md            ← The five figures built outside this repo
│   ├── FIGURE_REVIEW_PROTOCOL.md  ← How the figures are reviewed; settled decisions
│   ├── presentation/      ← Deck, speaker notes, full project documentation
│   └── archive/           ← Superseded documents. Do not cite — see its README
│
├── START_HERE.md          ← Read first if you are new to this repo
├── README.md              ← This file
├── RUNBOOK.md             ← Every command, with troubleshooting
├── CHANGELOG.md           ← Dated record of changes
├── TODO.md                ← Backlog
└── CLAUDE.md              ← Conventions and current state, for AI sessions
```

### Getting the data

**The repository does not contain the source rasters.** They are roughly 297 MB
and all freely available; `docs/METHODOLOGY.md` and `docs/RESEARCH_CONTEXT.md`
name the exact product and version for each:

| Layer | Source |
|---|---|
| `rainfall.tif` | Built by `build_rainfall.py` from 11 CHIRPS v3.0 annual globals |
| `slope.tif` | HydroSHEDS CONDEM → GDAL Slope |
| `soil_texture.tif` | ISRIC SoilGrids250m, `TEXMHT_M_sl1` |
| `lulc.tif` | MODIS MCD12Q1, IGBP `LC_Type1` |
| `population.tif` | WorldPop India 2020 |

Because of this, a fresh clone cannot reproduce the analysis without first
obtaining those layers. The paper's figures and number tables are committed for
exactly that reason.

---

## ⚙️ Setup

```bash
cd rwh_gis_assistant
python -m venv venv

# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> **Windows note:** GeoPandas and Rasterio can be awkward to install with pip.
> If you hit build errors, use conda instead:
> `conda install geopandas rasterio folium streamlit numpy pandas shapely pyproj fiona scipy`

Place your QGIS exports in `data/`, then normalise their filenames:

```bash
python setup_data.py
```

Build the mean annual rainfall surface from the CHIRPS annual downloads
(reads only the district window from each global raster):

```bash
python build_rainfall.py
```

Optionally generate the derived hydrological surfaces (drainage density, Curve
Number, runoff depth and runoff coefficient) into `outputs/`:

```bash
python derived_maps.py            # 100 mm design storm by default
python derived_maps.py --storm-mm 120
```

Export all artefacts, or run the sensitivity sweep, from the command line:

```bash
python exports.py         # writes 5 files to outputs/
python sensitivity.py     # 12-run ±20% sweep, ~1.6 s
python algorithms.py      # compare all 4 algorithms, ~2.8 s
python consensus.py --write  # consensus sites + agreement maps
python validation.py      # ROC-AUC (needs data/rwh_structures.geojson)
```

Run the app:

```bash
streamlit run app.py
```

Then open `http://localhost:8501`.

---

## 📦 Input Layers

| File | Source dataset | Type | Role |
|---|---|---|---|
| `boundary.geojson` | GADM India ADM2 | Vector polygon | Study-area mask |
| `rivers.geojson` | HydroRIVERS v1.0 | Vector lines | Drainage proximity criterion |
| `rainfall.tif` | CHIRPS v3.0 annual, 2014–2024 | Raster (mm/yr) | Rainfall criterion |
| `slope.tif` | HydroSHEDS CONDEM → GDAL Slope | Raster (degrees) | Slope criterion |
| `soil_texture.tif` | SoilGrids 250 m | Raster (categorical) | Soil criterion |
| `lulc.tif` | MODIS MCD12Q1 `LC_Type1` | Raster (categorical) | Land-cover criterion |
| `population.tif` | WorldPop 2020 | Raster (people/km²) | Settlement proximity criterion |

Export vectors as GeoJSON and rasters as GeoTIFF. The pipeline reprojects
everything onto a common EPSG:4326 analysis grid at run time, so the input CRS
does not need to match — but each file must carry a valid CRS.

---

## 🏗 How It Works

```
             boundary.geojson
                    │
                    ▼
    ┌────────────────────────────────┐
    │ 1. Common analysis grid        │  450 px on the long side (~0.3 km/px)
    │    + district mask             │
    └───────────────┬────────────────┘
                    ▼
    ┌────────────────────────────────┐
    │ 2. Reproject each raster onto  │  bilinear for continuous layers,
    │    the grid; gap-fill the rim  │  nearest for categorical ones
    └───────────────┬────────────────┘
                    ▼
    ┌────────────────────────────────┐
    │ 3. Score each criterion 0–1    │  criteria.py — fixed class breaks,
    │    (reclassification tables)   │  categorical lookups, moderate-optimal
    └───────────────┬────────────────┘
                    ▼
    ┌────────────────────────────────┐
    │ 4. AHP weights (CR = 0.0235)   │  ahp.py
    └───────────────┬────────────────┘
                    ▼
    ┌────────────────────────────────┐
    │ 5. Weighted Linear Combination │  → continuous suitability 0–1
    │    → Low / Medium / High       │  → area statistics per class
    └───────────────┬────────────────┘
                    ▼
    ┌────────────────────────────────┐
    │ 6. Candidate extraction        │  best-per-tile, then global maxima
    │    + per-site explainability   │  with 5 km minimum separation
    └───────────────┬────────────────┘
                    ▼
         Folium map + ranked site cards
```

### Criteria and weights

| Criterion | AHP weight | Scoring method |
|---|---|---|
| Rainfall | 0.428 | Benefit — continuous percentile rank (mean annual, 1,184–1,713 mm) |
| Slope | 0.225 | Cost — interpolated ramp in degrees |
| Soil texture | 0.154 | Categorical — explicit texture-class lookup |
| Drainage density | 0.093 | Benefit — km/km² on a 2.5 km moving window, interpolated ramp |
| Land cover | 0.060 | Categorical — IGBP class lookup |
| Settlement proximity | 0.040 | Moderate-optimal — peak 1–5 km from a settlement |

Consistency Ratio **0.0235** (< 0.10, so the judgement matrix is acceptable).

Every number in the scoring tables is justified in
[docs/METHODOLOGY.md](docs/METHODOLOGY.md).

### Current result

Analysing 11,412 km² of Chandrapur (99.7% of the district's official
11,443 km²):

| Class | Share | Area |
|---|---|---|
| High (≥ 0.85) | 18.5% | 2,107 km² |
| Medium (0.65–0.85) | 54.8% | 6,254 km² |
| Low (< 0.65) | 26.7% | 3,051 km² |

A full run takes about 1.6 s.

---

## 🚀 Roadmap

Full backlog, including deferred fixes and the slide updates still outstanding,
is in [TODO.md](TODO.md).

**Sprint 2 — decision-support features** ✅ done
- [x] Export ranked sites (CSV / GeoJSON), suitability raster (GeoTIFF), map (PNG)
- [x] Editable AHP pairwise matrix in the sidebar with live CR recomputation
- [x] Scenario presets — 4 weightings, all CR < 0.10
- [x] One-way sensitivity analysis: ±20% retains 90% of the top-10 on average

**Sprint 3 — methods and validation**
- [x] Four algorithms: AHP/Fuzzy-AHP × WLC/TOPSIS, with a comparison panel
- [ ] Validate against known RWH structures; compute AUC — ⚠ blocked on
      `data/rwh_structures.geojson`, which does not exist yet

**Sprint 4 — multiple scoring engines, including a learned model**
- [ ] Pluggable engines: WLC, AHP-TOPSIS, Fuzzy-AHP, and an ML classifier
- [ ] Train scikit-learn models on known structures; spatial block cross-validation
- [ ] Compare learned feature importance against AHP weights
- [ ] Auto-generate the technical report as PDF (ReportLab)

---

## 📚 Libraries

| Library | Purpose |
|---|---|
| `streamlit` | Web app UI |
| `geopandas` | Vector GIS operations |
| `rasterio` | Raster IO, reprojection, rasterisation, vectorisation |
| `scipy` | Distance transform, gap fill, moving-window convolution |
| `matplotlib` | Derived hydrology map figures |
| `folium` | Interactive Leaflet map |
| `shapely` | Geometry operations |
| `numpy` | Raster array maths |
