# Paper revisions — draft v3 (`rwh_journal_paper_v3_preview.pdf`) against current results

**Use:** work through the manuscript top to bottom with this file open. Each
entry gives where the text is, what it says now, and what it should say. Every
replacement value was computed on 4 October 2026 from the current data and code,
using:

- `tools/paper_figures.py`, which prints Tables 7, 9, 10, 11, 12 and 13, the
  consensus tables and others;
- `tools/build_figure_data.py`, which writes the figures and
  `review_pack/FIGURE_DATA.md`;
- `algorithms.py`, `sensitivity.py` and `consensus.py`.

**Why almost every result changes:** the draft predates the soil legend
correction of 2 October 2026. Code 4, which covers 77.8% of the district, was
read as Silt Loam and scored 1.00. It is in fact **Clay Loam and scores 0.60**.
Codes 1 and 7 were also mislabelled. Every result that depends on soil moved,
and so did several of the paper's central claims.

---

## 0. Results I computed for you (they were open items)

### 0.1 Loam robustness check — Loam rescored 1.00 → 0.80, everything else fixed

| Baseline rank | Site | Soil | Score | Rank after the change |
|---|---|---|---|---|
| 1 | (79.6825, 20.3645) | Loam | 0.957 | **1** (the cell shifts 1.7 km within the same cluster; score 0.941) |
| 2 | (79.6712, 20.3023) | Loam | 0.932 | **drops out of the top 25** |
| 3 | (79.9653, 20.0423) | Loam | 0.931 | **17** |
| 4 | (79.4336, 20.5086) | Sandy Clay Loam | 0.926 | **2** |
| 5 | (79.5948, 20.3786) | Loam | 0.926 | **16** |
| 6 | (79.3658, 20.4295) | Clay Loam | 0.922 | 3 |
| 7 | (79.9030, 20.1780) | Sandy Clay Loam | 0.920 | 4 |
| 8 | (79.7673, 19.6664) | Clay Loam | 0.920 | 6 |
| 9 | (79.4619, 20.3956) | Sandy Clay Loam | 0.917 | 7 |
| 10 | (79.9228, 20.3051) | Loam | 0.917 | 20 |

- **Retained: top 5 2/5, top 10 6/10, top 25 20/25.** The High share barely
  moves: 6.44% → 6.40%.
- **Reading:** the class areas don't depend on the Loam score, but the order of
  the shortlist does. The top site survives, and three of the other four Loam
  sites in the top 5 fall to ranks 16–25 or leave the list. Put this in the
  Discussion or Limitations next to the citation for Loam = 1.00.

### 0.2 Table 12 (criterion correlation) — no longer empty

**Use Pearson r, not Spearman.** Soil has 4 distinct values and land cover 10,
so rank correlations involving them are unreliable because of ties (tie
probability 0.64 and 0.46). If you keep the Spearman version, add that caveat.

**Pearson r** (whole district, 123,555 cells):

| | Rain | Slope | Soil | Drain | LULC | Settl. |
|---|---|---|---|---|---|---|
| Rainfall | 1 | 0.211 | **0.449** | 0.005 | −0.174 | 0.000 |
| Slope | | 1 | 0.125 | 0.177 | 0.063 | 0.082 |
| Soil | | | 1 | −0.021 | −0.125 | −0.058 |
| Drainage | | | | 1 | 0.181 | −0.007 |
| Land cover | | | | | 1 | 0.256 |
| Settlement | | | | | | 1 |

**Spearman ρ** (ties flagged): slope–rain 0.125, slope–drain 0.269, slope–soil
0.008†, slope–lulc 0.340†, slope–settl 0.140, rain–drain 0.011, rain–soil
0.439†, rain–lulc −0.175†, rain–settl −0.022, drain–soil −0.019†, drain–lulc
0.219†, drain–settl 0.014, soil–lulc −0.129†, soil–settl −0.062†, lulc–settl
0.251† († = unreliable because of ties).

**The paragraph to write:**
- No pair is strongly dependent. The largest is **rainfall–soil, r = 0.45**:
  they share about 20% of their variance and carry 0.58 of the weight between them.
- The draft assumes a cropland-belt dependence. **The data only partly support
  it.** Correlations with land cover are driven by the contrast between cropland
  and non-cropland: cropland cells score +0.14 higher on drainage and +0.17
  higher on settlement. Inside cropland the land-cover score is constant.
- **Slope–land cover is ρ 0.34 against r 0.06**, which is a tie and
  concentration effect, not a real dependence.
- The Euclidean-distance caveat for TOPSIS still applies, but say the
  dependence is **weak**.

### 0.3 Table 13 (percentile vs fixed-band rainfall) — no longer empty

| Measure | Percentile rank | Fixed bands |
|---|---|---|
| Highly suitable share | 6.44% | **37.65%** |
| Highly suitable area (km²) | 735.0 | **4,297.1** |
| Mean composite | 0.673 | **0.826** |
| Top-10 sites shared with baseline | 10/10 | **0/10** |
| Spearman ρ against baseline | 1.0000 | **0.7839** |
| Class agreement | 100.0% | **31.3%** |
| Rainfall level contribution | 36.95% | **49.80%** |
| Rainfall level / assigned ratio | 0.862 | **1.162** |

**The paragraphs to write:**
- The bands are defined only for this comparison, in `tools/paper_figures.py`,
  and are not taken from a published classification. **Say so.**
- Chandrapur's 1,189–1,714 mm falls entirely in the top three bands (0.75,
  0.90, 1.00). Fixed bands therefore compress rainfall into near-uniform high
  scores. That makes the share of highly suitable land nearly six times larger,
  and it replaces the **entire** top 10.
