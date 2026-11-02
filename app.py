"""app.py
──────
Streamlit UI for Rainwater Harvesting Suitability Analysis using AHP.

Single-button workflow: run analysis and display ideal RWH sites.
"""

import streamlit as st
import os
import re
import numpy as np
from gis_analysis import build_criteria_stack, score_stack
from utils.map_renderer import render_map
from utils import structures as STR
from utils.labels import criterion_label
from ahp import ahp_engine, SCENARIOS
from algorithms import ALGORITHMS, weights_for_algorithm, compare_algorithms
import criteria as C
import exports
from sensitivity import (one_way_sensitivity, summary_sentence,
                         map_removal_sensitivity, single_parameter_sensitivity)
import consensus as CONS


CRITERIA_ORDER = ["slope", "rainfall", "drainage", "soil", "lulc", "population"]


def _criterion_sort_key(criterion: str, weights: dict) -> tuple:
    try:
        w = float(weights.get(criterion, 0.0))
    except Exception:
        w = 0.0
    try:
        fallback_idx = CRITERIA_ORDER.index(criterion)
    except ValueError:
        fallback_idx = 999
    return (-w, fallback_idx, criterion)


FARMLAND_SCENARIO = "Fertile farmland"
MATRIX_HELP = (
    "Saaty 1–9 scale. Edit the upper triangle only — the lower triangle is "
    "rebuilt as its reciprocal. Row *i* over column *j* is how much more "
    "important *i* is than *j*."
)


def _icon(name: str) -> str:
    """A Material Symbols glyph, for headings written as raw HTML."""
    return f'<span class="rwh-icon">{name}</span>'


def _section(title: str, icon: str, suffix: str = "") -> None:
    st.markdown(f'<div class="section-header">{_icon(icon)}{title}{suffix}</div>',
                unsafe_allow_html=True)


_NOTE_ICONS = {"⚠️": ":material/warning:", "✅": ":material/check_circle:",
               "ℹ️": ":material/info:", "📊": ":material/bar_chart:"}


def _note_markdown(note: str) -> str:
    """A pipeline note with Material icons and the human land-cover label."""
    for emoji, icon in _NOTE_ICONS.items():
        note = note.replace(emoji, icon)
    return re.sub(r"\b(LULC|Lulc)\b", "Land cover", note)


def _reciprocal_matrix(table) -> np.ndarray:
    """A pairwise matrix from an editor table: upper triangle kept, lower rebuilt."""
    # np.array (not asarray) — the DataFrame st.data_editor returns is backed
    # by a read-only buffer, so an in-place edit below would raise
    # "ValueError: assignment destination is read-only". Copy first.
    matrix = np.array(table, dtype=float, copy=True)
    # Enforce reciprocity from the upper triangle so the matrix stays valid.
    n = matrix.shape[0]
    for i in range(n):
        matrix[i, i] = 1.0
        for j in range(i + 1, n):
            if matrix[i, j] <= 0 or not np.isfinite(matrix[i, j]):
                matrix[i, j] = 1.0
            matrix[j, i] = 1.0 / matrix[i, j]
    return matrix


def _matrix_table(matrix):
    """The table the editor shows, rounded as the scoring matrix is built from it."""
    import pandas as pd
    names = [criterion_label(c) for c in ahp_engine.criteria]
    return pd.DataFrame(matrix, index=names, columns=names).round(3)


def _cr_message(cr: float, note: str = "") -> str:
    if cr < 0.10:
        return (f'<div class="status-ok">{_icon("check_circle")}Consistency Ratio '
                f'{cr:.4f}{note} — acceptable</div>')
    return (f'<div class="status-missing">{_icon("cancel")}Consistency Ratio {cr:.4f} — '
            f'inconsistent, revise the judgements</div>')


@st.dialog("Edit pairwise matrix", width="large")
def _matrix_dialog(scenario_name: str, current) -> None:
    # Closing a dialog clears its widgets' state, so an applied matrix is stored
    # in session state; the sidebar reads that, never the editor directly.
    st.caption(MATRIX_HELP)
    edited = st.data_editor(
        _matrix_table(current),
        key=f"matrix_editor_{scenario_name}",
        use_container_width=True,
    )
    preview = _reciprocal_matrix(edited)
    _weights, cr = ahp_engine.calculate_weights(preview)
    st.markdown(_cr_message(cr), unsafe_allow_html=True)
    apply_col, cancel_col, _ = st.columns([1, 1, 3])
    with apply_col:
        if st.button("Apply", key="matrix_apply", use_container_width=True):
            st.session_state["_matrix_applied"] = {"scenario": scenario_name,
                                                   "matrix": preview}
            st.rerun()
    with cancel_col:
        if st.button("Cancel", key="matrix_cancel", use_container_width=True):
            st.rerun()


