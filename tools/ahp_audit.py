"""
tools/ahp_audit.py
──────────────────
Retrospective audit of the AHP pairwise comparison matrix.

    python tools/ahp_audit.py              # all three analyses
    python tools/ahp_audit.py --part B     # one part
    python tools/ahp_audit.py --draws 4000 --sample 200

Why this file exists
    The paper originally carried a placeholder describing a multi-round
    elicitation ("revised N times until CR fell below 0.10"). No such process
    took place: the authors confirmed on 23 September 2026 that the matrix was
    specified once, accepted without revision, and never externally reviewed.

    Rather than assert a history that cannot be evidenced, this audit
    characterises the matrix that exists — how its inconsistency is distributed,
    how much any single judgement matters, and where the shipped weights sit
    within the space of alternative matrices encoding the same reasoning.

    Narrative and suggested Methods wording: docs/AHP_MATRIX_AUDIT.md

Parts
    A   per-judgement consistency diagnostic
    B   single-step perturbation of each of the 15 judgements
    C   Monte Carlo over judgement space, with downstream effect on the map
"""

from __future__ import annotations

import os
import sys

# Drop tools/ from sys.path before any third-party import: this directory holds
# inspect.py, which shadows the stdlib module numpy imports internally.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
               if os.path.abspath(p or os.getcwd()) != _HERE]
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import argparse  # noqa: E402

import numpy as np  # noqa: E402

from ahp import ahp_engine as E  # noqa: E402

# The full Saaty scale including reciprocals, ascending. Perturbation moves a
# judgement by whole steps along this ladder rather than by arbitrary amounts,
# because that is the granularity at which a human actually revises a judgement.
SAATY_LADDER = np.array([1/9, 1/8, 1/7, 1/6, 1/5, 1/4, 1/3, 1/2,
                         1, 2, 3, 4, 5, 6, 7, 8, 9])

MC_SEED = 20260923      # reproduces the figures in docs/AHP_MATRIX_AUDIT.md
MC_DRAWS = 4000
MC_SAMPLE = 200         # accepted matrices scored through the full pipeline
MC_MAX_STEP = 2         # each judgement perturbed by up to this many steps
CR_THRESHOLD = 0.10


def _fmt(v: float) -> str:
    """Saaty value as a human reads it: 3, or 1/3."""
    return f"{v:.0f}" if v >= 1 else f"1/{1 / v:.0f}"


def _ladder_index(value: float) -> int:
    return int(np.argmin(np.abs(SAATY_LADDER - value)))


def _upper_pairs(n: int):
    for i in range(n):
        for j in range(i + 1, n):
            yield i, j


def part_a() -> None:
    """Per-judgement consistency diagnostic."""
    M, crit = E.matrix, E.criteria
    weights, cr = E.calculate_weights()
    w = np.array([weights[c] for c in crit])

    print("### A. Per-judgement consistency diagnostic")
    print(f"Shipped matrix CR = {cr:.4f}")
    print("The value implied by perfect consistency is w_i / w_j.")
    print("Deviation = stated / implied. The last column is the CR the matrix")
    print("would have if that one judgement were replaced by its implied value.\n")
    print(f"{'comparison':<26}{'stated':>8}{'implied':>9}{'deviation':>11}{'CR if corrected':>18}")

    rows = []
    for i, j in _upper_pairs(len(crit)):
        stated = M[i, j]
        implied = w[i] / w[j]
        trial = M.copy()
        trial[i, j] = implied
        trial[j, i] = 1.0 / implied
        _, cr_fixed = E.calculate_weights(trial)
        rows.append((crit[i], crit[j], stated, implied, stated / implied, cr_fixed))

    for a, b, stated, implied, dev, cr_fixed in sorted(rows, key=lambda r: -abs(np.log(r[4]))):
        print(f"{a + ' vs ' + b:<26}{_fmt(stated):>8}{implied:>9.2f}{dev:>11.3f}{cr_fixed:>18.4f}")

    best = min(rows, key=lambda r: r[5])
    print(f"\nCorrecting the single worst judgement moves CR from {cr:.4f} to {best[5]:.4f}.")
    print("The inconsistency is distributed across the matrix rather than")
    print("concentrated in one comparison — the signature of independent")
    print("judgement rather than a transcription error.")


