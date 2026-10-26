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
from branca.element import MacroElement
from folium.plugins import MiniMap, MeasureControl
from jinja2 import Template
import json
import os

from utils import data_layers
from utils import structures as STR

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


_DATA_LAYER_CSS = """
<style>
.rwh-crisp { image-rendering: pixelated; image-rendering: crisp-edges; }
.rwh-panel, .rwh-legend {
  background: rgba(13,17,23,0.92); border: 1px solid #30363d; border-radius: 10px;
  color: #e6edf3; font-family: 'DM Sans', 'Segoe UI', sans-serif; font-size: 12px;
  box-shadow: 0 4px 24px rgba(0,0,0,0.5);
}
.rwh-panel { padding: 10px 12px; width: 230px; }
.rwh-h { font-weight: 700; color: #58a6ff; margin-bottom: 6px; font-size: 13px; }
.rwh-panel select {
  width: 100%; background: #0d1117; color: #e6edf3; border: 1px solid #30363d;
  border-radius: 6px; padding: 4px; font-size: 12px; margin-bottom: 6px;
}
.rwh-row { display: flex; align-items: center; gap: 6px; margin: 4px 0; cursor: pointer; }
.rwh-row input[type=range] { flex: 1; }
.rwh-disabled { opacity: 0.45; cursor: default; }
.rwh-hint { color: #7d8590; font-size: 11px; margin-top: 4px; }
.rwh-legend { padding: 8px 11px 7px; width: 245px; max-height: 250px; overflow-y: auto; }
.rwh-lt { font-weight: 700; font-size: 13px; }
.rwh-unit { color: #7d8590; font-size: 11px; margin-bottom: 6px; }
.rwh-bar { position: relative; height: 12px; border-radius: 3px; border: 1px solid #30363d; }
.rwh-mark { position: absolute; top: -3px; bottom: -3px; width: 2px; margin-left: -1px;
  background: #e6edf3; box-shadow: 0 0 0 1px #0d1117; }
.rwh-ticks, .rwh-marks { position: relative; height: 15px; margin: 2px 6px 0; font-size: 10.5px; }
.rwh-ticks span, .rwh-marks span { position: absolute; transform: translateX(-50%); white-space: nowrap; }
.rwh-marks { color: #e6edf3; font-weight: 700; }
.rwh-ticks { color: #c9d1d9; }
.rwh-classes { margin-top: 4px; }
.rwh-item { display: flex; align-items: center; gap: 6px; margin: 1px 0; font-size: 11.5px; line-height: 1.25; }
.rwh-sw { width: 16px; height: 12px; border-radius: 2px; border: 1px solid #30363d; flex-shrink: 0; }
.rwh-sub { margin-left: auto; color: #7d8590; font-size: 10.5px; }
.rwh-note { color: #c9d1d9; font-size: 11px; margin-top: 6px; }
.rwh-src { color: #7d8590; font-size: 10.5px; margin-top: 6px; border-top: 1px solid #30363d; padding-top: 5px; }
.rwh-pop .leaflet-popup-content { font-family: 'DM Sans', 'Segoe UI', sans-serif; font-size: 12px; margin: 10px 12px; }
.rwh-pop table { border-collapse: collapse; }
.rwh-pop td { padding: 1px 8px 1px 0; vertical-align: top; }
.rwh-pop td:first-child { color: #57606a; white-space: nowrap; }
.rwh-pop tr.rwh-on td { background: #fff3c4; }
.rwh-pop-h { font-weight: 700; margin-bottom: 4px; }
.rwh-sc { color: #57606a; font-size: 11px; }
.rwh-pop-f { color: #8c959f; font-size: 10.5px; margin-top: 5px; }
</style>
"""


class _DataLayerControls(MacroElement):
    """Injects utils/data_layers.js after the map and its layers exist."""
    _template = Template(
        "{% macro header(this, kwargs) %}{{ this.css }}{% endmacro %}"
        "{% macro script(this, kwargs) %}{{ this.js }}{% endmacro %}"
    )

    def __init__(self, map_name: str, payload: dict):
        super().__init__()
        self._name = "RwhDataLayers"
        js_path = os.path.join(os.path.dirname(__file__), "data_layers.js")
        with open(js_path, encoding="utf-8") as f:
            js = f.read()
        self.js = (js.replace("__MAP__", map_name)
                     .replace("__PAYLOAD__", data_layers.payload_json(payload)))
        self.css = _DATA_LAYER_CSS