- Fixed bands would restore transferability, but at a severe cost in
  within-district discrimination. **This is the largest single effect measured
  in the study** (+31.21 pp on High, −39.51 pp on Low).

---

## 1. Figure numbering — the generated set doesn't match the draft's slots

| Draft figure | Draft content | Generated figure to use | Notes |
|---|---|---|---|
| 1 | Study area | — | QGIS, not made yet |
| 2 | Normalisation families | **fig02** | Use the generated caption |
| 3 | Preprocessing chain | — | Diagram tool, not made yet |
| 4 | Two-stage architecture | — | Diagram tool, not made yet |
| 5 | Scoring forms (4 panels) | **fig05** | **Six** panels, including soil and land cover. Update the caption |
| 6 | Six criterion surfaces | **fig06** | |
| 7 | Baseline map | — | QGIS. Use Medium `#E8E4DC` (FIGURE_SPECS) |
| 8 | Step vs ramp | **fig08** | **Two panels, one per legend.** Rewrite the caption (§4 below) |
| 9 | Parallel coordinates | **fig09** | The finding changed (§4) |
| 10 | Four variants | **fig10** | |
| 11 | Factorial interaction | **fig11** | |
| 12 | Histograms + alluvial | **fig13** (ECDF + alluvial) | An ECDF, not histograms |
| 13 | Difference map | **fig14** | |
| 14 | Scenario stacked bars | **fig15** | |
| 15 | Agreement rasters | **fig16** | Categories collapsed to never / minority / half or more / unanimous |
| 16 | Tornado | **fig17** | Three panels: ±20% perturbation, map-removal retention, map-removal ΔHigh |
| 17 | Assigned vs effective | **fig18** | Now **level vs variance**, not one "effective weight" |
| 18 | Hydrological surfaces | — | **Not generated.** Make it in QGIS from the `derived_maps.py` outputs |
| 19 | Correlation heatmap | **fig19** | |
| 20 | Field workflow | — | Diagram tool, not made yet |
| — | — | **fig12** Effect magnitudes | **No slot in the draft.** It carries the analyst-decision thesis (§3) |
| — | — | **fig21** Ranking vs cutoff partition | **No slot.** |
| — | — | **fig22** Stability vs suitability | **No slot.** |

Take every caption from `review_pack/FIGURE_DATA.md`. They're computed and current.

---

## 2. Section-by-section edits

### Abstract — rewrite the results half

| Draft says | Replace with |
|---|---|
| 18.51% (2,112.6 km²) highly suitable | **6.44% (735.0 km²)** |
| ±20% perturbation retains 90% of top-ten on average | **88%** (87.5%; worst case 60%, maximum rank shift 3) |
| Removing drainage density (9.3% of weight) leaves just 2 of 10 | **Removing rainfall leaves 0 of 10; drainage leaves 3 of 10** |
| Slope exerts 1.29× its weight, drainage 0.71× | Slope **1.40×** its weight in **level** but **0.43×** in **variance**; land cover is the extreme case (1.32× level, 0.08× variance) |
| Aggregation main effect −5.15 pp vs −0.45, ratio 11.6, negligible interaction | **−0.957 pp vs −0.560 pp, ratio 1.7; interaction −0.162 pp**. The aggregation finding now holds for **ranking, not area**: TOPSIS keeps 5/10 of the shortlist, Fuzzy-AHP keeps 10/10 |
| Consensus 1,416.8 km² (12.41%) | **528.5 km² (4.63%)**; 15 sites selected by all four (unchanged) |
| — | **Add the paper's new thesis:** analyst decisions dominate algorithm choice. Over the same surface, rainfall scoring moves High by +31.21 pp, weighting judgements by 16.23 pp, cutoff scheme by 36.43 pp and the soil-legend data error by −12.07 pp, while algorithm choice moves it by under 1 pp (Fig. 12) |

### Nomenclature

- **Wᵢ:** "Effective (realised) weight" → **"level contribution of criterion i"**
  (the mean over cells of wᵢrᵢ/V).
- **Add** "Pratt variance share, βᵢ·corr(rᵢ, V)".

### 1.2 Study area

- "soil texture resolves to four classes, of which **Silt Loam** is dominant" →
  "… of which **Clay Loam** (77.8%) is dominant". The four are Clay, Clay Loam,
  Sandy Clay Loam and Loam.

### 1.3 Weaknesses in current practice

- "min–max scaling left **97.4%** of slope cells and **97.7%** of population
  cells above 0.90": these came from the whole raster. In-district they are
  **95.8%** (slope) and **97.4%** (population, cost-inverted). Use the
  in-district values, as Fig. 2 does.
- "places water bodies at 1.00 and urban land at **0.75** while deciduous
  forest scores 0.00": in-district (codes 4–17), urban is **0.69**. Water 1.00
  and deciduous broadleaf 0.00 are unchanged.
- "Roughly 48% of the total weight was either doing no work or doing the wrong
  work": **verified, keep it, and show the sum.** Under min–max, two criteria
  did no work (slope 0.2254 and settlement 0.0397, with ≥ 95% of cells above
  0.90) and two did the wrong work (land cover 0.0597 and soil 0.1535, ranked by
  class code). 0.2254 + 0.0397 + 0.0597 + 0.1535 = **0.478**. Suggested wording:
  "…roughly 48% of the total weight (slope, settlement, land cover and soil
  together) was either doing no work or doing the wrong work."

### 1.4 Contributions

