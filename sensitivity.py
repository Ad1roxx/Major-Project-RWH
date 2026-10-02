"""
sensitivity.py
──────────────
One-way sensitivity analysis on the AHP weights.

The standard criticism of AHP is that the weights are expert judgement, so the
result is whatever the analyst decided. The answer is to show how much the
result actually moves when the weights move.

For each criterion in turn, its weight is scaled by (1 ± delta) and the
remaining weights are rescaled to keep the vector summing to 1. The stack is
re-scored and the new ranking is compared against the baseline.

Cheap because `build_criteria_stack()` runs once: a full 12-run sweep re-scores
in roughly 2 seconds.

Reported per run:
    retained     how many of the baseline top-N survive in the perturbed top-N
    max shift    largest rank change among the sites that survived
    High %       change in the share of the district classed highly suitable

A site is matched between runs by position, not by rank — candidates are
extracted independently each time, so coordinates move slightly. The default
2 km tolerance is well inside the 5 km minimum separation between sites, so a
match is never ambiguous.
"""

from __future__ import annotations

import numpy as np

from gis_analysis import score_stack

DEFAULT_DELTA = 0.20
DEFAULT_TOP_N = 10
DEFAULT_MATCH_KM = 2.0


def perturb_weights(weights: dict, criterion: str, factor: float) -> dict:
    """Scale one weight by `factor`, rescaling the others to keep the sum at 1."""
    if criterion not in weights:
        raise KeyError(criterion)

    w = {k: float(v) for k, v in weights.items()}
    target = w[criterion] * factor
    target = min(max(target, 1e-6), 0.999)

    others = {k: v for k, v in w.items() if k != criterion}
    others_total = sum(others.values())
    if others_total <= 0:
        return {criterion: 1.0, **{k: 0.0 for k in others}}

    scale = (1.0 - target) / others_total
    out = {k: v * scale for k, v in others.items()}
    out[criterion] = target
    return {k: out[k] for k in weights}


def _haversine_km(lon1, lat1, lon2, lat2) -> float:
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return float(6371.0 * 2 * np.arcsin(np.sqrt(a)))


def _match_sites(base: list[dict], other: list[dict], match_km: float):
    """Pair baseline sites with perturbed sites by position.

    Returns (pairs, retained) where pairs is [(base_rank, other_rank), ...].
    """
    pairs = []
    used = set()
    for b in base:
        best, best_d = None, match_km
        for o in other:
            if o["rank"] in used:
                continue
            d = _haversine_km(b["lon"], b["lat"], o["lon"], o["lat"])
            if d < best_d:
                best, best_d = o, d
        if best is not None:
            used.add(best["rank"])
            pairs.append((b["rank"], best["rank"]))
    return pairs, len(pairs)


