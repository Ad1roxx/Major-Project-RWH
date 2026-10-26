"""
gis_analysis.py
───────────────
AHP-based weighted overlay analysis for Rainwater Harvesting suitability.

Pipeline
    1. Build one common analysis grid from the district boundary.
    2. Reproject every criterion raster onto that grid.
    3. Score each criterion to 0–1 using the explicit reclassification tables
       in criteria.py (no data-driven min–max rescaling).
    4. Derive the two distance-based criteria (drainage, settlement) in
       kilometres and score them with a moderate-optimal curve.
    5. Mask everything to the district polygon.
    6. Weighted linear combination using AHP weights, renormalised per pixel
       over the criteria that actually have data there.
    7. Classify into Low / Medium / High by fixed score thresholds, report the
       area statistics, and extract ranked candidate sites.
"""

import os
import numpy as np

from ahp import ahp_engine
import criteria as C


DEFAULT_MAX_GRID_SIZE = 450  # caps raster resolution for fast interactive runs
DEFAULT_TOP_N = 25
DEFAULT_MIN_SEPARATION_KM = 5.0

# Mean Earth radii used for the degree → km conversion of the analysis grid.
KM_PER_DEG_LAT = 110.574
KM_PER_DEG_LON_EQUATOR = 111.320


def _first_existing_path(*paths: str) -> str | None:
    for p in paths:
        if p and os.path.exists(p):
            return p
    return None


# ── Lazy imports ───────────────────
def _import_geopandas():
    try:
        import geopandas as gpd
        return gpd
    except ImportError:
        raise ImportError("geopandas not installed. Run: pip install geopandas")


def _import_rasterio():
    try:
        import rasterio
        from rasterio.features import shapes as rio_shapes
        return rasterio, rio_shapes
    except ImportError:
        raise ImportError("rasterio not installed. Run: pip install rasterio")


def _import_shapely():
    from shapely.geometry import shape, mapping, Point, Polygon, MultiPolygon
    from shapely.ops import unary_union
    return shape, mapping, Point, Polygon, MultiPolygon, unary_union


# ─────────────────────────────────────────────────────────────────────────────
# Analysis grid
# ─────────────────────────────────────────────────────────────────────────────

def _make_common_grid(bounds, max_grid_size: int):
    """Create a fixed analysis grid (shape + transform) based on bounds."""
    from rasterio.transform import from_bounds

    minx, miny, maxx, maxy = bounds
    dx = maxx - minx
    dy = maxy - miny
    if dx <= 0 or dy <= 0:
        width = height = min(max_grid_size, 200)
    else:
        if dx >= dy:
            width = max_grid_size
            height = max(1, int(round(max_grid_size * (dy / dx))))
        else:
            height = max_grid_size
            width = max(1, int(round(max_grid_size * (dx / dy))))

    transform = from_bounds(minx, miny, maxx, maxy, width, height)
    return (height, width), transform


def _pixel_size_km(transform, shape) -> tuple[float, float]:
    """Return (pixel_height_km, pixel_width_km) for a geographic (EPSG:4326) grid.

    Longitude degrees shrink with latitude, so the east–west size is evaluated
    at the grid's centre latitude.
    """
    height, _width = shape
    centre_lat = transform.f + (height / 2.0) * transform.e  # transform.e is negative
    dy_km = abs(transform.e) * KM_PER_DEG_LAT
    dx_km = abs(transform.a) * KM_PER_DEG_LON_EQUATOR * np.cos(np.radians(centre_lat))
    return float(dy_km), float(dx_km)


def _pixel_area_km2_per_row(transform, shape) -> np.ndarray:
    """Area in km² of one pixel, per raster row (varies slightly with latitude)."""
    height, _width = shape
    rows = np.arange(height)
    lat_centres = transform.f + (rows + 0.5) * transform.e
    dy_km = abs(transform.e) * KM_PER_DEG_LAT
    dx_km = abs(transform.a) * KM_PER_DEG_LON_EQUATOR * np.cos(np.radians(lat_centres))
    return dy_km * dx_km


def _load_raster_to_grid(tif_path: str, dst_shape, dst_transform,
                         dst_crs: str = "EPSG:4326", band: int = 1,
                         resampling: str = "bilinear"):
    """Reproject a raster band onto the fixed analysis grid."""
    rasterio = _import_rasterio()[0]
    from rasterio.warp import reproject, Resampling

    resampling_map = {
        "nearest": Resampling.nearest,
        "bilinear": Resampling.bilinear,
    }
    resampling_method = resampling_map.get(resampling, Resampling.bilinear)

    with rasterio.open(tif_path) as src:
        dst = np.full(dst_shape, np.nan, dtype=np.float32)
        src_crs = src.crs if src.crs is not None else dst_crs
        reproject(
            source=rasterio.band(src, band),
            destination=dst,
            src_transform=src.transform,
            src_crs=src_crs,
            src_nodata=src.nodata,
            dst_transform=dst_transform,
            dst_crs=dst_crs,
            dst_nodata=np.nan,
            resampling=resampling_method,
        )
        profile = src.profile

    return np.array(dst, dtype=float), dst_transform, profile


