"""
tools/inspect.py
────────────────
Profile a data file without dumping it.

    python tools/inspect.py <path> [--rows N] [--cols COL[,COL...]]

Supports vector (.geojson/.shp/.gpkg), raster (.tif/.tiff) and tabular
(.csv/.parquet). Raster statistics come from a decimated read, never a full
load, so a 7200x2400 global CHIRPS raster profiles as fast as a small one.

Output is kept to roughly 40 lines. Use --rows for targeted record debugging
and --cols to restrict to named columns.
"""

from __future__ import annotations

import os
import sys

# This file is named inspect.py, which collides with the standard library's
# `inspect` module. Running it as a script puts tools/ at the front of
# sys.path, so numpy's internal `import inspect` would resolve to this file and
# fail with "module 'inspect' has no attribute 'cleandoc'". Dropping this
# directory from sys.path before any third-party import resolves it. All heavy
# imports below are deliberately kept inside functions for the same reason.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
               if os.path.abspath(p or os.getcwd()) != _HERE]

import argparse  # noqa: E402

MAX_LIST = 25          # max columns / bands / categories listed before truncating
DECIMATE_TO = 512      # longest raster side read for statistics


def _hr(title: str) -> None:
    print(f"── {title} " + "─" * max(0, 60 - len(title)))


def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024.0
    return f"{n:.1f} GB"


def _column_table(df, cols=None) -> None:
    """Print columns with dtype and null count, truncating long lists."""
    import pandas as pd

    names = list(cols) if cols else [c for c in df.columns if c != "geometry"]
    shown = names[:MAX_LIST]
    nulls = df[shown].isna().sum() if shown else pd.Series(dtype=int)

    print(f"{'column':<22} {'dtype':<12} {'nulls':>8}")
    for c in shown:
        print(f"{str(c):<22} {str(df[c].dtype):<12} {int(nulls[c]):>8}")
    if len(names) > MAX_LIST:
        print(f"... {len(names) - MAX_LIST} more columns")


def _describe_numeric(df, cols=None) -> None:
    from pandas.api.types import is_numeric_dtype

    names = list(cols) if cols else list(df.columns)
    num = [c for c in names if c != "geometry" and is_numeric_dtype(df[c])]
    if not num:
        return
    _hr("numeric summary")
    desc = df[num[:MAX_LIST]].describe().T[["count", "mean", "std", "min", "50%", "max"]]
    print(desc.to_string(float_format=lambda v: f"{v:,.3f}"))


def inspect_vector(path: str, rows: int, cols) -> None:
    import geopandas as gpd

    gdf = gpd.read_file(path)

    _hr("vector")
    print(f"path        {path}  ({_fmt_bytes(os.path.getsize(path))})")
    print(f"features    {len(gdf):,}")
    print(f"CRS         {gdf.crs}")
    geom_types = gdf.geom_type.value_counts()
    print(f"geometry    {', '.join(f'{k} x{v}' for k, v in geom_types.items())}")
    if len(gdf):
        minx, miny, maxx, maxy = gdf.total_bounds
        print(f"bounds      {minx:.4f}, {miny:.4f}  →  {maxx:.4f}, {maxy:.4f}")

    _hr("columns")
    _column_table(gdf, cols)
    _describe_numeric(gdf, cols)

    if rows:
        _hr(f"first {rows} rows")
        sub = gdf[list(cols)] if cols else gdf.drop(columns="geometry", errors="ignore")
        print(sub.head(rows).to_string())


