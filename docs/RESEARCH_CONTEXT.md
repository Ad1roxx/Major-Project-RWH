# RESEARCH_CONTEXT.md

**Purpose.** Complete, audited context for an LLM writing a journal-length
(~40 page) research paper on this project, without access to the repository.

**Prepared:** 2026-08-26, by static analysis of every source file plus live
execution of the analysis pipeline.

**Project:** *Suitability Analysis for Rainwater Harvesting Site Planning Using
GIS* — Chandrapur district, Maharashtra, India. BTech major project, Group 11.

---

> # ⚠ RESULT NUMBERS SUPERSEDED — 2 October 2026
>
> This document was audited on 2026-08-26, **before** the soil texture legend
> was found to be wrong. Three of the four SoilGrids class codes present in the
> district were mapped to the wrong texture, and the dominant class — 77.8% of
> the district — was scoring 1.00 as Silt Loam when it is Clay Loam. Full
> record: `docs/SOIL_LEGEND_CORRECTION.md` and `CHANGELOG.md` 2026-10-02.
>
> **Everything in §0.1's [CODE] and [INFER] tiers still holds** — the method,
> the file and function index, the criticisms, the structure of the argument.
> **Every [RUN] number that depends on the soil criterion does not.** That is
> most of §16–§18 and the abstract headline in §25.
>
> ## Corrected headline figures [RUN, 2026-10-02]
>
> | | This document says | **Current** |
> |---|---|---|
> | High suitability | 18.51% — 2,112.6 km² | **6.44% — 735.0 km²** |
> | Medium | 54.79% | **52.48%** |
> | Low | 26.70% | **41.08%** |
> | Mean composite score | 0.7294 | **0.6733** |
> | Mean soil criterion score | 0.9080 | **0.5428** |
> | Most influential criterion (±20%) | drainage | **soil** (1.42 pp) |
>
> ## The abstract headline in §25 is wrong as written
>
> It claims aggregation moves highly-suitable **area** by ~5 pp. After the
> correction the factorial main effects on High-class area are **−0.957 pp**
> (aggregation) against **−0.560 pp** (weighting) — a ratio of under 2×, not
> 26×. Note these are main effects; the simple effects quoted in `CLAUDE.md`
> (0.79 pp and 0.40 pp) are a different quantity. The finding survives, but
> **on ranking, not area**: TOPSIS retains **5/10** of the baseline shortlist
> and 87.2% class agreement, Fuzzy-AHP + WLC retains **10/10** at 99.0%.
> Restate it that way.
>
> ## Factorial effects on both class shares [RUN, `tools/make_figures.py` fig 12]
>
> Measured on the shares produced by the fixed 0.65/0.85 breakpoints. The
> interaction follows the Yates convention — half the difference of the simple
> effects — so differencing the two slopes in Figure 11 gives twice it.
>
> **Recomputed 2026-10-03 from unrounded shares.** The values below replace an
> earlier set that differenced `_area_statistics`'s 2-dp display field, which
> quantised every effect to 0.01 pp — the Low-class effects came out as
> +9.030, −0.100 and 0.000, three values ending in a zero they had not earned.
> All shares now come from `gis_analysis.class_share_pct`.
>
> | Factor | High-class share | Low-class share |
> |---|---|---|
> | Rainfall scoring: percentile → fixed bands ¹ | **+31.21 pp** | **−39.51 pp** |
> | Weighting JUDGEMENTS: range over 5 scenarios ² | **range 16.23 pp** | **range 24.83 pp** |
> | Soil legend corrected (data error, not a choice) | **−12.07 pp** | **+14.38 pp** |
> | Aggregation: WLC → TOPSIS | −0.957 pp | **+9.032 pp** |
> | Weighting METHOD: AHP → Fuzzy-AHP | −0.560 pp | −0.103 pp |
> | Interaction | −0.162 pp | +0.005 pp |
>
> ² A RANGE (max − min), not a directional change, and not the same kind of
> quantity as the pairwise effects beside it — it would grow if more scenarios
> were added. It sizes the weighting judgements; do not difference it.
>
> ¹ A one-at-a-time swap evaluated under AHP+WLC, **not** a factorial main
> effect, and its size depends on the band set used (≤500 mm → 0.20 through
> >1,500 mm → 1.00, defined as `RAINFALL_FIXED_BANDS` in
> `tools/paper_figures.py`). Chandrapur's 1,189–1,714 mm spread falls entirely
> in the top three bands, which is why the effect is large.
>
> **The ordering is the same in both classes** — rainfall, soil, aggregation,
> weighting, interaction. What changes between them is only the magnitude of
> the aggregation effect, 0.96 pp on High against 9.03 pp on Low. Do not write
> that the ranking of drivers depends on the class.
>
> ## Figure-derived results added 2026-10-03 [RUN]
>
> All from `python tools/make_figures.py`, which prints every value it plots.
>
> ### Say this in the Methods: shares are area-weighted
>
> Every class share in this project is **area-weighted, not a cell count**, and
> comes from `gis_analysis.class_share_pct`. The analysis grid is EPSG:4326, so
> a cell's ground area falls with latitude — across Chandrapur the largest cell
> is **0.81%** bigger than the smallest. The Low class sits mostly in the
> southern half where cells are larger, so counting cells understates it by
> about **0.05 pp**. Two figures briefly disagreed for exactly this reason
> (41.08% against 41.04%). `tools/smoke_test.py` now asserts that every
> reporting path — the rounded field, the exact field and the area-weighted
> cumulative distribution — agrees to within 0.005 pp.
>
> ### Weighting judgements versus the weighting method — read this before §25
>
> These are **two different quantities** and the paper must not merge them.
>
> | | High-class share | Low-class share |
> |---|---|---|
> | Weighting **method** (AHP → Fuzzy-AHP, judgements fixed) | −0.560 pp | −0.103 pp |
> | Weighting **judgements** (range across the 5 scenarios) | **16.23 pp** | **24.83 pp** |
>
> The scenario range is larger than the soil correction (12.07 pp) and about
> 17× the aggregation effect. "Weighting barely matters" is true only of the
> method. Fig. 12 now carries both bars on one axis so the distinction is
> visible rather than argued.
>
> ### Scenario results (Fig. 15)
>
> | Scenario | CR | High % | Low % |
> |---|---|---|---|
> | Baseline (rainfall-led) ¹ | 0.0235 | 6.44 | 41.08 |
> | Maximise recharge | 0.0044 | 2.54 | 31.19 |
> | Community-focused | 0.0059 | 11.12 | 37.90 |
> | Low-earthwork siting | 0.0078 | **18.77** | 16.25 |
> | Fertile farmland | 0.0146 | 3.39 | 38.21 |
>
> ¹ Renamed from "Baseline (balanced)" on 2026-10-03. The baseline matrix gives
> rainfall 0.428, more than the bottom four criteria together, so "balanced"
> described the intent and not the vector.
>
> ### Criterion correlation (Fig. 19)
>
> Maximum |Pearson r| across all pairs of **scored** layers, over the 123,555
> in-district cells: **r = 0.45 (rainfall–soil)**, with **ρ = 0.44** for the
> same pair. Those two carry **0.58** of the total weight between them, so they
> share about 20% of their variance and the model counts one signal twice to
> that extent — real, but far from redundant. No significance tests: the cells
> are strongly spatially autocorrelated and a p-value on n of this size would
> be meaningless.
>
> Ties and concentration are **different defects** and should not be conflated.
> Largest single tied score, as a share of in-district cells: soil **77.8%**,
> land cover **65.6%**, drainage 11.7%, population 9.3%, slope **0.1%**,
> rainfall 0.0%. Slope is not tied; it is *concentrated*, with **86.0%** of
> cells above 0.90 under the anchored ramp (the 95.8% figure in Fig. 2 is the
> min–max version that was replaced). Both pull ρ away from r, and slope
> against land cover is where they diverge most: ρ = 0.34 against r = 0.06.
>
> ### Two measures that have both been called "effective weight" (Fig. 18)
>
> ⚠ **The level share is a mean of per-cell ratios, and is NOT reproducible
> from the criterion means.** Combining Fig. 6's means with the weights gives
> about 38.2% for rainfall and 30.9% for slope, against the 36.95% and 31.64%
> Fig. 18 reports, because mean(wᵢrᵢ/V) ≠ wᵢ·mean(rᵢ)/mean(V). The same applies
> to the Pratt index. Say so, or a reader will report it as an error.
>
> `sensitivity.single_parameter_sensitivity` measures contribution to the
> score's **level** — the mean over pixels of wᵢ·rᵢ/V. It is **not** a measure
> of influence on which cells come out High, and the paper must not present it
> as one. `sensitivity.discrimination_weights`, added 2026-10-03, measures
> contribution to the score's **variation** via the Pratt index
> βᵢ·corr(rᵢ,V) with βᵢ = wᵢ·sd(rᵢ)/sd(V), which partitions var(V) and sums
> to 100%. They disagree sharply.
>
> | Criterion | Assigned % | Level contribution (ratio) | Variance share % (ratio) |
> |---|---|---|---|
> | Rainfall | 42.85 | 36.95 (0.86×) | **71.98 (1.68×)** |
> | Slope | 22.54 | **31.64 (1.40×)** | 9.72 (**0.43×**) |
> | Soil texture | 15.35 | 12.47 (0.81×) | 9.75 (0.63×; exactly 0.6348 — 0.64 was double-rounded from 0.635) |
> | Drainage density | 9.32 | 7.18 (0.77×) | 6.50 (0.70×) |
> | Land cover | 5.97 | 7.89 (1.32×) | 0.46 (**0.08×**) |
> | Settlement prox. | 3.97 | 3.88 (0.98×) | 1.59 (0.40×) |
>
> sd of the composite = 0.1242. Only defined for a linear aggregator, so
> computed on AHP + WLC; the TOPSIS closeness coefficient is not a weighted sum.
>
> **Land cover is the extreme case, not slope.** Per unit of assigned weight,
> land cover takes **1.32×** the level and **0.08×** the variance — about five
> times less discriminating than slope's 0.43×, while also taking more of the
> level. Slope is the better-known example because of its weight, but if the
> text names a single criterion it should name land cover. Consistent with map
> removal: dropping rainfall retains **0/10** sites, dropping land cover
> retains 9/10.
>
> **Two caveats, both needed in the text.** The Pratt index partitions the
> variance of the *continuous* composite, not membership of the High class,
> which depends on the upper tail and on where the breakpoints fall — which is
> why Fig. 17, measuring class share, ranks the criteria differently. Soil has
> the largest ±20% perturbation effect (1.42 pp) and only 9.75% of the
> variance; that is not a contradiction, because soil puts 77.8% of the
> district on one tied score, so reweighting it slides a large uniform block
> across the 0.85 breakpoint without separating anything inside it. And the
> index is defined only for a linear aggregator, so it is computed on AHP+WLC;
> the TOPSIS closeness coefficient is not a weighted sum.
>
> ### Aggregation and the breakpoints (Fig. 13)
>
> Cumulative share of in-district cells at or below each breakpoint, AHP
> weighting throughout (n = 123,555):
>
> | | ≤ 0.65 | ≤ 0.85 |
> |---|---|---|
> | AHP + WLC | **41.084%** | 93.559% |
> | AHP + TOPSIS | **50.111%** | 94.354% |
>
> These are area-weighted and so equal the Low share and 100 − High share that
> Fig. 10 reports for the same surfaces. The 9.03 pp gap at 0.65 against
> 0.80 pp at 0.85 is why the aggregation rule
> moves the Low class an order of magnitude more than the High class. Class
> flows, WLC → TOPSIS: Medium→Low **1,146.4 km²**, Low→Medium 116.2,
> High→Medium 146.4, Medium→High 55.6; net Low gain 1,030.2 km² = 9.03 pp.
> **The classifier assigns Low at score ≤ 0.65 and High at score > 0.85**
> (`gis_analysis._classify_suitability`); every legend and label uses that
> convention.
>
> ### Map removal, recomputed 2026-10-03 from unrounded shares (Fig. 17)
>
> `sensitivity.py` had the same defect as the factorial effects: both
> `one_way_sensitivity` and `map_removal_sensitivity` differenced the rounded
> `percent` field. Both now read `class_share_pct`. Change in High-class share
> on removing each criterion, with the remaining five renormalised:
>
> | Criterion | Δ High (pp) | Top-10 sites retained |
> |---|---|---|
> | Soil texture | **+7.67** (was +7.68) | 4/10 |
> | Drainage density | +5.12 | 3/10 |
> | Rainfall | +2.54 | **0/10** |
> | Settlement prox. | +0.49 | 5/10 |
> | Land cover | −1.06 | 9/10 |
> | Slope | −3.11 | 5/10 |
>
> ±20% perturbation, mean |Δ| High: soil 1.42, rainfall 1.24, slope 1.16,
> drainage 0.61, land cover 0.27, settlement 0.08 pp. Unchanged at 2 dp.
>
> **A figure that did NOT change: rainfall's level contribution is 36.95%**
> (exactly 36.9459). **At 1 dp it is 36.9, not 37.0.** The 37.0 printed until
> 4 October 2026 was double rounding: 36.9459 → 36.95 (stored at 2 dp) →
> 37.0. The same thing turned the 42.849% assigned weight into 42.9. Figure 18
> now formats the unrounded `*_exact` fields from sensitivity.py. Nothing in
> `single_parameter_sensitivity` was altered, and it is a per-cell mean of
> ratios rather than an area share, so area-weighting does not apply to it.
> The same holds for the Pratt index: both are per-cell statistics over the
> composite, not shares of district area, and the paper should say so.
>
> ### The shortlist depends on a scarce soil class (Fig. 9) [RUN]
>
> **State this in the Limitations.** Soil texture class areas, in-district,
> area-weighted:
>
> | Code | Texture | Score | Share | Area |
> |---|---|---|---|---|
> | 1 | Clay | 0.25 | 18.612% | 2,124.0 km² |
> | 4 | Clay Loam | 0.60 | 77.825% | 8,881.7 km² |
> | 6 | Sandy Clay Loam | 0.80 | 3.187% | 363.7 km² |
> | 7 | **Loam** | **1.00** | **0.376%** | **42.9 km²** |
>
> **4 of the top 5 candidate sites sit on Loam**, the only texture scored 1.00,
> which is 43 km² of 11,412. The top of the shortlist therefore depends on a
> class covering under 0.4% of the district being mapped correctly — the same
> exposure that produced the 2026-10-02 legend error. SoilGrids is 250 m,
> resampled nearest to the ~300 m grid, so a class this small is near the
> resolution of the input. **Robustness check for the Discussion:** rescore
> Loam at 0.80, like Sandy Clay Loam, and report how the shortlist moves.
>
> ### Step classes vs ramps — the plateau needed both (Fig. 8) [RUN]
>
> The 973-cell plateau at exactly 1.000 is a **historical reconstruction** and
> must never be quoted as a current result. Running the same reconstructed
> step-class scheme on the two soil legends:
>
> | Soil legend | Step-class cells at exactly 1.000 |
> |---|---|
> | In use at the time (superseded) | **973** |
> | Corrected (since 2026-10-02) | **1** |
>
> Interpolated ramps give 0 under either. The plateau required flat-topped
> class breaks **and** a dominant soil class wrongly scored 1.00; neither alone
> produces it. The case for ramps over step classes rests on the IQR
> comparison in Fig. 2 and the discrimination measure in Fig. 18, both on
> current data — not on the 973.
>
> ### Method disagreement is a narrow band (Fig. 22) [RUN]
>
> Every cell above **0.8887** is High under all 4 method combinations; no cell
> below **0.8515** is, and below **0.8174** no combination calls any cell High.
> Disagreement occupies **0.817–0.889** (0.033 below the 0.85 breakpoint,
> 0.039 above) — the same mechanism Fig. 21 quantifies. Of the 25
> candidate sites, **22 are unanimous, 2 at 3/4, 1 at 2/4**, and the three
> non-unanimous are ranks **23 (0.8592), 24 (0.8584), 25 (0.8536)** — the
> bottom of the list, not the top. "Scoring well is not the same as every
> method agreeing" overstates it: scoring well is almost the same as unanimity;
> what is unstable is scoring *just* well enough.
>
> ### Exact AHP weights [RUN]
>
> Reported to 3 dp throughout. The exact values, in case a reader recomputes:
> slope 0.2253604, rainfall **0.4284938**, drainage 0.0931907, soil 0.1535363,
> land cover 0.0597465, settlement 0.0396723. Note rainfall is **0.428** at
> 3 dp — it is below 0.4285, so half-up rounding does not take it to 0.429.
>
> ### The shortlist depends on a scarce soil class (Fig. 9) [RUN]
>
> **State this in the Limitations.** Soil texture class areas, in-district,
> area-weighted:
>
> | Code | Texture | Score | Share | Area |
> |---|---|---|---|---|
> | 1 | Clay | 0.25 | 18.612% | 2,124.0 km² |
> | 4 | Clay Loam | 0.60 | 77.825% | 8,881.7 km² |
> | 6 | Sandy Clay Loam | 0.80 | 3.187% | 363.7 km² |
> | 7 | **Loam** | **1.00** | **0.376%** | **42.9 km²** |
>
> **4 of the top 5 candidate sites sit on Loam**, the only texture scored 1.00,
> which is 43 km² of 11,412. The top of the shortlist therefore depends on a
> class covering under 0.4% of the district being mapped correctly — the same
> exposure that produced the 2026-10-02 legend error. SoilGrids is 250 m,
> resampled nearest to the ~300 m grid, so a class this small is near the
> resolution of the input. **Robustness check for the Discussion:** rescore
> Loam at 0.80, like Sandy Clay Loam, and report how the shortlist moves.
>
> ### Step classes vs ramps — the plateau needed both (Fig. 8) [RUN]
>
> The 973-cell plateau at exactly 1.000 is a **historical reconstruction** and
> must never be quoted as a current result. Running the same reconstructed
> step-class scheme on the two soil legends:
>
> | Soil legend | Step-class cells at exactly 1.000 |
> |---|---|
> | In use at the time (superseded) | **973** |
> | Corrected (since 2026-10-02) | **1** |
>
> Interpolated ramps give 0 under either. The plateau required flat-topped
> class breaks **and** a dominant soil class wrongly scored 1.00; neither alone
> produces it. The case for ramps over step classes rests on the IQR
> comparison in Fig. 2 and the discrimination measure in Fig. 18, both on
> current data — not on the 973.
>
> ### Method disagreement is a narrow band (Fig. 22) [RUN]
>
> Every cell above **0.8887** is High under all 4 method combinations; no cell
> below **0.8515** is, and below **0.8174** no combination calls any cell High.
> Disagreement occupies **0.817–0.889** (0.033 below the 0.85 breakpoint,
> 0.039 above) — the same mechanism Fig. 21 quantifies. Of the 25
> candidate sites, **22 are unanimous, 2 at 3/4, 1 at 2/4**, and the three
> non-unanimous are ranks **23 (0.8592), 24 (0.8584), 25 (0.8536)** — the
> bottom of the list, not the top. "Scoring well is not the same as every
> method agreeing" overstates it: scoring well is almost the same as unanimity;
> what is unstable is scoring *just* well enough.
>
> ### Exact AHP weights [RUN]
>
> Reported to 3 dp throughout. The exact values, in case a reader recomputes:
> slope 0.2253604, rainfall **0.4284938**, drainage 0.0931907, soil 0.1535363,
> land cover 0.0597465, settlement 0.0396723. Note rainfall is **0.428** at
> 3 dp — it is below 0.4285, so half-up rounding does not take it to 0.429.
>
> ### Ranking against cutoffs — the cell partition (Fig. 21) [RUN]
>
> ⚠ **Supersedes an earlier netted version of this analysis.** Subtracting the
> churn under share-matched cutoffs from the churn under fixed ones is NOT a
> decomposition: they are different sets of cells, and for the Low class the
> difference is negative (−2.970 pp), because the fixed 0.65 holds cells in Low
> that a matched cutoff releases. **Do not write "77% of the disagreement is
> re-ranking"** — that figure came from the netted version and treats one set as
> a subset of the other. The correct figure is **50.3%**.
>
> Cutoffs matching WLC's class sizes are the quantiles of the TOPSIS surface,
> **0.5998** and **0.8452**, against the fixed 0.65 and 0.85.
>
> **A three-way partition of cells**, which sums correctly by construction:
>
> | Category | pp of district | km² |
> |---|---|---|
> | Re-ranked under **both** cutoff schemes | **6.457** | **736.9** |
> | Changes only under the **fixed** cutoffs | 6.376 | 727.7 |
> | Re-ranked but **masked** by the fixed cutoffs | 3.445 | 393.2 |
>
> - robust + induced = **12.833 pp**, the area that actually changes class.
> - robust + masked = **9.902 pp**, the area that changes under matched cutoffs.
> - **50.3%** of what changes class changes under BOTH cutoff schemes tested (two schemes,
>   not all possible ones).
>
> Per origin class (robust + induced = area leaving that class), which
> reconciles with the Fig. 13 Sankey: High 1.283, Medium 10.533, Low 1.018,
> summing to 12.833.
>
> **The cutoff asymmetry is the mechanism.** Removing the +9.027 pp Low shift
> takes a **0.050** move of the lower cutoff; removing the −0.795 pp High shift
> takes only **0.005**. That is why the aggregation rule appears to move the Low
> class an order of magnitude more than the High class.
>
> **The breakpoint scheme is itself an analyst decision**, so the one algorithm
> effect that looked large is substantially another analyst-decision effect.
> Fig. 12 now carries it as its own bar: a **range over four standard
> schemes** (fixed 0.65/0.85, equal interval, terciles by area, natural breaks)
> of **36.43 pp** on High and **36.00 pp** on Low. The earlier single swap to
> the 33rd/67th percentile split (+26.53 / −8.04 pp) is superseded.
>
> Spearman ρ = **0.9643**, a per-cell statistic over the two surfaces.
> Shortlist retention **5/10** and **18/25**.
>
> ⚠ **Shortlist overlap depends on how many sites were extracted.** Candidate
> extraction is best-per-tile with a 5 km separation rule and is **not nested**:
> the top 10 of a 10-site run is not the first 10 of a 25-site run (5/10 against
> 8/10). Always extract at the size being reported. `algorithms.py` and
> Fig. 17(b) use the same rule.
>
> ### Edge-effect test (Fig. 14)
>
> Reclassification rate between AHP+WLC and AHP+TOPSIS by distance to the
> district boundary, **area-weighted** like every other share: 0–2 km **6.48%**
> (n = 12,654 cells), 2–5 km 6.64% (17,495), 5–10 km 8.45% (24,283),
> 10–20 km 16.70% (35,328), >20 km **17.53%** (33,795); district overall
> **12.83%**. That overall figure now reconciles exactly with the Sankey in
> Fig. 13(b): 1,146 + 146 + 116 + 56 = 1,464 km² of 11,412 km² = 12.83%, so
> 87.17% is unchanged. The rate *falls* towards the boundary (ratio 0.37×),
> which rules out an edge artefact from rim gap-filling. It does not establish
> a distance mechanism; the gradient is geographic.
>
> ### Consensus area (Fig. 16)
>
> Collapsed to shared categories, since the denominators differ (4 against 5):
>
> | | Unanimous | Half or more | Minority | Never High |
> |---|---|---|---|---|
> | Across 4 method combinations | **528.5 km²** | 201.8 | 60.8 | 10,621.3 |
> | Across 5 weighting scenarios | **239.9 km²** | 333.8 | 1,893.8 | 8,944.8 |
>
> Same finding as Fig. 12 in map form: the scenarios scatter the High class far
> more than the algorithms do — 1,894 km² of minority agreement against 61.

