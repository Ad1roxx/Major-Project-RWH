"""Map page: zone statistics, the suitability map, and its agreement line."""
import json

import numpy as np
import streamlit as st

from ahp import ahp_engine
from algorithms import ALGORITHMS, weights_for_algorithm
import criteria as C
from gis_analysis import build_criteria_stack, score_stack
from utils import structures as STR
from utils import ui
from utils.map_renderer import render_map

result = ui.require_result()
active = ui.active()
matrix = active["matrix"]

ui.section("Suitability Map", "map",
           f'<span style="font-size:0.75rem; color:#7d8590;"> · {result.get("algorithm", "")} '
           f'· {st.session_state.get("scenario", "")}</span>')

# ─── Area Statistics ─────────────────────────────────────────────────────────
area_stats = result.get("area_statistics")
if area_stats:
    st.markdown(f'<div class="sidebar-title">{ui.icon("bar_chart")}Suitability Zone Statistics</div>',
                unsafe_allow_html=True)
    total = area_stats.get("total_km2", 0)
    cls = area_stats.get("classes", {})
    cols = st.columns(4)
    with cols[0]:
        st.metric("District analysed", f"{total:,.0f} km²")
    for col, label in zip(cols[1:], ["High", "Medium", "Low"]):
        entry = cls.get(label, {})
        with col:
            st.metric(
                f"{label} suitability",
                f"{entry.get('percent', 0):.1f}%",
                f"{entry.get('area_km2', 0):,.0f} km²",
                delta_color="off",
            )

# ─── Suitability Map ─────────────────────────────────────────────────────────
# Folium gives the page new element ids on every render, so a rebuild reloads the
# iframe. Build only when the result, matrix or scenario changes; changing page
# or using another widget reuses the same page.
matrix_key = tuple(np.round(matrix, 6).ravel())
map_key = (st.session_state.get("result_key"), matrix_key,
           st.session_state.get("scenario"))
map_slot = st.empty()
map_cache = st.session_state.get("_map_cache")
if not map_cache or map_cache["key"] != map_key:
    with map_slot, st.spinner("Building map..."):
        # Top sites of all four algorithms under the current judgements, for the
        # per-algorithm site overlays. Recomputed only when the pairwise matrix
        # changes (≈0.6 s); the overlays start switched off.
        if st.session_state.get("algo_sites_key") != matrix_key:
            stack = build_criteria_stack(ui.DATA_DIR)
            algo_sites = {}
            for name in ALGORITHMS:
                w, agg, _label = weights_for_algorithm(name, matrix, ahp_engine.criteria)
                algo_sites[name] = score_stack(
                    stack, w, aggregator=agg, algorithm=name,
                    extract_sites=False)["top_locations_details"]
            st.session_state["algo_sites"] = algo_sites
            st.session_state["algo_sites_key"] = matrix_key

        # Render map with suitability zones
        map_html = render_map(result, stack=build_criteria_stack(ui.DATA_DIR),
                              site_context=ui.site_contexts(result),
                              algorithm_sites=st.session_state.get("algo_sites"),
                              water_works=STR.load_water_works(),
                              confirmed_structures=STR.load_confirmed())
    map_cache = {"key": map_key, "html": map_html}
    st.session_state["_map_cache"] = map_cache

# ─── A site sent here from the Candidate sites page ──────────────────────────
focus = st.session_state.get("_map_focus")
page_html = map_cache["html"]
if focus:
    # Read by utils/map_panels.js, which marks the site and flies there once.
    page_html = page_html.replace(
        "<head>", f"<head><script>window.RWH_FOCUS = {json.dumps(focus)};</script>", 1)
with map_slot:
    st.components.v1.html(page_html, height=620)
if focus:
    note_col, clear_col = st.columns([5, 1])
    with note_col:
        text = (f"Marked on the map: Rank #{focus['rank']} of {focus['method']} · "
                f"{focus['scenario']}, score {focus['score']:.3f}.")
        if (focus["method"], focus["scenario"]) != (active["algorithm"], active["scenario"]):
            text += (f" The sidebar has since changed to {active['algorithm']} · "
                     f"{active['scenario']}, so the zones and candidate sites may not "
                     f"match this site.")
        st.caption(text)
    with clear_col:
        if st.button("Clear marker", key="map_focus_clear", use_container_width=True):
            del st.session_state["_map_focus"]
            st.rerun()

enrich = ui.works_enrichment(result)
if enrich:
    h = enrich["High"]
    st.caption(
        f"{h['points_pct']:.1f}% of existing MGNREGA water works lie in High zones "
        f"({h['ratio']:.2f}× the area share). These are category codes, not verified "
        f"structures. Agreement with existing practice, not an accuracy measure.")
    st.page_link("views/agreement.py", label="More on agreement with recorded works",
                 icon=":material/fact_check:")

if area_stats:
    ui.muted(
        f"Classes use fixed thresholds on the 0–1 suitability score "
        f"(High ≥ {C.SUITABILITY_THRESHOLDS[1]}, Medium {C.SUITABILITY_THRESHOLDS[0]}–{C.SUITABILITY_THRESHOLDS[1]}, "
        f"Low &lt; {C.SUITABILITY_THRESHOLDS[0]}), computed over pixels inside the district boundary only.")
