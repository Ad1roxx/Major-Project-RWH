"""
utils/structures.py — existing MGNREGA water works for the browser map.

Display and comparison only: nothing here feeds the suitability model.

Two point sets:
  • water works: every in-district MGNREGA geotag in the two water categories
    (WC, WH), from data/interim/mgnrega_all.parquet. The photo audit
    (docs/PHOTO_LABELLING_PROTOCOL.md) found only about 17% (strict) to 49%
    (lenient) of these photos show a harvesting structure, so they are
    unverified works, not confirmed structures.
  • photo-confirmed structures: the audit photos either labeller marked storage
    or recharge, built by tools/build_structure_layer.py (git-ignored output).
    Strict ones (both labellers) carry an embedded, privacy-checked thumbnail.

No observer names or other personal fields are read. Photos of the unverified
works are linked to their published Bhuvan URL, not copied.
"""
from __future__ import annotations

import base64
import functools
import math
import os

import numpy as np

WATER_CATEGORIES = ("WC", "WH")
CATEGORY_NAMES = {"WC": "Water conservation (WC)", "WH": "Water harvesting (WH)"}
STAGE_NAMES = {"0": "Phase I (works before Nov 2017)", "3": "Phase II (geotag at completion)"}
# A candidate site "has a structure" if one lies within the 600 m circle the
# map draws around each site.
OVERLAP_KM = 0.6

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PARQUET = os.path.join(_ROOT, "data", "interim", "mgnrega_all.parquet")
_LAYER = os.path.join(_ROOT, "reports", "photo_audit", "map_layer")


@functools.lru_cache(maxsize=1)
def load_water_works() -> list[dict]:
    """In-district WC/WH geotags: lat, lon, category, stage, photo URL."""
    if not os.path.exists(_PARQUET):
        return []
    import pandas as pd
    df = pd.read_parquet(_PARQUET, columns=["lat", "lon", "category_seg", "stage",
                                            "path1", "inside_district"])
    df = df[df["category_seg"].isin(WATER_CATEGORIES) & df["inside_district"].astype(bool)]
    return [{"lat": float(r.lat), "lon": float(r.lon), "category": r.category_seg,
             "stage": str(r.stage), "url": r.path1 or ""}
            for r in df.itertuples(index=False)]


@functools.lru_cache(maxsize=1)
def load_confirmed() -> list[dict]:
    """Photo-confirmed structures; strict ones carry a base64 thumbnail."""
    path = os.path.join(_LAYER, "confirmed_structures.csv")
    if not os.path.exists(path):
        return []
    import pandas as pd
    out = []
    for r in pd.read_csv(path, dtype={"collection_sno": str, "stage": str}).itertuples(index=False):
        thumb = None
        tpath = os.path.join(_LAYER, "thumbs", f"{r.collection_sno}.jpg")
        if r.rule == "strict" and os.path.exists(tpath):
            with open(tpath, "rb") as fh:
                thumb = "data:image/jpeg;base64," + base64.b64encode(fh.read()).decode("ascii")
        out.append({"lat": float(r.lat), "lon": float(r.lon), "rule": r.rule,
                    "category": r.category_seg, "stage": str(r.stage),
                    "labels": f"{r.label_a} / {r.label_b}", "url": r.photo_url,
                    "thumb": thumb})
    return out


def zone_of_points(points: list[dict], result: dict) -> list[int | None]:
    """Suitability class (1 Low, 2 Medium, 3 High) of the cell under each point."""
    classified = result.get("classified_raster")
    transform = result.get("suitability_transform")
    if classified is None or transform is None:
        return [None] * len(points)
    inv = ~transform
    rows, cols = classified.shape
    out = []
    for p in points:
        c, r = inv * (p["lon"], p["lat"])
        r, c = int(math.floor(r)), int(math.floor(c))
        v = classified[r, c] if 0 <= r < rows and 0 <= c < cols else np.nan
        out.append(None if np.isnan(v) else int(v))
    return out


def enrichment(points: list[dict], zones: list[int | None], result: dict) -> dict | None:
    """Share of points in each class against that class's share of the district."""
    scored = [z for z in zones if z is not None]
    if not scored:
        return None
    classes = (result.get("area_statistics") or {}).get("classes") or {}
    out = {"n": len(scored)}
    for code, name in ((3, "High"), (2, "Medium"), (1, "Low")):
        pts = 100.0 * sum(z == code for z in scored) / len(scored)
        area = classes.get(name, {})
        area_pct = area.get("percent_exact", area.get("percent"))
        out[name] = {"points_pct": pts, "area_pct": area_pct,
                     "ratio": (pts / area_pct) if area_pct else None}
    return out