---

## 0. HOW TO USE THIS DOCUMENT

### 0.1 Evidence tiers — respect these

Every substantive claim below carries a tag. **Do not promote a claim to a
higher tier when writing.**

| Tag | Meaning |
|---|---|
| **[CODE]** | Directly readable in the source. Cite file/function given. |
| **[RUN]** | Measured by executing the project on 2026-08-26. Reproducible via §24. |
| **[DOC]** | Asserted in project documentation (`docs/METHODOLOGY.md`, `docs/PAPER_GUIDE.md`, `CHANGELOG.md`) but **not independently re-verified** in this audit. Usually a historical measurement. |
| **[INFER]** | My inference from the code. Reasonable but not stated anywhere. **Do not present as established fact.** |
| **[ABSENT]** | Does not exist in the repository. Named so nobody writes it up. |

### 0.2 The three rules

1. **Never report a validation metric.** No AUC, accuracy, precision, recall,
   F1, kappa, or RMSE exists. See §18.
2. **Never describe a machine-learning model.** None is trained, fitted, or
   even imported. See §19.
3. **Never report an annual runoff volume.** Runoff exists only per design
   storm. See §16.3.

### 0.3 Honest note on the 40-page target

The repository supports roughly **10–14 pages** of original methodology and
results at journal density. Reaching 40 pages requires substantial material the
repository does not contain: an extended literature review, a theoretical
treatment of MCDA, comparative discussion against published studies, and
expanded figures/tables. §25 gives a realistic page budget showing which
sections draw on the repo and which the writer must source externally. **Padding
the results sections with invented experiments would be misconduct** — expand the
review, theory and discussion instead.

---

## 1. RESEARCH PROBLEM

### 1.1 The problem as the project frames it — [DOC]

From the project's own framing (presentation deck, `README.md`,
`docs/PAPER_GUIDE.md` §1):

Chandrapur district receives substantial monsoon rainfall, yet experiences
water scarcity. Rainfall is seasonally concentrated, much of it leaves as
surface runoff, and groundwater is under pressure. Siting rainwater harvesting
(RWH) structures is currently ad hoc or manual, and manual site selection cannot
economically evaluate an 11,412 km² district at sub-kilometre resolution.

### 1.2 The methodological problem — [CODE] + [DOC]

This is the more defensible framing for a journal paper, and it is what the code
actually addresses. Three specific weaknesses in the standard GIS-MCDA workflow
are identified and answered:

**P1 — Data-driven normalisation destroys criterion information.** Min–max
rescaling maps criterion values onto 0–1 using the observed range of one
district's raster. Measured on this data, that left **97.4% of slope pixels and
97.7% of population pixels scoring above 0.90** [DOC — `docs/PAPER_GUIDE.md`
§6.1; measured before the fix, not re-verifiable now that the code is gone].
Applied to categorical layers it scored classes by their *code number*, so IGBP
class 17 (water) scored 1.00 and class 13 (urban) 0.75 while forest scored 0.00.

**P2 — AHP weights are asserted, not tested.** The standard criticism is that
the result is whatever the analyst decided. A consistency ratio establishes
internal coherence, not correctness.

**P3 — Method choice is rarely isolated.** Papers typically report one
weighting × one aggregation and cannot say how much of the result is the data
and how much is the method.

### 1.3 What this project does about them — [CODE]

- **P1 →** all scoring moved into `criteria.py` as explicit, physically anchored
  reclassification tables and interpolated ramps. No data-driven rescale
  anywhere in the pipeline.
- **P2 →** three independent sensitivity analyses in `sensitivity.py`.
- **P3 →** four algorithms over one shared criteria stack (`algorithms.py`) plus
  cross-method consensus (`consensus.py`).

---

## 2. OBJECTIVES AND CONTRIBUTIONS

### 2.1 Objectives — [DOC], from `README.md` and the project deck

1. Integrate multi-source spatial data for Chandrapur into a common analysis grid.
2. Derive thematic criterion layers (slope, soil, rainfall, LULC, drainage,
   settlement proximity).
3. Assign criterion weights by AHP with a verified consistency ratio.
4. Combine criteria into a continuous suitability surface and classify it
   Low/Medium/High.