- **C2:** "Three independent sensitivity analyses … All three converge" →
  "complementary". The analyses share one stack and **don't** all agree:
  perturbation ranks soil first, map removal ranks rainfall first for the
  shortlist, and the level and variance measures disagree sharply.
- **C3:** "the aggregation rule matters considerably more than the weighting
  rule is the paper's most novel result" → restate it.
  - On **ranking**, aggregation replaces half the shortlist and weighting none of it.
  - On **area**, the two are similar (−0.957 against −0.560 pp).
  - The more novel result is that **analyst decisions** (scoring, judgements,
    cutoffs, data) move the High share 13–38× more than the aggregation effect does
    (12.07–36.43 pp against 0.957).

### 1.5 Research questions

The questions still stand. The answers to RQ2 and RQ3 changed (see 5.3 and 5.8).

### 2.4.3 Alternatives to AHP

- Slope mean 0.924 is unchanged. Settlement (sd 0.343) and drainage (0.303) are
  still the most dispersed. The text still holds.

### 4.2 Table 4 — soil row and soil text

- **Soil row:** "Sand 0.55, Silt Loam 1.00, Sandy Clay Loam 0.80, Silt Clay Loam
  0.50 · 4 values, mean 0.908" → **"Loam 1.00, Sandy Clay Loam 0.80, Clay Loam
  0.60, Clay 0.25 (all 12 USDA classes tabulated) · 4 values, mean 0.543"**.
- **Text:** "Soil peaks at **Silt Loam** rather than Sand…" → "Soil peaks at
  **Loam**…". Keep the recharge-versus-storage reasoning, **and add the citation
  for the ordering Loam > Sandy Clay Loam > Clay Loam > Clay** (outstanding
  item 1).
- **Source:** state that the legend is read from the `LEGEND` tag of SoilGrids250m
  `TEXMHT_M_sl1` [25].
- **Settlement:** the gentle peak (0.97 / 1.00 / 0.97 at 1 / 3 / 5 km) is
  described correctly. Keep it.

### 4.4 Classification

- The percentile-split argument stands.
- **Add one sentence:** the cutoff scheme is itself an analyst decision. Across
  four standard schemes the High share ranges over **36.43 pp** (Fig. 12).

### 4.6 Planning scenarios

- "baseline (balanced, rainfall-led)" → **"baseline (rainfall-led)"**.

### 4.8 Derived hydrological surfaces

- "forest at CN 55 … built-up land at CN 85". Under the corrected hydrologic
  soil groups (Clay is now group D, not A), the mean CN is **77** for deciduous
  forest, **88.8** for cropland and **91.9** for built-up land.
  - At the annual 1,493 mm, class runoff coefficients are **0.94–0.98**, so the
    argument holds and is stronger.
  - At the 100 mm storm, class means spread **0.45–0.78** (draft: 0.13–0.61).

### 5.1 Weights and surface

