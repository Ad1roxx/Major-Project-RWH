"""
tools/inspect_mgnrega.py
────────────────────────
Read the raw MGNREGA geotag pulls, write one inspection table and a report.
NO filtering, thresholding, category selection or validation happens here.

    python tools/inspect_mgnrega.py

Inputs : data/raw/mgnrega/stage{0,3}/<block>.json, check_blockAll_stage*.json,
         pull_log.json, data/boundary.geojson
Outputs: data/interim/mgnrega_all.parquet   (every record, observername dropped)
         data/interim/mgnrega_coord_rejects.csv
         reports/mgnrega_inspection.md

observername is personal data. It is read only to be dropped, and it appears
in no output, table or report.
"""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
ROOT = os.path.dirname(_HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "mgnrega")
INTERIM = os.path.join(ROOT, "data", "interim")
REPORTS = os.path.join(ROOT, "reports")
BOUNDARY = os.path.join(ROOT, "data", "boundary.geojson")
STAGES = ["0", "3"]
STAGE_NAMES = {"0": "Phase I: Assets", "3": "Phase II: After"}
LAT_RANGE, LON_RANGE = (19.0, 21.5), (78.5, 80.5)
EXPECTED_FIELDS = {"collection_sno", "assetid", "workcode", "serial_no", "accuracy",
                   "creationtime", "gpname", "lat", "lon", "observername",
                   "path1", "path2"}
PERSONAL = {"observername"}

FY_RE = re.compile(r"/((?:19|20)\d{2})-((?:19|20)\d{2})/")
PHOTO_RE = re.compile(r"_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{4})\.[A-Za-z]{3,4}$")


def _in(v, rng):
    return v is not None and not np.isnan(v) and rng[0] <= v <= rng[1]


def _f(x):
    try:
        return float(str(x).strip())
    except Exception:
        return np.nan


def load():
    names = {}
    for line in open(os.path.join(RAW, "dropdown_codes.tsv"), encoding="utf-8"):
        p = line.rstrip("\r\n").split("\t")
        if len(p) >= 3 and p[0] == "block" and p[1] != "All":
            names[p[1]] = p[2]
    rows, field_sets, file_rows = [], Counter(), {}
    for s in STAGES:
        for path in sorted(glob.glob(os.path.join(RAW, f"stage{s}", "*.json"))):
            block = os.path.splitext(os.path.basename(path))[0]
            data = json.loads(open(path, "rb").read().decode("utf-8"))
            if not isinstance(data, list):
                raise SystemExit(f"{path}: response is not a JSON array")
            file_rows[(s, block)] = len(data)
            for rec in data:
                field_sets[frozenset(rec)] += 1
                r = {k: v for k, v in rec.items() if k not in PERSONAL}
                r["stage"], r["requested_block_code"] = s, block
                rows.append(r)
    return pd.DataFrame(rows), field_sets, file_rows, names