5. Extract and rank candidate sites with per-site justification.
6. Quantify the robustness of the result to the weighting and method choices.

### 2.2 Contributions to lead with — [CODE] + [RUN]

**C1 — Reproducible, transferable criterion scoring.** Scores come from fixed
class breaks and interpolated ramps anchored to physical thresholds. A 4° slope
maps to the same score in any district. `criteria.py`.

**C2 — Quantified robustness rather than asserted weights.** Three sensitivity
analyses: one-way ±20% perturbation, map removal (Lodwick et al. 1990), and
single-parameter effective weights (Napolitano & Fabbri 1996). `sensitivity.py`.

**C3 — Method comparison on a shared criteria stack.** Four algorithms over
identical inputs isolate the effect of the method itself. **The headline finding
— that the aggregation rule matters far more than the weighting rule — is the
paper's most novel result.** `algorithms.py`.

**C4 — Cross-method consensus as ground-truth-free robustness.** Borda-aggregated
site consensus and a per-pixel agreement raster. Lets the paper make a defensible
robustness claim while validation data is unavailable. `consensus.py`.

**C5 — Site-level explainability.** Every ranked site reports per-criterion
normalised score, weighted contribution, raw measured value, and a
criteria-satisfied list. `gis_analysis.score_stack()`, lines building `details`.

---

## 3. STUDY AREA

| Quantity | Value | Tier |
|---|---|---|
| District | Chandrapur, Maharashtra, India | [DOC] |
| Bounding box | 78.7960 – 79.9893 °E, 19.4587 – 20.7305 °N | **[RUN]** `tools/inspect.py data/boundary.geojson` |
| Area analysed | 11,412.5 km² | **[RUN]** |
| Official district area | 11,443 km² (99.7% captured) | [DOC] |
| Boundary geometry | 1 MultiPolygon, GADM ADM2, EPSG:4326 | **[RUN]** |
| Population | 2,204,307; density 193 persons/km² | [DOC] — deck slide 16, census figure, **not in repo data** |
| Mean annual rainfall (this study) | 1,492.9 mm/yr district mean | **[RUN]** — `data/rainfall.tif` metadata tag `DISTRICT_MEAN_MM` |
| Commonly cited long-term normal | ≈1,245 mm | [DOC] — `build_rainfall.py:EXPECTED_MEAN_MM`, used only as a sanity check |

**Context the paper needs but the repo does not contain** [ABSENT]: Tadoba-Andhari
Tiger Reserve extent, coal-mining footprint, agro-climatic zone, aquifer type,
groundwater-level trends, administrative tehsil breakdown. Source these
externally and cite them.

---

## 4. SYSTEM ARCHITECTURE

### 4.1 The central architectural decision — [CODE]

The pipeline is split into a **weight-independent** stage and a **weight-dependent**
stage. This is the single most consequential design decision in the codebase and
deserves a paragraph in the paper.

```
build_criteria_stack(data_dir, max_grid_size, use_cache)   ~0.90 s  [DOC]
    ├── reads boundary, rivers, 5 rasters
    ├── builds the common grid + district mask
    ├── reprojects, gap-fills
    ├── derives drainage density and settlement distance
    └── scores all six criteria to 0–1
    → cached in gis_analysis._STACK_CACHE, keyed (abspath, grid_size)

score_stack(stack, weights, ..., aggregator, algorithm)    ~0.15 s  [DOC]
    ├── aggregates (WLC or TOPSIS) with per-pixel weight renormalisation
    ├── applies the ≥80% coverage gate
    ├── classifies by fixed thresholds
    ├── computes area statistics
    ├── extracts + ranks candidate sites
    └── builds per-site explainability
```

**Why it matters** [INFER, but strongly supported]: scenario switching,
sensitivity sweeps, algorithm comparison and consensus all re-score the *same*
stack. A 12-run sensitivity sweep therefore costs ~2 s rather than ~12 s, and —
more importantly for validity — **every variant is guaranteed to be scored on
byte-identical criterion rasters**, so any difference between them is
attributable to the method alone. `algorithms.py` docstring states this
explicitly [CODE].

`run_ahp_analysis(data_dir, ...)` is a thin convenience wrapper calling both.

### 4.2 Module map — [CODE]

| Module | LOC | Responsibility |
|---|---|---|
| `gis_analysis.py` | 983 | Grid, masking, reprojection, gap fill, distance/density, overlay, classification, candidate extraction |
| `app.py` | 781 | Streamlit UI (entry point) |
| `criteria.py` | 451 | **All** 0–1 scoring. Every threshold and lookup table |
| `validation.py` | 378 | ROC-AUC harness, candidate proximity, per-algorithm ranking |
| `consensus.py` | 357 | Variant generation, Borda consensus, agreement raster |
| `utils/map_renderer.py` | 345 | Folium map, legend, site popups |
| `algorithms.py` | 320 | WLC/TOPSIS aggregators, Fuzzy-AHP, cross-algorithm comparison |
| `sensitivity.py` | 309 | Three sensitivity analyses |
| `derived_maps.py` | 260 | SCS-CN, runoff, drainage surfaces |
| `exports.py` | 249 | Result → CSV/GeoJSON/GeoTIFF/PNG with provenance |
| `tools/inspect.py` | 232 | Data profiling CLI |
| `build_rainfall.py` | 229 | CHIRPS → mean annual surface |
| `ahp.py` | 155 | Pairwise matrix, geometric-mean weights, CR, scenario presets |
| `tools/smoke_test.py` | 118 | End-to-end app test |
| `setup_data.py` | 116 | Filename standardisation (⚠ unverified, mutates `data/`) |

**Total: 5,286 lines of Python** [RUN — `wc -l`].

### 4.3 Architectural invariant — [CODE]

`criteria.py` is the sole owner of scoring. No threshold, class break or lookup
table appears anywhere else in the pipeline. `gis_analysis.py`, `algorithms.py`,
`derived_maps.py` and `app.py` all import it as `C` and read constants from it.
Stated as a project convention in `CLAUDE.md`. This is what makes the parameter
table in §22 complete and auditable.

---

## 5. TECHNOLOGY STACK — [CODE], from `requirements.txt`

| Layer | Package | Pin | Role |
|---|---|---|---|
| Geospatial vector | `geopandas` | ≥0.14.0 | Boundary, rivers, site GeoDataFrames |
| Raster I/O | `rasterio` | ≥1.3.0, **<1.5.0** | Read/reproject/write GeoTIFF |
| Geometry | `shapely` | ≥2.0.0 | Polygonisation, point geometry |
| Projection | `pyproj` | ≥3.5.0 | CRS transforms |
| Vector driver | `fiona` | ≥1.9.0 | GeoJSON/shapefile I/O |
| Web app | `streamlit` | ≥1.32.0 | UI |
| Interactive map | `folium` | ≥0.16.0 | Leaflet map |
| Arrays | `numpy` | ≥1.24.0 | All numerics |
| Tables | `pandas` | ≥2.0.0 | Site tables, CSV |
| Scientific | `scipy` | ≥1.11.0 | Exact EDT, nearest-value fill, convolution, Spearman |
| Figures | `matplotlib` | ≥3.8.0 | Static PNG maps |

**Desktop GIS:** QGIS, used manually for the upstream exports (clipping,
reprojection, GDAL Slope). Not scripted — see §7.4 [DOC].

**Notable absences** [ABSENT]: no `scikit-learn`, no `torch`/`tensorflow`, no
`reportlab`, no `pytest`. There is no ML, no automated report generation, and no
test framework (`tools/smoke_test.py` is a standalone script).

**Version note** [CODE, `requirements.txt`]: rasterio 1.5.0 installed with
missing compiled extensions on Windows; pinned below it. 1.4.4 verified working
on Python 3.11 / Windows 11.

**Not a dependency:** `python-pptx` 1.0.2 is present in the venv but imported by
no module — installed 2026-08-25 to read the presentation, deliberately excluded
from `requirements.txt` [CODE + `CHANGELOG.md` 2026-08-25].

---

## 6. DATASETS

### 6.1 Sources — [DOC] for provenance, **[RUN]** for measured properties

| Layer | Source (as documented) | Native resolution **[RUN]** | CRS **[RUN]** | Role |
|---|---|---|---|---|
| District boundary | GADM India ADM2 | vector, 1 MultiPolygon | EPSG:4326 | Study-area mask |
| Drainage network | HydroRIVERS v1.0 (HydroSHEDS), Asia | vector, 776 features | EPSG:4326 | Drainage density |
| Rainfall | CHIRPS v3.0 annual, 2014–2024 | 0.05° (~5.3 km) | EPSG:4326 | Rainfall criterion |
| Slope | HydroSHEDS CONDEM → GDAL Slope | 88.03 × 91.42 m | EPSG:32644 | Slope criterion |
| Soil texture | SoilGrids 250 m | 220.23 × 228.47 m | EPSG:32644 | Soil criterion |
| Land cover | MODIS MCD12Q1 `LC_Type1` (IGBP) | 0.004167° (~463 m) | EPSG:4326 | Land-cover criterion |
| Population | WorldPop India 2020 | 880.88 × 912.28 m | EPSG:32644 | Settlement proximity |

**Seven source datasets, six criteria** — population feeds a derived
settlement-distance criterion rather than entering directly.

### 6.2 Measured layer properties — **[RUN]**, 2026-08-26

Whole-raster statistics (`tools/inspect.py`):

| File | Shape | dtype | NoData | Valid % | Range |
|---|---|---|---|---|---|
| `rainfall.tif` | 33 × 32 | float32 | −9999 | 100.0% | 1,140.0 – 1,823.2 mm/yr |
| `slope.tif` | 1533 × 1414 | float32 | −9999 | 64.9% | 0.00 – 72.21° |
| `soil_texture.tif` | 621 × 571 | uint8 | 255 | 62.7% | classes {1, 4, 6, 7} |
| `lulc.tif` | 306 × 287 | uint8 | 255 | 65.1% | 11 of 17 IGBP classes present: {4,5,7,8,9,10,11,12,13,14,17} |
| `population.tif` | 154 × 142 | float32 | −99999 | 64.1% | 1.88 – 9,101.1 people/km² |

**In-district statistics after reprojection onto the analysis grid** — these are
the numbers to quote in a results table, because they describe what the model
actually saw:

| Criterion | Min | Mean | Max |
|---|---|---|---|
| Slope (°) | 0.000 | 1.466 | 56.041 |
| Mean annual rainfall (mm/yr) | 1,189.4 | 1,500.3 | 1,714.3 |
| Population density (people/km²) | 2.81 | 205.9 | 8,506.9 |
| Drainage density (km/km²) | 0.0000 | 0.2328 | 0.8482 |
| Distance to settlement (km) | 0.000 | 6.969 | 30.656 |

⚠ **Whole-raster and in-district figures differ** and both appear in the project
docs. `rainfall.tif` extends 0.20° beyond the district, so its whole-raster range
(1,140–1,823, mean 1,471.9) is wider than the in-district range (1,189–1,714,
mean 1,500.3). Slope's whole-raster max is 72.21° but only 56.04° falls inside
the district. **State which domain you are quoting.**

### 6.3 Rivers layer detail — **[RUN]**

776 features (756 LineString, 20 MultiLineString). `LENGTH_KM`: min 0.43, median
3.22, mean 3.875, max 16.88. Total in-district channel length **2,766 km**.
Attributes include `ORD_STRA` (Strahler order), `ORD_CLAS`, `ORD_FLOW`,
`CATCH_SKM`, `UPLAND_SKM`, `DIS_AV_CMS`.

**Only `ORD_STRA` is documented as used conceptually; the density computation
uses geometry alone, not stream order** [CODE — `_river_length_grid()` reads no
attributes]. Do not claim stream order weights the density.

### 6.4 Rainfall surface construction — [CODE], `build_rainfall.py`

1. Read the district bounding box **+ 0.20° margin** (`BUFFER_DEG`) as a window
   from each global CHIRPS raster — the 7200 × 2400 globals are never fully
   loaded.
2. Treat any value ≤ **−100** (`NODATA_CUTOFF`) as NoData. **CHIRPS ships −9999
   as fill but does not declare it in the GeoTIFF header**, so rasterio will not
   mask it automatically. This is a real trap worth a footnote.
3. Handles both download shapes: annual files (`chirps-v3.0.2014.tif`) averaged
   directly, or monthly files summed within each year first.
4. Average the 11 annual totals → mean annual surface.
5. Sanity-check the district mean against 1,245 mm ± 20%.
6. Write `data/rainfall.tif` with provenance in GeoTIFF metadata tags.

Verified tags on the shipped file **[RUN]**: `SOURCE=CHIRPS annual precipitation`,
`YEARS=2014-2024`, `N_YEARS=11`, `AGGREGATION=mean of annual totals`,
`UNITS=mm/year`, `DISTRICT_MEAN_MM=1492.9`, `GENERATED_BY=build_rainfall.py`,
`GENERATED_ON=2026-08-04`.

### 6.5 The wet-decade finding — [DOC], worth reporting

The 11-year mean runs ~20% above the commonly cited long-term normal of
≈1,245 mm. Per `criteria.py` and `docs/PAPER_GUIDE.md` §6.8 this is a real
signal, not a unit error: 2014, 2015 and 2017 sit near 1,220–1,260 mm while every
other year in the window runs 1,425–1,930 mm (interannual sd 198 mm). The recent
decade is genuinely wetter than the older baseline.

⚠ The per-year figures are **[DOC]** — recorded in the changelog from the
original build run, not re-derived in this audit. Re-run `build_rainfall.py` and
capture its per-year output if the paper quotes them.

### 6.6 Files present but NOT used by the pipeline — [CODE] + **[RUN]**

