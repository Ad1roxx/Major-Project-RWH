# Methodology — Criterion Scoring and Aggregation

This document justifies every number used to turn raw spatial data into a
0–1 suitability score. It is the reference for the project report and for
questions during evaluation. All constants live in `criteria.py`; nothing in
this document is hard-coded anywhere else.

**Last updated:** 8 August 2026

---

## 1. Why fixed reclassification instead of min–max rescaling

The earlier implementation normalised every criterion with a min–max rescale
over the observed values of that raster. Measured on the project's own data,
that produced:

| Layer | Observed range | After min–max normalisation |
|---|---|---|
| `slope.tif` | 0 – 72.4° | mean 0.98 — **97.4% of pixels scored > 0.90** |
| `population.tif` | 1.9 – 9101 people/km² | mean 0.98 — **97.7% of pixels scored > 0.90** |

A single steep escarpment and the Chandrapur urban core stretched each range so
far that every other pixel collapsed to ≈ 1.0. Slope carries 22.5% of the total
AHP weight and was contributing an almost constant value, so it could not
discriminate between sites at all.

The two categorical layers were worse. Min–max on a class *code* is meaningless:

- `soil_texture.tif` holds codes {1, 4, 6, 7}, so Sand scored 0.00 and Silt Clay
  Loam scored 1.00 purely because 7 > 1.
- `lulc.tif` holds IGBP codes, so class 17 (**Water**) scored 1.00 and class 13
  (**Urban**) scored 0.75, while class 4 (deciduous forest) scored 0.00.

Together, roughly 48% of the total AHP weight was either flat or semantically
inverted, meaning the output map was effectively driven by rainfall and
distance-to-river alone.

Fixed reclassification fixes all of this and adds two properties the project
needs: **reproducibility** (a 4° slope always scores 0.70, whatever else is in
the raster) and **transferability** (the same tables can be applied to another
district without re-deriving anything).

---

## 2. Slope — cost criterion, interpolated ramp

**Units: degrees.** GDAL's `Slope` tool outputs degrees unless `-p` is passed,
and the raster's maximum of 72.4° is consistent with degrees on a 90 m DEM.

Scores are interpolated linearly between these anchors, so 0.3° outranks 0.9°:

| Slope | Score | Reasoning |
|---|---|---|
| 0° | 1.00 | Dead level; ideal for percolation tanks and ponds |
| 1° | 0.95 | Near-level |
| 3° | 0.85 | Very gentle; ideal for most RWH structures |
| 5° | 0.68 | Gentle; suitable, mild earthwork |
| 10° | 0.42 | Moderate; check dams only, higher cost |
| 15° | 0.20 | Steep; marginal |
| 25°+ | 0.08 → 0.05 | Impractical to impound |

Gentle slopes hold water long enough for it to infiltrate; steep slopes
accelerate runoff and raise earthwork cost. Chandrapur is very flat — median
slope 0.8°, 90th percentile 2.6° — so these breaks place most of the district in
the top two classes while still separating the hilly south-west.

---

## 3. Soil texture — categorical lookup

Objective is groundwater **recharge**, so moderate-to-good infiltration scores
highest. Pure sand infiltrates fastest but retains nothing and gives poor
structural stability for embankments; clay-rich texture impedes the recharge the
project exists to promote.

**Source.** ISRIC SoilGrids250m, product `TEXMHT_M_sl1` — *Texture class (USDA
system) at depth 0.00 m*, published 2017-03-10. Cite Hengl et al. 2017,
doi:10.1371/journal.pone.0169748.

The legend is taken verbatim from the `LEGEND` metadata tag on the original
download. All twelve classes are tabulated so the table transfers; only 1, 4, 6
and 7 occur in Chandrapur.

