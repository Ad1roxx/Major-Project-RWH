"""app.py
──────
Streamlit UI for Rainwater Harvesting Suitability Analysis using AHP.

The entry point: page setup, the shared sidebar, and scoring, on every run. The
pages in views/ read the result from session state.
"""

import streamlit as st

from ahp import ahp_engine, SCENARIOS
from algorithms import ALGORITHMS, weights_for_algorithm
import criteria as C
from gis_analysis import build_criteria_stack, score_stack
from utils import ui
from utils.labels import criterion_label

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RWH Suitability Analysis | AHP",
    page_icon=":material/water_drop:",
    layout="wide",
    initial_sidebar_state="auto",  # open on a desktop, closed on a phone
)

pg = st.navigation([
    st.Page("views/map.py", title="Map", icon=":material/map:", default=True),
    st.Page("views/sites.py", title="Candidate sites", icon=":material/location_on:"),
    st.Page("views/robustness.py", title="Robustness", icon=":material/tune:"),
    st.Page("views/agreement.py", title="Agreement with recorded works", icon=":material/fact_check:"),
    st.Page("views/method.py", title="Method", icon=":material/menu_book:"),
])

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Less empty space above the title, so the map fits a laptop window sooner. */
[data-testid="stMainBlockContainer"] {
    padding-top: 2.5rem;
}

.rwh-icon {
    font-family: 'Material Symbols Rounded';
    font-weight: normal;
    font-style: normal;
    font-size: 1.15em;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    white-space: nowrap;
    vertical-align: -0.18em;
    margin-right: 0.4em;
    font-feature-settings: 'liga';
    -webkit-font-feature-settings: 'liga';
}

.main-title {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #58a6ff;
    letter-spacing: -0.5px;
    margin-bottom: 0;
}

.sub-title {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.95rem;
    color: #7d8590;
    margin-top: 2px;
    margin-bottom: 12px;
}

.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 1.2rem;
    font-weight: 600;
    color: #58a6ff;
    margin-bottom: 16px;
}

.weights-table {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px;
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: #79c0ff;
}

.location-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 8px;
    font-size: 0.85rem;
}

.stTextInput > div > div > input {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 1rem !important;
}

.stTextInput > div > div > input:focus {
    border-color: #58a6ff !important;
    box-shadow: 0 0 0 3px rgba(88,166,255,0.15) !important;
}

.stButton > button {
    background: #30363d !important;
    color: #e6edf3 !important;
    border: 1px solid #484f58 !important;
    border-radius: 8px !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
    font-size: 0.95rem !important;
    transition: background 0.2s !important;
}

.stButton > button:hover {
    background: #484f58 !important;
}

.st-key-run_analysis button, .st-key-matrix_apply button {
    background: #e6edf3 !important;
    color: #0d1117 !important;
    border-color: #e6edf3 !important;
}

.st-key-run_analysis button:hover, .st-key-matrix_apply button:hover {
    background: #c9d1d9 !important;
}

/* Candidate site cards. Rank 1 gets a subtle highlight. */
[class*="st-key-site_card_"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px;
    font-size: 0.85rem;
    gap: 0.5rem;
}

.st-key-site_card_1 {
    border-left: 3px solid #58a6ff;
}

[class*="st-key-site_card_"] [data-testid="stMarkdownContainer"],
[class*="st-key-site_card_"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.85rem;
}

[class*="st-key-site_card_"] .site-title {
    font-size: 0.95rem;
}

.site-coords {
    color: #7d8590;
    padding-bottom: 1rem;
}

.criteria-count {
    margin-left: 6px;
    padding: 1px 8px;
    border: 1px solid #30363d;
    border-radius: 10px;
    color: #7d8590;
    font-size: 0.75rem;
    white-space: nowrap;
}

.photo-link {
    display: inline-block;
    margin: 2px 4px 2px 0;
    padding: 1px 8px;
    border: 1px solid #484f58;
    border-radius: 6px;
    font-size: 0.78rem;
    color: #79c0ff !important;
    text-decoration: none !important;
    white-space: nowrap;
}

.photo-link:hover {
    background: #30363d;
}

[class*="st-key-view_site_"] button {
    background: none !important;
    border: none !important;
    color: #79c0ff !important;
    padding: 0 4px !important;
    min-height: 0 !important;
    font-size: 0.82rem !important;
    font-weight: 400 !important;
}

[class*="st-key-view_site_"] button:hover {
    background: #30363d !important;
}

/* Four metrics in a row beside the sidebar: at full size their values get cut off. */
@media (max-width: 1100px) {
    [data-testid="stMetricValue"] > div {
        font-size: 1.4rem;
    }

    [data-testid="stMetricLabel"] p {
        font-size: 0.78rem;
    }
}

/* The comparison stays side by side on a phone: stacked, A and B can't be told apart. */
@media (max-width: 640px) {
    .st-key-compare_rows [data-testid="stHorizontalBlock"] {
        flex-wrap: nowrap;
        font-size: 0.78rem;
    }

    .st-key-compare_rows [data-testid="stColumn"] {
        min-width: 0 !important;
        overflow-wrap: anywhere;
    }
}

.sidebar-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.85rem;
    color: #7d8590;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

.status-ok {
    color: #3fb950;
    font-size: 0.82rem;
}

.status-missing {
    color: #f85149;
    font-size: 0.82rem;
}

.info-box {
    background: #0d2137;
    border: 1px solid #1f6feb;
    border-radius: 8px;
    padding: 14px 18px;
    color: #79c0ff;
    font-size: 0.88rem;
    margin: 12px 0;
}