| File | Status |
|---|---|
| `data/dem.tif` (38 MB) | ⚠ **Contains no valid pixels — 100% NoData.** Verified by windowed reads at four locations and `statistics()`, all empty. Referenced only in `app.py`'s data-status panel and `setup_data.py`'s rename map; **no analysis module reads it**. |
| `data/rainfall_previous.tif` | Superseded placeholder from before the CHIRPS build |
| `data/Clipped_rivers.*` (shapefile) | Fallback if `rivers.geojson` is absent |
| `data/osm_water_candidates_UNVERIFIED.geojson` | 158 OSM points. **Not RWH structures.** See §18.3 |
| `data/chirps-v3.0.YYYY.tif` × 11 | Inputs to `build_rainfall.py`, not read at analysis time |

⚠ **Consequence for the paper:** because `dem.tif` is empty, the stated
provenance of `slope.tif` (HydroSHEDS CONDEM → GDAL Slope) **cannot be verified
from the repository**. The slope raster itself is valid and populated, and its
88 × 91 m cell size in EPSG:32644 is consistent with a reprojected 3-arc-second
(~90 m) source [INFER]. Describe the slope provenance as documented, not as
reproducible.

---

## 7. PREPROCESSING

### 7.1 Common analysis grid — [CODE], `_make_common_grid()`

Built from the boundary's bounding box. The longer axis is set to
`DEFAULT_MAX_GRID_SIZE = 450` px and the shorter scaled to preserve aspect ratio.

Verified **[RUN]**:

| Quantity | Value |
|---|---|
| Grid | 450 × 422 cells |
| In-district cells | 123,555 |
| Cell size | 0.3125 km (N–S) × 0.2956 km (E–W) |
| Cell area | 0.0924 km² |
| Analysis CRS | EPSG:4326 |

Because the grid is geographic, longitude cell width shrinks with latitude.
`_pixel_size_km()` evaluates E–W size at the grid's **centre latitude**, and
`_pixel_area_km2_per_row()` computes true cell area **per raster row** for area
statistics — so reported areas are not a naive cell-count × constant [CODE].

Constants: `KM_PER_DEG_LAT = 110.574`, `KM_PER_DEG_LON_EQUATOR = 111.320`.

### 7.2 Reprojection — [CODE], `_load_raster_to_grid()`

Every raster is warped onto the common grid with `rasterio.warp.reproject`.

**Resampling discipline** — explicit in `raster_config`:

| Criterion | Method | Reason |
|---|---|---|
| slope | bilinear | continuous |
| rainfall | bilinear | continuous |
| population | bilinear | continuous |
| soil | **nearest** | categorical — averaging class codes invents classes |
| lulc | **nearest** | categorical |

This is worth a sentence in the paper; it is a correctness issue, not a
preference.

### 7.3 District masking and gap filling — [CODE]

`_rasterize_boundary()` rasterises the polygon with `all_touched=True` to a
boolean mask.

`_fill_nearest(data, domain)` fills NoData **inside** the district from the
nearest valid pixel using SciPy's `distance_transform_edt(return_indices=True)`.
Rationale [CODE docstring]: source layers stop short of the boundary at different
places; discarding the whole rim would shrink the study area, and the affected
layers vary slowly in space.

Measured gap fill **[RUN]**, as a share of the 123,555 in-district cells:

| Criterion | Cells filled | Share |
|---|---|---|
| Soil | 2,675 | 2.2% |
| Population | 2,510 | 2.0% |
| Slope | 1,303 | 1.1% |
| LULC | 138 | 0.1% |
| Rainfall | 0 | 0.0% |

Rainfall needs no fill because `build_rainfall.py` reads a 0.20° margin —
a direct benefit of building that layer in code rather than by hand.

### 7.4 Upstream manual preprocessing — [DOC], `docs/METHODOLOGY.md` §12

`slope.tif`, `soil_texture.tif`, `lulc.tif`, `population.tif` and
`rivers.geojson` were clipped to the Chandrapur outline **in QGIS before
entering the project**. This is not scripted and not reproducible from the repo.
It also causes the edge-effect limitation in §21.3.

---

## 8. CRITERION NORMALISATION — the scoring model

All of this is [CODE], `criteria.py`. This section is the paper's methodological
core.

### 8.1 Four normalisation forms

| Form | Function | Applied to |
|---|---|---|
| Anchored interpolated ramp (cost) | `score_ramp()` | Slope |
| Anchored interpolated ramp (benefit) | `score_ramp()` | Drainage density |
| Categorical class lookup | `score_categorical()` | Soil texture, LULC |
| Continuous percentile rank (benefit) | `score_percentile_benefit()` | Rainfall |
| Moderate-optimal piecewise curve | `moderate_optimal()` | Settlement proximity |

All are NaN-in/NaN-out.

### 8.2 Slope — cost, interpolated ramp

`SLOPE_RAMP_DEG`, units **degrees**:

| Slope | Score | Rationale in source |
|---|---|---|
| 0.0° | 1.00 | dead level — ideal ponding / percolation tanks |
| 1.0° | 0.95 | near-level |
| 3.0° | 0.85 | very gentle — ideal for most RWH structures |
| 5.0° | 0.68 | gentle — suitable, mild earthwork |
| 10.0° | 0.42 | moderate — check dams only, higher cost |
| 15.0° | 0.20 | steep — marginal |
| 25.0° | 0.08 | very steep |
| 90.0° | 0.05 | impractical to impound |

Linearly interpolated between anchors. Resulting in-district scores **[RUN]**:
min 0.066, mean 0.924, max 1.000, **6,276 distinct values**.

### 8.3 Soil texture — categorical

`SOIL_TEXTURE_SCORES`, default 0.30 for unrecognised codes:

| Code | Class | Score | Rationale |
|---|---|---|---|
| 1 | Sand | 0.55 | very high infiltration, poor retention/stability |
| 4 | Silt Loam | **1.00** | best infiltration/retention balance |
| 6 | Sandy Clay Loam | 0.80 | good infiltration, stable |
| 7 | Silt Clay Loam | 0.50 | low infiltration, limits recharge |

Objective is **recharge**, so moderate-to-good infiltration scores highest —
pure sand infiltrates fastest but retains nothing and gives poor embankment
stability. This is a defensible, non-obvious modelling choice worth a paragraph.

⚠ **Unverified coding** [CODE — explicit warning in source]: the source file
carries a `⚠ VERIFY BEFORE SUBMISSION` comment noting that standard SoilGrids
USDA texture coding (TEXMHT) numbers classes differently (1 = clay … 12 = sand).
**The paper must list this as a limitation.** In-district scores **[RUN]**: only
**4 distinct values**, mean 0.908 — Silt Loam dominates.

### 8.4 Land cover — categorical, all 17 IGBP classes

`LULC_SCORES`, default 0.30. Full table (all 17 listed so the table generalises
beyond the 11 classes present in Chandrapur):

| Code | Class | Score |
|---|---|---|
| 1–4 | Evergreen/Deciduous Needleleaf & Broadleaf Forest | 0.30 |
| 5 | Mixed Forest | 0.35 |
| 6 | Closed Shrubland | 0.55 |
| 7 | Open Shrubland | 0.70 |
| 8 | Woody Savanna | 0.60 |
| 9 | Savanna | 0.70 |
| 10 | Grassland | 0.85 |
| 11 | Permanent Wetland | 0.20 |
| 12 | **Cropland** | **1.00** |
| 13 | Urban and Built-up | 0.10 |
| 14 | Cropland / Natural Vegetation Mosaic | 0.90 |
| 15 | Permanent Snow and Ice | 0.00 |
| 16 | Barren | 0.65 |
| 17 | Water Bodies | 0.00 |

Rationale [CODE]: cropland highest (irrigation demand + low acquisition cost +
runoff generation); **forest deliberately low** because Chandrapur's forest is
largely protected (Tadoba-Andhari), construction is restricted, and infiltration
is already good. This is a locally-reasoned choice, not a generic table — say so.

In-district **[RUN]**: 10 distinct scores, mean 0.855.

### 8.5 Rainfall — continuous percentile rank

`score_percentile_benefit()`:

```
score = RAINFALL_FLOOR + (1 − RAINFALL_FLOOR) × percentile_rank
RAINFALL_FLOOR = 0.20
```

Rank is computed **within the district**, over district pixels only (the raster
is masked before scoring — `gis_analysis.py`, rainfall branch).

**Justification** [CODE]: the whole district receives adequate monsoon rainfall,
so what discriminates *sites* is relative rainfall within the study area; and it
maximises discrimination across the 1,189–1,714 mm spread instead of collapsing
it into one or two absolute bands.

**Acknowledged trade-off** [CODE + DOC]: fixed mm bands would transfer better to
another district at the cost of within-district discrimination.
`score_continuous_breaks()` exists to support that alternative but is not used.
`RAINFALL_QUANTILE_CUTS`/`_SCORES` are retained in source **for reference only**
— the five-class quintile version was replaced because it gave the wettest 20%
an identical 1.00.

In-district **[RUN]**: min 0.200, mean 0.600, max 1.000, 8,001 distinct values.
**The mean is mechanically ≈0.6 by construction** — this matters for interpreting
the effective-weight result in §17.3.

### 8.6 Drainage density — benefit, interpolated ramp

**Computation** [CODE], `_river_length_grid()` then `_drainage_density()`:

1. Reproject rivers to EPSG:32644, densify to **100 m segments**, reproject back.
2. For each segment, compute true length via local degree→km scaling at the
   segment midpoint latitude; accumulate into the cell containing the midpoint
   (`np.add.at`).
3. Convolve the length grid with a **circular kernel of radius 2.5 km**
   (`DRAINAGE_DENSITY_WINDOW_KM`), divide by true window area → km/km².

Rasterising lines directly would only give a boolean "channel present" mask,
which cannot produce a density — worth stating.

`DRAINAGE_DENSITY_RAMP`:

| Density (km/km²) | Score |
|---|---|
| 0.00 | 0.10 |
| 0.10 | 0.25 |
| 0.20 | 0.50 |
| 0.30 | 0.72 |
| 0.40 | 0.88 |
| 0.90 | 1.00 |

**Window size rationale** [CODE]: a 1 km window over a 0.3 km grid is only ~3×3
cells and produces a noisy, speckled surface; 2.5 km (≈20 km²) gives a smooth
field that still resolves sub-district variation.

⚠ **Calibration warning, explicit in source** [CODE]: these breaks are calibrated
to a **HydroRIVERS-derived** network, which is thresholded to larger channels.
District-wide density is **0.242 km/km²** **[RUN]** — an order of magnitude below
the 0.5–2.0 km/km² bands used in studies working from DEM-extracted networks. If
the network were re-derived by flow accumulation, the breaks would need
recalibration; the class *shares* are what should be preserved, not the numbers.
**This must appear in the limitations section.**

Verified **[RUN]**: 2,766 km of channel / 11,414 km² = 0.242 km/km² district-wide;
local range 0.00–0.85. In-district scores: min 0.100, mean 0.517, max 0.988,
8,354 distinct values.

### 8.7 Settlement proximity — moderate-optimal

**This criterion replaced a plain "population density, lower is better" measure**
and the direction was corrected during development [DOC — `CHANGELOG.md`
2026-07-29 §B]. The design intent [CODE]: a site in suitable terrain but *set
back* from the settlement it serves.

Definition: a **settlement pixel** is any pixel with population density ≥
`SETTLEMENT_DENSITY_THRESHOLD = 400 people/km²`. Distance from every pixel to the
nearest settlement pixel is computed by SciPy's **exact anisotropic Euclidean
distance transform** (`sampling=(dy_km, dx_km)`), with a 2-pass chamfer fallback
if SciPy is unavailable [CODE, `_distance_km()`].

`moderate_optimal()` curve, piecewise-linear:

| Distance | Score | Constant |
|---|---|---|
| 0 km | 0.05 | `SETTLEMENT_SCORE_AT_ZERO` |
| 1 km | 0.97 | `band_edge` (default 0.97) |
| **3 km** | **1.00** | centre of `SETTLEMENT_PEAK_KM = (1, 5)` |
| 5 km | 0.97 | `band_edge` |
| 15 km | 0.10 | `SETTLEMENT_FLOOR`, at peak_hi + `SETTLEMENT_FALLOFF_KM = 10` |

**Why a gentle peak rather than a flat plateau** [CODE docstring]: a flat top
would give every location in a 4 km-wide band an identical 1.00, which was a
major source of tied candidate sites. The band still reads as "1–5 km is
optimal" — everything inside scores ≥0.97 — but the centre is strictly preferred,
so ranking is possible.

Verified **[RUN]**: 6.6% of pixels classed as settlement; in-district scores min
0.050, mean 0.643, max 1.000, 1,740 distinct values.

**Empirical caution** — see §18.3. A diagnostic against OSM water features
suggests real structures sit *closer* to villages than this band assumes. That is
not validation, but it is a known open question (`TODO.md` §A3).

---

## 9. WEIGHTING — AHP

### 9.1 The pairwise comparison matrix — [CODE], `ahp.py:AHPEngine.__init__`

Criteria order throughout the codebase: **slope, rainfall, drainage, soil, lulc,
population**.

|  | slope | rainfall | drainage | soil | lulc | population |
|---|---|---|---|---|---|---|
| **slope** | 1 | 1/3 | 3 | 2 | 4 | 5 |
| **rainfall** | 3 | 1 | 5 | 3 | 6 | 7 |
| **drainage** | 1/3 | 1/5 | 1 | 1/2 | 2 | 3 |
| **soil** | 1/2 | 1/3 | 2 | 1 | 3 | 4 |
| **lulc** | 1/4 | 1/6 | 1/2 | 1/3 | 1 | 2 |
| **population** | 1/5 | 1/7 | 1/3 | 1/4 | 1/2 | 1 |

**Rationale, verbatim from source** [CODE]: *"rainfall is the water source and
dominates; slope governs whether the water can be retained at all; soil controls
infiltration; drainage locates the runoff; LULC and settlement proximity are
feasibility/demand modifiers rather than primary physical drivers."*

### 9.2 Weight derivation — [CODE], `calculate_weights()`