# Per-algorithm candidate sites: one colour and one ring size each, so a
# location chosen by several algorithms shows as concentric rings. Smaller
# rings sit in higher panes, so every ring stays hoverable.
ALGORITHM_SITE_STYLES = {
    "AHP + WLC":          {"color": "#ff9f1c", "radius": 8,  "z": 470},
    "AHP + TOPSIS":       {"color": "#f72585", "radius": 11, "z": 465},
    "Fuzzy-AHP + WLC":    {"color": "#ffd60a", "radius": 14, "z": 460},
    "Fuzzy-AHP + TOPSIS": {"color": "#b388ff", "radius": 17, "z": 455},
}
SITE_MATCH_KM = 2.0   # same radius the consensus analysis uses


def _haversine_km(lat1, lon1, lat2, lon2):
    import math
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _add_algorithm_sites(m, algorithm_sites: dict) -> list[str]:
    """One toggleable overlay per algorithm; returns the names drawn."""
    drawn = []
    for name, style in ALGORITHM_SITE_STYLES.items():
        sites = algorithm_sites.get(name) or []
        if not sites:
            continue
        pane = "algoPane" + "".join(ch for ch in name if ch.isalnum())
        if CustomPane is not None:
            m.add_child(CustomPane(pane, z_index=style["z"]))
        label = (f'<span style="color:{style["color"]};font-weight:700;">&#9711;</span> '
                 f'Sites &middot; {name}')
        fg = folium.FeatureGroup(name=label, show=False)
        for s in sites:
            others = []
            for other, osites in algorithm_sites.items():
                if other == name or not osites:
                    continue
                best = min(osites, key=lambda o: _haversine_km(
                    s["lat"], s["lon"], o["lat"], o["lon"]))
                if _haversine_km(s["lat"], s["lon"], best["lat"], best["lon"]) <= SITE_MATCH_KM:
                    others.append(f"{other} (#{best.get('rank')})")
            shared = ("Also chosen by: " + ", ".join(others)) if others \
                else "Chosen by this algorithm only"
            tip = (
                "<div style='font-family:DM Sans,Segoe UI,sans-serif;font-size:12px;'>"
                f"<b style='color:{style['color']};'>&#9711; {name}</b><br>"
                f"Rank <b>#{s.get('rank')}</b> &middot; score "
                f"{float(s.get('suitability_score', 0)):.3f}<br>"
                f"{float(s['lat']):.4f}&deg;N, {float(s['lon']):.4f}&deg;E<br>"
                f"<span style='color:#57606a;'>{shared}</span></div>"
            )
            folium.CircleMarker(
                location=[s["lat"], s["lon"]],
                radius=style["radius"],
                color=style["color"],
                weight=2.5,
                fill=True,
                fill_color=style["color"],
                fill_opacity=0.08,
                tooltip=folium.Tooltip(tip, sticky=True),
                pane=pane if CustomPane is not None else None,
            ).add_to(fg)
        fg.add_to(m)
        drawn.append(name)
    return drawn


# Existing MGNREGA water works (utils/structures.py). Colours avoid the
# suitability green and the four algorithm ring colours.
WORK_COLOURS = {"WC": "#4dabf7", "WH": "#ffffff"}
CONFIRMED_COLOUR = "#00e5ff"
OVERLAP_COLOUR = "#ffd43b"
ZONE_NAMES = {3: "High", 2: "Medium", 1: "Low"}

_WORKS_CALLBACK = """
function (row) {
    var cats = {cats}, stages = {stages}, zones = {zones}, colours = {colours},
        prefixes = {prefixes};
    var url = row[6] === null ? "" : prefixes[row[5]] + row[6];
    var html = "<div style='font-family:DM Sans,Segoe UI,sans-serif;font-size:12px;'>"
        + "<b>MGNREGA work &middot; " + cats[row[2]] + "</b><br>"
        + stages[row[3]] + "<br>Suitability zone here: <b>" + zones[row[4]] + "</b><br>"
        + "<span style='color:#57606a;'>Unverified: category code only. The photo "
        + "audit found most works in these categories are not structures.</span>"
        + (url ? "<br><a href='" + url + "' target='_blank' rel='noopener'>"
                 + "Photo on Bhuvan &#8599;</a>" : "")
        + "</div>";
    var mk = L.circleMarker(new L.LatLng(row[0], row[1]), {
        radius: 3.5, color: "#0d1117", weight: 0.8,
        fillColor: colours[row[2]], fillOpacity: 0.95});
    mk.bindPopup(html, {maxWidth: 260});
    return mk;
}
"""