- Table 5 is **unchanged** (the AHP and Fuzzy weights don't depend on data).
  λmax 6.1460, CI 0.0292 and CR 0.0235 are also unchanged.
- **Surface statistics** — min 0.2563 → **0.2103**, max 0.9839 → **0.9566**,
  mean 0.7294 → **0.6733**, median 0.7415 → **0.6840**, sd 0.1263 →
  **0.1242**, distinct values 108,229 → **107,729**. Exactly one cell at the
  maximum is unchanged.

**Table 6:**

| Class | Share | Area |
|---|---|---|
| High | **6.44%** | **735.0 km²** |
| Medium | **52.48%** | **5,988.7 km²** |
| Low | **41.08%** | **4,688.7 km²** |

**The step-versus-ramp paragraph — rewrite.** Compare on one legend at a time.

| Legend | Step: tied at 1.000 | Step distinct | Step High | Ramp High | Ramp tied |
|---|---|---|---|---|---|
| Superseded (in use when steps were live) | **973** | 46,217 | 25.84% | — | **0** |
| Corrected (current) | **1** | 46,224 | **13.61%** | **6.44%** | 0 |

- 973 is a **historical reconstruction**. The plateau needed flat-topped breaks
  **and** a dominant soil class wrongly scored 1.00, and neither alone produces it.
- "The headline moved from 25.6% to 18.51%" → on the corrected legend, steps give
  **13.61%** and ramps **6.44%**.
- Distinct composite values under ramps: **107,729**.
- **Fig. 8 caption:** "3,872 cells fall in 0.98–1.00 under step scoring against
  37 under ramps" → superseded legend 3,872 (step); **corrected legend 14
  (step) against 0 (ramps)**. Use the fig08 caption from FIGURE_DATA.
- "Because classification uses fixed thresholds, **18.51%** is a property of
  Chandrapur…" → **6.44%**.

### 5.2 Candidate sites

- "scoring 0.984 at rank 1 to 0.866 at rank 25 … across 22 distinct values" →
  **0.957 to 0.854, 19 distinct values (3 dp), range 0.103**.
- **Table 7 — replace it entirely** with the current top 5 per variant:

**AHP + WLC**

| Rank | Lon | Lat | Score | Slope | Soil | Drainage | Settlement |
|---|---|---|---|---|---|---|---|
| 1 | 79.6825 | 20.3645 | 0.957 | 1.07° | Loam | 0.44 | 7.2 km |
| 2 | 79.6712 | 20.3023 | 0.932 | 0.70° | Loam | 0.27 | 0.6 km |
| 3 | 79.9653 | 20.0423 | 0.931 | 0.42° | Loam | 0.30 | 5.0 km |
| 4 | 79.4336 | 20.5086 | 0.926 | 0.82° | Sandy Clay Loam | 0.36 | 3.6 km |
| 5 | 79.5948 | 20.3786 | 0.926 | 0.73° | Loam | 0.40 | 8.6 km |

**AHP + TOPSIS**

| Rank | Lon | Lat | Score | Slope | Soil | Drainage | Settlement |
|---|---|---|---|---|---|---|---|
| 1 | 79.6825 | 20.3645 | 0.958 | 1.07° | Loam | 0.44 | 7.2 km |
| 2 | 79.6712 | 20.3023 | 0.929 | 0.70° | Loam | 0.27 | 0.6 km |
| 3 | 79.4336 | 20.5086 | 0.925 | 0.82° | Sandy Clay Loam | 0.36 | 3.6 km |
| 4 | 79.9030 | 20.1780 | 0.924 | 1.24° | Sandy Clay Loam | 0.40 | 6.2 km |
| 5 | 79.4619 | 20.3956 | 0.920 | 1.09° | Sandy Clay Loam | 0.71 | 8.5 km |

**Fuzzy-AHP + WLC**

| Rank | Lon | Lat | Score | Slope | Soil | Drainage | Settlement |
|---|---|---|---|---|---|---|---|
| 1 | 79.6825 | 20.3645 | 0.956 | 1.07° | Loam | 0.44 | 7.2 km |
| 2 | 79.9653 | 20.0423 | 0.931 | 0.42° | Loam | 0.30 | 5.0 km |
| 3 | 79.6712 | 20.3023 | 0.931 | 0.70° | Loam | 0.27 | 0.6 km |
| 4 | 79.5948 | 20.3786 | 0.926 | 0.73° | Loam | 0.40 | 8.6 km |
| 5 | 79.4336 | 20.5086 | 0.925 | 0.82° | Sandy Clay Loam | 0.36 | 3.6 km |

**Fuzzy-AHP + TOPSIS**

| Rank | Lon | Lat | Score | Slope | Soil | Drainage | Settlement |
|---|---|---|---|---|---|---|---|
| 1 | 79.6825 | 20.3645 | 0.958 | 1.07° | Loam | 0.44 | 7.2 km |
| 2 | 79.6712 | 20.3023 | 0.926 | 0.70° | Loam | 0.27 | 0.6 km |
| 3 | 79.4336 | 20.5086 | 0.922 | 0.82° | Sandy Clay Loam | 0.36 | 3.6 km |
| 4 | 79.9030 | 20.1780 | 0.922 | 1.24° | Sandy Clay Loam | 0.40 | 6.2 km |
| 5 | 79.4619 | 20.3956 | 0.918 | 1.09° | Sandy Clay Loam | 0.71 | 8.5 km |

  All 20 rows are cropland. The caption's "Every one of the twenty rows is Silt
  Loam under cropland" → "All twenty are cropland; **12 are Loam and 8 Sandy
  Clay Loam**".
- **The paragraph after Table 7:**
  - Rank 1 is the same location under all four variants, and rank 2 is shared
    by three (Fuzzy-AHP + WLC swaps ranks 2 and 3).
  - **Both TOPSIS variants replace two Loam sites** — (79.9653, 20.0423) and
    (79.5948, 20.3786) — with two Sandy Clay Loam sites, (79.9030, 20.1780) and
    (79.4619, 20.3956).
  - The split is still by aggregation rule.
- **Fig. 9 caption:** "The soil axis is a perfectly flat line at 1.000, SD
  0.0000, because every site is Silt Loam" → the flat axis is now **land
  cover** (24 of 25 sites at exactly 1.000).
  - Soil is SD **0.174**, settlement **0.239** and drainage **0.110**.
  - Axes are ordered by weighted spread: soil and rainfall separate the
    shortlist most.
- **The concentration paragraph and Table 8 — rewrite.**
  - The shortlist is **no longer** concentrated on one soil class. The 25 sites
    are **Clay Loam 10, Loam 9, Sandy Clay Loam 6**.
  - The new dependency runs the other way: **4 of the top 5 sit on Loam, which
    is 0.38% of the district (42.9 km²)** (see 0.1).
  - "Silt Loam covers 77.82% and scores 1.00" → "**Clay Loam** covers 77.82%
    and scores **0.60**".
  - "Two of the six criteria are close to constant" → only **land cover** is
    (24/25 at 1.00). Slope is concentrated (86% of cells above 0.90) but not tied.
  - "the TOPSIS variants … retaining 9 of the baseline's top 10" → **5 of 10**.

**Table 8, soil columns:**

| Soil | km² | Share | Score |
|---|---|---|---|
| Clay Loam | 8,881.7 | 77.82% | 0.60 |
| Clay | 2,124.0 | 18.61% | 0.25 |
| Sandy Clay Loam | 363.7 | 3.19% | 0.80 |
| Loam | 42.9 | 0.38% | 1.00 |

  The land-cover columns are unchanged.

### 5.3 Comparative analysis

**Table 9, quantitative rows:**

| | AHP + WLC | AHP + TOPSIS | Fuzzy + WLC | Fuzzy + TOPSIS |
|---|---|---|---|---|
| High suitability | 6.44% | 5.65% | 6.04% | 4.92% |
| Δ from baseline | — | −0.80 pp | −0.40 pp | −1.52 pp |
| High area (km²) | 735.0 | 644.3 | 689.6 | 562.0 |
| Mean composite | 0.673 | 0.640 | 0.673 | 0.640 |
| Δ mean | — | −0.033 | −0.0003 | −0.033 |
| Top-10 shared | 10/10 | **5/10** | **10/10** | **5/10** |
| Spearman ρ | 1.000 | 0.964 | 0.9998 | 0.967 |
| Class agreement | 100.0% | 87.17% | 99.0% | 87.3% |

- "Position: most permissive …" — the ordering on High still holds.
- **The paragraph after the table:** "The top-10 row is the exception … Fuzzy-AHP
  with WLC sits alone at 7" → **false now.** The top-10 row also separates
  cleanly by aggregation (10, 5, 10, 5). **Every** quantitative row splits by
  aggregation rule.

**5.3.1 Factorial decomposition — rewrite the numbers.**

- **Aggregation main effect −0.957 pp, weighting −0.560 pp, ratio 1.7** (draft:
  −5.15, −0.45, 11.6).
- On the mean composite: **−0.0329 against −0.0003**.
- **Interaction −0.162 pp**, about one sixth of the aggregation effect. It is
  **not** negligible, so drop "a twentieth" and "close to additive".
- The weighting effect is **−0.40 pp under WLC and −0.72 pp under TOPSIS**, so it
  roughly doubles once compensation is restricted. The mechanism the draft gives
  is right.
- **Equation 12 sign:** the draft's E_int = ½(Δ_agg^crisp − Δ_agg^fuzzy) gives
  **+0.162**. The figures use the standard factorial convention,
  ½(Δ_agg^fuzzy − Δ_agg^crisp) = **−0.162**. Flip the equation so it matches.
  Simple effects: AHP −0.795, Fuzzy-AHP −1.119.
- **Fig. 11 caption:** "The WLC line runs 18.51 to 18.32 and the TOPSIS line
  13.62 to 12.92" → **WLC 6.44 → 6.04, TOPSIS 5.65 → 4.92**. The two lines are
  separated by under 1 pp, not 5.

**5.3.2 Why aggregation dominates.**

- "0.669 against 0.729" → **0.640 against 0.673**.
- The fuzzy surfaces still correlate at ρ 0.9998, with class agreement **99.0%**
  (not 98.7%).
- **The framing should change.** On area, aggregation **doesn't** dominate by
  much (1.7×). Its real effect is on **which sites are recommended**.
- And the large Low-class shift (+9.03 pp) is a **cutoff effect** (Fig. 21):
  matching the class sizes removes it, and doing so takes a 0.050 move of the
  lower cutoff against 0.005 for High. Add this, and cite Fig. 21.

**Fig. 12 caption (now generated fig13):**
- "30,703 cells move down against 761 up … Medium to Low at 23,988 cells, or
  2,217 km²" → **13,998 down against 1,862 up; Medium→Low 12,412 cells =
  1,146.4 km²**.
- There are four off-diagonal flows: Medium→Low 1,146.4, High→Medium 146.4,
  Low→Medium 116.2 and Medium→High 55.6 km².

**Fig. 13 caption (now fig14):**
- "the 25.5% of the district that reclassifies" → **12.83%**.
- The finding is that the rate **falls** towards the boundary: 6.49% within 2 km
  against 17.52% beyond 20 km. **It is not an edge artefact.**

**5.3.3 Table 10:**

| From \ To | Low | Medium | High | Row total |
|---|---|---|---|---|
| High | 0 | 1,586 | 6,380 | 7,966 |
| km² | 0.0 | 146.4 | 588.7 | 735.0 |
| Medium | 12,412 | 51,871 | 603 | 64,886 |
| km² | 1,146.4 | 4,786.7 | 55.6 | 5,988.7 |
| Low | 49,444 | 1,259 | 0 | 50,703 |
| km² | 4,572.5 | 116.2 | 0.0 | 4,688.7 |

- **Text:** still graded, with no cell crossing two classes.
  - 13,998 cells move down and 1,862 up.
  - Medium→Low is 12,412 cells (1,146.4 km²), against 1,586 cells leaving High.
- "92,091 cells left unchanged, 74.53%" → **107,695 cells; 87.17% of district
  area**. Quote the area figure. The cell count gives 87.16.

**5.3.4 Table 11:**

| | A | B | C | D |
|---|---|---|---|---|
| A | — | 0.9643 | 0.9998 | 0.9672 |
| B | 0.9621 | — | 0.9588 | 0.9999 |
| C | 0.9998 | 0.9568 | — | 0.9620 |
| D | 0.9654 | 0.9999 | 0.9604 | — |

- Spearman is above the diagonal and Pearson below.
- Cross-aggregation pairs sit at **0.9588–0.9672**.
- **"A result worth isolating: Fuzzy-AHP with WLC … shares only 7 of the
  baseline's top 10 … the two TOPSIS variants both retain 9 of 10" — delete
  it, because it is now false.**
  - Fuzzy-AHP + WLC retains **10/10** and the TOPSIS variants **5/10**.
  - The "two levels of robustness" point **still stands with a new example**:
    TOPSIS correlates at ρ 0.964 and agrees on 87% of the map, yet replaces
    half the shortlist.
  - "twenty-two distinct scores across twenty-five sites in a range of 0.118" →
    **19 distinct (3 dp) in a range of 0.103**.

### 5.4 Criterion dependence

Fill Table 12 and the paragraph from §0.2.

### 5.5 Rainfall normalisation

- "Rainfall carries 42.85% of the assigned weight" is fine at 2 dp; at 1 dp it
  is **42.8%**.
- Fill Table 13 from §0.3. The "Rainfall effective weight 34.11%, 0.796"
  entries → **36.95%, 0.862**.

### 5.6 Scenarios

**Table 14:** the weights are unchanged. Update the High % column and the name.

| Scenario | CR | High % |
|---|---|---|
| **Baseline (rainfall-led)** | 0.0235 | **6.44** |
| Maximise recharge | 0.0044 | **2.54** |
| Community-focused | 0.0059 | **11.12** |
| Low-earthwork (proxy) | 0.0078 | **18.77** |
| Fertile farmland (proxy) | 0.0146 | **3.39** |

- **Rewrite the paragraph after it; every claim reversed or moved.**
  - Maximise recharge now **lowers** High, to 2.54% (−3.90 pp). Promoting soil
    no longer lifts the map, because the dominant soil scores 0.60, not 1.00.
  - **Low-earthwork** is the one that raises it: +12.33 pp, to 18.77%.
  - Community-focused is at 11.12%, **not** near the baseline. Drop "almost
    exactly the baseline share".
  - The scenarios span **16.23 pp**, about **17×** the aggregation main effect
    (0.957). The policy-versus-algorithm point is **stronger**.
- **Table 15 — replace it:**

| Scenario | Lon | Lat | Score | To settlement |
|---|---|---|---|---|
| Baseline (rainfall-led) | 79.6825 | 20.3645 | 0.957 | 7.2 km |
| Maximise recharge | 79.6768 | 20.3956 | 0.962 | 3.9 km |
| Community-focused | 79.6768 | 20.3956 | 0.965 | 3.9 km |
| Low-earthwork | 79.6768 | 20.3956 | 0.957 | 3.9 km |
| Fertile farmland | 79.6768 | 20.3956 | 0.968 | 3.9 km |

  The caption's "All five are Silt Loam cropland" → "All five are **Loam**
  cropland".
- **Text:** "Two of the five displace the leading candidate … three distinct
  sites … moves 90 km" → **four of the five agree** on one site, (79.6768,
  20.3956). Only the baseline picks a different one, about 3.5 km away. That
  makes **2 distinct top sites**. **Drop the community-focused "90 km" example.**

