# UI inventory

Every interactive element and output of the Streamlit app, written **before** the
overhaul touched any code, from `main` at `b551358`. Each phase adds a column
giving the element's new location. Nothing may be missing at the end of a phase.

"Same" means the element stays where it was. Restyling doesn't count as moving.

## Sidebar

| # | Element | Before | After phase 1 | After phase 2 | After phase 3 |
|---|---|---|---|---|---|
| 1 | Data Status heading and 8 file rows (tick or cross, red if missing) | Sidebar | Same, with Material icons | Method page, all 8 rows; sidebar keeps a one-line count with a link | Same |
| 2 | Scenario dropdown, key `scenario` | Sidebar | Same | Sidebar | Same |
| 3 | Scenario rationale caption | Sidebar | Same | Sidebar; all five also listed on Method | Same |
| 4 | Priorities line and weights table, arrows against the baseline | Sidebar | Same | Sidebar | Same |
| 5 | Fertile farmland extra note | Sidebar | Same | Sidebar | Same |
| 6 | Pairwise matrix editor, key `matrix_editor_<scenario>`, with help caption | Sidebar expander | Dialog opened by the sidebar button "Edit pairwise matrix" | Dialog from the sidebar, on every page | Same |
| 7 | Reciprocal rebuild of the lower triangle | On every edit | Same code, on Apply and in the dialog's CR preview | Same | Same |
| 8 | Algorithm dropdown, key `algorithm` | Sidebar | Same | Sidebar | Same |
| 9 | Algorithm note caption | Sidebar | Same | Sidebar; all four also listed on Method | Same |
| 10 | Consistency Ratio message (green, or red with warning) | Sidebar | Same; also previewed in the dialog | Sidebar and dialog | Same |
| 11 | Live weights list | Sidebar | Same, human labels | Sidebar | Same |
| 12 | About text | Sidebar | Same | Sidebar | Same |
| 13 | Collapse and expand of the sidebar | Streamlit | Same | Same | Same; starts closed on a phone |

## Main page

| # | Element | Before | After phase 1 | After phase 2 | After phase 3 |
|---|---|---|---|---|---|
| 14 | Title and subtitle | Top | Same, Material icon | Top of every page | Same |
| 15 | "Run Analysis" heading and Run Suitability Analysis button | Top | Same | Sidebar: "Run Analysis" heading and button, on every page | Same |
| 16 | Spinners: "Running AHP multi-criteria analysis…", "Re-scoring with the new weights…" | Under Run | Same | Main area, on every page | Same |
| 17 | Provisional rainfall warning, when the source note is set | Under Run | Same, Material icon | Top of every page | Same |
| 18 | Suitability Map heading with algorithm and scenario | Results | Same | Map page | Same |
| 19 | The map (iframe, 640 px) | Results | Same, plus "Building map..." placeholder while it builds | Map page, 620 px, built only when the result changes | Same |
| 20 | Works agreement caption, live numbers | Under map | Same, wording unchanged | Agreement page in full; one line with the caveats under the map, with a link | Agreement page: caveats in an info box at the top, statistics as 3 labelled metrics, paper sentence on the baseline view; 17–50%. Map line same |
| 21 | Zone statistics heading, 4 metrics, threshold note | Results | Same | Map page: metrics above the map, threshold note below | Same |
| 22 | Ideal RWH Sites: 10 cards (rank, score, coordinates, criteria, raw values) | Results | Same, human labels | Candidate sites | Candidate sites: title line with a criteria count, coordinates, rest in a Details expander; rank 1 highlighted |
| 23 | Farmland context on cards: works, confirmed, river distances, cropland, 3 Bhuvan links | Cards | Same | Candidate sites | Candidate sites: context in Details; 3 Bhuvan links as small buttons on the card |
| 24 | "No ideal sites extracted" message | Results | Same | Candidate sites | Same |
| 25 | Compare: Site A and Site B dropdowns, keys `compare_site_a`, `compare_site_b` | Results | Same | Candidate sites, values remembered | Same |
| 26 | Compare: summary cards with arrows, help line, per-criterion table | Results | Same, human labels | Candidate sites | Candidate sites: score difference first, then the same cards and table; TOPSIS note |
| 27 | Export note and 4 downloads: Sites (CSV), Sites (GeoJSON), Suitability (GeoTIFF), Map (PNG) | Results | Same | Method page, grouped as Sites and Rasters and maps; linked from Candidate sites | Same |
| 28 | Sensitivity: heading, help line, "Vary weights by" slider, Run sensitivity button | Results | Same | Robustness, Sensitivity tab, slider value remembered | Same |
| 29 | Sensitivity: 3 metrics, summary sentence, one-way table, influence caption | Results | Same, human labels | Robustness, Sensitivity tab | Same |
| 30 | Map removal title, caption, table | Results | Same, human labels | Robustness, Sensitivity tab | Same |
| 31 | Single-parameter title, caption, table | Results | Same, human labels | Robustness, Sensitivity tab | Same |
| 32 | Consensus: heading, help line, Vary radio (key `consensus_axis`) with help, Compute button | Results | Same | Robustness, Consensus tab, axis remembered | Same |
| 33 | Consensus: 3 metrics, variants caption, table, Borda caption | Results | Same | Robustness, Consensus tab | Same |
| 34 | Agreement map image, 2 downloads (CSV, PNG) | Results | Same | Robustness, Consensus tab | Same |
| 35 | Algorithm comparison: heading, help line, Compare button | Results | Same | Robustness, Algorithm comparison tab | Same |
| 36 | Comparison table, caption, "Weights by algorithm" table | Results | Same, human labels | Robustness, Algorithm comparison tab | Same |
| 37 | Notes list | Results | Same, Material icons | Method page | Same |
| 38 | AHP Weights expander (table, CR verdict, "Weights not available") | Results | Same, human labels | Method page | Same |
| 39 | How each criterion is scored expander ("Scoring metadata not available") | Results | Same, human labels | Method page | Same |
| 40 | "Analysis failed" error with its notes | After Run | Same | Top of every page | Same |

