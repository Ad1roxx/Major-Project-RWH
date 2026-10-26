# Soil Texture Legend — Verification Result

**Resolved 2 October 2026.** The open item flagged in `criteria.py`,
`docs/METHODOLOGY.md` §3 and `TODO.md` §A2 has been settled.

**Outcome: the legend in `criteria.py` is wrong.** Three of the four class codes
present in the district are mapped to the wrong soil texture, and the error
systematically over-scores ~96% of the study area.

**Applied 2 October 2026** across `criteria.py`, `derived_maps.py`,
`docs/METHODOLOGY.md` and `tools/paper_figures.py`. All figures regenerated.
See §5b for measured outcomes and `CHANGELOG.md` 2026-10-02.

---

## 1. Where the data came from — now fully established

The original download survives at
`Documents/Major Project Research Papers/Chandrapur_SoilTexture.tif` and retains
its complete SoilGrids metadata, which the QGIS re-export stripped.

| Field | Value |
|---|---|
| Producer | ISRIC — World Soil Information |
| Series | SoilGrids250m |
| Product | `TEXMHT_M_sl1` |
| Title | Texture class (USDA system) at depth 0.00 m |
| Depth | 0.00 m (`sl1`) |
| Published | 2017-03-10 |
| Source file | `TEXMHT_M_sl1_250m_ll.tif` |
| Citation DOI | `10.1371/journal.pone.0169748` |
| Contact | tom.hengl@isric.org |
| NoData | 255 |
| Value domain | 0–12 |

That DOI is Hengl et al. (2017), the SoilGrids250m paper — **use it as the
citation in the references list**, which currently names only "SoilGrids 250 m".

## 2. The legend, read verbatim from the file

The original carries this as a metadata tag:

```
LEGEND=255:NODATA, 1:Cl, 2:SiCl, 3:SaCl, 4:ClLo, 5:SiClLo, 6:SaClLo,
       7:Lo, 8:SiLo, 9:SaLo, 10:Si, 11:LoSa, 12:Sa
```

| Code | Texture | Code | Texture |
|---|---|---|---|
| 1 | Clay | 7 | Loam |
| 2 | Silty Clay | 8 | Silt Loam |
| 3 | Sandy Clay | 9 | Sandy Loam |
| 4 | Clay Loam | 10 | Silt |
| 5 | Silty Clay Loam | 11 | Loamy Sand |
| 6 | Sandy Clay Loam | 12 | Sand |

This is the standard USDA ordering that the warning in `criteria.py` anticipated.
**The warning was correct and the standard coding does apply.**

## 3. The mismatch

| Code | Assumed in `criteria.py` | Score | **Actual texture** | Status | District share |
|---|---|---|---|---|---|
| 1 | Sand | 0.55 | **Clay** | ❌ wrong | 18.61% |
| 4 | Silt Loam | **1.00** | **Clay Loam** | ❌ wrong | **77.82%** |
| 6 | Sandy Clay Loam | 0.80 | Sandy Clay Loam | ✅ correct | 3.19% |
| 7 | Silt Clay Loam | 0.50 | **Loam** | ❌ wrong | 0.38% |

Two of the three errors are consequential in opposite directions:

- **Code 4 — 77.8% of the district.** Scored **1.00**, the maximum, on the
  assumption it was Silt Loam. It is **Clay Loam**, which has moderate-to-poor
  infiltration. By the project's own stated reasoning — *"clay-rich texture
  impedes the recharge the project exists to promote"* — this class should score
  near the middle, not at the top.
- **Code 7 — Loam.** Scored **0.50** on the assumption it was Silty Clay Loam.
  Loam is arguably the single best texture for the stated objective: good
  infiltration with real retention and stable embankment material. It is being
  penalised as one of the worst.
- **Code 1 — 18.6% of the district.** Scored 0.55 as Sand. It is **Clay**, the
  poorest texture for recharge, and currently out-scores the Loam class.

Together, codes 1 and 4 cover **96.4% of the district**.

Note also: the original raster contains a single pixel of code 3 (Sandy Clay)
that is lost during reprojection to EPSG:32644. Immaterial, but it explains the
small difference in valid-pixel percentage between the two files (63.91% vs
62.68%).

## 4. Impact — measured, not estimated

A corrected lookup was applied **without modifying any project file**, using the
same reasoning already documented in `docs/METHODOLOGY.md` §3: recharge needs
infiltration *and* retention/stability; sand infiltrates fastest but retains
nothing; clay impedes recharge.

Proposed table, covering all 12 classes so it transfers:

| Code | Texture | Proposed | Code | Texture | Proposed |
|---|---|---|---|---|---|
| 1 | Clay | 0.25 | 7 | Loam | **1.00** |
| 2 | Silty Clay | 0.30 | 8 | Silt Loam | 0.95 |
| 3 | Sandy Clay | 0.40 | 9 | Sandy Loam | 0.85 |
| 4 | Clay Loam | 0.60 | 10 | Silt | 0.60 |
| 5 | Silty Clay Loam | 0.55 | 11 | Loamy Sand | 0.70 |
| 6 | Sandy Clay Loam | 0.80 | 12 | Sand | 0.55 |