| Code | Class | Score | Reasoning | District share |
|---|---|---|---|---|
| 1 | Clay | 0.25 | Very low infiltration, impedes recharge | 18.61% |
| 2 | Silty Clay | 0.30 | Very low infiltration | — |
| 3 | Sandy Clay | 0.40 | Low infiltration, some sand fraction | — |
| 4 | Clay Loam | 0.60 | Moderate infiltration, good retention | 77.82% |
| 5 | Silty Clay Loam | 0.55 | Moderate-low infiltration | — |
| 6 | Sandy Clay Loam | 0.80 | Good infiltration, structurally stable | 3.19% |
| 7 | **Loam** | **1.00** | Best infiltration/retention balance | 0.38% |
| 8 | Silt Loam | 0.95 | Very good balance | — |
| 9 | Sandy Loam | 0.85 | Good infiltration, moderate retention | — |
| 10 | Silt | 0.60 | Moderate infiltration, poor stability | — |
| 11 | Loamy Sand | 0.70 | High infiltration, limited retention | — |
| 12 | Sand | 0.55 | Very high infiltration, poor retention and stability | — |

Unrecognised codes score 0.30.

> ✅ **Legend verified 2 October 2026 — and corrected.** Until that date this
> table used an **assumed** legend mapping 1→Sand, 4→Silt Loam, 7→Silt Clay
> Loam. The assumption had no source: it entered with `criteria.py` on
> 2026-07-29 and was attributed to "the project's soil slide", but slide 22
> records only the dataset, period, resolution and CRS — no class legend. The
> attribution was incorrect and gave an assumption the appearance of provenance.
> Three of the four codes present in the district were wrong. The two consequential errors ran in opposite directions:
> code 4 (**Clay Loam**, 77.8% of the district) scored 1.00 as if it were Silt
> Loam, while code 7 (**Loam**, the best texture for this objective) scored
> 0.50. Correcting the legend moved the highly-suitable share from 18.51% to
> 6.44% and displaced 8 of the top 10 candidate sites.
>
> Full record, including provenance and measured impact:
> `docs/SOIL_LEGEND_CORRECTION.md`.

**Knock-on.** `derived_maps.HSG_FROM_SOIL` reads the same codes to assign
hydrologic soil groups and carried the same error — code 1 was group A (highest
infiltration) when Clay is group D. Corrected in the same pass; Curve Number and
both runoff surfaces changed.

---

## 4. Land use / land cover — categorical lookup

MODIS MCD12Q1 **v6.1 (collection 061), 2024 product**, IGBP `LC_Type1`, 500 m
(0.004167°), clipped to the district bounding box via NASA AppEEARS (request
`aid0001`). The original download,
`Downloads/MCD12Q1.061_LC_Type1_doy2024001000000_aid0001.tif` (md5 `a5637e89…`),
is identical cell for cell to `data/lulc.tif` (verified 2026-10-20). All 17 classes are tabulated so the table
transfers to other districts; 11 occur in Chandrapur.

| Code | Class | Score | Reasoning |
|---|---|---|---|
| 12 | Cropland | 1.00 | Highest demand, best siting economics, generates runoff |
| 14 | Cropland / Natural Vegetation Mosaic | 0.90 | As above, slightly more constrained |
| 10 | Grassland | 0.85 | High runoff, low land cost, easy siting |
| 7 | Open Shrubland | 0.70 | Good runoff, low land cost |
| 9 | Savanna | 0.70 | Workable |
| 16 | Barren | 0.65 | High runoff but poor soil and vegetation support |
| 8 | Woody Savanna | 0.60 | Partially wooded, more clearance needed |
| 6 | Closed Shrubland | 0.55 | Denser cover |
| 5 | Mixed Forest | 0.35 | Restricted, already infiltrating well |
| 1–4 | Forest classes | 0.30 | Chandrapur's forest is largely protected (Tadoba-Andhari); construction restricted |
| 11 | Permanent Wetland | 0.20 | Already saturated; poor construction ground |
| 13 | Urban and Built-up | 0.10 | Impervious, high land acquisition cost |
| 17 | Water Bodies | 0.00 | Cannot site a structure in existing water |
| 15 | Permanent Snow and Ice | 0.00 | Not applicable |

Unrecognised codes score 0.30.

---

## 5. Rainfall — benefit criterion, continuous percentile rank

Scored by **continuous percentile rank within the district**: the driest
location scores 0.20, the wettest 1.00, everything between scales with its rank.

