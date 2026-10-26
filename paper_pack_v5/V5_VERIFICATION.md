# Draft v5: verification of the "unverified numbers" and corrections to apply

Checked on 2026-10-20 by recomputing each value from the code and data
(`build_criteria_stack`, `score_stack`, `tools/ahp_audit.py`, `sensitivity.py`,
`consensus.py`, geometry in UTM 44N). Use this file together with the v5
change log.

## Corrections to make in v5 (four)

| Where | v5 says | Correct | Why |
|---|---|---|---|
| §1.2 study area | 19.459° and **20.731°**N | 19.459° and **20.730°**N | The boundary's top is 20.73046°N; rounded half-up to 3 dp that is 20.730 |
| §4.2.1 matrix audit | "among 200 of them scored through the pipeline every weight in Table 5 falls between the 40th and 63rd percentiles" | "every weight in Table 5 falls between the 40th and 63rd percentiles **of the 1,013 accepted matrices**. Scoring 200 of them through the pipeline gives a mean High share of 6.51% (SD 1.56, range 3.24–10.85) and keeps 7.7 of the top ten on average (minimum 4)." | The percentiles describe the weights of the 1,013 accepted matrices. The 200 pipeline runs measure the High share and site retention |
| §4.7, §5.11, Table B3 | CGWB proposes **417** structures (150 / 112 / **155**); AUC **0.361 [0.341, 0.383]**; shafts **0.336** | **418** structures (150 / 112 / **156**, as the report says); AUC **0.362 [0.341, 0.382]**; shafts **0.337** | One shaft row (#94) wrapped across two lines in the PDF and was missed by the parser. It is now included and the validation re-run. Unchanged: check dams 0.364, tanks 0.386, 70.3% in Low, 1.0% in High, 43.1%, 13 of 25 |
| §5.11 | "Of the proposed sites 70.3% fall on Low land … and 1.0% on High" | Unchanged; Medium moves 28.8% → 28.7% if quoted | — |

`CGWB_FINDINGS.md` saying "156" was right. The pack files now all agree on
418 / 156.

## Verified as printed in v5 (no change)

| Item | v5 value | Recomputed |
|---|---|---|
| Western, eastern, southern extent | 78.796°E, 79.989°E, 19.459°N | 78.796, 79.989, 19.459 |
| Mean in-district slope | 1.47° | 1.47° |
| River features; Strahler orders | 776; 1–7 | 776; 1–7 |
| Channel length; drainage density | 2,766 km; 0.242 km/km² | 2,765.6 km binned to cells, so 0.242. (Line geometry is 2,767.7 km, which §3.4 already states) |
| Population density | 2.8–8,507 persons/km², mean 206 | 2.8, 8,507, 206 |
| Settlement share at 400 persons/km² | 6.6% | 6.62% (area-weighted) |
| Rainfall on the grid | 1,189–1,714 mm/yr | 1,189–1,714 |
| Rim-fill shares | soil 2.2, population 2.0, slope 1.1, land cover 0.1% | Same (pipeline notes) |
| λmax, CI, CR | 6.1460, 0.0292, 0.0235 | 6.1460, 0.0292, 0.0235 |
| Matrix audit | 30 perturbations, worst CR 0.0336, order never changes; 4,000 drawn, 1,013 accepted; percentiles 40–63 | Same (`tools/ahp_audit.py`). Only the wording above needs correcting |
| Fuzzy-AHP weights | 0.417 / 0.224 / 0.159 / 0.097 / 0.062 / 0.041; max difference 0.012 | Same; max difference 0.0118 |
| Scenario CRs, High %, Low %, weight vectors (Table 13) | all values | All match |
| Class agreement with baseline | 87.17%, 99.0%, 87.3% | 87.17, 99.01, 87.30 |
| One-way perturbation | 87.5% mean, worst 60%, maximum rank shift 3 | 87.5, 60.0, 3 |
| Map removal: Sᵢ, Max, Mean \|ΔV\|, retained, High % (Table 17) | all values | All match |
| Level SD column (Table 18) | 9.33 / 5.92 / 3.39 / 2.92 / 4.22 / 2.26 | All match |
| Scenario consensus | 61 locations, 2 chosen by all five | 61, 2 |
| District within 5 km of the border | 24.4% | 24.4% |
| Sites within 5 km of the border; rank 1 | nine; 27 km inside | 9 (geometric distance to the outline); rank 1 at 27.3 km |

**Carried from records in the pack and repo, consistent with the code, not
recomputed here:**
- the step scheme on the corrected legend (13.61%, 46,224 distinct values):
  `supporting/PAPER_REVISIONS_v3_to_v4.md`;
- the CHIRPS −6,947 against 889.6 mm case: `CHANGELOG.md`, when the guard was
  added;
- the class-mean runoff coefficients (0.45–0.78 at 100 mm; 0.94–0.98 with
  annual totals): `supporting/PAPER_REVISIONS_v3_to_v4.md`;
- the Table 22 minima and maxima: `PAPER_REVISIONS` §5.10 and
  `PAPER_NUMBERS`;
- the Loam rank movements: `PAPER_REVISIONS` §0.1.

## Figures regenerated (printed cross-references now match v5 numbering)

- `fig04` (framework): "(Fig. 15)" is now "(Fig. 8)".
- `fig12` (effects, v5 Fig. 7): "see Fig. 21" is now "see Fig. A8". All
  plotted values are unchanged.
- `fig03` (preprocessing, v5 Fig. A1): "(Fig. 5)" is now "(Fig. A2)".

No other generated or QGIS figure prints a figure number. The rest appear
only in caption text.
