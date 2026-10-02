# Project Progress Update

**Project:** Suitability Analysis for Rainwater Harvesting Site Planning Using GIS
**Study area:** Chandrapur District, Maharashtra
**Group 11** — Yesha Palan, Akshay Khandor, Aditya Dubey, Arya Chimurkar
**Guide:** Mr. Chirag Ramesh Desai · **Date:** 4 August 2026

---

## Status

The system runs end to end in about 1.5 seconds and produces a suitability map
(High / Medium / Low), 25 ranked candidate sites with coordinates, and a
per-factor explanation for each site. As a cross-check, it measures the district
area as 11,412 sq. km against the official 11,443 — a 99.7% match.

---

## What we fixed

**1. Scoring method.** Our old method stretched each layer between its lowest
and highest value. In practice this broke down: one steep hill made **97% of the
district score above 0.90 on slope**, and Chandrapur city did the same to
population — so two factors carrying a quarter of the total weight had almost no
effect. Worse, soil and land cover were scored by their category *code numbers*,
so **water bodies ranked as the best possible land and forest as the worst**.
About half our decision weight was flat or backwards.

Replaced with proper scoring tables, where every class and range has a score
justified by published research. Scores are now reproducible and could be
applied to another district.

**2. Rainfall data.** We were using a single test month. Now using **11 years of
CHIRPS annual data (2014–2024)**, averaged automatically by a small program so
the layer can be rebuilt at any time. *Finding:* our 11-year average is
**1,493 mm**, ~20% above the 1,245 mm normally quoted for Chandrapur. We
verified this is not an error — the last decade has genuinely been wetter.

**3. Drainage factor.** Our documentation and all reviewed papers specify
**drainage density**, but the code was calculating **distance to the nearest
river** — a different thing. Corrected to true density (river length within
2.5 km of each location; district average 0.242 km/sq. km). This also improved
ranking quality: locations tied at the top score dropped from ~3,000 to 973.

**4. New maps.** Added drainage density, Curve Number and runoff maps. Note that
the standard runoff method is designed for a single storm, not a yearly total —
with the annual figure, forest and built-up land gave nearly identical results,
so we calculate runoff for a 100 mm design storm instead.

---

## Current results

| Suitability class | Share | Area |
|---|---|---|
| **High** | 25.6% | 2,922 sq. km |
| **Medium** | 45.0% | 5,134 sq. km |
| **Low** | 29.4% | 3,357 sq. km |

Our 25.6% sits within the 19–34% range reported by comparable studies in our
literature review.

We also changed how classes are defined. Splitting by percentile always yields
about 33% High regardless of the data, so that number was a product of the
method rather than a finding. Fixed score thresholds now make it a real result.

AHP weights are unchanged — rainfall 0.428, slope 0.225, soil 0.154, drainage
0.093, land cover 0.060, settlement proximity 0.040 — with a Consistency Ratio
of **0.0235**, well below the 0.10 limit.

---

## Scope change

We have removed the natural-language query feature. It was never connected to
the working system and added complexity without strengthening the core
contribution. Four AI/GIS papers in our literature review will be replaced with
four more rainwater-harvesting studies, making the review more focused.

---

## Points we would like your guidance on

1. **Population factor** — we interpret this as *distance from a settlement*,
   best at 1–5 km. Is this interpretation and range appropriate?
2. **Drainage direction** — we treat higher density as better. Some
   recharge-focused studies assume the opposite.
3. **Design storm** — our runoff map uses 100 mm for one day. Is there a
   standard figure for Chandrapur we should use?
4. **Validation data** — where can we obtain records of existing rainwater
   harvesting structures in the district?

---

## Next steps

Add export options (spreadsheet, GIS files, images); allow AHP weights to be
adjusted in the application; run a sensitivity analysis showing how much the
rankings shift when weights are varied, which addresses the criticism that AHP
weights are subjective.

After that: validate against known existing structures and calculate an accuracy
score, then compare our method against an alternative technique such as
Fuzzy-AHP or TOPSIS.

All work is recorded alongside the code in a methodology document, a dated
change log, and a task list of pending work.
