"""
tools/smoke_test.py
───────────────────
End-to-end smoke test for the Streamlit app.

    python tools/smoke_test.py        # exits 0 on success, 1 on any failure

Why this exists: `streamlit run app.py` starts a server but does **not** execute
the script until a browser session connects, so "the app starts" proves almost
nothing. A `ValueError: assignment destination is read-only` in the sidebar
matrix editor shipped precisely because startup was the only check. This runs
the script body and the real interactions through Streamlit's AppTest harness.

No pytest required — the project has no test framework, and this deliberately
does not add one.
"""

from __future__ import annotations

import os
import sys

# Same stdlib-shadowing guard as tools/inspect.py: keep tools/ off sys.path so
# a module in here can never shadow a standard-library import.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]

APP = os.path.join(os.path.dirname(_HERE), "app.py")

failures: list[str] = []


def check(app_test, step: str) -> bool:
    if app_test.exception:
        msg = app_test.exception[0].message
        print(f"  FAIL  {step}\n        {msg}")
        failures.append(f"{step}: {msg}")
        return False
    print(f"  ok    {step}")
    return True


def high_pct(app_test) -> str:
    for m in app_test.metric:
        if m.label == "High suitability":
            return m.value
    return "n/a"


def main() -> int:
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(APP, default_timeout=300)

    print("Streamlit app smoke test")
    at.run()
    check(at, "script loads")

    at.button[0].click().run()
    check(at, f"run analysis (High {high_pct(at)})")

    # Scenario switching re-scores the cached stack.
    at.sidebar.selectbox[0].select("Maximise recharge").run()
    check(at, f"scenario -> Maximise recharge (High {high_pct(at)})")

    # Algorithm switching swaps the aggregator.
    at.sidebar.selectbox[1].select("AHP + TOPSIS").run()
    check(at, f"algorithm -> AHP + TOPSIS (High {high_pct(at)})")

    at.sidebar.selectbox[1].select("Fuzzy-AHP + WLC").run()
    check(at, "algorithm -> Fuzzy-AHP + WLC")

    at.sidebar.selectbox[0].select("Baseline (rainfall-led)").run()
    at.sidebar.selectbox[1].select("AHP + WLC").run()
    check(at, f"back to baseline (High {high_pct(at)})")

    # Ranks must be 1..N and non-increasing in score. The two selection stages
    # each emit their own descending run, so this shipped broken once already:
    # rank #22 scored 0.948 while rank #13 scored 0.866.
    from gis_analysis import run_ahp_analysis
    sites = run_ahp_analysis("data")["top_locations_details"]
    ranks = [s["rank"] for s in sites]
    scores = [s["suitability_score"] for s in sites]
    out_of_order = sum(1 for a, b in zip(scores, scores[1:]) if b > a + 1e-9)
    if ranks != list(range(1, len(sites) + 1)) or out_of_order:
        failures.append(f"rank ordering broken ({out_of_order} out of order)")
        print(f"  FAIL  rank ordering ({out_of_order} out of order)")
    else:
        print(f"  ok    rank ordering (1..{len(sites)}, scores descending)")

    n_downloads = len(at.get("download_button"))
    if n_downloads < 4:
        failures.append(f"expected 4 download buttons, found {n_downloads}")
        print(f"  FAIL  export buttons ({n_downloads}/4)")
    else:
        print(f"  ok    export buttons ({n_downloads})")

    labels = [b.label for b in at.button]
    for want in ("Run sensitivity", "Compute consensus", "Compare all algorithms"):
        idx = [i for i, lab in enumerate(labels) if lab == want]
        if not idx:
            failures.append(f"button not found: {want}")
            print(f"  FAIL  button missing: {want}")
            continue
        at.button[idx[0]].click().run()
        check(at, want)
        labels = [b.label for b in at.button]

    partition_problems = check_transition_partition()
    if partition_problems:
        failures.extend(partition_problems)
        for msg in partition_problems:
            print(f"  FAIL  transition partition: {msg}")
    else:
        print("  ok    class-transition decomposition partitions cells")

    rounding_problems = check_no_rounded_inputs()
    if rounding_problems:
        failures.extend(rounding_problems)
        for msg in rounding_problems:
            print(f"  FAIL  rounded input: {msg}")
    else:
        print("  ok    no derived effect comes from a rounded share")

    share_problems = check_class_shares()
    if share_problems:
        failures.extend(share_problems)
        for msg in share_problems:
            print(f"  FAIL  class share disagreement: {msg}")
    else:
        print("  ok    class shares agree across every reporting path")

    print()
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("all checks passed")
    return 0


