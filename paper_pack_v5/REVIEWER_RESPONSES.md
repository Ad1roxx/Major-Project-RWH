# Reviewer questions and the agreed answers

These answer questions the panel and reviewers raised after v4. The team has
decided **not to change the model**. Each answer strengthens the
justification for what exists, and the validation now adds evidence to
several of them. Wording is ready to adapt into the paper (Methods,
Discussion, Limitations) and the response letter.

---

## 1. "Rainwater harvesting and groundwater recharge are conflicting criteria"

**Position:** they aren't two objectives. The study targets
**recharge-oriented rainwater harvesting**: capturing monsoon runoff so it
reaches groundwater.

> Rainwater harvesting and groundwater recharge are treated here as one
> objective, harvesting monsoon runoff in order to recharge groundwater.
> Chandrapur receives about 1,490 mm a year, concentrated in one short
> monsoon, and most of it runs off: the mean runoff coefficient for a 100 mm
> design storm is 0.637 (Curve Number 89 covers 62.6% of the district).
> The constraint is therefore retention of runoff in the subsurface rather
> than rainfall supply, which makes recharge structures (percolation tanks,
> check dams, recharge pits) the appropriate target.
>
> Five of the six criteria (rainfall, slope, drainage density, land cover,
> settlement proximity) favour the same locations for storage and recharge
> structures alike. Only soil texture differs in direction, and its scoring
> deliberately favours infiltration (Loam 1.00 > Sandy Clay Loam 0.80 > Clay
> Loam 0.60 > Clay 0.25), following USDA TR-55 hydrologic soil groups and FAO
> basic infiltration rates. A storage-oriented variant, with the soil
> ordering reversed, is identified as future work.

- **Don't overclaim.** The storage/recharge difference is real. The study
  made an explicit choice; it doesn't deny the difference.
- **Evidence now available, used carefully:** the photo audit labels separate
  `storage` from `recharge`.
  - All 12 photo-confirmed structures were labelled *storage* by both
    labellers.
  - Only one of 480 labels was *recharge*.
  - This **doesn't** show that MGNREGA builds storage rather than recharge
    works. The protocol labels percolation tanks and check dams as
    *storage* because they hold open water, though their purpose is
    recharge. Recharge pits and trenches are also hard to see in photos. Use
    the split only to say what is visible in photos, not what the works are
    for.
- **CGWB checked (2026-10-20); it does NOT support a "declining groundwater"
  justification.** See `CGWB_FINDINGS.md`.
  - The district is Safe, at a 19.35% stage of development.
  - Significant decline covers only 7% of the area.
  - CGWB judges recharge **not feasible** in the six north-eastern blocks
    that hold 43.1% of our High zone.
  - Its 418 proposed recharge sites score below chance on our map (AUC
    0.362).
- **So this answer must change, and the team must choose:**
  - **(A) (recommended):** reframe the objective as surface
    rainwater-harvesting suitability. Recharge becomes one use of harvested
    water, valid where the aquifer has room.
  - **(B):** keep the recharge framing, with the CGWB comparison as a major
    limitation.

  Under (A) the quoted paragraph above becomes:

  > The study maps where monsoon runoff can be captured: where rainfall is
  > plentiful, slopes are gentle, soils and land cover suit harvesting
  > structures and demand is near. Chandrapur's problem is the loss of
  > monsoon rainfall as runoff (mean runoff coefficient 0.637 for a 100 mm
  > storm; Curve Number 89 over 62.6% of the district), not a shortage of
  > rain. Whether harvested water should then be used to recharge the
  > aquifer depends on aquifer capacity, which the surface criteria cannot
  > see: the Central Ground Water Board judges artificial recharge feasible
  > in only nine of the district's fifteen blocks, and the district as a
  > whole remains Safe (all fifteen blocks; stage of extraction 29.3% in
  > the 2023 assessment, up from 19.35% in 2017).
  > Surface suitability and aquifer capacity therefore point to different
  > parts of the district (Section X), and siting a recharge structure
  > requires both.

  Keep the soil ordering. It still favours infiltration at the structure,
  but it is no longer described as maximising aquifer recharge.