_CLUSTER_ICON = """
function (cluster) {
    var n = cluster.getChildCount();
    var s = n < 50 ? 28 : (n < 500 ? 34 : 40);
    return L.divIcon({
        html: "<div style='width:" + s + "px;height:" + s + "px;line-height:" + s
            + "px;border-radius:50%;background:rgba(31,111,235,0.78);box-shadow:0 0 0 3px rgba(77,171,247,0.25);"
            + "border:1.5px solid #a5d8ff;color:#ffffff;font:600 11px DM Sans,"
            + "Segoe UI,sans-serif;text-align:center;'>" + n + "</div>",
        className: "", iconSize: L.point(s, s)});
}
"""


def _add_water_works(m, works: list[dict], zones: list) -> int:
    """All in-district WC/WH geotags, clustered, off by default."""
    if not works:
        return 0
    from folium.plugins import FastMarkerCluster
    cats = list(STR.WATER_CATEGORIES)
    stages = sorted({w["stage"] for w in works})
    zone_keys = [3, 2, 1, None]
    prefixes, rows = [], []
    for w, z in zip(works, zones):
        url = w["url"] or ""
        cut = url.find("/upload/")
        prefix, rest = (url[:cut + 8], url[cut + 8:]) if cut >= 0 else ("", url)
        if prefix not in prefixes:
            prefixes.append(prefix)
        rows.append([round(w["lat"], 5), round(w["lon"], 5), cats.index(w["category"]),
                     stages.index(w["stage"]), zone_keys.index(z),
                     prefixes.index(prefix), rest or None])
    callback = _WORKS_CALLBACK
    for k, v in {"{cats}": [STR.CATEGORY_NAMES[c] for c in cats],
                 "{stages}": [STR.STAGE_NAMES.get(s, f"Stage {s}") for s in stages],
                 "{zones}": [ZONE_NAMES.get(z, "outside the scored area") for z in zone_keys],
                 "{colours}": [WORK_COLOURS[c] for c in cats],
                 "{prefixes}": prefixes}.items():
        callback = callback.replace(k, json.dumps(v))
    FastMarkerCluster(
        rows, callback=callback,
        name=(f'<span style="color:{WORK_COLOURS["WC"]};">&#9679;</span>'
              f'<span style="color:{WORK_COLOURS["WH"]};">&#9679;</span> '
              f'MGNREGA water works, WC/WH ({len(rows):,}, unverified)'),
        show=False, icon_create_function=_CLUSTER_ICON,
        disableClusteringAtZoom=13, showCoverageOnHover=False,
        chunkedLoading=True,
    ).add_to(m)
    return len(rows)


