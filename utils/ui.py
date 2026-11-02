"""
utils/ui.py — helpers shared by app.py and the pages in views/.

app.py builds the sidebar and owns scoring on every run; the pages read the result
from session state. Display only: nothing here changes a score.
"""
import os
import re

import numpy as np
import streamlit as st

from ahp import ahp_engine, SCENARIOS
from utils import structures as STR
from utils.labels import criterion_label

DATA_DIR = "data"
FARMLAND_SCENARIO = "Fertile farmland"
CRITERIA_ORDER = ["slope", "rainfall", "drainage", "soil", "lulc", "population"]
EMPTY_MESSAGE = "Run the analysis from the sidebar to see this page"
MATRIX_HELP = (
    "Saaty 1–9 scale. Edit the upper triangle only — the lower triangle is "
    "rebuilt as its reciprocal. Row *i* over column *j* is how much more "
    "important *i* is than *j*."
)

_DATA_FILES = [
    ("District Boundary", ["boundary.geojson"]),
    ("Rivers / Drainage", ["rivers.geojson", "Clipped_rivers.shp"]),
    ("Rainfall (Raster)", ["rainfall.tif"]),
    ("Derived Slope (Degrees)", ["slope.tif", "Derived_Slope(Degrees).tif"]),
    ("Soil Texture", ["soil_texture.tif", "Soil_Texture_Chandrapur(correct CRS).tif", "soil.tif"]),
    ("Land Use/Land Cover (Raster)", ["lulc.tif"]),
    ("Population Density (Raster)", ["population.tif"]),
    ("DEM / Elevation (Optional)", ["dem.tif"]),
]

_NOTE_ICONS = {"⚠️": ":material/warning:", "✅": ":material/check_circle:",
               "ℹ️": ":material/info:", "📊": ":material/bar_chart:"}


# ── Text and headings ────────────────────────────────────────────────────────
def icon(name: str) -> str:
    """A Material Symbols glyph, for headings written as raw HTML."""
    return f'<span class="rwh-icon">{name}</span>'


def section(title: str, icon_name: str, suffix: str = "") -> None:
    st.markdown(f'<div class="section-header">{icon(icon_name)}{title}{suffix}</div>',
                unsafe_allow_html=True)


def muted(text: str, margin_bottom: int = 0) -> None:
    st.markdown(f"<div style='color:#7d8590; font-size:0.82rem; "
                f"margin-bottom:{margin_bottom}px;'>{text}</div>",
                unsafe_allow_html=True)


def note_markdown(note: str) -> str:
    """A pipeline note with Material icons and the human land-cover label."""
    for emoji, icon_code in _NOTE_ICONS.items():
        note = note.replace(emoji, icon_code)
    return re.sub(r"\b(LULC|Lulc)\b", "Land cover", note)


def show_notes(result: dict) -> None:
    for note in result.get("notes", []):
        st.markdown(f"• {note_markdown(note)}")


def fmt_arrow(is_better: bool | None) -> str:
    # Green up / Red down / Grey dash
    if is_better is True:
        return "<span style='color:#3fb950; font-weight:700;'>↑</span>"
    if is_better is False:
        return "<span style='color:#f85149; font-weight:700;'>↓</span>"
    return "<span style='color:#7d8590;'>—</span>"


def safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


def criterion_sort_key(criterion: str, weights: dict) -> tuple:
    try:
        w = float(weights.get(criterion, 0.0))
    except Exception:
        w = 0.0
    try:
        fallback_idx = CRITERIA_ORDER.index(criterion)
    except ValueError:
        fallback_idx = 999
    return (-w, fallback_idx, criterion)


# ── Data status ──────────────────────────────────────────────────────────────
def data_status() -> list[tuple[str, bool]]:
    """Each data file's label, and whether it exists."""
    return [(label, any(os.path.exists(os.path.join(DATA_DIR, n)) for n in names))
            for label, names in _DATA_FILES]