Geometric-mean (priority vector) method:

```
w_i = (∏_j a_ij)^(1/n) / Σ_k (∏_j a_kj)^(1/n)
```

Consistency, `_calculate_consistency_ratio()`:

```
λ_max = mean( (A·w)_i / w_i )
CI    = (λ_max − n) / (n − 1)
CR    = CI / RI
```

`RANDOM_INDEX` is the full Saaty table for n = 1…10:
{1:0.00, 2:0.00, 3:0.58, 4:0.90, 5:1.12, **6:1.24**, 7:1.32, 8:1.41, 9:1.45, 10:1.49}.

### 9.3 Verified results — **[RUN]**

| Criterion | Weight |
|---|---|
| Rainfall | **0.4285** |
| Slope | 0.2254 |
| Soil texture | 0.1535 |
| Drainage density | 0.0932 |
| Land cover | 0.0597 |
| Settlement proximity | 0.0397 |

**λ_max = 6.1460, CI = 0.0292, RI = 1.24, CR = 0.0235 < 0.10.** ✓

### 9.4 Fuzzy-AHP — [CODE], `algorithms.py`

Buckley's geometric-mean method. `FUZZY_DELTA = 1.0` — ±1 step on the Saaty
scale.

**Fuzzification** (`_to_tfn`): a judgement of 3 → (2, 3, 4); its reciprocal 1/3 →
(1/4, 1/3, 1/2). Spread clipped at scale ends, so 1 → (1, 1, 2) and 9 → (8, 9, 9).

**Steps:** fuzzify → row geometric mean per component → fuzzy weight by dividing
by the fuzzy column sum → defuzzify by centroid (l+m+u)/3 → normalise.

**Two method choices that deserve explicit paragraphs:**

1. **Buckley, not Chang** [CODE docstring]: *"Chang's extent analysis is the more
   commonly cited approach but is known to assign zero weight to criteria that
   are genuinely relevant — a documented criticism of the method. Buckley's
   geometric mean cannot produce a zero weight."*

2. **Additive spread, not multiplicative** [CODE, explicit ⚠ in source]: a
   uniform multiplicative spread a → (a/s, a, a·s) **scales every row's fuzzy
   geometric mean by the same constant, so the fuzziness cancels exactly during
   normalisation and Fuzzy-AHP returns weights identical to crisp AHP.** The
   source records that an earlier multiplicative implementation reproduced the
   crisp weights to 3 decimal places. The additive form is asymmetric at the scale
   ends, which is what makes the fuzzy weights genuinely differ. **This is a real
   trap that few papers mention — it is worth a footnote or a short subsection.**

Verified Fuzzy-AHP weights **[RUN]**: rainfall 0.417, slope 0.224, soil 0.159,
drainage 0.097, lulc 0.062, population 0.041.

---

## 10. AGGREGATION

### 10.1 Weighted Linear Combination — [CODE], `aggregate_wlc()` / `_weighted_overlay()`

```
S(x,y) = Σ_{i∈V} w_i · r_i(x,y)  /  Σ_{i∈V} w_i
```

where V is the set of criteria with data at (x,y). **Fully compensatory** — a
high rainfall score offsets a poor slope score in direct proportion to weights.

**Per-pixel renormalisation** is the important detail: a pixel missing one
criterion is scored on the remainder with weights rescaled to sum to 1, so the
output stays on a true 0–1 scale rather than being artificially depressed at the
edge of a layer.

### 10.2 Coverage gate — [CODE]

`MIN_WEIGHT_COVERAGE = 0.80`. A pixel is scored **only if ≥80% of the total AHP
weight has data there**.

Rationale [CODE]: *"without this gate an edge pixel holding just rainfall + LULC
could be scored 1.00 from 2 criteria and outrank a genuine site evaluated on all
6."* On the current inputs, gap filling means no district pixel is actually
dropped **[RUN — the pipeline emits no "excluded" note]**, but the gate is a
structural safeguard and applies identically in both aggregators.

### 10.3 TOPSIS — [CODE], `aggregate_topsis()`

```
d⁺ = √( Σ w_i² (1 − r_i)² )
d⁻ = √( Σ w_i²  r_i²      )
C  = d⁻ / (d⁺ + d⁻)
```

**Ideals are theoretical, not observed** — A⁺ = w_i (r_i = 1) and A⁻ = 0
(r_i = 0), the best and worst *attainable* values on the 0–1 criterion scale.

**Justification** [CODE docstring]: *"Using observed extremes would make the
result depend on the data range — the same defect as the min–max normalisation
removed in Sprint 1 — and would stop the score being comparable between districts
or between scenario runs."* This is a deliberate deviation from textbook TOPSIS
and **must be stated in the paper.**

Weights are renormalised per pixel and the same coverage gate applies, so WLC and
TOPSIS differ **only** in the aggregation rule.

### 10.4 The algorithm catalogue — [CODE], `ALGORITHMS`

Two independent choices → four combinations:

| Algorithm | Weighting | Aggregation |
|---|---|---|
| AHP + WLC | crisp Saaty | fully compensatory |
| AHP + TOPSIS | crisp Saaty | closeness to ideal |
| Fuzzy-AHP + WLC | Buckley TFN | fully compensatory |
| Fuzzy-AHP + TOPSIS | Buckley TFN | closeness to ideal |

---

## 11. CLASSIFICATION

[CODE], `_classify_suitability()` + `criteria.SUITABILITY_THRESHOLDS`.

| Class | Rule |
|---|---|
| High | score > 0.85 |
| Medium | 0.65 < score ≤ 0.85 |
| Low | score ≤ 0.65 |

`CLASSIFICATION_MODE = "fixed"`. A `"percentile"` mode (33rd/67th) remains
available as a fallback but is not used.

**Why fixed and not percentile** [CODE, explicit ⚠ in source]: *"A percentile
split (33rd/67th) is self-fulfilling: it always reports ~33% of the district as
highly suitable whatever the underlying scores, so the resulting percentage is an
artefact of the method rather than a finding."* The earlier percentile
implementation duly returned 32.9 / 34.0 / 33.1 [DOC].

⚠ **STALE COMMENT — do not quote it.** `criteria.py` states, immediately below
`SUITABILITY_THRESHOLDS`, that the thresholds yield *"roughly 31% High / 46%
Medium / 23% Low"*. **The measured values are 18.51 / 54.79 / 26.70** **[RUN]**.
The comment predates a later change and was never updated. Use §16.1.

---

## 12. CANDIDATE SITE EXTRACTION

[CODE], `_extract_top_locations()`. Three stages:

**Stage 1 — best pixel per tile.** The grid is divided into a **5 × 5** tile
grid; the highest-ranking pixel inside the High-suitability mask is taken from
each tile. Purpose: spread sites across the district rather than clustering them
in one favourable belt.

**Stage 2 — separated global maxima.** Remaining slots are filled from
district-wide maxima. A deterministic hash-based jitter (`h % 1000 / 1000 × 1e-6`)
breaks exact ties reproducibly.

**Stage 3 — renumber by score.** `_rank_by_score()` sorts all selected sites by
`(suitability_score, tiebreak_value)` descending and renumbers 1…N.

**Stage 3 is not cosmetic** [CODE docstring]: *"the two selection stages each emit
their own descending run, so a stage-2 site (a global maximum) routinely
outscores a late stage-1 site (the best pixel of a mediocre tile). Numbering in
selection order would publish rank #22 with a higher score than rank #13."* This
was a real defect fixed on 2026-08-12 [DOC — `CHANGELOG.md` 2026-08-12 (e)].

**Constraints:** `DEFAULT_TOP_N = 25`; `DEFAULT_MIN_SEPARATION_KM = 5.0`,
enforced by haversine distance against all previously selected sites.

**Tie-break raster** [CODE], `_tiebreak_raster()`: a continuous 0–1 surface used
**only** to order candidates that tie on the discrete suitability score. It
averages: (1 − slope/15 clipped), rainfall percentile rank, drainage-density
percentile rank, and closeness to the centre of the settlement band. Applied with
a `1e-3` coefficient — large enough to separate exact ties, too small to reorder
distinct scores.

**Consequence worth explaining in the paper** [INFER, but well-supported]: the
5 km separation constraint means a large contiguous High-suitability zone may
contain only one or two candidate markers. A reader looking at the map will see
High-suitability areas with no site in them; this is the constraint operating, not
a defect.

---

## 13. EXPLAINABILITY

[CODE], built in `score_stack()` when assembling `details`. Per candidate site:

| Field | Content |
|---|---|
| `rank`, `lon`, `lat`, `suitability_score` | Position and aggregate score |
| `criteria_scores` | Normalised 0–1 score per criterion at that pixel |
| `criteria_satisfied` | Criteria whose score ≥ `SATISFIED_THRESHOLD = 0.66` |
| `raw_values.slope_deg` | Slope in degrees |
| `raw_values.soil_class` | Human-readable class name via `SOIL_TEXTURE_LABELS` |
| `raw_values.lulc_class` | Human-readable class name via `LULC_LABELS` |
| `raw_values.drainage_density` | km/km² |
| `raw_values.settlement_km` | Distance in km |

`exports.py:_site_records()` additionally emits **`contrib_<criterion>` =
w_i × r_i** per criterion, ordered by descending AHP weight — the weighted
contribution that shows *how much each factor actually drove* the score.

The Streamlit UI adds a **side-by-side compare panel** (Site A vs Site B with
per-criterion arrows and an overall winner) [CODE, `app.py` lines ~428–470].

**This is C5 and most comparable papers report only an aggregate score.**

---

## 14. SCENARIOS

[CODE], `ahp.py:SCENARIOS`. Five presets. A scenario is a **different set of
pairwise judgements over the same six criteria** — no additional data is
involved.

Matrices are generated from an importance ranking by `matrix_from_levels()`,
which snaps each pair's ratio to the nearest Saaty 1–9 value, keeping the matrix
**consistent by construction**.

Level vectors in criteria order (slope, rainfall, drainage, soil, lulc, population):

| Scenario | Levels | Rationale (verbatim from source) |
|---|---|---|
| Baseline (balanced) | hand-built matrix | "Rainfall-led general-purpose weighting used throughout the report." |
| Maximise recharge | [6,5,2,7,2,1] | "Getting water into the aquifer: soil infiltration and gentle slope dominate; demand near settlements is close to irrelevant." |
| Community-focused | [3,7,2,2,5,6] | "Serving people: settlement proximity and cropland demand carry the weight; physical recharge efficiency matters less." |
| Low-earthwork siting | [8,3,4,2,5,1] | "Construction feasibility **PROXY** — flat ground, easily cleared land cover, short feeder works. **Not a cost model**; the project holds no land-value or unit-rate data." |
| Fertile farmland | [4,6,3,8,7,2] | "Agricultural benefit — soil texture and cropland cover lead, then rainfall. **PROXY**: reweights the existing six criteria; **no soil-fertility dataset** (organic carbon, N/P/K, pH) is held." |

⚠ **Two scenarios are explicitly self-labelled PROXY in the source.** The paper
must name them as such. "Low-earthwork siting" is not a cost analysis; "fertile
farmland" is not a fertility model.

Verified **[RUN]**:

| Scenario | CR | High % | slope | rainfall | drainage | soil | lulc | settlement |
|---|---|---|---|---|---|---|---|---|
| Baseline | 0.0235 | 18.51 | 0.225 | **0.428** | 0.093 | 0.154 | 0.060 | 0.040 |
| Maximise recharge | 0.0044 | 30.14 | 0.266 | 0.226 | 0.095 | **0.273** | 0.095 | 0.045 |
| Community-focused | 0.0059 | 18.77 | 0.107 | 0.245 | 0.094 | 0.094 | 0.214 | **0.245** |
| Low-earthwork siting | 0.0078 | 29.91 | **0.367** | 0.121 | 0.172 | 0.096 | 0.200 | 0.043 |
| Fertile farmland | 0.0146 | 28.19 | 0.135 | 0.204 | 0.100 | **0.257** | 0.229 | 0.074 |

All five pass CR < 0.10 comfortably.

---

## 15. CONSENSUS ACROSS METHOD VARIATIONS

[CODE], `consensus.py`. Two independent axes: **algorithms** (4 variants,
weighting matrix fixed) and **scenarios** (5 variants, algorithm fixed at
AHP + WLC).

### 15.1 Site consensus by Borda count

Sites are matched across variants **by position, not rank** — each variant
extracts candidates independently, so the same location shifts by a pixel or two.
Match radius **2.0 km**, chosen to sit well inside the 5 km minimum separation
enforced within a single run, so a cluster can never absorb two distinct sites
from the same variant [CODE docstring].

Greedy clustering, strongest site first. **Borda count:** within one variant a
site at rank r of N scores N − r + 1; a variant that did not select the site
scores **0**. The zero is deliberate — *"a method staying silent about a site is
not evidence in its favour."*

Consensus ranking key: `(−borda, −n_variants, −best_score)`.

### 15.2 Agreement raster

`agreement_raster()` counts, per pixel, how many variants class it **High**.
`agreement_stats()` converts to area/share using true per-row cell area.
`agreement_png()` renders a discrete-colormap figure.

### 15.3 Verified results — **[RUN]**

**Across the 4 algorithms:**

| Measure | Value |
|---|---|
| Distinct locations proposed | 36 |
| Selected by **all 4** | **15** |
| District High in all 4 | **12.41% — 1,416.8 km²** |
| High in 3 of 4 | 0.70% — 79.8 km² |
| High in 2 of 4 | 5.50% — 627.6 km² |
| High in 1 of 4 | 0.61% — 70.1 km² |
| High in none | 80.77% — 9,218.0 km² |

Top consensus sites (all 4/4): (79.3658, 20.4295) Borda 100; (79.7673, 19.6664)
Borda 96; (79.3262, 20.4549) Borda 88; (79.6570, 20.3532) Borda 88.

**Across the 5 scenarios:**