def _add_confirmed(m, confirmed: list[dict], zones: list) -> int:
    """Photo-confirmed structures; strict ones show their photo."""
    if not confirmed:
        return 0
    if CustomPane is not None:
        m.add_child(CustomPane("confirmedPane", z_index=475))
    n_strict = sum(c["rule"] == "strict" for c in confirmed)
    fg = folium.FeatureGroup(
        name=(f'<span style="color:{CONFIRMED_COLOUR};font-weight:700;">&#9670;</span> '
              f'Photo-confirmed structures ({n_strict} strict &middot; '
              f'{len(confirmed) - n_strict} lenient)'), show=False)
    for c, z in zip(confirmed, zones):
        strict = c["rule"] == "strict"
        rule = ("Both labellers: harvesting structure" if strict
                else "One labeller of two: harvesting structure")
        photo = (f"<img src='{c['thumb']}' style='width:240px;border-radius:4px;"
                 f"margin-top:6px;display:block;'>" if c.get("thumb")
                 else f"<a href='{c['url']}' target='_blank' rel='noopener'>"
                      f"Photo on Bhuvan &#8599;</a>")
        html = ("<div style='font-family:DM Sans,Segoe UI,sans-serif;font-size:12px;'>"
                f"<b style='color:#0b7285;'>Photo-confirmed ({c['rule']})</b><br>"
                f"{rule} &middot; labels {c['labels']}<br>"
                f"MGNREGA category {c['category']} &middot; "
                f"{STR.STAGE_NAMES.get(c['stage'], 'stage ' + c['stage'])}<br>"
                f"Suitability zone here: <b>{ZONE_NAMES.get(z, 'outside the scored area')}</b>"
                f"{photo}</div>")
        folium.RegularPolygonMarker(
            location=[c["lat"], c["lon"]], number_of_sides=4, rotation=0,
            radius=8 if strict else 6, color=CONFIRMED_COLOUR, weight=2,
            fill=True, fill_color=CONFIRMED_COLOUR, fill_opacity=0.9 if strict else 0.15,
            popup=folium.Popup(html, max_width=270),
            tooltip=f"Photo-confirmed structure ({c['rule']})",
            pane="confirmedPane" if CustomPane is not None else None,
        ).add_to(fg)
    fg.add_to(m)
    return len(confirmed)


def _add_site_overlaps(m, result: dict, algorithm_sites: dict | None,
                       works: list[dict], confirmed: list[dict]) -> int:
    """A gold star on every candidate site with an existing work inside its circle."""
    active = result.get("algorithm") or "AHP + WLC"
    entries = [(active, s) for s in (result.get("top_locations_details") or [])[:25]]
    for name, sites in (algorithm_sites or {}).items():
        entries += [(name, s) for s in sites or []]
    merged = []   # one star per location, listing every method that chose it
    for name, s in entries:
        for g in merged:
            if _haversine_km(s["lat"], s["lon"], g["lat"], g["lon"]) <= 0.3:
                if name not in g["by"]:
                    g["by"][name] = s.get("rank")
                break
        else:
            merged.append({"lat": s["lat"], "lon": s["lon"], "by": {name: s.get("rank")}})
    if CustomPane is not None:
        m.add_child(CustomPane("overlapPane", z_index=480))
    fg = folium.FeatureGroup(
        name=(f'<span style="color:{OVERLAP_COLOUR};">&#9733;</span> Candidate site '
              f'with an existing work within {int(STR.OVERLAP_KM * 1000)} m'), show=True)
    n = 0
    for g in merged:
        near_w = STR.nearby(g, works)
        near_c = STR.nearby(g, confirmed)
        if not near_w and not near_c:
            continue
        n += 1
        by = ", ".join(f"{k} #{v}" for k, v in g["by"].items())
        lines = []
        if near_c:
            strict = sum(c["rule"] == "strict" for _, c in near_c)
            lines.append(f"<b>{len(near_c)} photo-confirmed</b> structure(s) "
                         f"({strict} strict), nearest {near_c[0][0] * 1000:.0f} m")
        if near_w:
            cats = ", ".join(f"{k} {v}" for k, v in sorted(
                {c: sum(w['category'] == c for _, w in near_w) for c in STR.WATER_CATEGORIES}.items())
                if v)
            lines.append(f"{len(near_w)} unverified WC/WH work(s) ({cats}), "
                         f"nearest {near_w[0][0] * 1000:.0f} m")
        tip = ("<div style='font-family:DM Sans,Segoe UI,sans-serif;font-size:12px;'>"
               f"<b style='color:#b08900;'>&#9733; Existing work at a candidate site</b><br>"
               f"Chosen by: {by}<br>" + "<br>".join(lines) +
               "<br><span style='color:#57606a;'>Within the site's 600 m circle. "
               "Agreement with where works were built, not proof of accuracy.</span></div>")
        folium.Marker(
            location=[g["lat"], g["lon"]],
            icon=folium.DivIcon(
                html=(f"<div style='font-size:22px;line-height:22px;color:{OVERLAP_COLOUR};"
                      "text-shadow:0 0 3px #000,0 0 2px #000;transform:translate(-11px,-11px);'>"
                      "&#9733;</div>"),
                icon_size=(22, 22), icon_anchor=(0, 0)),
            tooltip=folium.Tooltip(tip, sticky=True),
            pane="overlapPane" if CustomPane is not None else None,
        ).add_to(fg)
    fg.add_to(m)
    return n