def derive(df: pd.DataFrame):
    a = df["lat"].map(_f)          # field NAMED lat
    b = df["lon"].map(_f)          # field NAMED lon
    swapped = a.map(lambda v: _in(v, LON_RANGE)) & b.map(lambda v: _in(v, LAT_RANGE))
    named = a.map(lambda v: _in(v, LAT_RANGE)) & b.map(lambda v: _in(v, LON_RANGE))
    df["orientation"] = np.where(swapped, "swapped", np.where(named, "as-named", "neither"))
    df["raw_lat_field"], df["raw_lon_field"] = df["lat"], df["lon"]
    df["lat"] = np.where(swapped, b, np.where(named, a, np.nan))
    df["lon"] = np.where(swapped, a, np.where(named, b, np.nan))

    seg = df["workcode"].fillna("").str.split("/")
    df["workcode_segments"] = seg.map(len)
    df["location_code"] = seg.map(lambda x: x[0] if len(x) > 0 else None)
    df["category_seg"] = seg.map(lambda x: x[1] if len(x) > 1 else None)
    df["serial_seg"] = seg.map(lambda x: x[-1] if len(x) > 2 else None)
    # Literal third segment of 4-segment workcodes (e.g. "IAY"). Reported as
    # found; not interpreted as a sub-category.
    df["third_seg"] = seg.map(lambda x: x[2] if len(x) == 4 else None)
    df["location_level"] = df["location_code"].map(
        lambda c: "block" if c and c.isdigit() and len(c) == 7
        else "panchayat" if c and c.isdigit() and len(c) == 10 else "other")
    slen = df["serial_seg"].fillna("").str.len()
    modal = int(slen[slen > 0].mode().iloc[0]) if (slen > 0).any() else 0
    df["serial_len"] = slen
    df["serial_irregular"] = (slen != modal) | ~df["serial_seg"].fillna("").str.isdigit() \
        | (df["workcode_segments"] != 3)

    def fy(p):
        m = FY_RE.search(str(p or ""))
        return f"{m.group(1)}-{m.group(2)}" if m and int(m.group(2)) == int(m.group(1)) + 1 else None
    df["fy_from_path"] = df["path1"].map(fy)

    def ptime(p):
        m = PHOTO_RE.search(str(p or ""))
        if not m:
            return pd.NaT
        hh, mi, ss, dd, mo, yy = map(int, m.groups())
        try:
            return pd.Timestamp(year=yy, month=mo, day=dd, hour=hh, minute=mi, second=ss)
        except ValueError:
            return pd.NaT
    df["photo_time"] = df["path1"].map(ptime)
    miss = df["photo_time"].isna()
    df.loc[miss, "photo_time"] = df.loc[miss, "path2"].map(ptime)
    # Two formats occur (with and without microseconds); "mixed" parses both.
    df["creationtime_parsed"] = pd.to_datetime(df["creationtime"], errors="coerce",
                                               format="mixed")
    # Three photo URL layouts occur. Two carry an FY segment; the third
    # (.../photos_comp2/<n>/<n>/...) does not, and accounts for every stage-0
    # record without a parseable fy_from_path.
    def _layout(u):
        if "/photos_comp2/" in u:
            return ("photos_comp2/<stage>/<FY>/..." if FY_RE.search(u)
                    else "photos_comp2/<n>/<n>/... (no FY segment)")
        return "photos/<stage>/<YYYY-MM>/<FY>/..." if "/photos/" in u else "other"
    df["path_layout"] = df["path1"].fillna("").map(_layout)
    df["accuracy_m"] = df["accuracy"].map(_f)
    return df, modal


