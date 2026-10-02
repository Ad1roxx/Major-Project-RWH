# Research Paper Guide — RWH Site Suitability

**Purpose.** Everything needed to write a 10+ page IEEE-style research paper on
this project, without access to the repository. Every number here is measured
from a run that can be reproduced with the commands in §11.

**Written for:** drafting the paper in a separate session. Paste this whole file
as context.

**Matched to the group's house style** (see the IoT/MQTT and Multimodal-DL
papers): IEEE two-column, numbered sections, Roman-numeral headings, numbered
equations, results in tables, an explicit research-gap subsection, a limitations
subsection, and a future-scope section. Target 20–25 references.

---

## 1. The paper in one paragraph

A GIS-based multi-criteria decision analysis identifies and ranks rainwater
harvesting sites across Chandrapur district, Maharashtra (11,412 km²). Six
criteria — rainfall, slope, soil texture, drainage density, land cover and
settlement proximity — are scored to a common 0–1 scale using explicit,
literature-anchored reclassification tables, weighted by AHP (consistency ratio
0.0235), and combined by weighted linear combination on a 450 × 422 analysis
grid at ~0.3 km resolution. The result is a Low/Medium/High suitability map
(High 18.5%, 2,113 km²) and 25 ranked candidate sites with per-criterion
attribution. The work additionally reports a one-way sensitivity analysis, a
four-algorithm comparison (AHP/Fuzzy-AHP × WLC/TOPSIS), and derived
hydrological surfaces (drainage density, SCS Curve Number, runoff).

## 2. What makes this publishable — the contributions to lead with

Most GIS-MCDA rainwater harvesting papers stop at "we built a weighted overlay
and here is the map". Four things here go further, and the paper should be
organised around them.

**C1 — Reproducible, transferable criterion scoring.** Scores come from fixed
class breaks and interpolated ramps anchored to physical thresholds, not from
min–max rescaling of the observed data range. A 4° slope maps to the same score
in any district. This directly addresses the "region-specific models are not
generalisable" gap that the literature review identifies.

**C2 — Quantified robustness instead of asserted weights.** A ±20% one-way
sensitivity analysis reports how far the ranking actually moves, answering the
standard "AHP weights are subjective" criticism with a number rather than a
defence.

**C3 — Method comparison on a shared criteria stack.** Four algorithms are run
over identical inputs, isolating the effect of the method itself. The finding —
that the *aggregation* rule matters far more than the *weighting* rule — is
novel enough to be the paper's headline result.

**C4 — Explainability at site level.** Every ranked site reports per-criterion
normalised score, weighted contribution (w × score), and the raw measured value
behind it (slope in degrees, soil class name, land-cover class, drainage density,
distance to settlement). Most comparable papers report only an aggregate score.

## 3. Section plan and page budget

Target ≈10 pages of content in IEEE two-column format ≈ 8,000–9,000 words.

| § | Section | Pages | Contents |
|---|---|---|---|
| — | Abstract + Index Terms | 0.25 | 200–250 words, all headline numbers |
| I | Introduction | 1.0 | Problem, study area, why GIS-MCDA, contributions C1–C4, paper structure |
| II | Literature Review | 1.5 | A. GIS-MCDA for RWH · B. Criterion selection and normalisation · C. Weighting methods (AHP, Fuzzy-AHP) · D. Aggregation (WLC, TOPSIS) · E. **Research gap analysis** |
| III | Study Area and Data | 1.25 | Chandrapur description, Table of 7 datasets, preprocessing, the rainfall construction |
| IV | Methodology | 2.5 | Grid, scoring per criterion (equations), AHP, aggregation engines (equations), classification, candidate extraction, explainability. **Include the workflow figure.** |
| V | Results | 2.0 | Weights + CR, area statistics, ranked sites, sensitivity, algorithm comparison, derived surfaces |
| VI | Discussion | 1.25 | Why the results look as they do, method comparison interpretation, **limitations** |
| VII | Conclusion | 0.4 | |
| VIII | Future Scope | 0.4 | Validation, ML, finer inputs, cost data |
| — | References | — | 20–25, excluded from the page count |

## 4. Numbers — all verified, use exactly these

### 4.0 Complete parameter table (§IV — reviewers will ask for this)

Every tunable constant, its value, and where it lives. All in `criteria.py`
unless noted.

