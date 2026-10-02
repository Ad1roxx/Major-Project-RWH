# AHP/MCDA logic and calculations (complete, code-accurate)

This document explains how the current application computes AHP weights, builds the MCDA suitability raster, classifies suitability, extracts candidate sites, and displays/compares sites in the UI.

Everything below reflects the current implementation in:
- `ahp.py`
- `gis_analysis.py`
- `utils/map_renderer.py`
- `app.py` / `ui.py`

---

## 0) What “scores” mean in the UI

- Each criterion produces a **normalized suitability score** in the range **[0, 1]** per pixel.
- The UI displays criterion suitability as a percent: `percent = score * 100`.
- These are **relative to the raster values inside the current analysis grid** (district bounds) and are **not physical units**.
  - Example: “Rainfall 82%” means “this pixel is high rainfall relative to other pixels in the district raster after resampling.”

---

## 1) AHP: weights from pairwise comparison matrix

### 1.1 Criteria order

The criteria are in this fixed order:

1. slope
2. rainfall
3. drainage
4. soil
5. lulc
6. population

### 1.2 Pairwise matrix

A default $6\times6$ pairwise comparison matrix $A$ is defined in `ahp.py`.

- $A_{ij}$ expresses how much more important criterion $i$ is than criterion $j$.
- Reciprocal property holds (e.g., $A_{ij}=1/A_{ji}$).

### 1.3 Matrix normalization (column-wise)

Compute column sums:

$$
s_j = \sum_{i=1}^{n} A_{ij}
$$

Normalize each entry:

$$
N_{ij} = \frac{A_{ij}}{s_j}
$$

### 1.4 Weight vector (geometric mean of normalized rows)

Compute geometric mean per row:

$$
g_i = \left(\prod_{j=1}^{n} N_{ij}\right)^{1/n}
$$

Normalize to sum to 1:

$$
w_i = \frac{g_i}{\sum_{k=1}^{n} g_k}
$$

The output is a dict `weights = {criterion: w_i}`.

### 1.5 Optional preference adjustment

If `preferences` contains `{"prioritize": "rainfall"}` (or another criterion name), the implementation:

- Multiplies that criterion’s weight by $(1 + 0.2)$.
- Redistributes the increase evenly across the other criteria.
- Clips negative weights to 0.01 and re-normalizes.

Note: the current Streamlit app calls `run_ahp_analysis({}, data_dir)` (empty preferences), so **default weights are used**.

### 1.6 Consistency ratio (CR)

Given weight vector $w$:

1) Weighted sum vector:

$$
u = A w
$$

2) Consistency vector:

$$
c_i = \frac{u_i}{w_i}
$$

3) Largest eigenvalue estimate:

$$
\lambda_{max} = \frac{1}{n}\sum_{i=1}^{n} c_i
$$

4) Consistency index:

$$
CI = \frac{\lambda_{max} - n}{n - 1}
$$

5) Consistency ratio:

$$
CR = \frac{CI}{RI}
$$

For $n=6$, the implementation uses $RI=1.24$.

---

## 2) Analysis grid: common bounds + capped resolution

### 2.1 Boundary and bounds

- The boundary is loaded from `data/boundary.geojson` when present.
- Bounds are taken from `boundary_gdf.total_bounds`:
  - $(minx, miny, maxx, maxy)$ in EPSG:4326.

If boundary is missing, demo bounds are used.

### 2.2 Create a fixed analysis grid

The grid is created so that the longer side is `max_grid_size` (default 450):

- If width in degrees $dx \ge dy$, then:
  - `width = max_grid_size`
  - `height = round(max_grid_size * dy/dx)`
- Else symmetric.

Transform is computed by `rasterio.transform.from_bounds(minx, miny, maxx, maxy, width, height)`.

Result:
- `common_shape = (height, width)`
- `common_transform`

This is the main performance optimization: all rasters are processed on this smaller grid.

---

## 3) Raster loading and reprojection

For each available raster, the code reprojects it to the common grid:

- Destination CRS: EPSG:4326
- Destination shape: `common_shape`
- Destination transform: `common_transform`

Implementation uses `rasterio.warp.reproject` and writes into a `np.nan`-initialized float array.

### 3.1 Resampling choice per criterion

Configured in `gis_analysis.py`:

- slope: bilinear
- rainfall: bilinear
- drainage: nearest (generated raster)
- soil: nearest
- lulc: nearest
- population: bilinear

---

## 4) Drainage criterion: distance-to-rivers raster

Drainage is computed from `data/rivers.geojson` (or `Clipped_rivers.shp`).

Steps:

1) Rasterize rivers into the common grid using `rasterio.features.rasterize`:
   - River pixels = 1, background = 0
   - `all_touched=True`

2) Compute a fast approximate distance transform using a 2-pass chamfer mask:
   - River pixels have distance 0
   - Neighbor moves cost 1 (N/S/E/W) and $\sqrt{2}$ (diagonals)

Output distance is in **pixel units** (not meters).

3) Normalize with suitability type `moderate` (see normalization section).

---

## 5) Normalization: convert each criterion raster to suitability [0, 1]

All criterion rasters are normalized into the same suitability scale.

Let $x$ be the raw raster value at a pixel, with valid values excluding NaNs.

### 5.1 higher_better

Used for: rainfall, soil, lulc

$$
score = \frac{x - x_{min}}{x_{max} - x_{min}}
$$

If $x_{max} = x_{min}$, score becomes 1 everywhere.

### 5.2 lower_better

Used for: slope, population

$$
score = 1 - \frac{x - x_{min}}{x_{max} - x_{min}}
$$

