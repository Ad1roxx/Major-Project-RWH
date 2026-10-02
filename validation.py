"""
validation.py
─────────────
Validate a suitability surface against known rainwater harvesting structures.

    python validation.py [--structures data/rwh_structures.geojson]

The test: sample the suitability score at locations where structures already
exist, and at random background locations inside the district. If the model is
any good, the structure sites score higher. ROC-AUC quantifies "higher".

    AUC = 1.00   perfect separation
    AUC ≈ 0.50   the model is no better than chance
    AUC < 0.50   the model is inverted

This is the only thing in the project that tests the map against reality rather
than against expert judgement, so it is the number worth reporting.

⚠ REQUIRES `data/rwh_structures.geojson`, which does not exist yet. Until it
does, this module reports that the input is missing and exits — it will not
invent a number. Collect structure locations from MGNREGS asset records,
Jalyukt Shivar records, the district water conservation office, or by digitising
visible check dams and farm ponds from satellite imagery. Target 150–300 points.

Expected schema: point geometry in any CRS with a valid `crs` set. Optional
attributes `type` (structure type) and `year` are carried into the report if
present; nothing else is required.
"""

from __future__ import annotations

import argparse
import os

import numpy as np

DEFAULT_STRUCTURES = os.path.join("data", "rwh_structures.geojson")
DEFAULT_BACKGROUND_MULTIPLIER = 5     # background points per positive
DEFAULT_EXCLUSION_KM = 1.0            # keep background away from known positives
RANDOM_SEED = 42


def roc_auc(positive_scores: np.ndarray, background_scores: np.ndarray) -> float:
    """ROC-AUC via the Mann-Whitney U statistic.

    Equivalent to the probability that a randomly chosen positive scores higher
    than a randomly chosen background point, with ties counted as one half.
    Computed directly so the module needs no scikit-learn.
    """
    pos = np.asarray(positive_scores, dtype=float)
    neg = np.asarray(background_scores, dtype=float)
    pos = pos[np.isfinite(pos)]
    neg = neg[np.isfinite(neg)]
    if pos.size == 0 or neg.size == 0:
        return float("nan")

    combined = np.concatenate([pos, neg])
    order = combined.argsort(kind="mergesort")
    ranks = np.empty(combined.size, dtype=float)
    ranks[order] = np.arange(1, combined.size + 1, dtype=float)

    # Average ranks within ties so tied scores contribute 0.5 each.
    sorted_vals = combined[order]
    i = 0
    while i < sorted_vals.size:
        j = i
        while j + 1 < sorted_vals.size and sorted_vals[j + 1] == sorted_vals[i]:
            j += 1
        if j > i:
            ranks[order[i:j + 1]] = ranks[order[i:j + 1]].mean()
        i = j + 1

    rank_sum_pos = ranks[:pos.size].sum()
    u = rank_sum_pos - pos.size * (pos.size + 1) / 2.0
    return float(u / (pos.size * neg.size))


def sample_raster_at_points(raster: np.ndarray, transform, lons, lats) -> np.ndarray:
    """Sample a raster at coordinates, returning NaN outside the grid."""
    import rasterio

    rows, cols = rasterio.transform.rowcol(transform, np.asarray(lons), np.asarray(lats))
    rows = np.atleast_1d(np.asarray(rows))
    cols = np.atleast_1d(np.asarray(cols))
    inside = ((rows >= 0) & (rows < raster.shape[0])
              & (cols >= 0) & (cols < raster.shape[1]))

    out = np.full(rows.shape, np.nan, dtype=float)
    out[inside] = raster[rows[inside], cols[inside]]
    return out


def _background_points(district_mask, transform, n_points, positives_rc,
                       exclusion_px, seed=RANDOM_SEED):
    """Random in-district cells, excluding a buffer around known positives."""
    rng = np.random.default_rng(seed)
    rows, cols = np.where(district_mask)
    if rows.size == 0:
        return np.array([]), np.array([])

    blocked = set()
    for r, c in positives_rc:
        for dr in range(-exclusion_px, exclusion_px + 1):
            for dc in range(-exclusion_px, exclusion_px + 1):
                blocked.add((r + dr, c + dc))

    idx = rng.permutation(rows.size)
    picked_r, picked_c = [], []
    for i in idx:
        rc = (int(rows[i]), int(cols[i]))
        if rc in blocked:
            continue
        picked_r.append(rc[0])
        picked_c.append(rc[1])
        if len(picked_r) >= n_points:
            break
    return np.array(picked_r), np.array(picked_c)