def status_row(label: str, ok: bool) -> str:
    if ok:
        return f'<div class="status-ok">{icon("check_circle")}{label}</div>'
    return f'<div class="status-missing">{icon("cancel")}{label}</div>'


# ── Pairwise matrix ──────────────────────────────────────────────────────────
def reciprocal_matrix(table) -> np.ndarray:
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


def matrix_table(matrix):
    """The table the editor shows, rounded as the scoring matrix is built from it."""
    import pandas as pd
    names = [criterion_label(c) for c in ahp_engine.criteria]
    return pd.DataFrame(matrix, index=names, columns=names).round(3)


def cr_message(cr: float, note: str = "") -> str:
    if cr < 0.10:
        return (f'<div class="status-ok">{icon("check_circle")}Consistency Ratio '
                f'{cr:.4f}{note} — acceptable</div>')
    return (f'<div class="status-missing">{icon("cancel")}Consistency Ratio {cr:.4f} — '
            f'inconsistent, revise the judgements</div>')


@st.dialog("Edit pairwise matrix", width="large")
def matrix_dialog(scenario_name: str, current) -> None:
    # Closing a dialog clears its widgets' state, so an applied matrix is stored
    # in session state; the sidebar reads that, never the editor directly.
    st.caption(MATRIX_HELP)
    edited = st.data_editor(
        matrix_table(current),
        key=f"matrix_editor_{scenario_name}",
        use_container_width=True,
    )
    preview = reciprocal_matrix(edited)
    _weights, cr = ahp_engine.calculate_weights(preview)
    st.markdown(cr_message(cr), unsafe_allow_html=True)
    apply_col, cancel_col, _ = st.columns([1, 1, 3])
    with apply_col:
        if st.button("Apply", key="matrix_apply", use_container_width=True):
            st.session_state["_matrix_applied"] = {"scenario": scenario_name,
                                                   "matrix": preview}
            st.rerun()
    with cancel_col:
        if st.button("Cancel", key="matrix_cancel", use_container_width=True):
            st.rerun()


def render_scenario_priorities(scenario_name: str, scenario_matrix) -> None:
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


# ── State shared between app.py and the pages ────────────────────────────────
def active() -> dict:
    """What the sidebar chose on this run: matrix, weights, CR, scenario, algorithm."""
    return st.session_state["_active"]


def require_result() -> dict:
    """The analysis result, or stop the page with its empty state.

    A failed run's error is already on screen from app.py, on every page.
    """
    result = st.session_state.get("analysis_result")
    if not result:
        st.info(EMPTY_MESSAGE, icon=":material/play_circle:")
        st.stop()
    if result.get("status") != "ok":
        st.stop()
    return result


def restore_widget(key: str, options: list | None = None, default=None) -> None:
    """Streamlit forgets a widget's value on any run that doesn't draw it, so a
    plain mirror key carries it across pages. A remembered value is dropped if it's
    no longer an option: site labels hold scores, so they change with the scenario.
    """
    if key in st.session_state and (options is None or st.session_state[key] in options):
        return
    value = st.session_state.get(f"_keep_{key}", default)
    if options is not None and value not in options:
        value = default
    st.session_state[key] = value


def remember_widget(key: str) -> None:
    st.session_state[f"_keep_{key}"] = st.session_state[key]


# ── Water works, for the map and agreement pages ─────────────────────────────
def works_enrichment(result: dict) -> dict | None:
    """Share of works per class. None without works or a High zone to compare."""
    works = STR.load_water_works()
    if not works:
        return None
    enrich = STR.enrichment(works, STR.zone_of_points(works, result), result)
    return enrich if enrich and enrich["High"]["area_pct"] else None