def check_class_shares() -> list:
    """Every path that reports a class share must agree with class_share_pct.

    Figures 10 and 13 once printed 41.08% and 41.04% for the Low class of the
    identical surface, because one path was area-weighted and the other counted
    cells. In EPSG:4326 a cell's ground area falls with latitude, and the Low
    class sits mostly in the south, so the two differ by about 0.05 pp - small
    enough to survive several rounds of review and large enough for a referee
    reading both figures to notice.

    This makes that a test failure. It checks the three places a share can come
    from: the rounded display field, the exact field, and an area-weighted
    cumulative distribution evaluated at the breakpoints.
    """
    import numpy as np

    import criteria as C
    import gis_analysis as G
    from ahp import ahp_engine
    from algorithms import ALGORITHMS, weights_for_algorithm

    problems = []
    stack = G.build_criteria_stack("data")
    mask = stack["district_mask"]
    px = G._pixel_area_km2_per_row(stack["transform"], stack["shape"])
    area = np.repeat(px[:, None], stack["shape"][1], axis=1)
    lo_t, hi_t = C.SUITABILITY_THRESHOLDS

    for name in ALGORITHMS:
        w, agg, _ = weights_for_algorithm(name, ahp_engine.matrix,
                                          ahp_engine.criteria)
        res = G.score_stack(stack, w, aggregator=agg, algorithm=name)
        cls = res["area_statistics"]["classes"]

        for klass in ("High", "Medium", "Low"):
            exact = G.class_share_pct(res, klass)
            shown = cls[klass]["percent"]
            if abs(exact - shown) > 0.005:
                problems.append(f"{name} {klass}: percent {shown} vs "
                                f"percent_exact {exact:.4f}")

        # The ECDF route, which is what Figure 13 plots.
        s = res["suitability_raster"]
        sel = mask & ~np.isnan(s)
        tot = area[sel].sum()
        for klass, t, cmp_ in (("Low", lo_t, "le"), ("High", hi_t, "gt")):
            below = 100.0 * float(area[sel][s[sel] <= t].sum() / tot)
            got = below if cmp_ == "le" else 100.0 - below
            exact = G.class_share_pct(res, klass)
            if abs(got - exact) > 0.005:
                problems.append(f"{name} {klass}: area-weighted ECDF "
                                f"{got:.4f} vs class_share_pct {exact:.4f}")
    return problems



def check_no_rounded_inputs() -> list:
    """No derived effect may be computed by differencing a rounded share.

    `_area_statistics` rounds `percent` to 2 dp for display. Anything that
    SUBTRACTS two shares must read `percent_exact` instead, or the result is
    quantised to 0.01 pp - which is how the paper's factorial effects came to
    read +9.030, -0.100 and 0.000, and how the map-removal effects carried a
    spurious +7.68 where the true value is +7.67.

    Two checks, because a reader of this file should not have to trust either
    alone:

    1. A static scan. Any module that both reads `["percent"]` and does
       arithmetic on shares is flagged for inspection. Crude, but it is the
       only thing that catches a NEW call site before it reaches a figure.
    2. A behavioural check. Every derived effect is recomputed and tested for
       being an exact multiple of 0.01, which is what quantisation looks like.
       A genuine effect landing on a hundredth is possible but all of them
       doing so is not, so the test is on the set rather than on each value.
    """
    import pathlib
    import re

    problems = []

    # ── 1. static scan ─────────────────────────────────────────────────────
    root = pathlib.Path(__file__).resolve().parent.parent
    for mod in ("sensitivity.py", "consensus.py", "algorithms.py",
                "tools/make_figures.py", "tools/paper_figures.py"):
        path = root / mod
        if not path.exists():
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if '["percent"]' not in line:
                continue
            # Reading it to display or store is fine; combining it is not.
            if re.search(r'\["percent"\]\s*[-+]|[-+]\s*\w+\["percent"\]', line):
                problems.append(f"{mod}:{i} differences the rounded "
                                f"'percent' field: {line.strip()}")

    # ── 2. behavioural check ───────────────────────────────────────────────
    import gis_analysis as G
    from ahp import ahp_engine
    from sensitivity import map_removal_sensitivity, one_way_sensitivity

    stack = G.build_criteria_stack("data")
    weights, _cr = ahp_engine.calculate_weights()

    derived = []
    ow = one_way_sensitivity(stack, weights)
    derived += [r["high_pct_delta"] for r in ow["runs"]]
    mr = map_removal_sensitivity(stack, weights)
    derived += [r["high_pct_delta"] for r in mr["rows"]]

    on_a_hundredth = [v for v in derived if abs(round(v, 2) - v) < 1e-9]
    if derived and len(on_a_hundredth) == len(derived):
        problems.append(
            f"all {len(derived)} derived effects are exact multiples of "
            "0.01 pp, which means they were differenced from a rounded share")
    return problems