| Measure | Value |
|---|---|
| Distinct locations proposed | 54 |
| Selected by **all 5** | **7** |
| District High in all 5 | **10.66% — 1,217.1 km²** |
| High in 4 of 5 | 9.00% — 1,027.2 km² |
| High in 3 of 5 | 6.37% — 727.5 km² |
| High in 2 of 5 | 4.91% — 559.9 km² |
| High in 1 of 5 | 7.26% — 828.5 km² |
| High in none | 61.79% — 7,052.3 km² |

**Why this belongs in the paper** [CODE docstring]: *"consensus is
method-agnostic robustness evidence that needs no ground truth. 'Selected
independently by all four methods' is a claim the project can make today. 'More
accurate than TOPSIS' is not."*

---

## 16. RESULTS

**All figures in this section are [RUN], measured 2026-08-26.**

### 16.1 Suitability distribution

Continuous surface: **n = 123,555**, min **0.2563**, max **0.9839**, mean
**0.7294**, median **0.7415**, sd **0.1263**. **108,229 distinct values**;
**exactly 1 pixel at the maximum.**

| Class | Threshold | Share | Area |
|---|---|---|---|
| **High** | > 0.85 | **18.51%** | **2,112.6 km²** |
| **Medium** | 0.65 – 0.85 | **54.79%** | **6,252.6 km²** |
| **Low** | ≤ 0.65 | **26.70%** | **3,047.3 km²** |

Total analysed: 11,412.5 km².

[DOC] `docs/PAPER_GUIDE.md` notes 18.5% sits inside the 19–34% "suitable" range
reported by comparable studies. **Verify that range against the actual cited
papers before repeating it** — it is not derivable from this repository.

### 16.2 Top five candidate sites

| Rank | Lon | Lat | Score | Slope | Soil | Land cover | Drainage density | Dist. to settlement |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 km |
| 2 | 79.7673 | 19.6664 | 0.982 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 km |
| 3 | 79.4195 | 20.4775 | 0.977 | 0.26° | Silt Loam | Cropland | 0.62 | 2.1 km |
| 4 | 79.3262 | 20.4549 | 0.977 | 0.35° | Silt Loam | Cropland | 0.40 | 4.7 km |
| 5 | 79.6570 | 20.3532 | 0.976 | 0.12° | Silt Loam | Cropland | 0.58 | 5.9 km |

25 sites extracted, 5 km minimum separation, scores **0.984 (rank 1) → 0.866
(rank 25), strictly descending**. Authoritative table: `outputs/rwh_sites.csv`.

**Pattern worth discussing** [INFER]: all top-5 sites are Silt Loam + Cropland on
near-flat ground. That is the model behaving consistently with its scoring tables
(soil 1.00, LULC 1.00, slope ≈1.00) — but it also means the shortlist is
concentrated in one landscape type, which is a legitimate discussion point about
compensatory aggregation.

### 16.3 Derived hydrological surfaces

Produced by `derived_maps.py`, **design storm P = 100 mm**:

| Surface | Min | Max | Mean |
|---|---|---|---|
| Drainage density (km/km²) | 0.000 | 0.848 | 0.233 |
| SCS Curve Number (AMC II) | 30 | 100 | 70.516 |
| Runoff depth (mm) | 0.00 | 100.00 | 35.366 |
| Runoff coefficient | 0.000 | 1.000 | 0.354 |

**Method** [CODE]: Curve Number from IGBP land cover × Hydrologic Soil Group
(HSG derived from soil texture: 1→A, 4→B, 6→C, 7→D), AMC II, good hydrologic
condition, after USDA-NRCS TR-55 analogues. Then
`S = 25400/CN − 254`, `Ia = 0.2S`, `Q = (P − Ia)²/(P + 0.8S)` for P > Ia.

**Why a design storm and not the annual total** [CODE, extended docstring]:
SCS-CN is an **event** model. At P = 1,493 mm/yr, forest (CN 55) yields a runoff
coefficient of 0.85 and built-up (CN 85) 0.96 — every land cover collapses into
the same value and the map carries no spatial information. At 100 mm the same
classes spread 0.13–0.61. Feeding an annual total is *"a common shortcut in the
literature and it is wrong here, measurably so."* **This is a good, citable
methodological point.**

**Runoff is deliberately NOT an AHP criterion** [CODE]: Curve Number is a
function of LULC and soil, and runoff additionally of rainfall — all three are
already weighted criteria, so including runoff would silently double-weight them.
**Do not describe runoff as a criterion.**

---

## 17. SENSITIVITY ANALYSIS — three independent methods

All [CODE] in `sensitivity.py`; all results **[RUN]**.

### 17.1 One-way ±20% weight perturbation

`one_way_sensitivity()`. For each criterion in turn, its weight is scaled by
(1 ± δ), δ = 0.20, and the remaining weights rescaled to sum to 1
(`perturb_weights()`). Retention is measured on the **top 10**, sites matched by
position within **2 km**.

| Criterion | Dir | Weight | Retained | Max shift | High % | Δ |
|---|---|---|---|---|---|---|
| rainfall | − | 0.428→0.343 | 7/10 | 3 | 19.45 | +0.94 |
| rainfall | + | 0.428→0.514 | 8/10 | 1 | 18.53 | +0.02 |
| slope | − | 0.225→0.180 | 10/10 | 0 | 17.11 | −1.40 |
| slope | + | 0.225→0.270 | 8/10 | 1 | 20.22 | +1.71 |
| soil | − | 0.154→0.123 | 10/10 | 0 | 17.44 | −1.07 |
| soil | + | 0.154→0.184 | 10/10 | 0 | 19.78 | +1.27 |
| drainage | − | 0.093→0.075 | 8/10 | 2 | 20.33 | +1.82 |
| drainage | + | 0.093→0.112 | 9/10 | 0 | 17.02 | −1.49 |
| lulc | − | 0.060→0.048 | 10/10 | 0 | 18.58 | +0.07 |
| lulc | + | 0.060→0.072 | 10/10 | 0 | 18.50 | −0.01 |
| population | − | 0.040→0.032 | 10/10 | 0 | 18.86 | +0.35 |
| population | + | 0.040→0.048 | 8/10 | 2 | 18.15 | −0.36 |

**Headline:** *Varying each AHP weight by ±20% retains **90%** of the top-10
sites on average (**70%** worst case), with a maximum rank shift of **3**.*

Influence on High-suitability area (mean absolute Δ, percentage points):
**drainage 1.66** > slope 1.55 > soil 1.17 > rainfall 0.48 > settlement 0.35 >
land cover 0.04.

**Discussion point:** weight magnitude and influence are not the same thing.
Drainage carries the fourth-largest weight but the largest influence; rainfall
carries the largest weight but is spatially smooth, so perturbing it barely moves
the map.

### 17.2 Map removal sensitivity (Lodwick, Monson & Svoboda, 1990)

`map_removal_sensitivity()`. Each criterion is removed entirely (weight → 0) and
the remaining weights renormalise.

| Criterion | Weight | S index (%) | Max (%) | Mean \|ΔV\| | Top-10 retained | High % | Δ High % |
|---|---|---|---|---|---|---|---|
| Rainfall | 0.428 | **17.374** | 50.05 | 0.1140 | **1/10** | 42.46 | +23.95 |
| Slope | 0.225 | 8.979 | 38.47 | 0.0592 | 9/10 | 13.27 | −5.24 |
| Soil | 0.154 | 5.301 | 38.61 | 0.0365 | 10/10 | 14.12 | −4.39 |
| Drainage | 0.093 | 4.280 | 13.80 | 0.0303 | **2/10** | 26.87 | +8.36 |
| Land cover | 0.060 | 2.501 | 16.92 | 0.0164 | 10/10 | 19.07 | +0.56 |
| Settlement | 0.040 | 1.780 | 8.53 | 0.0122 | 9/10 | 20.75 | +2.24 |

⚠ **Index adaptation — must be stated in the paper** [CODE docstring]. The
original formulation is S = |V/N − V′/n| / V × 100, where /N and /n convert a
weighted *sum* over N (then n) parameters into a per-parameter average. This
project's aggregation **already divides by the sum of the weights present**, so V
and V′ are both on a 0–1 scale; applying /N and /n again would normalise twice.
The index used is therefore:

```
S_i = mean over district pixels of |V − V′_i| / V × 100
```

**Two findings to write up:**

1. **The S index tracks weight order, but site retention does not.** Removing
   drainage changes the surface by only 4.28% — fourth of six — yet leaves just
   **2 of the top 10 sites standing**, worse than removing slope (S 8.98%, 9/10
   retained). Drainage barely moves the *map* but almost completely reorders the
   *shortlist*, because it has the highest spatial variance of the six criteria
   and is what separates otherwise near-identical candidates. This corroborates
   §17.1 independently.
2. **Removing rainfall inflates High to 42.46%.** Rainfall is scored by
   percentile rank, so it averages ~0.6 and acts as a *brake* on the composite;
   remove it and everything else — mostly high-scoring across the district —
   pushes the score up. **A criterion can be *restrictive* rather than merely
   *important*, which the weight alone does not tell you.**

### 17.3 Single-parameter / effective weight (Napolitano & Fabbri, 1996)

`single_parameter_sensitivity()`. Effective weight
**W_i = mean over district pixels of (w_i · r_i) / V × 100**, compared with the
theoretical weight w_i × 100.

| Criterion | Theoretical % | Effective % | SD | Ratio |
|---|---|---|---|---|
| Rainfall | 42.85 | 34.11 | 8.87 | **0.796** |
| Slope | 22.54 | 29.11 | 5.25 | **1.292** |
| Soil | 15.35 | 19.35 | 3.94 | 1.260 |
| Land cover | 5.97 | 7.25 | 2.61 | 1.214 |
| Drainage | 9.32 | 6.61 | 3.88 | **0.710** |
| Settlement | 3.97 | 3.57 | 2.06 | 0.901 |

**The explanation is the interesting part.** Criteria that score uniformly well
across Chandrapur contribute more than their assigned weight — slope (1.29×)
because the district is very flat (mean 1.47°), soil (1.26×) because Silt Loam
dominates and scores 1.00. Criteria that score uniformly poorly contribute less —
drainage (0.71×) because district density is only 0.242 km/km². **Rainfall
(0.80×) is a special case: percentile-rank scoring mechanically fixes its mean
near 0.6, capping its effective contribution regardless of its 0.428 weight.**

**This is the formal answer to "are your weights meaningful?"** Assigned weight
and realised influence are different quantities, and the gap is explained by the
distribution of each criterion across the study area, not by the AHP judgements.

---

## 18. VALIDATION — methodology only, NO RESULTS

### 18.1 What is implemented — [CODE], `validation.py`

Three functions, all written and their arithmetic verified, **none ever run on
real data**:

**`roc_auc(positive_scores, background_scores)`** — ROC-AUC via the Mann-Whitney
U statistic, with mid-ranks for ties. Implemented directly so the project needs
no scikit-learn. Equivalent to the probability that a randomly chosen positive
scores higher than a randomly chosen background point.

**`validate(result, stack, structures_path, ...)`** — presence-only design:
sample the suitability surface at known structure locations and at random
in-district background points; report AUC, mean scores, and the share of
structures falling in High / High+Medium. Background sampling
(`_background_points()`) excludes a **1.0 km** buffer around known positives, uses
**5 background points per positive**, seed **42**.

**`candidate_proximity(result, stack, ...)`** — a *different* question from AUC.
AUC asks whether the *surface* scores known structures highly; this asks whether
the *shortlist* lands near them. Distance from each candidate to the nearest known
structure, compared against random in-district points, summarised as the
Mann-Whitney probability on negated distances. **This is the "existing versus
candidate sites" comparison.**

**`validate_all_algorithms(stack, ...)`** — runs all four algorithms against the
same structures and ranks them by AUC. *"the only honest way to say which one
performs best."*

### 18.2 Why there is no result — [CODE] + **[RUN]**

`data/rwh_structures.geojson` **does not exist**. Every entry point returns
`{"status": "missing_data"}` and `python validation.py` exits non-zero. The
module docstring states explicitly: *"Until it does, this module reports that the
input is missing and exits — it will not invent a number."*

Expected schema: point geometry in any CRS with a valid `crs`; optional `type`
and `year` attributes. Target **150–300 points**. Suggested sources [DOC]:
MGNREGS asset records, Jalyukt Shivar records, the district water conservation
office, or digitising visible check dams and farm ponds from satellite imagery.

### 18.3 The OSM diagnostic — ⚠ NOT A VALIDATION RESULT

[DOC — `CHANGELOG.md` 2026-08-25 §A] + **[RUN]** for the file's properties.

`data/osm_water_candidates_UNVERIFIED.geojson` holds **158 OpenStreetMap points**
tagged as artificial water features inside the district (verified: 158 Point
features, EPSG:4326, columns `kind`, `name`, `verified`, `notes`, `osm_id`,
`osm_type`). These were pushed through the AUC harness as a code-path exercise.

Indicative figures, **for internal reasoning only**:

| Measure | Value |
|---|---|
| Overall AUC against the 158 points | 0.482 |
| AUC of the settlement-proximity criterion alone | 0.379 |

**These must NOT appear in the paper as validation.** OSM artificial water
polygons are not RWH structures — they include farm ponds, quarry pits, tanks and
mine water. The overall figure is indistinguishable from chance.

**However, the breakdown is informative and may be worth a sentence in future
work:** the entire deficit came from settlement proximity; every other criterion
scored at or above chance. This suggests real water structures sit *closer* to
villages than the 1–5 km moderate-optimal band assumes. It is a hypothesis about
a criterion definition, logged as `TODO.md` §A3, not a finding.

### 18.4 What the paper should say

> The four algorithms differ measurably, but *differing* is not *being better*.
> Naming an outperformer requires an external standard — agreement with RWH
> structures that already exist. Until that inventory is assembled and
> `validation.py` produces a per-algorithm AUC, the paper reports that the methods
> **differ**, quantifies by how much, and states that ranking them by accuracy is
> future work.

