# PAPER DATA HANDOFF

> # ⚠ EVERY NUMBER BELOW IS SUPERSEDED — 2 October 2026
>
> The soil texture legend was found to be **wrong** on 2 October. The dominant
> class — 77.8% of the district — is **Clay Loam**, not Silt Loam, and was
> scoring 1.00 instead of 0.60. Three of four class codes were mis-mapped.
> Full record: `docs/SOIL_LEGEND_CORRECTION.md` and `CHANGELOG.md` 2026-10-02.
>
> **Regenerate everything with `python tools/paper_figures.py --csv-dir
> outputs/paper`.** The tool is corrected; this document is not.
>
> The *narrative* notes below ("worth a sentence in the text", the caveats, the
> structural observations) mostly still hold. The *numbers* do not.
>
> ## New headline figures
>
> | | Old (wrong legend) | **Current** |
> |---|---|---|
> | High suitability | 18.51% — 2,112.6 km² | **6.44% — 735.0 km²** |
> | Medium / Low | 54.79% / 26.70% | **52.48% / 41.08%** |
> | Score range, mean | 0.256–0.984, 0.729 | **0.210–0.957, 0.673** |
> | Sites rank 1 → 25 | 0.984 → 0.866 | **0.957 → 0.854** |
> | Curve Number mean | 70.5 | **85.97** |
> | Runoff coefficient | 0.354 | **0.637** |
>
> ## Two findings that changed in kind, not just in value
>
> **§3/§4 — the headline claim must be restated.** "Aggregation dominates
> weighting" has *weakened on area* (WLC→TOPSIS 0.79 pp vs AHP→Fuzzy 0.40 pp,
> a ratio of 2× where it was 26×) but *strengthened on ranking*:
>
> | Algorithm | High % | Top-10 shared | ρ | Class agreement |
> |---|---|---|---|---|
> | AHP + WLC | 6.44 | 10/10 | 1.000 | 100.0% |
> | AHP + TOPSIS | 5.65 | **5/10** | 0.964 | 87.2% |
> | Fuzzy-AHP + WLC | 6.04 | **10/10** | 1.000 | 99.0% |
> | Fuzzy-AHP + TOPSIS | 4.92 | 5/10 | 0.967 | 87.3% |
>
> Changing the aggregation rule replaces **half the shortlist**; changing the
> weighting method replaces **none of it**. Make the claim on shortlist overlap
> and class agreement, not on class area.
>
> **§9 — the shortlist-concentration limitation is materially weaker.** The 25
> sites previously all sat on one soil class scoring 1.00. They now span three
> textures (Clay Loam 10, Loam 9, Sandy Clay Loam 6) and two land covers. Soil
> sd across sites rose from 0.0000 to 0.1742. Soften that limitation.
>
> The §9 weighted-dispersion claim **survives** — the ordering still predicts
> map-removal retention (rainfall > drainage > soil > population ≈ slope > lulc).
>
> Other movements: sensitivity ±20% now 88% retained (60% worst), most
> influential criterion is **soil** not drainage; map removal — rainfall now
> 0/10; effective weight of soil flipped 1.260 → **0.812**; consensus 15/35 by
> all four algorithms (**528.5 km²**), only **2** of 61 by all five scenarios.

Response to the data request from the paper-writing session.
**Generated 23 September 2026** by running the pipeline — see the notice above
before using any figure.

## Status summary

| # | Request | Status |
|---|---|---|
| 1 | AHP elicitation rounds | ✅ **RESOLVED 23 Sep 2026 — no rounds occurred; see §1** |
| 2 | Top 5 sites per algorithm variant | ✅ measured |
| 3 | Full 4×4 Spearman + Pearson | ✅ measured |
| 4 | High-suitability area per variant | ✅ measured — your derived values were close but use these |
| 5 | Per-paper criterion usage, 8 studies | ❌ **NOT IN REPO — see §5** |
| 6 | Class transition matrix WLC→TOPSIS | ✅ measured |
| 7 | Composite score histograms | ✅ measured, 50 bins |
| 8 | Step vs ramp distribution | ⚠️ **reconstruction** — reproduces the 973 spike exactly, see caveat |
| 9 | Per-criterion variance | ✅ measured — **and it contradicts the paper's claim, see §9** |
| 10 | 15 consensus sites | ✅ measured |
| 11 | Per-scenario top site | ✅ measured |
| 12 | CHIRPS annual means 2014–2024 | ✅ measured |
| 13 | Area per IGBP / soil class | ✅ measured |
| 14 | Coverage gate drops zero cells | ✅ confirmed |
| 15 | Benchmarked runtimes | ✅ measured — **the 0.9 s / 0.15 s pair should change, see §15** |

**One item remains blocked: §5, the per-paper criterion coding, which must be
done by hand from the eight papers.** §1 was resolved by the authors on 23 Sep.
Two sections carry corrections you need before the text is final: §9 and §15.

---

