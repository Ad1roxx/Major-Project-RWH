# UI inventory

Every interactive element and output of the Streamlit app, written **before** the
overhaul touched any code, from `main` at `b551358`. Each phase adds a column
giving the element's new location. Nothing may be missing at the end of a phase.

"Same" means the element stays where it was. Restyling doesn't count as moving.

## Sidebar

| # | Element | Before | After phase 1 |
|---|---|---|---|
| 1 | Data Status heading and 8 file rows (tick or cross, red if missing) | Sidebar | Same, with Material icons |
| 2 | Scenario dropdown, key `scenario` | Sidebar | Same |
| 3 | Scenario rationale caption | Sidebar | Same |
| 4 | Priorities line and weights table, arrows against the baseline | Sidebar | Same |
| 5 | Fertile farmland extra note | Sidebar | Same |
| 6 | Pairwise matrix editor, key `matrix_editor_<scenario>`, with help caption | Sidebar expander | Dialog opened by the sidebar button "Edit pairwise matrix" |
| 7 | Reciprocal rebuild of the lower triangle | On every edit | Same code, on Apply and in the dialog's CR preview |
| 8 | Algorithm dropdown, key `algorithm` | Sidebar | Same |
| 9 | Algorithm note caption | Sidebar | Same |
| 10 | Consistency Ratio message (green, or red with warning) | Sidebar | Same; also previewed in the dialog |
| 11 | Live weights list | Sidebar | Same, human labels |
| 12 | About text | Sidebar | Same |
| 13 | Collapse and expand of the sidebar | Streamlit | Same |

## Main page

| # | Element | Before | After phase 1 |
|---|---|---|---|
| 14 | Title and subtitle | Top | Same, Material icon |
| 15 | "Run Analysis" heading and Run Suitability Analysis button | Top | Same |
| 16 | Spinners: "Running AHP multi-criteria analysis…", "Re-scoring with the new weights…" | Under Run | Same |
| 17 | Provisional rainfall warning, when the source note is set | Under Run | Same, Material icon |
| 18 | Suitability Map heading with algorithm and scenario | Results | Same |
| 19 | The map (iframe, 640 px) | Results | Same, plus "Building map..." placeholder while it builds |
| 20 | Works agreement caption, live numbers | Under map | Same, wording unchanged |
| 21 | Zone statistics heading, 4 metrics, threshold note | Results | Same |
| 22 | Ideal RWH Sites: 10 cards (rank, score, coordinates, criteria, raw values) | Results | Same, human labels |
| 23 | Farmland context on cards: works, confirmed, river distances, cropland, 3 Bhuvan links | Cards | Same |
| 24 | "No ideal sites extracted" message | Results | Same |
| 25 | Compare: Site A and Site B dropdowns, keys `compare_site_a`, `compare_site_b` | Results | Same |
| 26 | Compare: summary cards with arrows, help line, per-criterion table | Results | Same, human labels |
| 27 | Export note and 4 downloads: Sites (CSV), Sites (GeoJSON), Suitability (GeoTIFF), Map (PNG) | Results | Same |
| 28 | Sensitivity: heading, help line, "Vary weights by" slider, Run sensitivity button | Results | Same |
| 29 | Sensitivity: 3 metrics, summary sentence, one-way table, influence caption | Results | Same, human labels |
| 30 | Map removal title, caption, table | Results | Same, human labels |
| 31 | Single-parameter title, caption, table | Results | Same, human labels |
| 32 | Consensus: heading, help line, Vary radio (key `consensus_axis`) with help, Compute button | Results | Same |
| 33 | Consensus: 3 metrics, variants caption, table, Borda caption | Results | Same |
| 34 | Agreement map image, 2 downloads (CSV, PNG) | Results | Same |
| 35 | Algorithm comparison: heading, help line, Compare button | Results | Same |
| 36 | Comparison table, caption, "Weights by algorithm" table | Results | Same, human labels |
| 37 | Notes list | Results | Same, Material icons |
| 38 | AHP Weights expander (table, CR verdict, "Weights not available") | Results | Same, human labels |
| 39 | How each criterion is scored expander ("Scoring metadata not available") | Results | Same, human labels |
| 40 | "Analysis failed" error with its notes | After Run | Same |

Tables keep Streamlit's built-in sort, search, download and fullscreen tools.

## Map

| # | Element | Before | After phase 1 |
|---|---|---|---|
| 41 | Zoom buttons, scroll and drag zoom, scale bar, attribution | Map | Same |
| 42 | Measure tool | Top left | Same |
| 43 | Minimap with toggle | Bottom right | Same |
| 44 | Basemap radios: Dark grey (Esri), OpenStreetMap | Layer box | Same, under a heading |
| 45 | Overlays: Boundary, Rivers / Drainage | Layer box | Same, under "Base data" |
| 46 | Overlay: High Suitability Zones | Layer box | Same, under "Suitability" |
| 47 | Overlays: Top Candidate Sites, Sites for each of 4 algorithms, Candidate site with a work within 600 m | Layer box | Same, under "Candidate sites" |
| 48 | Overlays: MGNREGA water works, Photo-confirmed structures | Layer box | Same, under "MGNREGA works"; works now start off |
| 49 | Data layer panel: grouped dropdown (12 layers plus None), model score checkbox, opacity slider, hint | Top right | Same, collapsible |
| 50 | Dynamic legend for the selected data layer | Bottom right | Bottom centre, clear of the panel stack |
| 51 | Click-to-read popup, with highlighted row and outside, no-data and old-browser messages | Map | Same |
| 52 | Candidate site tooltip and popup, including the farmland block | Map | Same, human labels |
| 53 | Algorithm ring tooltips | Map | Same |
| 54 | Works clusters (WC and WH colours), popup with Bhuvan link | Map | Same |
| 55 | Confirmed structure tooltip and popup, strict ones with a photo | Map | Same |
| 56 | Gold star tooltip | Map | Same |
| 57 | River tooltip | Map | Same |
| 58 | Main legend: symbols, ring key, works statistics, CR, top factor | Bottom left | Same, collapsible |
| 59 | Map title | Top centre, clipped | Top left, unclipped |

## Session-state keys that must keep their meaning

Results: `analysis_result`, `result_key`, `algo_sites`, `algo_sites_key`,
`sensitivity`, `map_removal`, `single_param`, `consensus`, `algo_comparison`.

Widgets: `scenario`, `algorithm`, `compare_site_a`, `compare_site_b`,
`consensus_axis`, `matrix_editor_<scenario>`.

Added in phase 1: `_matrix_applied` (the applied matrix and its scenario, since the
editor's own state is cleared when the dialog closes) and `_map_cache` (the built
map and its site context).