What the paper *can* claim today is **consensus** (§15): method-agnostic
robustness requiring no ground truth.

---

## 19. "TRAINING METHODOLOGY" — there is none

**[ABSENT] — read this section carefully; it prevents the most likely error.**

The user's brief asked for training methodology. **This project contains no
machine learning of any kind.** Specifically:

- No model is trained, fitted, or optimised.
- No training/validation/test split exists.
- No loss function, no cross-validation, no hyperparameter search.
- `scikit-learn`, `torch` and `tensorflow` are **not installed and not imported**.
- The only "learned" quantity in the entire pipeline is the AHP priority vector,
  which is a **deterministic geometric mean of a hand-specified 6 × 6 matrix** —
  closed-form arithmetic, not estimation from data.

**The correct framing for the paper:** this is a *knowledge-driven* (expert-driven)
MCDA model, in contrast to *data-driven* approaches. That contrast is itself worth
a paragraph in the literature review — knowledge-driven models need no training
data, which is precisely why they are used where inventories are unavailable, and
their weakness is exactly the subjectivity that §17 quantifies.

**Planned but not implemented** [DOC — `TODO.md` §C2, "Sprint 4"]: a learned
suitability model using the same criteria stack as features, with the structure
inventory as labels, compared against AHP. **It is blocked on the same missing
file as validation.** Describe it in Future Work as planned; never in Methodology.

---

## 20. DESIGN DECISIONS — each worth a paragraph

Ten decisions with evidence behind them. These are what a reviewer will probe.

**D1 — Fixed reclassification, not min–max.** [CODE + DOC] Min–max left 97.4% of
slope and 97.7% of population pixels above 0.90, and scored categorical layers by
code number. Roughly 48% of the total weight was flat or semantically inverted.
Fixed tables remove both failures and make scores transferable across districts.

**D2 — Interpolated ramps, not step classes.** [CODE + DOC] Step classes give
every pixel in the best band an identical score. With six criteria doing that,
**973 pixels scored exactly 1.000 on everything**, so the top sites were tied.
Interpolating between the *same* anchors raised distinct scores from 47,495 to
**108,229** and reduced pixels sharing the maximum from **973 to 1**. The second
figure is re-verified **[RUN]**: exactly 1 pixel at the maximum, 108,229 distinct.

**D3 — Fixed classification thresholds, not percentiles.** [CODE] See §11.

**D4 — Drainage *density*, not distance to river.** [CODE + DOC] Distance to the
nearest channel is a siting-convenience measure; density is what the RWH
literature uses and what indicates where runoff concentrates. Verified during
development: 2,765.6 km binned against 2,767.7 km of input geometry, **0.08%
loss** [DOC].

**D5 — Settlement proximity as moderate-optimal, not "population, lower is
better".** [CODE + DOC] Direction corrected 2026-07-29. See §8.7.

**D6 — Theoretical ideals in TOPSIS.** [CODE] See §10.3.

**D7 — Buckley, not Chang, for Fuzzy-AHP; additive, not multiplicative,
fuzzification.** [CODE] See §9.4. The multiplicative-cancellation trap is a
genuine contribution to state.

**D8 — Design storm for runoff, not annual total.** [CODE] See §16.3.

**D9 — Per-pixel weight renormalisation plus a coverage gate.** [CODE] See §10.

**D10 — Pipeline split into cached stack + cheap scoring.** [CODE] See §4.1.
Guarantees that method comparisons differ only by method.

### 20.1 Drawbacks of Euclidean distance in TOPSIS — [DOC], `docs/PAPER_GUIDE.md` §6.9

Four consequences, each worth a paragraph in the discussion:

1. **It assumes the criteria are orthogonal.** Euclidean distance treats each
   criterion as an independent axis. These are not: drainage density, land cover
   and soil are all spatially correlated with the same cropland belt, so
   correlated criteria are effectively counted more than once. Mahalanobis
   distance corrects for this but needs a covariance estimate and loses
   interpretability.
2. **It is only weakly compensatory, which is a choice, not a fact.** Squaring the
   shortfall penalises one bad criterion disproportionately. Defensible for siting
   — a site on a steep slope should not be rescued by rainfall — but it is a
   modelling assumption imported silently with the metric.
3. **It depends on the choice of ideal points.** With observed best/worst the score
   becomes data-range dependent and non-comparable across districts. This project
   uses theoretical ideals specifically to avoid that (D6).
4. **Closeness compresses the middle.** C = d⁻/(d⁺ + d⁻) pushes mediocre pixels
   toward 0.5, which is why TOPSIS reports a lower mean (0.669 vs 0.729) and a
   smaller High class (13.6% vs 18.5%) on identical inputs. **[RUN]** confirms both.

---

## 21. LIMITATIONS — write these honestly

1. **No ground-truth validation.** Every reported number describes the model's
   internal behaviour; none tests the map against built structures. Harness
   implemented, arithmetic verified, inventory not assembled. **[CODE]**

2. **Input resolution is uneven.** The analysis grid is ~300 m but land cover is
   ~463 m, population ~900 m and rainfall ~5.3 km. **The map is drawn finer than
   three of its six inputs.** **[RUN]**

3. **Edge effects from pre-clipped inputs.** Distance- and density-based criteria
   see only in-district features, so a river or town just across the boundary is
   invisible. Measured [DOC — `docs/METHODOLOGY.md` §12]: 24.4% of the district
   lies within 5 km of the border; **25.8% of pixels could have a nearer
   out-of-district settlement**; 4.9% a nearer river; **8 of the 25 candidate
   sites, including rank #1**, lie in the exposed zone. **Bounded:** combined
   weight of the two affected criteria is 0.133, so class areas barely move; the
   effect is on near-border *ranking*. Fix requires re-exporting inputs clipped to
   a 20 km buffered boundary — no code change needed.

4. **HydroRIVERS understates the network.** 0.242 km/km² against 0.5–2.0 km/km²
   typical of DEM-derived networks. Class breaks are calibrated to *this* network
   and would need recalibration for another. **[CODE + RUN]**

5. **AHP weights remain expert judgement.** CR = 0.0235 establishes internal
   consistency, not correctness. §17 bounds the consequence but does not remove
   the subjectivity.

6. **No socio-economic or cost dimension.** No land value, acquisition or
   construction-cost data. "Low-earthwork siting" is a slope/land-cover proxy.
   **[CODE]**

7. **Soil class coding unverified** against the source dataset's documentation.
   **[CODE — explicit warning in `criteria.py`]**

8. **Rainfall percentile-rank scoring is district-relative.** It maximises
   within-district discrimination but is not transferable: the same 1,400 mm pixel
   would score differently in a wetter district. This is a deliberate trade-off
   (§8.5) and partially contradicts the transferability claim in C1 — **be honest
   about this tension; it is a legitimate reviewer question.** **[INFER]**

9. **Upstream preprocessing is manual and unscripted.** QGIS clipping and slope
   derivation are not reproducible from the repository. Compounded by
   `data/dem.tif` being empty (§6.6), the slope layer's provenance cannot be
   independently verified. **[RUN]**

10. **Single study area, single time slice.** No temporal analysis, no
    cross-district transfer test. Transferability is argued from construction, not
    demonstrated. **[INFER]**

---

## 22. COMPLETE PARAMETER TABLE — [CODE]

Every tunable constant. In `criteria.py` unless noted. Reviewers will ask for this.

| Parameter | Value | Role |
|---|---|---|
| `DEFAULT_MAX_GRID_SIZE` | 450 px | Longest grid side (`gis_analysis.py`) |
| Analysis CRS | EPSG:4326 | Common grid |
| `KM_PER_DEG_LAT` / `_LON_EQUATOR` | 110.574 / 111.320 | Degree→km (`gis_analysis.py`) |
| Resampling | bilinear / nearest | Continuous / categorical |
| `MIN_WEIGHT_COVERAGE` | 0.80 | Pixel scored only if ≥80% of weight has data |
| `SUITABILITY_THRESHOLDS` | (0.65, 0.85) | Low/Medium/High breaks |
| `CLASSIFICATION_MODE` | "fixed" | Not percentile |
| `SLOPE_RAMP_DEG` | (0,1.00) (1,0.95) (3,0.85) (5,0.68) (10,0.42) (15,0.20) (25,0.08) (90,0.05) | Slope anchors |
| `RAINFALL_FLOOR` | 0.20 | Driest pixel's score |
| `SOIL_TEXTURE_SCORES` | {1:0.55, 4:1.00, 6:0.80, 7:0.50} | Texture lookup |
| `SOIL_DEFAULT_SCORE` | 0.30 | Unrecognised code |
| `LULC_SCORES` | 17 IGBP classes, Cropland 1.00 … Water 0.00 | Land-cover lookup |
| `LULC_DEFAULT_SCORE` | 0.30 | Unrecognised code |
| `DRAINAGE_DENSITY_WINDOW_KM` | 2.5 km | Circular moving window (≈20 km²) |
| `DRAINAGE_DENSITY_RAMP` | (0.00,0.10) (0.10,0.25) (0.20,0.50) (0.30,0.72) (0.40,0.88) (0.90,1.00) | Density anchors |
| River densification | 100 m | Segment length (`gis_analysis.py`) |
| `SETTLEMENT_DENSITY_THRESHOLD` | 400 people/km² | Settlement pixel (6.6% of district) |
| `SETTLEMENT_PEAK_KM` | (1, 5) km | Optimal band; peak 1.00 at 3 km |
| `SETTLEMENT_FALLOFF_KM` | 10 km | Decay beyond band |
| `SETTLEMENT_SCORE_AT_ZERO` | 0.05 | Inside settlement |
| `SETTLEMENT_FLOOR` | 0.10 | Remote |
| `band_edge` | 0.97 | Score at band edges (`moderate_optimal`) |
| `SATISFIED_THRESHOLD` | 0.66 | "Criterion satisfied" flag |
| `DEFAULT_TOP_N` | 25 | Candidate sites (`gis_analysis.py`) |
| `DEFAULT_MIN_SEPARATION_KM` | 5.0 km | Minimum candidate spacing |
| Tile grid | 5 × 5 | Stage-1 selection |
| Tie-break coefficient | 1e-3 | Separates exact ties only |
| `FUZZY_DELTA` | 1.0 | ±1 Saaty step (`algorithms.py`) |
| `SAATY_MIN` / `SAATY_MAX` | 1.0 / 9.0 | Fuzzy clipping bounds |
| Sensitivity δ | ±20% | One-way perturbation (`sensitivity.py`) |
| Sensitivity top-N / match | 10 / 2.0 km | Retention measurement |
| Consensus match radius | 2.0 km | Cross-variant matching (`consensus.py`) |
| Consensus top-N | 25 | Sites per variant |
| `DEFAULT_STORM_MM` | 100 mm | Runoff design storm (`derived_maps.py`) |
| SCS-CN condition | AMC II, good | Curve Number basis |
| `DEFAULT_CN` / `DEFAULT_HSG` | 70 / "C" | Fallbacks (`derived_maps.py`) |
| `BUFFER_DEG` | 0.20° | CHIRPS read margin (`build_rainfall.py`) |
| `NODATA_CUTOFF` | −100.0 | CHIRPS undeclared fill (`build_rainfall.py`) |
| `EXPECTED_MEAN_MM` / tolerance | 1245.0 / ±20% | Sanity check (`build_rainfall.py`) |
| `DEFAULT_BACKGROUND_MULTIPLIER` | 5 | Background points per positive (`validation.py`) |
| `DEFAULT_EXCLUSION_KM` | 1.0 km | Background buffer (`validation.py`) |
| `RANDOM_SEED` | 42 | Background sampling (`validation.py`) |

---

## 23. EQUATIONS TO INCLUDE

Number them IEEE-style. All verified against the implementing code.

**(1) AHP priority vector (geometric mean)** — `ahp.calculate_weights()`
```
w_i = (∏_{j=1}^{n} a_ij)^{1/n} / Σ_{k=1}^{n} (∏_{j=1}^{n} a_kj)^{1/n}
```

**(2) Consistency** — `ahp._calculate_consistency_ratio()`
```
λ_max = (1/n) Σ_i (Aw)_i / w_i ;  CI = (λ_max − n)/(n − 1) ;  CR = CI/RI
```

**(3) Weighted linear combination, per-pixel renormalised** — `aggregate_wlc()`
```
S(x,y) = Σ_{i∈V} w_i r_i(x,y) / Σ_{i∈V} w_i ,   scored only if Σ_{i∈V} w_i ≥ 0.80
```

**(4) TOPSIS closeness, theoretical ideals A⁺ = w_i, A⁻ = 0** — `aggregate_topsis()`
```
d⁺ = √(Σ w_i²(1 − r_i)²) ;  d⁻ = √(Σ w_i² r_i²) ;  C = d⁻/(d⁺ + d⁻)
```

**(5) Fuzzy-AHP, Buckley geometric mean** — `fuzzy_ahp_weights()`
```
ã_ij = (l_ij, m_ij, u_ij) ;  r̃_i = (∏_j ã_ij)^{1/n} ;  w̃_i = r̃_i ⊗ (Σ_k r̃_k)^{-1}
defuzzified by centroid (l + m + u)/3, then renormalised
```

**(6) Drainage density** — `_drainage_density()`
```
D_d = Σ L / A   over a circular moving window of radius 2.5 km
```

**(7) Moderate-optimal settlement score** — `moderate_optimal()`
```
piecewise-linear: 0.05 at 0 km → 0.97 at 1 km → 1.00 at 3 km → 0.97 at 5 km → 0.10 at 15 km
```

**(8) Percentile-rank benefit score** — `score_percentile_benefit()`
```
r = 0.20 + 0.80 × rank(v) / (m − 1),  rank within district, m = 123,555
```

**(9) Map removal sensitivity index (adapted)** — `map_removal_sensitivity()`
```
S_i = (1/m) Σ_pixels |V − V′_i| / V × 100
```

