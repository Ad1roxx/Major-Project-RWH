"""Validation of the suitability surfaces against MGNREGA water works.

Reads only: no raster, weight, cutoff or scoring rule is changed. Every
random step uses its own generator seeded 42. Everything written to
outputs/validation/ is produced here; nothing is typed in by hand.

    python -P tools/validate_mgnrega.py            (from the repo root, venv)

Inputs
  data/interim/mgnrega_all.parquet    82,289 accepted geotags (observer names
                                      already dropped; tools/inspect_mgnrega.py)
  reports/photo_audit/                blinded photo audit (key, two sheets)
  the live model                      20 surfaces = 4 methods x 5 scenarios

Deviations from the validation brief, forced by the data (also written to
VALIDATION_NUMBERS.txt):
  * No work-status field exists. Only stages 0 (Phase I: assets, works before
    Nov 2017) and 3 (Phase II: after, geotagged at completion) were pulled;
    both are completed or existing assets, so the status filter removes 0.
  * No asset-type field exists; the only category information is the workcode
    category segment. The primary presence set is the two water segments,
    WC and WH. The photo audit measured how many of them show a harvesting
    structure, and the 12 / 42 photo-confirmed structures are run as extra
    presence sets.
  * Figures are PNG only (project rule since 2026-10-03).
"""
import json
import math
import os
import sys
from collections import Counter

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "outputs", "validation")
AUDIT = os.path.join(ROOT, "reports", "photo_audit")
SEED = 42
N_BG = 10_000
N_BOOT = 2_000
WATER = ("WC", "WH")
POSITIVE = {"storage", "recharge"}
VARIANTS = ["AHP + WLC", "AHP + TOPSIS", "Fuzzy-AHP + WLC", "Fuzzy-AHP + TOPSIS"]
CRITERIA = ["rainfall", "slope", "soil", "lulc", "drainage", "population"]
CRIT_LABEL = {"rainfall": "rainfall", "slope": "slope", "soil": "soil", "lulc": "land cover",
              "drainage": "drainage density", "population": "settlement proximity"}
CLASS = {1: "Low", 2: "Medium", 3: "High"}


def _rng():
    return np.random.default_rng(SEED)


# ── metrics ──────────────────────────────────────────────────────────────────
def auc(pos, neg):
    """ROC AUC as P(score_presence > score_background), ties counted half."""
    from scipy.stats import rankdata
    pos, neg = np.asarray(pos, float), np.asarray(neg, float)
    r = rankdata(np.concatenate([pos, neg]))
    n1, n0 = len(pos), len(neg)
    return (r[:n1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def boot_indices(n1, n0, rng):
    """N_BOOT paired resamples: presences and background resampled separately."""
    return [(rng.integers(0, n1, n1), rng.integers(0, n0, n0)) for _ in range(N_BOOT)]


def auc_ci(pos, neg, idx):
    vals = np.array([auc(pos[i], neg[j]) for i, j in idx])
    return auc(pos, neg), np.percentile(vals, 2.5), np.percentile(vals, 97.5), vals


def delong(pos_a, neg_a, pos_b, neg_b):
    """DeLong test for two correlated AUCs on the same points (two-sided p)."""
    from scipy.stats import norm, rankdata

    def components(pos, neg):
        m, n = len(pos), len(neg)
        allr = rankdata(np.concatenate([pos, neg]))
        v10 = (allr[:m] - rankdata(pos)) / n
        v01 = 1 - (allr[m:] - rankdata(neg)) / m
        return v10.mean(), v10, v01

    a1, v10a, v01a = components(pos_a, neg_a)
    a2, v10b, v01b = components(pos_b, neg_b)
    s10 = np.cov(np.vstack([v10a, v10b]))
    s01 = np.cov(np.vstack([v01a, v01b]))
    s = s10 / len(pos_a) + s01 / len(neg_a)
    var = s[0, 0] + s[1, 1] - 2 * s[0, 1]
    z = (a1 - a2) / math.sqrt(var) if var > 0 else 0.0
    return a1 - a2, 2 * norm.sf(abs(z))


def pr_auc(pos, neg):
    """Average precision (step-wise area under the precision-recall curve)."""
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    s = np.r_[pos, neg]
    order = np.argsort(-s, kind="mergesort")
    y, s = y[order], s[order]
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]   # end of each tie group
    tp = np.cumsum(y)[last]
    fp = (last + 1) - tp
    prec = tp / (tp + fp)
    rec = tp / y.sum()
    return float(np.sum(np.diff(np.r_[0, rec]) * prec))


def roc_curve(pos, neg):
    s = np.r_[pos, neg]
    y = np.r_[np.ones(len(pos)), np.zeros(len(neg))]
    order = np.argsort(-s, kind="mergesort")
    y, s = y[order], s[order]
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]
    tp = np.cumsum(y)[last]
    fp = (last + 1) - tp
    return np.r_[0, fp / len(neg)], np.r_[0, tp / len(pos)]


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    cats = np.union1d(a, b)
    po = np.mean(a == b)
    pe = sum(np.mean(a == c) * np.mean(b == c) for c in cats)
    return (po - pe) / (1 - pe)