# 1. AHP elicitation rounds — RESOLVED ✅

**There were none.** Confirmed by the authors on 23 September 2026: the pairwise
matrix was specified once, accepted without revision, and has never been
externally reviewed. CR = 0.0235 was achieved on first evaluation.

This matches what the repository shows — `ahp.py` holds a single hand-written
matrix literal, there is no version control, and `CHANGELOG.md` never records an
elicitation or revision process.

**Delete the `[N]` sentence.** Replace it with the Methods wording in
`docs/AHP_MATRIX_AUDIT.md` §5, which states the single-specification fact
directly and substitutes a three-part audit for the missing history:

- per-judgement consistency diagnostic (15 comparisons)
- single-step perturbation of every judgement (30 perturbations, worst CR 0.0336,
  zero ordering changes)
- Monte Carlo over judgement space (4,000 drawn, 1,013 accepted, 200 scored —
  every shipped weight between the 40th and 63rd percentile)

Reproduce with `python tools/ahp_audit.py`.

**Do not add a supervisory-review clause.** The matrix was not reviewed. §6 of
the audit document carries a prepared answer if a reviewer challenges this.

---

# 2. Top 5 sites per algorithm variant ✅

Coordinates EPSG:4326. `dd` = drainage density km/km². All four variants use the
same baseline pairwise matrix; only weighting and aggregation differ.

### AHP + WLC (baseline, already exported — included for alignment)
| rk | lon | lat | score | slope | soil | land cover | dd | settl km |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 |
| 2 | 79.7673 | 19.6664 | 0.982 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 |
| 3 | 79.4195 | 20.4775 | 0.977 | 0.26° | Silt Loam | Cropland | 0.62 | 2.1 |
| 4 | 79.3262 | 20.4549 | 0.977 | 0.35° | Silt Loam | Cropland | 0.40 | 4.7 |
| 5 | 79.6570 | 20.3532 | 0.976 | 0.12° | Silt Loam | Cropland | 0.58 | 5.9 |

### AHP + TOPSIS
| rk | lon | lat | score | slope | soil | land cover | dd | settl km |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 |
| 2 | 79.7673 | 19.6664 | 0.977 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 |
| 3 | 79.6712 | 20.3560 | 0.975 | 0.59° | Silt Loam | Cropland | 0.58 | 6.3 |
| 4 | 79.3234 | 20.4521 | 0.975 | 0.53° | Silt Loam | Cropland | 0.44 | 5.1 |
| 5 | 79.4195 | 20.4097 | 0.973 | 0.04° | Silt Loam | Cropland | 0.48 | 6.9 |

### Fuzzy-AHP + WLC
| rk | lon | lat | score | slope | soil | land cover | dd | settl km |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 |
| 2 | 79.7673 | 19.6664 | 0.981 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 |
| 3 | 79.4195 | 20.4775 | 0.977 | 0.26° | Silt Loam | Cropland | 0.62 | 2.1 |
| 4 | 79.3262 | 20.4549 | 0.976 | 0.35° | Silt Loam | Cropland | 0.40 | 4.7 |
| 5 | 79.6570 | 20.3532 | 0.976 | 0.12° | Silt Loam | Cropland | 0.58 | 5.9 |

### Fuzzy-AHP + TOPSIS
| rk | lon | lat | score | slope | soil | land cover | dd | settl km |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 |
| 2 | 79.7673 | 19.6664 | 0.976 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 |
| 3 | 79.6712 | 20.3560 | 0.974 | 0.59° | Silt Loam | Cropland | 0.58 | 6.3 |
| 4 | 79.3234 | 20.4521 | 0.974 | 0.53° | Silt Loam | Cropland | 0.44 | 5.1 |
| 5 | 79.4280 | 20.4182 | 0.972 | 0.44° | Silt Loam | Cropland | 0.56 | 5.8 |

**Worth a sentence in the text:** rank 1 is identical across all four variants,
and rank 2 is identical across all four. The divergence begins at rank 3, where
the two TOPSIS variants both substitute (79.6712, 20.3560) and (79.3234,
20.4521) for the WLC pair. The aggregation rule, not the weighting rule, is what
reorders the shortlist — consistent with the headline finding.

Also: **all 20 rows are Silt Loam cropland.** Useful for the
shortlist-concentration discussion and for Figure 9.

---

# 3. Full pairwise correlation matrix ✅

All six pairs, computed over 123,555 in-district cells.

| pair | Spearman ρ | Pearson r |
|---|---|---|
| AHP+WLC vs AHP+TOPSIS | 0.9641 | 0.9609 |
| AHP+WLC vs Fuzzy-AHP+WLC | **0.9998** | **0.9998** |
| AHP+WLC vs Fuzzy-AHP+TOPSIS | 0.9671 | 0.9643 |
| AHP+TOPSIS vs Fuzzy-AHP+WLC | 0.9586 | 0.9557 |
| AHP+TOPSIS vs Fuzzy-AHP+TOPSIS | **0.9999** | **0.9999** |
| Fuzzy-AHP+WLC vs Fuzzy-AHP+TOPSIS | 0.9618 | 0.9594 |

