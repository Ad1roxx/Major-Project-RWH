"""
tools/inspect_mgnrega_2.py
──────────────────────────
Follow-up inspection of data/interim/mgnrega_all.parquet. Still no filtering
and no validation.

    python tools/inspect_mgnrega_2.py            # all parts, downloads photos
    python tools/inspect_mgnrega_2.py --no-photos

1. Photo-audit sample: 30 records per category segment, stratified by stage,
   seed 42; photo1 downloaded one at a time, 1 s apart, existing files skipped.
2. Spread of multi-geotag workcodes (max pairwise distance).
3. The stage-3 FY 2021-22 spike, by category segment.
4. Distance of out-of-district points to the boundary; mask provenance.
Writes reports/mgnrega_inspection_2.md.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
ROOT = os.path.dirname(_HERE)
sys.path.insert(0, ROOT)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

PARQUET = os.path.join(ROOT, "data", "interim", "mgnrega_all.parquet")
BOUNDARY = os.path.join(ROOT, "data", "boundary.geojson")
REPORT = os.path.join(ROOT, "reports", "mgnrega_inspection_2.md")
AUDIT = os.path.join(ROOT, "reports", "photo_audit")
SEGS = ["WC", "WH", "RS", "DP", "IF", "LD", "FP"]
N, SEED = 30, 42


def md(df, index=False):
    d = df.reset_index() if index else df
    def cell(v):
        if isinstance(v, (float, np.floating)):
            return "" if np.isnan(v) else (f"{v:,.1f}" if abs(v) >= 10 else f"{v:.3f}".rstrip("0").rstrip("."))
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}"
        return "" if v is None else str(v)
    rows = ["| " + " | ".join(map(str, d.columns)) + " |", "|" + "---|" * len(d.columns)]
    rows += ["| " + " | ".join(cell(v) for v in r) + " |" for r in d.itertuples(index=False)]
    return "\n".join(rows)


def stratified(pool, n, seed):
    """n records, split across stages in proportion to the pool (largest remainder)."""
    if len(pool) <= n:
        return pool
    share = pool["stage"].value_counts() / len(pool)
    raw = share * n
    k = np.floor(raw).astype(int)
    for s in (raw - k).sort_values(ascending=False).index[: n - k.sum()]:
        k[s] += 1
    return pd.concat([pool[pool.stage == s].sample(int(k[s]), random_state=seed)
                      for s in k.index if k[s] > 0])


# ── 1 ───────────────────────────────────────────────────────────────────────
def photo_audit(df, download: bool, R):
    import requests
    R.append("## 1. Photo-audit sample\n")
    is_iay = df["third_seg"].fillna("") == "IAY"
    R.append(f"Records with a 4th workcode segment `IAY` excluded from the main sample: "
             f"**{int(is_iay.sum()):,}** (all in category IF: "
             f"{int((is_iay & (df.category_seg == 'IF')).sum()):,}).\n")
    groups = [(seg, df[(df.category_seg == seg) & ~is_iay]) for seg in SEGS]
    groups.append(("IF_IAY", df[(df.category_seg == "IF") & is_iay]))
    rows, summary, failed = [], [], []
    for seg, pool in groups:
        smp = stratified(pool, N, SEED)
        summary.append({"group": seg, "pool": len(pool),
                        "pool stage 0": int((pool.stage == "0").sum()),
                        "pool stage 3": int((pool.stage == "3").sum()),
                        "sampled": len(smp), "sampled stage 0": int((smp.stage == "0").sum()),
                        "sampled stage 3": int((smp.stage == "3").sum())})
        os.makedirs(os.path.join(AUDIT, seg), exist_ok=True)
        for r in smp.itertuples():
            rel = f"reports/photo_audit/{seg}/{r.collection_sno}.jpg"
            path = os.path.join(ROOT, rel)
            ok = os.path.exists(path)
            if download and not ok:
                try:
                    resp = requests.get(r.path1, timeout=60)
                    if resp.status_code == 200 and resp.content:
                        with open(path, "wb") as fh:
                            fh.write(resp.content)
                        ok = True
                    else:
                        failed.append((seg, r.collection_sno, f"HTTP {resp.status_code}"))
                except Exception as exc:
                    failed.append((seg, r.collection_sno, exc.__class__.__name__))
                time.sleep(1)
            rows.append({"collection_sno": r.collection_sno, "category_seg": seg,
                         "stage": r.stage, "workcode": r.workcode,
                         "photo_file": rel if ok else "", "label": "", "notes": ""})
    pd.DataFrame(rows).to_csv(os.path.join(AUDIT, "labels.csv"), index=False)
    R.append(md(pd.DataFrame(summary)) + "\n")
    got = sum(1 for r in rows if r["photo_file"])
    R.append(f"Photos on disk: **{got} of {len(rows)}**; download failures: **{len(failed)}**"
             + ("" if not failed else " — " + "; ".join(f"{s}/{c} ({e})" for s, c, e in failed[:20]))
             + ". Labels template: `reports/photo_audit/labels.csv` (label and notes empty). "
             "Sampling seed 42; stage split proportional to each pool (largest remainder).\n")


# ── 2 ───────────────────────────────────────────────────────────────────────
def _maxpair_m(lat, lon):
    la, lo = np.radians(lat), np.radians(lon)
    dla = la[:, None] - la[None, :]
    dlo = lo[:, None] - lo[None, :]
    a = np.sin(dla / 2) ** 2 + np.cos(la[:, None]) * np.cos(la[None, :]) * np.sin(dlo / 2) ** 2
    return float(2 * 6371008.8 * np.arcsin(np.sqrt(a)).max())


def spread(df, R):
    R.append("## 2. Spread of workcodes with more than one record\n")
    R.append("Max pairwise great-circle distance between a workcode's points, computed within "
             "each stage (no workcode occurs in both stages).\n")
    out = []
    for (s, wc), g in df.groupby(["stage", "workcode"], sort=False):
        if len(g) < 2:
            continue
        out.append({"stage": s, "workcode": wc, "n": len(g),
                    "category_seg": g["category_seg"].iloc[0],
                    "location_level": g["location_level"].iloc[0],
                    "max_m": _maxpair_m(g["lat"].to_numpy(float), g["lon"].to_numpy(float))})
    sp = pd.DataFrame(out)

    def summ(d):
        m = d["max_m"]
        return pd.Series({"workcodes": len(d), "records": int(d["n"].sum()),
                          "max group": int(d["n"].max()),
                          "q1 m": m.quantile(.25), "median m": m.median(), "q3 m": m.quantile(.75),
                          "max m": m.max(),
                          "< 50 m": f"{100 * (m < 50).mean():.1f}%",
                          "< 300 m": f"{100 * (m < 300).mean():.1f}%",
                          "> 1 km": f"{100 * (m > 1000).mean():.1f}%"})
    R.append("**Per stage**\n")
    R.append(md(sp.groupby("stage").apply(summ, include_groups=False), index=True) + "\n")
    R.append("**Per category segment (both stages)**\n")
    t = sp.groupby("category_seg").apply(summ, include_groups=False).sort_values("workcodes", ascending=False)
    R.append(md(t, index=True) + "\n")
    R.append("**Per stage × category segment (segments with ≥ 20 multi-record workcodes)**\n")
    t2 = sp.groupby(["stage", "category_seg"]).apply(summ, include_groups=False)
    t2 = t2[t2["workcodes"] >= 20]
    R.append(md(t2, index=True) + "\n")
    ns = sp[sp.location_level == "other"]
    R.append(f"Of these, **{len(ns):,}** workcodes are non-standard (no 7- or 10-digit location "
             f"code, e.g. `{ns.workcode.iloc[0] if len(ns) else ''}`), covering {int(ns.n.sum()):,} "
             f"records. Such a code may group unrelated works, so a large spread there says "
             f"nothing about any one structure. Their median spread: "
             f"{ns.max_m.median():,.0f} m.\n" if len(ns) else "")


# ── 3 ───────────────────────────────────────────────────────────────────────
def fy_spike(df, R):
    R.append("## 3. Stage-3 FY 2021-22 spike\n")
    s3 = df[df.stage == "3"]
    spike = s3[s3.fy_from_path == "2021-2022"]
    rest = s3[s3.fy_from_path != "2021-2022"]
    t = pd.DataFrame({"2021-22 n": spike.category_seg.value_counts(),
                      "other FYs n": rest.category_seg.value_counts()}).fillna(0).astype(int)
    t["2021-22 % of segment"] = (100 * t["2021-22 n"] / (t["2021-22 n"] + t["other FYs n"])).round(1)
    t["share of spike %"] = (100 * t["2021-22 n"] / len(spike)).round(1)
    R.append(f"{len(spike):,} of {len(s3):,} stage-3 records ({100 * len(spike) / len(s3):.1f}%) "
             "carry fy_from_path 2021-2022 (unverified field).\n")
    R.append(md(t.sort_values("2021-22 n", ascending=False), index=True) + "\n")
    third = spike.third_seg.value_counts()
    if len(third):
        R.append("4th-segment workcodes inside the spike: " +
                 ", ".join(f"`{k}` {v:,}" for k, v in third.items()) + ".\n")
    ct = pd.to_datetime(spike.creationtime_parsed).dt.year.value_counts().sort_index()
    R.append("creationtime year of the spike records: " +
             ", ".join(f"{int(k)}: {v:,}" for k, v in ct.items()) + ".\n")


# ── 4 ───────────────────────────────────────────────────────────────────────
def outside(df, R):
    import geopandas as gpd
    import gis_analysis as G
    import rasterio
    R.append("## 4. Out-of-district points\n")
    bnd = gpd.read_file(BOUNDARY)
    out = df[df.inside_district == False].copy()  # noqa: E712
    pts = gpd.GeoSeries(gpd.points_from_xy(out.lon, out.lat), crs=4326).to_crs(32644)
    poly = bnd.to_crs(32644).union_all() if hasattr(bnd, "union_all") else bnd.to_crs(32644).unary_union
    out["dist_m"] = [poly.distance(p) for p in pts]
    stack = G.build_criteria_stack(os.path.join(ROOT, "data"))
    mask, tr = stack["district_mask"], stack["transform"]
    rc = [rasterio.transform.rowcol(tr, x, y) for x, y in zip(out.lon, out.lat)]
    h, w = mask.shape
    out["in_mask_cell"] = [0 <= r < h and 0 <= c < w and bool(mask[r, c]) for r, c in rc]

    def summ(d):
        m = d["dist_m"]
        return pd.Series({"n": len(d), "q1 m": m.quantile(.25), "median m": m.median(),
                          "q3 m": m.quantile(.75), "max m": m.max(),
                          "≤ 500 m": f"{100 * (m <= 500).mean():.1f}%",
                          "≤ 1 km": f"{100 * (m <= 1000).mean():.1f}%",
                          "in a masked cell": int(d["in_mask_cell"].sum())})
    names = {}
    for line in open(os.path.join(ROOT, "data", "raw", "mgnrega", "dropdown_codes.tsv"), encoding="utf-8"):
        p = line.rstrip("\r\n").split("\t")
        if len(p) >= 3 and p[0] == "block":
            names[p[1]] = p[2]
    R.append(f"{len(out):,} points fall outside `data/boundary.geojson`. Distances are to the polygon "
             "in EPSG:32644 (UTM 44N).\n")
    R.append("**All**\n")
    R.append(md(summ(out).to_frame().T) + "\n")
    R.append("**Per requested block**\n")
    t = out.groupby("requested_block_code").apply(summ, include_groups=False)
    t.insert(0, "block", [names.get(i, "?") for i in t.index])
    R.append(md(t, index=True) + "\n")
    R.append("**Per stage**\n")
    R.append(md(out.groupby("stage").apply(summ, include_groups=False), index=True) + "\n")

    # Mask provenance
    sha = hashlib.sha256(open(BOUNDARY, "rb").read()).hexdigest()
    R.append("### Which boundary built the suitability mask\n")
    R.append(f"- `gis_analysis.build_criteria_stack` reads `os.path.join(data_dir, 'boundary.geojson')` "
             f"(gis_analysis.py:703) with `data_dir='data'`, i.e. **the same file**, "
             f"`data/boundary.geojson` (SHA-256 `{sha[:16]}…`). There is no other boundary input.")
    R.append(f"- It is rasterised with `all_touched=True` (gis_analysis.py:158), so the mask includes "
             f"every cell the polygon touches. Mask cells: {int(mask.sum()):,} (expected 123,555: "
             f"**{int(mask.sum()) == 123555}**). The mask therefore extends up to one cell (~0.3 km) "
             f"beyond the polygon edge, which is why **{int(out.in_mask_cell.sum()):,}** of the "
             f"{len(out):,} 'outside' points still fall in a masked cell and would receive a "
             "suitability score.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-photos", action="store_true")
    args = ap.parse_args()
    df = pd.read_parquet(PARQUET)
    head = ["# MGNREGA geotags: follow-up inspection\n",
            f"From `data/interim/mgnrega_all.parquet` ({len(df):,} records). No record "
            "filtered; no validation. Generated by `tools/inspect_mgnrega_2.py`.\n"]
    parts = {}
    for name, fn in (("2", spread), ("3", fy_spike), ("4", outside)):
        parts[name] = []
        fn(df, parts[name])
        print(f"done: {fn.__name__}", flush=True)
    parts["1"] = []
    photo_audit(df, not args.no_photos, parts["1"])
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    text = "\n".join(head + parts["1"] + parts["2"] + parts["3"] + parts["4"])
    with open(REPORT, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
