"""
algorithms.py
─────────────
Alternative MCDA engines, so the project reports more than one suitability map.

Two independent choices combine into an algorithm:

    weighting     how criterion weights are derived
                    AHP        crisp Saaty matrix, geometric-mean priority vector
                    Fuzzy-AHP  triangular fuzzy numbers, Buckley geometric mean

    aggregation   how the weighted criteria are combined per pixel
                    WLC        weighted linear combination (fully compensatory)
                    TOPSIS     closeness to the ideal solution (less compensatory)

The distinction that matters for the report: **WLC is compensatory** — a high
rainfall score can fully offset a poor slope score. **TOPSIS is not** — it
measures Euclidean distance to the ideal, so a site that is weak on any
high-weight criterion is penalised more than WLC penalises it. Comparing the
two shows whether the ranking depends on that assumption.

All engines consume the same criteria stack and the same 0–1 criterion scores,
so any difference between their outputs is attributable to the method alone.
"""

from __future__ import annotations

import numpy as np

import criteria as C


# ─────────────────────────────────────────────────────────────────────────────
# Aggregation engines
# ─────────────────────────────────────────────────────────────────────────────

def aggregate_wlc(rasters: dict, weights: dict) -> np.ndarray:
    """Weighted linear combination: S = Σ wᵢ·rᵢ, weights renormalised per pixel.

    Fully compensatory — a strong criterion offsets a weak one in direct
    proportion to their weights.
    """
    shape = next(iter(rasters.values())).shape
    weighted_sum = np.zeros(shape, dtype=np.float32)
    weight_sum = np.zeros(shape, dtype=np.float32)
    total = sum(float(weights.get(k, 0.0)) for k in rasters)

    for criterion, raster in rasters.items():
        w = float(weights.get(criterion, 0.0))
        if w <= 0:
            continue
        valid = ~np.isnan(raster)
        weighted_sum[valid] += raster[valid].astype(np.float32) * w
        weight_sum[valid] += w

    coverage = weight_sum / total if total > 0 else weight_sum
    out = np.full(shape, np.nan, dtype=np.float32)
    usable = (weight_sum > 0) & (coverage >= C.MIN_WEIGHT_COVERAGE)
    out[usable] = weighted_sum[usable] / weight_sum[usable]
    return out


def aggregate_topsis(rasters: dict, weights: dict) -> np.ndarray:
    """TOPSIS closeness coefficient, computed per pixel.

        vᵢ  = wᵢ·rᵢ                        weighted score
        A⁺  = wᵢ    (rᵢ = 1, ideal best)   theoretical, not observed
        A⁻  = 0     (rᵢ = 0, ideal worst)
        d⁺  = √Σ wᵢ²(1 − rᵢ)²
        d⁻  = √Σ wᵢ² rᵢ²
        C   = d⁻ / (d⁺ + d⁻)               → 0–1, higher is better

    The ideals are **theoretical** (the best and worst attainable score on the
    0–1 criterion scale), not the observed best and worst pixel. Using observed
    extremes would make the result depend on the data range — the same defect
    as the min–max normalisation removed in Sprint 1 — and would stop the score
    being comparable between districts or between scenario runs.

    Weights are renormalised per pixel over the criteria that have data there,
    matching WLC, and the same coverage gate applies.
    """
    shape = next(iter(rasters.values())).shape
    d_best_sq = np.zeros(shape, dtype=np.float64)
    d_worst_sq = np.zeros(shape, dtype=np.float64)
    weight_sum = np.zeros(shape, dtype=np.float32)
    total = sum(float(weights.get(k, 0.0)) for k in rasters)

    present = {}
    for criterion, raster in rasters.items():
        w = float(weights.get(criterion, 0.0))
        if w <= 0:
            continue
        valid = ~np.isnan(raster)
        weight_sum[valid] += w
        present[criterion] = (raster, w, valid)

    coverage = weight_sum / total if total > 0 else weight_sum
    usable = (weight_sum > 0) & (coverage >= C.MIN_WEIGHT_COVERAGE)

    for _criterion, (raster, w, valid) in present.items():
        # Renormalise this criterion's weight by the weight actually present.
        sel = valid & usable
        wr = np.zeros(shape, dtype=np.float64)
        wr[sel] = w / weight_sum[sel]
        r = np.nan_to_num(raster, nan=0.0).astype(np.float64)
        d_best_sq[sel] += (wr[sel] ** 2) * (1.0 - r[sel]) ** 2
        d_worst_sq[sel] += (wr[sel] ** 2) * (r[sel] ** 2)

    out = np.full(shape, np.nan, dtype=np.float32)
    d_best = np.sqrt(d_best_sq[usable])
    d_worst = np.sqrt(d_worst_sq[usable])
    denom = d_best + d_worst
    closeness = np.where(denom > 0, d_worst / np.where(denom > 0, denom, 1.0), 0.0)
    out[usable] = closeness.astype(np.float32)
    return out