**Structure worth naming in the text:** the matrix has a clear block structure.
The two same-aggregation pairs correlate at ρ ≥ 0.9998; all four
cross-aggregation pairs sit at ρ = 0.959–0.967. That is the factorial result
visible in the correlation matrix itself, and it's a cleaner statement than the
against-baseline column alone.

⚠ **Correction:** earlier material reports ρ = 1.000 for AHP+WLC vs
Fuzzy-AHP+WLC. At four decimal places it is **0.9998**, not 1.000. Do not write
"identical" or "perfectly correlated" — write 0.9998, or "ρ > 0.999".

---

# 4. High-suitability area per variant ✅

Pipeline-reported, using per-row latitude-corrected cell areas.

| variant | High % | **High km²** | Medium km² | Low km² |
|---|---|---|---|---|
| AHP + WLC | 18.51 | **2,112.6** | 6,252.6 | 3,047.3 |
| AHP + TOPSIS | 13.62 | **1,554.3** | 4,602.5 | 5,255.7 |
| Fuzzy-AHP + WLC | 18.32 | **2,091.2** | 6,353.5 | 2,967.8 |
| Fuzzy-AHP + TOPSIS | 12.92 | **1,474.1** | 4,756.4 | 5,182.0 |

District total 11,412.5 km² in every case.

**Your derivations vs measured:** 1,554.4 → 1,554.3 · 2,090.9 → 2,091.2 ·
1,474.5 → 1,474.1. Differences of 0.1–0.4 km², arising because the pipeline
integrates true per-row cell area rather than multiplying share by a constant
total. Use the measured column.

---

# 5. Per-paper criterion usage — NOT IN REPO ❌

**The eight reviewed papers are not in this repository** — no PDFs, no
extracted tables, no coding sheet. The only record of them is the summary text
on the presentation slides, which gives each paper's purpose and headline
conclusion but **not a criterion-by-criterion breakdown.**

I cannot verify the 8-of-8 counts in Table 3, and neither can any automated
process from what's here.

**This has to be done by hand:** open each of the eight papers, record which of
the six criteria each one uses, and build the matrix. It is maybe an hour of
work and it is the sort of table a reviewer will spot-check, because it is
trivially falsifiable against the cited papers.

⚠ **A specific risk:** the claim "slope and rainfall appear in 8 of 8" is
plausible but unverified. If even one paper omits one of them, an 8/8 becomes
7/8 and a reviewer who checks will treat the whole table as unreliable. Verify
before submission.

One anchor I *can* confirm from your own slides: Fetene et al. is described as
using five biophysical parameters — slope, rainfall, soil, drainage density and
LULC — which is five of your six, omitting settlement proximity. That is one
row of the matrix confirmed; seven to go.

---

# 6. Class transition matrix, AHP+WLC → AHP+TOPSIS ✅

Cell counts, with km² underneath. 123,555 in-district cells.

| from \ to | Low | Medium | High | row total |
|---|---|---|---|---|
| **High** | 0 | 6,715 | 16,173 | 22,888 |
| *km²* | 0.0 | 620.0 | 1,492.6 | 2,112.6 |
| **Medium** | 23,988 | 43,070 | 669 | 67,727 |
| *km²* | 2,216.9 | 3,974.0 | 61.7 | 6,252.6 |
| **Low** | 32,848 | 92 | 0 | 32,940 |
| *km²* | 3,038.8 | 8.5 | 0.0 | 3,047.3 |

**Unchanged: 92,091 cells = 74.53%. Reclassified: 25.47%.**

Features worth writing up:
- **The transition is almost entirely downward.** 30,703 cells move down a
  class; only 761 move up. TOPSIS is systematically more conservative.
- **No cell crosses two classes in either direction** — High→Low and Low→High are
  both exactly zero. The disagreement is graded, not chaotic.
- **The single largest flow is Medium→Low**, 23,988 cells / 2,216.9 km². That is
  the bulk of the reclassification, not the High→Medium flow you might expect to
  dominate.
- 74.53% unchanged matches the 74.5% class-agreement figure already reported.

For the alluvial: six non-zero flows, band widths by km².

---

# 7. Composite score histograms, 50 bins ✅

WLC and TOPSIS over 0–1, in-district cells. Empty bins omitted.

