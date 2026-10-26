# paper_pack_v5 — everything needed to draft v5

Built 2026-10-20. It supersedes `paper_pack/` (v4), which is kept for history.

**To use:** give a fresh Claude this folder plus the v4 manuscript, and start
with `DRAFTING_BRIEF.md`.

| File | Purpose |
|---|---|
| `DRAFTING_BRIEF.md` | **Start here.** What changed since v4, section-by-section edits, rules, placeholders |
| `PAPER_NUMBERS.txt` | All model numbers (regenerated; identical to v4's) |
| `validation/VALIDATION_NUMBERS.txt` | All validation numbers, with provenance at the top |
| `validation/filter_ledger.csv`, `asset_types_kept.txt` | The presence-set filters and the category decisions |
| `validation/validation_summary.json` | Machine-readable validation results |
| `VALIDATION_FINDINGS.md` | What the validation shows, what it supports, what it can't claim, suggested wording |
| `FIGURE_INDEX.md` | All 28 figures: order, content, caption checklist, open items |
| `REVIEWER_RESPONSES.md` | Agreed answers: recharge vs storage, groundwater data, resolution, validation |
| `CGWB_FINDINGS.md` | **CGWB's view of Chandrapur, and how the model compares. Changes the objective framing** |
| `TABLE2_CODING.md` | Table 2 (criteria of the eight reviewed studies), checked against the papers |
| `DATA_PROVENANCE.md` | Every dataset, version, licence and citation |
| `figures/` | All figure PNGs, 300 dpi |
| `supporting/` | FIGURE_DATA (generated-figure captions), figure specs, photo protocol, soil-legend record, the v3→v4 edit list |

**Regenerate** (from the repo root):

```
python -P tools/paper_figures.py > paper_pack_v5/PAPER_NUMBERS.txt
python -P tools/validate_mgnrega.py
python -P tools/prep_map_layers.py
"C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" -P tools/qgis_figures.py <fig01|fig03|fig04|fig07|fig20|hydrology|fig_val_map>
```

The first three run in the venv; the last runs in QGIS's own Python.
