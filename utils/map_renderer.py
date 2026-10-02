"""
utils/map_renderer.py
─────────────────────
Renders an interactive Folium map from the AHP suitability analysis result.

Legend:
  - Grey outline      → Chandrapur district boundary
  - Blue lines        → Rivers / drainage
  - Green polygons    → High suitability zones
  - Yellow polygons   → Medium suitability zones
  - Red polygons      → Low suitability zones
"""

import folium
from folium.plugins import MiniMap, MeasureControl
import json
import os

try:
    from folium.map import CustomPane
except Exception:  # pragma: no cover
    CustomPane = None


CHANDRAPUR_CENTER = [20.10, 79.30]   # lat, lon


CRITERIA_ORDER = ["slope", "rainfall", "drainage", "soil", "lulc", "population"]


def _criterion_sort_key(criterion: str, weights: dict) -> tuple:
    """Sort by AHP priority (higher weight first), then by stable fallback order."""
    try:
        w = float(weights.get(criterion, 0.0))
    except Exception:
        w = 0.0
    try:
        fallback_idx = CRITERIA_ORDER.index(criterion)
    except ValueError:
        fallback_idx = 999
    return (-w, fallback_idx, criterion)


def _format_criteria_scores(scores: dict, weights: dict | None = None) -> list[tuple[str, float]]:
    """Return (criterion, score0to1) ordered by priority (AHP weights)."""
    if not scores:
        return []
    weights = weights or {}
    items = []
    for k, v in scores.items():
        try:
            items.append((k, float(v)))
        except Exception:
            continue
    items.sort(key=lambda kv: _criterion_sort_key(kv[0], weights))
    return items


def _gdf_to_geojson_str(gdf):
    """Safely convert GeoDataFrame to GeoJSON string."""
    try:
        return gdf.to_json()
    except Exception:
        return None


