"""
build_rainfall.py
─────────────────
Build the mean annual rainfall surface used by the suitability analysis.

Reads a set of CHIRPS rasters covering the study area, averages them across
years, and writes a small district-extent GeoTIFF to data/rainfall.tif.

Handles both shapes of CHIRPS download:

  • annual files   chirps-v3.0.2014.tif        → averaged directly
  • monthly files  chirps-v3.0.2014.01.tif …   → summed within each year to an
                                                 annual total, then averaged

Only the window covering the district is read from each file, so the global
0.05° rasters (7200 × 2400 px each) never need to be loaded or clipped by hand.

Usage
    python build_rainfall.py
    python build_rainfall.py --source-dir data --pattern "chirps-v3.0.*.tif"
    python build_rainfall.py --years 2015 2024

Why this exists
    The rainfall layer carries the largest AHP weight (0.428), so how it was
    produced has to be reproducible and stated in the report. Building it here
    rather than by hand in QGIS means the provenance is recorded in code and in
    the output file's metadata tags.
"""

from __future__ import annotations

import argparse
import glob
import os
import re
from collections import defaultdict
from datetime import date

import numpy as np
import rasterio
from rasterio.windows import from_bounds, transform as window_transform

# CHIRPS uses -9999 as its fill value but does NOT declare it as nodata in the
# GeoTIFF header, so rasterio will not mask it automatically. Anything at or
# below this cutoff is treated as no-data.
NODATA_CUTOFF = -100.0
OUT_NODATA = -9999.0

# Extra margin (degrees) read around the district so the analysis grid has real
# values right to the boundary instead of relying on gap filling.
BUFFER_DEG = 0.20

# Long-term mean annual rainfall for Chandrapur, used only as a sanity check.
EXPECTED_MEAN_MM = 1245.0
SANITY_TOLERANCE = 0.20  # ±20%

YEAR_MONTH_RE = re.compile(r"\.(\d{4})\.(\d{2})\.tif$", re.IGNORECASE)
YEAR_RE = re.compile(r"\.(\d{4})\.tif$", re.IGNORECASE)


def discover(source_dir: str, pattern: str, year_range=None):
    """Group matching rasters by year. Returns {year: {month|None: path}}."""
    found = defaultdict(dict)
    for path in sorted(glob.glob(os.path.join(source_dir, pattern))):
        name = os.path.basename(path)
        m = YEAR_MONTH_RE.search(name)
        if m:
            year, month = int(m.group(1)), int(m.group(2))
        else:
            m = YEAR_RE.search(name)
            if not m:
                continue
            year, month = int(m.group(1)), None
        if year_range and not (year_range[0] <= year <= year_range[1]):
            continue
        found[year][month] = path
    return dict(sorted(found.items()))


def read_window(path: str, bounds) -> tuple[np.ndarray, object, object]:
    """Read only the district window from a raster; return (data, transform, crs)."""
    minx, miny, maxx, maxy = bounds
    with rasterio.open(path) as src:
        win = from_bounds(minx, miny, maxx, maxy, src.transform)
        win = win.intersection(from_bounds(*src.bounds, src.transform))
        data = src.read(1, window=win).astype("float64")
        tr = window_transform(win, src.transform)
        crs = src.crs
        declared = src.nodata

    data[data <= NODATA_CUTOFF] = np.nan
    if declared is not None:
        data[data == declared] = np.nan
    return data, tr, crs


def district_mask(boundary_path: str, shape, transform):
    """Boolean mask, True inside the district polygon."""
    import geopandas as gpd
    from rasterio.features import rasterize

    gdf = gpd.read_file(boundary_path)
    geoms = [(g, 1) for g in gdf.geometry if g is not None and not g.is_empty]
    mask = rasterize(geoms, out_shape=shape, transform=transform,
                     fill=0, dtype="uint8", all_touched=True)
    return mask.astype(bool), gdf