def _haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dp, dl = p2 - p1, np.radians(lon2 - lon1)
    a = np.sin(dp / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def nearest(site: dict, points: list[dict]) -> tuple[float, dict] | None:
    """The point nearest a site, as (distance_km, point)."""
    if not points:
        return None
    lat = np.array([p["lat"] for p in points])
    lon = np.array([p["lon"] for p in points])
    d = _haversine_km(site["lat"], site["lon"], lat, lon)
    i = int(np.argmin(d))
    return float(d[i]), points[i]


# ── Water and farmland context of a site (shown for the farmland scenario) ──
CROPLAND_CODE = 12          # MODIS IGBP LC_Type1 "Croplands"
FARMLAND_RADIUS_KM = 1.0    # the farmland a structure at the site could serve
NEAREST_WORKS = 3           # unverified works listed per site, with photo links
_RIVERS_M = {}


def _rivers_metric(rivers_gdf):
    key = id(rivers_gdf)
    if key not in _RIVERS_M:
        _RIVERS_M.clear()
        _RIVERS_M[key] = rivers_gdf.to_crs(32644)   # UTM 44N, metres
    return _RIVERS_M[key]


def site_context(site: dict, stack: dict, works: list[dict],
                 confirmed: list[dict]) -> dict:
    """Distances to existing water features, and the farmland around a site.

    Returns km to the nearest WC/WH work, photo-confirmed structure and mapped
    river (HydroRIVERS, larger channels only), the land cover at the site, and
    the cropland area within FARMLAND_RADIUS_KM. Nothing here feeds the score.
    """
    ctx = {}
    w = nearest(site, works)
    if w:
        ctx["work_km"], ctx["work_cat"] = w[0], w[1]["category"]
    if works:
        lat = np.array([p["lat"] for p in works])
        lon = np.array([p["lon"] for p in works])
        d = _haversine_km(site["lat"], site["lon"], lat, lon)
        ctx["works_near"] = [
            {"km": float(d[i]), "category": works[i]["category"],
             "stage": works[i]["stage"], "url": works[i]["url"]}
            for i in np.argsort(d)[:NEAREST_WORKS]]
    c = nearest(site, confirmed)
    if c:
        ctx["confirmed_km"], ctx["confirmed_rule"] = c[0], c[1]["rule"]

    rivers = stack.get("rivers_gdf")
    if rivers is not None and len(rivers):
        from shapely.geometry import Point
        import geopandas as gpd
        pt = gpd.GeoSeries([Point(site["lon"], site["lat"])], crs=4326).to_crs(32644).iloc[0]
        ctx["river_km"] = float(_rivers_metric(rivers).distance(pt).min()) / 1000.0

    lulc = (stack.get("raw_rasters") or {}).get("lulc")
    transform, mask = stack.get("transform"), stack.get("district_mask")
    if lulc is not None and transform is not None:
        inv = ~transform
        col, row = inv * (site["lon"], site["lat"])
        r0, c0 = int(math.floor(row)), int(math.floor(col))
        dx, dy = abs(transform.a), abs(transform.e)
        km_x = dx * 111.32 * math.cos(math.radians(site["lat"]))
        km_y = dy * 110.57
        nr = int(math.ceil(FARMLAND_RADIUS_KM / km_y)) + 1
        nc = int(math.ceil(FARMLAND_RADIUS_KM / km_x)) + 1
        rr, cc = np.mgrid[max(r0 - nr, 0):min(r0 + nr + 1, lulc.shape[0]),
                          max(c0 - nc, 0):min(c0 + nc + 1, lulc.shape[1])]
        dist = np.hypot((rr - r0) * km_y, (cc - c0) * km_x)
        inside = dist <= FARMLAND_RADIUS_KM
        if mask is not None:
            inside &= mask[rr, cc].astype(bool)
        cells = lulc[rr, cc][inside]
        cell_km2 = km_x * km_y
        ctx["area_km2"] = float(inside.sum() * cell_km2)
        ctx["cropland_km2"] = float((cells == CROPLAND_CODE).sum() * cell_km2)
        if 0 <= r0 < lulc.shape[0] and 0 <= c0 < lulc.shape[1]:
            ctx["on_cropland"] = bool(lulc[r0, c0] == CROPLAND_CODE)
    return ctx


def works_links_html(ctx: dict) -> str:
    """The nearest unverified works, each linked to its Bhuvan photo."""
    items = []
    for w in ctx.get("works_near") or []:
        label = f"{w['km']:.2f} km {w['category']}"
        items.append(f"<a href='{w['url']}' target='_blank' rel='noopener'>{label} &#8599;</a>"
                     if w.get("url") else label)
    return ", ".join(items)


def nearby(site: dict, points: list[dict], km: float = OVERLAP_KM) -> list[tuple[float, dict]]:
    """Points within `km` of a site, nearest first, as (distance_km, point)."""
    if not points:
        return []
    lat = np.array([p["lat"] for p in points])
    lon = np.array([p["lon"] for p in points])
    d = _haversine_km(site["lat"], site["lon"], lat, lon)
    idx = np.where(d <= km)[0]
    return sorted(((float(d[i]), points[i]) for i in idx), key=lambda t: t[0])