def _render_scenario_priorities(scenario_name: str, scenario_matrix) -> None:
    """What the selected scenario prioritises, against the baseline weights."""
    weights, _cr = ahp_engine.calculate_weights(scenario_matrix)
    base, _ = ahp_engine.calculate_weights(
        ahp_engine.matrix_for_scenario(list(SCENARIOS)[0]))
    is_base = scenario_name == list(SCENARIOS)[0]
    rows = []
    for c in sorted(weights, key=weights.get, reverse=True):
        w, b = float(weights[c]), float(base[c])
        change = ""
        if not is_base and abs(w - b) >= 0.01:
            arrow, col = ("▲", "#3fb950") if w > b else ("▼", "#f85149")
            change = (f"<span style='color:{col};'>{arrow} from {b:.2f}</span>")
        rows.append(
            f"<tr><td style='padding:1px 6px 1px 0;'>{criterion_label(c)}</td>"
            f"<td style='text-align:right;padding:1px 6px;'><b>{w:.2f}</b></td>"
            f"<td style='font-size:0.75rem;'>{change}</td></tr>")
    top = [criterion_label(c) for c in sorted(weights, key=weights.get, reverse=True)[:2]]
    farm_note = ("<div style='color:#7d8590;margin-top:4px;'>Farmland sites also show "
                 "the distance to existing water works and rivers, and the cropland "
                 "around them.</div>") if scenario_name == FARMLAND_SCENARIO else ""
    st.markdown(
        f"<div style='font-size:0.8rem;color:#c9d1d9;margin:2px 0 6px;'>"
        f"<b>Prioritises:</b> {top[0]}, then {top[1]}"
        f"{'' if is_base else ' &middot; arrows compare with the baseline'}"
        f"<table style='margin-top:4px;font-size:0.78rem;'>{''.join(rows)}</table>"
        f"{farm_note}"
        f"</div>", unsafe_allow_html=True)


def _site_context_html(ctx: dict | None) -> str:
    """Water and farmland context line for a site card (farmland scenario)."""
    if not ctx:
        return ""
    bits = []
    if "work_km" in ctx:
        bits.append(f"nearest MGNREGA water work ({ctx['work_cat']}, unverified) "
                    f"<b>{ctx['work_km']:.2f} km</b>")
    if ctx.get("works_near"):
        bits.append("check their photos: " + STR.works_links_html(ctx))
    if "confirmed_km" in ctx:
        bits.append(f"nearest photo-confirmed structure <b>{ctx['confirmed_km']:.1f} km</b>")
    if "river_km" in ctx:
        bits.append(f"nearest mapped river <b>{ctx['river_km']:.2f} km</b>")
    farm = ""
    if ctx.get("area_km2"):
        pct = 100 * ctx["cropland_km2"] / ctx["area_km2"]
        on = "on cropland" if ctx.get("on_cropland") else "not on cropland"
        farm = (f"<br>Site {on}; cropland within {STR.FARMLAND_RADIUS_KM:g} km: "
                f"<b>{ctx['cropland_km2']:.1f} km²</b> ({pct:.0f}% of the circle)")
    return ("<br><span style='color:#79c0ff;'>" + " · ".join(bits) + "</span>" + farm)


