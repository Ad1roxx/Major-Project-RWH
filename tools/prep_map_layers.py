"""Prepares the small vector inputs for the QGIS figures (tools/qgis_figures.py).

Runs in the project venv (it needs geopandas and rasterio, which QGIS's Python
lacks) and writes to outputs/figures/qgis/inputs/:

  maharashtra.geojson       Maharashtra outline, GADM 4.1 level 1 (inset of Fig 1)
  maharashtra_districts.geojson  its districts, GADM 4.1 level 2, simplified
  india_soi.geojson         India, official Survey of India outline (DataMeet),
                            simplified for an inset
  river_labels.geojson      the named rivers labelled on Fig 1, one merged line
                            each, from OpenStreetMap (data/raw/osm_rivers/)
  grid_window.geojson       a 16 x 16-cell window of the analysis grid where the
                            boundary crosses it, flagged in or out of district

    python tools/prep_map_layers.py
"""
import os
import re

import geopandas as gpd
import numpy as np
import rasterio
from shapely.geometry import box
from shapely.ops import linemerge, unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs", "figures", "qgis", "inputs")
GADM_ZIP = os.path.join(os.path.expanduser("~"), "Downloads", "gadm41_IND_shp.zip")
# The rivers labelled on Fig 1: the two boundary rivers and the main internal
# ones, checked by the authors against the OSM list on 2026-10-20.
RIVERS = ["Wardha", "Wainganga", "Penganga", "Uma", "Andhari", "Erai"]
WINDOW = 16


def _p(*a):
    return os.path.join(ROOT, *a)


def main():
    os.makedirs(OUT, exist_ok=True)
    boundary = gpd.read_file(_p("data", "boundary.geojson"))

    mh = gpd.read_file(f"zip://{GADM_ZIP}!gadm41_IND_1.shp")
    mh[mh.NAME_1 == "Maharashtra"][["NAME_1", "geometry"]].to_file(
        os.path.join(OUT, "maharashtra.geojson"), driver="GeoJSON")
    dist = gpd.read_file(f"zip://{GADM_ZIP}!gadm41_IND_2.shp")
    dist = dist[dist.NAME_1 == "Maharashtra"][["NAME_2", "geometry"]].copy()
    dist["geometry"] = dist.geometry.simplify(0.003, preserve_topology=True)
    dist.to_file(os.path.join(OUT, "maharashtra_districts.geojson"), driver="GeoJSON")

    india = gpd.read_file(_p("data", "raw", "india_boundary", "india-soi.geojson"))
    india["geometry"] = india.geometry.simplify(0.01, preserve_topology=True)
    india.to_file(os.path.join(OUT, "india_soi.geojson"), driver="GeoJSON")

    osm = gpd.read_file(_p("data", "raw", "osm_rivers", "chandrapur_named_rivers_osm.geojson"))
    osm["river"] = osm["name"].str.replace(r"\s+[Rr]iver$", "", regex=True).str.strip()
    near = boundary.to_crs(32644).buffer(3000).to_crs(4326).union_all()
    rows = []
    for name in RIVERS:
        lines = osm[osm.river == name].geometry.intersection(near)
        merged = linemerge(unary_union(list(lines)))
        if merged.is_empty:
            raise RuntimeError(f"no OSM geometry for {name}")
        # The line only carries the label: keep the longest continuous piece, or
        # QGIS may label a stub (Andhari is three pieces under two OSM spellings).
        if merged.geom_type == "MultiLineString":
            merged = max(merged.geoms, key=lambda g: g.length)
        rows.append({"river": name, "geometry": merged})
    gpd.GeoDataFrame(rows, crs=4326).to_file(os.path.join(OUT, "river_labels.geojson"),
                                            driver="GeoJSON")

    # Grid window centred on the eastern boundary near 20.0°N, where the outline
    # indents and cuts across cells. (The westernmost point lies on the grid's
    # own edge, and a window there would index off the array.)
    with rasterio.open(_p("outputs", "rwh_suitability_classified.tif")) as r:
        cls, t = r.read(1), r.transform
    shape = boundary.geometry.iloc[0]
    target = (79.88, 20.02)
    lon, lat = min((c for part in getattr(shape, "geoms", [shape]) for c in part.exterior.coords),
                   key=lambda c: (c[0] - target[0]) ** 2 + (c[1] - target[1]) ** 2)
    row, col = rasterio.transform.rowcol(t, lon, lat)
    r0, c0 = row - WINDOW // 2, col - WINDOW // 2
    if r0 < 0 or c0 < 0 or r0 + WINDOW > cls.shape[0] or c0 + WINDOW > cls.shape[1]:
        raise RuntimeError("grid window falls off the raster")
    cells = []
    for r in range(r0, r0 + WINDOW):
        for c in range(c0, c0 + WINDOW):
            x0, y0 = t * (c, r)
            x1, y1 = t * (c + 1, r + 1)
            cells.append({"row": r, "col": c, "inside": int(cls[r, c] > 0),
                          "geometry": box(min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))})
    g = gpd.GeoDataFrame(cells, crs=4326)
    g.to_file(os.path.join(OUT, "grid_window.geojson"), driver="GeoJSON")
    _cn_classes()

    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    ew = geod.inv(lon, lat, lon + t.a, lat)[2] / 1000
    ns = geod.inv(lon, lat, lon, lat - t.e)[2] / 1000
    print(f"wrote inputs to {os.path.relpath(OUT, ROOT)}; grid window at row {r0}, col {c0}; "
          f"one cell is {ew:.3f} km E-W x {ns:.3f} km N-S; "
          f"{int(g.inside.sum())} of {len(g)} cells in district")