Tables keep Streamlit's built-in sort, search, download and fullscreen tools.

## Map

| # | Element | Before | After phase 1 | After phase 2 | After phase 3 |
|---|---|---|---|---|---|
| 41 | Zoom buttons, scroll and drag zoom, scale bar, attribution | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 42 | Measure tool | Top left | Same | Map page; view, layers and data layer restored after changing page | Same |
| 43 | Minimap with toggle | Bottom right | Same | Map page; view, layers and data layer restored after changing page | Same |
| 44 | Basemap radios: Dark grey (Esri), OpenStreetMap | Layer box | Same, under a heading | Map page; view, layers and data layer restored after changing page | Same |
| 45 | Overlays: Boundary, Rivers / Drainage | Layer box | Same, under "Base data" | Map page; view, layers and data layer restored after changing page | Same |
| 46 | Overlay: High Suitability Zones | Layer box | Same, under "Suitability" | Map page; view, layers and data layer restored after changing page | Same |
| 47 | Overlays: Top Candidate Sites, Sites for each of 4 algorithms, Candidate site with a work within 600 m | Layer box | Same, under "Candidate sites" | Map page; view, layers and data layer restored after changing page | Same |
| 48 | Overlays: MGNREGA water works, Photo-confirmed structures | Layer box | Same, under "MGNREGA works"; works now start off | Map page; view, layers and data layer restored after changing page | Same |
| 49 | Data layer panel: grouped dropdown (12 layers plus None), model score checkbox, opacity slider, hint | Top right | Same, collapsible | Map page; view, layers and data layer restored after changing page | Same |
| 50 | Dynamic legend for the selected data layer | Bottom right | Bottom centre, clear of the panel stack | Map page; view, layers and data layer restored after changing page | Same |
| 51 | Click-to-read popup, with highlighted row and outside, no-data and old-browser messages | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 52 | Candidate site tooltip and popup, including the farmland block | Map | Same, human labels | Map page; view, layers and data layer restored after changing page | Same |
| 53 | Algorithm ring tooltips | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 54 | Works clusters (WC and WH colours), popup with Bhuvan link | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 55 | Confirmed structure tooltip and popup, strict ones with a photo | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 56 | Gold star tooltip | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 57 | River tooltip | Map | Same | Map page; view, layers and data layer restored after changing page | Same |
| 58 | Main legend: symbols, ring key, works statistics, CR, top factor | Bottom left | Same, collapsible | Map page; view, layers and data layer restored after changing page | Same |
| 59 | Map title | Top centre, clipped | Top left, unclipped | Map page; view, layers and data layer restored after changing page | Same |

## Added after phase 2

| # | Element | Location |
|---|---|---|
| 60 | "List sites for scenario" and "Using method" dropdowns (keys `sites_scenario`, `sites_method`), rationale, method note, weights with changes against the baseline | Candidate sites |
| 61 | "View on map" on each listed site, marker and popup, note, "Clear marker" button | Candidate sites; Map page |
| 62 | "Computed for" line or "Out of date" warning on each robustness result, WLC and edited-matrix notes | Robustness, all three tabs |

## Session-state keys that must keep their meaning

Results: `analysis_result`, `result_key`, `algo_sites`, `algo_sites_key`,
`sensitivity`, `map_removal`, `single_param`, `consensus`, `algo_comparison`.

Widgets: `scenario`, `algorithm`, `compare_site_a`, `compare_site_b`,
`consensus_axis`, `matrix_editor_<scenario>`.

No keys added in phase 3 beyond the `site_card_<rank>` and `compare_rows` containers, used for styling only.

Added after phase 2: `sites_scenario`, `sites_method`, `_sites_combinations`, `_map_focus`, `_sensitivity_for`, `_consensus_for`, `_consensus_new`, `_comparison_for`.

Added in phase 2: `_active` (what the sidebar chose on this run), `_site_ctx`, `sens_delta`
(the sensitivity slider), and `_keep_<widget>` mirrors for `compare_site_a`,
`compare_site_b`, `consensus_axis` and `sens_delta`.

Added in phase 1: `_matrix_applied` (the applied matrix and its scenario, since the
editor's own state is cleared when the dialog closes) and `_map_cache` (the built
map).
