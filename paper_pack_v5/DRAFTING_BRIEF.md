# Drafting brief — RWH GIS-MCDA paper, draft v5

**You are revising a journal manuscript.** Draft v4 (attach it, as `.tex` or
PDF) is current on every model result. Since v4 the project has added:

- **a validation** against recorded MGNREGA water works, with a blinded
  photo audit;
- **all remaining figures**, including a new illustrated central figure;
- **new data provenance**: MODIS year, talukas, the official India outline;
- **answers to reviewer questions** on the objective, groundwater data and
  resolution.

Produce draft v5: v4's structure, voice and numbers, plus everything below.
**No model result has changed.** `PAPER_NUMBERS.txt` was regenerated on
2026-10-20 and is identical to v4's.

---

## 1. Attachments, in order of authority

| File | What it is | How to use it |
|---|---|---|
| `PAPER_NUMBERS.txt` | Live output of `tools/paper_figures.py` | **Highest authority for any model number** |
| `validation/VALIDATION_NUMBERS.txt` | Live output of `tools/validate_mgnrega.py` | **Highest authority for any validation number** |
| `VALIDATION_FINDINGS.md` | What the validation shows, what it can't claim, and suggested wording | Write the validation Methods, Results and Discussion from this |
| `FIGURE_INDEX.md` | Every figure: file, content, recommended order, caption checklist | Build captions and numbering from this |
| `supporting/FIGURE_DATA.md` | Values and final captions of the 17 generated figures | Captions for those figures, and **equal authority for any value plotted in them** (e.g. Fig 12 effects 36.43 / 31.21 / 16.23 pp, 528.5 km²) |
| `REVIEWER_RESPONSES.md` | Agreed answers on recharge vs storage, groundwater data, resolution and validation | Fold into Introduction, Methods, Discussion and Limitations |
| `CGWB_FINDINGS.md` | What CGWB says about Chandrapur, the comparison with the model, and the objective decision | **Changes the objective framing.** Read before §1 and the Discussion |
| `TABLE2_CODING.md` | Table 2 checked against the eight papers | Replace v4's Table 2 claims |
| `DATA_PROVENANCE.md` | Every dataset, version, licence, citation | Data section and reference list |
| `figures/` | All figures (28 PNG) | Check that each caption describes what is drawn |
| `supporting/` | v3→v4 edit list, soil-legend record, photo protocol, figure specs | Reference only; already applied to v4 |
| v4 manuscript | The current text | Keep its structure and argument |

If a number appears in v4 but in none of those three files, list it under
"Unverified numbers" (§6). If v4 and the attachments disagree on any number,
the attachments win.

---

## 2. What changed since v4

**New data and findings**
1. **Validation against MGNREGA water works.** 3,119 works in the water
   category segments (WC, WH) were compared with 10,000 random district cells
   on all 20 surfaces.
   - **Agreement:** baseline AUC 0.661 [0.650, 0.672]; the range across all
     20 surfaces is 0.629–0.715, and every CI is above 0.5.
   - **Classes:** High land holds 1.93× its area share of works, Low 0.52×.
   - **Robustness:** it holds under thinning, settlement removal and a
     cropland-only test; the negative control gives 0.496.
   - **Reading:** a *lower bound*, because most works in those categories
     aren't harvesting structures. This is **not** accuracy.

   Details in `VALIDATION_FINDINGS.md`.
2. **Photo audit.** 240 blinded photos, two labellers.
   - Agreement κ = 0.459.
   - The water categories hold harvesting structures in 17% of photos
     (strict) to 47–50% (lenient).
   - No category passed the inclusion rule.
   - Declare four protocol deviations (`VALIDATION_FINDINGS.md` §2.6).
3. **The validation echoes the thesis.** Weighting judgements (scenario)
   move AUC by 0.049, aggregation by about 0.03, and weighting method by
   0.002. Analyst decisions matter most here too.
4. **Land cover year found:** MODIS MCD12Q1 v6.1, **2024** product. The
   other sources are verified too (`DATA_PROVENANCE.md`).
5. **Talukas:** 15 Census 2011 talukas, used in Fig 1 and the validation
   map.