def site_contexts(result: dict, scenario: str | None = None,
                  algorithm: str | None = None) -> dict:
    """Farmland scenario: water and farmland context for each candidate site.

    With no scenario, this is the sidebar's result. Otherwise it's that
    combination's, from combination_result.
    """
    from gis_analysis import build_criteria_stack
    if scenario is None:
        scenario = st.session_state.get("scenario")
        key = ("sidebar", st.session_state.get("result_key"), scenario)
    else:
        key = ("combination", scenario, algorithm)
    cached = st.session_state.get("_site_ctx")
    if cached and cached["key"] == key:
        return cached["sites"]
    sites = {}
    if scenario == FARMLAND_SCENARIO:
        stack = build_criteria_stack(DATA_DIR)
        works, confirmed = STR.load_water_works(), STR.load_confirmed()
        sites = {loc["rank"]: STR.site_context(loc, stack, works, confirmed)
                 for loc in (result.get("top_locations_details") or [])[:25]}
    st.session_state["_site_ctx"] = {"key": key, "sites": sites}
    return sites


# ── A method and scenario other than the sidebar's ───────────────────────────
def default_matrix(scenario: str) -> np.ndarray:
    """A scenario's scoring matrix, built exactly as the sidebar builds it."""
    return reciprocal_matrix(matrix_table(ahp_engine.matrix_for_scenario(scenario)))


def combination_result(scenario: str, algorithm: str) -> dict:
    """Top sites and weights of one method and scenario, without touching the
    sidebar's result. Kept per combination, because only these fields are needed.
    """
    from algorithms import weights_for_algorithm
    from gis_analysis import build_criteria_stack, score_stack
    cache = st.session_state.setdefault("_sites_combinations", {})
    key = (scenario, algorithm)
    if key not in cache:
        matrix = default_matrix(scenario)
        weights, aggregator, _label = weights_for_algorithm(algorithm, matrix, ahp_engine.criteria)
        _crisp, cr = ahp_engine.calculate_weights(matrix)
        res = score_stack(build_criteria_stack(DATA_DIR), weights, cr,
                          aggregator=aggregator, algorithm=algorithm)
        cache[key] = {"top_locations_details": res.get("top_locations_details", []),
                      "weights": res.get("weights", {})}
    return cache[key]


def baseline_weights() -> dict:
    """The weights every combination's changes are shown against."""
    from algorithms import ALGORITHMS, weights_for_algorithm
    weights, _agg, _label = weights_for_algorithm(
        list(ALGORITHMS)[0], default_matrix(list(SCENARIOS)[0]), ahp_engine.criteria)
    return weights


def weights_changes_html(weights: dict, base: dict) -> str:
    """A combination's weights, largest first, with changes against the baseline."""
    rows = []
    for c in sorted(weights, key=weights.get, reverse=True):
        w, b = float(weights[c]), float(base[c])
        change = ""
        if abs(w - b) >= 0.01:
            arrow, col = ("▲", "#3fb950") if w > b else ("▼", "#f85149")
            change = f"<span style='color:{col};'>{arrow} from {b:.2f}</span>"
        rows.append(
            f"<tr><td style='padding:1px 10px 1px 0;'>{criterion_label(c)}</td>"
            f"<td style='text-align:right;padding:1px 10px;'><b>{w:.3f}</b></td>"
            f"<td style='font-size:0.78rem;'>{change}</td></tr>")
    return ("<table style='font-size:0.82rem;'>" + "".join(rows) + "</table>"
            "<div style='color:#7d8590;font-size:0.78rem;margin-top:4px;'>"
            "Arrows compare with the baseline weights.</div>")


# ── Robustness results: what they were computed for ──────────────────────────
def setup_note(computed_for: str, stale: bool, button: str) -> None:
    """Say which setup a stored result belongs to, and warn if that's not current."""
    if stale:
        st.warning(f"Out of date: computed for {computed_for}. The sidebar has changed "
                   f"since, so press **{button}** to update.", icon=":material/history:")
    else:
        st.caption(f"Computed for: {computed_for}")


def matrix_is_edited() -> bool:
    return "_matrix_applied" in st.session_state


def scenario_label() -> str:
    """The sidebar's scenario, marked if its matrix has been edited."""
    scenario = st.session_state.get("scenario", "")
    return f"{scenario} (edited matrix)" if matrix_is_edited() else scenario