def _rasterize_boundary(boundary_gdf, out_shape, out_transform) -> np.ndarray | None:
    """Boolean mask that is True inside the district polygon."""
    if boundary_gdf is None or len(boundary_gdf) == 0:
        return None
    from rasterio.features import rasterize

    try:
        geoms = [(geom, 1) for geom in boundary_gdf.geometry
                 if geom is not None and not geom.is_empty]
        if not geoms:
            return None
        mask = rasterize(geoms, out_shape=out_shape, transform=out_transform,
                         fill=0, dtype="uint8", all_touched=True)
        return mask.astype(bool)
    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Distance rasters
# ─────────────────────────────────────────────────────────────────────────────

def _distance_transform_chamfer(binary_mask: np.ndarray) -> np.ndarray:
    """Approximate Euclidean distance transform in PIXEL units (2-pass chamfer).

    Fallback for when SciPy is unavailable. SciPy's exact transform is used
    when it can be imported (see _distance_km).
    """
    h, w = binary_mask.shape
    inf = np.float32(1e9)
    dist = np.full((h, w), inf, dtype=np.float32)
    dist[binary_mask.astype(bool)] = 0.0

    sqrt2 = np.float32(1.41421356)
    for y in range(h):
        for x in range(w):
            v = dist[y, x]
            if y > 0:
                v = min(v, dist[y - 1, x] + 1.0)
                if x > 0:
                    v = min(v, dist[y - 1, x - 1] + sqrt2)
                if x + 1 < w:
                    v = min(v, dist[y - 1, x + 1] + sqrt2)
            if x > 0:
                v = min(v, dist[y, x - 1] + 1.0)
            dist[y, x] = v

    for y in range(h - 1, -1, -1):
        for x in range(w - 1, -1, -1):
            v = dist[y, x]
            if y + 1 < h:
                v = min(v, dist[y + 1, x] + 1.0)
                if x > 0:
                    v = min(v, dist[y + 1, x - 1] + sqrt2)
                if x + 1 < w:
                    v = min(v, dist[y + 1, x + 1] + sqrt2)
            if x + 1 < w:
                v = min(v, dist[y, x + 1] + 1.0)
            dist[y, x] = v

    return dist


def _distance_km(source_mask: np.ndarray, dy_km: float, dx_km: float) -> np.ndarray | None:
    """Distance from every pixel to the nearest True pixel in `source_mask`, in km.

    Uses SciPy's exact anisotropic EDT when available; otherwise falls back to
    the chamfer approximation scaled by the mean pixel size.
    """
    if not np.any(source_mask):
        return None

    try:
        from scipy.ndimage import distance_transform_edt
        return np.asarray(
            distance_transform_edt(~source_mask, sampling=(dy_km, dx_km)),
            dtype=np.float32,
        )
    except ImportError:
        mean_px_km = (dy_km + dx_km) / 2.0
        return _distance_transform_chamfer(source_mask) * np.float32(mean_px_km)


def _fill_nearest(data: np.ndarray, domain: np.ndarray | None) -> tuple[np.ndarray, int]:
    """Fill NoData gaps inside `domain` with the nearest valid value.

    The criterion rasters come from different sources at different resolutions
    (CHIRPS rainfall is a ~5 km grid), so several of them stop just short of the
    district boundary. Rather than discard the whole rim, gaps *inside* the
    district are filled from the nearest valid pixel — appropriate for layers
    that vary slowly in space, and it keeps the analysis covering the full
    district area.

    Returns (filled, n_filled). Requires SciPy; without it the array is
    returned unchanged and the coverage gate in _weighted_overlay handles the
    rim instead.
    """
    if domain is None:
        return data, 0
    gaps = domain & np.isnan(data)
    n_gaps = int(gaps.sum())
    if n_gaps == 0:
        return data, 0

    try:
        from scipy.ndimage import distance_transform_edt
    except ImportError:
        return data, 0

    valid = ~np.isnan(data)
    if not valid.any():
        return data, 0

    _dist, (iy, ix) = distance_transform_edt(~valid, return_indices=True)
    filled = data.copy()
    filled[gaps] = data[iy[gaps], ix[gaps]]
    return filled, n_gaps


def _river_length_grid(rivers_gdf, out_shape, out_transform,
                       segment_m: float = 100.0) -> np.ndarray | None:
    """Total river length (km) falling inside each analysis cell.

    Rasterising the lines would only give a boolean "channel present" mask,
    which cannot produce a density in km/km². Instead each line is densified
    into ~100 m segments and every segment's length is accumulated into the
    cell containing its midpoint. Segment length is measured on the ellipsoid
    via local degree-to-km scaling, so the result is in true kilometres.
    """
    rasterio = _import_rasterio()[0]
    import geopandas as gpd

    try:
        dense = rivers_gdf.to_crs("EPSG:32644").segmentize(segment_m)
        dense = gpd.GeoDataFrame(geometry=dense, crs="EPSG:32644").to_crs("EPSG:4326")
    except Exception:
        dense = rivers_gdf

    xs, ys, lengths = [], [], []
    for geom in dense.geometry:
        if geom is None or geom.is_empty:
            continue
        parts = geom.geoms if geom.geom_type == "MultiLineString" else [geom]
        for line in parts:
            coords = np.asarray(line.coords)
            if len(coords) < 2:
                continue
            mid_lat = (coords[:-1, 1] + coords[1:, 1]) / 2.0
            d_lon = (coords[1:, 0] - coords[:-1, 0]) * KM_PER_DEG_LON_EQUATOR * np.cos(np.radians(mid_lat))
            d_lat = (coords[1:, 1] - coords[:-1, 1]) * KM_PER_DEG_LAT
            xs.append((coords[:-1, 0] + coords[1:, 0]) / 2.0)
            ys.append(mid_lat)
            lengths.append(np.sqrt(d_lon ** 2 + d_lat ** 2))

    if not lengths:
        return None

    xs = np.concatenate(xs)
    ys = np.concatenate(ys)
    lengths = np.concatenate(lengths)

    rows, cols = rasterio.transform.rowcol(out_transform, xs, ys)
    rows = np.asarray(rows)
    cols = np.asarray(cols)
    inside = (rows >= 0) & (rows < out_shape[0]) & (cols >= 0) & (cols < out_shape[1])

    grid = np.zeros(out_shape, dtype=np.float64)
    np.add.at(grid, (rows[inside], cols[inside]), lengths[inside])
    return grid