| Parameter | Value | Role |
|---|---|---|
| `DEFAULT_MAX_GRID_SIZE` | 450 px | Longest side of the analysis grid (`gis_analysis.py`) |
| Analysis CRS | EPSG:4326 | Common grid; inputs reprojected at run time |
| Resampling | bilinear / nearest | Continuous / categorical layers |
| `MIN_WEIGHT_COVERAGE` | 0.80 | Pixel scored only if ≥80% of total weight has data |
| `SUITABILITY_THRESHOLDS` | (0.65, 0.85) | Low / Medium / High class breaks |
| `CLASSIFICATION_MODE` | "fixed" | Fixed thresholds, not percentiles |
| `SLOPE_RAMP_DEG` | (0,1.00) (1,0.95) (3,0.85) (5,0.68) (10,0.42) (15,0.20) (25,0.08) (90,0.05) | Slope score anchors, interpolated |
| `RAINFALL_FLOOR` | 0.20 | Driest pixel's score; percentile rank scales 0.20→1.00 |
| `SOIL_TEXTURE_SCORES` | {1:0.55, 4:1.00, 6:0.80, 7:0.50} | Sand / Silt Loam / Sandy Clay Loam / Silt Clay Loam |
| `LULC_SCORES` | 17 IGBP classes, Cropland 1.00 … Water 0.00 | Land-cover lookup |
| `DRAINAGE_DENSITY_WINDOW_KM` | 2.5 km | Circular moving window (≈20 km²) |
| `DRAINAGE_DENSITY_RAMP` | (0.00,0.10) (0.10,0.25) (0.20,0.50) (0.30,0.72) (0.40,0.88) (0.90,1.00) | Density score anchors, km/km² |
| River densification | 100 m | Segment length before per-cell accumulation (`gis_analysis.py`) |
| `SETTLEMENT_DENSITY_THRESHOLD` | 400 people/km² | Defines a settlement pixel (6.6% of district) |
| `SETTLEMENT_PEAK_KM` | (1, 5) km | Optimal band; peak 1.00 at 3 km, ≥0.97 across the band |
| `SETTLEMENT_FALLOFF_KM` | 10 km | Decay beyond the band to the floor |
| Settlement score at 0 km / floor | 0.05 / 0.10 | Inside settlement / remote |
| `SATISFIED_THRESHOLD` | 0.66 | "Criterion satisfied" flag in explainability |
| `DEFAULT_TOP_N` | 25 | Candidate sites extracted (`gis_analysis.py`) |
| `DEFAULT_MIN_SEPARATION_KM` | 5.0 km | Minimum spacing between candidates |
| Tile grid | 5 × 5 | Stage-1 best-per-tile selection |
| Tie-break weight | 1e-3 | Separates exact ties only; cannot reorder distinct scores |
| `FUZZY_DELTA` | 1.0 | ±1 step on the Saaty scale for Fuzzy-AHP (`algorithms.py`) |
| Sensitivity δ | ±20% | One-way weight perturbation (`sensitivity.py`) |
| Sensitivity top-N / match | 10 / 2 km | Retention measured on top 10, matched by position |
| Consensus match radius | 2.0 km | Cross-variant site matching (`consensus.py`) |
| SCS-CN design storm | 100 mm | Runoff map only (`derived_maps.py`) |
| SCS-CN condition | AMC II, good | Curve Number table basis |
| CHIRPS window margin | 0.20° | Read around the district (`build_rainfall.py`) |

### 4.1 Study area and grid
| Quantity | Value |
|---|---|
| District area analysed | 11,412.5 km² (99.7% of the official 11,443 km²) |
| Analysis grid | 450 × 422 cells, 123,555 in-district cells |
| Cell size | ≈0.30 × 0.31 km (~0.09 km²) |
| Analysis CRS | EPSG:4326 |
| Full pipeline runtime | ≈1.5 s (criteria stack 0.90 s + scoring 0.15 s) |

### 4.2 Input datasets (Table for §III)
| Layer | Source | Native resolution | Role |
|---|---|---|---|
| District boundary | GADM India ADM2 | vector | Study-area mask |
| Drainage network | HydroRIVERS v1.0 | vector, 776 features, 2,767.7 km, Strahler 1–7 | Drainage density |
| Rainfall | CHIRPS v3.0 annual, 2014–2024 (11 years) | 0.05° (≈5.3 km) | Rainfall criterion |
| Elevation → slope | HydroSHEDS CONDEM → GDAL Slope | ≈90 m | Slope criterion |
| Soil texture | SoilGrids | 250 m | Soil criterion |
| Land cover | MODIS MCD12Q1 `LC_Type1` (IGBP) | 500 m | Land-cover criterion |
| Population | WorldPop 2020 | ≈1 km | Settlement proximity |