### 5.7 Consensus

- "36 distinct locations, 15 by all four; five scenarios proposed 54, 7 by all
  five" → **35 distinct, 15 by all four; scenarios 61 distinct, 2 by all five**.
- **Borda leaders:** (79.6825, 20.3645) 100; (79.6712, 20.3023) 95; (79.4336,
  20.5086) 89; (79.9653, 20.0423) 85.

**Table 16** (the area at each agreement level):

| Agreement | 4 algorithms | 5 scenarios |
|---|---|---|
| All | **4.63% — 528.5 km²** | **2.10% — 239.9 km²** |
| All but one | 0.46% — 52.5 | 1.12% — 128.0 |
| Middle (2 of 4 / 3 of 5) | 1.31% — 149.3 | 1.80% — 205.8 |
| Two of five | — | 5.25% — 599.0 |
| One only | 0.53% — 60.8 | 11.35% — 1,294.8 |
| None | 93.07% — 10,621.3 | 78.38% — 8,944.8 |

- **Text:**
  - "only 6.8% … in partial agreement" → **2.30%** for algorithms and **19.52%**
    for scenarios.
  - "fully agreed area falling from 12.41% to 10.66%" → **from 4.63% to 2.10%**.
  - The conclusion (policy moves the answer more than arithmetic) holds and is
    stronger.

