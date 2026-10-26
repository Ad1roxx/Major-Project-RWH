# RUNBOOK — How to run everything

Every command in the project, what it does, what it writes, and how long it
takes. All commands run **from the repo root** (`rwh_gis_assistant/`, the folder
containing `app.py`).

---

## Quick start

```powershell
cd "C:\Users\Aditya Dubey\Documents\rwh_gis_assistant\rwh_gis_assistant"
venv\Scripts\Activate.ps1
streamlit run app.py
```

Browser opens at `http://localhost:8501`. **Click "Run Suitability Analysis"** —
nothing renders until you do. `Ctrl+C` in the terminal stops it.

---

## Environment

The project venv lives **inside** the project: `rwh_gis_assistant/venv`.

```powershell
venv\Scripts\Activate.ps1          # PowerShell
venv\Scripts\activate.bat          # cmd.exe
pip install -r requirements.txt    # first time, or after pulling changes
```

If PowerShell refuses to run the activation script, skip activating and call the
interpreter directly — every command below works this way too:

```powershell
venv\Scripts\python.exe -m streamlit run app.py
venv\Scripts\python.exe exports.py
```

> ⚠ There is a second, older venv one folder up (`..\venv`). It still works but
> is redundant. Use the project one. If you delete anything, delete the outer one.

---

## Command reference

| Command | What it does | Writes | Time |
|---|---|---|---|
| `streamlit run app.py` | Interactive app: map, ranked sites, scenarios, algorithm picker, exports, sensitivity | — | ~2 s per run |
| `python exports.py` | Exports the baseline result in every format | 5 files → `outputs/` | ~3 s |
| `python sensitivity.py` | Three analyses: ±20% one-way perturbation, map removal (Lodwick), single-parameter effective weights | — (stdout) | ~3.7 s |
| `python algorithms.py` | Runs all 4 algorithms, prints comparison + weights | — (stdout) | ~2.8 s |
| `python derived_maps.py` | Drainage density, Curve Number, runoff depth, runoff coefficient | 4 GeoTIFF + 1 PNG → `outputs/` | ~4 s |
| `python build_rainfall.py` | Rebuilds the mean annual rainfall surface from the CHIRPS globals | `data/rainfall.tif` | ~5 s |
| `python consensus.py` | Consensus sites + agreement across algorithms and scenarios | — (stdout) | ~3 s |
| `python consensus.py --write` | Same, plus CSV + agreement PNG per axis | 4 files → `outputs/` | ~5 s |
| `python validation.py` | ROC-AUC against known structures | — (stdout) | ~2 s |
| `python tools/inspect.py <path>` | Profiles any data file without dumping it | — (stdout) | <1 s |
| `python tools/paper_figures.py` | Every number and figure dataset cited in the paper, by section | — (stdout) | ~25 s |
| `python tools/paper_figures.py --csv-dir DIR` | Same, plus machine-readable CSVs per section | 12 CSVs → DIR | ~30 s |
| `python tools/ahp_audit.py` | AHP matrix audit: consistency diagnostic, perturbation, Monte Carlo | — (stdout) | ~70 s |
| `python tools/smoke_test.py` | End-to-end app test: loads the script, runs the analysis, switches scenario and algorithm, clicks every button. **Run as `PYTHONPATH=. venv\Scripts\python.exe -P tools/smoke_test.py`** or app.py cannot import `gis_analysis` | — (exit 0/1) | ~40 s |
| `python -P tools/make_figures.py [--only N]` | The 17 generated paper figures | PNG → `outputs/figures/` | ~1–2 min |
| `python -P tools/build_figure_data.py` | Figure datasets and captions, then the figures | `FIGURE_DATA.md` + PNGs | ~2 min |
| `python -P tools/validate_mgnrega.py` | Agreement of all 20 surfaces with MGNREGA water works, plus the CGWB comparison (seed 42) | `outputs/validation/` + `fig_val_roc/scores/gain.png` | ~1.5 min |
| `python -P tools/prep_map_layers.py` | Inputs for the QGIS figures (outlines, grid window, scores, method maps, consensus) | `outputs/figures/qgis/inputs/` | ~1 min |
| `"C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" -P tools/qgis_figures.py <fig01\|fig03\|fig04\|fig07\|fig20\|hydrology\|fig_val_map>` | QGIS-rendered map and diagram figures; **runs in QGIS's Python, not the venv** | PNG + editable `.qgz` | ~20 s each |
| `python tools/pull_mgnrega.py` | Re-pulls the Bhuvan geotags (already saved; do not re-run without need) | `data/raw/mgnrega/` | ~2 min |
| `python -P tools/inspect_mgnrega.py` / `inspect_mgnrega_2.py` | Inspection reports and the 240-photo audit sample | `reports/` | <1 min |
| `python -P tools/build_structure_layer.py` | Photo-confirmed structures and thumbnails for the web map | `reports/photo_audit/map_layer/` (git-ignored) | <1 min |
| `python setup_data.py` | Standardises QGIS export filenames | ⚠ **renames files in `data/`** | — |