```csv
bin_lo,bin_hi,WLC_count,TOPSIS_count
0.24,0.26,4,20
0.26,0.28,7,41
0.28,0.30,20,68
0.30,0.32,32,201
0.32,0.34,67,362
0.34,0.36,157,570
0.36,0.38,227,768
0.38,0.40,414,1248
0.40,0.42,432,1779
0.42,0.44,584,3187
0.44,0.46,727,3465
0.46,0.48,1201,3999
0.48,0.50,1507,4565
0.50,0.52,2047,5492
0.52,0.54,3041,4892
0.54,0.56,2703,4530
0.56,0.58,3250,4602
0.58,0.60,4117,4933
0.60,0.62,5131,4939
0.62,0.64,4688,4769
0.64,0.66,5258,4638
0.66,0.68,6245,4342
0.68,0.70,6351,5123
0.70,0.72,6346,4850
0.72,0.74,6718,5166
0.74,0.76,7166,4886
0.76,0.78,7606,4221
0.78,0.80,8026,4797
0.80,0.82,6617,4938
0.82,0.84,6721,6323
0.84,0.86,6249,5784
0.86,0.88,5458,4908
0.88,0.90,5029,3047
0.90,0.92,3869,2038
0.92,0.94,2190,1451
0.94,0.96,1845,1503
0.96,0.98,1468,1091
0.98,1.00,37,19
```

**The shape is the story.** WLC is left-skewed with mass piled between 0.66 and
0.86. TOPSIS is flatter and shifted left, with a long tail into 0.40–0.55 that
WLC barely populates. This is the middle-compression property of the closeness
coefficient made visible — mediocre cells get pulled toward the centre rather
than resolving high.

---

# 8. Step reclassification vs ramps ⚠️ RECONSTRUCTION

### Read this caveat before using the numbers

**The step-reclassification code was deleted in August 2026 and no longer
exists.** I rebuilt it from the surviving anchor constants plus the `CHANGELOG`
description of what each criterion's flat top was.

**Evidence the reconstruction is faithful:** it produces **exactly 973 cells at
score 1.000** — matching the historical figure precisely. That is a strong
check; the probability of an inexact reconstruction landing on that number is
low.

**Where it differs slightly from the record:** distinct values 46,217 vs 47,495
recorded; High share 25.86% vs 25.6% recorded. So it is faithful in structure
but not identical to the byte-for-byte original.

**How to write it:** describe the pre-correction distribution as *reconstructed*
in the caption. The 973 figure can be stated flatly (it is corroborated from two
independent directions); the 46,217 / 25.86% figures should either be omitted or
labelled as reconstruction.

### Summary

| measure | STEP (reconstructed) | RAMP (current) |
|---|---|---|
| min | 0.2505 | 0.2563 |
| max | **1.0000** | **0.9839** |
| mean | 0.7356 | 0.7294 |
| distinct values | 46,217 | **108,229** |
| **cells at exactly 1.000** | **973** | **0** |
| cells at the maximum | 973 | **1** |
| High share (> 0.85) | 25.86% | 18.52% |

### 50-bin histogram

```csv
bin_lo,bin_hi,STEP_count,RAMP_count
0.24,0.26,10,4
0.26,0.28,17,7
0.28,0.30,46,20
0.30,0.32,116,32
0.32,0.34,284,67
0.34,0.36,253,157
0.36,0.38,592,227
0.38,0.40,517,414
0.40,0.42,540,432
0.42,0.44,1069,584
0.44,0.46,950,727
0.46,0.48,1669,1201
0.48,0.50,2054,1507
0.50,0.52,3253,2047
0.52,0.54,2339,3041
0.54,0.56,3851,2703
0.56,0.58,4184,3250
0.58,0.60,4667,4117
0.60,0.62,3568,5131
0.62,0.64,4534,4688
0.64,0.66,3952,5258
0.66,0.68,5661,6245
0.68,0.70,4796,6351
0.70,0.72,5238,6346
0.72,0.74,5561,6718
0.74,0.76,6271,7166
0.76,0.78,4711,7606
0.78,0.80,5500,8026
0.80,0.82,6472,6617
0.82,0.84,6052,6721
0.84,0.86,4831,6249
0.86,0.88,5436,5458
0.88,0.90,6002,5029
0.90,0.92,5613,3869
0.92,0.94,3398,2190
0.94,0.96,2814,1845
0.96,0.98,2862,1468
0.98,1.00,3872,37
```

**The terminal bin is the figure.** Step puts **3,872 cells** in 0.98–1.00
(973 of them stacked on exactly 1.000); ramps put **37**. A log-scale y-axis or
a broken axis will be needed — otherwise that bar flattens everything else.

---

# 9. Per-criterion dispersion — ⚠️ THIS CONTRADICTS THE PAPER

**The paper asserts drainage density has the highest spatial variance of the six
criteria. That is false on every measure I computed.**

### Across all in-district cells

| criterion | weight | mean | **sd** | variance | CV | distinct |
|---|---|---|---|---|---|---|
| settlement | 0.0397 | 0.643 | **0.3429** | 0.11761 | 0.533 | 1,740 |
| drainage | 0.0932 | 0.517 | **0.3032** | 0.09193 | 0.587 | 8,354 |
| land cover | 0.0597 | 0.855 | 0.2451 | 0.06010 | 0.287 | 10 |
| rainfall | 0.4285 | 0.600 | 0.2309 | 0.05333 | 0.385 | 8,001 |
| soil | 0.1535 | 0.908 | 0.1773 | 0.03142 | 0.195 | 4 |
| slope | 0.2254 | 0.924 | 0.1167 | 0.01363 | 0.126 | 6,276 |