def _context_html(ctx: dict | None) -> str:
    """Water and farmland block for a candidate-site popup (farmland scenario)."""
    if not ctx:
        return ""
    rows = []
    if "work_km" in ctx:
        rows.append(f"Nearest MGNREGA water work ({ctx['work_cat']}, unverified): "
                    f"<b>{ctx['work_km']:.2f} km</b>")
    if ctx.get("works_near"):
        rows.append(f"Nearest {len(ctx['works_near'])} unverified works (open the photo to "
                    f"judge each): {STR.works_links_html(ctx)}")
    if "confirmed_km" in ctx:
        rows.append(f"Nearest photo-confirmed structure: <b>{ctx['confirmed_km']:.1f} km</b>")
    if "river_km" in ctx:
        rows.append(f"Nearest mapped river: <b>{ctx['river_km']:.2f} km</b>")
    if ctx.get("area_km2"):
        pct = 100 * ctx["cropland_km2"] / ctx["area_km2"]
        rows.append(f"{'On' if ctx.get('on_cropland') else 'Not on'} cropland; cropland within "
                    f"{STR.FARMLAND_RADIUS_KM:g} km: <b>{ctx['cropland_km2']:.1f} km²</b> "
                    f"({pct:.0f}%)")
    return ("<hr style='border:0;border-top:1px solid #ddd;margin:6px 0;'>"
            "<b>Water &amp; farmland</b><br>" + "<br>".join(rows) +
            "<br><span style='color:#7d8590;'>Rivers: HydroRIVERS, larger channels only.</span>")