AGGREGATORS = {
    "WLC": aggregate_wlc,
    "TOPSIS": aggregate_topsis,
}


# ─────────────────────────────────────────────────────────────────────────────
# Fuzzy-AHP weighting (Buckley's geometric-mean method)
# ─────────────────────────────────────────────────────────────────────────────

FUZZY_DELTA = 1.0    # ±1 step on the Saaty scale: 3 → (2, 3, 4)
SAATY_MIN, SAATY_MAX = 1.0, 9.0


def _to_tfn(matrix: np.ndarray, delta: float = FUZZY_DELTA):
    """Convert a crisp pairwise matrix to triangular fuzzy numbers (l, m, u).

    Uses the standard fuzzy Saaty scale: a judgement of 3 becomes (2, 3, 4),
    and its reciprocal 1/3 becomes (1/4, 1/3, 1/2). The spread is clipped at
    the ends of the scale, so 1 becomes (1, 1, 2) and 9 becomes (8, 9, 9).

    ⚠ A uniform *multiplicative* spread — a → (a/s, a, a·s) — must NOT be used
    here. It scales every row's fuzzy geometric mean by the same constant, so
    the fuzziness cancels exactly during normalisation and Fuzzy-AHP returns
    weights identical to crisp AHP. Verified: an earlier multiplicative
    implementation reproduced the crisp weights to 3 decimal places. The
    additive form is asymmetric at the scale ends, which is what makes the
    fuzzy weights genuinely differ.
    """
    m = np.asarray(matrix, dtype=float)
    n = m.shape[0]
    lower = np.ones_like(m)
    upper = np.ones_like(m)

    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            a = m[i, j]
            if a >= 1.0:
                lower[i, j] = max(SAATY_MIN, a - delta)
                upper[i, j] = min(SAATY_MAX, a + delta)
            else:
                inv = 1.0 / a
                lo = max(SAATY_MIN, inv - delta)
                hi = min(SAATY_MAX, inv + delta)
                lower[i, j] = 1.0 / hi
                upper[i, j] = 1.0 / lo
    return lower, m, upper


def fuzzy_ahp_weights(matrix: np.ndarray, criteria: list[str],
                      delta: float = FUZZY_DELTA) -> dict:
    """Fuzzy-AHP weights by Buckley's geometric-mean method.

    Chang's extent analysis is the more commonly cited approach but is known to
    assign zero weight to criteria that are genuinely relevant — a documented
    criticism of the method. Buckley's geometric mean cannot produce a zero
    weight and is used here instead; state that choice in the report.

    Steps: fuzzify the matrix → row geometric mean per component → fuzzy weight
    by dividing by the fuzzy column sum → defuzzify by centroid → normalise.
    """
    lower, mid, upper = _to_tfn(matrix, delta)
    n = lower.shape[0]

    r_l = np.prod(lower, axis=1) ** (1.0 / n)
    r_m = np.prod(mid, axis=1) ** (1.0 / n)
    r_u = np.prod(upper, axis=1) ** (1.0 / n)

    # Fuzzy division: (l, m, u) / (Σu, Σm, Σl)
    w_l = r_l / r_u.sum()
    w_m = r_m / r_m.sum()
    w_u = r_u / r_l.sum()

    centroid = (w_l + w_m + w_u) / 3.0
    weights = centroid / centroid.sum()
    return dict(zip(criteria, weights))


# ─────────────────────────────────────────────────────────────────────────────
# Algorithm catalogue
# ─────────────────────────────────────────────────────────────────────────────

ALGORITHMS = {
    "AHP + WLC": {
        "weighting": "AHP", "aggregation": "WLC",
        "note": "Baseline. Crisp Saaty weights, fully compensatory aggregation.",
    },
    "AHP + TOPSIS": {
        "weighting": "AHP", "aggregation": "TOPSIS",
        "note": "Same weights, ranked by closeness to the ideal solution. "
                "Penalises a site that is weak on any high-weight criterion.",
    },
    "Fuzzy-AHP + WLC": {
        "weighting": "Fuzzy-AHP", "aggregation": "WLC",
        "note": "Weights derived from fuzzified pairwise judgements (Buckley), "
                "acknowledging that expert comparisons are imprecise.",
    },
    "Fuzzy-AHP + TOPSIS": {
        "weighting": "Fuzzy-AHP", "aggregation": "TOPSIS",
        "note": "Fuzzy weights and non-compensatory aggregation combined.",
    },
}


