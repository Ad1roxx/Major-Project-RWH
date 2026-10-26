# Figure index — all figures, final files, review status, caption checklist

All files are in `figures/`, PNG at 300 dpi. For the generated set (`fig02`,
`fig05`, `fig06`, `fig08`–`fig19`, `fig21`, `fig22`), **take captions from
`supporting/FIGURE_DATA.md`**: they are computed and current, and unchanged
since v4. Every figure has passed external review and is publishable.

**File names are not paper numbers.** v4 numbered its figures by draft slot
(`supporting/PAPER_REVISIONS_v3_to_v4.md` §1). Renumber once for v5 and
keep this file as the key.

## Recommended order for v5

1. `fig01`: study area
2. **`fig04`: illustrated framework**, moved **ahead of** the preprocessing
   figure (overview before detail; candidate graphical abstract)
3. `fig03`: preprocessing chain
4. `fig05`, `fig02`, `fig06`: scoring forms, normalisation, criterion surfaces
5. `fig07`: the main suitability map
6. `fig08`, `fig09`: step vs ramp, dispersion
7. `fig10`–`fig14`, `fig12`, `fig21`, `fig22`: method comparison and the
   analyst-decision results (§5.3.5 in v4)
8. `fig15`, `fig16`: scenarios, consensus
9. `fig17`, `fig18`, `fig19`: sensitivity, level vs variance, correlation
10. `fig_hydrology`: hydrological surfaces (draft slot 18)
11. **New:** `fig_val_map`, `fig_val_roc`, `fig_val_gain`, `fig_val_scores`:
    agreement with recorded water works
12. `fig20`: model to field

`fig04_boxes` (the old box diagram) is for a supplement only.

## Figures new or remade since v4

| File | Content | Notes for the caption |
|---|---|---|
| `fig01` | (a) India, official Survey of India outline; (b) Maharashtra districts; (c) a 16 × 16-cell window of the analysis grid; (d) the district with 15 talukas, their headquarters, and six named rivers | 11,412.5 km² analysed against 11,443 km² official (99.7%). **Grid is 450 rows × 422 columns**; cell ≈ 0.30 km E–W × 0.31 km N–S. Credit the Survey of India (DataMeet, CC BY-SA 2.5), Census 2011 (via datta07/INDIAN-SHAPEFILES), HydroRIVERS, and © OpenStreetMap for the names |
| `fig03` | Seven sources → common grid (build, reproject, mask, fill, derive, score) → six criteria with weights | **Scoring sentence (must be exact):** fixed ramps for slope, drainage and settlement; class lookups for soil and land cover; **district-relative percentile for rainfall**. Never "fixed, literature-based breakpoints" for all. Sources: CHIRPS v3.0 2014–2024; HydroSHEDS 3″; SoilGrids250m (2017); MODIS MCD12Q1 v6.1, 2024; WorldPop 2020; HydroRIVERS v1.0 (vector, straight to derivation) |
| `fig04` | **Illustrated framework.** (a) Stage 1: raw inputs → grid → six scored criteria (magma). (b) Stage 2: judgement matrix → AHP / Fuzzy-AHP → weights; aggregate → classify; 2 × 2 method maps; baseline map with 25 sites. (c) What moves the High share. (d) Consensus. (e) Why rank 1 scores 0.957 | Name both palettes: scores in magma, classes in High/Medium/Low. The 2 × 2 runs **TOPSIS \| WLC** by **AHP \| Fuzzy-AHP**, and the outlined map is the baseline. ★ marks the three analyst decisions. (c): **ranges vs one swap vs main effects**, values from Fig 12, rounded (0.96, 0.56 = 0.957, 0.560). (d): consensus = agreement between methods, not correctness; 15 of 35 locations matched within 2 km. (e): every site carries this breakdown; exact score 0.9566, shortfall 0.043; soil segment = Loam, 0.38% of district. Scenarios are reported under AHP + WLC only. **Print on a full landscape page** |
| `fig07` | Main suitability map, 25 numbered sites; inset on rank 1 with the 5 km separation circle | High 6.44% (735.0 km²), Medium 52.48%, Low 41.08%; baseline AHP + WLC; Low ≤ 0.65 < Medium ≤ 0.85 < High. **Extraction (verified in code):** the best High cell per tile of a 5 × 5 grid, then the highest remaining High cells, all pairs ≥ 5 km apart. Only 12 tiles hold High land, so at least 13 sites come from the second step. Seven sites (4, 6, 9, 11, 13, 16, 17) lie in the north-central belt; the central block holds only rank 1, with ranks 2 and 5 on its edge. The box in (a) marks (b), and each scale bar applies to its own panel. Every site is on a High cell; some on patches smaller than the ring. Rank 1 at 79.6825°E, 20.3645°N, 0.957; sites run 0.957–0.854. Loam caveat: 4 of the top 5 sit on Loam, 0.38% of the district. UTM 44N |
| `fig_hydrology` | (a) Drainage density; (b) Curve Number in 7 classes, each with runoff Q, coefficient C and area | Q and C are fixed functions of CN for the 100 mm storm, so they share panel (b), not separate maps. CN 89 covers 62.6% of the district (70 mm of 100 mm runs off). Mean CN 85.97, Q 63.65 mm, C 0.637. Drainage ramp stretched to its 2nd–98th percentile. Replaces draft slot 18 (**not** the generated `fig18`) |
| `fig20` | Model to field: "This study" (GIS-MCDA → consensus screening) against "Not done" (field reconnaissance → … → final siting) | "15 sites picked by all 4 methods": each method's 25-site shortlist matched within 2 km; 15 of 35 locations in all four. **Different from Fig 22's "22 of 25".** 528.5 km² High under all four (Fig 16 prints 528; say which is rounded). Consensus = agreement between methods, not correctness |
| `fig_val_roc` | ROC curves, four methods, baseline; AUC with 95% CI in the legend | See `VALIDATION_FINDINGS.md`. Presences = 3,119 MGNREGA works in the water categories; 10,000 random background cells; 2,000 bootstraps; seed 42 |
| `fig_val_scores` | Score distributions, works vs background, per method, with the 0.65 / 0.85 lines | TOPSIS axis is the closeness coefficient, a different quantity from the WLC score |
| `fig_val_gain` | % of area vs % of works per class, four methods, with ratios | High 1.93×, Low 0.52× (AHP + WLC) |
| `fig_val_map` | Works over the baseline classified map, with block and district boundaries | Works are category segments, not verified structures (photo audit 17–50%). Block lines drawn from Census 2011 talukas |