**Table 17** (the 15 sites selected by all four, in consensus-rank order):

| C-rank | Lon | Lat | Borda | Best | Mean rank |
|---|---|---|---|---|---|
| 1 | 79.6825 | 20.3645 | 100 | 0.958 | 1.0 |
| 2 | 79.6712 | 20.3023 | 95 | 0.932 | 2.2 |
| 3 | 79.4336 | 20.5086 | 89 | 0.926 | 3.8 |
| 4 | 79.9653 | 20.0423 | 85 | 0.931 | 4.8 |
| 5 | 79.9030 | 20.1779 | 82 | 0.924 | 5.5 |
| 6 | 79.5948 | 20.3786 | 81 | 0.926 | 5.8 |
| 7 | 79.4619 | 20.3956 | 76 | 0.920 | 7.0 |
| 8 | 79.9228 | 20.3051 | 65 | 0.917 | 9.8 |
| 9 | 79.3658 | 20.4295 | 57 | 0.922 | 11.8 |
| 10 | 79.7673 | 19.6664 | 51 | 0.920 | 13.2 |
| 11 | 79.8239 | 20.2006 | 48 | 0.910 | 14.0 |
| 12 | 79.3262 | 20.4549 | 42 | 0.915 | 15.5 |
| 15 | 79.4252 | 20.4266 | 36 | 0.913 | 17.0 |
| 24 | 79.7701 | 19.9349 | 18 | 0.885 | 21.5 |
| 29 | 79.5722 | 20.2062 | 12 | 0.873 | 23.0 |

  The gaps are at 13, 14 and 16–23 and 25–28. "Fourteen of fifteen on cropland;
  exception (79.5694, 20.2119) on savanna" → **still fourteen of fifteen, but
  the exception is now C-rank 29, (79.5722, 20.2062), on grassland** (Clay
  Loam). Checked in `outputs/consensus_algorithms.csv`.
- **"What the common sites are…":** 1,416.8 km² → **528.5 km²**.

### 5.8 Sensitivity

**5.8.1 One-way perturbation:**
- "90% … worst case 70% … max shift three" → **88% (87.5%), worst 60%, max
  shift 3**.
- "Influence order: drainage (1.66), slope (1.55), soil (1.17), rainfall (0.48),
  settlement (0.35), land cover (0.04)" → **soil (1.42), rainfall (1.24), slope
  (1.16), drainage (0.61), land cover (0.27), settlement (0.08)**.
- "That order does not match the weight order" is still true: soil is third by
  weight and first here.
- **Fig. 16 caption:** "from the 18.51% baseline" → **6.44%**.