**Settlement proximity has the highest dispersion. Drainage is second.**

### Weighted contribution, sd(wᵢ · rᵢ), all cells

rainfall **0.09896** > drainage 0.02826 > soil 0.02722 > slope 0.02631 >
land cover 0.01465 > settlement 0.01361

**Rainfall is first here. Drainage is second.** Drainage is never first on any
framing.

### The number that actually explains the finding

Restricting to the **22,888 High-suitability cells** — which is where all 25
candidates are drawn from — and ranking by weighted dispersion:

| criterion | weight | sd(w·r) within High | **top-10 retained on removal** |
|---|---|---|---|
| rainfall | 0.4285 | **0.03206** | **1 / 10** |
| drainage | 0.0932 | **0.02391** | **2 / 10** |
| settlement | 0.0397 | 0.01087 | 9 / 10 |
| soil | 0.1535 | 0.01085 | 10 / 10 |
| land cover | 0.0597 | 0.00978 | 10 / 10 |
| slope | 0.2254 | 0.00593 | 9 / 10 |

**This is a near-perfect monotonic relationship, and it is a better result than
the one currently in the paper.** The two criteria with the highest weighted
dispersion *inside the high-suitability zone* are exactly the two whose removal
destroys the shortlist. The four with low dispersion there all retain 9–10 of 10
— regardless of their assigned weight. Slope carries 0.2254 of the weight and
retains 9/10; drainage carries 0.0932 and retains 2/10.

### Suggested replacement claim

> Criterion influence on the shortlist is governed not by assigned weight but by
> weighted score dispersion *within the high-suitability zone* from which
> candidates are drawn. Ranking the six criteria by sd(wᵢ·rᵢ) over the 22,888
> high-suitability cells orders them identically to their effect on top-10 site
> retention: rainfall (0.0321, 1/10 retained) and drainage density (0.0239,
> 2/10) displace the shortlist, while slope, soil, land cover and settlement
> proximity — all below 0.011 — leave 9–10 of 10 sites standing.

That is quantified, monotonic, and defensible. The current claim is not.

### Also useful: dispersion across the 25 selected sites

| criterion | sd across 25 sites | min | max |
|---|---|---|---|
| settlement | 0.2189 | 0.137 | 0.995 |
| drainage | 0.1040 | 0.459 | 0.957 |
| rainfall | 0.0574 | 0.762 | 1.000 |
| land cover | 0.0407 | 0.850 | 1.000 |
| slope | 0.0183 | 0.905 | 0.998 |
| **soil** | **0.0000** | **1.000** | **1.000** |

**Soil is constant at 1.000 across all 25 sites** — every selected site is Silt
Loam. That is a hard number for the shortlist-concentration limitation, and it
is exactly what Figure 9's parallel-coordinates plot will show: a flat line on
the soil axis and a fan on settlement and drainage.

---

# 10. Consensus sites across the four algorithms ✅

36 distinct locations proposed; **15 unanimous (4/4)**.

### Top 20 by consensus rank

| crank | lon | lat | picked | borda | best | mean rank | land cover | settl km |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 4/4 | 100 | 0.984 | 1.0 | Cropland | 5.9 |
| 2 | 79.7673 | 19.6664 | 4/4 | 96 | 0.982 | 2.0 | Cropland | 2.7 |
| 3 | 79.3262 | 20.4549 | 4/4 | 88 | 0.977 | 4.0 | Cropland | 4.7 |
| 4 | 79.6570 | 20.3532 | 4/4 | 88 | 0.976 | 4.0 | Cropland | 5.9 |
| 5 | 79.4195 | 20.4775 | 4/4 | 86 | 0.977 | 4.5 | Cropland | 2.1 |
| 6 | 79.4195 | 20.4097 | 4/4 | 82 | 0.976 | 5.5 | Cropland | 6.9 |
| 7 | 79.7475 | 19.6155 | 4/4 | 76 | 0.970 | 7.0 | Cropland | 5.4 |
| 8 | 79.3347 | 20.5030 | 4/4 | 70 | 0.969 | 8.5 | Cropland | 1.2 |
| 9 | 79.4025 | 20.5199 | 4/4 | 62 | 0.961 | 10.5 | Cropland | 1.5 |
| 10 | 79.4647 | 20.3532 | 4/4 | 60 | 0.960 | 11.0 | Cropland | 9.0 |
| 11 | 79.9228 | 20.1949 | 3/4 | 53 | 0.967 | 8.3 | Cropland | 8.3 |
| 12 | 79.6684 | 20.3080 | 4/4 | 51 | 0.955 | 13.2 | Cropland | 1.0 |
| 13 | 79.4563 | 20.4436 | 4/4 | 49 | 0.961 | 13.8 | Cropland | 3.3 |
| 14 | 79.5694 | 20.2119 | 4/4 | 35 | 0.936 | 17.2 | **Savanna** | 9.8 |
| 15 | 79.6712 | 20.3984 | 3/4 | 34 | 0.954 | 14.7 | Cropland | 3.5 |
| 16 | 79.4761 | 20.5199 | 3/4 | 33 | 0.946 | 15.0 | Cropland | 6.3 |
| 17 | 79.6231 | 20.3532 | 2/4 | 28 | 0.952 | 12.0 | Cropland | 6.6 |
| 18 | 79.9709 | 20.2034 | 3/4 | 24 | 0.936 | 18.0 | Cropland | 11.2 |
| 19 | 79.6118 | 20.3701 | 2/4 | 20 | 0.948 | 16.0 | Cropland | 8.1 |
| 20 | 79.2470 | 20.4549 | 4/4 | 18 | 0.915 | 21.5 | Cropland | 5.2 |