div[data-testid="stExpander"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
}
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown(f'<div class="main-title">{ui.icon("water_drop")}RWH Suitability Analysis</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">AHP-based Multi-Criteria Decision System · Chandrapur District</div>', unsafe_allow_html=True)

# "View on map" asked for a site's combination. A widget's value can only be set
# before the widget is drawn, so this has to come first.
st.session_state.update(st.session_state.pop("_pending_sidebar", {}))

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="sidebar-title">{ui.icon("play_circle")}Run Analysis</div>', unsafe_allow_html=True)
    run_btn = st.button("Run Suitability Analysis", key="run_analysis", use_container_width=True)

    # ─── Scenario + weights ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f'<div class="sidebar-title">{ui.icon("balance")}Weighting</div>', unsafe_allow_html=True)

    scenario_name = st.selectbox("Scenario", list(SCENARIOS), index=0, key="scenario")
    st.caption(SCENARIOS[scenario_name]["rationale"])

    scenario_matrix = ahp_engine.matrix_for_scenario(scenario_name)
    ui.render_scenario_priorities(scenario_name, scenario_matrix)

    # The scoring matrix has always been built from the editor's table, which is
    # rounded to 3 dp, so the app's CR and weights depend on that rounding. Going
    # through the same steps here keeps every printed number the same.
    # An applied edit lasts until the scenario changes, as it did in the old editor.
    applied = st.session_state.get("_matrix_applied")
    if applied and applied["scenario"] != scenario_name:
        del st.session_state["_matrix_applied"]
        applied = None
    matrix = (applied["matrix"] if applied
              else ui.reciprocal_matrix(ui.matrix_table(scenario_matrix)))

    open_matrix_editor = st.button("Edit pairwise matrix", key="matrix_open",
                                   icon=":material/grid_on:", use_container_width=True)
    if applied:
        st.caption("Using your edited matrix. Changing scenario returns to the defaults.")

    # ─── Algorithm ───────────────────────────────────────────────────────────
    algo_name = st.selectbox("Algorithm", list(ALGORITHMS), index=0, key="algorithm")
    st.caption(ALGORITHMS[algo_name]["note"])

    active_weights, active_aggregator, weighting_label = weights_for_algorithm(
        algo_name, matrix, ahp_engine.criteria)

    # CR is defined on the crisp pairwise matrix. Fuzzy-AHP has no standard
    # consistency ratio, so the crisp CR of the same judgements is reported.
    _crisp_weights, active_cr = ahp_engine.calculate_weights(matrix)

    cr_note = " (of the crisp matrix)" if weighting_label == "Fuzzy-AHP" else ""
    st.markdown(ui.cr_message(active_cr, cr_note), unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:0.78rem; color:#7d8590; margin-top:6px;'>"
        + "<br>".join(f"{criterion_label(k)}: <b>{v:.3f}</b>" for k, v in
                      sorted(active_weights.items(), key=lambda kv: -kv[1]))
        + "</div>", unsafe_allow_html=True)

    # ─── Data status: one line here, every file on the Method page ───────────
    st.markdown("---")
    status = ui.data_status()
    n_found = sum(ok for _label, ok in status)
    st.markdown(ui.status_row(f"{n_found} of {len(status)} data files found", n_found == len(status)),
                unsafe_allow_html=True)
    st.page_link("views/method.py", label="Data status", icon=":material/folder:")

    st.markdown("---")
    st.markdown(f'<div class="sidebar-title">{ui.icon("info")}About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.82rem; color:#7d8590; line-height:1.6;">
    This system uses Analytic Hierarchy Process (AHP) for multi-criteria evaluation of rainwater harvesting suitability, considering slope, rainfall, drainage, soil, land use, and population factors.
    <br><br>
    <strong style="color:#e6edf3;">Stack:</strong> Python · Streamlit · GeoPandas · Rasterio · Folium
    </div>
    """, unsafe_allow_html=True)

if open_matrix_editor:
    # Unedited, the table shows the scenario's own values, as the old editor did.
    ui.matrix_dialog(scenario_name, matrix if applied else scenario_matrix)

st.session_state["_active"] = {"matrix": matrix, "weights": active_weights, "cr": active_cr,
                               "scenario": scenario_name, "algorithm": algo_name}

if "analysis_result" not in st.session_state:
    st.session_state["analysis_result"] = None
    st.session_state["result_key"] = None

# ─── Main Analysis ────────────────────────────────────────────────────────────
# The criteria stack is weight-independent and cached in gis_analysis, so
# changing scenario or editing the matrix re-scores in ~0.15 s instead of
# rebuilding the rasters.
weight_key = (algo_name,) + tuple(round(active_weights[k], 6) for k in sorted(active_weights))
stale = (st.session_state.get("analysis_result") is not None
         and st.session_state.get("result_key") != weight_key)

if run_btn or stale:
    label = "Re-scoring with the new weights…" if stale and not run_btn else \
            "Running AHP multi-criteria analysis…"
    with st.spinner(label):
        stack = build_criteria_stack(ui.DATA_DIR)
        st.session_state["analysis_result"] = score_stack(
            stack, active_weights, active_cr,
            aggregator=active_aggregator, algorithm=algo_name)
        st.session_state["result_key"] = weight_key

# ─── Shown on every page ─────────────────────────────────────────────────────
result = st.session_state.get("analysis_result")
if result:
    if result.get("status") == "ok":
        # ─── Provisional-input banner ────────────────────────────────────────
        if getattr(C, "RAINFALL_SOURCE_NOTE", None):
            st.warning(C.RAINFALL_SOURCE_NOTE, icon=":material/warning:")
    else:
        st.error("Analysis failed. Check data files and try again.")
        ui.show_notes(result)

pg.run()