**Facts established while building figures** (use these wordings)
- **Grid:** **450 rows × 422 columns**; one cell ≈ **0.30 km E–W × 0.31 km
  N–S** (≈0.092 km²). Any "0.31 × 0.30 km" in v4 is N–S × E–W; restate it
  with directions.
- **Candidate extraction (verified in code):**
  - the best High cell in each tile of a 5 × 5 grid over the bounding box;
  - then the highest-scoring remaining High cells;
  - every pair ≥ 5 km apart, both stages;
  - sites then ranked by score.

  Only 12 of 25 tiles hold High land, so at least 13 of 25 sites come from
  the second step.
- **Scoring forms:**
  - fixed ramps for slope, drainage and settlement;
  - class lookups for soil and land cover;
  - **district-relative percentile** for rainfall (floor 0.20).

  Never describe all criteria as "fixed, literature-based breakpoints".
- **Scenarios** are compared under **AHP + WLC only**. The other three
  methods are compared under the baseline judgements only.
- **Rank 1:** exact score **0.9566** (printed 0.957), shortfall from 1 =
  **0.043**.
- **Hydrology:** runoff depth Q and coefficient C are fixed functions of the
  Curve Number for the 100 mm storm. CN 89 covers **62.6%** of the district.

**Figures**
- **All figures now exist,** 28 files. See `FIGURE_INDEX.md` for every
  caption item.
- **Fig 4 is replaced** by an illustrated framework built from real
  outputs. It carries the thesis: ★ marks the analyst decisions, and
  panel (c) is a miniature of Fig 12. Put it **before** the preprocessing
  figure, on a full landscape page.
- **New validation figures:** `fig_val_map`, `fig_val_roc`, `fig_val_gain`,
  `fig_val_scores`.

---

## 3. Section-by-section edits

**Abstract**
- **Replace** "no accuracy metric is reported" with the validation sentence
  in `VALIDATION_FINDINGS.md` §5. Keep the word *accuracy* out of any claim.
- **Keep** the analyst-decision thesis, and add one clause that validation
  agreement shows the same ordering.

**§1 Introduction**
- **Objective:** **surface rainwater-harvesting suitability**, with
  recharge as one use of harvested water (framing (A), `CGWB_FINDINGS.md`
  §3, pending the authors' decision; use the replacement paragraph in
  `REVIEWER_RESPONSES.md` §1). **Do not** call it "recharge-oriented"
  or claim Chandrapur's groundwater is declining district-wide: CGWB rates
  it Safe (19.35%).
- **Justification:** runoff loss, not rainfall shortage, with runoff
  coefficient 0.637 and CN 89 on 62.6% of the district.
- **Contributions:** add the validation and the photo audit.

**Study area / data**
- **Talukas:** the district has 15 talukas, shown in Fig 1(d).
- **Versions:** every source with its version and year (`DATA_PROVENANCE.md`).
- **Fig 1 outline:** the India outline is the official Survey of India one.

**Methods**
- **Grid:** state rows × columns once.
- **Scoring:** use the exact scoring-forms sentence (§2 above).
- **Extraction:** state the procedure (§2 above).
- **Hydrology:** note that Q and C follow from CN.
- **New subsection, "Agreement with recorded water works":**
  - **Data:** source, pull and filter ledger, with its table.
  - **Photo audit:** the protocol, κ, the strict rule, and the four
    deviations.
  - **Background:** 10,000 uniform random cells, excluding presence
    neighbourhoods, seed 42.
  - **Metrics:** ROC AUC with 2,000 bootstraps, paired bootstrap and DeLong,
    PR AUC, Boyce, the gain table.
  - **Robustness:** 1 km thinning, settlement removal, single criteria,
    cropland-only, photo-confirmed subsets, negative control.
- **Deviations from the original validation plan:** no asset-type or
  status field; PNG only (`VALIDATION_FINDINGS.md` §4).

**Results**
- **New subsection** with the headline table, gain table, method and
  scenario comparison, and robustness (`VALIDATION_FINDINGS.md` §2), citing
  the four validation figures.
- **Placement of Fig 4:** introduce it early, as the overview.

**Discussion**
- **Validation:** what it supports, and what it can't claim
  (`VALIDATION_FINDINGS.md` §5).