def _drainage_density(length_grid: np.ndarray, dy_km: float, dx_km: float,
                      radius_km: float) -> np.ndarray:
    """Drainage density in km/km² over a circular moving window."""
    from scipy.ndimage import convolve

    ry = max(1, int(round(radius_km / dy_km)))
    rx = max(1, int(round(radius_km / dx_km)))
    yy, xx = np.mgrid[-ry:ry + 1, -rx:rx + 1]
    kernel = (((yy * dy_km) ** 2 + (xx * dx_km) ** 2) <= radius_km ** 2).astype(np.float64)

    window_km2 = kernel.sum() * dy_km * dx_km
    total_length = convolve(length_grid, kernel, mode="constant", cval=0.0)
    return (total_length / window_km2).astype(np.float32)


# ─────────────────────────────────────────────────────────────────────────────
# Overlay, classification, statistics
# ─────────────────────────────────────────────────────────────────────────────

def _weighted_overlay(raster_dict: dict, weights: dict) -> tuple[np.ndarray, np.ndarray]:
    """Weighted linear combination, renormalised per pixel over available data.

    A pixel where one criterion is NoData is scored using the remaining
    criteria with their weights rescaled to sum to 1, so the output stays on a
    true 0–1 scale instead of being artificially depressed at the edge of a
    layer. Pixels backed by less than criteria.MIN_WEIGHT_COVERAGE of the total
    weight are left as NaN rather than scored from a thin subset of criteria.

    Returns (suitability, weight_coverage).
    """
    shape = next(iter(raster_dict.values())).shape
    weighted_sum = np.zeros(shape, dtype=np.float32)
    weight_sum = np.zeros(shape, dtype=np.float32)

    total_weight = sum(float(weights.get(k, 0.0)) for k in raster_dict)

    for criterion, raster in raster_dict.items():
        w = float(weights.get(criterion, 0.0))
        if w <= 0:
            continue
        valid = ~np.isnan(raster)
        weighted_sum[valid] += raster[valid].astype(np.float32) * w
        weight_sum[valid] += w

    coverage = weight_sum / total_weight if total_weight > 0 else weight_sum

    out = np.full(shape, np.nan, dtype=np.float32)
    usable = (weight_sum > 0) & (coverage >= C.MIN_WEIGHT_COVERAGE)
    out[usable] = weighted_sum[usable] / weight_sum[usable]
    return out, coverage


def _classify_suitability(suitability: np.ndarray) -> np.ndarray:
    """Classify into 1=Low / 2=Medium / 3=High.

    Uses the fixed thresholds in criteria.SUITABILITY_THRESHOLDS by default;
    set criteria.CLASSIFICATION_MODE = "percentile" for the 33rd/67th split.
    """
    valid = suitability[~np.isnan(suitability)]
    if len(valid) == 0:
        return np.full_like(suitability, np.nan)

    if C.CLASSIFICATION_MODE == "percentile":
        low_thresh = np.percentile(valid, 33)
        high_thresh = np.percentile(valid, 67)
    else:
        low_thresh, high_thresh = C.SUITABILITY_THRESHOLDS

    classified = np.full_like(suitability, np.nan)
    classified[suitability <= low_thresh] = 1
    classified[(suitability > low_thresh) & (suitability <= high_thresh)] = 2
    classified[suitability > high_thresh] = 3
    return classified