### 4.3 Input layer statistics
| Layer | Min | Max | Mean | Median |
|---|---|---|---|---|
| Mean annual rainfall (mm/yr) | 1,140.0 | 1,823.2 | 1,471.9 | 1,456.8 |
| Slope (degrees) | 0.00 | 72.36 | 1.42 | 0.80 |
| Population density (people/km²) | 1.9 | 9,101.1 | 205.2 | 138.7 |
| Drainage density (km/km²) | 0.00 | 0.85 | 0.23 | — |

District-wide drainage density = 2,766 km of channel / 11,414 km² = **0.242 km/km²**.

### 4.4 AHP weights and consistency
| Criterion | Weight |
|---|---|
| Rainfall | 0.428 |
| Slope | 0.225 |
| Soil texture | 0.154 |
| Drainage density | 0.093 |
| Land cover | 0.060 |
| Settlement proximity | 0.040 |

λ_max = 6.1460, CI = 0.0292, RI = 1.24 (n = 6), **CR = 0.0235 < 0.10**.

### 4.5 Suitability distribution
Continuous score: n = 123,555, min 0.256, max 0.984, mean 0.729.

| Class | Threshold | Share | Area |
|---|---|---|---|
| High | ≥ 0.85 | 18.51% | 2,112.6 km² |
| Medium | 0.65 – 0.85 | 54.79% | 6,252.6 km² |
| Low | < 0.65 | 26.70% | 3,047.3 km² |

18.5% sits inside the 19–34% "suitable" range reported by comparable studies.

### 4.6 Top five candidate sites
| Rank | Lon | Lat | Score | Slope | Soil | Land cover | Drainage density | Dist. to settlement |
|---|---|---|---|---|---|---|---|---|
| 1 | 79.3658 | 20.4295 | 0.984 | 0.22° | Silt Loam | Cropland | 0.72 | 5.9 km |
| 2 | 79.7673 | 19.6664 | 0.982 | 0.46° | Silt Loam | Cropland | 0.41 | 2.7 km |
| 3 | 79.4195 | 20.4775 | 0.977 | 0.26° | Silt Loam | Cropland | 0.62 | 2.1 km |
| 4 | 79.3262 | 20.4549 | 0.977 | 0.35° | Silt Loam | Cropland | 0.40 | 4.7 km |
| 5 | 79.6570 | 20.3532 | 0.976 | 0.12° | Silt Loam | Cropland | 0.58 | 5.9 km |

25 sites extracted, 5 km minimum separation, scores 0.984 (rank 1) down to
0.866 (rank 25), strictly descending.

*(Corrected 2026-08-12: ranks previously followed selection order rather than
score, so this table has changed from rank 4 down. Regenerate with
`python exports.py` if in doubt — `outputs/rwh_sites.csv` is authoritative.)*

### 4.7 Sensitivity analysis (±20% one-way)
**Headline:** *Varying each AHP weight by ±20% retains 90% of the top-10 sites on
average (70% worst case), with a maximum rank shift of 3.*

Influence on highly-suitable area (mean absolute change, percentage points):

| Criterion | Weight | Influence (pp) |
|---|---|---|
| Drainage density | 0.093 | **1.66** |
| Slope | 0.225 | 1.55 |
| Soil | 0.154 | 1.17 |
| Rainfall | 0.428 | 0.48 |
| Settlement | 0.040 | 0.35 |
| Land cover | 0.060 | 0.04 |

**Discuss this.** Weight magnitude and influence are not the same thing.
Drainage carries the fourth-largest weight but the largest influence, because it
has the highest spatial variance of the six criteria; rainfall carries the
largest weight but is spatially smooth, so perturbing it barely moves the map.
This is a genuine and non-obvious result.

### 4.7b Map removal sensitivity (Lodwick, Monson & Svoboda, 1990)

Each criterion layer is removed entirely and the remaining weights renormalise.