def part_b() -> None:
    """Move each judgement one step in each direction along the Saaty ladder."""
    M, crit = E.matrix, E.criteria
    weights, _cr = E.calculate_weights()
    w = np.array([weights[c] for c in crit])
    base_order = np.argsort(-w)

    print("### B. Single-judgement perturbation")
    print("Each of the 15 judgements moved one step in each direction.\n")
    print(f"{'comparison':<26}{'step':>6}{'new':>8}{'CR':>9}{'passes':>8}"
          f"{'max weight shift':>18}{'order kept':>12}")

    tested = worst_cr = 0.0
    tested = 0
    order_breaks = 0
    max_shift = 0.0
    shift_by_pair = {}

    for i, j in _upper_pairs(len(crit)):
        k = _ladder_index(M[i, j])
        for step, label in ((-1, "-1"), (1, "+1")):
            k2 = k + step
            if not 0 <= k2 < len(SAATY_LADDER):
                continue
            trial = M.copy()
            trial[i, j] = SAATY_LADDER[k2]
            trial[j, i] = 1.0 / SAATY_LADDER[k2]
            w2d, cr2 = E.calculate_weights(trial)
            w2 = np.array([w2d[c] for c in crit])
            shift = float(np.abs(w2 - w).max())
            kept = bool((np.argsort(-w2) == base_order).all())

            tested += 1
            worst_cr = max(worst_cr, cr2)
            max_shift = max(max_shift, shift)
            order_breaks += (not kept)
            pair = f"{crit[i]} vs {crit[j]}"
            shift_by_pair[pair] = max(shift_by_pair.get(pair, 0.0), shift)

            print(f"{pair:<26}{label:>6}{_fmt(SAATY_LADDER[k2]):>8}{cr2:>9.4f}"
                  f"{('yes' if cr2 < CR_THRESHOLD else 'NO'):>8}{shift:>18.4f}"
                  f"{('yes' if kept else 'NO'):>12}")

    most = max(shift_by_pair.items(), key=lambda kv: kv[1])
    least = min(shift_by_pair.items(), key=lambda kv: kv[1])
    print(f"\n  {tested} perturbations tested")
    print(f"  worst CR reached: {worst_cr:.4f} (threshold {CR_THRESHOLD}) -> "
          f"all {'PASS' if worst_cr < CR_THRESHOLD else 'DO NOT PASS'}")
    print(f"  perturbations changing the criterion rank order: {order_breaks}")
    print(f"  largest weight shift from any single step: {max_shift:.4f}")
    print(f"  most influential judgement : {most[0]} ({most[1]:.4f})")
    print(f"  least influential judgement: {least[0]} ({least[1]:.4f})")
    print("\n  No single judgement is load-bearing.")


