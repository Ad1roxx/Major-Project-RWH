"""Candidate sites page: site cards, farmland context, Site A against Site B."""
import streamlit as st

from utils import structures as STR
from utils import ui
from utils.labels import criterion_label


def site_context_html(ctx: dict | None) -> str:
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


result = ui.require_result()
site_ctx = ui.site_contexts(result)

# ─── Top Locations + Criteria Satisfaction ───────────────────────────────────
ui.section("Ideal RWH Sites", "location_on",
           f'<span style="font-size:0.75rem; color:#7d8590;"> · {result.get("algorithm", "")} '
           f'· {st.session_state.get("scenario", "")}</span>')

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
        ctx_html = site_context_html(site_ctx.get(loc["rank"])) if site_ctx else ""

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

# ─── Compare Panel ───────────────────────────────────────────────────────────
if top_locations and len(top_locations) >= 2:
    ui.section("Compare Candidate Sites", "compare_arrows")

    weights = result.get("weights", {}) or {}

    # Build stable option labels
    options = []
    loc_by_label = {}
    for loc in top_locations:
        label = f"Rank #{loc.get('rank')} · {float(loc.get('suitability_score', 0)):.3f} · ({float(loc.get('lon', 0)):.4f}, {float(loc.get('lat', 0)):.4f})"
        options.append(label)
        loc_by_label[label] = loc

    ui.restore_widget("compare_site_a", options, options[0])
    ui.restore_widget("compare_site_b", options, options[1])
    left_col, right_col = st.columns(2)
    with left_col:
        left_label = st.selectbox("Site A", options, key="compare_site_a",
                                  on_change=ui.remember_widget, args=("compare_site_a",))
    with right_col:
        right_label = st.selectbox("Site B", options, key="compare_site_b",
                                   on_change=ui.remember_widget, args=("compare_site_b",))

    a = loc_by_label.get(left_label)
    b = loc_by_label.get(right_label)
    if a and b:
        a_score = ui.safe_float(a.get("suitability_score"))
        b_score = ui.safe_float(b.get("suitability_score"))

        if a_score is None or b_score is None:
            overall_cmp = None
        elif abs(a_score - b_score) < 1e-9:
            overall_cmp = None
        else:
            overall_cmp = a_score > b_score

        header_cols = st.columns([1, 1])
        with header_cols[0]:
            st.markdown(
                f"<div class='location-card'><strong>Site A</strong> {ui.fmt_arrow(True if overall_cmp is True else (False if overall_cmp is False else None))}<br>"
                f"Rank #{a.get('rank')} · Suitability <b>{float(a_score or 0):.3f}</b></div>",
                unsafe_allow_html=True,
            )
        with header_cols[1]:
            st.markdown(
                f"<div class='location-card'><strong>Site B</strong> {ui.fmt_arrow(False if overall_cmp is True else (True if overall_cmp is False else None))}<br>"
                f"Rank #{b.get('rank')} · Suitability <b>{float(b_score or 0):.3f}</b></div>",
                unsafe_allow_html=True,
            )

        scores_a = (a.get("criteria_scores") or {})
        scores_b = (b.get("criteria_scores") or {})
        all_criteria = sorted(
            set(scores_a.keys()) | set(scores_b.keys()),
            key=lambda c: ui.criterion_sort_key(c, weights),
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
            wa = ui.safe_float(weights.get(c, 0.0)) or 0.0
            va = ui.safe_float(scores_a.get(c))
            vb = ui.safe_float(scores_b.get(c))

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
                        f"<div>{ui.fmt_arrow(cmp_a)} {va * 100:.1f}% <span style='color:#7d8590;'>(+{contrib_a:.3f})</span></div>",
                        unsafe_allow_html=True,
                    )
            with r3:
                if vb is None:
                    st.markdown("<div style='color:#7d8590;'>—</div>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        f"<div>{ui.fmt_arrow(cmp_b)} {vb * 100:.1f}% <span style='color:#7d8590;'>(+{contrib_b:.3f})</span></div>",
                        unsafe_allow_html=True,
                    )

st.page_link("views/method.py", label="Download sites and maps (Method page)",
             icon=":material/download:")