# Curve Number takes few discrete values (a lookup over soil group x land
# cover), so the hydrology figure shows it as classes. Runoff depth and the
# runoff coefficient are fixed functions of CN for the 100 mm design storm, so
# each class carries its own Q and C instead of separate, identical maps.
CN_CLASSES = [(55, 74), (77, 77), (78, 80), (83, 83), (85, 85), (89, 89), (90, 100)]


def _cn_classes():
    import json
    with rasterio.open(_p("outputs", "curve_number.tif")) as r:
        cn, prof, t = r.read(1).astype(float), r.profile, r.transform
        nd = r.nodata
    with rasterio.open(_p("outputs", "runoff_depth.tif")) as r:
        q = r.read(1).astype(float)
    valid = cn != nd
    # Area-weighted shares: the grid is EPSG:4326, so cell area falls with latitude.
    lat = t.f + (np.arange(cn.shape[0]) + 0.5) * t.e
    w = np.repeat(np.cos(np.radians(lat))[:, None], cn.shape[1], axis=1)
    out = np.zeros(cn.shape, dtype=np.uint8)
    rows = []
    for k, (lo, hi) in enumerate(CN_CLASSES, start=1):
        m = valid & (cn >= lo) & (cn <= hi)
        if not m.any():
            raise RuntimeError(f"no cells in CN class {lo}-{hi}")
        out[m] = k
        rows.append({"code": k, "cn": f"{lo}" if lo == hi else f"{lo}–{hi}",
                     "q_mm": [round(float(q[m].min()), 1), round(float(q[m].max()), 1)],
                     "share_pct": round(float(w[m].sum() / w[valid].sum() * 100), 2)})
    if (valid & (out == 0)).any():
        raise RuntimeError("a Curve Number value falls outside every class")
    prof.update(dtype="uint8", nodata=0, count=1)
    with rasterio.open(os.path.join(OUT, "cn_class.tif"), "w", **prof) as dst:
        dst.write(out, 1)
    with open(os.path.join(OUT, "cn_classes.json"), "w", encoding="utf8") as fh:
        json.dump(rows, fh, ensure_ascii=False, indent=1)