def main():
    ap = argparse.ArgumentParser(description="Build the mean annual rainfall surface.")
    ap.add_argument("--source-dir", default="data")
    ap.add_argument("--pattern", default="chirps*.tif")
    ap.add_argument("--boundary", default="data/boundary.geojson")
    ap.add_argument("--out", default="data/rainfall.tif")
    ap.add_argument("--years", nargs=2, type=int, metavar=("START", "END"))
    args = ap.parse_args()

    if not os.path.exists(args.boundary):
        raise SystemExit(f"Boundary not found: {args.boundary}")

    import geopandas as gpd
    bnd = gpd.read_file(args.boundary)
    minx, miny, maxx, maxy = bnd.total_bounds
    bounds = (minx - BUFFER_DEG, miny - BUFFER_DEG,
              maxx + BUFFER_DEG, maxy + BUFFER_DEG)

    groups = discover(args.source_dir, args.pattern,
                      tuple(args.years) if args.years else None)
    if not groups:
        raise SystemExit(
            f"No rasters matched {args.pattern!r} in {args.source_dir!r}.\n"
            "Expected names like chirps-v3.0.2014.tif or chirps-v3.0.2014.01.tif"
        )

    print(f"Found {len(groups)} year(s): {min(groups)}–{max(groups)}")
    print(f"Reading window {[round(b, 3) for b in bounds]} (district + {BUFFER_DEG}° margin)\n")

    annual_totals, used_years, ref_transform, ref_crs = [], [], None, None

    for year, months in groups.items():
        if list(months.keys()) == [None]:
            total, tr, crs = read_window(months[None], bounds)
            label = "annual file"
        else:
            monthly = [m for m in sorted(months) if m is not None]
            if len(monthly) != 12:
                print(f"  ! {year}: only {len(monthly)}/12 monthly files — skipped")
                continue
            stack, tr, crs = [], None, None
            for m in monthly:
                data, tr, crs = read_window(months[m], bounds)
                stack.append(data)
            total = np.nansum(np.stack(stack), axis=0)
            total[np.all(np.isnan(np.stack(stack)), axis=0)] = np.nan
            label = "12 monthly files"

        if ref_transform is None:
            ref_transform, ref_crs = tr, crs
        elif total.shape != annual_totals[0].shape:
            print(f"  ! {year}: window shape {total.shape} differs — skipped")
            continue

        annual_totals.append(total)
        used_years.append(year)
        print(f"  {year}  ({label:16s})  window mean {np.nanmean(total):7.1f} mm")

    if not annual_totals:
        raise SystemExit("No usable years — nothing written.")

    stack = np.stack(annual_totals)
    mean_annual = np.nanmean(stack, axis=0)

    # ── Sanity check against the long-term normal, inside the district only ──
    mask, _ = district_mask(args.boundary, mean_annual.shape, ref_transform)
    inside = mean_annual[mask & ~np.isnan(mean_annual)]
    district_mean = float(np.nanmean(inside))

    print(f"\nMean annual rainfall over {len(used_years)} years "
          f"({min(used_years)}–{max(used_years)})")
    print(f"  district mean : {district_mean:,.1f} mm")
    print(f"  district range: {np.nanmin(inside):,.1f} – {np.nanmax(inside):,.1f} mm")

    per_year = [float(np.nanmean(t[mask & ~np.isnan(t)])) for t in annual_totals]
    print(f"  interannual   : {min(per_year):,.0f} – {max(per_year):,.0f} mm "
          f"(sd {np.std(per_year):,.0f} mm)")

    deviation = abs(district_mean - EXPECTED_MEAN_MM) / EXPECTED_MEAN_MM
    if deviation <= SANITY_TOLERANCE:
        print(f"  ✅ within {deviation * 100:.1f}% of the {EXPECTED_MEAN_MM:,.0f} mm "
              "long-term normal — units are mm/year as expected")
    else:
        print(f"  ⚠️  {deviation * 100:.1f}% away from the {EXPECTED_MEAN_MM:,.0f} mm "
              "normal — CHECK THE UNITS before using this layer")

    # ── Write ────────────────────────────────────────────────────────────────
    out = mean_annual.astype("float32")
    out[np.isnan(out)] = OUT_NODATA

    if os.path.exists(args.out):
        backup = args.out.replace(".tif", "_previous.tif")
        os.replace(args.out, backup)
        print(f"\nExisting {args.out} moved to {backup}")

    profile = {
        "driver": "GTiff", "dtype": "float32", "count": 1,
        "height": out.shape[0], "width": out.shape[1],
        "crs": ref_crs, "transform": ref_transform,
        "nodata": OUT_NODATA, "compress": "deflate",
    }
    with rasterio.open(args.out, "w", **profile) as dst:
        dst.write(out, 1)
        dst.update_tags(
            SOURCE="CHIRPS annual precipitation",
            YEARS=f"{min(used_years)}-{max(used_years)}",
            N_YEARS=str(len(used_years)),
            AGGREGATION="mean of annual totals",
            UNITS="mm/year",
            DISTRICT_MEAN_MM=f"{district_mean:.1f}",
            GENERATED_BY="build_rainfall.py",
            GENERATED_ON=date.today().isoformat(),
        )

    size_kb = os.path.getsize(args.out) / 1024
    print(f"\nWrote {args.out} — {out.shape[1]}×{out.shape[0]} px, {size_kb:,.0f} KB")
    print("Next: set RAINFALL_SOURCE_NOTE = None in criteria.py, then rerun the app.")


if __name__ == "__main__":
    main()