| Criterion | Weight | S index (%) | Max (%) | Mean \|ΔV\| | Top-10 retained | High % | Δ High % |
|---|---|---|---|---|---|---|---|
| Rainfall | 0.428 | **17.374** | 50.05 | 0.1140 | **1/10** | 42.46 | +23.95 |
| Slope | 0.225 | 8.979 | 38.47 | 0.0592 | 9/10 | 13.27 | −5.24 |
| Soil | 0.154 | 5.301 | 38.61 | 0.0365 | 10/10 | 14.12 | −4.39 |
| Drainage | 0.093 | 4.280 | 13.80 | 0.0303 | **2/10** | 26.87 | +8.36 |
| Land cover | 0.060 | 2.501 | 16.92 | 0.0164 | 10/10 | 19.07 | +0.56 |
| Settlement | 0.040 | 1.780 | 8.53 | 0.0122 | 9/10 | 20.75 | +2.24 |

**Index used:** S_i = mean over district pixels of |V − V′_i| / V × 100. The
original formulation carries /N and /n terms that convert a weighted *sum* over
N (then n) parameters into a per-parameter average; this project's aggregation
already divides by the sum of the weights present, so V and V′ are both on a
0–1 scale and applying /N and /n again would normalise twice. **State this
adaptation in the paper.**

**Two findings to write up.**

1. **The S index tracks weight order, but site retention does not.** Removing
   drainage changes the surface by only 4.28% — fourth of six — yet leaves just
   **2 of the top 10 sites standing**, worse than removing slope (S index 8.98%,
   9/10 retained). Drainage barely moves the *map* but almost completely
   reorders the *shortlist*, because it has the highest spatial variance of the
   six criteria and is what separates otherwise near-identical candidates. This
   corroborates the ±20% result independently.
2. **Removing rainfall inflates the High class to 42.46%.** Rainfall is scored
   by percentile rank, so it averages ~0.6 and acts as a brake on the composite;
   remove it and everything else — mostly high-scoring across the district —
   pushes the score up. A criterion can therefore be *restrictive* rather than
   merely *important*, which the weight alone does not tell you.

### 4.7c Single-parameter sensitivity (Napolitano & Fabbri, 1996)

Effective weight W_i = mean over district pixels of (w_i · r_i) / V × 100,
compared against the theoretical weight w_i × 100 from AHP.

| Criterion | Theoretical % | Effective % | SD | Ratio |
|---|---|---|---|---|
| Rainfall | 42.85 | 34.11 | 8.87 | **0.796** |
| Slope | 22.54 | 29.11 | 5.25 | **1.292** |
| Soil | 15.35 | 19.35 | 3.94 | 1.260 |
| Land cover | 5.97 | 7.25 | 2.61 | 1.214 |
| Drainage | 9.32 | 6.61 | 3.88 | **0.710** |
| Settlement | 3.97 | 3.57 | 2.06 | 0.901 |

**The explanation is the interesting part.** Criteria that score uniformly well
across Chandrapur contribute more than the weight assigned to them — slope
(1.29×) because the district is very flat, soil (1.26×) because Silt Loam
dominates and scores 1.00. Criteria that score uniformly poorly contribute less
— drainage (0.71×) because district density is only 0.242 km/km². Rainfall
(0.80×) is a special case: percentile-rank scoring mechanically fixes its mean
near 0.6, capping its effective contribution regardless of its 0.428 weight.

**This is the formal answer to "are your weights meaningful?"** Assigned weight
and realised influence are different quantities, and the gap is explained by the
distribution of each criterion across the study area, not by the AHP judgements.

### 4.8 Algorithm comparison
| Algorithm | High % | Mean score | Top-10 shared | Pearson r | **Spearman ρ** | Class agreement |
|---|---|---|---|---|---|---|
| AHP + WLC (baseline) | 18.51 | 0.729 | 10/10 | 1.000 | **1.000** | 100.0% |
| AHP + TOPSIS | 13.62 | 0.669 | 9/10 | 0.961 | **0.964** | 74.5% |
| Fuzzy-AHP + WLC | 18.32 | 0.731 | 7/10 | 1.000 | **1.000** | 98.7% |
| Fuzzy-AHP + TOPSIS | 12.92 | 0.671 | 9/10 | 0.964 | **0.967** | 74.9% |

Report **both** correlations and say why: Pearson asks whether two scores move
together linearly; **Spearman asks whether they rank locations the same way**,
which is the question a site-selection method actually answers. They agree
closely here, which is itself worth stating.

Fuzzy-AHP weights: rainfall 0.417, slope 0.224, soil 0.159, drainage 0.097,
lulc 0.062, population 0.041.

