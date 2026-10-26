"""Builds the photo-confirmed structure set the browser map shows.

Reads the two returned label sheets, the blinding key and the MGNREGA table,
and writes to reports/photo_audit/map_layer/ (git-ignored, like the photos):

  confirmed_structures.csv   every photo either labeller marked storage or
                             recharge: rule "strict" (both did) or "lenient"
                             (one did), with category, stage and coordinates
  thumbs/<collection_sno>.jpg  a 320 px thumbnail for each STRICT structure,
                               the only ones the map embeds

The thumbnails were checked by eye on 2026-10-18: no people are visible. P098
carries a photographer's name watermark along its bottom edge, which is cropped
off. Lenient-only photos are not embedded: they include fields, a hand pump and
a house yard, and the map links them to Bhuvan instead.

    python tools/build_structure_layer.py
"""
import csv
import os

import pandas as pd
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUDIT = os.path.join(ROOT, "reports", "photo_audit")
OUT = os.path.join(AUDIT, "map_layer")
POSITIVE = {"storage", "recharge"}
# Fraction of the image height to crop from the bottom, by blinded ID.
CROP_BOTTOM = {"P098": 0.15}   # photographer's name watermark
THUMB_PX = 320


def _labels(name):
    path = os.path.join(AUDIT, "returned", name)
    return {r["random_id"].strip(): r["label"].strip().lower()
            for r in csv.DictReader(open(path, encoding="utf8"))}


def main():
    a, b = _labels("labels_A.csv"), _labels("labels_B.csv")
    key = {r["random_id"]: r for r in
           csv.DictReader(open(os.path.join(AUDIT, "blind", "key.csv"), encoding="utf8"))}
    df = pd.read_parquet(os.path.join(ROOT, "data", "interim", "mgnrega_all.parquet"),
                         columns=["collection_sno", "lat", "lon", "path1"])
    df["collection_sno"] = df["collection_sno"].astype(str)
    df = df.set_index("collection_sno")

    os.makedirs(os.path.join(OUT, "thumbs"), exist_ok=True)
    rows = []
    for rid in sorted(key):
        pa, pb = a.get(rid) in POSITIVE, b.get(rid) in POSITIVE
        if not (pa or pb):
            continue
        k = key[rid]
        sno = str(k["collection_sno"])
        rec = df.loc[sno]
        rule = "strict" if pa and pb else "lenient"
        rows.append({"collection_sno": sno, "rule": rule,
                     "category_seg": k["category_seg"], "stage": k["stage"],
                     "lat": float(rec["lat"]), "lon": float(rec["lon"]),
                     "label_a": a.get(rid), "label_b": b.get(rid),
                     "photo_url": rec["path1"]})
        if rule == "strict":
            im = Image.open(os.path.join(AUDIT, k["category_seg"], f"{sno}.jpg")).convert("RGB")
            crop = CROP_BOTTOM.get(rid)
            if crop:
                im = im.crop((0, 0, im.width, int(im.height * (1 - crop))))
            im.thumbnail((THUMB_PX, THUMB_PX))
            im.save(os.path.join(OUT, "thumbs", f"{sno}.jpg"), quality=72)
    pd.DataFrame(rows).to_csv(os.path.join(OUT, "confirmed_structures.csv"), index=False)
    n_strict = sum(r["rule"] == "strict" for r in rows)
    print(f"{len(rows)} confirmed ({n_strict} strict, {len(rows) - n_strict} lenient) "
          f"-> {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