def _fmt_arrow(is_better: bool | None) -> str:
    # Green up / Red down / Grey dash
    if is_better is True:
        return "<span style='color:#3fb950; font-weight:700;'>↑</span>"
    if is_better is False:
        return "<span style='color:#f85149; font-weight:700;'>↓</span>"
    return "<span style='color:#7d8590;'>—</span>"


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RWH Suitability Analysis | AHP",
    page_icon=":material/water_drop:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
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
    margin-top: 4px;
    margin-bottom: 24px;
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
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown(f'<div class="main-title">{_icon("water_drop")}RWH Suitability Analysis</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">AHP-based Multi-Criteria Decision System · Chandrapur District</div>', unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="sidebar-title">{_icon("folder")}Data Status</div>', unsafe_allow_html=True)

    def _exists_any(data_dir: str, names: list[str]) -> bool:
        return any(os.path.exists(os.path.join(data_dir, n)) for n in names)

    layers = {
        "boundary.geojson": ("District Boundary", ["boundary.geojson"]),
        "rivers.geojson": ("Rivers / Drainage", ["rivers.geojson", "Clipped_rivers.shp"]),
        "rainfall.tif": ("Rainfall (Raster)", ["rainfall.tif"]),
        "slope.tif": ("Derived Slope (Degrees)", ["slope.tif", "Derived_Slope(Degrees).tif"]),
        "soil_texture.tif": ("Soil Texture", ["soil_texture.tif", "Soil_Texture_Chandrapur(correct CRS).tif", "soil.tif"]),
        "lulc.tif": ("Land Use/Land Cover (Raster)", ["lulc.tif"]),
        "population.tif": ("Population Density (Raster)", ["population.tif"]),
        "dem.tif": ("DEM / Elevation (Optional)", ["dem.tif"]),
    }

    data_dir = "data"
    all_present = True

    for _, (label, candidates) in layers.items():
        if _exists_any(data_dir, candidates):
            st.markdown(f'<div class="status-ok">{_icon("check_circle")}{label}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-missing">{_icon("cancel")}{label}</div>', unsafe_allow_html=True)
            all_present = False

    # ─── Scenario + weights ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f'<div class="sidebar-title">{_icon("balance")}Weighting</div>', unsafe_allow_html=True)

    scenario_name = st.selectbox("Scenario", list(SCENARIOS), index=0, key="scenario")
    st.caption(SCENARIOS[scenario_name]["rationale"])

    scenario_matrix = ahp_engine.matrix_for_scenario(scenario_name)
    _render_scenario_priorities(scenario_name, scenario_matrix)

    # The scoring matrix has always been built from the editor's table, which is
    # rounded to 3 dp, so the app's CR and weights depend on that rounding. Going
    # through the same steps here keeps every printed number the same.
    # An applied edit lasts until the scenario changes, as it did in the old editor.
    applied = st.session_state.get("_matrix_applied")
    if applied and applied["scenario"] != scenario_name:
        del st.session_state["_matrix_applied"]
        applied = None
    matrix = (applied["matrix"] if applied
              else _reciprocal_matrix(_matrix_table(scenario_matrix)))

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
    st.markdown(_cr_message(active_cr, cr_note), unsafe_allow_html=True)

    st.markdown(
        "<div style='font-size:0.78rem; color:#7d8590; margin-top:6px;'>"
        + "<br>".join(f"{criterion_label(k)}: <b>{v:.3f}</b>" for k, v in
                      sorted(active_weights.items(), key=lambda kv: -kv[1]))
        + "</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<div class="sidebar-title">{_icon("info")}About</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:0.82rem; color:#7d8590; line-height:1.6;">
    This system uses Analytic Hierarchy Process (AHP) for multi-criteria evaluation of rainwater harvesting suitability, considering slope, rainfall, drainage, soil, land use, and population factors.
    <br><br>
    <strong style="color:#e6edf3;">Stack:</strong> Python · Streamlit · GeoPandas · Rasterio · Folium
    </div>
    """, unsafe_allow_html=True)

if open_matrix_editor:
    # Unedited, the table shows the scenario's own values, as the old editor did.
    _matrix_dialog(scenario_name, matrix if applied else scenario_matrix)

# ─── Run Button (single-button workflow) ─────────────────────────────────────
_section("Run Analysis", "play_circle")
run_btn = st.button("Run Suitability Analysis", key="run_analysis", use_container_width=False)

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
            "⚙️ Running AHP multi-criteria analysis…"
    with st.spinner(label):
        stack = build_criteria_stack(data_dir)
        st.session_state["analysis_result"] = score_stack(
            stack, active_weights, active_cr,
            aggregator=active_aggregator, algorithm=algo_name)
        st.session_state["result_key"] = weight_key

result = st.session_state.get("analysis_result")
if result:
    if result.get("status") == "ok":
        weights = result.get("weights", {})
        consistency_ratio = result.get("consistency_ratio", 0)

        # ─── Provisional-input banner ────────────────────────────────────────
        if getattr(C, "RAINFALL_SOURCE_NOTE", None):
            st.warning(C.RAINFALL_SOURCE_NOTE, icon=":material/warning:")

        # ─── Suitability Map ─────────────────────────────────────────────────
        _section("Suitability Map", "map",
                 f'<span style="font-size:0.75rem; color:#7d8590;"> · {result.get("algorithm", "")} '
                 f'· {st.session_state.get("scenario", "")}</span>')

        # Folium gives the page new element ids on every render, so a rebuild
        # reloads the iframe and resets the view. Build only when the result,
        # matrix or scenario changes; anything else reuses the same page.
        matrix_key = tuple(np.round(matrix, 6).ravel())
        map_key = (st.session_state.get("result_key"), matrix_key,
                   st.session_state.get("scenario"))
        map_slot = st.empty()
        map_cache = st.session_state.get("_map_cache")
        if not map_cache or map_cache["key"] != map_key:
            with map_slot, st.spinner("Building map..."):
                # Top sites of all four algorithms under the current judgements,
                # for the per-algorithm site overlays. Recomputed only when the
                # pairwise matrix changes (≈0.6 s); the overlays start switched off.
                if st.session_state.get("algo_sites_key") != matrix_key:
                    stack = build_criteria_stack(data_dir)
                    algo_sites = {}
                    for name in ALGORITHMS:
                        w, agg, _label = weights_for_algorithm(name, matrix, ahp_engine.criteria)
                        algo_sites[name] = score_stack(
                            stack, w, aggregator=agg, algorithm=name,
                            extract_sites=False)["top_locations_details"]
                    st.session_state["algo_sites"] = algo_sites
                    st.session_state["algo_sites_key"] = matrix_key

                # Farmland scenario: water and farmland context for each candidate site
                site_ctx = {}
                if st.session_state.get("scenario") == FARMLAND_SCENARIO:
                    _stack = build_criteria_stack(data_dir)
                    _works, _conf = STR.load_water_works(), STR.load_confirmed()
                    site_ctx = {loc["rank"]: STR.site_context(loc, _stack, _works, _conf)
                                for loc in (result.get("top_locations_details") or [])[:25]}

                # Render map with suitability zones
                map_html = render_map(result, stack=build_criteria_stack(data_dir),
                                      site_context=site_ctx,
                                      algorithm_sites=st.session_state.get("algo_sites"),
                                      water_works=STR.load_water_works(),
                                      confirmed_structures=STR.load_confirmed())
            map_cache = {"key": map_key, "html": map_html, "site_ctx": site_ctx}
            st.session_state["_map_cache"] = map_cache
        site_ctx = map_cache["site_ctx"]
        with map_slot:
            st.components.v1.html(map_cache["html"], height=640)
        works = STR.load_water_works()
        if works:
            enrich = STR.enrichment(works, STR.zone_of_points(works, result), result)
            if enrich and enrich["High"]["area_pct"]:
                h = enrich["High"]
                st.caption(
                    f"Existing MGNREGA water works (WC/WH, {enrich['n']:,} in the scored area): "
                    f"{h['points_pct']:.1f}% lie in High zones, which cover {h['area_pct']:.2f}% "
                    f"of the district ({h['ratio']:.2f}× the area share). These are category "
                    f"codes, not verified structures: the photo audit found about 17–49% of "
                    f"them show a harvesting structure. Most works sit on cropland, which "
                    f"the model also favours, so part of this agreement comes from land "
                    f"cover alone. Agreement with existing practice, not an accuracy measure.")

        # ─── Area Statistics ─────────────────────────────────────────────────
        area_stats = result.get("area_statistics")
        if area_stats:
            _section("Suitability Zone Statistics", "bar_chart")
            total = area_stats.get("total_km2", 0)
            cls = area_stats.get("classes", {})
            cols = st.columns(4)
            with cols[0]:
                st.metric("District analysed", f"{total:,.0f} km²")
            for col, (label, colour) in zip(cols[1:], [("High", "#3fb950"), ("Medium", "#d29922"), ("Low", "#f85149")]):
                entry = cls.get(label, {})
                with col:
                    st.metric(
                        f"{label} suitability",
                        f"{entry.get('percent', 0):.1f}%",
                        f"{entry.get('area_km2', 0):,.0f} km²",
                        delta_color="off",
                    )
            st.markdown(
                "<div style='color:#7d8590; font-size:0.82rem;'>"
                f"Classes use fixed thresholds on the 0–1 suitability score "
                f"(High ≥ {C.SUITABILITY_THRESHOLDS[1]}, Medium {C.SUITABILITY_THRESHOLDS[0]}–{C.SUITABILITY_THRESHOLDS[1]}, "
                f"Low &lt; {C.SUITABILITY_THRESHOLDS[0]}), computed over pixels inside the district boundary only."
                "</div>",
                unsafe_allow_html=True,
            )

        # ─── Top Locations + Criteria Satisfaction ───────────────────────────
        _section("Ideal RWH Sites", "location_on")

        top_locations = result.get("top_locations_details", [])
        if top_locations:
            for loc in top_locations[:10]:
                satisfied = loc.get("criteria_satisfied", [])
                scores = loc.get("criteria_scores", {})
                sat_parts = []
                for c in satisfied:
                    if c in scores:
                        try:
                            sat_parts.append(f"{criterion_label(c)} ({float(scores[c]) * 100:.1f}%)")
                        except Exception:
                            sat_parts.append(criterion_label(c))
                    else:
                        sat_parts.append(criterion_label(c))
                satisfied_str = ", ".join(sat_parts) if sat_parts else "(none)"

                raw = loc.get("raw_values", {}) or {}
                raw_bits = []
                if "slope_deg" in raw:
                    raw_bits.append(f"Slope {raw['slope_deg']:.2f}°")
                if "soil_class" in raw:
                    raw_bits.append(f"Soil: {raw['soil_class']}")
                if "lulc_class" in raw:
                    raw_bits.append(f"Land cover: {raw['lulc_class']}")
                if "drainage_density" in raw:
                    raw_bits.append(f"Drainage {raw['drainage_density']:.2f} km/km²")
                if "settlement_km" in raw:
                    raw_bits.append(f"{raw['settlement_km']:.1f} km from settlement")
                raw_str = " · ".join(raw_bits)
                ctx_html = _site_context_html(site_ctx.get(loc["rank"])) if site_ctx else ""

                st.markdown(
                    f"""
                    <div class="location-card">
                    <strong>Rank #{loc['rank']}</strong> | Score: {loc['suitability_score']:.3f}<br>
                    Coordinates: {loc['lon']:.5f}, {loc['lat']:.5f}<br>
                    <strong>Criteria satisfied:</strong> {satisfied_str}
                    {f"<br><span style='color:#7d8590;'>{raw_str}</span>" if raw_str else ""}
                    {ctx_html}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("No ideal sites extracted - check data availability")

        # ─── Compare Panel ─────────────────────────────────────────────────
        if top_locations and len(top_locations) >= 2:
            _section("Compare Candidate Sites", "compare_arrows")

            weights = result.get("weights", {}) or {}

            # Build stable option labels
            options = []
            loc_by_label = {}
            for loc in top_locations:
                label = f"Rank #{loc.get('rank')} · {float(loc.get('suitability_score', 0)):.3f} · ({float(loc.get('lon', 0)):.4f}, {float(loc.get('lat', 0)):.4f})"
                options.append(label)
                loc_by_label[label] = loc

            left_col, right_col = st.columns(2)
            with left_col:
                left_label = st.selectbox("Site A", options, index=0, key="compare_site_a")
            with right_col:
                right_label = st.selectbox("Site B", options, index=1, key="compare_site_b")

            a = loc_by_label.get(left_label)
            b = loc_by_label.get(right_label)
            if a and b:
                a_score = _safe_float(a.get("suitability_score"))
                b_score = _safe_float(b.get("suitability_score"))

                if a_score is None or b_score is None:
                    overall_cmp = None
                elif abs(a_score - b_score) < 1e-9:
                    overall_cmp = None
                else:
                    overall_cmp = a_score > b_score

                header_cols = st.columns([1, 1])
                with header_cols[0]:
                    st.markdown(
                        f"<div class='location-card'><strong>Site A</strong> {_fmt_arrow(True if overall_cmp is True else (False if overall_cmp is False else None))}<br>"
                        f"Rank #{a.get('rank')} · Suitability <b>{float(a_score or 0):.3f}</b></div>",
                        unsafe_allow_html=True,
                    )
                with header_cols[1]:
                    st.markdown(
                        f"<div class='location-card'><strong>Site B</strong> {_fmt_arrow(False if overall_cmp is True else (True if overall_cmp is False else None))}<br>"
                        f"Rank #{b.get('rank')} · Suitability <b>{float(b_score or 0):.3f}</b></div>",
                        unsafe_allow_html=True,
                    )

                scores_a = (a.get("criteria_scores") or {})
                scores_b = (b.get("criteria_scores") or {})
                all_criteria = sorted(
                    set(scores_a.keys()) | set(scores_b.keys()),
                    key=lambda c: _criterion_sort_key(c, weights),
                )

                st.markdown(
                    "<div style='color:#7d8590; font-size:0.85rem; margin-bottom:8px;'>"
                    "Criteria are ordered by AHP priority (highest weight first). Values are normalized suitability scores shown as % (higher is better)."
                    "</div>",
                    unsafe_allow_html=True,
                )

                # Table header
                h1, h2, h3 = st.columns([1.2, 1, 1])
                with h1:
                    st.markdown("<div style='font-weight:700;'>Criterion</div>", unsafe_allow_html=True)
                with h2:
                    st.markdown("<div style='font-weight:700;'>Site A</div>", unsafe_allow_html=True)
                with h3:
                    st.markdown("<div style='font-weight:700;'>Site B</div>", unsafe_allow_html=True)

                for c in all_criteria:
                    wa = _safe_float(weights.get(c, 0.0)) or 0.0
                    va = _safe_float(scores_a.get(c))
                    vb = _safe_float(scores_b.get(c))

                    if va is None or vb is None:
                        cmp_a = None
                        cmp_b = None
                    elif abs(va - vb) < 1e-9:
                        cmp_a = None
                        cmp_b = None
                    else:
                        cmp_a = va > vb
                        cmp_b = vb > va

                    contrib_a = None if va is None else wa * va
                    contrib_b = None if vb is None else wa * vb

                    r1, r2, r3 = st.columns([1.2, 1, 1])
                    with r1:
                        st.markdown(
                            f"<div style='color:#e6edf3;'>"
                            f"<span style='font-family:Space Mono,monospace;'>{criterion_label(c)}</span> "
                            f"<span style='color:#7d8590;'>(w={wa:.3f})</span>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
                    with r2:
                        if va is None:
                            st.markdown("<div style='color:#7d8590;'>—</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<div>{_fmt_arrow(cmp_a)} {va * 100:.1f}% <span style='color:#7d8590;'>(+{contrib_a:.3f})</span></div>",
                                unsafe_allow_html=True,
                            )
                    with r3:
                        if vb is None:
                            st.markdown("<div style='color:#7d8590;'>—</div>", unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<div>{_fmt_arrow(cmp_b)} {vb * 100:.1f}% <span style='color:#7d8590;'>(+{contrib_b:.3f})</span></div>",
                                unsafe_allow_html=True,
                            )

        # ─── Downloads ───────────────────────────────────────────────────────
        _section("Export", "download")
        st.markdown(
            "<div style='color:#7d8590; font-size:0.82rem; margin-bottom:8px;'>"
            "Every file embeds the weights, consistency ratio and classification "
            "thresholds used to produce it.</div>", unsafe_allow_html=True)

        d1, d2, d3, d4 = st.columns(4)
        with d1:
            st.download_button("Sites (CSV)", exports.sites_csv(result),
                               "rwh_sites.csv", "text/csv", use_container_width=True)
        with d2:
            st.download_button("Sites (GeoJSON)", exports.sites_geojson(result),
                               "rwh_sites.geojson", "application/geo+json",
                               use_container_width=True)
        with d3:
            st.download_button("Suitability (GeoTIFF)", exports.suitability_geotiff(result),
                               "rwh_suitability.tif", "image/tiff",
                               use_container_width=True)
        with d4:
            st.download_button("Map (PNG)", exports.map_png(result),
                               "rwh_suitability_map.png", "image/png",
                               use_container_width=True)

        # ─── Sensitivity analysis ────────────────────────────────────────────
        _section("Sensitivity Analysis", "tune")
        st.markdown(
            "<div style='color:#7d8590; font-size:0.82rem;'>"
            "Varies each weight up and down and measures how far the ranking moves. "
            "This is the answer to \"your AHP weights are subjective\"."
            "</div>", unsafe_allow_html=True)

        sens_col1, sens_col2 = st.columns([1, 3])
        with sens_col1:
            delta_pct = st.select_slider("Vary weights by", [10, 20, 30], value=20,
                                         format_func=lambda v: f"±{v}%")
            run_sens = st.button("Run sensitivity", use_container_width=True)

        if run_sens:
            with st.spinner("Re-scoring across perturbed weights…"):
                stack = build_criteria_stack(data_dir)
                st.session_state["sensitivity"] = one_way_sensitivity(
                    stack, active_weights, delta=delta_pct / 100.0)
                st.session_state["map_removal"] = map_removal_sensitivity(
                    stack, active_weights)
                st.session_state["single_param"] = single_parameter_sensitivity(
                    stack, active_weights)

        sens = st.session_state.get("sensitivity")
        if sens:
            m1, m2, m3 = st.columns(3)
            m1.metric("Top-10 retained (mean)", f"{sens['mean_retained_pct']:.0f}%")
            m2.metric("Worst case", f"{sens['worst_retained_pct']:.0f}%")
            m3.metric("Max rank shift", sens["max_rank_shift"])

            st.markdown(f"**{summary_sentence(sens)}**")

            import pandas as pd
            df = pd.DataFrame(sens["runs"])[
                ["criterion", "direction", "weight_from", "weight_to",
                 "retained", "max_rank_shift", "high_pct", "high_pct_delta"]]
            df.columns = ["Criterion", "Dir", "Weight from", "Weight to",
                          f"Retained /{sens['top_n']}", "Max shift", "High %", "Δ High %"]
            df["Criterion"] = df["Criterion"].map(criterion_label)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.caption(
                "Influence on highly-suitable area (mean absolute change, "
                "percentage points): "
                + " · ".join(f"{criterion_label(k)} {v:.2f}" for k, v in sens["influence_high_pct"].items()))

            mr = st.session_state.get("map_removal")
            if mr:
                st.markdown("**Map removal sensitivity** (Lodwick et al., 1990)")
                st.caption(
                    "Each criterion layer is dropped entirely and the remaining "
                    "weights renormalise. S index = mean |V − V′| / V × 100 over "
                    "district pixels — how far the map moves when the layer is gone."
                )
                mdf = pd.DataFrame(mr["rows"])[
                    ["criterion", "weight", "sensitivity_index", "max_index",
                     "mean_abs_change", "retained", "high_pct", "high_pct_delta"]]
                mdf.columns = ["Criterion", "Weight", "S index %", "Max %",
                               "Mean |ΔV|", f"Retained /{mr['top_n']}",
                               "High %", "Δ High %"]
                mdf["Criterion"] = mdf["Criterion"].map(criterion_label)
                st.dataframe(mdf, use_container_width=True, hide_index=True)

            sp = st.session_state.get("single_param")
            if sp:
                st.markdown("**Single-parameter sensitivity** (Napolitano & Fabbri, 1996)")
                st.caption(
                    "Effective weight = mean of (wᵢ·rᵢ)/V × 100 — the share of the "
                    "final score a criterion actually contributes, against the "
                    "theoretical weight AHP assigned it. Ratio > 1 means the "
                    "criterion punches above its assigned weight across the district."
                )
                # Named columns, not positional: the rows also carry unrounded
                # *_exact fields for the figures, which the table does not show.
                sdf = pd.DataFrame(sp["rows"])[
                    ["criterion", "theoretical_pct", "effective_pct",
                     "effective_sd", "ratio"]]
                sdf.columns = ["Criterion", "Theoretical %", "Effective %",
                               "SD", "Ratio"]
                sdf["Criterion"] = sdf["Criterion"].map(criterion_label)
                st.dataframe(sdf, use_container_width=True, hide_index=True)

        # ─── Consensus across method variations ──────────────────────────────
        _section("Consensus Sites", "handshake")
        st.markdown(
            "<div style='color:#7d8590; font-size:0.82rem;'>"
            "Which sites survive when the method changes. A site chosen by one "
            "configuration may be an artefact of it; a site chosen by all of them "
            "is not. This is robustness evidence that needs no ground-truth data."
            "</div>", unsafe_allow_html=True)

        c_axis = st.radio(
            "Vary", ["Algorithms", "Scenarios"], horizontal=True, key="consensus_axis",
            help="Algorithms: same weights, different maths. "
                 "Scenarios: same maths, different weights.")

        if st.button("Compute consensus"):
            with st.spinner(f"Scoring every {c_axis.lower()[:-1]} variant…"):
                stack = build_criteria_stack(data_dir)
                axis = "algorithms" if c_axis == "Algorithms" else "scenarios"
                kw = ({"scenario": st.session_state.get("scenario")} if axis == "algorithms"
                      else {"algorithm": st.session_state.get("algorithm", "AHP + WLC")})
                st.session_state["consensus"] = CONS.consensus_report(stack, axis=axis, **kw)

        rep = st.session_state.get("consensus")
        if rep:
            import pandas as pd
            n_var = len(rep["variants"])
            sites = rep["sites"]
            unanimous = [s for s in sites if s["unanimous"]]
            stats = rep.get("agreement_stats") or {}
            top_level = (stats.get("levels") or {}).get(n_var, {})

            k1, k2, k3 = st.columns(3)
            k1.metric("Locations proposed", len(sites))
            k2.metric(f"Chosen by all {n_var}", len(unanimous))
            k3.metric(f"District High in all {n_var}",
                      f"{top_level.get('percent', 0):.1f}%",
                      f"{top_level.get('area_km2', 0):,.0f} km²", delta_color="off")

            st.caption("Varied: " + " · ".join(rep["variants"]))

            rows = [{
                "Consensus rank": s["consensus_rank"],
                "Longitude": s["lon"], "Latitude": s["lat"],
                "Chosen by": f"{s['n_variants']}/{s['n_possible']}",
                "Borda": s["borda"],
                "Best score": s["best_score"],
                "Mean rank": s["mean_rank"],
                "Land cover": (s.get("raw_values") or {}).get("lulc_class", ""),
            } for s in sites[:20]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(
                "Ranked by Borda count: within each variant a site at rank r of N "
                "scores N−r+1, and a variant that did not select the site scores it 0. "
                "Sites are matched across variants by position (2 km), not by rank."
            )

            if rep.get("agreement") is not None:
                png = CONS.agreement_png(
                    rep["agreement"], n_var, result.get("boundary_gdf"),
                    result["suitability_transform"],
                    f"Agreement across {n_var} {rep['axis']} — Chandrapur")
                st.image(png, use_container_width=True)
                d1, d2 = st.columns(2)
                with d1:
                    st.download_button("Consensus sites (CSV)", CONS.consensus_csv(rep),
                                       f"consensus_{rep['axis']}.csv", "text/csv",
                                       use_container_width=True)
                with d2:
                    st.download_button("Agreement map (PNG)", png,
                                       f"agreement_{rep['axis']}.png", "image/png",
                                       use_container_width=True)

        # ─── Algorithm comparison ────────────────────────────────────────────
        _section("Algorithm Comparison", "science")
        st.markdown(
            "<div style='color:#7d8590; font-size:0.82rem;'>"
            "Runs every algorithm on the same criteria stack, so any difference is "
            "attributable to the method alone. WLC is fully compensatory; TOPSIS "
            "penalises a site that is weak on any high-weight criterion."
            "</div>", unsafe_allow_html=True)

        if st.button("Compare all algorithms"):
            with st.spinner("Scoring every algorithm…"):
                stack = build_criteria_stack(data_dir)
                st.session_state["algo_comparison"] = compare_algorithms(
                    stack, matrix, ahp_engine.criteria)

        comp = st.session_state.get("algo_comparison")
        if comp:
            import pandas as pd
            rows = [{
                "Algorithm": r["algorithm"],
                "Weighting": r["weighting"],
                "Aggregation": r["aggregation"],
                "High %": r["high_pct"],
                "Mean score": r["score_mean"],
                f"Top-{comp['top_n']} shared": r["top_overlap"],
                "Surface corr": r["surface_corr"],
                "Class agreement %": r["class_agreement_pct"],
            } for r in comp["rows"]]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
            st.caption(
                f"Compared against **{comp['baseline']}**. 'Top-N shared' counts how many "
                f"of the baseline's top {comp['top_n']} sites the algorithm also selects "
                "(matched by position within 2 km)."
            )

            wrows = [{"Algorithm": r["algorithm"], **{criterion_label(k): v
                      for k, v in r["weights"].items()}} for r in comp["rows"]]
            st.markdown("**Weights by algorithm**")
            st.dataframe(pd.DataFrame(wrows), use_container_width=True, hide_index=True)

        _section("Notes", "lightbulb")
        for note in result.get("notes", []):
            st.markdown(f"• {_note_markdown(note)}")

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
                st.markdown(
                    "<div style='color:#7d8590; font-size:0.82rem; margin-top:8px;'>"
                    "Every criterion is reclassified with fixed, documented breakpoints rather than a "
                    "min–max rescale, so a given slope or soil class always scores the same. "
                    "Full justification in docs/METHODOLOGY.md."
                    "</div>",
                    unsafe_allow_html=True,
                )
            else:
                st.info("Scoring metadata not available")

    else:
        st.error("Analysis failed. Check data files and try again.")
        for note in result.get("notes", []):
            st.markdown(f"• {_note_markdown(note)}")

# No prompt/extra footer: single-button workflow