**Two findings to write up.**
1. The **aggregation rule dominates the weighting rule.** WLC → TOPSIS moves the
   highly-suitable area by ~5 pp and drops class agreement to ~75%. AHP →
   Fuzzy-AHP moves it 0.2 pp at 98.7% agreement. Papers that compare only
   weighting methods may therefore be comparing the less consequential choice.
2. **Surface correlation is the wrong metric for ranking stability.**
   Fuzzy-AHP + WLC correlates 1.000 with the baseline surface yet shares only
   7 of the top 10 sites. Report top-N overlap alongside correlation.

### 4.9 Derived hydrological surfaces
| Surface | Min | Max | Mean |
|---|---|---|---|
| Drainage density (km/km²) | 0.00 | 0.85 | 0.23 |
| SCS Curve Number (AMC II) | 30 | 100 | 70.52 |
| Runoff depth, 100 mm storm (mm) | 0.00 | 100.00 | 35.37 |
| Runoff coefficient | 0.00 | 1.00 | 0.354 |

### 4.10 Scenario analysis (optional section)
| Scenario | CR | High % |
|---|---|---|
| Baseline (balanced) | 0.0235 | 18.51 |
| Maximise recharge | 0.0044 | 30.14 |
| Community-focused | 0.0059 | 18.77 |
| Low-earthwork siting | 0.0078 | 29.91 |
| Fertile farmland | 0.0146 | 28.19 |

Scenario weights (criteria order: slope, rainfall, drainage, soil, lulc, settlement):

| Scenario | slope | rainfall | drainage | soil | lulc | settlement |
|---|---|---|---|---|---|---|
| Baseline | 0.225 | **0.428** | 0.093 | 0.154 | 0.060 | 0.040 |
| Maximise recharge | 0.266 | 0.226 | 0.095 | **0.273** | 0.095 | 0.045 |
| Community-focused | 0.107 | 0.245 | 0.094 | 0.094 | 0.214 | **0.245** |
| Low-earthwork siting | **0.367** | 0.121 | 0.172 | 0.096 | 0.200 | 0.043 |
| Fertile farmland | 0.135 | 0.204 | 0.100 | **0.257** | 0.229 | 0.074 |

⚠ Two scenarios are **proxies and must be named as such**: "low-earthwork
siting" is not a cost model (no land-value or unit-rate data), and "fertile
farmland" is not a fertility model (no soil organic carbon, N/P/K or pH data).
Both reweight the same six criteria.

### 4.11 Consensus across method variations

Sites matched across variants by position (2 km), ranked by Borda count.
Agreement raster counts, per pixel, how many variants class it High.

**Across the 4 algorithms** (weighting held fixed):

| Measure | Value |
|---|---|
| Distinct locations proposed | 36 |
| Selected by **all 4** | **15** |
| District classed High by all 4 | **12.41%** — 1,416.8 km² |
| District classed High by none | 80.77% — 9,218.0 km² |

**Across the 5 scenarios** (algorithm held fixed at AHP + WLC):

| Measure | Value |
|---|---|
| Distinct locations proposed | 54 |
| Selected by **all 5** | **7** |
| District classed High by all 5 | **10.66%** — 1,217.1 km² |
| District classed High by 4 of 5 | 9.00% — 1,027.2 km² |

**Why this belongs in the paper.** It is robustness evidence that requires **no
ground-truth data**. "Fifteen sites were selected independently by four
different MCDA methods, and 1,417 km² was classed highly suitable by all of
them" is a defensible claim today. It also gives the reader a shortlist that
does not depend on trusting one method.

Top consensus sites across algorithms (all 4/4): (79.3658, 20.4295) Borda 100;
(79.7673, 19.6664) Borda 96; (79.3262, 20.4549) Borda 88.

## 5. Equations to include (§IV)

Number them (1), (2), … in IEEE style.

**AHP priority vector (geometric mean):**
w_i = (∏_{j=1}^{n} a_ij)^{1/n} / Σ_{k=1}^{n} (∏_{j=1}^{n} a_kj)^{1/n}

**Consistency:** λ_max = (1/n) Σ (Aw)_i / w_i ; CI = (λ_max − n)/(n − 1) ; CR = CI/RI

**Weighted linear combination, per-pixel renormalised:**
S(x,y) = Σ_{i∈V} w_i r_i(x,y) / Σ_{i∈V} w_i, where V is the set of criteria with
data at (x,y). A pixel is scored only if Σ_{i∈V} w_i ≥ 0.80 of the total weight.