- **The farmland caution:** the scenario's higher AUC reflects the cropland
  bias of the works, not better siting.
- **Within-cropland equivalence:** the methods tie on cropland, so the
  WLC–TOPSIS gap arises outside cropland.
- **Reviewer answers:** objective framing, surface proxies, and resolution
  (`REVIEWER_RESPONSES.md` §§1–3).
- **New paragraph, surface suitability against aquifer capacity**
  (`CGWB_FINDINGS.md`):
  - CGWB's recharge-infeasible blocks hold 43.1% of the High zone and
    13 of the top 25 sites;
  - its 418 proposed recharge structures score AUC 0.362 on the baseline;
  - 70.3% of them fall in Low.
  - Contrast this with the MGNREGA agreement (0.661): built works match the
    model, aquifer-capacity siting doesn't.
- **Table 2 sentence:** replace with the one in `TABLE2_CODING.md`. Note that
  settlement proximity appears in only 2 of 8 studies, and Alene et al. score
  clay highest (storage logic).

**Limitations**
- **Replace** "validation has not been run" with:
  - presence-only data;
  - works sited by people, not only by suitability;
  - category codes that are noisy (17–50% structures);
  - a moderate AUC that is a lower bound;
  - photo-audit deviations;
  - Phase I geotags were retrospective.
- **Strengthen:** no depth-to-water or aquifer-capacity layer. **Now shown
  to matter** (the CGWB comparison).
- **Keep:** storage objective not modelled; resolution of inputs; Loam
  scarcity and its robustness check.

**Future scope**
- record-level verification of works;
- a larger audit of WC/WH only;
- a storage-oriented variant;
- hydrogeological layers;
- finer land cover and elevation.

**Conclusion:** add one validation sentence, with the same rule as the
Abstract.

**Declarations / data availability**
- **New tools:** `tools/validate_mgnrega.py`, `tools/qgis_figures.py`,
  `tools/prep_map_layers.py`.
- **Inputs:** validation inputs are public (Bhuvan). Observer names are
  removed from all processed data. Audit photos aren't shared, since they
  may show people.
- **Software (if v4 describes the web application):**
  - data-layer viewer with click-to-read values;
  - population heatmap;
  - per-method site overlays;
  - MGNREGA works overlay, with a star where a site has a work within 600 m;
  - a scenario-priorities panel;
  - farmland-scenario site context.

  All are display features; none changes a result.

---

## 4. Rules — a reviewer will check these

**Numbers**
- Every number comes from `PAPER_NUMBERS.txt`, `VALIDATION_NUMBERS.txt` or `supporting/FIGURE_DATA.md`.
  Never compute a new one from rounded values.
- **Precision:**
  - AUC and Boyce to 3 decimals;
  - percentages to 1 decimal;
  - class shares to 2 decimals as in v4.
- **Rounding:** half-up, applied once. The traps:

  | Quantity | Correct | Not |
  |---|---|---|
  | Rainfall weight | 42.8% | 42.9% |
  | Rainfall level share | 36.9% | 37.0% |
  | Soil variance share | 9.7% | 9.8% |
  | Soil variance ratio | 0.63× | 0.64× |
  | Rank 1 shortfall | 0.043 | 0.044 |

- **Cutoff effect:** the Fig 12 bar is a **range over four schemes,
  36.43 pp**. 26.53 pp is only the single fixed-vs-tercile comparison.
- **Consensus area:** 528.5 km². Where 528 appears, say it is rounded.
- **Class signs:** Low ≤ 0.65 < Medium ≤ 0.85 < High.

**Wording**
- **Validation:**
  - "agreement with recorded water works", "consistent with existing
    practice", "a lower bound";
  - **never** "validated", "accurate", "accuracy of X%";
  - AUC ≈ 0.66 is "moderate".
- **Carried over from v4:**
  - "under both cutoff schemes tested";
  - "half or more";
  - "Baseline (rainfall-led)";
  - "complementary" sensitivity analyses;
  - "level contribution" / "variance share".
- **Resolution:** don't write that the inputs "couldn't be more precise".
  That's true for rainfall and soil only.