def inspect_raster(path: str, rows: int, cols) -> None:
    import numpy as np
    import rasterio

    with rasterio.open(path) as src:
        _hr("raster")
        print(f"path        {path}  ({_fmt_bytes(os.path.getsize(path))})")
        print(f"CRS         {src.crs}")
        print(f"shape       {src.height} x {src.width}  ({src.count} band(s))")
        print(f"dtype       {src.dtypes[0]}          nodata: {src.nodata}")
        res_x, res_y = src.res
        print(f"resolution  {res_x:.6g} x {res_y:.6g} (CRS units)")
        b = src.bounds
        print(f"bounds      {b.left:.4f}, {b.bottom:.4f}  →  {b.right:.4f}, {b.top:.4f}")
        print(f"transform   {src.transform.a:.6g}, {src.transform.e:.6g} "
              f"(origin {src.transform.c:.4f}, {src.transform.f:.4f})")

        scale = min(1.0, DECIMATE_TO / max(src.height, src.width))
        out_h = max(1, int(src.height * scale))
        out_w = max(1, int(src.width * scale))

        _hr(f"band statistics (decimated read {out_h}x{out_w})")
        print(f"{'band':<6}{'min':>14}{'max':>14}{'mean':>14}{'std':>14}{'valid%':>9}")
        for i in range(1, min(src.count, MAX_LIST) + 1):
            arr = src.read(i, out_shape=(out_h, out_w), masked=True).astype("float64")
            v = np.asarray(arr.compressed() if hasattr(arr, "compressed") else arr.ravel())
            v = v[np.isfinite(v)]
            if v.size == 0:
                print(f"{i:<6}{'(no valid data)':>65}")
                continue
            pct = 100.0 * v.size / (out_h * out_w)
            print(f"{i:<6}{v.min():>14,.3f}{v.max():>14,.3f}"
                  f"{v.mean():>14,.3f}{v.std():>14,.3f}{pct:>8.1f}%")

            if v.size and np.allclose(v, np.round(v)) and len(np.unique(v)) <= MAX_LIST:
                uniq = np.unique(v).astype(int).tolist()
                print(f"      categorical — {len(uniq)} classes: {uniq}")

            # Undeclared fill values silently poison any statistic computed from
            # the band. CHIRPS ships -9999 without declaring it as nodata.
            if src.nodata is None:
                sentinel = v <= -9990
                if sentinel.any():
                    real = v[~sentinel]
                    share = 100.0 * sentinel.sum() / v.size
                    print(f"      !! nodata undeclared; {share:.1f}% of pixels <= -9990 "
                          f"look like a fill value")
                    if real.size:
                        print(f"      excluding those: min {real.min():,.3f}  "
                              f"max {real.max():,.3f}  mean {real.mean():,.3f}")

        # TIFFTAG_* are writer boilerplate; only show provenance tags we set.
        tags = {k: val for k, val in src.tags().items()
                if k.isupper() and k != "AREA_OR_POINT" and not k.startswith("TIFFTAG_")}
        if tags:
            _hr("metadata tags")
            for k, val in list(tags.items())[:8]:
                print(f"{k:<20} {val}")

        if rows:
            _hr(f"centre {rows}x{rows} window, band 1")
            r0 = max(0, src.height // 2 - rows // 2)
            c0 = max(0, src.width // 2 - rows // 2)
            win = rasterio.windows.Window(c0, r0, min(rows, src.width), min(rows, src.height))
            print(np.array2string(src.read(1, window=win), precision=2, suppress_small=True))


def inspect_tabular(path: str, rows: int, cols) -> None:
    import pandas as pd

    df = pd.read_parquet(path) if path.lower().endswith(".parquet") else pd.read_csv(path)
    if cols:
        missing = [c for c in cols if c not in df.columns]
        if missing:
            sys.exit(f"columns not found: {', '.join(missing)}")
        df = df[list(cols)]

    _hr("tabular")
    print(f"path        {path}  ({_fmt_bytes(os.path.getsize(path))})")
    print(f"shape       {df.shape[0]:,} rows x {df.shape[1]} columns")

    _hr("columns")
    _column_table(df)
    _describe_numeric(df)

    low_card = [c for c in df.columns
                if df[c].nunique(dropna=True) <= 12 and df[c].nunique(dropna=True) > 0]
    if low_card:
        _hr("low-cardinality columns")
        for c in low_card[:5]:
            counts = df[c].value_counts(dropna=False).head(6)
            pairs = ", ".join(f"{k}={v}" for k, v in counts.items())
            print(f"{str(c):<22} {pairs}")

    if rows:
        _hr(f"first {rows} rows")
        print(df.head(rows).to_string())


DISPATCH = {
    ".geojson": inspect_vector, ".shp": inspect_vector, ".gpkg": inspect_vector,
    ".json": inspect_vector,
    ".tif": inspect_raster, ".tiff": inspect_raster,
    ".csv": inspect_tabular, ".parquet": inspect_tabular,
}


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Profile a data file without dumping it.")
    ap.add_argument("path")
    ap.add_argument("--rows", type=int, default=0,
                    help="print N actual rows (raster: centre NxN window)")
    ap.add_argument("--cols", default=None,
                    help="comma-separated column subset")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.exit(f"not found: {args.path}")

    ext = os.path.splitext(args.path)[1].lower()
    handler = DISPATCH.get(ext)
    if handler is None:
        sys.exit(f"unsupported extension {ext!r}. "
                 f"Supported: {', '.join(sorted(DISPATCH))}")

    cols = [c.strip() for c in args.cols.split(",")] if args.cols else None
    handler(args.path, args.rows, cols)


if __name__ == "__main__":
    main()