**TOPSIS closeness (theoretical ideals A⁺ = w_i, A⁻ = 0):**
d⁺ = √(Σ w_i²(1 − r_i)²) ; d⁻ = √(Σ w_i² r_i²) ; C = d⁻/(d⁺ + d⁻)

**Fuzzy-AHP (Buckley geometric mean):** with ã_ij = (l_ij, m_ij, u_ij),
r̃_i = (∏_j ã_ij)^{1/n}, w̃_i = r̃_i ⊗ (Σ_k r̃_k)^{-1}, defuzzified by centroid
(l + m + u)/3 and renormalised.

**Drainage density:** D_d = Σ L / A over a circular moving window of radius 2.5 km.

**Map removal sensitivity index:** S_i = (1/m) Σ_pixels |V − V′_i| / V × 100,
where V is the suitability with all criteria and V′_i with criterion i removed
and the remaining weights renormalised.

**Effective weight (single-parameter sensitivity):**
W_i = (1/m) Σ_pixels (w_i · r_i) / V × 100, compared with the theoretical
weight w_i × 100.

**Moderate-optimal (settlement proximity):** piecewise-linear, 0.05 at 0 km,
rising to 0.97 at 1 km, peaking at 1.00 at 3 km, 0.97 at 5 km, falling to 0.10
at 15 km.

**SCS-CN runoff:** S = 25400/CN − 254 ; I_a = 0.2S ; Q = (P − I_a)²/(P + 0.8S) for P > I_a.

**Spearman's rank correlation** between two suitability surfaces, over the
n = 123,555 district pixels: ρ = 1 − 6 Σ d_i² / (n(n² − 1)), where d_i is the
difference in rank of pixel i between the two surfaces (mid-ranks for ties).

**Borda count** for consensus ranking: a site at rank r of N within one variant
scores B = N − r + 1; a variant that did not select the site contributes 0. The
consensus score is the sum over variants.

## 6. Methodological decisions that are worth a paragraph each

These are the parts a reviewer will probe. Each is a defensible choice with
evidence behind it.

**6.1 Why not min–max normalisation.** Measured on this data, min–max left
**97.4% of slope pixels and 97.7% of population pixels scoring above 0.90** —
one steep escarpment and one city stretched each range so far that both criteria
became near-constant despite carrying 26.5% of the combined weight. Worse,
applied to categorical layers it scored classes by their *code number*, so IGBP
class 17 (water) scored 1.00 and class 13 (urban) 0.75 while forest scored 0.00.
Roughly 48% of the total weight was flat or semantically inverted. Fixed
reclassification removes both failures and makes scores transferable.

**6.2 Why interpolated ramps rather than step classes.** Step classes give every
pixel in a criterion's best band an identical score. With six criteria doing
that, **973 pixels scored exactly 1.000 on everything**, so the top seven sites
were tied and per-criterion comparison between them was uninformative. Replacing
flat tops with linear interpolation between the same anchors raised the number of
distinct scores from 47,495 to **108,229** and reduced pixels sharing the maximum
from **973 to 1**.

**6.3 Why fixed classification thresholds, not percentiles.** A 33rd/67th
percentile split reports ≈33% of any district as highly suitable regardless of
the underlying scores — the figure is a property of the method. The earlier
percentile implementation duly returned 32.9/34.0/33.1. Fixed thresholds make
the reported area a real, comparable result.

**6.4 Why drainage *density*, not distance to river.** Distance to the nearest
channel is a siting-convenience measure. Drainage density (channel length per
unit area) is the variable the RWH literature uses and it indicates where runoff
concentrates. Computed by densifying river lines to 100 m segments, accumulating
true segment length per cell, and convolving with a 2.5 km circular window.
Verified: 2,765.6 km binned against 2,767.7 km of input geometry (0.08% loss).

**6.5 Why theoretical ideals in TOPSIS.** Using the observed best and worst
pixel would make the score depend on the data range — reintroducing exactly the
defect removed in 6.1 — and would stop scores being comparable across scenarios
or districts. Ideals are therefore the best and worst attainable values on the
0–1 criterion scale.

**6.6 Why Buckley, not Chang, for Fuzzy-AHP.** Chang's extent analysis is more
commonly cited but can assign zero weight to a genuinely relevant criterion.
Buckley's geometric mean cannot. **Also worth a footnote:** a uniform
*multiplicative* fuzzification a → (a/s, a, a·s) returns weights identical to
crisp AHP, because it scales every row's fuzzy geometric mean by the same
constant and cancels under normalisation. The additive Saaty fuzzy scale
(3 → (2,3,4), clipped at the scale ends) is required for the fuzziness to have
any effect. This is a real trap and few papers mention it.