Five discrete quintile classes were used until 8 August 2026, but they gave the
wettest 20% of the district an identical score of 1.00 — a large contributor to
the tied-sites defect described in §10.

### Source

`data/rainfall.tif` is the **mean annual rainfall surface**, built by
`build_rainfall.py` from **11 CHIRPS v3.0 annual rasters covering 2014–2024**,
in mm/year.

| Property | Value |
|---|---|
| District mean | 1,493 mm/yr |
| District range | 1,184 – 1,713 mm/yr |
| Interannual range of district means | 1,211 – 1,957 mm (sd 198 mm) |
| Native resolution | 0.05° (≈5.28 km) |

The layer is reproducible from the source downloads by running
`python build_rainfall.py` — the aggregation is in code, not hand-built in
QGIS, and the output file carries the source, year range and units in its
GeoTIFF metadata tags.

### Units check — and a real finding

The 11-year mean of 1,493 mm sits about **20% above the ≈1245 mm long-term
normal** commonly cited for Chandrapur (and quoted on the project's own
geographic-statistics slide). This is not a unit error. The per-year district
means show why:

- 2014, 2015 and 2017 fall near 1,220–1,260 mm — in line with the normal;
- every other year in the window runs 1,425–1,930 mm, peaking in 2022.

The recent decade is simply wetter than the older baseline the 1245 mm figure
derives from. **This is worth stating in the report** — it is a defensible
observation drawn from the project's own data, and it pre-empts the obvious
question about why the numbers disagree.

### Why percentile rank rather than fixed mm bands

Now that the unit is confirmed, both options are available. Percentile rank is
kept because:

- the whole district receives adequate monsoon rainfall, so what discriminates
  between *sites* is relative rainfall within the study area;
- it spreads the district's 1,184–1,713 mm range continuously instead of
  collapsing it into one or two absolute bands.

The trade-off is transferability: fixed mm bands would carry to another
district unchanged, which speaks to the "region-specific models" gap in the
literature review. Swapping them in needs only `score_continuous_breaks()` with
a break table — no other code change. A worthwhile Sprint 2 comparison.

### Coarse pixels and the district edge

CHIRPS pixels are 5.28 km across (27.9 km² each), so a clip in QGIS follows the
pixel grid rather than the district outline and looks blocky. The pipeline is
unaffected: the district mask discards every overshooting pixel, and the final
suitability raster has **0 pixels outside the boundary and 0 unscored pixels
inside**.

`build_rainfall.py` reads a 0.20° margin around the district, so the rainfall
layer now covers the district completely and needs **no gap filling at all**
(it previously required 5.7%).

For a clean-edged rainfall figure in QGIS, resample *before* clipping: Warp
(Reproject) with bilinear resampling to 250 m, then Clip Raster by Mask Layer
with "match the extent of the clipped raster to the extent of the mask layer".
State in the report that this is cosmetic — resampling does not add information,
the underlying field is still 5.28 km.

---

## 6. Drainage density — benefit criterion, interpolated ramp