def _area_statistics(classified: np.ndarray, transform, shape) -> dict:
    """Area (km²) and share (%) of the district in each suitability class.

    Shares are **area-weighted, not cell counts.** The analysis grid is in
    EPSG:4326, so a cell's ground area shrinks with latitude: across Chandrapur
    the largest cell is 0.81% bigger than the smallest. The Low class sits
    mostly in the southern half, where the cells are larger, so counting cells
    understates it by about 0.05 pp. Every reported share must come from here
    (or from `class_share_pct`), never from a mean over a boolean mask.

    `percent` is rounded to 2 dp for display. **`percent_exact` is not**, and
    anything that subtracts two shares must use it: the factorial effects in
    the paper's Figure 12 were quantised to 0.01 pp for a while because they
    differenced the rounded field, which is how "+9.030 pp" and "-0.100 pp"
    came to end in a zero they had not earned.
    """
    px_area = _pixel_area_km2_per_row(transform, shape)          # per row
    area_grid = np.repeat(px_area[:, None], shape[1], axis=1)    # full grid

    valid = ~np.isnan(classified)
    total_km2 = float(area_grid[valid].sum())

    stats = {"total_km2": round(total_km2, 1), "classes": {}}
    for code, label in ((3, "High"), (2, "Medium"), (1, "Low")):
        sel = valid & (classified == code)
        km2 = float(area_grid[sel].sum())
        pct = (100.0 * km2 / total_km2) if total_km2 > 0 else 0.0
        stats["classes"][label] = {
            "area_km2": round(km2, 1),
            "percent": round(pct, 2),
            "percent_exact": pct,
            "pixels": int(sel.sum()),
        }
    return stats


def class_share_pct(result: dict, klass: str) -> float:
    """The single source of truth for "x% of the district is <class>".

    Full precision, area-weighted. Figures, tables, captions and
    `docs/RESEARCH_CONTEXT.md` all read shares through this, so they cannot
    report different numbers for the same surface. `tools/smoke_test.py`
    asserts the agreement.
    """
    return float(result["area_statistics"]["classes"][klass]["percent_exact"])


def area_weighted_ecdf(values: np.ndarray, areas: np.ndarray):
    """(sorted values, cumulative % of district area at or below each).

    The area-weighted counterpart of a plain ECDF, so that a curve's height at
    a class breakpoint equals the share `class_share_pct` reports. An unweighted
    ECDF is off by the same ~0.05 pp as a cell count, which is visible when a
    reader checks one figure against another.
    """
    order = np.argsort(values, kind="mergesort")
    v = values[order]
    a = areas[order]
    return v, 100.0 * np.cumsum(a) / a.sum()


