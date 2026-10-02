"""
criteria.py
───────────
Criterion normalisation (reclassification) for RWH suitability analysis.

Every criterion raster is converted to a 0–1 suitability score here, and
*only* here. Each scoring table is an explicit, citable constant rather than a
data-driven rescale, which means:

  • the scores are reproducible — the same slope value always scores the same,
    regardless of which district (or which subset of a district) is analysed;
  • the scores are defensible — each break point maps to a stated physical
    reason rather than to the observed min/max of one raster;
  • categorical layers (soil texture, LULC) are scored by *class meaning*
    rather than by the numeric value of the class code.

See docs/METHODOLOGY.md for the justification behind every number below.

Normalisation types used (matching the project's methodology slide):
  1. Benefit / cost, anchored ramp    → score_ramp()
  2. Categorical class lookup         → score_categorical()
  3. Relative benefit within district → score_percentile_benefit()
  4. Moderate-optimal (best in a
     middle range, worse either side) → moderate_optimal()

Anchored ramps replaced step classes on 8 August 2026: a step gives every pixel
in the best band the identical score 1.00, which left ~1,000 pixels tied at a
perfect score and made the site ranking meaningless. Ramps keep the same
physically justified anchors while restoring a strict ordering.
"""

from __future__ import annotations

import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# 1. SLOPE — cost criterion, fixed class breaks
# ─────────────────────────────────────────────────────────────────────────────
# Units: DEGREES. GDAL's `Slope` algorithm outputs degrees unless the `-p`
# (percent) flag is passed; the project's slope raster tops out at 72.4°, which
# is consistent with degrees on a 90 m DEM.
#
# Gentle slopes retain water long enough to infiltrate and allow low-cost
# structures; steep slopes accelerate runoff, raise earthwork cost and make
# impoundment impractical.
#
# ⚠ Why a RAMP and not flat classes.
# Step classes give every pixel in the best class the identical score 1.00. With
# six criteria all doing that, ~1,000 pixels scored exactly 1.000 on everything,
# so the top candidate sites were all tied and the site-comparison panel showed
# 100% on every row — the ranking carried no information. The class breakpoints
# below are retained as ANCHORS, but scores are linearly interpolated between
# them, so a 0.3° slope now scores above a 0.9° slope.
#
# This keeps both properties the class breaks were introduced for: a given slope
# always maps to the same score (reproducible), and the anchors are physically
# justified rather than derived from the data range (transferable).
#
# Format: ordered (slope_degrees, score) anchors, interpolated between.
SLOPE_RAMP_DEG: tuple[tuple[float, float], ...] = (
    (0.0, 1.00),    # dead level    — ideal ponding / percolation tanks
    (1.0, 0.95),    # near-level
    (3.0, 0.85),    # very gentle   — ideal for most RWH structures
    (5.0, 0.68),    # gentle        — suitable, mild earthwork
    (10.0, 0.42),   # moderate      — check dams only, higher cost
    (15.0, 0.20),   # steep         — marginal
    (25.0, 0.08),   # very steep
    (90.0, 0.05),   # impractical to impound
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. SOIL TEXTURE — categorical lookup
# ─────────────────────────────────────────────────────────────────────────────
# Source: ISRIC SoilGrids250m, product TEXMHT_M_sl1 — "Texture class (USDA
# system) at depth 0.00 m", published 2017-03-10. Cite Hengl et al. 2017,
# doi:10.1371/journal.pone.0169748.
#
# The legend below is taken VERBATIM from the LEGEND metadata tag on the
# original download, which survives at
# Documents/Major Project Research Papers/Chandrapur_SoilTexture.tif:
#
#   1:Cl 2:SiCl 3:SaCl 4:ClLo 5:SiClLo 6:SaClLo 7:Lo 8:SiLo 9:SaLo 10:Si
#   11:LoSa 12:Sa          (255 = NoData)
#
# ⚠ CORRECTED 2026-10-02. Until that date this table used an assumed legend
# mapping 1→Sand, 4→Silt Loam and 7→Silt Clay Loam. That mapping had no source:
# it was introduced with this file on 2026-07-29 and attributed in a comment to
# "the project's soil slide", but slide 22 of the deck records only the dataset
# and resolution — it contains no class legend. The attribution was wrong and
# made an assumption look sourced. Three of the four codes present were wrong,
# and the two that matter were inverted: code 4 (Clay Loam, 77.8% of the
# district) scored 1.00 as if it were Silt Loam, while code 7 (Loam, the best
# texture for this objective) scored 0.50. Correcting it moved the
# highly-suitable share from 18.51% to 6.44% and displaced 8 of the top 10
# sites. Full record: docs/SOIL_LEGEND_CORRECTION.md.
#
# All 12 classes are tabulated so the table transfers beyond the four that
# occur in Chandrapur (1, 4, 6, 7).
#
# Objective is groundwater RECHARGE, so moderate infiltration combined with
# retention scores highest. Loam is the best balance. Pure sand infiltrates
# fastest but retains nothing and gives poor structural stability for
# embankments; clay-rich textures impede the recharge the project exists to
# promote.
SOIL_TEXTURE_SCORES: dict[int, float] = {
    1: 0.25,   # Clay             — very low infiltration, impedes recharge
    2: 0.30,   # Silty Clay       — very low infiltration
    3: 0.40,   # Sandy Clay       — low infiltration, some sand fraction
    4: 0.60,   # Clay Loam        — moderate infiltration, good retention
    5: 0.55,   # Silty Clay Loam  — moderate-low infiltration
    6: 0.80,   # Sandy Clay Loam  — good infiltration, structurally stable
    7: 1.00,   # Loam             — best infiltration/retention balance
    8: 0.95,   # Silt Loam        — very good balance
    9: 0.85,   # Sandy Loam       — good infiltration, moderate retention
    10: 0.60,  # Silt             — moderate infiltration, poor stability
    11: 0.70,  # Loamy Sand       — high infiltration, limited retention
    12: 0.55,  # Sand             — very high infiltration, poor retention/stability
}
SOIL_TEXTURE_LABELS: dict[int, str] = {
    1: "Clay",
    2: "Silty Clay",
    3: "Sandy Clay",
    4: "Clay Loam",
    5: "Silty Clay Loam",
    6: "Sandy Clay Loam",
    7: "Loam",
    8: "Silt Loam",
    9: "Sandy Loam",
    10: "Silt",
    11: "Loamy Sand",
    12: "Sand",
}
SOIL_DEFAULT_SCORE = 0.30  # unrecognised class code

# ─────────────────────────────────────────────────────────────────────────────
# 3. LULC — categorical lookup (MODIS MCD12Q1, IGBP LC_Type1)
# ─────────────────────────────────────────────────────────────────────────────
# All 17 IGBP classes are listed so the table generalises beyond the 11 classes
# that happen to occur in Chandrapur.
#
# Cropland scores highest (demand for irrigation water + land available at low
# acquisition cost + runoff generation). Forest scores low: Chandrapur's forest
# is largely protected (Tadoba-Andhari), construction is restricted, and
# infiltration is already good. Built-up and open water are effectively
# excluded.
LULC_SCORES: dict[int, float] = {
    1: 0.30,   # Evergreen Needleleaf Forest
    2: 0.30,   # Evergreen Broadleaf Forest
    3: 0.30,   # Deciduous Needleleaf Forest
    4: 0.30,   # Deciduous Broadleaf Forest — protected forest, restricted
    5: 0.35,   # Mixed Forest
    6: 0.55,   # Closed Shrubland
    7: 0.70,   # Open Shrubland — good runoff, low land cost
    8: 0.60,   # Woody Savanna
    9: 0.70,   # Savanna
    10: 0.85,  # Grassland — high runoff, low cost, easy siting
    11: 0.20,  # Permanent Wetland — already saturated, poor construction ground
    12: 1.00,  # Cropland — highest demand + best siting economics
    13: 0.10,  # Urban and Built-up — impervious, high land cost
    14: 0.90,  # Cropland / Natural Vegetation Mosaic
    15: 0.00,  # Permanent Snow and Ice (not present in district)
    16: 0.65,  # Barren — high runoff but poor soil/vegetation support
    17: 0.00,  # Water Bodies — cannot site a structure in existing water
}
LULC_LABELS: dict[int, str] = {
    1: "Evergreen Needleleaf Forest",
    2: "Evergreen Broadleaf Forest",
    3: "Deciduous Needleleaf Forest",
    4: "Deciduous Broadleaf Forest",
    5: "Mixed Forest",
    6: "Closed Shrubland",
    7: "Open Shrubland",
    8: "Woody Savanna",
    9: "Savanna",
    10: "Grassland",
    11: "Permanent Wetland",
    12: "Cropland",
    13: "Urban and Built-up",
    14: "Cropland / Natural Vegetation Mosaic",
    15: "Permanent Snow and Ice",
    16: "Barren",
    17: "Water Bodies",
}
LULC_DEFAULT_SCORE = 0.30  # unrecognised class code

# ─────────────────────────────────────────────────────────────────────────────
# 4. RAINFALL — benefit criterion, quantile classes
# ─────────────────────────────────────────────────────────────────────────────
# INPUT: data/rainfall.tif is the MEAN ANNUAL rainfall surface built by
# build_rainfall.py from 11 CHIRPS v3.0 annual rasters (2014–2024), in mm/year.
# District mean 1,493 mm, range 1,184–1,713 mm across Chandrapur.
#
# Units verified against Chandrapur's commonly cited long-term normal of
# ≈1245 mm. The 11-year mean runs ~20% above that normal, which is a real
# signal rather than a unit error: 2014, 2015 and 2017 sit near 1,220–1,260 mm
# while every other year in the window runs 1,425–1,930 mm (interannual sd
# 198 mm). The recent decade is simply wetter than the older baseline the
# 1245 mm figure comes from. Worth stating in the report.
#
# Rainfall is classified by QUANTILE within the district rather than against
# fixed mm thresholds. Two reasons:
#   • the whole district receives adequate monsoon rainfall, so what
#     discriminates *sites* is relative rainfall within the study area;
#   • it maximises discrimination across the district's 1,184–1,713 mm spread
#     instead of collapsing it into one or two absolute bands.
#
# Now that the unit is confirmed, fixed mm bands are a viable alternative via
# score_continuous_breaks() — they would transfer better to another district,
# at the cost of within-district discrimination. See docs/METHODOLOGY.md §5.
# Scored by CONTINUOUS percentile rank within the district rather than five
# discrete quintile classes. Quintiles gave the wettest 20% of the district an
# identical score of 1.00, which is a large source of tied sites. The continuous
# form keeps the same meaning — relative rainfall within the study area — while
# letting the wettest location outrank the second wettest.
#
# score = RAINFALL_FLOOR + (1 - RAINFALL_FLOOR) x percentile_rank
RAINFALL_FLOOR = 0.20

RAINFALL_QUANTILE_CUTS = (20.0, 40.0, 60.0, 80.0)          # kept for reference
RAINFALL_QUANTILE_SCORES = (0.20, 0.40, 0.60, 0.80, 1.00)  # kept for reference

# Set to a string to show a provisional-input warning in the app and in the
# analysis notes; None when the rainfall input is the real deal.
RAINFALL_SOURCE_NOTE = None

# ─────────────────────────────────────────────────────────────────────────────
# 5. DRAINAGE DENSITY — benefit criterion, fixed class breaks (km/km²)
# ─────────────────────────────────────────────────────────────────────────────
# Drainage density is total channel length per unit area, computed on a moving
# circular window. It is the variable named on the project's criteria slide
# ("indicates runoff concentration; helps locate collection points") and the one
# cited across references [5]–[12] — higher density means more runoff is
# concentrated and available to harvest.
#
# (An earlier implementation scored *distance to the nearest river* instead.
# That is a siting-convenience measure, not drainage density, and it did not
# match the documented methodology. Replaced 2026-08-04.)
#
# Window radius: 2.5 km. A 1 km window over a 0.3 km grid is only ~3×3 cells and
# produces a noisy, speckled surface; 2.5 km (≈20 km² window) gives a smooth
# field that still resolves sub-district variation.
DRAINAGE_DENSITY_WINDOW_KM = 2.5

# ⚠ These breaks are calibrated to a HydroRIVERS-derived network at a 2.5 km
# window, where the district-wide density is 0.242 km/km². HydroRIVERS is
# thresholded to larger channels, so its densities sit an order of magnitude
# below the 0.5–2.0 km/km² bands used in studies working from DEM-extracted
# stream networks. If the network is ever re-derived from dem.tif by flow
# accumulation, these breaks must be recalibrated — the class *shares* are what
# should be preserved, not the numbers.
#
# Interpolated between anchors rather than stepped, for the reason given above
# the slope ramp: a flat top makes every well-drained pixel score identically.
DRAINAGE_DENSITY_RAMP: tuple[tuple[float, float], ...] = (
    (0.00, 0.10),   # effectively undrained within 2.5 km
    (0.10, 0.25),   # sparse
    (0.20, 0.50),   # moderate
    (0.30, 0.72),   # good
    (0.40, 0.88),   # good runoff concentration
    (0.90, 1.00),   # dense channel network (district maximum ≈0.85)
)

# ─────────────────────────────────────────────────────────────────────────────
# 6. SETTLEMENT PROXIMITY — moderate-optimal on distance to settlement (km)
# ─────────────────────────────────────────────────────────────────────────────
# Replaces "population density, lower is better". The design intent is a site
# in suitable terrain but set back from the settlement it serves:
#
#   peak suitability 1–5 km from a settlement — close enough that harvested
#   water serves real demand, far enough to avoid built-up impervious land,
#   land-acquisition cost and greywater contamination.
#
# A settlement is any pixel whose population density is at or above the
# threshold below. At 400 people/km² (district mean is 193) this classifies
# ~6.4% of Chandrapur's pixels as settlement, which matches the built-up
# footprint well.
SETTLEMENT_DENSITY_THRESHOLD = 400.0   # people/km²
SETTLEMENT_PEAK_KM = (1.0, 5.0)        # plateau of full suitability
SETTLEMENT_FALLOFF_KM = 10.0           # distance beyond plateau to reach floor
SETTLEMENT_SCORE_AT_ZERO = 0.05        # inside the settlement itself
SETTLEMENT_FLOOR = 0.10                # remote — no demand to serve

# Threshold at which a criterion counts as "satisfied" in the explainability
# output shown per candidate site.
SATISFIED_THRESHOLD = 0.66

# ─────────────────────────────────────────────────────────────────────────────
# 7. Aggregation and classification settings
# ─────────────────────────────────────────────────────────────────────────────
# Minimum share of the total AHP weight that must have data at a pixel before
# that pixel is scored at all. The source layers do not all cover the district
# to its very edge (CHIRPS rainfall reaches only ~94% of boundary pixels), and
# without this gate an edge pixel holding just rainfall + LULC could be scored
# 1.00 from 2 criteria and outrank a genuine site evaluated on all 6.
MIN_WEIGHT_COVERAGE = 0.80

# Suitability class thresholds on the final 0–1 score.
#
# ⚠ These are FIXED thresholds, not percentiles. A percentile split (33rd/67th)
# is self-fulfilling: it always reports ~33% of the district as highly suitable
# whatever the underlying scores, so the resulting percentage is an artefact of
# the method rather than a finding. Fixed thresholds make the reported area
# statistics a real, comparable result.
#
#   High   ≥ 0.85  — weighted average sits in the upper class of essentially
#                    every criterion; a site here fails none of them badly
#   Medium   0.65 – 0.85
#   Low    < 0.65  — several criteria are in their poor classes
#
# On the current Chandrapur inputs this yields roughly 31% High / 46% Medium /
# 23% Low, which is in line with the 19–34% "suitable" shares reported by the
# comparable GIS-MCDA studies in the literature review.
SUITABILITY_THRESHOLDS = (0.65, 0.85)

# Set to "percentile" to fall back to the 33rd/67th percentile split.
CLASSIFICATION_MODE = "fixed"


# ─────────────────────────────────────────────────────────────────────────────
# Scoring functions
# ─────────────────────────────────────────────────────────────────────────────

def score_continuous_breaks(data: np.ndarray, breaks) -> np.ndarray:
    """Score a continuous raster using ordered (upper_bound, score) class breaks.

    The first class whose upper bound is >= the pixel value wins. NaN in,
    NaN out.
    """
    out = np.full(data.shape, np.nan, dtype=np.float32)
    unassigned = ~np.isnan(data)
    for upper, score in breaks:
        hit = unassigned & (data <= upper)
        out[hit] = score
        unassigned &= ~hit
        if not unassigned.any():
            break
    return out


def score_categorical(data: np.ndarray, table: dict, default: float) -> np.ndarray:
    """Score a categorical raster via an explicit {class_code: score} lookup.

    Values are rounded to the nearest integer first, because reprojection can
    introduce tiny floating-point drift on class codes. Codes absent from the
    table receive `default`. NaN in, NaN out.
    """
    out = np.full(data.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(data)
    if not valid.any():
        return out

    codes = np.rint(data[valid]).astype(np.int32)
    scores = np.full(codes.shape, default, dtype=np.float32)
    for code, score in table.items():
        scores[codes == int(code)] = score
    out[valid] = scores
    return out


def score_quantiles(data: np.ndarray, cuts=RAINFALL_QUANTILE_CUTS,
                    scores=RAINFALL_QUANTILE_SCORES) -> np.ndarray:
    """Score a benefit raster by quantile class within the study area.

    `cuts` are percentiles (ascending); `scores` must be len(cuts) + 1 long and
    ascending. NaN in, NaN out.
    """
    if len(scores) != len(cuts) + 1:
        raise ValueError("scores must have exactly one more entry than cuts")

    out = np.full(data.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(data)
    if not valid.any():
        return out

    values = data[valid]
    edges = np.percentile(values, cuts)
    # np.digitize returns the class index directly (0..len(cuts))
    idx = np.digitize(values, edges, right=True)
    out[valid] = np.asarray(scores, dtype=np.float32)[idx]
    return out


def moderate_optimal(distance_km: np.ndarray, peak_lo: float, peak_hi: float,
                     falloff_km: float, score_at_zero: float,
                     floor: float, band_edge: float = 0.97) -> np.ndarray:
    """Moderate-optimal score: best inside [peak_lo, peak_hi].

        score_at_zero  at distance 0
        rises to `band_edge` at peak_lo
        peaks at 1.0 at the centre of the band
        returns to `band_edge` at peak_hi
        falls linearly to `floor` at peak_hi + falloff_km

    The band is a gentle peak rather than a flat plateau. A flat top would give
    every location in a 4 km-wide band the identical score of 1.00, which was a
    major source of tied candidate sites. The band still reads as "1–5 km is the
    optimal range" — everything inside scores at least `band_edge` — but the
    centre of the range is now strictly preferred, so ranking is possible.

    NaN in, NaN out.
    """
    centre = (float(peak_lo) + float(peak_hi)) / 2.0
    xs = [0.0, float(peak_lo), centre, float(peak_hi),
          float(peak_hi) + float(falloff_km)]
    ys = [float(score_at_zero), float(band_edge), 1.0, float(band_edge),
          float(floor)]

    out = np.interp(distance_km, xs, ys, left=score_at_zero, right=floor)
    out = np.asarray(out, dtype=np.float32)
    out[np.isnan(distance_km)] = np.nan
    return out


def score_ramp(data: np.ndarray, anchors) -> np.ndarray:
    """Score a continuous raster by linear interpolation between (value, score)
    anchors. Anchor values must be ascending. NaN in, NaN out."""
    xs = [float(a[0]) for a in anchors]
    ys = [float(a[1]) for a in anchors]
    out = np.interp(data, xs, ys, left=ys[0], right=ys[-1])
    out = np.asarray(out, dtype=np.float32)
    out[np.isnan(data)] = np.nan
    return out


def score_percentile_benefit(data: np.ndarray, floor: float = RAINFALL_FLOOR) -> np.ndarray:
    """Continuous benefit score from within-district percentile rank.

    The lowest value scores `floor`, the highest scores 1.0, everything in
    between scales linearly with its rank. NaN in, NaN out.
    """
    out = np.full(data.shape, np.nan, dtype=np.float32)
    valid = ~np.isnan(data)
    if not valid.any():
        return out

    values = data[valid]
    order = np.argsort(values, kind="stable")
    ranks = np.empty(len(values), dtype=np.float32)
    ranks[order] = np.arange(len(values), dtype=np.float32)
    pct = ranks / max(1, len(values) - 1)
    out[valid] = floor + (1.0 - floor) * pct
    return out


def score_drainage_density(density_km_per_km2: np.ndarray) -> np.ndarray:
    """Suitability from drainage density in km/km² (higher is better)."""
    return score_ramp(density_km_per_km2, DRAINAGE_DENSITY_RAMP)


def score_slope(slope_degrees: np.ndarray) -> np.ndarray:
    """Suitability from slope in degrees (lower is better)."""
    return score_ramp(slope_degrees, SLOPE_RAMP_DEG)


def score_settlement_distance(distance_km: np.ndarray) -> np.ndarray:
    """Suitability from distance-to-settlement in km."""
    return moderate_optimal(
        distance_km,
        peak_lo=SETTLEMENT_PEAK_KM[0],
        peak_hi=SETTLEMENT_PEAK_KM[1],
        falloff_km=SETTLEMENT_FALLOFF_KM,
        score_at_zero=SETTLEMENT_SCORE_AT_ZERO,
        floor=SETTLEMENT_FLOOR,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Human-readable description of how each criterion is scored (for the UI/report)
# ─────────────────────────────────────────────────────────────────────────────

CRITERION_METHOD = {
    "slope": "Cost criterion · interpolated ramp in degrees (0°=1.00, 3°=0.85, 10°=0.42, >25°=0.05)",
    "rainfall": "Benefit criterion · continuous percentile rank within the district (0.20 … 1.00)",
    "drainage": (
        f"Benefit criterion · drainage density in km/km² on a "
        f"{DRAINAGE_DENSITY_WINDOW_KM:.1f} km moving window, interpolated ramp "
        "(0.00=0.10 … 0.40=0.88 … 0.90=1.00)"
    ),
    "soil": "Categorical · explicit texture-class lookup (Silt Loam best, Silt Clay Loam worst)",
    "lulc": "Categorical · IGBP class lookup (Cropland best; Water/Built-up excluded)",
    "population": (
        f"Moderate-optimal · peak {SETTLEMENT_PEAK_KM[0]}–{SETTLEMENT_PEAK_KM[1]} km "
        f"from a settlement (≥{SETTLEMENT_DENSITY_THRESHOLD:.0f} people/km²)"
    ),
}