def md_table(df, index=True):
    """Plain markdown table; no tabulate dependency."""
    d = df.reset_index() if index else df
    def cell(v):
        if isinstance(v, float):
            return "" if np.isnan(v) else (f"{v:,.2f}" if v % 1 else f"{int(v):,}")
        if isinstance(v, (int, np.integer)):
            return f"{int(v):,}"
        return "" if v is None or (isinstance(v, float) and np.isnan(v)) else str(v)
    head = "| " + " | ".join(str(c) for c in d.columns) + " |"
    sep = "|" + "---|" * len(d.columns)
    body = ["| " + " | ".join(cell(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join([head, sep] + body)


def main():
    os.makedirs(INTERIM, exist_ok=True)
    os.makedirs(REPORTS, exist_ok=True)
    df, field_sets, file_rows, names = load()
    df, modal_serial = derive(df)
    contradictions, R = [], []
    add = R.append
    total = len(df)

    # ── fields ──────────────────────────────────────────────────────────────
    all_fields = set().union(*field_sets) if field_sets else set()
    extra, missing = sorted(all_fields - EXPECTED_FIELDS), sorted(EXPECTED_FIELDS - all_fields)
    if extra or missing:
        contradictions.append(f"Field set differs from the documented 12: extra {extra}, "
                              f"missing {missing}.")
    if len(field_sets) > 1:
        contradictions.append(f"Records do not all share one field set ({len(field_sets)} variants).")

    add("# MGNREGA geotags, Chandrapur: inspection report\n")
    add(f"Generated by `tools/inspect_mgnrega.py` from the raw pulls in `data/raw/mgnrega/` "
        f"(provenance: `data/raw/mgnrega/PROVENANCE.md`). **No record has been filtered.** "
        f"`observername` is excluded from this report and from every processed output.\n")
    add(f"Total records: **{total:,}** (stage 0: {int((df.stage == '0').sum()):,}; "
        f"stage 3: {int((df.stage == '3').sum()):,}).\n")
    add(f"Fields present: {', '.join(sorted(all_fields - PERSONAL))} (+ observername, dropped).\n")

    # ── 1. rows per block per stage ────────────────────────────────────────
    add("## 1. Rows per block per stage\n")
    t = pd.DataFrame([{"block_code": b, "block": names.get(b, "?"),
                       **{f"stage {s}": file_rows.get((s, b)) for s in STAGES}}
                      for b in sorted(names)])
    t["total"] = t[[f"stage {s}" for s in STAGES]].sum(axis=1)
    tot = {"block_code": "TOTAL", "block": "", **{c: int(t[c].sum()) for c in t.columns[2:]}}
    t = pd.concat([t, pd.DataFrame([tot])], ignore_index=True)
    add(md_table(t, index=False) + "\n")
    zeros = [(b, s) for b in names for s in STAGES if file_rows.get((s, b)) == 0]
    missing_files = [(b, s) for b in names for s in STAGES if (s, b) not in file_rows]
    add(f"Blocks with zero rows: {', '.join(f'{b} {names[b]} (stage {s})' for b, s in zeros) or 'none'}.")
    add(f"Missing response files: {', '.join(f'{b} (stage {s})' for b, s in missing_files) or 'none'}.\n")

    # block=All check
    add("### block_code=All check (not used as data)\n")
    for s in STAGES:
        p = os.path.join(RAW, f"check_blockAll_stage{s}.json")
        per_block = sum(v for (st, _b), v in file_rows.items() if st == s)
        if os.path.exists(p):
            try:
                obj = json.loads(open(p, "rb").read().decode("utf-8"))
                n = len(obj) if isinstance(obj, list) else None
            except Exception as exc:
                n = f"unparseable ({exc.__class__.__name__})"
            eq = (n == per_block)
            add(f"- Stage {s}: block=All returned **{n}** rows; sum of 15 per-block files = "
                f"{per_block:,}; equal: **{eq}**.")
            if isinstance(n, int) and not eq:
                contradictions.append(f"Stage {s}: block=All gives {n:,} rows, per-block sum {per_block:,}.")
        else:
            add(f"- Stage {s}: check file missing.")
    add("")

    # ── 2. request consistency ─────────────────────────────────────────────
    add("## 2. Request consistency\n")
    bad = ~df.apply(lambda r: str(r["location_code"] or "").startswith(r["requested_block_code"]), axis=1)
    add(f"Records whose workcode location code does not start with the requested block code: "
        f"**{int(bad.sum()):,}** of {total:,}.")
    if bad.any():
        x = df[bad].groupby(["stage", "requested_block_code"]).size().rename("n").reset_index()
        add("\n" + md_table(x, index=False))
        nonstd = bad & (df["location_level"] == "other")
        other_blk = bad & ~nonstd
        add(f"\nOf these, **{int(nonstd.sum()):,}** have a non-standard workcode (no 7- or "
            f"10-digit location code; examples: "
            + ", ".join(f"`{w}`" for w in df.loc[nonstd, "workcode"].drop_duplicates().head(10))
            + f") and **{int(other_blk.sum()):,}** name a different block:\n")
        xb = df[other_blk].assign(named_block=df.loc[other_blk, "location_code"].str[:7]) \
            .groupby(["requested_block_code", "named_block"]).size().rename("n").reset_index()
        add(md_table(xb, index=False))
        contradictions.append(f"{int(other_blk.sum())} records with a well-formed workcode sit in "
                              "a block file other than the block their workcode names; "
                              f"{int(nonstd.sum())} more have non-standard workcodes.")
    add(f"\nLocation level: " + ", ".join(f"{k} {v:,}" for k, v in
                                          df["location_level"].value_counts().items()) + ".")
    add(f"Workcode segment counts: " + ", ".join(f"{k} segments: {v:,}" for k, v in
                                                 sorted(df["workcode_segments"].value_counts().items())) + ".\n")

    # ── 3. categories ──────────────────────────────────────────────────────
    add("## 3. Category segment per stage\n")
    c = df.groupby(["category_seg", "stage"]).size().unstack(fill_value=0)
    c["total"] = c.sum(axis=1)
    add(md_table(c.sort_values("total", ascending=False)) + "\n")
    cat_fields = [f for f in all_fields if "categ" in f.lower()]
    if cat_fields:
        add(f"Category fields present: {cat_fields}. Breakdown for 01, 02, 09:\n")
        for f in cat_fields:
            add(md_table(df[f].value_counts().rename("n").to_frame()) + "\n")
    else:
        add("**No record carries a category or sub-category field.** The only category "
            "information is the workcode's second segment above. Codes 01 / 02 / 09 cannot be "
            "reported and sub-categories have not been inferred.\n")
    t4 = df["third_seg"].value_counts()
    add(f"4-segment workcodes ({int((df.workcode_segments == 4).sum()):,}): literal third segment "
        + ", ".join(f"`{k}` {v:,}" for k, v in t4.items())
        + "; second segment " + ", ".join(
            f"{k} {v:,}" for k, v in
            df.loc[df.workcode_segments == 4, "category_seg"].value_counts().items())
        + ". Reported as found, not interpreted.\n")
    add(f"Serial segment (last segment): modal length {modal_serial}; flagged irregular (other length, non-digit, "
        f"or not 3 workcode segments): **{int(df.serial_irregular.sum()):,}**. Length distribution: "
        + ", ".join(f"{k}: {v:,}" for k, v in sorted(df["serial_len"].value_counts().items())) + ".\n")

    # ── 4. duplicates ──────────────────────────────────────────────────────
    add("## 4. Duplicates\n")
    for s in STAGES:
        d = df[df.stage == s]
        wc = d["workcode"].duplicated(keep=False)
        ai = d["assetid"].duplicated(keep=False)
        add(f"- Stage {s}: records sharing a workcode **{int(wc.sum()):,}** "
            f"({d.loc[wc, 'workcode'].nunique():,} distinct workcodes); records sharing an assetid "
            f"**{int(ai.sum()):,}** ({d.loc[ai, 'assetid'].nunique():,} distinct assetids).")
    both = set(df.loc[df.stage == "0", "workcode"]) & set(df.loc[df.stage == "3", "workcode"])
    add(f"- Workcodes present in both stage 0 and stage 3: **{len(both):,}**.\n")

    # ── 5. coordinates ─────────────────────────────────────────────────────
    add("## 5. Coordinates\n")
    oc = df["orientation"].value_counts()
    add("Orientation, assigned by value range (lat 19.0–21.5, lon 78.5–80.5), never by field name:\n")
    for k in ("swapped", "as-named", "neither"):
        add(f"- {k}: **{int(oc.get(k, 0)):,}**")
    if oc.get("as-named", 0):
        contradictions.append(f"{int(oc['as-named'])} records have lat/lon as named, "
                              "not swapped as documented.")
    rej = df[df.orientation == "neither"][["stage", "requested_block_code", "assetid", "workcode",
                                           "raw_lat_field", "raw_lon_field"]]
    rej.to_csv(os.path.join(INTERIM, "mgnrega_coord_rejects.csv"), index=False)
    add(f"\nRejects ({len(rej):,}) logged with raw values to `data/interim/mgnrega_coord_rejects.csv`.\n")

    import geopandas as gpd
    bnd = gpd.read_file(BOUNDARY).to_crs(4326)
    ok = df["lat"].notna()
    pts = gpd.GeoDataFrame(df[ok][["stage", "requested_block_code"]],
                           geometry=gpd.points_from_xy(df.loc[ok, "lon"], df.loc[ok, "lat"]), crs=4326)
    inside = pts.within(bnd.union_all() if hasattr(bnd, "union_all") else bnd.unary_union)
    df["inside_district"] = pd.Series(pd.NA, index=df.index, dtype="boolean")
    df.loc[ok, "inside_district"] = inside.values
    add(f"District boundary: `data/boundary.geojson` (GADM ADM2, EPSG:4326). Of {int(ok.sum()):,} "
        f"resolvable points: inside **{int(inside.sum()):,}**, outside **{int((~inside).sum()):,}**.\n")
    ib = df[ok].groupby(["requested_block_code", "stage"])["inside_district"] \
        .agg(inside="sum", n="size").reset_index()
    ib["outside"] = ib["n"] - ib["inside"]
    ib["block"] = ib["requested_block_code"].map(names)
    add(md_table(ib[["requested_block_code", "block", "stage", "n", "inside", "outside"]], index=False) + "\n")

    # ── 6. accuracy ────────────────────────────────────────────────────────
    add("## 6. Accuracy (m, as reported)\n")
    acc = []
    for s in STAGES:
        a = df.loc[df.stage == s, "accuracy_m"]
        q = a.quantile([0, .25, .5, .75, 1.0])
        acc.append({"stage": s, "n": int(a.notna().sum()), "unparseable": int(a.isna().sum()),
                    "min": q[0], "q1": q[.25], "median": q[.5], "q3": q[.75], "max": q[1.0],
                    ">10 m": int((a > 10).sum()), ">20 m": int((a > 20).sum()),
                    ">50 m": int((a > 50).sum())})
    add(md_table(pd.DataFrame(acc).round(2), index=False) + "\n")
    add("Observation: no record reports more than 20 m, although the request sent "
        "accuracy=0. The values look capped or pre-filtered at 20 m by the portal.\n")

    # ── 7. time ────────────────────────────────────────────────────────────
    add("## 7. Time\n")
    for s in STAGES:
        d = df[df.stage == s]
        ct, pt = d["creationtime_parsed"], d["photo_time"]
        add(f"**Stage {s} ({STAGE_NAMES[s]})**\n")
        add(f"- creationtime: {ct.min()} → {ct.max()} (unparseable {int(ct.isna().sum()):,})")
        add(f"- photo_time (filename): {pt.min()} → {pt.max()} (unparseable {int(pt.isna().sum()):,})")
        both_t = ct.notna() & pt.notna()
        diff = (ct[both_t] - pt[both_t]).abs()
        add(f"- photo_time vs creationtime, where both parse ({int(both_t.sum()):,}): identical "
            f"{int((diff == pd.Timedelta(0)).sum()):,}; within 1 h {int((diff <= pd.Timedelta(hours=1)).sum()):,}; "
            f"within 1 day {int((diff <= pd.Timedelta(days=1)).sum()):,}; more than 1 day apart "
            f"**{int((diff > pd.Timedelta(days=1)).sum()):,}**")
        add(f"- photo_time before 2005 (implausible for MGNREGA geotagging; likely a device "
            f"clock): **{int((pt < pd.Timestamp('2005-01-01')).sum()):,}**")
        add("- path1 layout: " + ", ".join(f"{k} {v:,}" for k, v in
                                           d["path_layout"].value_counts().items()))
        fyv = d["fy_from_path"]
        add(f"- fy_from_path parseable: **{int(fyv.notna().sum()):,}** of {len(d):,}. Distribution:\n")
        add(md_table(fyv.value_counts(dropna=False).sort_index().rename("n").to_frame()) + "\n")
    stage0_after = df[(df.stage == "0") & (df.fy_from_path.notna())]["fy_from_path"] \
        .map(lambda x: int(x[:4]) >= 2018).sum()
    if stage0_after:
        contradictions.append(f"{int(stage0_after)} stage-0 records (works said to start before "
                              "1 Nov 2017) carry a fy_from_path of 2018-19 or later. fy_from_path "
                              "is unverified, so this is a flag, not a finding.")

    # ── 8. contradictions ──────────────────────────────────────────────────
    add("## 8. Contradictions with the task CONTEXT\n")
    add("\n".join(f"- {c}" for c in contradictions) if contradictions else "- None found.")
    add("")

    # ── outputs ────────────────────────────────────────────────────────────
    keep = [c for c in df.columns if c not in PERSONAL]
    out = df[keep].copy()
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].astype("string")
    out.to_parquet(os.path.join(INTERIM, "mgnrega_all.parquet"), index=False)
    with open(os.path.join(REPORTS, "mgnrega_inspection.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(R))
    print("\n".join(R))
    print(f"\nWrote data/interim/mgnrega_all.parquet ({len(out):,} rows, {len(out.columns)} cols), "
          "data/interim/mgnrega_coord_rejects.csv, reports/mgnrega_inspection.md")


if __name__ == "__main__":
    main()