def render_map(result: dict, stack: dict | None = None,
               algorithm_sites: dict | None = None,
               water_works: list | None = None,
               confirmed_structures: list | None = None,
               site_context: dict | None = None) -> str:
    """
    Build and return Folium map HTML string.
    Called from app.py with the result of gis_analysis.score_stack(). When the
    criteria `stack` is passed, the map also offers the colour-coded data
    layers, their legend and the click-to-read values (utils/data_layers.py).
    `algorithm_sites` ({algorithm name: top sites}) adds one colour-coded,
    toggleable site overlay per algorithm, off by default.
    `water_works` and `confirmed_structures` (utils/structures.py) add the
    existing MGNREGA works, and a star on every candidate site that has one
    within its circle. `site_context` ({rank: utils.structures.site_context})
    adds the water and farmland block to those sites' popups (farmland scenario).
    """

    # ── Base map ──────────────────────────────────────────────────────────────
    # Basemaps. CARTO's dark_matter tiles now return an "API key required"
    # watermark without an account key, so the default is Esri's dark-grey
    # canvas (keyless), with OpenStreetMap as the alternative in the layer box.
    m = folium.Map(
        location=CHANDRAPUR_CENTER,
        zoom_start=10,
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/"
              "World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
        name="Dark grey (Esri)",
        max_zoom=16,
    ).add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap", show=False).add_to(m)

    # Panes control render order and pointer-event behavior.
    # boundary/zones should be behind candidates and not steal hover.
    # Data-layer images use a pane at z 210 (utils/data_layers.js), above the
    # basemap tiles (200) and below the zones, boundary, rivers and sites.
    if CustomPane is not None:
        m.add_child(CustomPane("boundaryPane", z_index=260))
        m.add_child(CustomPane("zonesPane", z_index=250))
        m.add_child(CustomPane("riversPane", z_index=300))
        m.add_child(CustomPane("candidatesPane", z_index=450))

    # Track bounds for auto-fit
    fit_bounds = None

    # Overlay groups (so LayerControl toggles reliably)
    boundary_fg = folium.FeatureGroup(name="Boundary", show=True)
    rivers_fg = folium.FeatureGroup(name="Rivers / Drainage", show=True)
    zones_fg = folium.FeatureGroup(name="High Suitability Zones", show=True)
    active_algo = result.get("algorithm") or "AHP + WLC"
    candidates_fg = folium.FeatureGroup(
        name=f"Top Candidate Sites (selected: {active_algo})", show=True)

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
                f"{_context_html((site_context or {}).get(loc.get('rank')))}"
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

    # ── Candidate sites of every algorithm (off by default) ──────────────────
    algo_drawn = _add_algorithm_sites(m, algorithm_sites) if algorithm_sites else []

    # ── Existing MGNREGA water works (off by default) ────────────────────────
    works = water_works or []
    confirmed = confirmed_structures or []
    work_zones = STR.zone_of_points(works, result)
    n_works = _add_water_works(m, works, work_zones)
    n_confirmed = _add_confirmed(m, confirmed, STR.zone_of_points(confirmed, result))
    n_overlap = (_add_site_overlaps(m, result, algorithm_sites, works, confirmed)
                 if (works or confirmed) else 0)
    enrich = STR.enrichment(works, work_zones, result) if works else None

    # ── Plugins ───────────────────────────────────────────────────────────────
    MiniMap(toggle_display=True, position="bottomright", minimized=True).add_to(m)
    MeasureControl(position="topleft", primary_length_unit="kilometers").add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    # ── Data layers (criteria, population, suitability, hydrology) ──────────
    if stack is not None:
        try:
            payload = data_layers.build_payload(stack, result)
        except Exception as e:  # display extra; never break the main map
            payload = None
            print(f"[map_renderer] data layers unavailable: {e}")
        if payload:
            _DataLayerControls(m.get_name(), payload).add_to(m)

    if fit_bounds is not None:
        try:
            m.fit_bounds(fit_bounds)
        except Exception:
            pass

    # ── Custom Legend ─────────────────────────────────────────────────────────
    weights = result.get("weights", {})
    consistency_ratio = result.get("consistency_ratio", 0)

    algo_legend = ""
    if algo_drawn:
        rows = "".join(
            f'<div style="display:flex;align-items:center;margin:2px 0;font-size:12px;">'
            f'<span style="display:inline-block;width:{2 * st["radius"] - 6}px;height:{2 * st["radius"] - 6}px;'
            f'border:2.5px solid {st["color"]};border-radius:50%;margin-right:8px;flex-shrink:0;'
            f'margin-left:{17 - st["radius"]}px;"></span>{n}</div>'
            for n, st in ALGORITHM_SITE_STYLES.items() if n in algo_drawn)
        algo_legend = (
            '<div style="font-size:11.5px;color:#7d8590;margin:-4px 0 4px;">'
            'Sites by algorithm &middot; tick them in the layer box. A site '
            'chosen by several shows as rings inside each other.</div>' + rows + '<div style="height:8px;"></div>')

    works_legend = ""
    if n_works or n_confirmed:
        dot = ('<span style="display:inline-block;width:8px;height:8px;border-radius:50%;'
               'background:{c};border:1px solid #0d1117;margin-right:4px;"></span>')
        rows = []
        if n_works:
            rows.append(dot.format(c=WORK_COLOURS["WC"]) + "WC "
                        + dot.format(c=WORK_COLOURS["WH"]) + "WH &nbsp;MGNREGA water works")
        if n_confirmed:
            rows.append(f'<span style="color:{CONFIRMED_COLOUR};margin-right:6px;">&#9670;</span>'
                        'Photo-confirmed structure')
        rows.append(f'<span style="color:{OVERLAP_COLOUR};margin-right:6px;">&#9733;</span>'
                    f'Site with a work within {int(STR.OVERLAP_KM * 1000)} m ({n_overlap})')
        note = ""
        if enrich and enrich["High"]["area_pct"]:
            h = enrich["High"]
            note = (f'<div style="font-size:11.5px;color:#7d8590;margin-top:3px;">'
                    f'{h["points_pct"]:.1f}% of WC/WH works lie in High zones, which cover '
                    f'{h["area_pct"]:.2f}% of the district ({h["ratio"]:.2f}&times;). '
                    f'Works are unverified codes.</div>')
        works_legend = ("".join(f'<div style="font-size:12px;margin:2px 0;">{r}</div>' for r in rows)
                        + note + '<div style="height:8px;"></div>')

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
        max-width: 270px;
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
        {algo_legend}
        {works_legend}

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

    # Return the full HTML document. st.components.v1.html already places it
    # in an iframe; Folium's _repr_html_ would wrap it in a second, base64-
    # encoded iframe, a third larger and slower with the data layers included.
    return m.get_root().render()