## 2. "Did you use groundwater recharge or recharge-zone data?"

**Position:** no dedicated hydrogeological layer. Say so plainly.

> The six criteria are those most frequently used in groundwater-potential
> and recharge-zone studies (slope, soil, land cover, drainage density,
> rainfall), so recharge potential is represented through its surface
> controls; infiltration is also quantified directly by the SCS-CN surfaces
> (Fig. hydrology). Subsurface layers (lithology, lineaments, geomorphology,
> aquifer type) were excluded so that every input is openly available,
> consistently gridded and reproducible in other districts. The output
> screens surface suitability at district scale; site-level hydrogeological
> verification remains part of pre-construction practice (Fig. 20).

Future sources: GSI Bhukosh (geology, lineaments, geomorphology), NRSC
groundwater-prospect maps, CGWB/India-WRIS water levels, CGWB NAQUIM aquifer
maps.

**Now partly answered with data.** The CGWB NAQUIM report for Chandrapur
(2021) was compared with the model (`CGWB_FINDINGS.md`). Its proposed
recharge sites fall mainly in the model's Low zone, and its "recharge not
feasible" blocks hold 43.1% of the High zone. This is the clearest evidence
that the omitted aquifer-capacity information matters. Report it, and make
CGWB's depth-to-water and feasibility map the first named addition in
future work.

## 3. "How standardised are the resolutions? Could they be more precise?"

> All inputs are resampled to one common grid of 450 rows × 422 columns
> (≈0.30 km E–W × 0.31 km N–S; 123,555 cells inside the district), bilinear
> for continuous layers and nearest neighbour for categorical ones; the
> mask's area matches the official district area to 99.7%. The grid sits
> between the finest inputs (SoilGrids 250 m, HydroSHEDS ~90 m) and the
> coarsest (CHIRPS ~5.3 km): a finer grid would add no information to the
> coarse layers and would imply precision the data cannot support. Rainfall
> varies smoothly at district scale, and CHIRPS v3.0 is the finest openly
> available long-term gridded record; SoilGrids is the finest open soil
> texture raster. Finer open products exist for land cover (10 m), elevation
> (30 m) and population (100 m) and are noted as future refinement. The
> results are intended for district-level screening, not structure design.

**Don't write** "it couldn't be more precise". It's true for rainfall and
soil only.

## 4. "How do you validate the approach?"

**Now answered by data** (`VALIDATION_FINDINGS.md`):
- **Agreement:** baseline AUC 0.661 [0.650, 0.672] against 3,119 MGNREGA
  water works; all 20 surfaces lie between 0.63 and 0.72.
- **Classes:** High land holds 1.9× its share of works.
- **Robustness:** the result holds under thinning, removing settlement, and
  restricting to cropland.
- **Lower bound:** the figures understate agreement, because most works in
  the water categories aren't harvesting structures (photo audit,
  κ = 0.459).

Plus the existing robustness evidence that needs no ground truth:
- three complementary sensitivity analyses;
- agreement across the four methods: 15 sites picked by all four, and
  528.5 km² High under all four;
- the Loam robustness check (Loam rescored to 0.80: High 6.44% → 6.40%,
  top 10 keeps 6/10).

## 5. Professor's requests (done, describe briefly if relevant)

- **Taluka-wise boundary map:** Fig 1 (d), with 15 Census 2011 talukas.
- **Population heatmap:** in the web application, a display layer only
  (1.5 km Gaussian-smoothed WorldPop density).
- **Farmland-scenario site context:** in the web application, a display layer
  only. For each site it shows the nearest water work and river, and the
  cropland within 1 km.
- **A creative architecture figure:** Fig 4, the illustrated framework.