### The 15 unanimous sites

| # | consensus rank | lon | lat | borda | best score | mean rank |
|---|---|---|---|---|---|---|
| 1 | 1 | 79.3658 | 20.4295 | 100 | 0.984 | 1.0 |
| 2 | 2 | 79.7673 | 19.6664 | 96 | 0.982 | 2.0 |
| 3 | 3 | 79.3262 | 20.4549 | 88 | 0.977 | 4.0 |
| 4 | 4 | 79.6570 | 20.3532 | 88 | 0.976 | 4.0 |
| 5 | 5 | 79.4195 | 20.4775 | 86 | 0.977 | 4.5 |
| 6 | 6 | 79.4195 | 20.4097 | 82 | 0.976 | 5.5 |
| 7 | 7 | 79.7475 | 19.6155 | 76 | 0.970 | 7.0 |
| 8 | 8 | 79.3347 | 20.5030 | 70 | 0.969 | 8.5 |
| 9 | 9 | 79.4025 | 20.5199 | 62 | 0.961 | 10.5 |
| 10 | 10 | 79.4647 | 20.3532 | 60 | 0.960 | 11.0 |
| 11 | 12 | 79.6684 | 20.3080 | 51 | 0.955 | 13.2 |
| 12 | 13 | 79.4563 | 20.4436 | 49 | 0.961 | 13.8 |
| 13 | 14 | 79.5694 | 20.2119 | 35 | 0.936 | 17.2 |
| 14 | 20 | 79.2470 | 20.4549 | 18 | 0.915 | 21.5 |
| 15 | 30 | 79.5128 | 20.4832 | 8 | 0.906 | 24.0 |

**Note for the text:** unanimity and Borda rank are not the same ordering.
Consensus ranks 11, 15–19 are *not* unanimous despite scoring above several
sites that are — because Borda weights rank position, and a site ranked highly
by three methods can out-score one ranked modestly by four. Worth one sentence,
because a reader will notice the gaps at 11 and 15–19 in the unanimous column.

Also: **site 13 (79.5694, 20.2119) is the only non-cropland unanimous site** —
Savanna. Every other unanimous site is Cropland.

Full table: `outputs/consensus_algorithms.csv`.

---

# 11. Top-ranked site per scenario ✅

| scenario | lon | lat | score | settl km |
|---|---|---|---|---|
| Baseline (balanced) | 79.3658 | 20.4295 | 0.984 | 5.9 |
| Maximise recharge | 79.3658 | 20.4295 | 0.985 | 5.9 |
| **Community-focused** | **79.7673** | **19.6664** | 0.984 | **2.7** |
| Low-earthwork siting | 79.3658 | 20.4295 | 0.982 | 5.9 |
| **Fertile farmland** | **79.3432** | **20.4493** | 0.985 | **4.2** |

**Two scenarios displace the baseline top site, not one.** The paper currently
says community-focused picks a different one — fertile farmland does too, and
picks a third distinct location.

Community-focused selects **(79.7673, 19.6664)**, 2.7 km from the nearest
settlement versus the baseline winner's 5.9 km. That is the criterion doing
exactly what the scenario intends, and it is a clean sentence: *"raising
settlement proximity to match rainfall moves the top-ranked site from 5.9 km to
2.7 km from the nearest settlement."*

All five top sites are Silt Loam cropland.

---

# 12. CHIRPS district mean per year ✅