**This is the variable the project documentation names.** The criteria slide
defines drainage density ("indicates runoff concentration; helps locate
collection points"), the data slide describes summarising river length within a
regular grid and converting to length per unit area, and references [5]–[12]
all cite drainage *density*.

> ⚠ **Corrected 2026-08-04.** The implementation previously scored **distance to
> the nearest river** instead — a siting-convenience measure, not drainage
> density. The project's own slides were internally inconsistent on this point
> (the data slide described density, the implemented-methodology slide described
> a distance transform). Both the code and the slides should now say density.

### Computation

Rasterising river lines yields only a boolean "channel present" mask, which
cannot give a density. Instead:

1. Each river line is densified into ~100 m segments.
2. Every segment's length is accumulated into the analysis cell containing its
   midpoint, with length measured via local degree-to-km scaling so the result
   is in true kilometres. (Verified: 2,765.6 km binned against 2,767.7 km of
   input geometry — 0.08% loss.)
3. A circular moving window sums length and divides by window area to give
   km/km².

**Window radius 2.5 km (≈20 km²).** A 1 km window over the 0.3 km analysis grid
is only about 3×3 cells and gives a speckled, noisy surface; 2.5 km produces a
smooth field that still resolves sub-district variation.

District-wide density is **0.242 km/km²** (2,766 km of channel over 11,414 km²),
with local values ranging 0.00–0.85 km/km².

### Class breaks

Higher density means more runoff is concentrated and available to harvest, so
this is a benefit criterion.

Scores are interpolated linearly between these anchors:

| Drainage density | Score |
|---|---|
| 0.00 km/km² | 0.10 |
| 0.10 | 0.25 |
| 0.20 | 0.50 |
| 0.30 | 0.72 |
| 0.40 | 0.88 |
| 0.90 | 1.00 (district maximum ≈0.85) |

> ⚠ **These breaks are calibrated to a HydroRIVERS-derived network.**
> HydroRIVERS is thresholded to larger channels, so its densities sit an order
> of magnitude below the 0.5–2.0 km/km² bands used in studies working from
> DEM-extracted stream networks. If the network is ever re-derived from
> `dem.tif` by flow accumulation, these breaks must be recalibrated — preserve
> the class *shares*, not the numbers.

**Note on direction.** Some recharge-focused studies treat *low* drainage
density as more suitable, on the basis that a less-dissected landscape
infiltrates more. This project follows its own stated rationale — density
indicates where runoff concentrates, which is where collection structures
belong — and treats it as a benefit. Worth stating explicitly in the report,
since a reviewer may expect the opposite convention.

---

## 6a. Runoff — a derived map, deliberately not a criterion

`derived_maps.py` produces an SCS Curve Number surface, a runoff depth surface
and a runoff coefficient surface, written as GeoTIFFs plus a four-panel figure
(`outputs/derived_hydrology.png`).

**Curve Number** comes from IGBP land cover × hydrologic soil group, at AMC II
and good hydrologic condition, using USDA-NRCS TR-55 land-use analogues. Soil
texture maps to HSG as Sand → A, Silt Loam → B, Sandy Clay Loam → C, Silt Clay
Loam → D. District mean CN is **70.5**, ranging 30 (forest on sandy soil) to 100
(open water).

**Runoff** follows the standard SCS-CN form, with S = 25400/CN − 254,
Ia = 0.2 S, and Q = (P − Ia)² / (P + 0.8 S) for P > Ia.

### Why a design storm and not the annual total

SCS-CN is an **event** model: P is the depth of one storm. Feeding it an annual
total is a shortcut seen in the literature, and it is demonstrably wrong here.
At P = 1,493 mm (Chandrapur's mean annual rainfall):

| Land cover | CN | Runoff coefficient at P = 1,493 mm | at P = 100 mm |
|---|---|---|---|
| Forest | 55 | 0.85 | 0.13 |
| Shrubland | 70 | 0.92 | — |
| Cropland | 78 | 0.94 | — |
| Built-up | 85 | 0.96 | 0.61 |

At the annual total every land cover collapses to 0.85–0.96 and the map carries
no spatial information — the same failure mode as min–max normalisation (§1).
The maps are therefore produced for a **100 mm design storm**, roughly a one-day
monsoon event, and labelled as such. District mean runoff is 35.4 mm, mean
coefficient 0.354.

To obtain a defensible *annual* runoff volume, run the model per month on
monthly CHIRPS rasters and sum the twelve results. That needs the monthly
download, which the project does not currently hold.

### Why runoff is not an AHP criterion

Curve Number is a function of LULC and soil; runoff is additionally a function
of rainfall. All three are already weighted criteria. Adding runoff as a seventh
criterion would silently double-weight them, which is a legitimate line of
attack on the model. It is therefore reported as a derived surface. The clean
alternative, if it must be weighted, is runoff *replacing* rainfall rather than
sitting alongside it.

---

## 7. Settlement proximity — moderate-optimal on distance to settlement

Replaces the earlier "population density, lower is better", which contradicted
the project's own stated rationale ("where water is actually needed"). The
design intent is a site in suitable terrain but set back from the settlement it
serves.

A **settlement** is any pixel with population density ≥ **400 people/km²**
(district mean is 193). This classifies 6.6% of Chandrapur's pixels as
settlement, which matches the built-up footprint well. Distance is then measured
from that mask.

| Distance from settlement | Score |
|---|---|
| 0 km (inside the settlement) | 0.05 |
| rises to 1 km | 0.05 → 0.97 |
| 1 – 5 km (optimal band) | 0.97 → **1.00 at 3 km** → 0.97 |
| falls linearly to 15 km | 0.97 → 0.10 |
| > 15 km | 0.10 |

The band is a gentle peak rather than a flat plateau. Everything in 1–5 km still
scores at least 0.97, so the band reads as "1–5 km is optimal", but the centre is
strictly preferred — a flat 4 km-wide top gave thousands of locations identical
scores (§10).

**The one-sentence justification:** peak suitability 1–5 km from a settlement —
close enough that harvested water serves real demand, far enough to avoid
built-up impervious land, land-acquisition cost and greywater contamination.

The density threshold and the distance band are starting values chosen from the
district's own density distribution. They should be reviewed with the project
guide and stated as assumptions in the report.

---

## 8. Aggregation

### Weighted Linear Combination

`S(x,y) = Σ wᵢ · rᵢ(x,y)` over the criteria that have data at that pixel, with
the weights renormalised to sum to 1 at each pixel. Without renormalisation, a
pixel missing one layer would be scored on a scale that no longer reaches 1.0
and would be unfairly penalised.

### Minimum coverage gate

A pixel is scored only if at least **80%** of the total AHP weight has data
there. Before this gate existed, edge pixels holding only rainfall and LULC
(0.49 of the weight) could score 1.000 from two criteria and outrank genuine
sites evaluated on all six — 13 of the original top 25 sites were such
artefacts.

### Gap filling

The source layers stop at slightly different places near the district boundary
(CHIRPS rainfall reached only 94.3% of boundary pixels). Gaps *inside* the
district are filled from the nearest valid pixel, which is appropriate for
layers that vary slowly in space and keeps the analysis covering the whole
district. Filled shares: soil 2.2%, population 2.0%, slope 1.1%, LULC 0.1%.
Rainfall no longer needs filling — `build_rainfall.py` reads a 0.20° margin
around the district, so the layer covers it completely (it previously required
5.7%).

With gap filling in place, the analysed area is 11,412 km² against the
district's official 11,443 km² — a 99.7% match, which is a useful sanity check
on the boundary mask and the pixel-area calculation.

---

## 9. Classification into Low / Medium / High

**Fixed thresholds on the 0–1 score**, not percentiles:

| Class | Threshold | Result on current data |
|---|---|---|
| High | ≥ 0.85 | 18.5% — 2,107 km² |
| Medium | 0.65 – 0.85 | 54.8% — 6,254 km² |
| Low | < 0.65 | 26.7% — 3,051 km² |

> **Why not percentiles.** A 33rd/67th percentile split is self-fulfilling: it
> reports ≈33% of the district as highly suitable *whatever* the underlying
> scores, so the percentage is an artefact of the method, not a finding. The
> earlier percentile implementation duly returned 32.9 / 34.0 / 33.1. Fixed
> thresholds make the reported area a real, comparable result — and 18.5% sits
> within the 19–34% "suitable" range reported by the comparable GIS-MCDA studies
> in the literature review.

`CLASSIFICATION_MODE = "percentile"` in `criteria.py` restores the old behaviour
if a comparison is wanted for the report.

---

## 10. Candidate site extraction

1. **Best per tile** — the grid is divided into 5 × 5 tiles and the highest
   scoring pixel inside the high-suitability mask is taken from each, so sites
   are spread across the district rather than clustered in one corner.
2. **Global maxima fill** — remaining slots are filled from the highest scoring
   remaining pixels, subject to a **5 km minimum separation** enforced by
   haversine distance.

### Tie-breaking

Discrete reclassification deliberately produces a small set of possible scores,
**this was a real defect, fixed on 8 August 2026.** Step classes gave every
pixel in a criterion's best band the identical score of 1.00. With all six
criteria doing that, **973 pixels scored exactly 1.000 on everything** — so the
top seven candidate sites were tied, every row of the site-comparison panel read
100%, and the ranking carried no information.

The fix was to replace the flat tops with interpolated ramps (§2, §5, §6) and to
give the settlement band a gentle peak instead of a 4 km-wide plateau (§7). The
class breakpoints are retained as anchors, so reproducibility and transferability
are unchanged.

Result: distinct scores across the district rose from 47,495 to **108,229**, and
the number of pixels sharing the maximum fell from **973 to 1**. The top 25
sites now hold 22 distinct scores and differ criterion by criterion, so both the
ranking and the comparison panel are meaningful.

A small continuous tie-break (weight 1e-3) is retained as a safety net for
genuine ties, but with continuous scoring it almost never engages.

---

## 11. Per-site explainability

Each candidate reports:

- rank, coordinates, and overall suitability score;
- per-criterion normalised score as a percentage;
- weighted contribution per criterion (`AHP weight × score`);
- criteria satisfied (normalised score ≥ 0.66);
- the raw measured values behind the scores — slope in degrees, soil class name,
  land-cover class name, drainage density in km/km², and distance to the nearest
  settlement in km.

Criteria are always listed in AHP priority order so the explanation mirrors the
decision logic used during scoring.

---

## 12. Known limitation — pre-cropped inputs and the district edge

`slope.tif`, `soil_texture.tif`, `lulc.tif`, `population.tif` and
`rivers.geojson` were clipped to the Chandrapur outline in QGIS before entering
the project. `rainfall.tif` is not — `build_rainfall.py` reads a 0.20° margin.

For most of the pipeline this is harmless: the district mask clips the output
anyway, and rainfall quantile breaks are computed on district pixels only. It
matters for the criteria that measure **distance or density**, which see only
features *inside* the district and are therefore blind to a river or settlement
just across the boundary.

Measured on the current inputs:

| Effect | Extent |
|---|---|
| District within 5 km of the border | 24.4% |
| Pixels where an out-of-district **settlement** could be nearer | 25.8% |
| Pixels where an out-of-district **river** could be nearer | 4.9% |
| Rim pixels needing gap fill (caused by cropping) | soil 2.17%, population 2.03%, slope 1.05%, LULC 0.11% |
| Candidate sites in the exposed zone | **8 of 25, including rank #1** |

Drainage *density* is affected the same way and slightly more directly than
distance was: a 2.5 km window centred near the border sums channel length only
from the inside, so density is systematically under-estimated along the rim.

**Bounded magnitude.** Settlement proximity carries 0.040 of the AHP weight and
drainage 0.093, so the worst-case swing in a pixel's final score is 0.133. The
suitability map and class areas are barely affected away from the border. The
effect is on candidate *ranking*, where the top plateau is separated by fine
tie-breaks.

**Fix:** re-export the affected layers clipped to a **20 km buffered** boundary
rather than the outline (QGIS: Vector → Geoprocessing Tools → Buffer, then use
the buffered polygon as the mask layer). Priority: `rivers.geojson`, then
`population.tif`, then the remaining rasters to remove the rim gap fill. No code
change is needed — the pipeline masks output to the true district regardless, so
buffered inputs cost only file size.

Until then, state as a limitation: *distance- and density-based criteria are
computed from in-district features only, which may understate drainage density
and overstate settlement distance for the ~24% of the district within 5 km of
the boundary.*

---

## 13. Open items

1. ~~Replace the provisional rainfall raster~~ — **done 4 Aug 2026.** Now an
   11-year CHIRPS v3.0 mean annual surface (2014–2024); see §5.
2. **Confirm the soil class coding** against the exported file's metadata (§3).
3. **Review the settlement threshold and distance band** with the project guide
   and record them as stated assumptions (§7).
4. **Validate** predicted high-suitability areas against known RWH structures
   and compute AUC — planned for Sprint 3.