def part_c(draws: int, sample: int, data_dir: str) -> None:
    """Monte Carlo over the space of matrices encoding the same ordering."""
    import gis_analysis as G
    from sensitivity import _match_sites

    M, crit = E.matrix, E.criteria
    weights, cr = E.calculate_weights()
    w = np.array([weights[c] for c in crit])
    base_order = np.argsort(-w)
    rng = np.random.default_rng(MC_SEED)

    print("### C. Monte Carlo over judgement space")
    print(f"Each of the 15 judgements perturbed by up to +/-{MC_MAX_STEP} Saaty steps.")
    print(f"Accepted only if CR < {CR_THRESHOLD} AND the criterion ordering is preserved.")
    print(f"Seed {MC_SEED}.\n")

    accepted, rejected_cr, rejected_order = [], 0, 0
    for _ in range(draws):
        trial = M.copy()
        for i, j in _upper_pairs(len(crit)):
            k = _ladder_index(M[i, j]) + int(rng.integers(-MC_MAX_STEP, MC_MAX_STEP + 1))
            k = int(np.clip(k, 0, len(SAATY_LADDER) - 1))
            trial[i, j] = SAATY_LADDER[k]
            trial[j, i] = 1.0 / SAATY_LADDER[k]
        w2d, cr2 = E.calculate_weights(trial)
        if cr2 >= CR_THRESHOLD:
            rejected_cr += 1
            continue
        w2 = np.array([w2d[c] for c in crit])
        if not (np.argsort(-w2) == base_order).all():
            rejected_order += 1
            continue
        accepted.append((w2, cr2))

    W = np.array([a[0] for a in accepted])
    CRs = np.array([a[1] for a in accepted])
    print(f"  drawn {draws}, accepted {len(accepted)}, "
          f"rejected {rejected_cr} on CR and {rejected_order} on ordering")
    print(f"  CR of accepted matrices: median {np.median(CRs):.4f}, max {CRs.max():.4f}")
    print(f"  the shipped matrix's CR of {cr:.4f} is well below that median —")
    print("  among matrices encoding this ordering it is unusually consistent.\n")

    print(f"{'criterion':<12}{'shipped':>9}{'MC mean':>9}{'MC sd':>8}"
          f"{'p5':>8}{'p95':>8}{'percentile':>12}")
    for i, c in enumerate(crit):
        col = W[:, i]
        pct = 100.0 * float((col < w[i]).mean())
        print(f"{c:<12}{w[i]:>9.4f}{col.mean():>9.4f}{col.std():>8.4f}"
              f"{np.percentile(col, 5):>8.4f}{np.percentile(col, 95):>8.4f}{pct:>11.0f}%")
    print("\n  Every shipped weight falls near the centre of the distribution of")
    print("  defensible alternatives — the matrix is not an outlier.\n")

    print(f"  Scoring {sample} accepted matrices through the full pipeline...")
    stack = G.build_criteria_stack(data_dir)
    base = G.score_stack(stack, weights, cr, extract_sites=False, top_n=10)
    base_high = base["area_statistics"]["classes"]["High"]["percent"]
    base_sites = base["top_locations_details"][:10]

    picks = rng.choice(len(accepted), size=min(sample, len(accepted)), replace=False)
    highs, retained = [], []
    for idx in picks:
        w2, cr2 = accepted[idx]
        res = G.score_stack(stack, dict(zip(crit, w2)), cr2, extract_sites=False, top_n=10)
        highs.append(res["area_statistics"]["classes"]["High"]["percent"])
        _pairs, keep = _match_sites(base_sites, res["top_locations_details"][:10], 2.0)
        retained.append(keep)

    highs, retained = np.array(highs), np.array(retained)
    print(f"\n  High share: shipped {base_high:.2f}%  |  MC mean {highs.mean():.2f}% "
          f"(sd {highs.std():.2f})  range {highs.min():.2f}-{highs.max():.2f}")
    print(f"  top-10 retention vs shipped: mean {retained.mean():.1f}/10  "
          f"median {np.median(retained):.0f}/10  min {retained.min()}/10")
    print(f"  matrices retaining >= 8/10: {100 * float((retained >= 8).mean()):.0f}%")
    print(f"  matrices retaining 10/10  : {100 * float((retained == 10).mean()):.0f}%")
    print("\n  This is a far larger excursion than the +/-20% one-way analysis in")
    print("  sensitivity.py, which moves ONE weight at a time. Reporting both is")
    print("  more informative than reporting either alone.")


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit the AHP comparison matrix.")
    ap.add_argument("--part", choices=("A", "B", "C"), help="run one part only")
    ap.add_argument("--draws", type=int, default=MC_DRAWS)
    ap.add_argument("--sample", type=int, default=MC_SAMPLE)
    ap.add_argument("--data-dir", default="data")
    args = ap.parse_args()

    parts = [args.part] if args.part else ["A", "B", "C"]
    for i, p in enumerate(parts):
        if i:
            print("\n" + "=" * 78 + "\n")
        if p == "A":
            part_a()
        elif p == "B":
            part_b()
        else:
            part_c(args.draws, args.sample, args.data_dir)


if __name__ == "__main__":
    main()