If $x_{max} = x_{min}$, score becomes 1 everywhere.

### 5.3 moderate

Used for: drainage distance

Let $\mu$ be mean and $\sigma$ be std-dev of valid values.

$$
score = 1 - \frac{|x - \mu|}{3\sigma}
$$

Then:
- clamp to [0, 1]
- if $\sigma = 0$, score becomes 1 everywhere

Interpretation: values near the mean distance are treated as most suitable.

---

## 6) Weighted overlay (MCDA)

Given normalized rasters $R_i$ and weights $w_i$:

$$
Suitability = \sum_i w_i \cdot R_i
$$

Implementation details:

- Initializes suitability array to zeros.
- For each criterion:
  - `weighted_raster = raster * weight`
  - Adds only where `weighted_raster` is not NaN.

Important nuance:
- The overlay does **not** re-normalize weights per-pixel if some criteria are missing/NaN at that pixel.

---

## 7) Suitability classification (high/medium/low)

From all valid suitability values:

- `low_thresh = 33rd percentile`
- `high_thresh = 67th percentile`

Then:

- Low: suitability $\le$ low_thresh -> class 1
- Medium: between thresholds -> class 2
- High: suitability $>$ high_thresh -> class 3

---

## 8) Candidate extraction: select top sites with coverage + separation

Candidate extraction is computed from:

- `suitability` raster
- `classified` raster
- `common_transform`

### 8.1 High-mask

Primary selection mask is:

- `high_mask = (classified == 3) & valid`

If no high cells exist, it falls back to all valid cells.

### 8.2 Stage 1: “best per tile” to enforce spatial coverage

Grid is split into tiles (`tiles=(5,5)` by default).

For each tile:

- Consider only pixels inside `high_mask`.
- Pick the pixel with maximum suitability in that tile.

All tile picks are sorted by score descending and added to the results until `top_n` is reached.

### 8.3 Stage 2: fill remaining slots using separated maxima

If fewer than `top_n` points are selected after tiling:

1) Collect all candidate pixels inside high_mask.
2) Compute `scores = suitability + jitter` where jitter is a deterministic tiny value based on (row, col) hashing.
   - Purpose: break ties in plateaus without randomness.
3) Take a large candidate pool (up to `max(remaining*400, 5000)` pixels) and sort by score.
4) Iterate candidates in descending order and keep a point only if it is at least `DEFAULT_MIN_SEPARATION_KM` (5.0 km) from all already-selected points.

Distance is computed using a haversine formula on (lon, lat) in degrees.

### 8.4 Coordinate extraction

Row/col is converted to lon/lat using:

- `rasterio.transform.xy(common_transform, row, col)`

Each location dict contains:

- `lon`, `lat`
- `suitability_score` (rounded to 3 decimals)
- `rank`

---

## 9) Per-location criterion scoring + “criteria satisfied”

For each selected (row, col):

- For each criterion raster `R_i`, take `val = R_i[row, col]`.
- Store into `criteria_scores` rounded to 3 decimals.
- Mark criterion as satisfied if:

$$
val \ge 0.66
$$

Output per location:

- `criteria_scores: {criterion: score0to1}`
- `criteria_satisfied: [criterion, ...]`

These enriched entries are returned as `top_locations_details`.

---

## 10) High suitability polygons (vectorization)

To display zones on the map:

- Build a mask raster `high_mask = (classified == 3).astype(uint8)`
- Vectorize using `rasterio.features.shapes(high_mask, mask=(high_mask==1), transform=common_transform)`
- Convert geometries to shapely polygons and return as `high_suitability_gdf`.

---

## 11) Map display calculations: tooltip/popup numbers

Candidate display uses:

- Criterion %: `score * 100`
- Contribution: `weight * score`

Criteria are ordered by AHP priority (highest weight first). This ordering is used for:

- Tooltip lines
- Popup list
- Satisfied list ordering

Boundary and high-zones are added as non-interactive layers so they don’t block candidate hover.

---

## 12) Compare panel: arrows + ordering + contributions

Given two selected locations A and B:

### 12.1 Overall suitability arrow

- Compare `a.suitability_score` and `b.suitability_score`.
- If equal (within ~1e-9), show a neutral dash.
- Else:
  - A higher -> A shows green up arrow, B shows red down arrow
  - B higher -> reversed

### 12.2 Per-criterion arrow

For each criterion $c$:

- Compare $scoreA_c$ vs $scoreB_c$.
- If equal (within ~1e-9) or missing -> dash.
- Else higher gets up arrow.

### 12.3 Contribution displayed

For each criterion:

$$
contrib = w_c \cdot score_c
$$

This is shown next to the % as `( +contrib )`.

### 12.4 Ordering

Criteria are listed in descending AHP weight (then a stable fallback order).

---

## 13) Practical interpretation notes (important)

- “High suitability” is relative: it’s the top ~33% of pixels by computed suitability, not an absolute threshold.
- Drainage distances are pixel-based before normalization; because it’s normalized and used as a relative factor, this still works for ranking, but should not be interpreted as meters.
- If you want “distance in meters/km”, drainage should be computed in a projected CRS (e.g., UTM) or using geodesic distance, then normalized.

---

## 14) Quick checklist of constants and defaults

From `gis_analysis.py`:

- `DEFAULT_MAX_GRID_SIZE = 450`
- `DEFAULT_TOP_N = 25`
- `DEFAULT_MIN_SEPARATION_KM = 5.0`
- Candidate tiles: `(5, 5)`
- Criteria satisfied threshold: `0.66`

From `ahp.py`:

- Preference adjustment factor: `+20%`
- Random index for CR: `RI = 1.24` (n=6)
