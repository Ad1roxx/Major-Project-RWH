"""
derived_maps.py
───────────────
Produces the two derived hydrological surfaces the project methodology calls
for, as GeoTIFFs plus a report-ready figure:

  1. Drainage density        (km/km², moving window)   — also an AHP criterion
  2. SCS Curve Number        (dimensionless, 30–100)
  3. Runoff depth            (mm, for a design storm)
  4. Runoff coefficient      (Q/P, dimensionless)

Run:
    python derived_maps.py
    python derived_maps.py --storm-mm 120
    python derived_maps.py --outdir outputs

────────────────────────────────────────────────────────────────────────────
WHY THE RUNOFF MAP USES A DESIGN STORM, NOT THE ANNUAL RAINFALL TOTAL
────────────────────────────────────────────────────────────────────────────
SCS-CN is an *event* model: P is the depth of one storm. Feeding it an annual
total is a common shortcut in the literature and it is wrong here, measurably
so. With P = 1,493 mm (Chandrapur's mean annual rainfall):

    CN 55 (forest)     → runoff coefficient 0.85
    CN 70 (shrubland)  → 0.92
    CN 78 (cropland)   → 0.94
    CN 85 (built-up)   → 0.96

Every land cover collapses into the same value, so the map carries no spatial
information — the same failure mode as min–max normalisation (see
docs/METHODOLOGY.md §1). At a 100 mm design storm the same four classes spread
across 0.13 – 0.61, which is a usable surface.

The runoff map is therefore produced for a single design storm and labelled as
such. To obtain a defensible *annual* runoff volume, run the model per month on
monthly CHIRPS rasters and sum the twelve results — that needs the monthly
download, which the project does not currently hold.

Runoff is deliberately NOT an AHP criterion: Curve Number is a function of LULC
and soil, and runoff additionally of rainfall — all three are already weighted
criteria, so including runoff would silently double-weight them.
"""

from __future__ import annotations

import argparse
import os

import numpy as np
import rasterio

import criteria as C
import gis_analysis as G

# ─────────────────────────────────────────────────────────────────────────────
# Hydrologic Soil Group from the project's soil texture classes
# ─────────────────────────────────────────────────────────────────────────────
# A = high infiltration / low runoff … D = very low infiltration / high runoff.
# Standard USDA-NRCS texture-to-group assignment, applied to the SoilGrids
# TEXMHT legend documented in criteria.py.
#
# ⚠ CORRECTED 2026-10-02 alongside criteria.SOIL_TEXTURE_SCORES. The previous
# mapping read the class codes against the wrong legend and assigned code 1 to
# group A (highest infiltration) when it is Clay, which is group D — the
# opposite end of the scale. Curve Number and both runoff surfaces are affected.
# See docs/SOIL_LEGEND_CORRECTION.md.
HSG_FROM_SOIL = {
    1: "D",    # Clay
    2: "D",    # Silty Clay
    3: "D",    # Sandy Clay
    4: "D",    # Clay Loam
    5: "D",    # Silty Clay Loam
    6: "C",    # Sandy Clay Loam
    7: "B",    # Loam
    8: "B",    # Silt Loam
    9: "A",    # Sandy Loam
    10: "B",   # Silt
    11: "A",   # Loamy Sand
    12: "A",   # Sand
}
DEFAULT_HSG = "C"

# ─────────────────────────────────────────────────────────────────────────────
# Curve Numbers by IGBP land cover × Hydrologic Soil Group
# ─────────────────────────────────────────────────────────────────────────────
# Antecedent Moisture Condition II (average), good hydrologic condition,
# after USDA-NRCS TR-55 land-use analogues.
CURVE_NUMBERS = {
    1:  (30, 55, 70, 77),   # Evergreen Needleleaf Forest — woods, good
    2:  (30, 55, 70, 77),   # Evergreen Broadleaf Forest
    3:  (30, 55, 70, 77),   # Deciduous Needleleaf Forest
    4:  (30, 55, 70, 77),   # Deciduous Broadleaf Forest
    5:  (30, 55, 70, 77),   # Mixed Forest
    6:  (35, 56, 70, 77),   # Closed Shrubland — brush, good
    7:  (35, 56, 70, 77),   # Open Shrubland
    8:  (45, 66, 77, 83),   # Woody Savanna — brush/grass mix
    9:  (45, 66, 77, 83),   # Savanna
    10: (39, 61, 74, 80),   # Grassland — pasture, good
    11: (85, 89, 92, 94),   # Permanent Wetland — near-saturated
    12: (67, 78, 85, 89),   # Cropland — row crops, straight row, good
    13: (77, 85, 90, 92),   # Urban and Built-up — residential
    14: (55, 70, 80, 85),   # Cropland / Natural Vegetation Mosaic
    15: (98, 98, 98, 98),   # Permanent Snow and Ice
    16: (77, 86, 91, 94),   # Barren
    17: (100, 100, 100, 100),  # Water Bodies
}
HSG_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}
DEFAULT_CN = 70