**5.8.2 Table 18 — replace it:**

| Removed | Weight | Sᵢ (%) | Max (%) | Mean \|ΔV\| | Retained | High % |
|---|---|---|---|---|---|---|
| Rainfall | 0.428 | 15.427 | 51.32 | 0.0939 | **0/10** | 8.98 |
| Slope | 0.225 | 12.106 | 46.74 | 0.0745 | 5/10 | 3.33 |
| Drainage | 0.093 | 4.356 | 17.73 | 0.0282 | 3/10 | 11.56 |
| Soil | 0.154 | 4.241 | 26.91 | 0.0278 | 4/10 | **14.12** |
| Land cover | 0.060 | 3.044 | 21.64 | 0.0184 | 9/10 | 5.38 |
| Settlement | 0.040 | 1.950 | 10.63 | 0.0123 | 5/10 | 6.93 |

**Text — rewrite both findings:**
- (1) The surface index still tracks weight, broadly. **Rainfall removal destroys
  the shortlist (0/10)**, not drainage removal.
  - Drainage retains 3/10 on a surface change of only 4.36%, so "barely moves
    the map while reordering the shortlist" **still applies to drainage**, but
    it is no longer the extreme.
  - Slope removal now retains only 5/10.
- (2) "Removing rainfall inflates the highly suitable share by nearly 24 pp"
  → **+2.54 pp** (to 8.98%).
  - **The largest inflation now comes from removing soil, +7.67 pp**: the
    dominant soil scores 0.60, so soil is now the brake.
  - Rewrite the "rainfall acts as a brake" argument around soil.

**5.8.3 Effective weights — Table 19, two measures now:**

| Criterion | Assigned % | Level % (ratio) | Level SD | Variance share % (ratio) |
|---|---|---|---|---|
| Rainfall | 42.8 | 36.9 (0.86) | 9.33 | **72.0 (1.68)** |
| Slope | 22.5 | **31.6 (1.40)** | 5.92 | 9.7 (0.43) |
| Soil texture | 15.4 | 12.5 (0.81) | 3.39 | 9.7 (**0.63**) |
| Land cover | 6.0 | 7.9 (1.32) | 2.92 | 0.5 (**0.08**) |
| Drainage density | 9.3 | 7.2 (0.77) | 4.22 | 6.5 (0.70) |
| Settlement prox. | 4.0 | 3.9 (0.98) | 2.26 | 1.6 (0.40) |

  At 2 dp, use 42.85 / 36.95 / 71.98 and so on. At 1 dp, round **once** from
  the unrounded value: 42.8, 36.9 and 9.7, **not** 42.9, 37.0 and 9.8.
- **Text:**
  - "soil 1.26 times because Silt Loam dominates" → soil is now **0.81×**,
    because the dominant Clay Loam scores 0.60.
  - Slope is **1.40×**, drainage **0.77×** (was 0.71) and rainfall **0.862** (was 0.796).
  - **Add the level/variance distinction.** The level share is a mean of
    per-cell ratios. It measures contribution to the score's level, **not**
    influence. The Pratt variance share does that: rainfall 72%, and land cover
    0.08× its weight.
  - Also add that level shares can't be reproduced from Fig. 6's means (38.2%
    against 36.9% for rainfall).

**5.8.4 What the three analyses agree on — rewrite.**
- "Perturbation ranks drainage first … despite its fourth-place weight" → it
  ranks **soil** first, the third-place weight.
- "Map removal shows dropping drainage leaves only 2 of 10" → rainfall leaves
  **0**, drainage 3 and slope 5.
- "drainage 0.71× and slope 1.29×" → drainage 0.77× and slope 1.40× in level;
  slope 0.43× in variance.
- The conclusion that weight magnitude is a poor predictor of influence
  **survives**. The "local ranking influence" example becomes **rainfall
  (0/10) and drainage (3/10)**.

**5.8.5 Table 20** (within the High zone, now **7,966 cells**, not 22,888):

| Criterion | sd(wᵢrᵢ) in High | Weight | Top-10 retained |
|---|---|---|---|
| Rainfall | 0.0197 | 0.428 | 0/10 |
| Drainage density | 0.0172 | 0.093 | 3/10 |
| Soil texture | 0.0135 | 0.154 | 4/10 |
| Settlement proximity | 0.0090 | 0.040 | 5/10 |
| Slope | 0.0040 | 0.225 | 5/10 |
| Land cover | 0.0034 | 0.060 | 9/10 |

- **Text:**
  - The ordering is now **exactly monotonic**, a stronger result. Drop "almost".
  - "Soil and settlement sit at identical dispersion" is no longer true.
  - "slope … retains 9 of 10" → **5 of 10**.
  - "Drainage ranges from 0.40 to 0.72 across the top five" → **0.27–0.44**.
  - The district-wide figures (settlement sd 0.343, drainage 0.303) are
    unchanged.
- **Fig. 17 caption:** "rainfall falls 42.85 to 34.11 while slope rises 22.54 to
  29.11 … drainage 9.32 to 6.61 … land cover 5.97 to 7.25" → **rainfall 42.85 →
  36.95, slope 22.54 → 31.64, drainage 9.32 → 7.18, land cover 5.97 → 7.89**.
  Generated fig18 shows level **and** variance. Use its caption.
- **Closing paragraph:** "rainfall governs which land qualifies, and drainage
  density governs which of the qualifying land is chosen" → within the High
  zone, **rainfall and drainage** together govern selection, and soil comes next.

### 5.9 Scale of the evaluation

- "11 automated end-to-end software checks" → **14**.