| year | district mean (mm) | min | max |
|---|---|---|---|
| 2014 | 1,268.9 | 966.2 | 1,522.8 |
| 2015 | 1,285.3 | 891.9 | 1,663.6 |
| 2016 | 1,535.6 | 1,195.9 | 1,913.0 |
| 2017 | **1,210.6** | 957.8 | 1,401.4 |
| 2018 | 1,446.0 | 1,194.2 | 1,768.5 |
| 2019 | 1,676.3 | 1,305.1 | 2,111.2 |
| 2020 | 1,551.3 | 1,296.1 | 1,775.5 |
| 2021 | 1,486.8 | 1,174.1 | 1,680.4 |
| 2022 | **1,956.8** | 1,565.9 | 2,289.2 |
| 2023 | 1,545.1 | 1,062.8 | 1,894.1 |
| 2024 | 1,458.9 | 1,191.7 | 1,742.1 |

**11-year mean: 1,492.9 mm** — matches `data/rainfall.tif`'s metadata tag
exactly. **Interannual sd: 208.1 mm.** Driest 2017 (1,210.6), wettest 2022
(1,956.8). **+19.9% above the 1,245 mm long-term normal.**

⚠ **Corrections to the recorded figures.** Earlier documentation says the three
dry years sit at "1,220–1,260 mm" and the rest at "1,425–1,930 mm", with sd
198 mm. Measured: dry years **1,210.6–1,285.3**, remaining years
**1,446.0–1,956.8**, sd **208.1**. Use these.

The wet-decade claim holds and is now properly substantiated: **3 of 11 years
below 1,300 mm, 8 of 11 above 1,400 mm.**

---

# 13. Area by IGBP and soil class ✅

### Land cover (MODIS MCD12Q1 IGBP, in-district)

| code | class | cells | km² | share | score |
|---|---|---|---|---|---|
| 12 | **Cropland** | 81,010 | **7,482.3** | **65.56%** | 1.00 |
| 9 | Savanna | 15,996 | 1,477.6 | 12.95% | 0.70 |
| 4 | Deciduous Broadleaf Forest | 13,020 | 1,202.3 | 10.53% | 0.30 |
| 10 | Grassland | 9,591 | 886.5 | 7.77% | 0.85 |
| 5 | Mixed Forest | 1,283 | 118.4 | 1.04% | 0.35 |
| 13 | Urban and Built-up | 1,261 | 116.6 | 1.02% | 0.10 |
| 14 | Cropland / Natural Veg. Mosaic | 562 | 51.9 | 0.45% | 0.90 |
| 11 | Permanent Wetland | 434 | 40.1 | 0.35% | 0.20 |
| 8 | Woody Savanna | 245 | 22.7 | 0.20% | 0.60 |
| 17 | Water Bodies | 105 | 9.7 | 0.08% | 0.00 |
| 7 | Open Shrubland | 48 | 4.4 | 0.04% | 0.70 |

### Soil texture (in-district)

| code | class | cells | km² | share | score |
|---|---|---|---|---|---|
| 4 | **Silt Loam** | 96,172 | **8,881.7** | **77.82%** | 1.00 |
| 1 | Sand | 22,980 | 2,124.0 | 18.61% | 0.55 |
| 6 | Sandy Clay Loam | 3,938 | 363.7 | 3.19% | 0.80 |
| 7 | Silt Clay Loam | 465 | 42.9 | 0.38% | 0.50 |

**These two tables explain the shortlist concentration quantitatively.** 65.56%
of the district is Cropland (scoring 1.00) and 77.82% is Silt Loam (scoring
1.00). Their intersection is large, and every candidate site falls in it. That
is a far better explanation than "compensatory aggregation concentrates the
shortlist" — it's the marginal distributions, not just the aggregation rule.

---

# 14. Coverage gate ✅ CONFIRMED

**Zero in-district cells are dropped.**

- In-district cells: 123,555
- Scored: 123,555
- Dropped by the 80% gate: **0**
- Weight coverage inside the district: min **1.0000**, mean **1.0000**
- Cells with less than 100% coverage: **0**

Every in-district cell has all six criteria present after nearest-neighbour gap
filling. The gate is a structural safeguard that does not bind on these inputs —
state it that way rather than implying it removes anything.

---

# 15. Benchmarked runtimes — ⚠️ THE QUOTED PAIR SHOULD CHANGE

Measured 27 August 2026, single machine, median where noted.

| operation | measured |
|---|---|
| Criteria stack build, libraries already imported | **0.23 s** (median of 4) |
| `score_stack` — aggregate, classify, extract, explain | **0.152 s** |
| Cold process start including library imports | **2.71 s** |
| Full cold pipeline, process start to result | **2.86 s** |
| Four-algorithm comparison | **1.36 s** |

**The "0.90 s / 0.15 s" pair in the current text is not what the code does.**
The 0.15 s scoring figure is accurate. The 0.90 s stack-build figure is not —
the computation alone is **0.23 s**, and a cold start including imports is
**2.71 s**. The 0.90 s value sits between the two and corresponds to neither.

**Suggested wording:** *"Criterion stack construction requires 0.23 s and
scoring 0.15 s on a commodity laptop; a cold start including library
initialisation completes in 2.9 s."*

Hardware not characterised — if the journal wants a spec line, add it manually.

---

# Reproduction

