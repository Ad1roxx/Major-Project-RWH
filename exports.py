"""
exports.py
──────────
Serialise an analysis result to the formats a planner or report actually needs.

Every function returns `bytes`, so the same code backs Streamlit download
buttons and a command-line export. Nothing here touches the filesystem except
`write_all()`.

    ranked sites   → CSV, GeoJSON
    suitability    → GeoTIFF (float32, -9999 nodata, provenance in tags)
    map            → PNG (static, for the report)

Provenance is written into every artefact: the weights, consistency ratio,
classification thresholds and generation date. A CSV without its weights is not
reproducible.
"""

from __future__ import annotations

import io
import json
import os
from datetime import date

import numpy as np

import criteria as C

CRITERIA_ORDER = ["rainfall", "slope", "soil", "drainage", "lulc", "population"]


def _site_records(result: dict) -> list[dict]:
    """Flatten ranked sites into one row per site, criteria in AHP order."""
    weights = result.get("weights", {}) or {}
    order = sorted(weights, key=lambda k: -float(weights.get(k, 0.0))) or CRITERIA_ORDER

    rows = []
    for site in result.get("top_locations_details", []):
        scores = site.get("criteria_scores", {}) or {}
        raw = site.get("raw_values", {}) or {}
        row = {
            "rank": site.get("rank"),
            "longitude": round(float(site.get("lon", 0.0)), 6),
            "latitude": round(float(site.get("lat", 0.0)), 6),
            "suitability_score": site.get("suitability_score"),
        }
        for c in order:
            if c in scores:
                row[f"score_{c}"] = scores[c]
                row[f"contrib_{c}"] = round(float(weights.get(c, 0.0)) * float(scores[c]), 4)
        row.update({
            "slope_deg": raw.get("slope_deg"),
            "soil_class": raw.get("soil_class"),
            "lulc_class": raw.get("lulc_class"),
            "drainage_density_km_per_km2": raw.get("drainage_density"),
            "settlement_distance_km": raw.get("settlement_km"),
            "criteria_satisfied": "; ".join(site.get("criteria_satisfied", [])),
        })
        rows.append(row)
    return rows


def _provenance(result: dict) -> dict:
    weights = result.get("weights", {}) or {}
    cr = result.get("consistency_ratio")
    return {
        "generated_on": date.today().isoformat(),
        "generated_by": "RWH SiteFinder",
        "consistency_ratio": f"{cr:.4f}" if cr is not None else "n/a",
        "classification": f"High>={C.SUITABILITY_THRESHOLDS[1]}, "
                          f"Medium {C.SUITABILITY_THRESHOLDS[0]}-{C.SUITABILITY_THRESHOLDS[1]}, "
                          f"Low<{C.SUITABILITY_THRESHOLDS[0]}",
        "weights": ", ".join(f"{k}={v:.3f}" for k, v in
                             sorted(weights.items(), key=lambda kv: -kv[1])),
    }


def sites_csv(result: dict) -> bytes:
    """Ranked sites as CSV, with a provenance header block."""
    import pandas as pd

    rows = _site_records(result)
    if not rows:
        return b"no sites\n"

    header = "".join(f"# {k}: {v}\n" for k, v in _provenance(result).items())
    body = pd.DataFrame(rows).to_csv(index=False)
    return (header + body).encode("utf-8")


def sites_geojson(result: dict) -> bytes:
    """Ranked sites as GeoJSON points (EPSG:4326)."""
    rows = _site_records(result)
    features = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
        "properties": {k: v for k, v in r.items() if k not in ("longitude", "latitude")},
    } for r in rows]

    doc = {
        "type": "FeatureCollection",
        "name": "rwh_candidate_sites",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "metadata": _provenance(result),
        "features": features,
    }
    return json.dumps(doc, indent=1).encode("utf-8")


def suitability_geotiff(result: dict) -> bytes:
    """Continuous suitability surface as a GeoTIFF, provenance in tags."""
    import rasterio
    from rasterio.io import MemoryFile

    arr = result.get("suitability_raster")
    if arr is None:
        return b""

    out = np.asarray(arr, dtype="float32").copy()
    out[np.isnan(out)] = -9999.0

    profile = {
        "driver": "GTiff", "dtype": "float32", "count": 1,
        "height": out.shape[0], "width": out.shape[1],
        "crs": "EPSG:4326", "transform": result["suitability_transform"],
        "nodata": -9999.0, "compress": "deflate",
    }
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(out, 1)
            dst.update_tags(UNITS="suitability 0-1",
                            **{k.upper(): str(v) for k, v in _provenance(result).items()})
        return mem.read()


