# Taluka (sub-district) boundaries — provenance

**Pulled:** 2026-10-20, for the study-area figure (Figure 1) and taluka-level
summaries. Display only: nothing here feeds the suitability model.

**Source:** GitHub `datta07/INDIAN-SHAPEFILES` (MIT licence), folder
`STATES/MAHARASHTRA/`.

- `MAHARASHTRA_SUBDISTRICTS.geojson`
  sha256 `014975245b515b77965942994b54155d2c793d2efb3d2d4f95e4ab53f0ef2b3e`
- `MAHARASHTRA Sub District Hq.geojson`, saved as
  `MAHARASHTRA_Sub_District_Hq.geojson`
  sha256 `b9b1c71bdf83a56a1dc3ac0b54744c6760cbe97ae8daf0aea35396e64e7e9205`

Download URL pattern:
`https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES/master/STATES/MAHARASHTRA/<file>`

**What the data is:** the attributes carry Census 2011 codes (`stcode11`,
`dtcode11`, `sdtcode11`) and Local Government Directory codes (`Subdt_LGD`,
`Dist_LGD`), so these are the Census 2011 sub-district boundaries. The
repository says its boundaries are "primarily 2019"; it does not name the
original publisher. **Cite as:** Census of India 2011 sub-district boundaries,
via datta07/INDIAN-SHAPEFILES.

**Checks (2026-10-20):**
- Chandrapur (Census district 509) has **15 talukas**, matching the official
  list: Ballarpur, Bhadravati, Brahmapuri, Chandrapur, Chimur, Gondpipri,
  Jiwati, Korpana, Mul, Nagbhir, Pombhurna, Rajura, Sawali, Sindewahi, Warora.
  There is one headquarters point per taluka.
- GADM level 3 (`gadm41_IND_3`) has only 10 for Chandrapur, the pre-split
  division, and is not used.
- **Area check, in UTM 44N:**

  | Measure | Area |
  |---|---|
  | Union of the 15 talukas | 11,353.6 km² |
  | Our GADM district outline (`data/boundary.geojson`) | 11,307.3 km² |
  | Overlap | 11,209.5 km² |
  | Symmetric difference | 241.9 km² (about 2%, along the edges) |

  For figures, use the copy clipped to our outline so that taluka lines and the
  analysis agree.

**Files derived here:**

| File | Contents |
|---|---|
| `chandrapur_talukas_census2011.geojson` | The 15 Chandrapur talukas, unclipped |
| `chandrapur_talukas_clipped_to_boundary.geojson` | The same, clipped to `data/boundary.geojson` |
| `chandrapur_taluka_hq.geojson` | The 15 taluka headquarters points (`taluka_hq` name) |
| `chandrapur_talukas_filled_to_boundary.geojson` | **Use this one for figures.** The clipped talukas with the gaps filled, so they tile `data/boundary.geojson` exactly |

**Why the filled version exists (2026-10-20):** clipping removes taluka area
outside our outline but cannot fill strips where our GADM outline reaches
beyond the Census edges. Those strips total 97.8 km² in 64 pieces; the largest
is 10.0 km². Each piece was added to the taluka sharing the longest border with
it; every piece touched one. After filling, nothing is uncovered, no talukas
overlap, and the total equals the boundary's 11,307.3 km² (UTM 44N). Taluka
areas move by at most 31 km² (Brahmapuri). Areas from this file are on our
outline, not the official Census ones.
