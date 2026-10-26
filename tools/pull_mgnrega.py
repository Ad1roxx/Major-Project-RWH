"""
tools/pull_mgnrega.py
─────────────────────
Pull MGNREGA accepted geotags for Chandrapur district from Bhuvan Bhugram and
save every response byte-for-byte. Nothing here filters, reformats or joins.

    python tools/pull_mgnrega.py

Requests: 15 blocks x 2 stages (0 = Phase I: Assets, 3 = Phase II: After),
then one block_code=All check per stage. One request at a time, 3 s apart;
one retry after 30 s on failure. Files that already exist are never
re-requested or overwritten.

Block, stage and category codes come from data/raw/mgnrega/dropdown_codes.tsv,
which was read from the portal's own dropdowns on 2026-10-04. Block codes are
NEVER generated from a numeric range: 1829007 does not exist and 1829016 does.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import shlex
import sys
import time
import urllib.parse

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path if os.path.abspath(p or os.getcwd()) != _HERE]
ROOT = os.path.dirname(_HERE)

import requests  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "mgnrega")
PORTAL = "https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/"
ENDPOINT = ("https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/php/"
            "reports/accepted_geotags.php")
STAGES = ["0", "3"]
STAGE_NAMES = {"0": "Phase I: Assets", "3": "Phase II: After"}
EXPECTED_BLOCKS = {
    "1829001": "CHANDRAPUR", "1829002": "BHADRAVATI", "1829003": "WARORA",
    "1829004": "CHIMUR", "1829005": "NAGBHIR", "1829006": "BRAHMAPURI",
    "1829008": "MUL", "1829009": "GONDPIPRI", "1829010": "RAJURA",
    "1829011": "SAOLI", "1829012": "BALLARPUR", "1829013": "KORPANA",
    "1829014": "SINDEWAHI", "1829015": "JIVTI", "1829016": "POMBHURNA",
}
SLEEP_S, RETRY_S, TIMEOUT_S = 3, 30, 180


def read_dropdowns():
    blocks, cats = {}, []
    with open(os.path.join(RAW, "dropdown_codes.tsv"), encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh, delimiter="\t"):
            if len(row) < 3:
                continue
            kind, code, name = (c.strip() for c in row[:3])
            if kind == "block" and code != "All":
                blocks[code] = name
            elif kind == "asset_category" and code not in ("All", ""):
                cats.append((code, name))
    assert len(blocks) == 15, f"expected 15 blocks, got {len(blocks)}: {blocks}"
    assert blocks == EXPECTED_BLOCKS, f"block list differs from expected: {blocks}"
    return blocks, cats


def form(stage: str, block: str, today: str) -> dict:
    return {
        "username": "unauthourized",   # sic: the portal's anonymous user
        "stage": stage, "state_code": "18", "district_code": "1829",
        "block_code": block, "panchayat_code": "All", "financial_year": "All",
        "accuracy": "0", "category_id": "All", "sub_category_id": "All",
        "start_date": "1998-09-30", "end_date": today,
    }


def curl_for(data: dict) -> str:
    return ("curl -sS -X POST " + shlex.quote(ENDPOINT) +
            " -H 'Content-Type: application/x-www-form-urlencoded'" +
            " --data " + shlex.quote(urllib.parse.urlencode(data)))


def row_count(path: str):
    try:
        with open(path, "rb") as fh:
            obj = json.loads(fh.read().decode("utf-8"))
        return len(obj) if isinstance(obj, list) else f"not a list ({type(obj).__name__})"
    except Exception as exc:          # report, never repair
        return f"unparseable: {exc.__class__.__name__}"


def fetch(data: dict, path: str, log: list, label: str):
    entry = {"label": label, "form": data, "file": os.path.relpath(path, ROOT).replace("\\", "/"),
             "curl": curl_for(data)}
    if os.path.exists(path):
        entry.update(status="SKIPPED (file exists)", timestamp=None,
                     bytes=os.path.getsize(path), rows=row_count(path))
        print(f"  {label}: exists, skipped ({entry['rows']} rows)")
        log.append(entry)
        return False
    for attempt in (1, 2):
        ts = dt.datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            r = requests.post(ENDPOINT, data=data, timeout=TIMEOUT_S)
            entry.update(timestamp=ts, status=r.status_code, attempt=attempt)
            if r.status_code == 200:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "wb") as fh:          # byte-for-byte
                    fh.write(r.content)
                entry.update(bytes=len(r.content), rows=row_count(path))
                print(f"  {label}: HTTP 200, {len(r.content):,} B, {entry['rows']} rows")
                log.append(entry)
                return True
            err = f"HTTP {r.status_code}"
        except Exception as exc:
            entry.update(timestamp=ts, status=f"ERROR {exc.__class__.__name__}: {exc}",
                         attempt=attempt)
            err = entry["status"]
        if attempt == 1:
            print(f"  {label}: {err}; retrying once in {RETRY_S} s")
            time.sleep(RETRY_S)
    entry.update(bytes=None, rows=None, failed=True)
    print(f"  {label}: FAILED after retry ({entry['status']})")
    log.append(entry)
    return True


def write_provenance(log: list, cats: list, today: str):
    with open(os.path.join(RAW, "pull_log.json"), "w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=1)
    L = ["# MGNREGA geotags — provenance", "",
         f"- **Portal:** {PORTAL}",
         f"- **Endpoint:** `POST {ENDPOINT}` (application/x-www-form-urlencoded, no login)",
         f"- **Pulled:** {today}, by `tools/pull_mgnrega.py`",
         "- **Codes:** stage, category and block codes were read from the portal's "
         "dropdowns and the browser Network payload on 2026-10-04 "
         "(`dropdown_codes.tsv`; categories also in `category_codes.csv`).",
         "- **Stages pulled:** 0 = Phase I: Assets (works started before 1 Nov 2017, "
         "tagged retrospectively); 3 = Phase II: After (geotag at completion). "
         "Stages 1 and 2 were not pulled.",
         "- Files are saved byte-for-byte as returned. Never edit them.",
         "- `observername` in these files is personal data: raw files only.", "",
         "## Requests", "",
         "| # | label | file | timestamp | HTTP | bytes | rows |",
         "|---|---|---|---|---|---|---|"]
    for i, e in enumerate(log, 1):
        L.append(f"| {i} | {e['label']} | `{e['file']}` | {e.get('timestamp') or '—'} | "
                 f"{e.get('status')} | {e.get('bytes') if e.get('bytes') is not None else '—'} | "
                 f"{e.get('rows') if e.get('rows') is not None else '—'} |")
    L += ["", "## Form data and equivalent curl, per request", ""]
    for i, e in enumerate(log, 1):
        L += [f"### {i}. {e['label']}", "", "```",
              urllib.parse.urlencode(e["form"]).replace("&", "\n"), "```", "",
              "```sh", e["curl"], "```", ""]
    with open(os.path.join(RAW, "PROVENANCE.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(L))


def main():
    blocks, cats = read_dropdowns()
    cat_path = os.path.join(RAW, "category_codes.csv")
    if not os.path.exists(cat_path):
        with open(cat_path, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["code", "name"])
            w.writerows(sorted(cats))
    today = dt.date.today().isoformat()
    log, first = [], True
    jobs = [(s, b) for s in STAGES for b in sorted(blocks)]
    jobs += [(s, "All") for s in STAGES]
    for stage, block in jobs:
        if block == "All":
            path = os.path.join(RAW, f"check_blockAll_stage{stage}.json")
            label = f"stage {stage} / block All (CHECK ONLY)"
        else:
            path = os.path.join(RAW, f"stage{stage}", f"{block}.json")
            label = f"stage {stage} / {block} {blocks[block]}"
        if not first and not os.path.exists(path):
            time.sleep(SLEEP_S)
        requested = fetch(form(stage, block, today), path, log, label)
        first = first and not requested
    write_provenance(log, cats, today)
    print(f"\nWrote {os.path.relpath(os.path.join(RAW, 'PROVENANCE.md'), ROOT)}")


if __name__ == "__main__":
    main()