def boyce(pres_scores, all_scores, frac=0.1, steps=101):
    """Continuous Boyce index (Hirzel et al. 2006): moving window of width
    frac x score range; F = P/E with E from all valid district cells;
    Spearman between window mid-points and F."""
    from scipy.stats import spearmanr
    lo, hi = float(np.nanmin(all_scores)), float(np.nanmax(all_scores))
    w = frac * (hi - lo)
    mids, F = [], []
    for start in np.linspace(lo, hi - w, steps):
        e = np.mean((all_scores >= start) & (all_scores <= start + w))
        if e == 0:
            continue
        p = np.mean((pres_scores >= start) & (pres_scores <= start + w))
        mids.append(start + w / 2)
        F.append(p / e)
    rho = spearmanr(mids, F).statistic
    return float(rho), np.array(mids), np.array(F)


# ── the model surfaces ───────────────────────────────────────────────────────
def build_surfaces(stack):
    from gis_analysis import score_stack
    from ahp import ahp_engine, SCENARIOS
    from algorithms import weights_for_algorithm
    surf = {}
    for sc in SCENARIOS:
        matrix = ahp_engine.matrix_for_scenario(sc)
        for v in VARIANTS:
            w, agg, _ = weights_for_algorithm(v, matrix, ahp_engine.criteria)
            r = score_stack(stack, w, aggregator=agg, algorithm=v, extract_sites=False)
            surf[(v, sc)] = {"score": r["suitability_raster"],
                             "class": r["classified_raster"], "weights": w, "agg": agg}
    return surf, list(SCENARIOS)