### 5.10 Table 21 (100 mm storm)

| Surface | Min | Max | Mean |
|---|---|---|---|
| Drainage density | 0.000 | 0.848 | 0.233 (unchanged) |
| SCS Curve Number | **55** | 100 | **85.97** |
| Runoff depth (mm) | **12.83** | 100.00 | **63.65** |
| Runoff coefficient | **0.128** | 1.000 | **0.637** |

Check the text's spatial claim ("low-CN forested southwest") against the CN
raster in QGIS. The HSG remap changed the values.

### 5.11 Limitations

- **Edge effects:** "8 of the 25 candidate sites including the top-ranked one
  fall in the affected zone" → **9 of 25 lie within 5 km of the boundary; the
  top-ranked site does not** (27 km inside). The 24.4%, 25.8% and 4.9% figures
  are unchanged.
- **Soil coding:** "The soil texture raster's class coding has not been verified
  against the provider's own documentation…" → **replace.** It has been
  verified, against the `LEGEND` tag of the original SoilGrids download, and
  found wrong in three of four classes. It was corrected on 2026-10-02.
  - Say so in one or two sentences: it is a strong reproducibility point.
  - Then add the remaining exposure: the top of the shortlist rests on Loam,
    0.38% of the district, near the 250 m resolution of the input. Give the
    robustness check result from §0.1.
- **Add:** the cutoff scheme is an analyst decision (Fig. 12, 36.43 pp range).

### 5.12 Future scope

- "the shortlist concentration discussed in Section 5.2" → that concentration is
  now weaker. Reword to "the dependence on a scarce soil class".

### 6 Conclusion — rewrite the numbers and the first finding

- 18.51% → **6.44%**.
- "aggregation … −5.15 against −0.45, negligible interaction" → on area
  **−0.957 against −0.560, interaction −0.162**. **On the shortlist,
  aggregation replaces half and weighting none.**
- "drainage density carries 9.3% of the weight yet ranks first for influence,
  and its removal leaves only 2 of the top 10" → **soil** ranks first for
  perturbation influence. **Rainfall removal leaves 0 of 10.** Land cover takes
  1.32× its weight in level and only 0.08× in variance.
- 1,416.8 km² → **528.5 km²**; 15 sites (unchanged).
- **Add the analyst-decision finding**, because it is now the strongest result.

### Declarations

- "the histogram bins behind Figures 8 and 12" → generated fig08 and fig13. Also
  mention `tools/build_figure_data.py`.

---

## 3. Material with no home in the draft

These are now the paper's strongest results. Each needs a subsection, suggested
as 5.3.5 "Breakpoints and analyst decisions":

- **Fig. 12, effect magnitudes on one axis:**

  | Effect | High | Low |
  |---|---|---|
  | Rainfall scoring | +31.21 pp | −39.51 pp |
  | Classification cutoffs (range over 4 schemes) | 36.43 pp | 36.00 pp |
  | Weighting judgements | 16.23 pp | 24.83 pp |
  | Soil-legend correction | −12.07 pp | +14.38 pp |
  | Aggregation | −0.957 pp | +9.032 pp |
  | Weighting method | −0.560 pp | −0.103 pp |

- **Fig. 21:**
  - The +9.03 pp Low shift is a cutoff effect.
  - 50.3% of the area that changes class does so under **both** cutoff schemes
    tested: 6.457 pp re-ranked, 6.376 pp from the fixed cutoffs only and
    3.445 pp masked by the fixed cutoffs.
  - Removing the Low shift takes a 0.050 cutoff move; removing the High shift
    takes 0.005.
- **Fig. 22:**
  - Method disagreement is confined to scores **0.817–0.889**.
  - 22 of 25 sites are unanimous.
  - The three non-unanimous sites are ranks 23–25.

---

## 4. Never quote as current

18.51% · 2,112.6 km² · 54.79 / 26.70 · 0.7294 · 0.984 → 0.866 · Silt Loam ·
Sand / Silt Clay Loam (for codes 1 / 7) · 973 (except as a reconstruction) ·
25.6% · 3,872 vs 37 · −5.15 / −0.45 / 11.6 · 13.62 / 18.32 / 12.92 · 74.5% /
74.9% / 98.7% · 9/10, 7/10 (top-10 shared) · 30,703 / 761 / 23,988 · 25.5% ·
1,416.8 km² · 12.41% · 36 / 54 / 7 (consensus) · 30.14 / 28.19 / 29.91 (scenario
High) · drainage 1.66 · 2 of 10 for drainage · +24 pp for rainfall removal ·
34.11 / 0.796 · 29.11 / 1.292 · 19.35 / 1.260 · 6.61 / 0.710 · 22,888 High
cells · CN 70.516 · 35.366 mm · 0.354 · 42.9 · 37.0 · 9.8 · 87.16 · 16.2 pp ·
97.4% / 97.7% (whole raster) · 77% re-ranking · +26.53 pp · "Baseline
(balanced)" · "majority" for 2 of 4 · "under any cutoff scheme" ·
"11 automated checks"

---

## 5. Still to do — needs you

1. **A citation for scoring Loam at 1.00** and for the texture ordering. This is
   now the most consequential scoring choice (see §0.1).
2. **Figures 1, 3, 4, 7, 18 and 20** have to be made outside the repo. Fig. 18
   (hydrological surfaces) isn't in the generated set; build it in QGIS from the
   `derived_maps.py` rasters. Fig. 15(c) is dropped. Fig. 20's consensus box
   uses "15 sites picked by all 4 methods · 528.5 km²", not "15 unanimous sites"
   (see FIGURE_SPECS).
