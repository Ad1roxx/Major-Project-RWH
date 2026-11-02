# UI overhaul plan

The agreed brief for restyling the Streamlit app, in three phases with approval
between each. Work happens on the `ui-overhaul` branch, because `main` is what the
submitted project link shows.

## Hard rules

1. Keep every function, widget, map layer, popup, tooltip, download and caption.
   They can be restyled and moved, not removed.
2. No calculation, threshold, weight, scoring rule or printed number changes. Don't
   edit `gis_analysis`, `ahp`, `algorithms`, `criteria`, `sensitivity`,
   `consensus.py`, `derived_maps.py` or `exports.py` beyond imports. Item 3.4 is the
   one approved wording change.
3. Keep the session-state keys listed in `docs/UI_INVENTORY.md`. Auto re-scoring must
   keep working.
4. Keep the caveat wording verbatim. Never write "validated" or "accurate".
5. Keep `docs/UI_INVENTORY.md` current, with a new location column per phase.

Each phase also runs `tools/smoke_test.py` and an output comparison against `main`:
every metric, table and number shown by the app, and `tools/paper_figures.py`.

## Phase 1: quick wins, single page

- **1.1** Fixed dark theme in `.streamlit/config.toml`, with a neutral accent.
- **1.2** Map panels: collapsible with remembered state, dark layer box, grouped
  overlays, collapsed on first load below 900 px, unclipped title.
- **1.3** Popups clear panels: only panels a popup actually overlaps collapse, and
  they are restored when it closes, so the Data layer panel stays usable beside a
  readout. Popups get auto-pan padding.
- **1.4** MGNREGA works start off, with the toggle kept.
- **1.5** Matrix editor in a large `st.dialog`, with an Apply button that stores the
  matrix for that scenario, because closing a dialog clears the editor's state.
- **1.6** Material icons, and one shared dict of human criterion labels.
- **1.7** "Building map..." placeholder. Needs the map cache from 2.4, otherwise the
  placeholder would reload the map on every rerun.

## Phase 2: five pages with shared state

`st.navigation` with `views/map.py`, `views/sites.py`, `views/robustness.py` (tabs:
Sensitivity, Consensus, Algorithm comparison), `views/agreement.py` and
`views/method.py`. `app.py` owns the sidebar, Run button and scoring.

- Remembered widget values must be checked against the current options before use,
  because the site labels contain scores and change with the scenario.
- The one-line caption under the map must keep "category codes" and "not an accuracy
  measure".
- Decide once where data status, scenario rationale and algorithm descriptions live.
  Make exports easy to find from the sidebar or Candidate sites.
- Text for the Agreement page beyond existing captions needs approval.
- Keep the map at a height that fits a 1280 × 720 window, about 620–640 px.
- Page changes reload the map iframe, so zoom and layers reset unless saved.
- Empty states on every page. Failed-run errors stay visible on every page.
- Optional analyses still run only when their buttons are pressed.

## Phase 3: polish

- **3.1** Site cards: title line, coordinates, details in an expander, photo-link
  buttons, subtle rank 1 highlight.
- **3.2** Site comparison: score difference first, every current number kept.
- **3.3** Agreement page: caveats first, statistics as labelled metric cards.
- **3.4** "17–49%" becomes "17–50%" in `app.py` and `utils/structures.py`. Under the
  High-zone ratio caption, on the baseline AHP + WLC view only, add a sentence
  explaining that the live figure uses all works in the scored area and the paper's
  1.93× uses 3,119 thinned works. Use the live count, not a typed 8,243.
- **3.5** At 900 and 390 px nothing overflows and map panels start collapsed.

## Reporting

At the end of each phase: what changed by file, anything that couldn't be placed,
anything guessed, then stop for approval.