```bash
python -c "from gis_analysis import run_ahp_analysis; r=run_ahp_analysis('data'); print(r['area_statistics'])"
python algorithms.py        # §3, §4
python consensus.py         # §10
python sensitivity.py       # §9 retention figures
python derived_maps.py      # hydrology surfaces
```

**Every section above is now committed as `tools/paper_figures.py`** (25 Sep
2026). Section numbers here match `--section` numbers there.

```bash
python tools/paper_figures.py                        # all sections
python tools/paper_figures.py --section 9            # one section
python tools/paper_figures.py --csv-dir outputs/paper  # also write CSVs
```

The AHP matrix audit is `tools/ahp_audit.py`; see `docs/AHP_MATRIX_AUDIT.md`.

Sections 1 and 5 are absent from the tool because they are not computable —
the elicitation history (no record exists) and the per-paper criterion coding
(must be done by hand from the eight papers).

---

# 16. Test and run counts ✅

Added 23 September 2026 in response to the request to report the number of tests
in the paper. Counts are read from the analysis result objects, not from
documentation. **"Test" is ambiguous — all plausible readings are tallied below;
use whichever matches what was asked.**

### 16.1 Robustness analyses — the most likely reading

| Analysis | Runs |
|---|---|
| One-way weight perturbation (±20%) | **12** — 6 criteria × 2 directions |
| Map removal (Lodwick et al. 1990) | **6** — one per criterion removed |
| Single-parameter / effective weight (Napolitano & Fabbri 1996) | **6** criteria evaluated |
| Algorithm comparison | **4** algorithms, **6** pairwise correlations |
| Scenario comparison | **5** scenarios |
| Consensus across algorithms | **4** variants |
| Consensus across scenarios | **5** variants |

**Four independent robustness analyses** (weight perturbation, map removal,
effective weights, cross-method consensus) comprising **24 perturbation runs**
(12 + 6 + 6).

### 16.2 Total pipeline scorings

Each is one complete `score_stack()` call — aggregation, coverage gate,
classification, area statistics, site extraction and explainability.

| Source | Scorings |
|---|---|
| Baseline | 1 |
| One-way sensitivity (incl. internal baseline) | 13 |
| Map removal (incl. internal baseline) | 7 |
| Single-parameter | 1 |
| Algorithm comparison | 4 |
| Consensus across algorithms | 4 |
| Consensus across scenarios | 5 |
| **Total** | **35** |

### 16.3 AHP matrix audit — 23 September 2026

See `docs/AHP_MATRIX_AUDIT.md`.

| Item | Count |
|---|---|
| Pairwise judgements elicited | **15** |
| Per-judgement consistency diagnostics | **15** |
| Single-step judgement perturbations | **30** |
| Monte Carlo matrices drawn | **4,000** |
| Monte Carlo matrices accepted (CR < 0.10, ordering preserved) | **1,013** |
| Accepted matrices scored through the full pipeline | **200** |

### 16.4 Software and correctness checks

| Check | Count |
|---|---|
| End-to-end application test assertions | **11** (all passing) |
| ROC-AUC analytic verification cases | **5** |
| Internal cross-checks | **3** — district area 99.7%, river-length conservation 0.08% loss, rainfall ±20% sanity bound |

### 16.5 Headline figure for the paper

If a single number is wanted:

> **Over 260 distinct model evaluations were performed: 35 full pipeline
> scorings across four independent robustness analyses, 200 alternative
> comparison matrices scored in the AHP audit, and 30 single-judgement
> perturbations, supported by 11 automated end-to-end software checks.**

⚠ Do not describe any of these as *validation* tests. They test the model's
internal behaviour and the software's correctness. None tests the map against
observed rainwater harvesting structures — see §5 of the main text and the
validation status in `docs/presentation/FINAL_PROJECT_DOCUMENTATION.md` §15.

---

# Items needing a decision before submission

1. ~~**§1 — AHP elicitation rounds.**~~ ✅ **RESOLVED 23 Sep 2026.** The team
   confirmed the matrix was specified once, never revised, and never externally
   reviewed. Drop the `[N]` sentence entirely and use the Methods wording in
   `docs/AHP_MATRIX_AUDIT.md` §5, which states this directly and replaces the
   missing history with a three-part audit.
2. **§5 — Per-paper criterion matrix.** Must be built by hand from the eight
   papers. Table 3 is currently unverified and trivially checkable by a reviewer.
3. **§9 — The drainage-variance claim is false as written.** Replacement claim
   supplied, better supported and monotonic.
4. **§15 — The 0.90 s figure is wrong.** Replacement wording supplied.
5. **§3 — ρ = 1.000 should be 0.9998.** Do not write "identical".
6. **§11 — Two scenarios displace the top site, not one.**
7. **§12 — Three recorded rainfall figures need correcting** (dry-year range,
   wet-year range, interannual sd).
8. **§8 — Label the step distribution a reconstruction** in the caption.