- **Weights:** the AHP weights come from **expert pairwise judgement** (the
  rationale is in `ahp.py`: rainfall is the water source; slope governs
  retention; soil controls infiltration; drainage locates runoff; land
  cover and settlement are feasibility and demand modifiers). **Never**
  say the weights were derived from how often criteria appear in the
  literature. Table 2 supports criterion **selection** only, worded as in
  `TABLE2_CODING.md`.
- **CGWB:** describe its sites as a water-budget allocation within a
  depth-to-water feasibility zone, with unpublished expert placement. Don't
  say how individual points were placed, and don't imply the model should
  reproduce them (`CGWB_FINDINGS.md` §3b).
- **Not in this draft:** do not report a clay-best (storage) soil variant.
  Mention it only as future work in Limitations.

**Never quote as current** (from v4, still binding)
- **Pre-correction results:** 18.51% · 2,112.6 km² · 54.79 / 26.70 ·
  0.984 → 0.866 · Silt Loam · 973 (except as a reconstruction).
- **Old method comparison:** −5.15 / −0.45 / 11.6 · 9/10 and 7/10 top-10
  shared.
- **Old consensus:** 1,416.8 km² · 12.41% · 36 / 54 / 7.
- **Old sensitivity:** drainage 1.66 · "2 of 10 for drainage" · +24 pp for
  rainfall removal.
- **Old hydrology:** CN 70.5 · 0.354 runoff coefficient.
- **Superseded figures and roundings:** 97.4% / 97.7% · 42.9 · 37.0 · 9.8 ·
  0.64× · 87.16 · −0.955 / −0.565 / −0.165 · 77% re-ranking.
- **Superseded wording:** "11 automated checks" · "Baseline (balanced)" ·
  "fixed, literature-based breakpoints" for all criteria.

**Style:** British spelling; plain ASCII in LaTeX; measured tone; no new
claims beyond the attachments.

---

## 5. Placeholders the authors must fill (leave them visible)

- `[DECIDE: objective framing (A) or (B)]`, from `CGWB_FINDINGS.md` §3.
  **Until the authors decide, write (A)**: surface rainwater-harvesting
  suitability, with recharge as one use of harvested water. Mark every
  sentence that depends on it.
- `[TARGET JOURNAL]`: sets the minimum figure text size, and whether Fig 4
  can take a full page.
- ~~Latest CGWB/GSDA assessment~~ **Resolved:** in 2023 all 15 blocks are
  Safe and the district is at 29.3%, computed from the block rows (GSDA &
  CGWB, *Dynamic Groundwater Resources of Maharashtra 2023*). Details in
  `supporting/gsda/PROVENANCE.md`.

**Resolved since the first version of this brief** (use these):
- **CGWB:** checked. It does not support "declining groundwater", and it
  disagrees with the High zones. **New Discussion and Limitations material
  is in `CGWB_FINDINGS.md`**; all its numbers are in
  `VALIDATION_NUMBERS.txt`. Cite it as Nelofar, Nanda & Venktesham (2021),
  *Aquifer Mapping and Management of Ground Water Resources, Chandrapur
  District, Maharashtra*, CGWB.
- **Table 2:** coded against all eight papers. See `TABLE2_CODING.md`, and
  **replace any "8 of 8" claim for rainfall or for five criteria**. Only
  slope and land cover are in all eight.
- **MODIS reference:** Friedl, M. & Sulla-Menashe, D. (**2022**).
  *MODIS/Terra+Aqua Land Cover Type Yearly L3 Global 500m SIN Grid V061*
  [Dataset]. NASA LP DAAC. doi:10.5067/MODIS/MCD12Q1.061. (The data used is
  the 2024 annual product of this collection.)
- Author names, ORCIDs, funding, repository URL or DOI.

---

## 6. What to hand back

Work section by section, starting with the Abstract, §1 and the new
validation subsections. For each section:

1. **The revised text,** in LaTeX if the `.tex` was attached.
2. **A change log:** every number added or changed (old → new → source
   file), every claim added, reversed or removed, and every placeholder.
3. **Unverified numbers:** anything kept from v4 that you can't trace to an
   attachment.

When unsure, choose the conservative wording and flag it.