**6.7 Why a design storm for runoff, not the annual total.** SCS-CN is an event
model. At P = 1,493 mm/yr, forest (CN 55) yields a runoff coefficient of 0.85 and
built-up (CN 85) 0.96 — every land cover collapses into the same value and the
map carries no information. At a 100 mm design storm the same classes spread
0.13–0.61. Report runoff for a design storm and say so.

**6.8 The wet-decade finding.** The 11-year CHIRPS mean is 1,472 mm/yr against a
commonly cited long-term normal of ≈1,245 mm. Not a unit error: 2014, 2015 and
2017 sit at 1,220–1,260 mm while every other year runs 1,425–1,930 mm
(interannual sd 198 mm). The recent decade is genuinely wetter than the older
baseline. State it — it pre-empts the obvious question.

**6.9 Drawbacks of the Euclidean distance used by TOPSIS.** TOPSIS ranks each
pixel by its Euclidean distance to the ideal and anti-ideal points. Four
consequences worth a paragraph each in the discussion:

1. **It assumes the criteria are orthogonal.** Euclidean distance treats each
   criterion as an independent axis. Ours are not: drainage density, land cover
   and soil are all spatially correlated with the same cropland belt, so
   correlated criteria are effectively counted more than once and the distance
   is distorted. Mahalanobis distance corrects for this but needs a covariance
   estimate and loses the method's interpretability.
2. **It is only weakly compensatory, which is a choice, not a fact.** Squaring
   the shortfall means one bad criterion is penalised disproportionately. That
   is defensible for siting (a site on a steep slope should not be rescued by
   rainfall), but it is a modelling assumption imported silently with the
   metric.
3. **It depends on the choice of ideal points.** With observed best/worst the
   score becomes data-range dependent and non-comparable across districts — the
   same defect as min–max normalisation (§6.1). This project uses **theoretical**
   ideals (1 and 0 on the criterion scale) specifically to avoid that, which is a
   deviation from textbook TOPSIS worth stating.
4. **Closeness compresses the middle.** C = d⁻/(d⁺ + d⁻) pushes scores toward
   0.5 for pixels that are mediocre on everything, which is why TOPSIS reports a
   lower mean (0.669 vs 0.729) and a smaller High class (13.6% vs 18.5%) on
   identical inputs.

**6.10 Which method "outperforms" — and why the paper cannot say yet.** The four
algorithms differ measurably (§4.8), but *differing* is not *being better*.
Naming an outperformer requires an external standard, and the only external
standard available is agreement with rainwater harvesting structures that already
exist. Until `data/rwh_structures.geojson` is assembled and `validation.py`
produces a per-algorithm AUC, the paper should say the methods **differ**, report
by how much, and state that ranking them by accuracy is future work. Anything
stronger is unfalsifiable.

What the paper *can* claim today is consensus (§4.11): 15 of 36 proposed
locations were selected by all four algorithms, and 1,417 km² was classed High
by all four. That is method-agnostic robustness and needs no ground truth.

## 7. Limitations — write these honestly (§VI-D)

A limitations section that names real constraints reads far stronger than one
that lists generic caveats.

1. **No ground-truth validation yet.** Every reported number describes the
   model's internal behaviour; none tests the map against built structures. A
   validation harness computing ROC-AUC against known RWH structures is
   implemented and its arithmetic verified, but the structure inventory has not
   yet been assembled. **Do not report an AUC.**
2. **Input resolution is uneven.** The analysis grid is ~300 m but land cover is
   500 m, population ~1 km and rainfall ~5.3 km. The map is drawn finer than
   three of its six inputs.
3. **Edge effects from pre-clipped inputs.** Drainage density and settlement
   distance are computed from in-district features only, so a river or town just
   across the boundary is invisible. 25.8% of district pixels could have a nearer
   out-of-district settlement and 4.9% a nearer river; 8 of the 25 candidate
   sites lie in the affected zone. Bounded: combined weight 0.133, so the map and
   class areas barely move, but near-border rankings can shift.
4. **HydroRIVERS understates the network.** It is thresholded to larger channels,
   giving 0.242 km/km² against the 0.5–2.0 km/km² typical of DEM-derived
   networks. Class breaks are calibrated to this network and would need
   recalibration for another.
