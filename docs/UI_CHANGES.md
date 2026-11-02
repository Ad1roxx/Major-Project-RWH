# What moved where in the UI overhaul

The app was one long page. It now has five pages, listed in the sidebar, which also
holds the scenario, algorithm, matrix editor and Run button on every page.
`docs/UI_INVENTORY.md` tracks every element individually.

## Where things are now

| You're looking for | Now on |
|---|---|
| Scenario, algorithm, weights, consistency ratio, Run button | Sidebar, every page |
| Pairwise matrix editor | Dialog, from "Edit pairwise matrix" in the sidebar |
| Data file status | One line in the sidebar; all 8 files on Method |
| Zone statistics and the map | Map |
| Ideal sites and Site A vs Site B | Candidate sites |
| Downloads (sites, GeoTIFF, map) | Method, linked from Candidate sites |
| Sensitivity, consensus, algorithm comparison | Robustness, one tab each |
| Agreement with MGNREGA works, and its caveats | Agreement with recorded works; one line under the map |
| AHP weights, scoring rules, notes, all scenario and algorithm descriptions | Method |

## Phase 3 changes

- **Site cards:** rank, score and a criteria count ("6/6 criteria") on the title line,
  then coordinates. Criteria percentages, raw values and farmland, river and works
  context are in a "Details" expander, closed by default. Rank 1 has a blue edge.
- **Bhuvan photo links:** now small buttons on the card. All three stay.
- **Site A vs Site B:** the score difference comes first. Every earlier number stays.
  Under TOPSIS, a note says the "+" figures don't add up to the site's score.
- **Agreement page:** caveats first, in an info box. The three statistics follow as
  labelled metrics.
- **Photo audit range:** "17–49%" is now "17–50%" (16.7% strict, up to 50.0% lenient).
- **The paper's 1.93×:** on the Agreement page, the baseline AHP + WLC view with an
  unedited matrix also says the live figure uses all works and the paper's uses 3,119
  thinned works. The count of all works is live. Other views don't show the sentence,
  because the paper's figure doesn't describe them.
- **Narrow screens:** at 900 and 390 px nothing overflows and map panels start
  collapsed. Metric values shrink below 1100 px so they aren't cut off. The sidebar
  starts closed on a phone, and the comparison stays side by side there.

## Added beyond the original brief

- Candidate sites can list any method and scenario without changing the sidebar.
- "View on map" moves the sidebar to the site's combination and marks the site. It
  drops an edited matrix if the site came from another combination.
- Robustness results show what they were computed for, and warn when out of date.

## What didn't change

No model code, weights, thresholds or scores. Apart from "17–50%", the comparison
against `main` found every earlier metric, table, warning and printed number in all
24 states tested. The score difference and the criteria count are worked out on the
page from values already shown.

Screenshots: `docs/ui_after/phase3/`.
