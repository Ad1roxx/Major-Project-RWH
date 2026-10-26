# Data provenance — every dataset, version, licence and citation

All items were checked against files in the repository or the original
downloads on 2026-10-20 unless marked otherwise.

## Model inputs (unchanged since v4)

| Criterion | Dataset, version | Resolution | How verified | Cite |
|---|---|---|---|---|
| Boundary / mask | GADM 4.1, India level 2 (Chandrapur, `GID_2` IND.20.8_1) | vector | `data/boundary.geojson` attributes | GADM (gadm.org), v4.1 |
| Rainfall | CHIRPS v3.0 annual, 2014–2024 (11 years) | 0.05° (~5.3 km) | the 11 files `chirps-v3.0.2014…2024.tif`; `build_rainfall.py` | Funk et al. (CHIRPS); state v3.0 |
| Slope | HydroSHEDS 3″ conditioned DEM (tiles `n10e070_con`, `n20e070_con`) → GDAL Slope (degrees, Horn) | ~90 m | the QGIS processing history (merge, clip, slope; 22 Apr 2026) | Lehner et al. 2008 (HydroSHEDS) |
| Soil texture | ISRIC SoilGrids250m `TEXMHT_M_sl1`, released 2017-03-10 | 250 m | the `LEGEND` tag of the original download | Hengl et al. 2017, doi:10.1371/journal.pone.0169748 |
| Land cover | **MODIS MCD12Q1 v6.1 (collection 061), 2024 product**, IGBP `LC_Type1`, via NASA AppEEARS | 500 m | the original download `MCD12Q1.061_LC_Type1_doy2024001000000_aid0001.tif` is identical, cell for cell, to `data/lulc.tif` (**found 2026-10-20**) | Friedl & Sulla-Menashe (2022), MCD12Q1 v061, doi:10.5067/MODIS/MCD12Q1.061 |
| Population / settlement | WorldPop India 2020 population density | ~1 km | QGIS history (clip of `ind_pd_2020_1km.tif`) | WorldPop (Tatem 2017) |
| Drainage | HydroRIVERS v1.0, Asia | vector | `data/rivers.geojson` | Lehner & Grill 2013 |

Soil scoring sources (already in v4): USDA TR-55, Appendix A (texture-based
hydrologic soil groups); FAO Training Manual No. 5, *Irrigation Methods*,
Annex 2, Table 7 (basic infiltration rates), Brouwer et al., FAO 1988.

## New since v4: figure layers (display only, none feeds the model)

| Use | Dataset | Licence | Cite |
|---|---|---|---|
| Fig 1 (a): India outline | Survey of India official boundary, dissolved, via DataMeet `maps/Country/india-soi.geojson` | CC BY-SA 2.5 / ODbL | "Survey of India, via DataMeet". The official outline is used because maps of India published from India must show it; **GADM's India outline is not used** |
| Fig 1 (b): Maharashtra and districts | GADM 4.1 levels 1–2 | GADM licence | GADM v4.1 |
| Fig 1 (d), Fig val map: 15 talukas + headquarters | Census of India 2011 sub-district boundaries, via GitHub `datta07/INDIAN-SHAPEFILES` | MIT (repository) | **Cite both:** Census of India 2011, and the repository. GADM level 3 has only 10 talukas (the pre-split division) and is not used |
| Fig 1 (d): river names | OpenStreetMap, Overpass API query of 2026-10-20 | ODbL | © OpenStreetMap contributors |

Taluka geometry: the 15 Census polygons are clipped to the GADM outline, and
64 sliver gaps (97.8 km²) are filled into the neighbouring taluka. **Use
official Census areas, not these, if taluka areas are quoted.** Details in
`data/raw/talukas/PROVENANCE.md`.

## New since v4: validation data

| Item | Detail |
|---|---|
| Source | NRSC Bhuvan Bhugram, "Accepted Geotags" report, https://bhuvan-app2.nrsc.gov.in/bhugram/bhugram_dashboard/, no login |
| Pulled | 2026-10-04 by `tools/pull_mgnrega.py`: 15 blocks × stages 0 and 3, 30 requests, all HTTP 200 |
| Filters on the portal | state 18, district 1829, each block; stage 0 (Phase I: assets, works before 1 Nov 2017, tagged retrospectively) and 3 (Phase II: geotag at completion); category All; financial year All; accuracy 0; dates 1998-09-30 to 2026-10-04 |
| Rows | stage 0: 38,815; stage 3: 43,474; total 82,289 |
| Files | `data/raw/mgnrega/stage{0,3}/<block>.json`, kept byte for byte; parsed to `data/interim/mgnrega_all.parquet` |
| Category information | Only the workcode's second segment (WC, WH, RS, IF …). No asset-type and no status field |
| Personal data | The raw files carry an observer name. It is **excluded** from every processed file, figure and table |
| Photo audit | 240 blinded photos, 30 per segment, two labellers, protocol in `supporting/PHOTO_LABELLING_PROTOCOL.md`. Photos stay out of the repository (they may show people) |

## New since v4: groundwater reference

| Item | Detail |
|---|---|
| Source | Nelofar, N. K. Nanda & V. Venktesham (2021). *Aquifer Mapping and Management of Ground Water Resources, Chandrapur District, Maharashtra*. CGWB (NAQUIM), Central Region, Nagpur. https://cgwb.gov.in/cgwbpnm/publication-detail/209 |
| Used for | District category (Safe, 19.35%, 2017 estimation), water-level trends, recharge feasibility by block, and the 418 proposed recharge structures compared with the model |
| Files | `supporting/cgwb/PROVENANCE.md` (facts and where in the report), `supporting/cgwb/cgwb_proposed_ar_sites.csv` (coordinates parsed from Annexures VII–IX) |

| Current status | GSDA & CGWB (2024). *Report on the Dynamic Groundwater Resources of Maharashtra 2023*. GSDA, Pune. All 15 Chandrapur blocks Safe; district 29.3% (computed). `supporting/gsda/PROVENANCE.md` |

## Reference list entries settled 2026-10-20

- **MODIS:** Friedl, M. & Sulla-Menashe, D. (2022). *MODIS/Terra+Aqua Land
  Cover Type Yearly L3 Global 500m SIN Grid V061* [Dataset]. NASA Land
  Processes DAAC. https://doi.org/10.5067/MODIS/MCD12Q1.061
- **CGWB:** as above.

## Still to confirm before submission

- The target journal, which sets the figure text minimum.
