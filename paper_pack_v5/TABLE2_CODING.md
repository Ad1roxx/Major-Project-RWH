# Table 2 — criteria used by the eight reviewed studies (checked against the papers)

Checked on 2026-10-20 against the full text of each paper, from the PDFs in
`Documents/Major Project Research Papers/` (the "Attach now" folder). The
coding is **strict**: ✓ only if the criterion is an explicit input layer
(weighted or used as a constraint) in the paper's own model. Partial uses
are marked with their form.

| Study | Rainfall | Slope | Soil | Land cover | Drainage | Settlement / proximity | Other layers used |
|---|---|---|---|---|---|---|---|
| Seif et al. 2024 (Egypt, MAR) | ✓ precipitation | ✓ | ~ infiltration rate (not texture) | ✓ | ✓ drainage density | ✗ | vertical permeability, unsaturated and saturated thickness, flow accumulation, salinity; geology as constraint |
| Mustapha et al. (Moulouya, Morocco) | ✓ | ✓ | ✗ (lithology, permeability instead) | ✓ | ✓ drainage density | ✗ | lithology, runoff coefficient, surface runoff, recharge, evapotranspiration |
| Al-Hasani et al. 2023 (Kirkuk, Iraq) | ✓ historical + future | ✓ | ✓ texture + HSG | ✓ | ✓ drainage density | ✗ | surface runoff potential |
| Haziq & Ibrahimi 2022 (Kandahar) | **✗** | ✓ | ✓ texture | ✓ | ~ "line density" / stream order | ✗ | lithology |
| Resen et al. (Wadi Sarkhar, Iraq) | ✓ | ✓ | ✓ type | ✓ | ~ stream orders 5–7 (not density) | **✓** population places, roads | runoff, evaporation |
| Fetene et al. 2026 (Awi Zone, Ethiopia) | ✓ | ✓ | ✓ texture | ✓ | ✓ drainage density | ✗ | — (five biophysical layers only) |
| Alene et al. 2022 (Wag Himra, Ethiopia) | ~ only via SCS-CN runoff depth | ✓ | ✓ texture (**clay scored most suitable**) | ✓ | ✓ drainage density | ~ road and town as constraints | runoff depth |
| Adham et al. (Western Desert, Iraq) | ~ only via runoff depth | ✓ | ✓ texture | ✓ | ~ stream order | ✗ ("did not include socioeconomic criteria") | runoff depth |

**Counts, strict / including partial:**

| Criterion | Explicit layer | Including partial forms |
|---|---|---|
| Slope | **8 / 8** | 8 / 8 |
| Land cover | **8 / 8** | 8 / 8 |
| Soil | 6 / 8 | 7 / 8 (Seif's infiltration rate) |
| Rainfall | **5 / 8** | 7 / 8 (Alene and Adham via runoff; Haziq none) |
| Drainage | 5 / 8 as density | 8 / 8 as any stream-network measure |
| Settlement | **1 / 8** (Resen) | 2 / 8 (Alene, as a constraint) |

## What to change in the paper

- **Any claim that rainfall appears in all eight studies is false.** Five
  use it as a layer, two only through runoff depth, and one (Haziq) not at
  all. Also false: "five of our six criteria appear in all eight". Only
  slope and land cover are universal.
- **Defensible sentence:**
  > Slope and land cover appear in all eight studies; soil in seven, rainfall
  > in seven (two of them only through modelled runoff depth), and a
  > stream-network measure in all eight (drainage density in five). Proximity
  > to settlement appears in only two, one of them as a constraint, which is
  > why its inclusion here is justified separately on demand grounds.
- **Settlement proximity is the project's least-supported criterion in the
  literature.** It is also the least influential: weight 0.040, and removing
  it changes the validation AUC by 0.004 at most. That supports keeping it as
  a minor, demand-side criterion.
- **Alene et al. score clay as most suitable** (a storage logic), the
  opposite of our soil ordering. Cite it where the storage/recharge
  distinction is discussed: published RWH studies differ on the direction
  of the soil criterion, which supports stating the objective explicitly.

Keep this file with the submission materials. A reviewer may spot-check
Table 2 against any of these papers.