def classified_geotiff(result: dict) -> bytes:
    """Low/Medium/High classification as a GeoTIFF (1/2/3, 0 = outside)."""
    import rasterio
    from rasterio.io import MemoryFile

    arr = result.get("classified_raster")
    if arr is None:
        return b""

    out = np.nan_to_num(np.asarray(arr, dtype="float32"), nan=0.0).astype("uint8")
    profile = {
        "driver": "GTiff", "dtype": "uint8", "count": 1,
        "height": out.shape[0], "width": out.shape[1],
        "crs": "EPSG:4326", "transform": result["suitability_transform"],
        "nodata": 0, "compress": "deflate",
    }
    with MemoryFile() as mem:
        with mem.open(**profile) as dst:
            dst.write(out, 1)
            dst.update_tags(CLASSES="1=Low, 2=Medium, 3=High, 0=outside district",
                            **{k.upper(): str(v) for k, v in _provenance(result).items()})
        return mem.read()


def map_png(result: dict, dpi: int = 150) -> bytes:
    """Static suitability map with boundary, rivers and ranked sites."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm

    classified = result.get("classified_raster")
    transform = result.get("suitability_transform")
    if classified is None or transform is None:
        return b""

    h, w = classified.shape
    extent = (transform.c, transform.c + w * transform.a,
              transform.f + h * transform.e, transform.f)

    cmap = ListedColormap(["#d73027", "#fee08b", "#1a9850"])
    norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

    fig, ax = plt.subplots(figsize=(9, 9))
    ax.imshow(classified, extent=extent, cmap=cmap, norm=norm, origin="upper")

    rivers = result.get("rivers_gdf")
    if rivers is not None and len(rivers):
        rivers.plot(ax=ax, color="#2b6cb0", linewidth=0.6, alpha=0.8)
    boundary = result.get("boundary_gdf")
    if boundary is not None and len(boundary):
        boundary.boundary.plot(ax=ax, color="black", linewidth=1.0)

    for site in result.get("top_locations_details", []):
        ax.plot(site["lon"], site["lat"], marker="o", markersize=5,
                markerfacecolor="white", markeredgecolor="black", markeredgewidth=0.8)
        ax.annotate(str(site["rank"]), (site["lon"], site["lat"]),
                    fontsize=6, xytext=(3, 3), textcoords="offset points")

    stats = result.get("area_statistics", {}).get("classes", {})
    subtitle = " · ".join(
        f"{k} {stats.get(k, {}).get('percent', 0):.1f}%" for k in ("High", "Medium", "Low"))
    cr = result.get("consistency_ratio")
    ax.set_title("RWH Suitability — Chandrapur District\n"
                 f"{subtitle}   (AHP CR {cr:.4f})" if cr is not None else subtitle,
                 fontsize=12, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    handles = [plt.Line2D([], [], marker="s", linestyle="", markersize=10, color=c, label=lab)
               for c, lab in zip(["#1a9850", "#fee08b", "#d73027"], ["High", "Medium", "Low"])]
    handles.append(plt.Line2D([], [], marker="o", linestyle="", markersize=6,
                              markerfacecolor="white", markeredgecolor="black",
                              label="Candidate site"))
    ax.legend(handles=handles, loc="lower left", fontsize=8, framealpha=0.9)

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, dpi=dpi, format="png")
    plt.close(fig)
    return buf.getvalue()


ARTEFACTS = {
    "rwh_sites.csv": sites_csv,
    "rwh_sites.geojson": sites_geojson,
    "rwh_suitability.tif": suitability_geotiff,
    "rwh_suitability_classified.tif": classified_geotiff,
    "rwh_suitability_map.png": map_png,
}


def write_all(result: dict, outdir: str = "outputs") -> list[str]:
    """Write every artefact to `outdir`. Returns the paths written."""
    os.makedirs(outdir, exist_ok=True)
    written = []
    for name, fn in ARTEFACTS.items():
        payload = fn(result)
        if not payload:
            continue
        path = os.path.join(outdir, name)
        with open(path, "wb") as fh:
            fh.write(payload)
        written.append(path)
    return written


if __name__ == "__main__":
    from gis_analysis import run_ahp_analysis

    res = run_ahp_analysis("data")
    for p in write_all(res):
        print(f"{os.path.getsize(p):>10,} B  {p}")
