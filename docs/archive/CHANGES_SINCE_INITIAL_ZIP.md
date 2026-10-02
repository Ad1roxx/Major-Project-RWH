# Changes made since the initial ZIP (session-reconstructed)

This project folder does not contain a git history, so an exact line-by-line diff versus the original ZIP cannot be generated automatically.

This document summarizes the changes that were made during this Copilot refactor session, based on the current codebase state and the session requirements that were implemented.

## High-level outcome

- Added AHP/MCDA suitability analysis as the primary workflow.
- Integrated **Derived Slope** and **Soil Texture** rasters into the AHP criteria set.
- Made the analysis fast enough for interactive use by using a fixed **common grid** capped in resolution.
- Simplified the UX into a **single-button workflow** (no “complete prompt” section).
- Made the map “map-first”: candidate sites are shown **on the map** with per-criterion suitability breakdowns.
- Added a **side-by-side compare** panel with priority ordering, and fixed Streamlit rerun issues by persisting results.

## Detailed change list (by feature)

### 1) Data layers: add slope + soil texture (and show them as “ticked”)

- Sidebar “Data Status” includes:
  - `slope.tif` (Derived Slope), with fallback to legacy filename `Derived_Slope(Degrees).tif`.
  - `soil_texture.tif` (Soil Texture), with fallbacks `Soil_Texture_Chandrapur(correct CRS).tif` and `soil.tif`.
- Setup script renames common QGIS exports to these standardized names.

### 2) Performance: make analysis much faster

The analysis pipeline is now designed around a single fixed analysis grid derived from the boundary bounds:

- A common grid is created from boundary bounds and capped by `DEFAULT_MAX_GRID_SIZE` (450).
- All rasters are reprojected onto this grid once, and computations are performed on the resampled arrays.

This reduces runtime dramatically compared to repeatedly loading and processing full-resolution rasters.

### 3) AHP/MCDA pipeline integrated end-to-end

- Suitability is produced by:
  - AHP weights (pairwise matrix) → normalized raster criteria → weighted overlay.
  - Suitability classification using percentiles.
- Drainage is generated as a distance-to-rivers raster (no precomputed raster required).

### 4) Candidate extraction: reduce clustering and improve district coverage

- Candidate selection is not “top-N pixels only” anymore.
- It uses:
  - Best-per-tile selection inside high-suitability cells to encourage coverage.
  - A second-stage fill that enforces a minimum separation (default 5 km) using a haversine distance check.
  - Deterministic tie-breaking to avoid selecting only top-left pixels in equal-score plateaus.

### 5) Map rendering: candidates + criteria breakdown on-map

- The Folium map shows:
  - Boundary outline (non-interactive so it doesn’t steal hover events).
  - Rivers.
  - High suitability zones.
  - Candidate points with tooltip + popup.
- Candidate tooltip/popup contains:
  - Rank and overall suitability score.
  - Per-criterion normalized suitability as %.
  - AHP weight and weighted contribution per criterion: `contrib = weight × score`.
  - “Criteria satisfied” list based on a normalized suitability threshold.

### 6) UI: single-button workflow + comparison + rerun-safe state

- The Streamlit UI has one primary action: **Run Suitability Analysis**.
- Results are persisted in `st.session_state["analysis_result"]` so changing compare selections does not wipe outputs.
- Added **Compare Candidate Sites** panel:
  - Two site selectors.
  - Green up arrow for “better”, red down arrow for “worse”, and dash for ties/unknown.
  - Criteria are ordered by AHP priority (highest weight first).
  - Shows per-criterion contributions (`w×score`) next to the %.

## What changed (by file)

### Core analysis

- `gis_analysis.py`
  - Implemented the fast, common-grid AHP pipeline.
  - Added slope + soil texture into raster configuration and filename resolution.
  - Added drainage distance raster generation from rivers.
  - Added candidate selection that spreads sites across the district.
  - Added `top_locations_details` with per-criterion scores + satisfied list.

- `ahp.py`
  - Defines the AHP engine: pairwise matrix, geometric-mean weight calculation, consistency ratio.

### Map rendering

- `utils/map_renderer.py`
  - Renders boundary/rivers/zones/candidates as togglable layers.
  - Ensures boundary/zones are non-interactive to avoid blocking candidate hover.
  - Shows per-site suitability breakdown and weighted contributions.

### Streamlit UI

- `app.py`
  - Single-button workflow.
  - Data status sidebar including slope + soil texture.
  - Map-first results.
  - Compare panel with arrows and priority ordering.
  - Session-state persistence to prevent refresh/reset.

- `ui.py`
  - Mirrors the same UI workflow (kept in sync with `app.py`).

### Data setup / docs

- `setup_data.py`
  - Adds filename standardization for derived slope and soil texture exports.
  - Prints required/optional data status.

- `README.md`
  - Documents data folder expectations and includes the new raster files.

## Notes / limitations

- “All changes since the initial ZIP” are reconstructed from the implemented requirements and current code state. If you provide the original ZIP contents (or re-add git history), we can generate an exact diff and a precise changelog.
