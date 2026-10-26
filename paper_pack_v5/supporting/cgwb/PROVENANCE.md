# CGWB aquifer mapping report, Chandrapur — provenance

**Report:** Nelofar, N. K. Nanda and V. Venktesham (2021). *Aquifer Mapping and
Management of Ground Water Resources, Chandrapur District, Maharashtra.*
Central Ground Water Board, Central Region, Nagpur (NAQUIM series).

- **Page:** https://cgwb.gov.in/cgwbpnm/publication-detail/209
- **Download:** https://cgwb.gov.in/cgwbpnm/download/209
- **Downloaded:** 2026-10-20
- **File:** `chandrapur_naquim_2021.pdf`, 356 pages, sha256
  `d8c7271a95382e00869fa49baacb7dfce5fcbffc3fd676fec63560768735e2bf`.
  Git-ignored; re-downloadable from the link above.

## Facts used by the project, as stated in the report

| Item | Value | Where |
|---|---|---|
| District category | **Safe** (Ground Water Resources Estimation 2017) | §1, p. 2; summary §13 |
| Stage of groundwater development | **19.35%** (2017); 16.29% (2004) rising to 19.34% (2017) | summary §13; chart, §7 |
| Annual extractable recharge / extraction | 1,079.21 / 208.81 MCM | summary §13 |
| Pre-monsoon water-level trend 2011–20 | decline over 5,918 km² (52% of area); decline > 0.20 m/yr over 804 km² (7%), in isolated parts of Bhadravati, Chandrapur, Warora, Chimur, Pombhurna; rise over 5,423 km² | §3.3 |
| Post-monsoon trend 2011–20 | rise over 5,870 km²; fall over 5,360 km²; fall > 0.20 m/yr over 472 km² (4%) | §3.3 |
| Rainfall trend | falling, 5.9 mm/yr | §2 |
| Issues listed | declining levels in parts of 4 blocks; fluoride in parts of 7 blocks; about 40% of the area with low-yield aquifers (< 1 lps); "low development of ground water resources" | summary §14 |
| Artificial recharge feasible | **2,613.95 km² in 9 blocks**: Ballarpur, Bhadravati, Brahmapuri, Chandrapur, Chimur, Gondpipri, Korpana, Rajura, Warora | Table 7.1 |
| AR **not** feasible | **Jiwati, Mul, Nagbhir, Pombhurna, Saoli, Sindewahi**: post-monsoon water level < 3 m bgl with rising trend | §7.1, Table 7.1 |
| Proposed structures | 150 percolation tanks, 112 check dams, 156 recharge shafts; expected recharge 32.04 MCM/yr | §7.1, Table 7.2 |

## `cgwb_proposed_ar_sites.csv`

**418 proposed structures** (150 percolation tanks, 112 check dams, 156
recharge shafts, matching the report), parsed from Annexures VII–IX by regular
expression from the PDF text layer. Shaft #94 (Shivanichor) wraps across two
lines in the PDF and was added by hand on 2026-10-20 after the first parse
missed it.

- `lon`, `lat`, `type`: reliable; all 418 fall inside the scored area.
- `taluka`, `village`: **unreliable**. The parser splits multi-word place
  names wrongly. Don't use those two columns.

These are the hydrogeologists' **proposed** sites, chosen where the aquifer
has unsaturated volume to receive recharge. They are not built structures.