## Generated set (unchanged since v4)

| File | Content (v4 slot) | Caption notes added by review |
|---|---|---|
| `fig02` | Normalisation families (2) | — |
| `fig05` | Scoring forms, six panels (5) | — |
| `fig06` | Six criterion surfaces (6) | Uses viridis. **Open decision:** switch to magma to match Fig 4 |
| `fig08` | Step vs ramp, two legends (8) | 973 and 18.51% are historical reconstructions only |
| `fig09` | Parallel coordinates / dispersion (9) | — |
| `fig10` | Four method surfaces (10) | — |
| `fig11` | Factorial interaction (11) | — |
| `fig12` | Effect magnitudes: analyst decisions vs algorithm (new in v4) | Cutoff bar = range over 4 schemes, 36.43 pp; +26.53 is valid only as the single fixed-vs-tercile comparison |
| `fig13` | ECDF + alluvial (12) | 87.17% unchanged, area-weighted |
| `fig14` | Difference map (13) | — |
| `fig15` | Scenario shares (14) | Scenarios run under AHP + WLC |
| `fig16` | Agreement rasters (15) | 528 km² vs 528.5: state the rounding |
| `fig17` | Perturbation, map removal (16) | Three *complementary* sensitivity analyses in Methods: ±20% perturbation, map removal, level/variance decomposition |
| `fig18` | Level vs variance (17) | 42.8 / 36.9 / 9.7; soil ratio 0.63×; soil and slope tie at 9.7% |
| `fig19` | Correlation heatmap (19) | — |
| `fig21` | Ranking vs cutoff partition (new in v4) | 50.3%; 6.457 / 6.376 / 3.445 pp |
| `fig22` | Stability vs suitability (new in v4) | Band 0.817–0.889; 22 of 25 unanimous; ranks 23–25 are not marked on Fig 7 |

## Set-wide, still open

- **Print text size.** Small labels are 5–6 pt at 174 mm in Figs 1, 4, 7 and
  the QGIS figures. Once the target journal is chosen, raise every figure to
  its minimum in one pass (`tools/qgis_figures.py`, `tools/make_figures.py`).
- **Fig 6 palette:** magma or viridis.
- **Captions** must be reviewed as a set against `supporting/FIGURE_DATA.md`
  and this file.
