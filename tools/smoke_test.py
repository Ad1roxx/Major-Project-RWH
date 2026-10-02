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

    at.sidebar.selectbox[0].select("Baseline (balanced)").run()
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

    print()
    if failures:
        print(f"{len(failures)} failure(s)")
        return 1
    print("all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