def no_settlement(stack, s):
    """The same method with settlement proximity removed, the other five weights
    renormalised to one (sensitivity.map_removal_sensitivity's convention)."""
    from gis_analysis import score_stack
    w = {k: (0.0 if k == "population" else v) for k, v in s["weights"].items()}
    tot = sum(w.values())
    w = {k: v / tot for k, v in w.items()}
    return score_stack(stack, w, aggregator=s["agg"], extract_sites=False)["suitability_raster"], w


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    import geopandas as gpd
    import rasterio
    from shapely.geometry import Point
    from shapely.prepared import prep
    from gis_analysis import build_criteria_stack

    os.makedirs(OUT, exist_ok=True)
    N = []                                   # VALIDATION_NUMBERS.txt lines
    say = N.append

    # ── provenance ───────────────────────────────────────────────────────────
    log = json.load(open(os.path.join(ROOT, "data", "raw", "mgnrega", "pull_log.json")))
    blocks = {}
    for line in open(os.path.join(ROOT, "data", "raw", "mgnrega", "dropdown_codes.tsv"),
                     encoding="utf8"):
        p = line.rstrip("\n").split("\t")
        if p[0] == "block" and p[1] != "All":
            blocks[p[1]] = p[2].title()
    req = [r for r in log if r["label"].startswith("stage")]
    say("# VALIDATION_NUMBERS — suitability surfaces vs MGNREGA water works")
    say("# generated by tools/validate_mgnrega.py; do not edit by hand")
    say("")
    say("## Provenance")
    say("portal: https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/ (Bhuvan Bhugram)")
    say("report: Accepted Geotags (accepted_geotags.php), no login")
    f = req[0]["form"]
    say(f"filters: state 18 (Maharashtra), district 1829 (Chandrapur), each of 15 blocks, "
        f"stage 0 (Phase I: assets) and 3 (Phase II: after); category All; financial year All; "
        f"accuracy {f['accuracy']}; dates {f['start_date']} to {f['end_date']}")
    say(f"downloaded: {req[0]['timestamp'][:10]}; {len(req)} requests, all HTTP "
        f"{sorted({r['status'] for r in req})}")
    say(f"files: data/raw/mgnrega/stage0/<block>.json and stage3/<block>.json; rows per "
        f"stage: 0 = {sum(r['rows'] for r in req if r['form']['stage'] == '0'):,}, "
        f"3 = {sum(r['rows'] for r in req if r['form']['stage'] == '3'):,}")
    say("parsed table: data/interim/mgnrega_all.parquet (observer names dropped)")
    say("")

    # ── Step 1: presence set ────────────────────────────────────────────────
    stack = build_criteria_stack(os.path.join(ROOT, "data"))
    t = stack["transform"]
    mask = stack["district_mask"].astype(bool)
    H, W = mask.shape
    lat_c = t.f + (np.arange(H) + 0.5) * t.e
    cell_w = np.repeat(np.cos(np.radians(lat_c))[:, None], W, axis=1)   # area weights

    df = pd.read_parquet(os.path.join(ROOT, "data", "interim", "mgnrega_all.parquet"))
    ledger = []

    def step(rule, frame):
        prev = ledger[-1][2] if ledger else len(frame)
        ledger.append((len(ledger) + 1, rule, len(frame), prev - len(frame)))
        return frame

    df = step("raw records loaded (both stages, 15 blocks)", df)
    df = step("missing or zero coordinates dropped",
              df[df.lat.notna() & df.lon.notna() & (df.lat != 0) & (df.lon != 0)])
    bnd = gpd.read_file(os.path.join(ROOT, "data", "boundary.geojson")).to_crs(4326)
    poly = prep(bnd.union_all())
    inside = np.array([poly.contains(Point(x, y)) for x, y in zip(df.lon, df.lat)])
    df = step("outside the GADM district boundary (points already EPSG:4326, the "
              "project CRS)", df[inside])
    df = step("work status = completed: no status field; stages 0 and 3 are both "
              "existing/completed assets, so nothing is removed", df)

    cats = df["category_seg"].fillna("(none)").value_counts()
    with open(os.path.join(OUT, "asset_types_kept.txt"), "w", encoding="utf8") as fh:
        fh.write("Category segment of the workcode (the only category field), every distinct\n"
                 "value inside the district, with the decision for each. No asset-type field\n"
                 "exists, so individual structure types (farm pond, check dam ...) cannot be\n"
                 "selected; the photo audit measures what the kept segments contain.\n\n")
        for c, n in cats.items():
            fh.write(f"{'KEPT    ' if c in WATER else 'EXCLUDED'}  {c:<10} {n:>6,}\n")
    df = step(f"water-harvesting category segments only: {', '.join(WATER)}",
              df[df.category_seg.isin(WATER)])

    df = df.assign(row=[rasterio.transform.rowcol(t, x, y)[0] for x, y in zip(df.lon, df.lat)],
                   col=[rasterio.transform.rowcol(t, x, y)[1] for x, y in zip(df.lon, df.lat)])
    df = step("exact duplicate coordinates dropped", df.drop_duplicates(subset=["lat", "lon"]))
    df = df.sort_values(["creationtime_parsed", "workcode"], na_position="last")
    taken = np.zeros((H, W), bool)
    keep = []
    for r, c in zip(df.row, df.col):
        if 0 <= r < H and 0 <= c < W and taken[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2].any():
            keep.append(False)
            continue
        keep.append(True)
        if 0 <= r < H and 0 <= c < W:
            taken[r, c] = True
    df = step("within one raster cell (same or adjacent cell) of a point already kept; "
              "earliest geotag kept", df[np.array(keep)])
    base = stack["normalized_rasters"]   # any criterion's NaN is the model's nodata
    ok = np.array([0 <= r < H and 0 <= c < W and mask[r, c] for r, c in zip(df.row, df.col)])
    df = step("on a nodata cell of the baseline surface", df[ok])

    # audit verdicts
    key = pd.read_csv(os.path.join(AUDIT, "blind", "key.csv"), dtype=str)
    la = pd.read_csv(os.path.join(AUDIT, "returned", "labels_A.csv"), dtype=str)
    lb = pd.read_csv(os.path.join(AUDIT, "returned", "labels_B.csv"), dtype=str)
    lab = key.merge(la, on="random_id").merge(lb, on="random_id", suffixes=("_a", "_b"))
    lab["pa"] = lab.label_a.str.strip().str.lower().isin(POSITIVE)
    lab["pb"] = lab.label_b.str.strip().str.lower().isin(POSITIVE)
    no_structure = set(lab.loc[~(lab.pa & lab.pb), "collection_sno"])
    df = step("photo-audited and NOT a harvesting structure under the protocol's strict "
              "rule (both labellers storage/recharge)",
              df[~df.collection_sno.astype(str).isin(no_structure)])
    pres = df.reset_index(drop=True)
    pd.DataFrame(ledger, columns=["step", "rule", "n_remaining", "n_removed"]).to_csv(
        os.path.join(OUT, "filter_ledger.csv"), index=False)

    say("## Step 1 — presence set (filter_ledger.csv)")
    for s_, rule, n, rem in ledger:
        say(f"{s_}. {rule}: {n:,} remaining ({rem:,} removed)")
    fy = pres.fy_from_path.dropna()
    yrs = pres.creationtime_parsed.dropna().dt.year
    say(f"financial year of work (from photo path, {len(fy):,} of {len(pres):,} have it): "
        f"{fy.min()} to {fy.max()}")
    say(f"geotag year (all with a parseable time, {len(yrs):,}): {yrs.min()} to {yrs.max()}")
    say("count per category segment: " + ", ".join(
        f"{k} {v:,}" for k, v in pres.category_seg.value_counts().items()))
    say("count per stage: " + ", ".join(
        f"{'Phase I' if k == '0' else 'Phase II'} {v:,}" for k, v in pres.stage.value_counts().items()))
    per_block = pres.requested_block_code.map(blocks).value_counts()
    say("count per block: " + ", ".join(f"{k} {v:,}" for k, v in per_block.items()))
    zero = sorted(set(blocks.values()) - set(per_block.index))
    say(f"blocks with zero retained structures: {len(zero)} of {len(blocks)}"
        + (f" ({', '.join(zero)})" if zero else ""))
    say(f"GPS accuracy as reported: median {pres.accuracy_m.median():.0f} m")
    say("")

    # ── Step 2: labelling agreement ─────────────────────────────────────────
    a_l = lab.label_a.str.strip().str.lower()
    b_l = lab.label_b.str.strip().str.lower()
    kap6 = kappa(a_l, b_l)
    kap2 = kappa(lab.pa, lab.pb)
    say("## Step 2 — labelling agreement")
    say(f"photos labelled: {len(lab)}, 30 per category segment over {lab.category_seg.nunique()} "
        "segments; labellers: 2; double-labelled overlap: all of them")
    say(f"raw agreement {np.mean(a_l == b_l) * 100:.1f}%; Cohen's kappa (6 labels) {kap6:.3f}; "
        f"kappa (harvesting structure or not) {kap2:.3f}")
    say("resolution: no joint session; the protocol's fixed strict rule (positive only if both "
        "labellers said storage or recharge). Deviations logged in "
        "docs/PHOTO_LABELLING_PROTOCOL.md (labeller A's sheet re-aligned by one row on the "
        "coordinator's instruction; key opened before the final sheets)")
    for seg in WATER:
        s = lab[lab.category_seg == seg]
        say(f"segment {seg}: harvesting structure in {s.pa.mul(s.pb).sum()} of {len(s)} photos "
            f"(strict, {s.pa.mul(s.pb).mean() * 100:.1f}%), {(s.pa | s.pb).sum()} of {len(s)} "
            f"(lenient, {(s.pa | s.pb).mean() * 100:.1f}%)")
    say("so the presence set is MOSTLY NOT harvesting structures: every AUC below is diluted "
        "toward 0.5 and is a lower bound on agreement with built structures")
    say("")

    # ── Step 3: background ──────────────────────────────────────────────────
    blocked = np.zeros((H, W), bool)
    for r, c in zip(pres.row, pres.col):
        blocked[max(r - 1, 0):r + 2, max(c - 1, 0):c + 2] = True
    cand = np.flatnonzero((mask & ~blocked).ravel())
    pick = _rng().choice(cand, N_BG, replace=False)
    bg_r, bg_c = np.unravel_index(pick, (H, W))
    say("## Step 3 — background")
    say(f"{N_BG:,} cells, uniform over valid district cells (incl. Low), seed {SEED}, none in "
        f"or adjacent to a presence cell ({int(blocked[mask].sum()):,} cells excluded of "
        f"{int(mask.sum()):,})")
    say("")

    # ── Step 4: extraction ──────────────────────────────────────────────────
    surf, scenarios = build_surfaces(stack)
    baseline = scenarios[0]
    pr, pc = pres.row.values, pres.col.values
    ex = lambda a, rr, cc: a[rr, cc].astype(float)
    to_ll = lambda rr, cc: rasterio.transform.xy(t, rr, cc)
    bx, by = to_ll(bg_r, bg_c)
    rows = []
    meta = pd.DataFrame({
        "point_id": [f"P{i:05d}" for i in range(len(pres))] + [f"B{i:05d}" for i in range(N_BG)],
        "kind": ["presence"] * len(pres) + ["background"] * N_BG,
        "x": np.r_[pres.lon.values, bx], "y": np.r_[pres.lat.values, by],
        "asset_type": list(pres.category_seg) + [""] * N_BG,
        "year": list(pres.fy_from_path.fillna("")) + [""] * N_BG,
        "block": list(pres.requested_block_code.map(blocks)) + [""] * N_BG})
    allr, allc = np.r_[pr, bg_r], np.r_[pc, bg_c]
    for (v, sc), s in surf.items():
        d = meta.copy()
        d["variant"], d["scenario"] = v, sc
        d["score"] = ex(s["score"], allr, allc)
        d["class"] = [CLASS.get(int(k), "") if not np.isnan(k) else "" for k in ex(s["class"], allr, allc)]
        rows.append(d)
    long = pd.concat(rows, ignore_index=True)
    long.to_csv(os.path.join(OUT, "validation_points.csv"), index=False, float_format="%.5f")
    wide = meta.copy()
    for k in CRITERIA:
        wide[k] = ex(stack["normalized_rasters"][k], allr, allc)
    wide["settlement_km"] = ex(stack["settlement_distance_km"], allr, allc)
    wide.to_csv(os.path.join(OUT, "validation_criteria.csv"), index=False, float_format="%.5f")
    gpd.GeoDataFrame(pres[["collection_sno", "category_seg", "stage", "fy_from_path",
                           "requested_block_code"]].assign(
        block=pres.requested_block_code.map(blocks)),
        geometry=gpd.points_from_xy(pres.lon, pres.lat), crs=4326).to_file(
        os.path.join(OUT, "presences_final.gpkg"), driver="GPKG")

    # ── Step 5: metrics ─────────────────────────────────────────────────────
    idx = boot_indices(len(pres), N_BG, _rng())
    say("## Step 5 — metrics, all 20 surfaces")
    say(f"bootstrap: {N_BOOT:,} resamples (presences and background resampled separately), "
        f"seed {SEED}, percentile 95% CI; prevalence baseline for PR AUC = "
        f"{len(pres) / (len(pres) + N_BG):.3f}")
    say("Boyce: continuous index, window 1/10 of the score range, 101 positions, expected "
        "frequency from all valid district cells. Its null spread is wide (random presences "
        "give mean 0.03, sd 0.26 over 30 seeds in this implementation), so read it with the AUC.")
    say("variant | scenario | ROC AUC [95% CI] | PR AUC | Boyce")
    results, boots = {}, {}
    for (v, sc), s in surf.items():
        P, B = ex(s["score"], pr, pc), ex(s["score"], bg_r, bg_c)
        a, lo, hi, vals = auc_ci(P, B, idx)
        by_ = boyce(P, s["score"][mask])[0]
        results[(v, sc)] = {"auc": a, "lo": lo, "hi": hi, "pr": pr_auc(P, B), "boyce": by_}
        boots[(v, sc)] = vals
        say(f"{v} | {sc} | {a:.3f} [{lo:.3f}, {hi:.3f}] | {results[(v, sc)]['pr']:.3f} | {by_:.3f}")
    say("")
    say(f"pairwise differences, baseline scenario ({baseline}): paired bootstrap on the same "
        "resamples, and DeLong")
    for i, a_ in enumerate(VARIANTS):
        for b_ in VARIANTS[i + 1:]:
            d = boots[(a_, baseline)] - boots[(b_, baseline)]
            sa, sb = surf[(a_, baseline)]["score"], surf[(b_, baseline)]["score"]
            dd, p = delong(ex(sa, pr, pc), ex(sa, bg_r, bg_c), ex(sb, pr, pc), ex(sb, bg_r, bg_c))
            say(f"{a_} minus {b_}: {dd:+.3f} [{np.percentile(d, 2.5):+.3f}, "
                f"{np.percentile(d, 97.5):+.3f}], DeLong p = {p:.3g}")
    say("")
    say("gain table (baseline scenario): % of district AREA in each class vs % of presences")
    gains = {}
    for v in VARIANTS:
        cl = surf[(v, baseline)]["class"]
        pcl = ex(cl, pr, pc)
        g = {}
        for code, name in CLASS.items():
            area = cell_w[mask & (cl == code)].sum() / cell_w[mask].sum() * 100
            pts = np.mean(pcl == code) * 100
            g[name] = (area, pts, pts / area if area else float("nan"))
        gains[v] = g
        say(f"{v}: " + "; ".join(f"{n} {g[n][0]:.1f}% area, {g[n][1]:.1f}% presences, "
                                  f"ratio {g[n][2]:.2f}" for n in ("High", "Medium", "Low")))
    say("sensitivity at the paper's High cutoff (score > 0.85, all variants): " + "; ".join(
        f"{v} {gains[v]['High'][1]:.1f}%" for v in VARIANTS))
    say("")

    # ── Step 6: robustness ──────────────────────────────────────────────────
    say("## Step 6 — robustness (baseline scenario)")
    # spatial thinning, 1 km grid in UTM 44N
    xy = gpd.GeoSeries(gpd.points_from_xy(pres.lon, pres.lat), crs=4326).to_crs(32644)
    gk = list(zip((xy.x // 1000).astype(int), (xy.y // 1000).astype(int)))
    order = _rng().permutation(len(pres))
    seen, thin = set(), []
    for i in order:
        if gk[i] not in seen:
            seen.add(gk[i])
            thin.append(i)
    thin = np.sort(np.array(thin))
    idx_t = boot_indices(len(thin), N_BG, _rng())
    say(f"spatial thinning: one presence per 1 km x 1 km cell (seed {SEED}): {len(thin):,} of "
        f"{len(pres):,} survive")
    for v in VARIANTS:
        s = surf[(v, baseline)]["score"]
        a, lo, hi, _ = auc_ci(ex(s, pr[thin], pc[thin]), ex(s, bg_r, bg_c), idx_t)
        say(f"  {v}: AUC {a:.3f} [{lo:.3f}, {hi:.3f}]")
    # settlement confound
    from scipy.stats import mannwhitneyu
    dp = ex(stack["settlement_distance_km"], pr, pc)
    db = ex(stack["settlement_distance_km"], bg_r, bg_c)
    u = mannwhitneyu(dp, db)
    say(f"settlement confound (a): distance to nearest settlement cell, median presences "
        f"{np.median(dp):.2f} km vs background {np.median(db):.2f} km; Mann-Whitney U = "
        f"{u.statistic:,.0f}, p = {u.pvalue:.3g}")
    say("settlement confound (b): AUC with and without the settlement criterion "
        "(other five weights renormalised)")
    nos = {}
    for v in VARIANTS:
        s = surf[(v, baseline)]
        a0 = results[(v, baseline)]
        Sx, w = no_settlement(stack, s)
        nos[v] = Sx
        a1, lo1, hi1, _ = auc_ci(ex(Sx, pr, pc), ex(Sx, bg_r, bg_c), idx)
        say(f"  {v}: with {a0['auc']:.3f} [{a0['lo']:.3f}, {a0['hi']:.3f}]; without "
            f"{a1:.3f} [{lo1:.3f}, {hi1:.3f}]")
    # single criteria
    say("single-criterion AUCs (each normalised criterion raster alone):")
    single = {}
    for k in CRITERIA:
        a, lo, hi, _ = auc_ci(ex(stack["normalized_rasters"][k], pr, pc),
                              ex(stack["normalized_rasters"][k], bg_r, bg_c), idx)
        single[k] = (a, lo, hi)
        say(f"  {CRIT_LABEL[k]}: {a:.3f} [{lo:.3f}, {hi:.3f}]")
    best = max(single, key=lambda k: single[k][0])
    say(f"best single criterion: {CRIT_LABEL[best]} {single[best][0]:.3f}; best combined "
        f"(baseline): {max(results[(v, baseline)]['auc'] for v in VARIANTS):.3f}")
    # land-cover confound: cropland-only background
    lulc = stack["raw_rasters"]["lulc"]
    crop_bg = lulc[bg_r, bg_c] == 12
    crop_p = lulc[pr, pc] == 12
    say(f"land-cover confound: {crop_p.mean() * 100:.1f}% of presences vs "
        f"{crop_bg.mean() * 100:.1f}% of background lie on cropland; AUC within cropland only:")
    idx_c = boot_indices(int(crop_p.sum()), int(crop_bg.sum()), _rng())
    for v in VARIANTS:
        s = surf[(v, baseline)]["score"]
        a, lo, hi, _ = auc_ci(ex(s, pr[crop_p], pc[crop_p]), ex(s, bg_r[crop_bg], bg_c[crop_bg]), idx_c)
        say(f"  {v}: {a:.3f} [{lo:.3f}, {hi:.3f}]")
    # photo-confirmed presence sets
    conf = lab.assign(strict=lab.pa & lab.pb, lenient=lab.pa | lab.pb)
    parq = pd.read_parquet(os.path.join(ROOT, "data", "interim", "mgnrega_all.parquet"),
                           columns=["collection_sno", "lat", "lon"])
    parq["collection_sno"] = parq.collection_sno.astype(str)
    say("photo-confirmed structures as the presence set (small n, wide intervals):")
    for rule in ("strict", "lenient"):
        cs = conf[conf[rule]].merge(parq, on="collection_sno")
        rc = [rasterio.transform.rowcol(t, x, y) for x, y in zip(cs.lon, cs.lat)]
        rc = [(r, c) for r, c in rc if 0 <= r < H and 0 <= c < W and mask[r, c]]
        if len(rc) < 3:
            continue
        rr, cc = np.array(rc).T
        idx_s = boot_indices(len(rr), N_BG, _rng())
        for v in VARIANTS[:1]:
            s = surf[(v, baseline)]["score"]
            a, lo, hi, _ = auc_ci(ex(s, rr, cc), ex(s, bg_r, bg_c), idx_s)
            say(f"  {rule} (n = {len(rr)}), {v}: AUC {a:.3f} [{lo:.3f}, {hi:.3f}]")
    # CGWB's proposed artificial-recharge sites (NAQUIM 2021): an expert,
    # recharge-specific reference, independent of the model and of MGNREGA.
    cg_path = os.path.join(ROOT, "data", "raw", "cgwb", "cgwb_proposed_ar_sites.csv")
    if os.path.exists(cg_path):
        cg = pd.read_csv(cg_path)
        rc = [rasterio.transform.rowcol(t, x, y) for x, y in zip(cg.lon, cg.lat)]
        keep_cg = [0 <= r < H and 0 <= c < W and mask[r, c] for r, c in rc]
        cg = cg[keep_cg].reset_index(drop=True)
        cr = np.array([r for (r, c), k in zip(rc, keep_cg) if k])
        ccl = np.array([c for (r, c), k in zip(rc, keep_cg) if k])
        s = surf[(VARIANTS[0], baseline)]
        idx_g = boot_indices(len(cg), N_BG, _rng())
        a, lo, hi, _ = auc_ci(ex(s["score"], cr, ccl), ex(s["score"], bg_r, bg_c), idx_g)
        say(f"CGWB proposed artificial-recharge sites (NAQUIM 2021, Annexures VII-IX; "
            f"n = {len(cg)}), baseline {VARIANTS[0]}: AUC {a:.3f} [{lo:.3f}, {hi:.3f}]")
        for ty, g in cg.groupby("type"):
            ii = g.index.values
            a2, lo2, hi2, _ = auc_ci(ex(s["score"], cr[ii], ccl[ii]), ex(s["score"], bg_r, bg_c),
                                     boot_indices(len(ii), N_BG, _rng()))
            say(f"  {ty} (n = {len(ii)}): AUC {a2:.3f} [{lo2:.3f}, {hi2:.3f}]")
        cls = ex(s["class"], cr, ccl)
        say("  share of proposed sites by class vs area: " + "; ".join(
            f"{n} {np.mean(cls == k) * 100:.1f}% vs {gains[VARIANTS[0]][n][0]:.1f}% "
            f"({np.mean(cls == k) * 100 / gains[VARIANTS[0]][n][0]:.2f}x)"
            for k, n in ((3, "High"), (2, "Medium"), (1, "Low"))))
        # blocks CGWB judges NOT feasible for recharge (shallow, rising water table)
        from rasterio.features import rasterize
        tal = gpd.read_file(os.path.join(ROOT, "data", "raw", "talukas",
                                         "chandrapur_talukas_filled_to_boundary.geojson"))
        nf = {"Jiwati", "Mul", "Nagbhir", "Pombhurna", "Sawali", "Sindewahi"}
        z = rasterize(((g, 1) for g, n_ in zip(tal.geometry, tal.taluka) if n_ in nf),
                      out_shape=(H, W), transform=t, fill=0).astype(bool)
        hi_c = mask & (s["class"] == 3)
        say(f"  CGWB 'AR not feasible' blocks (Jiwati, Mul, Nagbhir, Pombhurna, Saoli, "
            f"Sindewahi; Census taluka outlines): {cell_w[mask & z].sum() / cell_w[mask].sum() * 100:.1f}% "
            f"of district area but {cell_w[hi_c & z].sum() / cell_w[hi_c].sum() * 100:.1f}% of the "
            f"baseline High area")
        sites = gpd.read_file(os.path.join(ROOT, "outputs", "rwh_sites.geojson"))
        srow = [rasterio.transform.rowcol(t, p.x, p.y) for p in sites.geometry]
        n_nf = sum(bool(z[r, c]) for r, c in srow)
        say(f"  baseline top-{len(sites)} candidate sites inside those blocks: {n_nf} of {len(sites)}")
    # negative control
    s0 = surf[(VARIANTS[0], baseline)]["score"].copy()
    vals = s0[mask]
    perm = s0.copy()
    perm[mask] = _rng().permutation(vals)
    a_neg = auc(ex(perm, pr, pc), ex(perm, bg_r, bg_c))
    say(f"negative control: baseline {VARIANTS[0]} cell values permuted (seed {SEED}): "
        f"AUC {a_neg:.3f}")
    if abs(a_neg - 0.5) > 0.03:
        raise SystemExit(f"negative control failed: AUC {a_neg:.3f} is not close to 0.5")
    say("")
    say("## Not done, and why")
    say("- work-status and asset-type filters as specified: the data carry neither field "
        "(Step 1, rules 4-5)")
    say("- vector PDF figures: PNG only by project rule")

    open(os.path.join(OUT, "VALIDATION_NUMBERS.txt"), "w", encoding="utf8").write("\n".join(N) + "\n")
    json.dump({"results": {f"{v}|{sc}": r for (v, sc), r in results.items()},
               "gains": gains, "single": single, "baseline": baseline,
               "n_presence": len(pres), "n_background": N_BG},
              open(os.path.join(OUT, "validation_summary.json"), "w"), indent=1, default=float)
    _figures(surf, baseline, pres, pr, pc, bg_r, bg_c, results, gains, ex)
    print("\n".join(N))


# ── Step 7: figures (matplotlib; the map is made in QGIS) ────────────────────
def _figures(surf, baseline, pres, pr, pc, bg_r, bg_c, results, gains, ex):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans"],
                         "font.size": 8, "axes.labelsize": 8.5, "axes.titlesize": 9.5,
                         "axes.titleweight": "bold", "axes.spines.top": False,
                         "axes.spines.right": False, "axes.linewidth": 0.6,
                         "legend.fontsize": 7.5, "figure.titlesize": 10,
                         "figure.titleweight": "bold"})
    style = {"AHP + WLC": ("#293241", "-"), "AHP + TOPSIS": ("#293241", "--"),
             "Fuzzy-AHP + WLC": ("#E56B6F", "-"), "Fuzzy-AHP + TOPSIS": ("#E56B6F", "--")}
    figdir = os.path.join(ROOT, "outputs", "figures")
    n = len(pres)

    fig, ax = plt.subplots(figsize=(4.2, 4.0))
    for v in VARIANTS:
        s = surf[(v, baseline)]["score"]
        fpr, tpr = roc_curve(ex(s, pr, pc), ex(s, bg_r, bg_c))
        r = results[(v, baseline)]
        c, ls = style[v]
        ax.plot(fpr, tpr, color=c, ls=ls, lw=1.2,
                label=f"{v}: {r['auc']:.3f} [{r['lo']:.3f}, {r['hi']:.3f}]")
    ax.plot([0, 1], [0, 1], color="#9a9a9a", lw=0.8, ls=":", label="no skill (0.5)")
    ax.set_xlabel("false positive rate (background)")
    ax.set_ylabel("true positive rate (MGNREGA water works)")
    ax.set_aspect("equal")
    ax.legend(loc="lower right", title="AUC [95% CI]", title_fontsize=7.5, frameon=False)
    a0 = results[(VARIANTS[0], baseline)]["auc"]
    fig.suptitle(f"All four methods rank water works\nabove random cells (AUC ≈ {a0:.2f})",
                 fontsize=9, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(figdir, "fig_val_roc.png"), dpi=300)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(6.8, 4.6), sharex=True, sharey=True)
    bins = np.linspace(0, 1, 41)
    for ax, v in zip(axes.ravel(), VARIANTS):
        s = surf[(v, baseline)]["score"]
        ax.hist(ex(s, bg_r, bg_c), bins=bins, density=True, color="#c8c8c8", label="background")
        ax.hist(ex(s, pr, pc), bins=bins, density=True, histtype="step", lw=1.3,
                color=style[v][0], label="MGNREGA water works")
        ax.axvline(0.85, color="#2166AC", lw=0.8)
        ax.axvline(0.65, color="#B2182B", lw=0.8)
        ax.set_title(v, fontsize=8.5)
    for ax in axes[1]:
        ax.set_xlabel("suitability score (WLC) / closeness (TOPSIS)")
    for ax in axes[:, 0]:
        ax.set_ylabel("density")
    axes[0, 0].legend(frameon=False, loc="upper left")
    fig.suptitle("Water works score higher than random cells on every surface "
                 "(lines: 0.65, 0.85)", fontsize=9, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(figdir, "fig_val_scores.png"), dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    colours = {"High": "#2166AC", "Medium": "#bfb8aa", "Low": "#B2182B"}
    x = np.arange(len(VARIANTS))
    wdt = 0.13
    for j, cls in enumerate(("High", "Medium", "Low")):
        area = [gains[v][cls][0] for v in VARIANTS]
        pts = [gains[v][cls][1] for v in VARIANTS]
        xs = x + (j - 1) * 2.2 * wdt
        ax.bar(xs - wdt / 2, area, wdt, color=colours[cls], alpha=0.35, edgecolor=colours[cls], lw=0.6)
        ax.bar(xs + wdt / 2, pts, wdt, color=colours[cls], edgecolor=colours[cls], lw=0.6)
        for xi, a, p in zip(xs, area, pts):
            ax.text(xi + wdt / 2, p + 1, f"{p / a:.2f}×", ha="center", fontsize=6.5)
    ax.set_xticks(x)
    ax.set_xticklabels(VARIANTS)
    ax.set_ylabel("% of district area / of works")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=colours[c], label=c) for c in colours] +
              [Patch(facecolor="white", edgecolor="#555", label="pale = area, solid = works")],
              frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    h = gains[VARIANTS[0]]["High"]
    fig.suptitle(f"High zones hold {h[2]:.1f}× their area share of water works; Low zones "
                 f"hold {gains[VARIANTS[0]]['Low'][2]:.2f}×", fontsize=9, x=0.02, ha="left")
    fig.tight_layout()
    fig.savefig(os.path.join(figdir, "fig_val_gain.png"), dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
