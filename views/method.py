"""Method page: exports, weights, scoring rules, scenarios, data status, notes.

Scenarios, algorithms and data status don't need a result, so they always show.
"""
import streamlit as st

from ahp import SCENARIOS
from algorithms import ALGORITHMS
import exports
from utils import ui
from utils.labels import criterion_label

result = st.session_state.get("analysis_result")
has_result = bool(result) and result.get("status") == "ok"

if not has_result and not result:
    st.info(ui.EMPTY_MESSAGE, icon=":material/play_circle:")

if has_result:
    weights = result.get("weights", {}) or {}
    consistency_ratio = result.get("consistency_ratio", 0)

    # ─── Downloads ───────────────────────────────────────────────────────────
    ui.section("Export", "download")
    ui.muted("Every file embeds the weights, consistency ratio and classification "
             "thresholds used to produce it.", margin_bottom=8)

    sites_col, rasters_col = st.columns(2)
    with sites_col:
        st.markdown("**Sites**")
        d1, d2 = st.columns(2)
        with d1:
            st.download_button("Sites (CSV)", exports.sites_csv(result),
                               "rwh_sites.csv", "text/csv", use_container_width=True)
        with d2:
            st.download_button("Sites (GeoJSON)", exports.sites_geojson(result),
                               "rwh_sites.geojson", "application/geo+json",
                               use_container_width=True)
    with rasters_col:
        st.markdown("**Rasters and maps**")
        d3, d4 = st.columns(2)
        with d3:
            st.download_button("Suitability (GeoTIFF)", exports.suitability_geotiff(result),
                               "rwh_suitability.tif", "image/tiff",
                               use_container_width=True)
        with d4:
            st.download_button("Map (PNG)", exports.map_png(result),
                               "rwh_suitability_map.png", "image/png",
                               use_container_width=True)

    # ─── Weights and scoring ─────────────────────────────────────────────────
    ui.section("Weights and scoring", "balance")
    with st.expander("AHP Weights", expanded=False):
        if weights:
            weights_html = '<div class="weights-table"><table style="width:100%; border-collapse: collapse;">'
            weights_html += '<tr><th style="text-align:left; padding:4px;">Criterion</th><th style="text-align:right; padding:4px;">Weight</th></tr>'
            for criterion, weight in weights.items():
                weights_html += f'<tr><td style="padding:4px;">{criterion_label(criterion)}</td><td style="text-align:right; padding:4px;">{weight:.3f}</td></tr>'
            weights_html += '</table></div>'
            st.markdown(weights_html, unsafe_allow_html=True)
            cr_verdict = "acceptable (CR < 0.10)" if consistency_ratio < 0.10 else "INCONSISTENT — revise the matrix"
            st.markdown(f"**Consistency Ratio:** {consistency_ratio:.4f} — {cr_verdict}")
        else:
            st.info("Weights not available")

    with st.expander("How each criterion is scored", expanded=False):
        method = result.get("criterion_method", {}) or {}
        if method:
            for criterion in sorted(method, key=lambda c: -float(weights.get(c, 0.0))):
                st.markdown(
                    f"**{criterion_label(criterion)}** (w={float(weights.get(criterion, 0.0)):.3f}) — {method[criterion]}"
                )
            ui.muted("Every criterion is reclassified with fixed, documented breakpoints rather than a "
                     "min–max rescale, so a given slope or soil class always scores the same. "
                     "Full justification in docs/METHODOLOGY.md.")
        else:
            st.info("Scoring metadata not available")

# ─── Scenarios and algorithms ────────────────────────────────────────────────
ui.section("Scenarios", "tune")
for name, spec in SCENARIOS.items():
    st.markdown(f"**{name}:** {spec['rationale']}")

ui.section("Algorithms", "science")
for name, spec in ALGORITHMS.items():
    st.markdown(f"**{name}:** {spec['note']}")

# ─── Data status ─────────────────────────────────────────────────────────────
ui.section("Data Status", "folder")
for label, ok in ui.data_status():
    st.markdown(ui.status_row(label, ok), unsafe_allow_html=True)

# ─── Notes ───────────────────────────────────────────────────────────────────
if has_result:
    ui.section("Notes", "lightbulb")
    ui.show_notes(result)