def validate(result: dict, stack: dict, structures_path: str = DEFAULT_STRUCTURES,
             background_multiplier: int = DEFAULT_BACKGROUND_MULTIPLIER,
             exclusion_km: float = DEFAULT_EXCLUSION_KM) -> dict:
    """Validate `result`'s suitability surface against known structures.

    Returns {"status": "missing_data", ...} when the structures file is absent —
    never a fabricated score.
    """
    if not os.path.exists(structures_path):
        return {
            "status": "missing_data",
            "message": (
                f"{structures_path} not found. Validation needs known RWH structure "
                "locations; see the module docstring for where to obtain them."
            ),
        }

    import geopandas as gpd
    import rasterio

    gdf = gpd.read_file(structures_path)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")

    pts = gdf[gdf.geometry.type == "Point"]
    if pts.empty:
        return {"status": "error", "message": "no point geometries in the structures file"}

    surface = result["suitability_raster"]
    transform = result["suitability_transform"]
    district_mask = stack["district_mask"]

    lons = pts.geometry.x.to_numpy()
    lats = pts.geometry.y.to_numpy()
    pos_scores = sample_raster_at_points(surface, transform, lons, lats)
    n_outside = int(np.isnan(pos_scores).sum())
    pos_scores = pos_scores[np.isfinite(pos_scores)]

    rows, cols = rasterio.transform.rowcol(transform, lons, lats)
    positives_rc = list(zip(np.atleast_1d(rows).tolist(), np.atleast_1d(cols).tolist()))

    dy_km = abs(transform.e) * 110.574
    exclusion_px = max(1, int(round(exclusion_km / dy_km)))
    n_background = max(1, len(pos_scores) * background_multiplier)
    br, bc = _background_points(district_mask, transform, n_background,
                                positives_rc, exclusion_px)
    bg_scores = surface[br, bc] if br.size else np.array([])
    bg_scores = bg_scores[np.isfinite(bg_scores)]

    auc = roc_auc(pos_scores, bg_scores)

    classified = result["classified_raster"]
    cls = sample_raster_at_points(classified, transform, lons, lats)
    cls = cls[np.isfinite(cls)]
    in_high = float((cls == 3).mean() * 100) if cls.size else float("nan")
    in_high_or_med = float((cls >= 2).mean() * 100) if cls.size else float("nan")

    return {
        "status": "ok",
        "algorithm": result.get("algorithm"),
        "n_structures": int(len(pts)),
        "n_scored": int(pos_scores.size),
        "n_outside_grid": n_outside,
        "n_background": int(bg_scores.size),
        "auc": round(float(auc), 4),
        "mean_score_structures": round(float(pos_scores.mean()), 4) if pos_scores.size else None,
        "mean_score_background": round(float(bg_scores.mean()), 4) if bg_scores.size else None,
        "pct_structures_in_high": round(in_high, 1),
        "pct_structures_in_high_or_medium": round(in_high_or_med, 1),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Candidate sites versus existing structures
# ─────────────────────────────────────────────────────────────────────────────

def candidate_proximity(result: dict, stack: dict,
                        structures_path: str = DEFAULT_STRUCTURES,
                        n_background: int = 500) -> dict:
    """Are the proposed candidate sites near places people actually built?

    A different question from the AUC. The AUC asks whether the *surface* scores
    known structures highly. This asks whether the *shortlist* lands near them.

    For every candidate site, the distance to the nearest known structure is
    measured, and the same is done for random in-district points. If the model
    is picking the same kind of places engineers picked, candidates should be
    systematically closer than chance.

    The summary statistic is the probability that a randomly chosen candidate is
    closer to a structure than a randomly chosen background point — the same
    Mann-Whitney quantity as the AUC, computed on negated distances so that
    "closer is better". 0.5 means no better than chance.
    """
    if not os.path.exists(structures_path):
        return {"status": "missing_data",
                "message": f"{structures_path} not found."}

    import geopandas as gpd
    import rasterio

    gdf = gpd.read_file(structures_path)
    if gdf.crs is not None and gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    pts = gdf[gdf.geometry.type == "Point"]
    if pts.empty:
        return {"status": "error", "message": "no point geometries"}

    s_lon = pts.geometry.x.to_numpy()
    s_lat = pts.geometry.y.to_numpy()

    def nearest_km(lon, lat):
        d = _haversine_km_vec(lon, lat, s_lon, s_lat)
        return float(d.min())

    sites = result.get("top_locations_details") or []
    cand = np.array([nearest_km(s["lon"], s["lat"]) for s in sites]) if sites else np.array([])

    transform = result["suitability_transform"]
    rows, cols = np.where(stack["district_mask"])
    rng = np.random.default_rng(RANDOM_SEED)
    pick = rng.choice(len(rows), size=min(n_background, len(rows)), replace=False)
    bx, by = rasterio.transform.xy(transform, rows[pick], cols[pick])
    bg = np.array([nearest_km(x, y) for x, y in zip(np.atleast_1d(bx), np.atleast_1d(by))])

    closer_than_chance = roc_auc(-cand, -bg) if cand.size and bg.size else float("nan")

    return {
        "status": "ok",
        "n_candidates": int(cand.size),
        "n_background": int(bg.size),
        "n_structures": int(len(pts)),
        "candidate_median_km": round(float(np.median(cand)), 2) if cand.size else None,
        "candidate_mean_km": round(float(cand.mean()), 2) if cand.size else None,
        "background_median_km": round(float(np.median(bg)), 2) if bg.size else None,
        "background_mean_km": round(float(bg.mean()), 2) if bg.size else None,
        "closer_than_chance": round(float(closer_than_chance), 4),
        "candidates_within_2km": int((cand <= 2.0).sum()) if cand.size else 0,
        "candidates_within_5km": int((cand <= 5.0).sum()) if cand.size else 0,
    }


def _haversine_km_vec(lon1, lat1, lon2, lat2):
    """Distance from one point to an array of points, in km."""
    lon1, lat1 = np.radians(lon1), np.radians(lat1)
    lon2, lat2 = np.radians(np.asarray(lon2)), np.radians(np.asarray(lat2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


# ─────────────────────────────────────────────────────────────────────────────
# Per-algorithm comparison
# ─────────────────────────────────────────────────────────────────────────────

def validate_all_algorithms(stack: dict, structures_path: str = DEFAULT_STRUCTURES,
                            matrix=None) -> dict:
    """Validate every algorithm against the same structures — the only honest
    way to say which one performs best.

    Until this runs on real data the paper can say the methods *differ*; it
    cannot say one is better. Ranking by AUC requires an external standard, and
    this is it.
    """
    if not os.path.exists(structures_path):
        return {"status": "missing_data",
                "message": f"{structures_path} not found; cannot rank methods by accuracy."}

    from ahp import ahp_engine
    from algorithms import ALGORITHMS, weights_for_algorithm
    from gis_analysis import score_stack

    if matrix is None:
        matrix = ahp_engine.matrix

    rows = []
    for name in ALGORITHMS:
        weights, aggregator, _label = weights_for_algorithm(
            name, matrix, ahp_engine.criteria)
        res = score_stack(stack, weights, aggregator=aggregator, algorithm=name)
        v = validate(res, stack, structures_path)
        prox = candidate_proximity(res, stack, structures_path)
        if v.get("status") != "ok":
            continue
        rows.append({
            "algorithm": name,
            "auc": v["auc"],
            "pct_in_high": v["pct_structures_in_high"],
            "pct_in_high_or_medium": v["pct_structures_in_high_or_medium"],
            "candidate_median_km": prox.get("candidate_median_km"),
            "closer_than_chance": prox.get("closer_than_chance"),
        })

    rows.sort(key=lambda r: -(r["auc"] or 0))
    return {"status": "ok", "rows": rows,
            "best": rows[0]["algorithm"] if rows else None}


def summary_sentence(v: dict) -> str:
    if v.get("status") != "ok":
        return v.get("message", "validation not run")
    return (
        f"Validated against {v['n_scored']} known structures with "
        f"{v['n_background']} background points: ROC-AUC {v['auc']:.3f}. "
        f"{v['pct_structures_in_high_or_medium']:.0f}% of existing structures fall in "
        f"Medium or High suitability ({v['pct_structures_in_high']:.0f}% in High). "
        f"Mean score at structures {v['mean_score_structures']:.3f} vs "
        f"{v['mean_score_background']:.3f} at background points."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate suitability against known structures.")
    ap.add_argument("--structures", default=DEFAULT_STRUCTURES)
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--background-multiplier", type=int, default=DEFAULT_BACKGROUND_MULTIPLIER)
    args = ap.parse_args()

    from ahp import ahp_engine
    from gis_analysis import build_criteria_stack, score_stack

    stack = build_criteria_stack(args.data_dir)
    weights, cr = ahp_engine.calculate_weights()
    result = score_stack(stack, weights, cr)

    out = validate(result, stack, args.structures, args.background_multiplier)
    if out["status"] != "ok":
        print(f"[{out['status']}] {out['message']}")
        raise SystemExit(1)

    for k, v in out.items():
        print(f"  {k:<34} {v}")
    print()
    print(summary_sentence(out))

    prox = candidate_proximity(result, stack, args.structures)
    if prox.get("status") == "ok":
        print()
        print("=== candidate sites vs existing structures ===")
        for k, v in prox.items():
            if k != "status":
                print(f"  {k:<34} {v}")

    print()
    print("=== per-algorithm ranking ===")
    comp = validate_all_algorithms(stack, args.structures)
    if comp.get("status") == "ok":
        print(f"{'algorithm':<22}{'AUC':>8}{'% in High':>11}{'% High+Med':>12}"
              f"{'cand median km':>16}")
        for r in comp["rows"]:
            print(f"{r['algorithm']:<22}{r['auc']:>8.3f}{r['pct_in_high']:>11.1f}"
                  f"{r['pct_in_high_or_medium']:>12.1f}{r['candidate_median_km']:>16.2f}")
        print(f"  best by AUC: {comp['best']}")
    else:
        print(f"  {comp.get('message')}")


if __name__ == "__main__":
    main()
