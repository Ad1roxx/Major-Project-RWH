"""
tools/paper_figures.py
──────────────────────
Every number and figure dataset cited in the research paper, reproducible from
the repository.

    python tools/paper_figures.py                 # all sections
    python tools/paper_figures.py --section 9     # one section
    python tools/paper_figures.py --csv-dir outputs/paper   # also write CSVs

Why this file exists
    The paper claims reproducibility as a contribution. Numbers that live only
    in a chat transcript contradict that claim. Every figure in the paper's
    results and every figure caption should trace to a section below, and every
    section is a function that can be re-run.

Section numbering matches docs/PAPER_DATA_HANDOFF.md, which is the document handed to
the paper-drafting session. Sections 1 and 5 of that document are not here
because they are not computable: section 1 is the AHP elicitation history (no
record exists; see docs/AHP_MATRIX_AUDIT.md) and section 5 is the per-paper
criterion coding for the literature table, which must be done by hand from the
eight reviewed papers.

The AHP matrix audit is in tools/ahp_audit.py — kept separate because it is
slower and answers a different question.
"""

from __future__ import annotations

import os
import sys

# Drop tools/ from sys.path BEFORE any third-party import. This directory
# contains inspect.py, which shadows the standard library's `inspect` module;
# numpy imports `inspect` internally and would otherwise fail with
# "module 'inspect' has no attribute 'cleandoc'". Then add the project root so
# the analysis modules resolve regardless of the working directory.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
               if os.path.abspath(p or os.getcwd()) != _HERE]
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import argparse  # noqa: E402

import numpy as np  # noqa: E402

import criteria as C  # noqa: E402
import gis_analysis as G  # noqa: E402
from ahp import SCENARIOS, ahp_engine  # noqa: E402
from algorithms import ALGORITHMS, weights_for_algorithm  # noqa: E402

HIST_BINS = 50          # bins over 0–1 for the score-distribution figures
MC_SEED = 20260923      # not used here; recorded so both tools agree


# ─────────────────────────────────────────────────────────────────────────────
# Shared setup
# ─────────────────────────────────────────────────────────────────────────────

def _context(data_dir: str = "data"):
    """Criteria stack, district mask, baseline weights and per-cell area grid."""
    stack = G.build_criteria_stack(data_dir)
    mask = stack["district_mask"]
    weights, cr = ahp_engine.calculate_weights()
    px = G._pixel_area_km2_per_row(stack["transform"], stack["shape"])
    area = np.repeat(px[:, None], stack["shape"][1], axis=1)
    return stack, mask, weights, cr, area


def _score_all_algorithms(stack):
    """One scored result per algorithm, all on the same criteria stack."""
    out = {}
    for name in ALGORITHMS:
        w, agg, _label = weights_for_algorithm(name, ahp_engine.matrix, ahp_engine.criteria)
        out[name] = G.score_stack(stack, w, aggregator=agg, algorithm=name)
    return out