**(10) Effective weight** — `single_parameter_sensitivity()`
```
W_i = (1/m) Σ_pixels (w_i · r_i) / V × 100 ,  compared with w_i × 100
```

**(11) SCS-CN runoff** — `scs_runoff()`
```
S = 25400/CN − 254 ;  I_a = 0.2S ;  Q = (P − I_a)²/(P + 0.8S)  for P > I_a, else 0
```

**(12) Spearman's rank correlation** — `algorithms._spearman()`, via `scipy.stats.spearmanr`
```
ρ = 1 − 6 Σ d_i² / (n(n² − 1)),  n = 123,555, mid-ranks for ties
```

**(13) ROC-AUC via Mann-Whitney U** — `validation.roc_auc()` *(implemented, unused)*
```
AUC = U / (n_pos · n_neg),  U = R_pos − n_pos(n_pos + 1)/2
```

**(14) Borda count for consensus** — `consensus_sites()`
```
B = N − r + 1 within a variant; 0 if not selected; consensus score = Σ over variants
```

---

## 24. REPRODUCING EVERY NUMBER

All from the repo root with the project venv. Runtimes [DOC].

```bash
# §16.1, §9.3 — weights, CR, area statistics
python -c "from gis_analysis import run_ahp_analysis; r=run_ahp_analysis('data'); print(r['area_statistics'])"

python sensitivity.py        # §17.1, §17.2, §17.3           ~3.7 s
python algorithms.py         # §16.4 comparison + Spearman   ~2.8 s
python consensus.py          # §15.3                          ~3 s
python consensus.py --write  # + CSV and agreement PNGs       ~5 s
python derived_maps.py       # §16.3                          ~4 s
python exports.py            # site table + map figure        ~3 s
python build_rainfall.py     # rebuild rainfall surface       ~5 s
python validation.py         # reports missing_data           ~2 s
python tools/inspect.py data/<file>   # dataset profiling
python tools/smoke_test.py   # end-to-end app test           ~40 s
streamlit run app.py         # interactive UI
```

Authoritative artefacts in `outputs/`: `rwh_sites.csv`, `rwh_sites.geojson`,
`rwh_suitability.tif`, `rwh_suitability_classified.tif`, `rwh_suitability_map.png`,
`derived_hydrology.png`, `agreement_algorithms.png`, `agreement_scenarios.png`,
`consensus_algorithms.csv`, `consensus_scenarios.csv`, plus 4 hydrology GeoTIFFs.

---

## 25. SUGGESTED 40-PAGE STRUCTURE

Honest allocation. **"Repo"** = supported by this document. **"External"** = the
writer must source it.

| § | Section | Pages | Source |
|---|---|---|---|
| — | Abstract, keywords | 0.5 | Repo |
| I | Introduction: water scarcity, RWH, GIS-MCDA, contributions C1–C5 | 3 | Mixed |
| II | Literature Review — A. GIS-MCDA for RWH · B. Criterion selection · C. Normalisation approaches · D. Weighting (AHP, Fuzzy-AHP, entropy, BWM) · E. Aggregation (WLC, TOPSIS, PROMETHEE, VIKOR) · F. Sensitivity practice in GIS-MCDA · G. Validation practice · **H. Research gaps** | **9** | **Mostly external — this is where the length legitimately comes from** |
| III | Study Area | 2.5 | Mixed (§3 + external physiography) |
| IV | Data and Preprocessing | 4 | Repo §6–7 |
| V | Methodology | 7 | Repo §8–15, §22–23 |
| VI | Results | 6 | Repo §16–17 |
| VII | Discussion — method comparison, effective weights, Euclidean-distance critique, comparison against published studies | 4.5 | Mixed |
| VIII | Limitations | 1.5 | Repo §21 |
| IX | Conclusion | 1 | Repo |
| X | Future Scope — validation, ML layer, finer inputs, cost data, PROMETHEE, temporal analysis | 1 | Repo §19 + `TODO.md` |
| — | References (30–45 for a journal) | — | External |

**Note the shape:** the literature review and discussion carry the page count.
That is normal for a journal paper and it is the only honest way to reach 40
pages from this codebase.

### Suggested title
*Reproducible GIS-MCDA for Rainwater Harvesting Site Selection: Criterion
Normalisation, Weight Sensitivity and Method Comparison in Chandrapur District,
India*

### Suggested headline for the abstract
Aggregation dominates weighting: WLC→TOPSIS moves the highly-suitable area by
~5 percentage points and drops class agreement to ~75%, whereas AHP→Fuzzy-AHP
moves it 0.2 points at 98.7% agreement.

### References the repo implies but does not contain [ABSENT]
Saaty (AHP); Buckley (fuzzy AHP); Chang (extent analysis, cited for its
criticism); Hwang & Yoon (TOPSIS); Lodwick, Monson & Svoboda 1990 (map removal);
Napolitano & Fabbri 1996 (single-parameter sensitivity); USDA-NRCS TR-55 (Curve
Number); Funk et al. (CHIRPS); Lehner & Grill / Linke et al. (HydroSHEDS,
HydroRIVERS); Hengl et al. (SoilGrids); Friedl et al. (MODIS MCD12Q1); Tatem
(WorldPop); GADM. Plus the 8 domain papers already in the project's literature
review [DOC]: Seif et al. 2023; Al-Hasani et al. 2024; Mustapha et al. 2023;
Haziq & Ibrahimi 2020; Resen et al. 2023; Fetene et al. 2023; Alene et al. 2022;
Adham et al. 2018. **Verify every one of these citations independently — this
document cannot confirm they exist or say what the project claims.**

---

## 26. DISCREPANCIES AND CAUTIONS

Found during this audit. **Read before quoting any number from project docs.**

| # | Issue | Resolution |
|---|---|---|
| 1 | `criteria.py` comment claims thresholds yield "31% High / 46% Medium / 23% Low" | **Stale.** Was 18.51 / 54.79 / 26.70; **now 6.44 / 52.48 / 41.08 [RUN, 2026-10-02]** after the soil legend correction. Use the banner at the top of this file, not §16.1. |
| 2 | Rainfall range quoted variously as 1,140–1,823 / 1,184–1,713 / 1,189–1,714 | All three describe different domains. Whole raster incl. 0.20° buffer: 1,140–1,823. In-district: **1,189.4–1,714.3 [RUN]**. State which. |
| 3 | Rainfall mean quoted as 1,471.9 and 1,492.9 and 1,500.3 | 1,471.9 = whole raster; **1,492.9 = district mean in the file's own metadata tag**; 1,500.3 = in-district on the analysis grid after reprojection. Prefer 1,493 mm and say "district mean". |
| 4 | Slope max quoted as 72.4° / 72.36° / 72.21° | Source raster max = **72.21 [RUN]**. In-district max = **56.04 [RUN]**. Report the in-district figure in results. |
| 5 | `data/dem.tif` is 100% NoData | **[RUN]** Verified empty at four windows. Unused by the pipeline. Do not cite it as the slope source without qualification (§6.6). |
| 6 | Settlement share quoted as 6.4% (`criteria.py`) | Actual **6.6% [RUN]**. |
| 7 | Population range 1.9–9,101 (`CLAUDE.md`) | That is the source raster. In-district: **2.81–8,506.9 [RUN]**. |
| 8 | Soil class coding | **Resolved 2026-10-02 — it was wrong.** The original download retained a `LEGEND` metadata tag giving the standard USDA order (1=Clay … 12=Sand); `criteria.py` had assumed 1=Sand, 4=Silt Loam, 7=Silt Clay Loam. Corrected in `criteria.py` and `derived_maps.py`. Cite Hengl et al. 2017, DOI `10.1371/journal.pone.0169748`. Report the correction; it is a finding, not a limitation. |
| 9 | The "19–34% suitable in comparable studies" comparison | [DOC] only. **Verify against the actual papers before repeating.** |
| 10 | Per-year rainfall figures (1,220–1,260 vs 1,425–1,930 mm) | [DOC] from the original build run; not re-derived here. Re-run `build_rainfall.py` if quoting. |
| 11 | Min–max failure statistics (97.4% / 97.7% / 973 tied pixels / 47,495→108,229) | [DOC] historical measurements; the defective code is gone. **The 108,229 and "1 pixel at max" figures ARE re-verified [RUN]**; the pre-fix figures are not re-derivable. |
| 12 | Runtime figures (0.90 s / 0.15 s / ~1.5 s) | [DOC]. Not benchmarked in this audit. |

---

## 27. FILE AND FUNCTION INDEX FOR KEY CLAIMS

| Claim | File · function |
|---|---|
| Criterion scoring tables and all thresholds | `criteria.py` (module-level constants) |
| Slope scoring | `criteria.SLOPE_RAMP_DEG`, `score_slope()`, `score_ramp()` |
| Soil / LULC scoring | `criteria.SOIL_TEXTURE_SCORES`, `LULC_SCORES`, `score_categorical()` |
| Rainfall scoring | `criteria.score_percentile_benefit()`, `RAINFALL_FLOOR` |
| Drainage scoring | `criteria.DRAINAGE_DENSITY_RAMP`, `score_drainage_density()` |
| Settlement scoring | `criteria.moderate_optimal()`, `score_settlement_distance()` |
| Analysis grid construction | `gis_analysis._make_common_grid()`, `_pixel_size_km()`, `_pixel_area_km2_per_row()` |
| Reprojection + resampling policy | `gis_analysis._load_raster_to_grid()`, `build_criteria_stack():raster_config` |
| District masking | `gis_analysis._rasterize_boundary()` |
| Gap filling | `gis_analysis._fill_nearest()` |
| Drainage density computation | `gis_analysis._river_length_grid()`, `_drainage_density()` |
| Settlement distance | `gis_analysis._distance_km()` (+ `_distance_transform_chamfer()` fallback) |
| Weighted overlay + coverage gate | `gis_analysis._weighted_overlay()`, `algorithms.aggregate_wlc()` |
| TOPSIS | `algorithms.aggregate_topsis()` |
| Classification | `gis_analysis._classify_suitability()` |
| Area statistics | `gis_analysis._area_statistics()` |
| Candidate extraction + ranking | `gis_analysis._extract_top_locations()`, `_rank_by_score()`, `_tiebreak_raster()` |
| Explainability | `gis_analysis.score_stack()` (details loop); `exports._site_records()` |
| AHP weights + CR | `ahp.AHPEngine.calculate_weights()`, `_calculate_consistency_ratio()` |
| Scenario presets | `ahp.SCENARIOS`, `matrix_from_levels()`, `matrix_for_scenario()` |
| Fuzzy-AHP | `algorithms._to_tfn()`, `fuzzy_ahp_weights()` |
| Algorithm comparison + Spearman | `algorithms.compare_algorithms()`, `_spearman()` |
| One-way sensitivity | `sensitivity.one_way_sensitivity()`, `perturb_weights()` |
| Map removal sensitivity | `sensitivity.map_removal_sensitivity()` |
| Effective weights | `sensitivity.single_parameter_sensitivity()` |
| Site matching across runs | `sensitivity._match_sites()` |
| Consensus + Borda | `consensus.consensus_sites()`, `variants_by_algorithm()`, `variants_by_scenario()` |
| Agreement raster | `consensus.agreement_raster()`, `agreement_stats()`, `agreement_png()` |
| ROC-AUC (unused) | `validation.roc_auc()`, `validate()` |
| Candidate proximity (unused) | `validation.candidate_proximity()` |
| Per-algorithm ranking (unused) | `validation.validate_all_algorithms()` |
| Rainfall surface construction | `build_rainfall.py` — `discover()`, `read_window()`, `main()` |
| Curve Number + runoff | `derived_maps.curve_number_grid()`, `scs_runoff()`, `CURVE_NUMBERS`, `HSG_FROM_SOIL` |
| Export artefacts + provenance | `exports.py` — `sites_csv()`, `sites_geojson()`, `suitability_geotiff()`, `classified_geotiff()`, `map_png()`, `_provenance()` |
| Interactive map | `utils/map_renderer.render_map()` |
| UI | `app.py` |

### Supporting documentation in the repo

| File | Content |
|---|---|
| `docs/METHODOLOGY.md` | Justification for every number in `criteria.py`; §12 the edge-effect measurement; §13 open items |
| `docs/PAPER_GUIDE.md` | Prior 10-page IEEE paper plan; §4 verified numbers; §6 design-decision paragraphs |
| `CHANGELOG.md` | Dated change record standing in for git history |
| `TODO.md` | Backlog; §A4 slide corrections; §C2 the planned ML sprint |
| `CLAUDE.md` | Conventions and current state |
| `RUNBOOK.md` | Every command with purpose, outputs, runtime, troubleshooting |
| `README.md` | Project overview and setup |
| `docs/archive/AHP_*.md` (7 files, Apr 2026) | Legacy AHP explainers, **superseded** by `docs/METHODOLOGY.md`. Treat as historical; do not cite. |

---

## 28. THINGS THE PAPER MUST NOT CLAIM

- ❌ **Any validation metric** — no AUC, accuracy, precision, recall, F1, kappa,
  RMSE. None exists. The 0.482 OSM figure is a diagnostic, not a result (§18.3).
- ❌ **Any machine learning** — no model is trained. Do not describe one (§19).
- ❌ **That one algorithm outperforms another** — they *differ*; ranking requires
  ground truth (§18.4).
- ❌ **Field verification** — no site has been visited.
- ❌ **Cost analysis** — call the third scenario *low-earthwork siting*.
- ❌ **Annual runoff volume** — runoff is per design storm only (§16.3).
- ❌ **Runoff as an AHP criterion** — it is a derived output, deliberately excluded
  to avoid double-weighting land cover, soil and rainfall.
- ❌ **A natural-language query interface** — removed from scope 2026-07-29.
- ❌ **Distance-to-river as the drainage criterion** — replaced by drainage
  density 2026-08-04. Older project materials still say this; they are wrong.
- ❌ **Percentile-based classification** — replaced by fixed thresholds.