def weights_for_algorithm(name: str, matrix, criteria: list[str]):
    """({criterion: weight}, aggregator_fn, weighting_label) for an algorithm."""
    if name not in ALGORITHMS:
        raise KeyError(f"unknown algorithm {name!r}; options: {list(ALGORITHMS)}")
    spec = ALGORITHMS[name]

    if spec["weighting"] == "Fuzzy-AHP":
        weights = fuzzy_ahp_weights(matrix, criteria)
    else:
        m = np.asarray(matrix, dtype=float)
        gm = np.prod(m, axis=1) ** (1.0 / m.shape[0])
        weights = dict(zip(criteria, gm / gm.sum()))

    return weights, AGGREGATORS[spec["aggregation"]], spec["weighting"]


# ─────────────────────────────────────────────────────────────────────────────
# Cross-algorithm comparison
# ─────────────────────────────────────────────────────────────────────────────

def _spearman(a: np.ndarray, b: np.ndarray) -> float:
    """Spearman's rank correlation coefficient between two score surfaces."""
    from scipy.stats import spearmanr
    return float(spearmanr(a, b).statistic)


def compare_algorithms(stack: dict, matrix, criteria: list[str],
                       baseline: str = "AHP + WLC", top_n: int = 10,
                       match_km: float = 2.0) -> dict:
    """Run every algorithm on one stack and measure how much they agree."""
    from gis_analysis import score_stack
    from sensitivity import _match_sites

    results, rows = {}, []
    for name in ALGORITHMS:
        weights, aggregator, _label = weights_for_algorithm(name, matrix, criteria)
        results[name] = score_stack(stack, weights, aggregator=aggregator,
                                    extract_sites=False, top_n=top_n)

    base = results[baseline]
    base_sites = base["top_locations_details"][:top_n]
    base_surface = base["suitability_raster"]
    base_class = base["classified_raster"]
    valid = ~np.isnan(base_surface)

    for name, res in results.items():
        sites = res["top_locations_details"][:top_n]
        _pairs, retained = _match_sites(base_sites, sites, match_km)

        both = valid & ~np.isnan(res["suitability_raster"])
        corr = float(np.corrcoef(base_surface[both], res["suitability_raster"][both])[0, 1]) \
            if both.sum() > 1 else float("nan")
        class_agree = float((base_class[both] == res["classified_raster"][both]).mean() * 100) \
            if both.sum() else float("nan")

        # Spearman's rho on the suitability surfaces. Pearson (above) asks
        # whether the two scores move together linearly; Spearman asks whether
        # they RANK locations the same way — the question a site-selection
        # method actually answers.
        spearman = (_spearman(base_surface[both], res["suitability_raster"][both])
                    if both.sum() > 1 else float("nan"))

        weights, _agg, label = weights_for_algorithm(name, matrix, criteria)
        rows.append({
            "algorithm": name,
            "weighting": label,
            "aggregation": ALGORITHMS[name]["aggregation"],
            "high_pct": round(res["area_statistics"]["classes"]["High"]["percent"], 2),
            "score_mean": round(float(np.nanmean(res["suitability_raster"])), 3),
            "top_overlap": retained,
            "surface_corr": round(corr, 3),
            "spearman_rho": round(spearman, 3),
            "class_agreement_pct": round(class_agree, 1),
            "weights": {k: round(v, 3) for k, v in weights.items()},
        })

    return {"baseline": baseline, "top_n": len(base_sites), "rows": rows,
            "results": results}


if __name__ == "__main__":
    from ahp import ahp_engine
    from gis_analysis import build_criteria_stack

    stack = build_criteria_stack("data")
    cmp = compare_algorithms(stack, ahp_engine.matrix, ahp_engine.criteria)

    print(f"{'algorithm':<22}{'High%':>7}{'mean':>7}{'top-10':>8}{'pearson':>9}{'spearman':>10}{'class agr':>11}")
    for r in cmp["rows"]:
        print(f"{r['algorithm']:<22}{r['high_pct']:>7.2f}{r['score_mean']:>7.3f}"
              f"{r['top_overlap']:>5}/{cmp['top_n']:<2}{r['surface_corr']:>9.3f}"
              f"{r['spearman_rho']:>10.3f}{r['class_agreement_pct']:>10.1f}%")
    print()
    print("weights by algorithm:")
    for r in cmp["rows"]:
        print(f"  {r['algorithm']:<22}" +
              "  ".join(f"{k[:4]}={v:.3f}" for k, v in r["weights"].items()))