def one_way_sensitivity(stack: dict, base_weights: dict,
                        delta: float = DEFAULT_DELTA,
                        top_n: int = DEFAULT_TOP_N,
                        match_km: float = DEFAULT_MATCH_KM) -> dict:
    """Vary each weight by ±delta and measure how far the ranking moves."""
    baseline = score_stack(stack, base_weights, extract_sites=False, top_n=top_n)
    base_sites = baseline["top_locations_details"][:top_n]
    base_high = baseline["area_statistics"]["classes"]["High"]["percent"]

    runs = []
    for criterion in sorted(base_weights, key=lambda k: -base_weights[k]):
        for direction, factor in (("−", 1.0 - delta), ("+", 1.0 + delta)):
            w = perturb_weights(base_weights, criterion, factor)
            res = score_stack(stack, w, extract_sites=False, top_n=top_n)
            sites = res["top_locations_details"][:top_n]
            high = res["area_statistics"]["classes"]["High"]["percent"]

            pairs, retained = _match_sites(base_sites, sites, match_km)
            max_shift = max((abs(a - b) for a, b in pairs), default=0)

            runs.append({
                "criterion": criterion,
                "direction": direction,
                "weight_from": round(base_weights[criterion], 3),
                "weight_to": round(w[criterion], 3),
                "retained": retained,
                "retained_pct": round(100.0 * retained / max(1, len(base_sites)), 1),
                "max_rank_shift": max_shift,
                "high_pct": round(high, 2),
                "high_pct_delta": round(high - base_high, 2),
            })

    retained_all = [r["retained_pct"] for r in runs]
    shifts = [r["max_rank_shift"] for r in runs]

    # Which criterion moves the answer most, averaged over its two directions.
    influence = {}
    for criterion in base_weights:
        rows = [r for r in runs if r["criterion"] == criterion]
        if rows:
            influence[criterion] = round(
                float(np.mean([abs(r["high_pct_delta"]) for r in rows])), 2)

    return {
        "delta": delta,
        "top_n": len(base_sites),
        "baseline_high_pct": round(base_high, 2),
        "runs": runs,
        "mean_retained_pct": round(float(np.mean(retained_all)), 1),
        "worst_retained_pct": round(float(np.min(retained_all)), 1),
        "max_rank_shift": int(np.max(shifts)) if shifts else 0,
        "influence_high_pct": dict(sorted(influence.items(), key=lambda kv: -kv[1])),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Map removal sensitivity analysis (Lodwick, Monson & Svoboda, 1990)
# ─────────────────────────────────────────────────────────────────────────────

def map_removal_sensitivity(stack: dict, base_weights: dict,
                            top_n: int = DEFAULT_TOP_N,
                            match_km: float = DEFAULT_MATCH_KM) -> dict:
    """Drop each criterion layer entirely and measure how far the map moves.

    Weight perturbation (one_way_sensitivity) asks "what if this criterion
    mattered somewhat more or less?". Map removal asks the harder question:
    "what if we did not have this layer at all?" — which is what a reviewer
    means when they doubt a criterion earns its place, and what a practitioner
    means when a neighbouring district lacks the data.

    Removal is implemented by setting the criterion's weight to zero. The
    per-pixel renormalisation in the aggregator then redistributes its weight
    across the remaining criteria automatically.

    **Index.** The original formulation is S = |V/N − V'/n| / V × 100, where the
    /N and /n terms convert a weighted *sum* over N (then n) parameters into a
    per-parameter average. This project's aggregation already divides by the sum
    of the weights present, so V and V' are both on a 0–1 scale and directly
    comparable; applying /N and /n again would normalise twice. The index used
    here is therefore the relative variation

        S_i = mean over district pixels of  |V − V'_i| / V × 100

    which is the same quantity the original expresses, without the double
    normalisation. State this adaptation in the paper.
    """
    base = score_stack(stack, base_weights, extract_sites=False, top_n=top_n)
    V = base["suitability_raster"]
    base_sites = base["top_locations_details"][:top_n]
    base_high = base["area_statistics"]["classes"]["High"]["percent"]
    valid = ~np.isnan(V)

    rows = []
    for criterion in sorted(base_weights, key=lambda k: -base_weights[k]):
        reduced = {k: (0.0 if k == criterion else v) for k, v in base_weights.items()}
        total = sum(reduced.values())
        if total <= 0:
            continue
        reduced = {k: v / total for k, v in reduced.items()}

        res = score_stack(stack, reduced, extract_sites=False, top_n=top_n)
        Vp = res["suitability_raster"]
        both = valid & ~np.isnan(Vp)

        abs_diff = np.abs(V[both] - Vp[both])
        nonzero = V[both] > 0
        rel = 100.0 * abs_diff[nonzero] / V[both][nonzero]

        sites = res["top_locations_details"][:top_n]
        _pairs, retained = _match_sites(base_sites, sites, match_km)
        high = res["area_statistics"]["classes"]["High"]["percent"]

        rows.append({
            "criterion": criterion,
            "weight": round(base_weights[criterion], 3),
            "sensitivity_index": round(float(rel.mean()), 3),      # %
            "max_index": round(float(rel.max()), 2),
            "mean_abs_change": round(float(abs_diff.mean()), 4),   # 0–1 units
            "retained": retained,
            "high_pct": round(high, 2),
            "high_pct_delta": round(high - base_high, 2),
        })

    rows.sort(key=lambda r: -r["sensitivity_index"])
    return {"baseline_high_pct": round(base_high, 2), "top_n": len(base_sites),
            "rows": rows}


# ─────────────────────────────────────────────────────────────────────────────
# Single-parameter sensitivity (Napolitano & Fabbri, 1996)
# ─────────────────────────────────────────────────────────────────────────────

def single_parameter_sensitivity(stack: dict, base_weights: dict) -> dict:
    """Effective weight of each criterion versus its assigned (theoretical) weight.

    The effective weight of criterion i at a pixel is the share of the final
    score that criterion actually contributed:

        W_i = (w_i · r_i) / V × 100

    Averaged over the district this is directly comparable with the theoretical
    weight w_i × 100 from AHP. A criterion that scores highly across the whole
    district contributes more than its assigned weight; one that scores poorly
    contributes less.

    This is the formal version of an observation the ±20% analysis already
    surfaces informally — that weight magnitude and actual influence are
    different things.
    """
    base = score_stack(stack, base_weights, extract_sites=False)
    V = base["suitability_raster"]
    valid = ~np.isnan(V) & (V > 0)
    rasters = stack["normalized_rasters"]

    rows = []
    for criterion, w in base_weights.items():
        if criterion not in rasters:
            continue
        r = rasters[criterion]
        both = valid & ~np.isnan(r)
        if not both.any():
            continue
        eff = 100.0 * (w * r[both]) / V[both]
        rows.append({
            "criterion": criterion,
            "theoretical_pct": round(100.0 * w, 2),
            "effective_pct": round(float(eff.mean()), 2),
            "effective_sd": round(float(eff.std()), 2),
            "ratio": round(float(eff.mean()) / (100.0 * w), 3) if w > 0 else None,
        })

    rows.sort(key=lambda x: -x["effective_pct"])
    return {"rows": rows}


def summary_sentence(result: dict) -> str:
    """One line suitable for the report or a slide."""
    worst = max(result["influence_high_pct"].items(), key=lambda kv: kv[1]) \
        if result["influence_high_pct"] else ("n/a", 0.0)
    return (
        f"Varying each AHP weight by ±{result['delta'] * 100:.0f}% retains "
        f"{result['mean_retained_pct']:.0f}% of the top-{result['top_n']} sites on "
        f"average ({result['worst_retained_pct']:.0f}% worst case), with a maximum "
        f"rank shift of {result['max_rank_shift']}. The result is most sensitive to "
        f"{worst[0]} (mean {worst[1]:.2f} pp change in highly-suitable area)."
    )


if __name__ == "__main__":
    from ahp import ahp_engine
    from gis_analysis import build_criteria_stack

    stack = build_criteria_stack("data")
    weights, _cr = ahp_engine.calculate_weights()
    out = one_way_sensitivity(stack, weights)

    print(f"{'criterion':<12}{'dir':<5}{'weight':>16}{'retained':>10}{'shift':>7}{'High%':>8}{'Δ':>8}")
    for r in out["runs"]:
        print(f"{r['criterion']:<12}{r['direction']:<5}"
              f"{r['weight_from']:>7.3f}→{r['weight_to']:<8.3f}"
              f"{r['retained']:>6}/{out['top_n']:<3}{r['max_rank_shift']:>6}"
              f"{r['high_pct']:>8.2f}{r['high_pct_delta']:>+8.2f}")
    print()
    print(summary_sentence(out))

    print()
    print("=== map removal sensitivity (Lodwick et al. 1990) ===")
    mr = map_removal_sensitivity(stack, weights)
    print(f"{'criterion':<12}{'weight':>8}{'S index %':>11}{'max %':>8}"
          f"{'mean |dV|':>11}{'retained':>10}{'High %':>9}{'delta':>8}")
    for r in mr["rows"]:
        print(f"{r['criterion']:<12}{r['weight']:>8.3f}{r['sensitivity_index']:>11.3f}"
              f"{r['max_index']:>8.2f}{r['mean_abs_change']:>11.4f}"
              f"{r['retained']:>7}/{mr['top_n']:<2}{r['high_pct']:>9.2f}"
              f"{r['high_pct_delta']:>+8.2f}")

    print()
    print("=== single-parameter sensitivity (Napolitano & Fabbri 1996) ===")
    sp = single_parameter_sensitivity(stack, weights)
    print(f"{'criterion':<12}{'theoretical %':>15}{'effective %':>13}{'sd':>8}{'ratio':>8}")
    for r in sp["rows"]:
        print(f"{r['criterion']:<12}{r['theoretical_pct']:>15.2f}"
              f"{r['effective_pct']:>13.2f}{r['effective_sd']:>8.2f}{r['ratio']:>8.3f}")