def _fig04_layers():
    """Rasters for the illustrated Figure 4, from the live model (baseline).

    score_<criterion>.tif   each criterion's 0–1 score surface
    class_<n>.tif           classified surface of each of the four methods
    agree4.tif              number of methods classing each cell High (0–4)
    fig04.json              weights, High shares, the all-four-High area and
                            rank 1's per-criterion contributions
    """
    import json
    import sys
    sys.path.insert(0, ROOT)
    from gis_analysis import build_criteria_stack, score_stack
    from ahp import ahp_engine, SCENARIOS
    from algorithms import ALGORITHMS, weights_for_algorithm

    stack = build_criteria_stack(_p("data"))
    t, mask = stack["transform"], stack["district_mask"].astype(bool)
    prof = {"driver": "GTiff", "height": mask.shape[0], "width": mask.shape[1], "count": 1,
            "crs": "EPSG:4326", "transform": t, "compress": "deflate"}
    for crit, arr in stack["normalized_rasters"].items():
        out = np.where(mask, arr, np.nan).astype("float32")
        with rasterio.open(os.path.join(OUT, f"score_{crit}.tif"), "w", dtype="float32",
                           nodata=np.nan, **prof) as dst:
            dst.write(out, 1)
    # Raw inputs as they land on the grid, masked to the district (the figure's
    # "raw sources" row; the source files themselves have ragged extents).
    for crit, arr in stack["raw_rasters"].items():
        out = np.where(mask, arr, np.nan).astype("float32")
        with rasterio.open(os.path.join(OUT, f"raw_{crit}.tif"), "w", dtype="float32",
                           nodata=np.nan, **prof) as dst:
            dst.write(out, 1)

    matrix = ahp_engine.matrix_for_scenario(list(SCENARIOS)[0])
    meta = {"methods": [], "weights": None}
    agree = np.zeros(mask.shape, dtype="uint8")
    lat = t.f + (np.arange(mask.shape[0]) + 0.5) * t.e
    cell_km2 = (abs(t.a) * 111.32 * np.cos(np.radians(lat)) * abs(t.e) * 110.57)[:, None]
    for i, name in enumerate(ALGORITHMS, start=1):
        w, agg, _ = weights_for_algorithm(name, matrix, ahp_engine.criteria)
        res = score_stack(stack, w, aggregator=agg, algorithm=name, extract_sites=(i == 1))
        cls = np.nan_to_num(res["classified_raster"], nan=0).astype("uint8")
        with rasterio.open(os.path.join(OUT, f"class_{i}.tif"), "w", dtype="uint8", nodata=0,
                           **prof) as dst:
            dst.write(cls, 1)
        agree += (cls == 3).astype("uint8")
        hi = res["area_statistics"]["classes"]["High"]
        meta["methods"].append({"code": i, "name": name,
                                "high_pct": hi.get("percent_exact", hi["percent"])})
        if i == 1:
            meta["weights"] = {k: float(v) for k, v in w.items()}
            # Contributions from the unrounded score rasters at the site's cell:
            # criteria_scores are stored to 3 dp, and their weighted sum
            # (0.9563) misses the true score (0.9566) by more than rounding.
            top = res["top_locations_details"][0]
            row, col = rasterio.transform.rowcol(t, top["lon"], top["lat"])
            contrib = {k: float(w[k]) * float(stack["normalized_rasters"][k][row, col])
                       for k in w}
            exact = float(res["suitability_raster"][row, col])
            if abs(sum(contrib.values()) - exact) > 1e-6:
                raise RuntimeError("rank 1 contributions do not sum to its score")
            meta["rank1"] = {"score": exact, "contrib": contrib}
    # The sites every method selects (consensus.py --write), for panel (d).
    import pandas as pd
    cons = pd.read_csv(_p("outputs", "consensus_algorithms.csv"), comment="#")
    cons = cons[cons["unanimous"].astype(str).str.lower().isin(["true", "1"])]
    gpd.GeoDataFrame(cons[["consensus_rank"]],
                     geometry=gpd.points_from_xy(cons.longitude, cons.latitude), crs=4326
                     ).to_file(os.path.join(OUT, "consensus_sites.geojson"), driver="GeoJSON")
    meta["consensus_sites"] = int(len(cons))
    # Fig 12's plotted effects on the High share, read from its own data so the
    # miniature in Fig 4 (e) cannot drift from the full figure.
    fig12 = {}
    in_block = False
    for line in open(_p("paper_pack", "FIGURE_DATA.md"), encoding="utf8"):
        if line.startswith("## "):
            in_block = line.strip() == "## fig12"
        elif in_block:
            m = re.match(r"\| `(high_\w+)` \| (-?[\d.]+) \|", line)
            if m:
                fig12[m.group(1)] = float(m.group(2))
    need = ["high_cutoff_range_pp", "high_rainfall_pp", "high_scenario_range_pp",
            "high_aggregation_pp", "high_weighting_pp"]
    missing = [k for k in need if k not in fig12]
    if missing:
        raise RuntimeError(f"fig12 values not found in FIGURE_DATA.md: {missing}")
    meta["fig12"] = {k: fig12[k] for k in need}
    agree[~mask] = 0
    with rasterio.open(os.path.join(OUT, "agree4.tif"), "w", dtype="uint8", nodata=255,
                       **prof) as dst:
        dst.write(np.where(mask, agree, 255).astype("uint8"), 1)
    meta["all4_high_km2"] = round(float(cell_km2.repeat(mask.shape[1], 1)[agree == 4].sum()), 1)
    with open(os.path.join(OUT, "fig04.json"), "w", encoding="utf8") as fh:
        json.dump(meta, fh, indent=1)
    print("fig04 layers:", [(m["name"], round(m["high_pct"], 2)) for m in meta["methods"]],
          "all-four High", meta["all4_high_km2"], "km2")


if __name__ == "__main__":
    main()
    _fig04_layers()