DEFAULT_STORM_MM = 100.0  # ≈1-day design event for a monsoon district


def curve_number_grid(lulc: np.ndarray, soil: np.ndarray) -> np.ndarray:
    """Curve Number from land cover × hydrologic soil group. NaN in, NaN out."""
    out = np.full(lulc.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(lulc)
    if not valid.any():
        return out

    lulc_codes = np.rint(np.nan_to_num(lulc, nan=-1)).astype(int)
    soil_codes = np.rint(np.nan_to_num(soil, nan=-1)).astype(int)

    hsg_idx = np.full(lulc.shape, HSG_INDEX[DEFAULT_HSG], dtype=int)
    for code, group in HSG_FROM_SOIL.items():
        hsg_idx[soil_codes == code] = HSG_INDEX[group]

    cn = np.full(lulc.shape, float(DEFAULT_CN), dtype=np.float32)
    for code, values in CURVE_NUMBERS.items():
        sel = lulc_codes == code
        if not sel.any():
            continue
        for group, idx in HSG_INDEX.items():
            cn[sel & (hsg_idx == idx)] = values[idx]

    out[valid] = cn[valid]
    return out


def scs_runoff(rain_mm: np.ndarray | float, cn: np.ndarray) -> np.ndarray:
    """SCS-CN runoff depth Q (mm) for storm depth P.

        S  = 25400 / CN - 254          potential maximum retention (mm)
        Ia = 0.2 S                     initial abstraction
        Q  = (P - Ia)² / (P + 0.8 S)   for P > Ia, else 0
    """
    with np.errstate(invalid="ignore", divide="ignore"):
        s = 25400.0 / cn - 254.0
        ia = 0.2 * s
        p = np.asarray(rain_mm, dtype=np.float64)
        q = np.where(p > ia, (p - ia) ** 2 / (p + 0.8 * s), 0.0)
    q = np.asarray(q, dtype=np.float32)
    q[np.isnan(cn)] = np.nan
    return q


def write_tif(path, array, transform, crs, nodata=-9999.0, tags=None):
    out = np.asarray(array, dtype="float32").copy()
    out[np.isnan(out)] = nodata
    profile = {
        "driver": "GTiff", "dtype": "float32", "count": 1,
        "height": out.shape[0], "width": out.shape[1],
        "crs": crs, "transform": transform,
        "nodata": nodata, "compress": "deflate",
    }
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(out, 1)
        if tags:
            dst.update_tags(**{k: str(v) for k, v in tags.items()})


def summarise(name, arr, mask, unit):
    v = arr[mask & ~np.isnan(arr)]
    print(f"  {name:22s} mean {v.mean():8.3f}  range {v.min():7.3f} – {v.max():7.3f}  {unit}")
    return v


def main():
    ap = argparse.ArgumentParser(description="Build derived hydrological maps.")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--outdir", default="outputs")
    ap.add_argument("--storm-mm", type=float, default=DEFAULT_STORM_MM,
                    help="Design storm depth in mm for the runoff map (default 100)")
    ap.add_argument("--grid", type=int, default=G.DEFAULT_MAX_GRID_SIZE)
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    import geopandas as gpd

    boundary = gpd.read_file(os.path.join(args.data_dir, "boundary.geojson"))
    shape, transform = G._make_common_grid(boundary.total_bounds, args.grid)
    mask = G._rasterize_boundary(boundary, shape, transform)
    dy_km, dx_km = G._pixel_size_km(transform, shape)
    crs = "EPSG:4326"

    print(f"Analysis grid {shape[0]}×{shape[1]} px (≈{dx_km:.2f} × {dy_km:.2f} km)\n")

    # ── 1. Drainage density ─────────────────────────────────────────────────
    rivers_path = os.path.join(args.data_dir, "rivers.geojson")
    rivers = gpd.read_file(rivers_path)
    length_grid = G._river_length_grid(rivers, shape, transform)
    density = G._drainage_density(length_grid, dy_km, dx_km, C.DRAINAGE_DENSITY_WINDOW_KM)
    density_m = np.where(mask, density, np.nan)

    # ── 2. Curve Number ─────────────────────────────────────────────────────
    lulc, _, _ = G._load_raster_to_grid(os.path.join(args.data_dir, "lulc.tif"),
                                        shape, transform, resampling="nearest")
    soil, _, _ = G._load_raster_to_grid(os.path.join(args.data_dir, "soil_texture.tif"),
                                        shape, transform, resampling="nearest")
    lulc, _ = G._fill_nearest(lulc, mask)
    soil, _ = G._fill_nearest(soil, mask)
    cn = np.where(mask, curve_number_grid(lulc, soil), np.nan)

    # ── 3/4. Runoff depth and coefficient for the design storm ──────────────
    runoff = scs_runoff(args.storm_mm, cn)
    runoff = np.where(mask, runoff, np.nan)
    coefficient = np.where(mask, runoff / args.storm_mm, np.nan)

    print(f"District summary (design storm P = {args.storm_mm:.0f} mm):")
    summarise("drainage density", density_m, mask, "km/km²")
    summarise("curve number", cn, mask, "")
    summarise("runoff depth", runoff, mask, "mm")
    summarise("runoff coefficient", coefficient, mask, "")

    common = {"GENERATED_BY": "derived_maps.py", "GRID": f"{shape[0]}x{shape[1]}"}
    write_tif(f"{args.outdir}/drainage_density.tif", density_m, transform, crs,
              tags={**common, "UNITS": "km/km2",
                    "WINDOW_KM": C.DRAINAGE_DENSITY_WINDOW_KM,
                    "SOURCE": "HydroRIVERS v1.0"})
    write_tif(f"{args.outdir}/curve_number.tif", cn, transform, crs,
              tags={**common, "UNITS": "dimensionless",
                    "BASIS": "IGBP LULC x hydrologic soil group, AMC II"})
    write_tif(f"{args.outdir}/runoff_depth.tif", runoff, transform, crs,
              tags={**common, "UNITS": "mm", "STORM_MM": args.storm_mm,
                    "MODEL": "SCS-CN, event based"})
    write_tif(f"{args.outdir}/runoff_coefficient.tif", coefficient, transform, crs,
              tags={**common, "UNITS": "dimensionless", "STORM_MM": args.storm_mm})

    # ── Figure ──────────────────────────────────────────────────────────────
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    extent = (transform.c, transform.c + shape[1] * transform.a,
              transform.f + shape[0] * transform.e, transform.f)

    panels = [
        (density_m, "Drainage Density", "km/km²", "YlGnBu"),
        (cn, "SCS Curve Number", "CN (AMC II)", "YlOrRd"),
        (runoff, f"Runoff Depth (P = {args.storm_mm:.0f} mm storm)", "mm", "Blues"),
        (coefficient, "Runoff Coefficient", "Q / P", "PuBuGn"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(13, 12))
    for ax, (arr, title, label, cmap) in zip(axes.ravel(), panels):
        im = ax.imshow(arr, extent=extent, cmap=cmap, origin="upper")
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.8)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Longitude"); ax.set_ylabel("Latitude")
        fig.colorbar(im, ax=ax, shrink=0.8, label=label)

    fig.suptitle("Chandrapur District — Derived Hydrological Surfaces",
                 fontsize=15, fontweight="bold")
    fig.text(0.5, 0.005,
             "SCS-CN is an event model: runoff is shown for a single design storm, "
             "not an annual total. See derived_maps.py for why.",
             ha="center", fontsize=9, style="italic", color="#555555")
    fig.tight_layout(rect=(0, 0.02, 1, 0.97))
    fig_path = f"{args.outdir}/derived_hydrology.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)

    print(f"\nWrote 4 GeoTIFFs and {fig_path} to {args.outdir}/")


if __name__ == "__main__":
    main()