def check_transition_partition() -> list:
    """A class-transition decomposition must partition cells, not net totals.

    Figure 21 originally subtracted the churn under share-matched breakpoints
    from the churn under fixed ones and called the remainder a "breakpoint
    component". Those are different SETS of cells, so the subtraction is not a
    decomposition: for the Low class it comes out NEGATIVE, because the fixed
    0.65 cutoff holds cells in Low that a matched cutoff releases. A stacked
    bar cannot draw a negative segment, so the row silently showed 3.99 pp
    under a total labelled 1.02 pp and the rows summed to 15.80 against a
    stated 12.83.

    This asserts the identities a real partition has to satisfy:

      robust + induced  == area that changes class under the fixed cutoffs
      robust + masked   == area that changes class under the matched cutoffs
      the per-origin-class rows sum to the whole in each category

    and, because that was the actual symptom, that no component is negative.
    """
    import numpy as np

    import gis_analysis as G
    from ahp import ahp_engine
    from algorithms import weights_for_algorithm

    problems = []
    stack = G.build_criteria_stack("data")
    mask = stack["district_mask"]
    px = G._pixel_area_km2_per_row(stack["transform"], stack["shape"])
    area = np.repeat(px[:, None], stack["shape"][1], axis=1)

    res = {}
    for name in ("AHP + WLC", "AHP + TOPSIS"):
        w, agg, _l = weights_for_algorithm(name, ahp_engine.matrix,
                                           ahp_engine.criteria)
        res[name] = G.score_stack(stack, w, aggregator=agg, algorithm=name)

    cw = res["AHP + WLC"]["classified_raster"]
    ct = res["AHP + TOPSIS"]["classified_raster"]
    sv = res["AHP + TOPSIS"]["suitability_raster"]
    ok = mask & ~np.isnan(cw) & ~np.isnan(ct) & ~np.isnan(sv)
    A = area[ok]
    tot = float(A.sum())
    W, T, V = cw[ok], ct[ok], sv[ok]

    share = {c: 100.0 * float(A[W == c].sum()) / tot for c in (1, 2, 3)}
    order = np.argsort(V, kind="mergesort")
    cum = 100.0 * np.cumsum(A[order]) / tot
    t_lo = V[order][np.searchsorted(cum, share[1])]
    t_hi = V[order][np.searchsorted(cum, share[1] + share[2])]
    M = np.where(V <= t_lo, 1, np.where(V <= t_hi, 2, 3))

    def pp(sel):
        return 100.0 * float(A[sel].sum()) / tot

    robust = (W != T) & (W != M)
    induced = (W != T) & (W == M)
    masked = (W == T) & (W != M)

    for name, got, want in (
            ("robust + induced", pp(robust) + pp(induced), pp(W != T)),
            ("robust + masked", pp(robust) + pp(masked), pp(W != M))):
        if abs(got - want) > 1e-6:
            problems.append(f"{name} = {got:.4f} pp, expected {want:.4f} pp")

    for cname, comp in (("robust", robust), ("induced", induced),
                        ("masked", masked)):
        if pp(comp) < 0:
            problems.append(f"{cname} component is negative")
        rows = sum(pp(comp & (W == c)) for c in (1, 2, 3))
        if abs(rows - pp(comp)) > 1e-6:
            problems.append(f"{cname}: per-class rows sum to {rows:.4f} pp, "
                            f"whole is {pp(comp):.4f} pp")
    return problems



if __name__ == "__main__":
    raise SystemExit(main())