5. **AHP weights remain expert judgement.** CR < 0.10 establishes internal
   consistency, not correctness. Sensitivity analysis bounds the consequence but
   does not remove the subjectivity.
6. **No socio-economic or cost dimension.** No land value, acquisition or
   construction-cost data. The "low-earthwork" scenario is a proxy via slope and
   land cover, not a cost model.
7. **Soil class coding unverified** against the source dataset's own
   documentation.

## 8. Things the paper must NOT claim

- **No AUC, accuracy, precision/recall or any validation metric.** None exists.
- **No machine learning.** There is no trained model. Do not describe one.
- **No field verification.** No site has been visited.
- **No "cost" analysis.** Call the third scenario low-earthwork siting.
- **No annual runoff volume.** Runoff is reported per design storm only.
- Do not describe runoff as an AHP criterion — it is a derived output surface,
  deliberately excluded from the weighting to avoid double-counting land cover,
  soil and rainfall.

## 9. Figures

| Fig. | Content | Source |
|---|---|---|
| 1 | Study area (India → Maharashtra → Chandrapur) | Existing slide |
| 2 | Methodology workflow | Existing slide, updated for drainage density |
| 3 | Six criterion score surfaces (2×3 panel) | Screenshot per criterion |
| 4 | Final classified suitability map with 25 ranked sites | `outputs/rwh_suitability_map.png` |
| 5 | Derived hydrology: drainage density, Curve Number, runoff depth, runoff coefficient | `outputs/derived_hydrology.png` |
| 6 | Sensitivity — influence per criterion (bar chart) | Table 4.7 |
| 7 | Algorithm comparison — 4 maps or the comparison table | §4.8 |
| 8 | Agreement across the 4 algorithms | `outputs/agreement_algorithms.png` |
| 9 | Agreement across the 5 scenarios | `outputs/agreement_scenarios.png` |

## 10. References

Reuse the 8 domain papers already in the literature review ([5]–[12] of the
existing deck: Seif et al. 2023; Al-Hasani et al. 2024; Mustapha et al. 2023;
Haziq & Ibrahimi 2020; Resen et al. 2023; Fetene et al. 2023; Alene et al. 2022;
Adham et al. 2018). **Drop the four LLM/GIS-agent papers** — the NLP component
was removed from scope.

Add roughly 12–15 more covering: Saaty's original AHP; Buckley's fuzzy AHP;
Hwang & Yoon on TOPSIS; Chang's extent analysis (to cite the criticism); the SCS
Curve Number handbook; CHIRPS (Funk et al.); HydroSHEDS/HydroRIVERS (Lehner,
Linke); SoilGrids (Hengl et al.); MODIS MCD12Q1 (Friedl et al.); WorldPop
(Tatem); drainage-density and morphometric analysis in groundwater potential
mapping; and 2–3 recent GIS-MCDA sensitivity-analysis papers.

## 11. Reproducing every number

```
python -c "from gis_analysis import run_ahp_analysis; r=run_ahp_analysis('data'); print(r['area_statistics'])"
python sensitivity.py      # §4.7, §4.7b, §4.7c
python algorithms.py       # §4.8
python derived_maps.py     # §4.9
python exports.py          # writes the site table and map figure
python consensus.py --write # §4.11 — consensus tables + agreement maps
python validation.py       # reports missing_data until structures exist
```

## 12. Suggested title and abstract skeleton

**Title:** *Reproducible GIS-MCDA for Rainwater Harvesting Site Selection:
Criterion Normalisation, Weight Sensitivity and Method Comparison in Chandrapur
District, India*

**Abstract skeleton (200–250 words):** problem (groundwater decline despite
1,472 mm/yr) → approach (six criteria, AHP CR 0.0235, WLC on a 123,555-cell
grid) → the normalisation contribution (fixed reclassification; min–max left
97% of slope pixels above 0.90) → result (High 18.5%, 2,113 km²; 25 ranked sites
with per-criterion attribution) → robustness (±20% retains 90% of the top 10) →
method comparison (aggregation dominates weighting: WLC→TOPSIS 5 pp and 75%
class agreement, versus 0.2 pp for AHP→Fuzzy-AHP) → conclusion.

**Index Terms:** Rainwater harvesting, GIS, Multi-criteria decision analysis,
Analytic Hierarchy Process, TOPSIS, Fuzzy-AHP, Sensitivity analysis, Drainage
density, Chandrapur.