def render_map(result: dict) -> str:
    """
    Build and return Folium map HTML string.
    Called from ui.py with the result dict from gis_analysis.run_ahp_analysis().
    """

    # ── Base map ──────────────────────────────────────────────────────────────
    m = folium.Map(
        location=CHANDRAPUR_CENTER,
        zoom_start=10,
        tiles="CartoDB dark_matter",
        control_scale=True,
    )

    # Panes control render order and pointer-event behavior.
    # boundary/zones should be behind candidates and not steal hover.
    if CustomPane is not None:
        m.add_child(CustomPane("boundaryPane", z_index=200))
        m.add_child(CustomPane("zonesPane", z_index=250))
        m.add_child(CustomPane("riversPane", z_index=300))
        m.add_child(CustomPane("candidatesPane", z_index=450))

    # Track bounds for auto-fit
    fit_bounds = None

    # Overlay groups (so LayerControl toggles reliably)
    boundary_fg = folium.FeatureGroup(name="Boundary", show=True)
    rivers_fg = folium.FeatureGroup(name="Rivers / Drainage", show=True)
    zones_fg = folium.FeatureGroup(name="High Suitability Zones", show=True)
    candidates_fg = folium.FeatureGroup(name="Top Candidate Sites", show=True)

    # ── Boundary layer ────────────────────────────────────────────────────────
    boundary_gdf = result.get("boundary_gdf")
    if boundary_gdf is not None and len(boundary_gdf) > 0:
        geojson_str = _gdf_to_geojson_str(boundary_gdf)
        if geojson_str:
            folium.GeoJson(
                data=geojson_str,
                style_function=lambda _: {
                    "color": "#aaaaaa",
                    "weight": 2,
                    "opacity": 0.8,
                    "fillOpacity": 0.0,
                },
                # Don't steal hover/click from candidate overlays
                tooltip=None,
                interactive=False,
                bubblingMouseEvents=False,
                pane="boundaryPane" if CustomPane is not None else None,
            ).add_to(boundary_fg)

        try:
            minx, miny, maxx, maxy = boundary_gdf.total_bounds
            fit_bounds = [[miny, minx], [maxy, maxx]]
        except Exception:
            pass

    # ── Boundary layer ────────────────────────────────────────────────────────
    # For now, assume boundary is not in result; can add later if needed
    # boundary_gdf = result.get("boundary_gdf")
    # ... similar to before

    # ── Rivers ────────────────────────────────────────────────────────────────
    # Load rivers if available
    try:
        import geopandas as gpd
        rivers_gdf = result.get("rivers_gdf")
        if rivers_gdf is None:
            rivers_path = "data/rivers.geojson"
            if os.path.exists(rivers_path):
                rivers_gdf = gpd.read_file(rivers_path)

        if rivers_gdf is not None:
            geojson_str = _gdf_to_geojson_str(rivers_gdf)
            if geojson_str:
                folium.GeoJson(
                    data=geojson_str,
                    style_function=lambda _: {
                        "color":  "#4fc3f7",
                        "weight": 2.5,
                        "opacity": 0.85,
                    },
                    tooltip="River / Drainage",
                    pane="riversPane" if CustomPane is not None else None,
                ).add_to(rivers_fg)
    except Exception:
        pass

    # ── Suitability Zones ─────────────────────────────────────────────────────
    high_suitability_gdf = result.get("high_suitability_gdf")
    if high_suitability_gdf is not None and len(high_suitability_gdf) > 0:
        geojson_str = _gdf_to_geojson_str(high_suitability_gdf)
        if geojson_str:
            folium.GeoJson(
                data=geojson_str,
                style_function=lambda _: {
                    "fillColor":   "#00ff00",
                    "color":       "#00ff00",
                    "weight":      2,
                    "fillOpacity": 0.6,
                },
                # IMPORTANT: no tooltip here; it was masking the per-site hover stats
                tooltip=None,
                interactive=False,
                bubblingMouseEvents=False,
                pane="zonesPane" if CustomPane is not None else None,
            ).add_to(zones_fg)

    # For medium and low, we could add if we have them, but for now just high

    # ── Top Locations ─────────────────────────────────────────────────────────
    weights = result.get("weights", {}) or {}
    top_locations = result.get("top_locations_details") or result.get("top_locations") or []
    if top_locations:
        for loc in top_locations[:25]:  # Show more so sites appear across the district
            satisfied = loc.get("criteria_satisfied", [])
            scores = loc.get("criteria_scores", {})

            ordered_scores = _format_criteria_scores(scores, weights)
            sat_parts = []
            for c in sorted(satisfied, key=lambda x: _criterion_sort_key(x, weights)):
                if c in scores:
                    try:
                        sat_parts.append(f"{c.capitalize()} ({float(scores[c]) * 100:.1f}%)")
                    except Exception:
                        sat_parts.append(c.capitalize())
                else:
                    sat_parts.append(c.capitalize())
            sat_str = ", ".join(sat_parts) if sat_parts else "(none)"

            score_lines = "".join(
                [
                    (
                        f"<li>{k.capitalize()}: {v * 100:.1f}% "
                        f"<span style='color:#7d8590'>(w={float(weights.get(k, 0.0)):.3f}, contrib={(float(weights.get(k, 0.0)) * float(v)):.3f})</span></li>"
                    )
                    for k, v in ordered_scores
                ]
            )

            tooltip_lines = "<br>".join(
                [
                    (
                        f"{k.capitalize()}: {v * 100:.1f}% "
                        f"<span style='color:#7d8590'>(+{(float(weights.get(k, 0.0)) * float(v)):.3f})</span>"
                    )
                    for k, v in ordered_scores
                ]
            )
            tooltip_html = (
                "<div style='font-family:DM Sans,Segoe UI,sans-serif; font-size:12px;'>"
                f"<b>Rank #{loc.get('rank')}</b> · {float(loc.get('suitability_score', 0)):.3f}<br>"
                f"{tooltip_lines}"
                "</div>"
            )

            popup_html = (
                f"<div style='font-family:DM Sans,Segoe UI,sans-serif; font-size:12px;'>"
                f"<b>Rank #{loc.get('rank')}</b><br>"
                f"Suitability: <b>{float(loc.get('suitability_score', 0)):.3f}</b><br>"
                f"Coords: {float(loc.get('lon', 0)):.5f}, {float(loc.get('lat', 0)):.5f}<br>"
                f"<b>Satisfied:</b> {sat_str}"
                f"<hr style='border:0;border-top:1px solid #ddd;margin:6px 0;'>"
                f"<b>Criterion Scores:</b><ul style='padding-left:18px; margin:4px 0;'>{score_lines}</ul>"
                f"</div>"
            )

            folium.Circle(
                location=[loc['lat'], loc['lon']],
                radius=600,
                color="#00ff00",
                fill=True,
                fill_color="#00ff00",
                fill_opacity=0.20,
                weight=2,
                popup=folium.Popup(popup_html, max_width=320),
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
                pane="candidatesPane" if CustomPane is not None else None,
            ).add_to(candidates_fg)

            folium.CircleMarker(
                location=[loc['lat'], loc['lon']],
                radius=5,
                color="#00ff00",
                fill=True,
                fill_color="#00ff00",
                fill_opacity=1.0,
                weight=2,
                tooltip=folium.Tooltip(tooltip_html, sticky=True),
                pane="candidatesPane" if CustomPane is not None else None,
            ).add_to(candidates_fg)

    # Add overlay groups to map (controls their visibility)
    boundary_fg.add_to(m)
    rivers_fg.add_to(m)
    zones_fg.add_to(m)
    candidates_fg.add_to(m)

    # ── Plugins ───────────────────────────────────────────────────────────────
    MiniMap(toggle_display=True, position="bottomright").add_to(m)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    if fit_bounds is not None:
        try:
            m.fit_bounds(fit_bounds)
        except Exception:
            pass

    # ── Custom Legend ─────────────────────────────────────────────────────────
    weights = result.get("weights", {})
    consistency_ratio = result.get("consistency_ratio", 0)

    legend_html = f"""
    <div style="
        position: fixed;
        bottom: 40px; left: 50px;
        z-index: 1000;
        background: rgba(13,17,23,0.92);
        border: 1px solid #30363d;
        border-radius: 10px;
        padding: 14px 18px;
        font-family: 'DM Sans', 'Segoe UI', sans-serif;
        font-size: 13px;
        color: #e6edf3;
        min-width: 230px;
        box-shadow: 0 4px 24px rgba(0,0,0,0.5);
    ">
        <div style="font-weight:700; font-size:14px; margin-bottom:10px; color:#58a6ff;">
            💧 RWH Suitability Map (AHP)
        </div>

        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <div style="width:28px;height:3px;background:#aaa;border:1px dashed #aaa;margin-right:10px;flex-shrink:0;"></div>
            Chandrapur Boundary
        </div>
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <div style="width:28px;height:3px;background:#4fc3f7;margin-right:10px;flex-shrink:0;"></div>
            Rivers / Drainage
        </div>
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <div style="width:28px;height:10px;background:rgba(0,255,0,0.6);border:1px solid #00ff00;border-radius:2px;margin-right:10px;flex-shrink:0;"></div>
            High Suitability Zones
        </div>
        <div style="display:flex; align-items:center; margin-bottom:12px;">
            <div style="width:10px;height:10px;background:#00ff00;border-radius:50%;margin-right:10px;flex-shrink:0;"></div>
            Top Candidate Locations
        </div>

        <div style="border-top:1px solid #30363d; padding-top:8px; font-size:11.5px; color:#7d8590;">
            <span style="color:#3fb950;">●</span> Consistency Ratio: <strong style="color:#e6edf3;">{consistency_ratio:.3f}</strong><br>
            <span style="color:#3fb950;">●</span> Top Factor: <strong style="color:#e6edf3;">{max(weights, key=weights.get).capitalize() if weights else 'N/A'}</strong>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # ── Title overlay ─────────────────────────────────────────────────────────
    title_html = """
    <div style="
        position: fixed;
        top: 12px; left: 50%; transform: translateX(-50%);
        z-index: 1000;
        background: rgba(13,17,23,0.88);
        border: 1px solid #1f6feb;
        border-radius: 8px;
        padding: 7px 20px;
        font-family: 'Space Mono', monospace;
        font-size: 12px;
        color: #79c0ff;
        pointer-events: none;
    ">
        Chandrapur District · AHP-Based RWH Suitability Analysis
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))

    # Return full HTML string
    return m._repr_html_()