### Result

| | Current (wrong legend) | Corrected legend |
|---|---|---|
| **High suitability** | **18.51% — 2,112.6 km²** | **6.44% — 735.0 km²** |
| Medium | 54.79% | 52.48% |
| Low | 26.70% | 41.08% |
| Mean composite score | 0.7294 | 0.6733 |
| Mean soil criterion score | 0.9080 | 0.5428 |
| **Top-10 sites retained** | — | **2 / 10** |
| **Top-25 sites retained** | — | **12 / 25** |

**The headline result changes substantially.** Highly-suitable area falls by
roughly two thirds, and eight of the ten leading candidate sites are displaced.

⚠ **The magnitude depends on the replacement scores, which are a judgement
call.** A different defensible table would give a different number. What is
*not* a judgement call is the direction: the dominant class is a clay loam, not
a silt loam, so the soil criterion has been systematically over-scoring almost
the entire district.

## 5. A second-order effect worth noting

Under the current legend, all 25 candidate sites sit on code 4 — 77.8% of the
district — and the paper discusses this as shortlist concentration arising from
compensatory aggregation plus the dominance of one well-scoring class.

Under the corrected legend the top sites move onto **code 7 (Loam), which is
0.38% of the district**. The concentration problem does not disappear; it
inverts. That is arguably a *better* result — the model is now selecting a
genuinely scarce and favourable soil rather than the most common one — but the
discussion in the paper would need rewriting either way.

## 5b. Confirmed after application — 2 October 2026

The correction was applied. Measured outcomes beyond those projected in §4:

- **Smoke test 11/11 passing**, including rank ordering.
- **The shortlist diversified.** The 25 sites now span three soil textures —
  Clay Loam 10, Loam 9, Sandy Clay Loam 6 — and two land covers (24 Cropland,
  1 Grassland). Soil score sd across sites rose from **0.0000 to 0.1742**.
- **The headline algorithm finding changed in character.** On class area,
  WLC→TOPSIS now moves 0.79 pp against AHP→Fuzzy-AHP's 0.40 pp — a ratio of
  about 2× where it was 26×. On ranking it is cleaner: TOPSIS retains **5/10**
  of the baseline shortlist, Fuzzy-AHP + WLC retains **10/10**. Class agreement
  87.2% vs 99.0%. The claim should be restated on ranking, not area.
- **Sensitivity:** ±20% retains 88% of the top 10 (60% worst case); the most
  influential criterion is now **soil** (1.42 pp), not drainage.
- **Map removal:** removing rainfall now retains **0/10** sites; drainage 3/10,
  soil 4/10, slope 5/10, population 5/10, land cover 9/10.
- **Effective weights:** soil flipped from over-contributing (1.260) to
  under-contributing (**0.812**); slope rose to **1.404**.
- **Consensus:** 35 distinct locations with 15 unanimous across algorithms
  (4/4 High **528.5 km²**); across scenarios only **2 of 61** are unanimous,
  down from 7 of 54.
- **The §9 dispersion claim survives.** Weighted dispersion inside the
  high-suitability zone still orders the criteria the same way map-removal
  retention does.

---

## 6. What needs to change if the correction is adopted

1. **`criteria.py`** — `SOIL_TEXTURE_SCORES` and `SOIL_TEXTURE_LABELS`. The
   labels drive the per-site explainability output, which currently mislabels
   every site's soil class in the UI, the CSV export and the paper's site table.
2. **`derived_maps.py`** — `HSG_FROM_SOIL` maps soil codes to hydrologic soil
   groups (1→A, 4→B, 6→C, 7→D). Under the real legend this is also wrong: Clay
   should be group D, not A. Curve Number and both runoff surfaces are affected.
3. **`docs/METHODOLOGY.md` §3** — the table and the warning.
4. **Every reported result.** Area statistics, the 25 sites, the algorithm
   comparison, sensitivity, consensus, the resume brief, the slide deck, and all
   of `docs/PAPER_DATA_HANDOFF.md`. `tools/paper_figures.py` regenerates most of it in
   one run.
5. **References** — cite Hengl et al. 2017, DOI `10.1371/journal.pone.0169748`.

## 7. Reproducing this finding

```bash
python tools/inspect.py "C:/Users/Aditya Dubey/Documents/Major Project Research Papers/Chandrapur_SoilTexture.tif"
```

Or read the tag directly:

```python
import rasterio
with rasterio.open("Chandrapur_SoilTexture.tif") as s:
    print(s.tags()["LEGEND"])
```

The impact figures in §4 were computed by substituting the corrected lookup into
the criteria stack at run time. That script is in the session scratchpad; say the
word and it becomes `tools/soil_legend_check.py`.