def _emit_csv(csv_dir: str | None, name: str, header: str, rows) -> None:
    if not csv_dir:
        return
    os.makedirs(csv_dir, exist_ok=True)
    path = os.path.join(csv_dir, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(header + "\n")
        for r in rows:
            fh.write(",".join(str(v) for v in r) + "\n")
    print(f"    [wrote {path}]")


# ─────────────────────────────────────────────────────────────────────────────
# §2 — Top five candidate sites per algorithm variant
# ─────────────────────────────────────────────────────────────────────────────

def section_2(ctx, csv_dir=None):
    stack, *_ = ctx
    print("### 2. Top 5 candidate sites per algorithm variant")
    rows = []
    for name, res in _score_all_algorithms(stack).items():
        print(f"\n--- {name} ---")
        print(f"{'rk':>3}{'lon':>10}{'lat':>10}{'score':>8}{'slope':>8}  "
              f"{'soil':<17}{'land cover':<20}{'dd':>7}{'settl km':>9}")
        for d in res["top_locations_details"][:5]:
            v = d["raw_values"]
            print(f"{d['rank']:>3}{d['lon']:>10.4f}{d['lat']:>10.4f}"
                  f"{d['suitability_score']:>8.3f}{v.get('slope_deg', float('nan')):>7.2f}°  "
                  f"{v.get('soil_class', '?'):<17}{v.get('lulc_class', '?'):<20}"
                  f"{v.get('drainage_density', float('nan')):>7.2f}"
                  f"{v.get('settlement_km', float('nan')):>9.1f}")
            rows.append([name, d["rank"], round(d["lon"], 4), round(d["lat"], 4),
                         d["suitability_score"], v.get("slope_deg"),
                         v.get("soil_class"), v.get("lulc_class"),
                         v.get("drainage_density"), v.get("settlement_km")])
    _emit_csv(csv_dir, "top5_per_algorithm.csv",
              "algorithm,rank,lon,lat,score,slope_deg,soil,lulc,drainage_density,settlement_km",
              rows)


# ─────────────────────────────────────────────────────────────────────────────
# §3 — Full pairwise correlation matrix
# ─────────────────────────────────────────────────────────────────────────────

def section_3(ctx, csv_dir=None):
    from scipy.stats import pearsonr, spearmanr
    stack, mask, *_ = ctx
    res = _score_all_algorithms(stack)
    names = list(res)
    surf = {n: res[n]["suitability_raster"] for n in names}

    valid = mask.copy()
    for n in names:
        valid &= ~np.isnan(surf[n])
    print("### 3. Pairwise correlation between algorithm surfaces")
    print(f"cells compared: {int(valid.sum()):,}\n")
    print(f"{'pair':<46}{'Spearman':>11}{'Pearson':>10}")
    rows = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = surf[names[i]][valid], surf[names[j]][valid]
            rho = float(spearmanr(a, b).statistic)
            r = float(pearsonr(a, b)[0])
            print(f"{names[i] + '  vs  ' + names[j]:<46}{rho:>11.4f}{r:>10.4f}")
            rows.append([names[i], names[j], round(rho, 4), round(r, 4)])
    print("\nNote: same-aggregation pairs sit at rho >= 0.9998; every")
    print("cross-aggregation pair sits at 0.959-0.967. Report 0.9998, not 1.000.")
    _emit_csv(csv_dir, "correlation_matrix.csv", "algorithm_a,algorithm_b,spearman,pearson", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §4 — Suitability class areas per algorithm variant
# ─────────────────────────────────────────────────────────────────────────────

def section_4(ctx, csv_dir=None):
    stack, *_ = ctx
    print("### 4. Suitability class area per algorithm variant")
    print("Areas integrate true per-row cell area; do NOT derive them by")
    print("multiplying class share by district total.\n")
    print(f"{'variant':<22}{'High %':>9}{'High km2':>12}{'Medium km2':>12}"
          f"{'Low km2':>11}{'total km2':>12}")
    rows = []
    for name, res in _score_all_algorithms(stack).items():
        cls = res["area_statistics"]["classes"]
        tot = res["area_statistics"]["total_km2"]
        print(f"{name:<22}{cls['High']['percent']:>9.2f}{cls['High']['area_km2']:>12.1f}"
              f"{cls['Medium']['area_km2']:>12.1f}{cls['Low']['area_km2']:>11.1f}{tot:>12.1f}")
        rows.append([name, cls["High"]["percent"], cls["High"]["area_km2"],
                     cls["Medium"]["area_km2"], cls["Low"]["area_km2"], tot])
    _emit_csv(csv_dir, "class_areas_per_algorithm.csv",
              "algorithm,high_pct,high_km2,medium_km2,low_km2,total_km2", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §6 — Class transition matrix, WLC → TOPSIS
# ─────────────────────────────────────────────────────────────────────────────

def section_6(ctx, csv_dir=None):
    stack, mask, _w, _cr, area = ctx
    res = _score_all_algorithms(stack)
    cw = res["AHP + WLC"]["classified_raster"]
    ct = res["AHP + TOPSIS"]["classified_raster"]
    both = mask & ~np.isnan(cw) & ~np.isnan(ct)
    label = {1: "Low", 2: "Medium", 3: "High"}

    print("### 6. Class transition matrix, AHP+WLC -> AHP+TOPSIS")
    print("Drives the alluvial panel. Band widths by km2.\n")
    print(f"{'from/to':<12}{'Low':>12}{'Medium':>12}{'High':>12}{'row total':>12}")
    rows = []
    for f in (3, 2, 1):
        counts, areas = [], []
        for t in (1, 2, 3):
            sel = both & (cw == f) & (ct == t)
            counts.append(int(sel.sum()))
            areas.append(float(area[sel].sum()))
            rows.append([label[f], label[t], counts[-1], round(areas[-1], 1)])
        print(f"{label[f]:<12}" + "".join(f"{c:>12,}" for c in counts) + f"{sum(counts):>12,}")
        print(f"{'  km2':<12}" + "".join(f"{a:>12.1f}" for a in areas) + f"{sum(areas):>12.1f}")

    unchanged = int((both & (cw == ct)).sum())
    total = int(both.sum())
    down = int((both & (ct < cw)).sum())
    up = int((both & (ct > cw)).sum())
    print(f"\nunchanged {unchanged:,}/{total:,} = {100 * unchanged / total:.2f}%   "
          f"reclassified {100 * (total - unchanged) / total:.2f}%")
    print(f"moved down a class: {down:,}   moved up: {up:,}   crossed two classes: "
          f"{int((both & (np.abs(ct - cw) == 2)).sum()):,}")
    _emit_csv(csv_dir, "transition_matrix.csv", "from_class,to_class,cells,km2", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §7 — Composite score histograms
# ─────────────────────────────────────────────────────────────────────────────

def section_7(ctx, csv_dir=None):
    stack, mask, *_ = ctx
    res = _score_all_algorithms(stack)
    edges = np.linspace(0, 1, HIST_BINS + 1)
    sw = res["AHP + WLC"]["suitability_raster"]
    st = res["AHP + TOPSIS"]["suitability_raster"]
    hw, _ = np.histogram(sw[mask & ~np.isnan(sw)], bins=edges)
    ht, _ = np.histogram(st[mask & ~np.isnan(st)], bins=edges)

    print(f"### 7. Composite score histograms, {HIST_BINS} bins over 0-1")
    print("Empty bins omitted.\n")
    print("bin_lo,bin_hi,WLC_count,TOPSIS_count")
    rows = []
    for i in range(HIST_BINS):
        if hw[i] or ht[i]:
            print(f"{edges[i]:.2f},{edges[i+1]:.2f},{hw[i]},{ht[i]}")
            rows.append([f"{edges[i]:.2f}", f"{edges[i+1]:.2f}", int(hw[i]), int(ht[i])])
    _emit_csv(csv_dir, "score_histograms_wlc_topsis.csv",
              "bin_lo,bin_hi,wlc_count,topsis_count", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §8 — Step reclassification vs interpolated ramps
# ─────────────────────────────────────────────────────────────────────────────
# ⚠ The step-scoring code was removed in August 2026. This rebuilds it from the
#   surviving anchor constants plus the CHANGELOG description of each flat top.
#   It is a RECONSTRUCTION of the August 2026 state of the model.
#
# ⚠⚠ It must also use the SOIL LEGEND AS IT WAS THEN, which was wrong (see
#   docs/SOIL_LEGEND_CORRECTION.md). This is not optional: the historical
#   973-cell plateau required BOTH flat scoring tops AND the dominant soil class
#   (code 4, 77.8% of the district) sitting at 1.00. Verified directly —
#   reconstructing with the historical soil table gives exactly 973 cells at
#   1.000, matching the record; with the corrected table it gives 1.
#
#   The paper should therefore say the tied plateau arose from flat tops acting
#   on a criterion that mislabelled the dominant class, not from flat tops
#   alone. Both contributed and the figure cannot separate them.

SLOPE_STEP = ((1, 1.00), (3, 0.85), (5, 0.68), (10, 0.42),
              (15, 0.20), (25, 0.08), (90, 0.05))
DRAINAGE_STEP = ((0.10, 0.25), (0.20, 0.50), (0.30, 0.72), (0.40, 0.88), (99, 1.00))

# The soil table as it stood before 2026-10-02. Used ONLY to reconstruct the
# historical distribution; criteria.py holds the corrected table.
HISTORICAL_SOIL_SCORES = {1: 0.55, 4: 1.00, 6: 0.80, 7: 0.50}


def _step_settlement(distance_km: np.ndarray) -> np.ndarray:
    """Pre-2026-08-08 settlement curve: a FLAT 1.00 plateau across 1-5 km."""
    out = np.full(distance_km.shape, np.nan, dtype=np.float32)
    out[distance_km < 1.0] = C.SETTLEMENT_SCORE_AT_ZERO
    out[(distance_km >= 1.0) & (distance_km <= 5.0)] = 1.00
    tail = distance_km > 5.0
    out[tail] = np.clip(1.00 - (distance_km[tail] - 5.0) / 10.0 * 0.90, 0.10, 1.00)
    return out


def section_8(ctx, csv_dir=None):
    stack, mask, weights, cr, _area = ctx
    raw = stack["raw_rasters"]

    step = {
        "slope": C.score_continuous_breaks(raw["slope"], SLOPE_STEP),
        "rainfall": C.score_quantiles(np.where(mask, raw["rainfall"], np.nan)),
        "soil": C.score_categorical(raw["soil"], HISTORICAL_SOIL_SCORES, C.SOIL_DEFAULT_SCORE),
        "lulc": C.score_categorical(raw["lulc"], C.LULC_SCORES, C.LULC_DEFAULT_SCORE),
        "drainage": C.score_continuous_breaks(stack["drainage_density"].astype(float), DRAINAGE_STEP),
        "population": _step_settlement(stack["settlement_distance_km"].astype(float)),
    }
    for k in step:
        step[k] = np.where(mask, step[k], np.nan)

    s_step, _cov = G._weighted_overlay(step, weights)
    s_ramp = G.score_stack(stack, weights, cr)["suitability_raster"]

    print("### 8. Step reclassification (RECONSTRUCTED) vs interpolated ramps")
    print("Rebuilds deleted code AND the pre-2026-10-02 soil legend, because the")
    print("historical distribution depended on both. See the module comment.")
    print("The 'current' column uses the corrected soil legend, so the two columns")
    print("differ by two changes, not one — state that in the caption.\n")
    for lab, s in (("STEP (reconstructed)", s_step), ("RAMP (current)", s_ramp)):
        a = s[mask & ~np.isnan(s)]
        print(f"{lab}")
        print(f"   n {a.size:,}   min {a.min():.4f}   max {a.max():.4f}   mean {a.mean():.4f}")
        print(f"   distinct values {len(np.unique(np.round(a, 6))):,}   "
              f"cells at exactly 1.000: {int((np.abs(a - 1.0) < 1e-9).sum()):,}")
        print(f"   High (> {C.SUITABILITY_THRESHOLDS[1]}): {100 * (a > C.SUITABILITY_THRESHOLDS[1]).mean():.2f}%\n")

    edges = np.linspace(0, 1, HIST_BINS + 1)
    hs, _ = np.histogram(s_step[mask & ~np.isnan(s_step)], bins=edges)
    hr, _ = np.histogram(s_ramp[mask & ~np.isnan(s_ramp)], bins=edges)
    print("bin_lo,bin_hi,STEP_count,RAMP_count")
    rows = []
    for i in range(HIST_BINS):
        if hs[i] or hr[i]:
            print(f"{edges[i]:.2f},{edges[i+1]:.2f},{hs[i]},{hr[i]}")
            rows.append([f"{edges[i]:.2f}", f"{edges[i+1]:.2f}", int(hs[i]), int(hr[i])])
    print("\nThe terminal bin is the figure: step puts thousands of cells in")
    print("0.98-1.00 against tens for ramps. Use a log or broken y-axis.")
    _emit_csv(csv_dir, "score_histograms_step_ramp.csv",
              "bin_lo,bin_hi,step_count,ramp_count", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §9 — Per-criterion score dispersion
# ─────────────────────────────────────────────────────────────────────────────

def section_9(ctx, csv_dir=None):
    stack, mask, weights, cr, _area = ctx
    res = G.score_stack(stack, weights, cr)
    high = mask & (res["classified_raster"] == 3)
    rasters = stack["normalized_rasters"]

    print("### 9. Per-criterion score dispersion")
    print("The paper must NOT claim drainage has the highest spatial variance.")
    print("It does not, on any framing below. The correct claim is in part (b).\n")

    print("(a) Across all in-district cells")
    print(f"{'criterion':<12}{'weight':>8}{'mean':>8}{'sd':>9}{'variance':>10}{'CV':>8}{'distinct':>10}")
    rows_a = []
    for k, v in sorted(rasters.items(), key=lambda kv: -float(np.nanstd(kv[1][mask]))):
        a = v[mask & ~np.isnan(v)]
        sd, mu = float(a.std()), float(a.mean())
        print(f"{k:<12}{weights[k]:>8.4f}{mu:>8.3f}{sd:>9.4f}{sd**2:>10.5f}"
              f"{sd/mu:>8.3f}{len(np.unique(np.round(a,4))):>10,}")
        rows_a.append([k, round(weights[k], 4), round(mu, 3), round(sd, 4), round(sd**2, 5)])

    print(f"\n(b) Within the {int(high.sum()):,} High-suitability cells — where every")
    print("    candidate site is drawn from. Ranked by weighted dispersion.")
    print("    This ordering matches top-10 retention under map removal exactly.")
    print(f"{'criterion':<12}{'weight':>8}{'mean':>8}{'sd':>9}{'sd(w*r)':>10}")
    rows_b = []
    scored = []
    for k, v in rasters.items():
        a = v[high & ~np.isnan(v)]
        scored.append((k, weights[k], float(a.mean()), float(a.std()), float((weights[k] * a).std())))
    for k, w, mu, sd, wsd in sorted(scored, key=lambda x: -x[4]):
        print(f"{k:<12}{w:>8.4f}{mu:>8.3f}{sd:>9.4f}{wsd:>10.5f}")
        rows_b.append([k, round(w, 4), round(mu, 3), round(sd, 4), round(wsd, 5)])

    print("\n(c) Across the 25 selected candidate sites")
    print(f"{'criterion':<12}{'sd':>10}{'min':>8}{'max':>8}")
    rows_c = []
    details = res["top_locations_details"]
    for k in rasters:
        vals = np.array([d["criteria_scores"].get(k, np.nan) for d in details], dtype=float)
        vals = vals[~np.isnan(vals)]
        print(f"{k:<12}{vals.std():>10.4f}{vals.min():>8.3f}{vals.max():>8.3f}")
        rows_c.append([k, round(float(vals.std()), 4), round(float(vals.min()), 3),
                       round(float(vals.max()), 3)])
    classes = {}
    for d in details:
        c = (d.get("raw_values") or {}).get("soil_class", "?")
        classes[c] = classes.get(c, 0) + 1
    print(f"\nSoil classes among the 25 sites: {classes}")
    print("Before the 2026-10-02 legend correction all 25 sat on one class scoring")
    print("1.000; the shortlist now spans several textures, which materially")
    print("weakens the shortlist-concentration limitation.")

    _emit_csv(csv_dir, "dispersion_all_cells.csv", "criterion,weight,mean,sd,variance", rows_a)
    _emit_csv(csv_dir, "dispersion_high_zone.csv", "criterion,weight,mean,sd,weighted_sd", rows_b)
    _emit_csv(csv_dir, "dispersion_top25.csv", "criterion,sd,min,max", rows_c)


# ─────────────────────────────────────────────────────────────────────────────
# §10 — Consensus sites across algorithms
# ─────────────────────────────────────────────────────────────────────────────

def section_10(ctx, csv_dir=None):
    from consensus import consensus_report
    stack, *_ = ctx
    rep = consensus_report(stack, axis="algorithms")
    sites = rep["sites"]
    unanimous = [s for s in sites if s["unanimous"]]

    print("### 10. Consensus sites across the four algorithms")
    print(f"{len(sites)} distinct locations proposed; {len(unanimous)} selected by all 4\n")
    print(f"{'crank':>6}{'lon':>10}{'lat':>10}{'picked':>8}{'borda':>7}"
          f"{'best':>7}{'meanrk':>8}  {'land cover':<22}{'settl':>7}")
    rows = []
    for s in sites[:20]:
        rv = s.get("raw_values") or {}
        print(f"{s['consensus_rank']:>6}{s['lon']:>10.4f}{s['lat']:>10.4f}"
              f"{str(s['n_variants']) + '/' + str(s['n_possible']):>8}{s['borda']:>7}"
              f"{s['best_score']:>7.3f}{s['mean_rank']:>8.1f}  "
              f"{rv.get('lulc_class', '?'):<22}{rv.get('settlement_km', float('nan')):>7.1f}")
    print("\nUnanimous (4/4) subset, in consensus-rank order:")
    for s in unanimous:
        print(f"  rank {s['consensus_rank']:<3} ({s['lon']:.4f}, {s['lat']:.4f})  "
              f"borda {s['borda']:>3}  best {s['best_score']:.3f}  mean rank {s['mean_rank']:.1f}")
        rows.append([s["consensus_rank"], round(s["lon"], 4), round(s["lat"], 4),
                     s["borda"], s["best_score"], s["mean_rank"]])
    print("\nUnanimity and Borda rank are different orderings: a site ranked highly")
    print("by three methods can out-score one ranked modestly by four.")
    _emit_csv(csv_dir, "consensus_unanimous.csv",
              "consensus_rank,lon,lat,borda,best_score,mean_rank", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §11 — Top-ranked site per scenario
# ─────────────────────────────────────────────────────────────────────────────

def section_11(ctx, csv_dir=None):
    stack, *_ = ctx
    print("### 11. Top-ranked site per planning scenario")
    print(f"{'scenario':<24}{'lon':>10}{'lat':>10}{'score':>8}{'CR':>9}{'settl km':>10}")
    rows = []
    for name in SCENARIOS:
        w, cr = ahp_engine.weights_for_scenario(name)
        res = G.score_stack(stack, w, cr)
        d = res["top_locations_details"][0]
        v = d["raw_values"]
        print(f"{name:<24}{d['lon']:>10.4f}{d['lat']:>10.4f}"
              f"{d['suitability_score']:>8.3f}{cr:>9.4f}"
              f"{v.get('settlement_km', float('nan')):>10.1f}")
        rows.append([name, round(d["lon"], 4), round(d["lat"], 4),
                     d["suitability_score"], round(cr, 4), v.get("settlement_km")])
    # Computed, not asserted — which scenarios agree has changed twice already.
    base_xy = (rows[0][1], rows[0][2])
    groups = {}
    for r in rows:
        groups.setdefault((r[1], r[2]), []).append(r[0])
    print(f"\n{len(groups)} distinct top-ranked location(s) across {len(rows)} scenarios:")
    for (lon, lat), members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        tag = "  <- baseline" if (lon, lat) == base_xy else ""
        print(f"  ({lon}, {lat})  chosen by {len(members)}: {', '.join(members)}{tag}")
    agree = max(len(m) for m in groups.values())
    if len(groups) == 1:
        print("\nAll scenarios agree on the same top site — reweighting does not move it.")
    elif agree == len(rows) - 1:
        print("\nOne scenario is the outlier; the rest agree. Name which, and say")
        print("that reweighting moves the top site only under that configuration.")
    else:
        print(f"\nScenarios split across {len(groups)} locations — reweighting")
        print("materially changes which site ranks first.")
    _emit_csv(csv_dir, "scenario_top_sites.csv", "scenario,lon,lat,score,cr,settlement_km", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §12 — CHIRPS district mean per year
# ─────────────────────────────────────────────────────────────────────────────

def section_12(ctx=None, csv_dir=None, data_dir="data"):
    import glob
    import re

    import geopandas as gpd
    import rasterio
    from rasterio.features import rasterize
    from rasterio.windows import from_bounds
    from rasterio.windows import transform as window_transform

    from build_rainfall import BUFFER_DEG, EXPECTED_MEAN_MM, NODATA_CUTOFF

    boundary = gpd.read_file(os.path.join(data_dir, "boundary.geojson"))
    minx, miny, maxx, maxy = boundary.total_bounds
    geoms = [(g, 1) for g in boundary.geometry if g is not None and not g.is_empty]

    print("### 12. CHIRPS district mean per year")
    print("Same window and NoData handling as build_rainfall.py.\n")
    print(f"{'year':>6}{'district mean mm':>18}{'min':>10}{'max':>10}")
    rows, means = [], []
    for path in sorted(glob.glob(os.path.join(data_dir, "chirps-v3.0.*.tif"))):
        m = re.search(r"\.(\d{4})\.tif$", path)
        if not m:
            continue
        year = int(m.group(1))
        with rasterio.open(path) as src:
            win = from_bounds(minx - BUFFER_DEG, miny - BUFFER_DEG,
                              maxx + BUFFER_DEG, maxy + BUFFER_DEG, src.transform)
            win = win.intersection(from_bounds(*src.bounds, src.transform))
            data = src.read(1, window=win).astype("float64")
            tr = window_transform(win, src.transform)
            if src.nodata is not None:
                data[data == src.nodata] = np.nan
        data[data <= NODATA_CUTOFF] = np.nan
        mask = rasterize(geoms, out_shape=data.shape, transform=tr,
                         fill=0, dtype="uint8", all_touched=True).astype(bool)
        vals = data[mask & ~np.isnan(data)]
        print(f"{year:>6}{vals.mean():>18.1f}{vals.min():>10.1f}{vals.max():>10.1f}")
        rows.append([year, round(float(vals.mean()), 1), round(float(vals.min()), 1),
                     round(float(vals.max()), 1)])
        means.append(float(vals.mean()))

    a = np.array(means)
    dry = [r[0] for r in rows if r[1] <= 1300]
    wet = [r[0] for r in rows if r[1] > 1400]
    print(f"\n11-year mean of annual means: {a.mean():.1f} mm   "
          f"interannual sd {a.std(ddof=1):.1f} mm")
    print(f"driest {a.min():.1f} ({rows[int(a.argmin())][0]})   "
          f"wettest {a.max():.1f} ({rows[int(a.argmax())][0]})")
    print(f"vs long-term normal {EXPECTED_MEAN_MM:.0f} mm: {100*(a.mean()-EXPECTED_MEAN_MM)/EXPECTED_MEAN_MM:+.1f}%")
    print(f"years at or below 1300 mm: {dry}")
    print(f"years above 1400 mm: {wet}")
    print("\nThese supersede three figures recorded in CHANGELOG.md — see the")
    print("corrections note in docs/PAPER_DATA_HANDOFF.md section 12.")
    _emit_csv(csv_dir, "chirps_annual_means.csv", "year,district_mean_mm,min_mm,max_mm", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §13 — Area by land-cover and soil class
# ─────────────────────────────────────────────────────────────────────────────

def section_13(ctx, csv_dir=None):
    stack, mask, _w, _cr, area = ctx
    print("### 13. Cell count and area by class")
    rows = []
    for layer, table, labels in (("lulc", C.LULC_SCORES, C.LULC_LABELS),
                                 ("soil", C.SOIL_TEXTURE_SCORES, C.SOIL_TEXTURE_LABELS)):
        data = stack["raw_rasters"][layer]
        valid = mask & ~np.isnan(data)
        codes = np.rint(np.where(valid, data, -1)).astype(int)
        total = float(area[valid].sum())
        print(f"\n-- {layer.upper()} --")
        print(f"{'code':>5}  {'class':<38}{'cells':>9}{'km2':>10}{'share %':>9}{'score':>7}")
        order = sorted(set(codes[valid].tolist()),
                       key=lambda c: -float(area[valid & (codes == c)].sum()))
        for code in order:
            sel = valid & (codes == code)
            km2 = float(area[sel].sum())
            print(f"{code:>5}  {labels.get(code, '?'):<38}{int(sel.sum()):>9,}"
                  f"{km2:>10.1f}{100 * km2 / total:>9.2f}{table.get(code, float('nan')):>7.2f}")
            rows.append([layer, code, labels.get(code, "?"), int(sel.sum()),
                         round(km2, 1), round(100 * km2 / total, 2), table.get(code)])
    print("\nCropland dominates land cover and Clay Loam dominates soil. Note the")
    print("dominant soil class scores 0.60, not 1.00 — before the 2026-10-02 legend")
    print("correction it was read as Silt Loam and scored 1.00. See")
    print("docs/SOIL_LEGEND_CORRECTION.md.")
    _emit_csv(csv_dir, "class_areas.csv", "layer,code,class,cells,km2,share_pct,score", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §14 — Coverage gate audit
# ─────────────────────────────────────────────────────────────────────────────

def section_14(ctx, csv_dir=None):
    stack, mask, weights, cr, _area = ctx
    res = G.score_stack(stack, weights, cr)
    surface = res["suitability_raster"]
    scored = int((mask & ~np.isnan(surface)).sum())
    dropped = int((mask & np.isnan(surface)).sum())

    coverage = np.sum([np.where(np.isnan(v), 0.0, weights[k])
                       for k, v in stack["normalized_rasters"].items()], axis=0)[mask]
    print("### 14. Coverage gate audit")
    print(f"in-district cells {int(mask.sum()):,}   scored {scored:,}   "
          f"dropped by the {C.MIN_WEIGHT_COVERAGE:.0%} gate: {dropped}")
    print(f"weight coverage inside district: min {coverage.min():.4f}  mean {coverage.mean():.4f}")
    print(f"cells below full coverage: {int((coverage < 0.9999).sum()):,}")
    print("\nThe gate is a structural safeguard that does not bind on these inputs.")
    print("State it that way; do not imply it removes anything.")


# ─────────────────────────────────────────────────────────────────────────────
# §16 — Test and run counts
# ─────────────────────────────────────────────────────────────────────────────

def section_16(ctx, csv_dir=None):
    from sensitivity import (map_removal_sensitivity, one_way_sensitivity,
                             single_parameter_sensitivity)
    stack, _mask, weights, _cr, _area = ctx
    ow = one_way_sensitivity(stack, weights)
    mr = map_removal_sensitivity(stack, weights)
    sp = single_parameter_sensitivity(stack, weights)

    n_alg, n_scn = len(ALGORITHMS), len(SCENARIOS)
    print("### 16. Test and run counts")
    print(f"  one-way perturbation       : {len(ow['runs'])} runs at +/-{ow['delta']*100:.0f}%")
    print(f"  map removal                : {len(mr['rows'])} runs")
    print(f"  single-parameter           : {len(sp['rows'])} criteria")
    print(f"  algorithms compared        : {n_alg}   pairwise correlations: {n_alg*(n_alg-1)//2}")
    print(f"  scenarios compared         : {n_scn}")
    total = 1 + (len(ow["runs"]) + 1) + (len(mr["rows"]) + 1) + 1 + n_alg * 2 + n_scn
    print(f"\n  total distinct pipeline scorings: {total}")
    print(f"  perturbation runs (12+6+6)      : {len(ow['runs']) + len(mr['rows']) + len(sp['rows'])}")
    print("\n  software checks: 11 smoke-test assertions, 5 AUC analytic cases,")
    print("  3 internal cross-checks (area 99.7%, river length 0.08%, rainfall +/-20%)")
    print("\n  NONE of these are validation tests. They test internal behaviour and")
    print("  software correctness, not agreement with observed structures.")


# ─────────────────────────────────────────────────────────────────────────────
# §17 — Criterion correlation matrix
# ─────────────────────────────────────────────────────────────────────────────

TIE_PROB_UNRELIABLE = 0.20   # above this, a rank correlation is not trustworthy


def _tie_probability(values: np.ndarray) -> float:
    """Probability that two randomly drawn cells share a value.

    The right diagnostic for whether a rank correlation can be believed. Soil
    takes 4 distinct values and land cover 10, so most pairs are tied and
    Spearman degenerates into comparing a handful of plateaus rather than
    measuring a monotone relationship.
    """
    _vals, counts = np.unique(values, return_counts=True)
    p = counts / counts.sum()
    return float((p ** 2).sum())


def _corr_pairs(rasters, sel, names):
    """Spearman and Pearson for every unordered pair, over the selected cells."""
    from scipy.stats import pearsonr, spearmanr
    out = {}
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = rasters[names[i]][sel], rasters[names[j]][sel]
            ok = ~np.isnan(a) & ~np.isnan(b)
            if ok.sum() < 3:
                out[(names[i], names[j])] = (float("nan"), float("nan"))
            else:
                out[(names[i], names[j])] = (
                    float(spearmanr(a[ok], b[ok]).statistic),
                    float(pearsonr(a[ok], b[ok])[0]))
    return out


def section_17(ctx, csv_dir=None):
    stack, mask, _w, _cr, _area = ctx
    rasters = stack["normalized_rasters"]
    names = [c for c in ahp_engine.criteria if c in rasters]

    print("### 17. Criterion correlation matrix")
    print(f"Measured on the SCORED 0-1 criterion surfaces over the "
          f"{int(mask.sum()):,} IN-DISTRICT cells.")
    print("Not the raw inputs; not the whole raster.\n")

    print("Tie structure — read before trusting any rank correlation below.")
    print("Tie probability = chance two randomly drawn cells share a value.")
    print(f"{'criterion':<12}{'distinct':>10}{'tie prob':>11}{'rank corr':>13}")
    ties = {}
    for c in names:
        v = rasters[c][mask & ~np.isnan(rasters[c])]
        ties[c] = _tie_probability(v)
        verdict = "UNRELIABLE" if ties[c] > TIE_PROB_UNRELIABLE else "ok"
        print(f"{c:<12}{len(np.unique(np.round(v, 6))):>10,}{ties[c]:>11.4f}{verdict:>13}")
    weak = [c for c in names if ties[c] > TIE_PROB_UNRELIABLE]
    print("\nTies handled by mid-rank (scipy default) throughout.")
    if weak:
        print(f"WARNING: Spearman involving {', '.join(weak)} is not reliable.")
        print("  Those criteria are near-constant in rank terms. Quote Pearson,")
        print("  or quote neither — do not report rho without this caveat.")

    whole = _corr_pairs(rasters, mask, names)
    print("\n--- All 15 pairs, whole district ---")
    print(f"{'pair':<26}{'Spearman':>11}{'Pearson':>10}  note")
    rows = []
    for (a, b), (rho, r) in whole.items():
        flag = ties[a] > TIE_PROB_UNRELIABLE or ties[b] > TIE_PROB_UNRELIABLE
        print(f"{a + ' / ' + b:<26}{rho:>11.4f}{r:>10.4f}  "
              f"{'rho unreliable (ties)' if flag else ''}")
        rows.append(["whole", a, b, round(rho, 4), round(r, 4),
                     "unreliable" if flag else "ok"])

    for label, idx in (("Spearman", 0), ("Pearson", 1)):
        print(f"\n--- 6x6 {label} matrix ---")
        print(f"{'':<12}" + "".join(f"{c[:8]:>10}" for c in names))
        for a in names:
            line = f"{a:<12}"
            for b in names:
                if a == b:
                    line += f"{1.0:>10.3f}"
                else:
                    key = (a, b) if (a, b) in whole else (b, a)
                    line += f"{whole[key][idx]:>10.3f}"
            print(line)

    # The specific question the paper asks: is the dependence between drainage,
    # land cover and soil a district-wide property or a cropland artefact?
    lulc_raw = stack["raw_rasters"].get("lulc")
    crop = mask & (np.rint(np.nan_to_num(lulc_raw, nan=-1)) == 12)
    noncrop = mask & ~crop & ~np.isnan(lulc_raw)
    sub_c = _corr_pairs(rasters, crop, names)
    sub_n = _corr_pairs(rasters, noncrop, names)

    print("\n--- Stratified by land cover: artefact or real? ---")
    print(f"cropland {int(crop.sum()):,} cells   non-cropland {int(noncrop.sum()):,} cells")

    # Pairs that do NOT involve land cover can be tested directly: if the
    # association survives inside both strata it is not a land-cover artefact.
    print(f"\n{'pair':<22}{'whole r':>10}{'cropland':>11}{'non-crop':>11}   verdict")
    for a, b in (("drainage", "soil"),):
        if a not in names or b not in names:
            continue
        key = (a, b) if (a, b) in whole else (b, a)
        rw, rc, rn = whole[key][1], sub_c[key][1], sub_n[key][1]
        inside = max(abs(rc), abs(rn))
        verdict = ("artefact of land cover" if abs(rw) > 0.05 and inside < abs(rw) * 0.5
                   else "persists within strata")
        print(f"{a + ' / ' + b:<22}{rw:>10.4f}{rc:>11.4f}{rn:>11.4f}   {verdict}")
        rows.append(["stratified", a, b, round(rw, 4), round(rc, 4), round(rn, 4)])

    # Pairs that DO involve land cover cannot be tested this way — holding land
    # cover constant makes it a constant, and the correlation is undefined
    # (nan). The mechanism to report instead is the group-mean contrast, which
    # is what generates the district-wide correlation in the first place.
    print("\nPairs involving land cover cannot be stratified by land cover —")
    print("within cropland the LULC score is constant, so r is undefined. The")
    print("mechanism is the between-group contrast, reported here instead:")
    print(f"\n{'criterion':<12}{'cropland mean':>15}{'non-crop mean':>15}{'difference':>12}")
    for c in names:
        if c == "lulc":
            continue
        mc = float(np.nanmean(rasters[c][crop]))
        mn = float(np.nanmean(rasters[c][noncrop]))
        print(f"{c:<12}{mc:>15.4f}{mn:>15.4f}{mc - mn:>+12.4f}")
        rows.append(["group_means", c, "cropland_vs_not", round(mc, 4), round(mn, 4),
                     round(mc - mn, 4)])
    print("\nA large difference here means the district-wide correlation with")
    print("land cover is driven by that contrast, not by a within-stratum")
    print("relationship. A small one means land cover is carrying independent")
    print("information.")

    strongest = max((abs(v[1]), k) for k, v in whole.items())
    print(f"\nStrongest absolute Pearson between any two criteria: "
          f"{strongest[0]:.3f} ({strongest[1][0]} / {strongest[1][1]}).")
    print("Wording note: weak correlation is evidence AGAINST double counting.")
    print("Do not use that phrase unless the magnitudes support it.")
    _emit_csv(csv_dir, "criterion_correlations.csv",
              "scope,criterion_a,criterion_b,val1,val2,val3", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §18 — Rainfall scoring: percentile rank versus fixed absolute bands
# ─────────────────────────────────────────────────────────────────────────────
# The fixed-band alternative did NOT exist before 2026-10-02. criteria.py
# supplied score_continuous_breaks() as a generic helper plus a comment calling
# fixed bands "a viable alternative", but no bands were ever defined. They are
# defined here, for this comparison only; criteria.py is unchanged and
# percentile rank remains the operational scoring.
#
# Provenance of the cut points: round absolute thresholds spanning the range of
# Indian annual rainfall relevant to RWH planning, chosen so the scheme
# transfers unchanged to a drier or wetter district. They are NOT from a
# published classification — no source in this repository supplies one. The
# paper must say so rather than implying a citation.

RAINFALL_FIXED_BANDS = (
    (500.0, 0.20),    # arid, minimal harvestable surplus
    (750.0, 0.35),
    (1000.0, 0.55),
    (1250.0, 0.75),
    (1500.0, 0.90),
    (9999.0, 1.00),   # very high annual rainfall
)


def section_18(ctx, csv_dir=None):
    from scipy.stats import pearsonr, spearmanr

    from sensitivity import _match_sites
    stack, mask, weights, cr, area = ctx

    print("### 18. Rainfall scoring: percentile rank vs fixed absolute bands")
    print("Everything else identical — same stack, weights, aggregation,")
    print("thresholds, extraction. Only the rainfall scoring function changes.")
    print("Domain: in-district cells.\n")
    print("Fixed bands used (upper bound -> score):")
    for ub, sc in RAINFALL_FIXED_BANDS:
        label = f"<= {ub:,.0f} mm" if ub < 9999 else "> 1,500 mm"
        print(f"    {label:>14}  ->  {sc:.2f}")
    print("\nNOTE: these bands are defined in this file for the comparison. They")
    print("are not in criteria.py and not from a published classification — say")
    print("so in the paper. Chandrapur spans 1,189-1,714 mm, so the whole")
    print("district falls in the top three bands. That IS the trade-off tested.")

    base = G.score_stack(stack, weights, cr)
    rain_raw = np.where(mask, stack["raw_rasters"]["rainfall"], np.nan)
    alt_rasters = dict(stack["normalized_rasters"])
    alt_rasters["rainfall"] = np.where(
        mask, C.score_continuous_breaks(rain_raw, RAINFALL_FIXED_BANDS), np.nan)
    alt_stack = dict(stack)
    alt_stack["normalized_rasters"] = alt_rasters
    alt = G.score_stack(alt_stack, weights, cr)

    rows = []
    print("\n--- Headline comparison ---")
    print(f"{'measure':<32}{'percentile':>14}{'fixed bands':>14}")
    for label, fn, fmt in (
        ("High suitability %", lambda r: r["area_statistics"]["classes"]["High"]["percent"], 2),
        ("High suitability km2", lambda r: r["area_statistics"]["classes"]["High"]["area_km2"], 1),
        ("Medium %", lambda r: r["area_statistics"]["classes"]["Medium"]["percent"], 2),
        ("Low %", lambda r: r["area_statistics"]["classes"]["Low"]["percent"], 2),
        ("composite mean", lambda r: float(np.nanmean(r["suitability_raster"])), 4),
        ("composite median", lambda r: float(np.nanmedian(r["suitability_raster"])), 4),
    ):
        a, b = fn(base), fn(alt)
        print(f"{label:<32}{a:>14.{fmt}f}{b:>14.{fmt}f}")
        rows.append([label, round(a, 4), round(b, 4)])

    sb, sa = base["suitability_raster"], alt["suitability_raster"]
    both = mask & ~np.isnan(sb) & ~np.isnan(sa)
    rho = float(spearmanr(sb[both], sa[both]).statistic)
    r = float(pearsonr(sb[both], sa[both])[0])
    agree = float((base["classified_raster"][both] == alt["classified_raster"][both]).mean() * 100)
    _p, k10 = _match_sites(base["top_locations_details"][:10],
                           alt["top_locations_details"][:10], 2.0)
    _p, k25 = _match_sites(base["top_locations_details"],
                           alt["top_locations_details"], 2.0)
    print(f"\n{'Spearman rho between surfaces':<32}{rho:>28.4f}")
    print(f"{'Pearson r between surfaces':<32}{r:>28.4f}")
    print(f"{'class agreement %':<32}{agree:>28.2f}")
    print(f"{'top-10 overlap':<32}{str(k10) + '/10':>28}")
    print(f"{'top-25 overlap':<32}{str(k25) + '/25':>28}")
    rows += [["spearman", rho, ""], ["pearson", r, ""],
             ["class_agreement_pct", round(agree, 2), ""],
             ["top10_overlap", k10, ""], ["top25_overlap", k25, ""]]

    print("\n--- Class transition, percentile -> fixed bands ---")
    cb, ca = base["classified_raster"], alt["classified_raster"]
    lab = {1: "Low", 2: "Medium", 3: "High"}
    print(f"{'from/to':<12}{'Low':>14}{'Medium':>14}{'High':>14}")
    for f in (3, 2, 1):
        cells, areas = [], []
        for t in (1, 2, 3):
            sel = both & (cb == f) & (ca == t)
            cells.append(int(sel.sum()))
            areas.append(float(area[sel].sum()))
            rows.append([f"transition_{lab[f]}_to_{lab[t]}", cells[-1], round(areas[-1], 1)])
        print(f"{lab[f]:<12}" + "".join(f"{c:>14,}" for c in cells))
        print(f"{'  km2':<12}" + "".join(f"{a:>14.1f}" for a in areas))
    unch = int((both & (cb == ca)).sum())
    print(f"\nunchanged {unch:,}/{int(both.sum()):,} = {100 * unch / int(both.sum()):.2f}%")

    print("\n--- Effective weights under each scheme ---")
    print(f"{'criterion':<12}{'assigned %':>12}{'pct-rank':>11}{'ratio':>8}"
          f"{'fixed':>11}{'ratio':>8}")
    for crit in ahp_engine.criteria:
        if crit not in stack["normalized_rasters"]:
            continue
        w = weights[crit]
        line = f"{crit:<12}{100 * w:>12.2f}"
        effs = []
        for res, rast in ((base, stack["normalized_rasters"]), (alt, alt_rasters)):
            V = res["suitability_raster"]
            ok = mask & ~np.isnan(V) & (V > 0) & ~np.isnan(rast[crit])
            eff = float((100.0 * w * rast[crit][ok] / V[ok]).mean())
            effs.append(eff)
            line += f"{eff:>11.2f}{eff / (100 * w):>8.3f}"
        print(line)
        rows.append([f"effweight_{crit}", round(effs[0], 2), round(effs[1], 2)])

    _emit_csv(csv_dir, "rainfall_scoring_comparison.csv",
              "measure,percentile,fixed_bands", rows)


# ─────────────────────────────────────────────────────────────────────────────
# §19 — Is the WLC→TOPSIS reclassification spatially concentrated?
# ─────────────────────────────────────────────────────────────────────────────
# Backs the difference map (Figure 14). The question the paper needs answered is
# not "do the two methods disagree" — §6 already quantifies that — but "do they
# disagree somewhere in particular". If the disagreement concentrates near the
# district boundary it connects to the documented edge effect, where distance-
# and density-based criteria are blind to features just outside the district.

def section_19(ctx, csv_dir=None):
    stack, mask, weights, cr, area = ctx
    res = _score_all_algorithms(stack)
    cw = res["AHP + WLC"]["classified_raster"]
    ct = res["AHP + TOPSIS"]["classified_raster"]
    sw = res["AHP + WLC"]["suitability_raster"]
    st = res["AHP + TOPSIS"]["suitability_raster"]
    both = mask & ~np.isnan(cw) & ~np.isnan(ct)

    # Distance from every in-district cell to the nearest cell outside the
    # district — i.e. to the boundary — in kilometres.
    dy_km, dx_km = G._pixel_size_km(stack["transform"], stack["shape"])
    dist_km = G._distance_km(~mask, dy_km, dx_km)

    print("### 19. Spatial structure of the WLC -> TOPSIS disagreement")
    print("Domain: in-district cells. Backs Figure 14.\n")

    diff = np.where(both, sw - st, np.nan)
    d = diff[both]
    print(f"baseline minus TOPSIS: mean {d.mean():+.4f}  median {np.median(d):+.4f}")
    print(f"  range {d.min():+.4f} to {d.max():+.4f}   "
          f"cells where WLC scores higher: {100 * float((d > 0).mean()):.1f}%")

    changed = both & (cw != ct)
    down = both & (ct < cw)
    print(f"\nreclassified {int(changed.sum()):,} of {int(both.sum()):,} cells "
          f"= {100 * changed.sum() / both.sum():.2f}%")
    print(f"  of those, {100 * float(down[changed].mean()):.1f}% moved DOWN a class")

    print("\n--- Reclassification rate by distance to the district boundary ---")
    print(f"{'band':<16}{'cells':>10}{'reclassified':>14}{'rate %':>10}{'km2':>10}")
    bands = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 999)]
    rows = []
    for lo, hi in bands:
        sel = both & (dist_km >= lo) & (dist_km < hi)
        n = int(sel.sum())
        if not n:
            continue
        rc = int((sel & changed).sum())
        label = f"{lo}-{hi} km" if hi < 999 else f">{lo} km"
        print(f"{label:<16}{n:>10,}{rc:>14,}{100 * rc / n:>10.2f}{float(area[sel].sum()):>10.1f}")
        rows.append([label, n, rc, round(100 * rc / n, 2), round(float(area[sel].sum()), 1)])

    near = both & (dist_km < 5)
    far = both & (dist_km >= 5)
    rate_near = 100 * float(changed[near].mean())
    rate_far = 100 * float(changed[far].mean())
    print(f"\nwithin 5 km of the boundary : {rate_near:.2f}% reclassified "
          f"({int(near.sum()):,} cells)")
    print(f"beyond 5 km                 : {rate_far:.2f}% reclassified "
          f"({int(far.sum()):,} cells)")
    ratio = rate_near / rate_far if rate_far else float("nan")
    print(f"ratio near/far: {ratio:.2f}x")
    rows.append(["within_5km_rate_pct", round(rate_near, 2), "", "", ""])
    rows.append(["beyond_5km_rate_pct", round(rate_far, 2), "", "", ""])

    if ratio > 1.25:
        print("\nFINDING: the disagreement IS concentrated near the boundary.")
        print("That connects directly to the edge-effect limitation — distance and")
        print("density criteria see only in-district features — and is reportable.")
    elif ratio < 0.8:
        print("\nFINDING: the disagreement is concentrated in the INTERIOR, not the")
        print("rim. It is not an edge artefact.")
    else:
        print("\nFINDING: no meaningful boundary concentration (ratio within 0.8-1.25).")
        print("The disagreement is spatially diffuse. Say so — it rules out the")
        print("edge effect as an explanation, which is itself worth one sentence.")

    print("\n--- Where the disagreement actually sits, by baseline class ---")
    lab = {1: "Low", 2: "Medium", 3: "High"}
    for c in (3, 2, 1):
        sel = both & (cw == c)
        if not sel.sum():
            continue
        print(f"  baseline {lab[c]:<7} {int(sel.sum()):>8,} cells, "
              f"{100 * float(changed[sel].mean()):>6.2f}% reclassified")
        rows.append([f"baseline_{lab[c]}_reclass_pct",
                     round(100 * float(changed[sel].mean()), 2), "", "", ""])

    _emit_csv(csv_dir, "disagreement_spatial_structure.csv",
              "band_or_measure,cells,reclassified,rate_pct,km2", rows)


SECTIONS = {
    2: section_2, 3: section_3, 4: section_4, 6: section_6, 7: section_7,
    8: section_8, 9: section_9, 10: section_10, 11: section_11,
    12: section_12, 13: section_13, 14: section_14, 16: section_16,
    17: section_17, 18: section_18, 19: section_19,
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Reproduce every number cited in the paper.")
    ap.add_argument("--section", type=int, choices=sorted(SECTIONS),
                    help="run one section only (default: all)")
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--csv-dir", default=None,
                    help="also write machine-readable CSVs to this directory")
    args = ap.parse_args()

    wanted = [args.section] if args.section else sorted(SECTIONS)

    # Section 12 reads the CHIRPS globals directly and needs no criteria stack.
    ctx = None
    if any(s != 12 for s in wanted):
        ctx = _context(args.data_dir)

    for i, num in enumerate(wanted):
        if i:
            print("\n" + "=" * 78 + "\n")
        if num == 12:
            section_12(csv_dir=args.csv_dir, data_dir=args.data_dir)
        else:
            SECTIONS[num](ctx, csv_dir=args.csv_dir)


if __name__ == "__main__":
    main()