def _percentile_rank(data: np.ndarray) -> np.ndarray:
    """Map a raster to its within-district percentile rank in [0, 1]. NaN-safe."""
    out = np.full(data.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(data)
    if not valid.any():
        return out
    vals = data[valid]
    order = np.argsort(vals, kind="stable")
    ranks = np.empty(len(vals), dtype=np.float32)
    ranks[order] = np.arange(len(vals), dtype=np.float32)
    out[valid] = ranks / max(1, len(vals) - 1)
    return out


def _tiebreak_raster(raw_rasters: dict, settlement_km, drainage_density, shape) -> np.ndarray:
    """Continuous 0–1 score used only to order candidates that tie on the
    discrete suitability score.

    The reclassification tables deliberately produce a small set of discrete
    scores, so a few thousand pixels can share the maximum. This raster keeps
    the published suitability map discrete while still giving a defensible,
    deterministic ordering within a plateau: among equally suitable pixels,
    prefer gentler slope, higher rainfall, denser drainage, and a settlement
    distance nearer the centre of the optimal band.
    """
    parts = []

    if 'slope' in raw_rasters:
        parts.append(1.0 - np.clip(raw_rasters['slope'] / 15.0, 0.0, 1.0))
    if 'rainfall' in raw_rasters:
        parts.append(_percentile_rank(raw_rasters['rainfall']))
    if drainage_density is not None:
        parts.append(_percentile_rank(np.asarray(drainage_density, dtype=float)))
    if settlement_km is not None:
        centre = (C.SETTLEMENT_PEAK_KM[0] + C.SETTLEMENT_PEAK_KM[1]) / 2.0
        span = centre + C.SETTLEMENT_FALLOFF_KM
        parts.append(1.0 - np.clip(np.abs(settlement_km - centre) / span, 0.0, 1.0))

    if not parts:
        return np.zeros(shape, dtype=np.float32)

    stacked = np.stack([np.asarray(p, dtype=np.float32) for p in parts])
    with np.errstate(invalid='ignore'):
        mean = np.nanmean(stacked, axis=0)
    return np.nan_to_num(mean, nan=0.0).astype(np.float32)


def _rank_by_score(locations: list[dict], ranker: np.ndarray) -> list[dict]:
    """Renumber sites by score descending, regardless of selection order.

    Ties are broken by the same continuous ranker used during selection, so the
    ordering is total and deterministic.
    """
    locations.sort(
        key=lambda loc: (loc['suitability_score'], float(ranker[loc['row'], loc['col']])),
        reverse=True,
    )
    for position, loc in enumerate(locations, start=1):
        loc['rank'] = position
    return locations


def _extract_top_locations(suitability, classified, transform, top_n=10,
                           tiles=(5, 5), rank_values=None):
    """Extract top N candidate locations from within high-suitability areas.

    Stage 1 — best pixel per tile inside the high-suitability mask, so sites
              are spread across the district rather than clustered.
    Stage 2 — fill remaining slots from global maxima subject to a minimum
              separation distance, with deterministic tie-breaking.
    Stage 3 — renumber every selected site by score, descending.

    Stage 3 matters: the two selection stages each emit their own descending
    run, so a stage-2 site (a global maximum) routinely outscores a late stage-1
    site (the best pixel of a mediocre tile). Numbering in selection order would
    publish rank #22 with a higher score than rank #13. Selection order controls
    *which* sites are chosen — spread across the district — and must not control
    what they are called.

    `rank_values` (optional) orders pixels during selection; the score reported
    for each site is always taken from `suitability`.
    """
    valid_mask = ~np.isnan(suitability)
    if not np.any(valid_mask):
        return []

    if rank_values is None:
        ranker = suitability
    else:
        ranker = np.where(np.isnan(suitability), np.nan,
                          suitability + 1e-3 * np.nan_to_num(rank_values, nan=0.0))

    rasterio = _import_rasterio()[0]

    high_mask = (classified == 3) & valid_mask
    if not np.any(high_mask):
        high_mask = valid_mask

    hgt, wdt = suitability.shape

    tile_rows = max(1, int(tiles[0]))
    tile_cols = max(1, int(tiles[1]))
    row_edges = np.linspace(0, hgt, tile_rows + 1, dtype=int)
    col_edges = np.linspace(0, wdt, tile_cols + 1, dtype=int)

    picked = []
    for r0, r1 in zip(row_edges[:-1], row_edges[1:]):
        for c0, c1 in zip(col_edges[:-1], col_edges[1:]):
            sub_mask = high_mask[r0:r1, c0:c1]
            if not np.any(sub_mask):
                continue
            masked = np.where(sub_mask, ranker[r0:r1, c0:c1], np.nan)
            if np.all(np.isnan(masked)):
                continue
            flat_idx = np.nanargmax(masked)
            rr, cc = np.unravel_index(flat_idx, masked.shape)
            row, col = int(r0 + rr), int(c0 + cc)
            score = float(suitability[row, col])
            if np.isnan(score):
                continue
            picked.append((row, col, score, float(ranker[row, col])))

    # Order tiles by the tie-broken ranking value, not the plateaued score.
    picked.sort(key=lambda x: x[3], reverse=True)

    def _haversine_km(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
        dlon, dlat = lon2 - lon1, lat2 - lat1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        return 6371.0 * (2 * np.arcsin(np.sqrt(a)))

    locations = []
    used = set()
    selected = []
    for row, col, score, _rank in picked:
        if (row, col) in used:
            continue
        lon, lat = rasterio.transform.xy(transform, row, col)
        lon, lat = float(lon), float(lat)
        if any(_haversine_km(lon, lat, p[0], p[1]) < DEFAULT_MIN_SEPARATION_KM
               for p in selected):
            continue
        used.add((row, col))
        selected.append((lon, lat))
        locations.append({
            'lon': lon, 'lat': lat,
            'suitability_score': round(float(score), 3),
            'rank': len(locations) + 1,
            'row': int(row), 'col': int(col),
        })
        if len(locations) >= top_n:
            return _rank_by_score(locations, ranker)

    # Stage 2 — separated global maxima
    rows, cols = np.where(high_mask)
    values = suitability[rows, cols].astype(np.float32)
    rank_at = ranker[rows, cols].astype(np.float32)

    h = (rows.astype(np.int64) * 73856093) ^ (cols.astype(np.int64) * 19349663)
    jitter = ((h % 1000).astype(np.float32) / 1000.0) * 1e-6
    scores = rank_at + jitter

    remaining = top_n - len(locations)
    candidate_pool = min(len(scores), max(remaining * 400, 5000))
    if candidate_pool < len(scores):
        top_idx = np.argpartition(scores, -candidate_pool)[-candidate_pool:]
    else:
        top_idx = np.arange(len(scores))
    top_idx = top_idx[np.argsort(scores[top_idx])[::-1]]

    for idx in top_idx:
        row, col = int(rows[idx]), int(cols[idx])
        if (row, col) in used:
            continue
        lon, lat = rasterio.transform.xy(transform, row, col)
        lon, lat = float(lon), float(lat)
        if any(_haversine_km(lon, lat, p[0], p[1]) < DEFAULT_MIN_SEPARATION_KM
               for p in selected):
            continue
        selected.append((lon, lat))
        used.add((row, col))
        locations.append({
            'lon': lon, 'lat': lat,
            'suitability_score': round(float(values[idx]), 3),
            'rank': len(locations) + 1,
            'row': row, 'col': col,
        })
        if len(locations) >= top_n:
            break

    return _rank_by_score(locations, ranker)


# ─────────────────────────────────────────────────────────────────────────────
# Main analysis
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# Stage 1 — build the criteria stack (independent of AHP weights)
# ─────────────────────────────────────────────────────────────────────────────

_STACK_CACHE: dict = {}


def clear_stack_cache() -> None:
    """Drop the cached criteria stack (call after changing files in data/)."""
    _STACK_CACHE.clear()


def build_criteria_stack(data_dir: str,
                         max_grid_size: int = DEFAULT_MAX_GRID_SIZE,
                         use_cache: bool = True) -> dict:
    """Load and score every criterion to 0–1, independent of AHP weights.

    This is the expensive half of the pipeline — raster reprojection, gap
    filling, distance transforms and the drainage-density convolution. None of
    it depends on the weights, so scenario switching and sensitivity analysis
    reuse one stack and only re-run `score_stack()`.
    """
    key = (os.path.abspath(data_dir), int(max_grid_size))
    if use_cache and key in _STACK_CACHE:
        return _STACK_CACHE[key]

    notes = []

    slope_path = _first_existing_path(
        os.path.join(data_dir, 'slope.tif'),
        os.path.join(data_dir, 'Derived_Slope(Degrees).tif'),
    )
    soil_path = _first_existing_path(
        os.path.join(data_dir, 'soil_texture.tif'),
        os.path.join(data_dir, 'Soil_Texture_Chandrapur(correct CRS).tif'),
        os.path.join(data_dir, 'soil.tif'),
    )

    # 'resampling' must be nearest for categorical layers — averaging class
    # codes would invent classes that do not exist.
    raster_config = {
        'slope':      {'path': slope_path,                                'resampling': 'bilinear'},
        'rainfall':   {'path': os.path.join(data_dir, 'rainfall.tif'),    'resampling': 'bilinear'},
        'soil':       {'path': soil_path,                                 'resampling': 'nearest'},
        'lulc':       {'path': os.path.join(data_dir, 'lulc.tif'),        'resampling': 'nearest'},
        'population': {'path': os.path.join(data_dir, 'population.tif'),  'resampling': 'bilinear'},
        # 'drainage' is derived from the rivers vector, not loaded from disk.
    }

    gpd = _import_geopandas()

    boundary_path = os.path.join(data_dir, 'boundary.geojson')
    boundary_gdf = None
    if os.path.exists(boundary_path):
        boundary_gdf = gpd.read_file(boundary_path)
        bounds = boundary_gdf.total_bounds
    else:
        bounds = [78.85, 19.65, 80.05, 20.65]
        notes.append("⚠️ boundary.geojson missing — using fallback bounds, results are not clipped to the district")

    rivers_gdf = None
    rivers_path = os.path.join(data_dir, 'rivers.geojson')
    if os.path.exists(rivers_path):
        rivers_gdf = gpd.read_file(rivers_path)
    else:
        shp_path = os.path.join(data_dir, 'Clipped_rivers.shp')
        if os.path.exists(shp_path):
            rivers_gdf = gpd.read_file(shp_path)

    common_shape, common_transform = _make_common_grid(bounds, max_grid_size)
    dy_km, dx_km = _pixel_size_km(common_transform, common_shape)
    notes.append(
        f"ℹ️ Analysis grid {common_shape[0]}×{common_shape[1]} px "
        f"(≈{dx_km:.2f} × {dy_km:.2f} km per pixel)"
    )

    district_mask = _rasterize_boundary(boundary_gdf, common_shape, common_transform)
    if district_mask is None and boundary_gdf is not None:
        notes.append("⚠️ Could not rasterise the district boundary — analysis not masked")

    normalized_rasters = {}
    raw_rasters = {}

    for criterion, config in raster_config.items():
        path = config['path']
        if not path or not os.path.exists(path):
            notes.append(f"⚠️ {criterion.capitalize()} raster missing — criterion excluded, weights renormalised")
            continue
        try:
            data, _t, _p = _load_raster_to_grid(
                path, dst_shape=common_shape, dst_transform=common_transform,
                dst_crs="EPSG:4326", band=1, resampling=config['resampling'],
            )
            data, n_filled = _fill_nearest(data, district_mask)
            if n_filled:
                pct = 100.0 * n_filled / max(1, district_mask.sum())
                notes.append(
                    f"ℹ️ {criterion.capitalize()}: {n_filled:,} district pixels ({pct:.1f}%) "
                    "gap-filled from the nearest valid value"
                )
            raw_rasters[criterion] = data
        except Exception as e:
            notes.append(f"⚠️ {criterion.capitalize()} raster error: {e}")

    if 'slope' in raw_rasters:
        normalized_rasters['slope'] = C.score_slope(raw_rasters['slope'])
        notes.append("✅ Slope scored by interpolated ramp (degrees)")

    if 'rainfall' in raw_rasters:
        rain = raw_rasters['rainfall']
        if district_mask is not None:
            rain = np.where(district_mask, rain, np.nan)
        normalized_rasters['rainfall'] = C.score_percentile_benefit(rain)
        notes.append("✅ Rainfall scored by continuous percentile rank within the district")
        if C.RAINFALL_SOURCE_NOTE:
            notes.append(f"⚠️ {C.RAINFALL_SOURCE_NOTE}")

    if 'soil' in raw_rasters:
        normalized_rasters['soil'] = C.score_categorical(
            raw_rasters['soil'], C.SOIL_TEXTURE_SCORES, C.SOIL_DEFAULT_SCORE)
        notes.append("✅ Soil texture scored by explicit class lookup")

    if 'lulc' in raw_rasters:
        normalized_rasters['lulc'] = C.score_categorical(
            raw_rasters['lulc'], C.LULC_SCORES, C.LULC_DEFAULT_SCORE)
        notes.append("✅ LULC scored by explicit IGBP class lookup")

    settlement_distance_km = None
    if 'population' in raw_rasters:
        pop = raw_rasters['population']
        settlement_mask = np.nan_to_num(pop, nan=0.0) >= C.SETTLEMENT_DENSITY_THRESHOLD
        settlement_distance_km = _distance_km(settlement_mask, dy_km, dx_km)
        if settlement_distance_km is None:
            notes.append(
                f"⚠️ No pixel reaches {C.SETTLEMENT_DENSITY_THRESHOLD:.0f} people/km² — "
                "settlement criterion excluded"
            )
        else:
            score = C.score_settlement_distance(settlement_distance_km)
            score[np.isnan(pop)] = np.nan
            normalized_rasters['population'] = score
            share = 100.0 * settlement_mask.sum() / max(1, np.isfinite(pop).sum())
            notes.append(
                f"✅ Settlement proximity scored moderate-optimal "
                f"({C.SETTLEMENT_PEAK_KM[0]:.0f}–{C.SETTLEMENT_PEAK_KM[1]:.0f} km peak; "
                f"{share:.1f}% of pixels classed as settlement)"
            )

    drainage_density = None
    if rivers_gdf is not None:
        try:
            length_grid = _river_length_grid(rivers_gdf, common_shape, common_transform)
            if length_grid is None:
                notes.append("⚠️ Rivers produced no usable geometry — drainage criterion excluded")
            else:
                drainage_density = _drainage_density(
                    length_grid, dy_km, dx_km, C.DRAINAGE_DENSITY_WINDOW_KM)
                normalized_rasters['drainage'] = C.score_drainage_density(drainage_density)
                if district_mask is not None:
                    inside = drainage_density[district_mask]
                    total_km = float(length_grid[district_mask].sum())
                    area_km2 = float(district_mask.sum() * dy_km * dx_km)
                    notes.append(
                        f"✅ Drainage density computed on a {C.DRAINAGE_DENSITY_WINDOW_KM:.1f} km window "
                        f"({total_km:,.0f} km of channel / {area_km2:,.0f} km² = "
                        f"{total_km / area_km2:.3f} km/km² district-wide; "
                        f"local range {inside.min():.2f}–{inside.max():.2f})"
                    )
                else:
                    notes.append("✅ Drainage density computed")
        except Exception as e:
            notes.append(f"⚠️ Drainage density error: {e}")
    else:
        notes.append("⚠️ Rivers data missing — drainage criterion excluded, weights renormalised")

    # Clip every criterion to the district once, here.
    if district_mask is not None:
        for k in normalized_rasters:
            normalized_rasters[k] = np.where(district_mask, normalized_rasters[k], np.nan)

    stack = {
        "status": "ok" if normalized_rasters else "error",
        "notes": notes,
        "normalized_rasters": normalized_rasters,
        "raw_rasters": raw_rasters,
        "settlement_distance_km": settlement_distance_km,
        "drainage_density": drainage_density,
        "district_mask": district_mask,
        "transform": common_transform,
        "shape": common_shape,
        "boundary_gdf": boundary_gdf,
        "rivers_gdf": rivers_gdf,
    }
    if not normalized_rasters:
        stack["notes"].append("⚠️ No criteria available — cannot perform analysis")

    if use_cache:
        _STACK_CACHE[key] = stack
    return stack


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2 — score the stack with a given weight vector
# ─────────────────────────────────────────────────────────────────────────────

def score_stack(stack: dict, weights: dict, consistency_ratio: float | None = None,
                top_n: int = DEFAULT_TOP_N, extract_sites: bool = True,
                aggregator=None, algorithm: str | None = None) -> dict:
    """Combine a criteria stack into a suitability surface using `weights`.

    Cheap: everything expensive already happened in build_criteria_stack().
    `extract_sites=False` skips vectorisation of the high-suitability zone,
    which is what sensitivity analysis wants when it only needs rankings.
    `aggregator` selects the MCDA engine — see algorithms.AGGREGATORS. Defaults
    to weighted linear combination.
    """
    gpd = _import_geopandas()
    normalized_rasters = stack["normalized_rasters"]
    district_mask = stack["district_mask"]
    common_transform = stack["transform"]
    common_shape = stack["shape"]
    raw_rasters = stack["raw_rasters"]

    if not normalized_rasters:
        return {"status": "error", "boundary_gdf": stack["boundary_gdf"],
                "rivers_gdf": stack["rivers_gdf"], "notes": list(stack["notes"])}

    notes = list(stack["notes"])

    used_weight = sum(float(weights.get(k, 0.0)) for k in normalized_rasters)
    if abs(used_weight - 1.0) > 1e-6:
        notes.append(
            f"ℹ️ {len(normalized_rasters)}/6 criteria available "
            f"({used_weight * 100:.1f}% of total AHP weight) — renormalised to 1.0"
        )

    if aggregator is None:
        suitability, _coverage = _weighted_overlay(normalized_rasters, weights)
    else:
        suitability = aggregator(normalized_rasters, weights)
    if district_mask is not None:
        suitability[~district_mask] = np.nan
        dropped = int((district_mask & np.isnan(suitability)).sum())
        if dropped:
            notes.append(
                f"ℹ️ {dropped:,} district pixels ({100 * dropped / district_mask.sum():.1f}%) "
                f"excluded — under {C.MIN_WEIGHT_COVERAGE * 100:.0f}% of AHP weight has data there"
            )

    classified = _classify_suitability(suitability)
    area_stats = _area_statistics(classified, common_transform, common_shape)
    mode = ("fixed thresholds " + str(C.SUITABILITY_THRESHOLDS)
            if C.CLASSIFICATION_MODE != "percentile" else "33rd/67th percentiles")
    notes.append(
        f"📊 District analysed: {area_stats['total_km2']:,.0f} km² ({mode}) — "
        f"High {area_stats['classes']['High']['percent']:.1f}%, "
        f"Medium {area_stats['classes']['Medium']['percent']:.1f}%, "
        f"Low {area_stats['classes']['Low']['percent']:.1f}%"
    )

    result = {
        "status": "ok",
        "weights": weights,
        "consistency_ratio": consistency_ratio,
        "algorithm": algorithm or "AHP + WLC",
        "criteria_used": sorted(normalized_rasters.keys()),
        "criterion_method": {k: C.CRITERION_METHOD.get(k, "") for k in normalized_rasters},
        "suitability_raster": suitability,
        "suitability_transform": common_transform,
        "suitability_shape": common_shape,
        "classified_raster": classified,
        "area_statistics": area_stats,
        "boundary_gdf": stack["boundary_gdf"],
        "rivers_gdf": stack["rivers_gdf"],
        "high_suitability_gdf": None,
        "top_locations_gdf": None,
        "notes": notes,
    }

    tiebreak = _tiebreak_raster(raw_rasters, stack["settlement_distance_km"],
                               stack["drainage_density"], common_shape)
    top_locations = _extract_top_locations(
        suitability, classified, common_transform, top_n=top_n,
        tiles=(5, 5), rank_values=tiebreak)

    details = []
    for loc in top_locations:
        row, col = loc.get('row'), loc.get('col')
        criterion_scores, satisfied, raw_values = {}, [], {}
        if row is not None and col is not None:
            for criterion, raster in normalized_rasters.items():
                val = float(raster[row, col])
                if np.isnan(val):
                    continue
                criterion_scores[criterion] = round(val, 3)
                if val >= C.SATISFIED_THRESHOLD:
                    satisfied.append(criterion)

            if 'slope' in raw_rasters and not np.isnan(raw_rasters['slope'][row, col]):
                raw_values['slope_deg'] = round(float(raw_rasters['slope'][row, col]), 2)
            if 'soil' in raw_rasters and not np.isnan(raw_rasters['soil'][row, col]):
                code = int(round(float(raw_rasters['soil'][row, col])))
                raw_values['soil_class'] = C.SOIL_TEXTURE_LABELS.get(code, f"code {code}")
            if 'lulc' in raw_rasters and not np.isnan(raw_rasters['lulc'][row, col]):
                code = int(round(float(raw_rasters['lulc'][row, col])))
                raw_values['lulc_class'] = C.LULC_LABELS.get(code, f"code {code}")
            if stack["settlement_distance_km"] is not None:
                raw_values['settlement_km'] = round(float(stack["settlement_distance_km"][row, col]), 2)
            if stack["drainage_density"] is not None:
                raw_values['drainage_density'] = round(float(stack["drainage_density"][row, col]), 3)

        details.append({
            **{k: v for k, v in loc.items() if k not in ('row', 'col')},
            'criteria_scores': criterion_scores,
            'criteria_satisfied': satisfied,
            'raw_values': raw_values,
        })

    result["top_locations"] = [{k: v for k, v in loc.items() if k not in ('row', 'col')}
                              for loc in top_locations]
    result["top_locations_details"] = details

    if not extract_sites:
        return result

    try:
        _rio, rio_shapes = _import_rasterio()
        shape_fn = _import_shapely()[0]
        high_mask = (classified == 3).astype(np.uint8)
        high_polys = [shape_fn(geom) for geom, val
                      in rio_shapes(high_mask, mask=(high_mask == 1), transform=common_transform)
                      if val == 1]
        result["high_suitability_gdf"] = (gpd.GeoDataFrame(geometry=high_polys, crs="EPSG:4326")
                                          if high_polys else None)
    except Exception as e:
        notes.append(f"⚠️ High suitability mapping error: {e}")

    try:
        if top_locations:
            Point = _import_shapely()[2]
            result["top_locations_gdf"] = gpd.GeoDataFrame(
                data=[{'rank': loc['rank'], 'score': loc['suitability_score']}
                      for loc in top_locations],
                geometry=[Point(loc['lon'], loc['lat']) for loc in top_locations],
                crs="EPSG:4326",
            )
    except Exception as e:
        notes.append(f"⚠️ Top locations GeoDataFrame error: {e}")

    return result


def run_ahp_analysis(data_dir: str, max_grid_size: int = DEFAULT_MAX_GRID_SIZE,
                     weights: dict | None = None,
                     consistency_ratio: float | None = None,
                     scenario: str | None = None) -> dict:
    """Full pipeline: build the criteria stack, then score it.

    Args:
        data_dir: directory holding the boundary, rivers and criterion rasters.
        max_grid_size: longest side of the common analysis grid, in pixels.
        weights: optional weight dict. Defaults to the baseline AHP matrix.
        consistency_ratio: CR to report alongside supplied weights.
        scenario: name from ahp.SCENARIOS, used when `weights` is not given.
    """
    if weights is None:
        if scenario:
            weights, consistency_ratio = ahp_engine.weights_for_scenario(scenario)
        else:
            weights, consistency_ratio = ahp_engine.calculate_weights()

    stack = build_criteria_stack(data_dir, max_grid_size)
    return score_stack(stack, weights, consistency_ratio)