### Useful flags

```powershell
python derived_maps.py --storm-mm 120        # different design storm (default 100)
python build_rainfall.py --years 2015 2024   # restrict the year range
python validation.py --structures path.geojson
python tools/inspect.py data/rivers.geojson --rows 5
python tools/paper_figures.py --section 9     # one section only
python tools/ahp_audit.py --part C            # Monte Carlo only
python tools/inspect.py data/soil_texture.tif --cols ORD_STRA,LENGTH_KM
```

### Running the pipeline without the app

There is no CLI wrapper for the analysis itself. To get numbers straight out:

```powershell
python -c "from gis_analysis import run_ahp_analysis; r=run_ahp_analysis('data'); print(r['area_statistics'])"
```

For a specific scenario or algorithm:

```powershell
python -c "from gis_analysis import build_criteria_stack, score_stack; from ahp import ahp_engine; from algorithms import weights_for_algorithm; s=build_criteria_stack('data'); w,agg,_=weights_for_algorithm('AHP + TOPSIS', ahp_engine.matrix, ahp_engine.criteria); r=score_stack(s,w,aggregator=agg); print(r['area_statistics'])"
```

---

## Common workflows

**Regenerate every figure and table for the report**
```powershell
python exports.py          # suitability map PNG + site table CSV/GeoJSON + GeoTIFFs
python derived_maps.py     # hydrology 4-panel figure
python sensitivity.py      # sensitivity table
python algorithms.py       # algorithm comparison table (incl. Spearman)
python consensus.py --write # consensus tables + agreement maps
```
Everything lands in `outputs/`, except the stdout tables which you copy.

**I replaced a file in `data/`**
The criteria stack is cached in memory per process, so just restart the app or
the script. Within one Python session, call
`gis_analysis.clear_stack_cache()`.

**I want to check what's inside a data file**
```powershell
python tools/inspect.py data/rainfall.tif
python tools/inspect.py data/rivers.geojson --rows 3
```
Never open rasters by reading them wholesale — this prints ~20 lines instead.

**Demo for the guide**
Start the app, click Run, then walk through: map → zone statistics → ranked
sites → change Scenario in the sidebar (map updates in ~0.15 s) → change
Algorithm → Compare all algorithms → Run sensitivity → download the CSV.

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'rasterio._base'`** (or `pandas._libs...`,
`shapely.lib`, `pyproj._context`, `fiona._env`)
Compiled extensions are missing — a damaged install. Rebuild the venv:
```powershell
Remove-Item -Recurse -Force venv
py -3.11 -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
```
`requirements.txt` pins `rasterio<1.5.0`; **1.5.0 was the version that broke.**

**`module 'inspect' has no attribute 'cleandoc'`**
Something re-added the `tools/` directory to `sys.path`. `tools/inspect.py`
shadows Python's standard-library `inspect` module; the file strips its own
directory from `sys.path` at the top to prevent this. Don't remove those lines.

**PowerShell won't run `Activate.ps1`**
Use `venv\Scripts\python.exe <script>` directly, or
`Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`.

**Streamlit port already in use**
`streamlit run app.py --server.port 8502`

**"ValueError: assignment destination is read-only"**
Fixed 2026-08-12. `st.data_editor` returns a DataFrame backed by a read-only
buffer, so the matrix editor must copy with `np.array(..., copy=True)` before
enforcing reciprocity. If it reappears, something changed `np.array` back to
`np.asarray` in `app.py`.

**I changed the app and want to know it still works**
`python tools/smoke_test.py`. Note that `streamlit run app.py` starting
successfully proves very little — the script body does not execute until a
browser connects.

**The app shows an old result after I changed weights**
It re-scores automatically when the weight vector changes. If it looks stuck,
press "Run Suitability Analysis" again.

**Unicode errors when piping output on Windows**
`$env:PYTHONIOENCODING="utf-8"` before the command.

---

## What does not exist

Listed so nobody hunts for them:

- **No test framework.** There is no pytest configuration. `tools/smoke_test.py`
  is a standalone script — run it directly, not via pytest.
- **No report generation.** ReportLab is not in the project.
- **No machine learning.** scikit-learn is not installed; there is no model.
- **No validation result.** `validation.py` runs but reports `missing_data`
  until `data/rwh_structures.geojson` exists — see TODO.md §A1b.

---

## Where things are documented

| Question | File |
|---|---|
| Why is a threshold set to that value? | `docs/METHODOLOGY.md` |
| What changed, when, and why? | `CHANGELOG.md` |
| What is still to do? | `TODO.md` |
| Numbers and structure for the paper | `docs/PAPER_GUIDE.md` |
| Data handed to the paper-drafting session | `docs/PAPER_DATA_HANDOFF.md` |
| Why the AHP matrix is defensible | `docs/AHP_MATRIX_AUDIT.md` |
| How to validate against real structures | `docs/VALIDATION_PROTOCOL.md` |
| Project overview and setup | `README.md` |
| Conventions and current state (for AI sessions) | `CLAUDE.md` |
