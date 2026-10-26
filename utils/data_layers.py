"""
utils/data_layers.py
────────────────────
Colour-coded data layers for the browser map.

Each layer is drawn as an image overlay on the Leaflet map, under the
suitability zones and candidate sites, with a legend that changes with the
layer and a click-to-identify readout. The layers are:

  • the six criteria as raw values (mm, degrees, km …) or, on a switch, as the
    0–1 score the model gives them;
  • population density, plus a smoothed population heatmap;
  • the current suitability score surface;
  • the derived hydrology surfaces (Curve Number, runoff for the design storm).

Display only: nothing here feeds back into the analysis. All values come from
the cached criteria stack (gis_analysis.build_criteria_stack), so the map shows
exactly what the model used.

Projection. The analysis grid is regular in latitude/longitude (EPSG:4326),
while Leaflet draws in Web Mercator. Longitude maps linearly in both, latitude
does not, so each image is re-sampled row by row onto a Mercator-spaced grid
before encoding. Without this the overlay would drift by up to a cell against
the boundary and the sites.
"""

from __future__ import annotations

import base64
import io
import json
import math
import zlib

import numpy as np
from matplotlib import colormaps
from matplotlib.colors import LinearSegmentedColormap, LogNorm, Normalize, to_hex
from PIL import Image
from scipy.ndimage import gaussian_filter

import criteria as C

# Output rows per source row in the Mercator re-sampling. 2 guarantees that no
# source row is skipped, so the crisp cells stay faithful when zoomed in.
_ROW_FACTOR = 2

# Population heatmap smoothing (Gaussian sigma, km).
HEATMAP_SIGMA_KM = 1.5

# Model score colour ramp, shared by every score view so they compare directly.
_SCORE_CMAP = "RdYlGn"

# Soil texture colours (USDA classes; only the classes present are listed in
# the legend). Loam, the only class scored 1.00, is the distinct green.
SOIL_COLORS = {
    1: "#8c3b1e",   # Clay
    2: "#a0522d",   # Silty Clay
    3: "#b8733a",   # Sandy Clay
    4: "#d9b26f",   # Clay Loam
    5: "#c9a06a",   # Silty Clay Loam
    6: "#f0dfa8",   # Sandy Clay Loam
    7: "#4d9221",   # Loam
    8: "#8fbf5a",   # Silt Loam
    9: "#f5c77e",   # Sandy Loam
    10: "#b9b9b9",  # Silt
    11: "#f7e3b5",  # Loamy Sand
    12: "#fff2c2",  # Sand
}

# MODIS MCD12Q1 IGBP land-cover colours (the product's standard palette, the
# one QGIS styles and the MODIS documentation use).
LULC_COLORS = {
    1: "#05450a", 2: "#086a10", 3: "#54a708", 4: "#78d203", 5: "#009900",
    6: "#c6b044", 7: "#dcd159", 8: "#dade48", 9: "#fbff13", 10: "#b6ff05",
    11: "#27ff87", 12: "#c24f44", 13: "#a5a5a5", 14: "#ff6d4c", 15: "#69fff8",
    16: "#f9ffa4", 17: "#1c0dff",
}

# Layer → criterion whose 0–1 score the "Show model score" switch displays.
_SCORE_OF = {
    "rainfall": "rainfall",
    "slope": "slope",
    "drainage": "drainage",
    "settlement": "population",
    "population": "population",
    "pop_heat": "population",
    "soil": "soil",
    "lulc": "lulc",
}

_CRITERION_NAME = {
    "rainfall": "Rainfall",
    "slope": "Slope",
    "drainage": "Drainage density",
    "population": "Settlement proximity",
    "soil": "Soil texture",
    "lulc": "Land cover",
}

_static_cache: dict[int, dict] = {}


# ─────────────────────────────────────────────────────────────────────────────
# Geometry
# ─────────────────────────────────────────────────────────────────────────────

def _grid_bounds(transform, shape):
    """(south, west, north, east) of the analysis grid."""
    h, w = shape
    west, north = transform.c, transform.f
    east = west + w * transform.a
    south = north + h * transform.e
    return south, west, north, east


def _mercator_rows(transform, shape) -> np.ndarray:
    """Source row for each output row of a Mercator-spaced image."""
    h, _w = shape
    south, _west, north, _east = _grid_bounds(transform, shape)

    def merc_y(lat):
        return math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))

    y_top, y_bot = merc_y(north), merc_y(south)
    n_out = h * _ROW_FACTOR
    y = y_top - (np.arange(n_out) + 0.5) * (y_top - y_bot) / n_out
    lat = np.degrees(2 * np.arctan(np.exp(y)) - math.pi / 2)
    rows = np.floor((north - lat) / (-transform.e)).astype(int)
    return np.clip(rows, 0, h - 1)


# ─────────────────────────────────────────────────────────────────────────────
# Colouring and encoding
# ─────────────────────────────────────────────────────────────────────────────

def _valid(arr, mask):
    return mask & np.isfinite(arr)


def _index_ramp(arr, mask, cmap, norm, alpha_ramp=None):
    """Palette image of a continuous layer: index 0 is transparent (outside the
    district or no data), indices 1–255 sample the colour ramp evenly."""
    valid = _valid(arr, mask)
    filled = np.where(valid, arr, np.nan)
    with np.errstate(invalid="ignore", divide="ignore"):
        t = np.ma.filled(norm(np.ma.masked_invalid(filled)), 0.0)
    t = np.clip(np.nan_to_num(np.asarray(t, dtype=float)), 0.0, 1.0)
    idx = np.where(valid, 1 + np.round(t * 254), 0).astype(np.uint8)
    cm = colormaps[cmap] if isinstance(cmap, str) else cmap
    levels = np.linspace(0, 1, 255)
    pal = [(0, 0, 0, 0)]
    for lv in levels:
        r, g, b, _a = cm(lv)
        a = alpha_ramp(lv) if alpha_ramp is not None else 1.0
        pal.append((int(r * 255), int(g * 255), int(b * 255), int(round(a * 255))))
    return idx, pal


def _index_classes(arr, mask, colors):
    inside = _valid(arr, mask)
    idx = np.zeros(arr.shape, dtype=np.uint8)
    pal = [(0, 0, 0, 0), (128, 128, 128, 255)]       # 1: unlisted code, grey
    idx[inside] = 1
    for code, hexc in colors.items():
        sel = inside & (arr == code)
        if not sel.any():
            continue
        r, g, b = (int(hexc[i:i + 2], 16) for i in (1, 3, 5))
        pal.append((r, g, b, 255))
        idx[sel] = len(pal) - 1
    return idx, pal


def _png_uri(image, rows):
    """Encode (index array, RGBA palette) as a palette PNG with per-entry
    alpha, re-sampled to Mercator rows."""
    idx, pal = image
    img = Image.fromarray(np.ascontiguousarray(idx[rows]), "P")
    flat = []
    for r, g, b, _a in pal:
        flat += [r, g, b]
    img.putpalette(flat + [0] * (768 - len(flat)))
    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True, transparency=bytes(a for *_rgb, a in pal))
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _ramp_colors(cmap, n=11):
    cm = colormaps[cmap] if isinstance(cmap, str) else cmap
    return [to_hex(cm(x)) for x in np.linspace(0, 1, n)]


def _fmt(v, dp):
    return f"{v:,.{dp}f}"


def _ramp_legend(title, unit, source, cmap, norm, ticks, dp, note=None,
                 marks=None):
    """Legend spec for a continuous layer. `marks` adds labelled lines."""
    ticks = [t for t in ticks if norm.vmin <= t <= norm.vmax]
    spec = {
        "kind": "ramp", "title": title, "unit": unit, "source": source,
        "colors": _ramp_colors(cmap),
        "ticks": [{"pos": float(norm(t)), "label": _fmt(t, dp)} for t in ticks],
    }
    if note:
        spec["note"] = note
    if marks:
        spec["marks"] = [{"pos": float(norm(v)), "label": lab} for v, lab in marks]
    return spec


def _class_legend(title, source, codes_present, colors, labels, scores, note=None):
    items = []
    for code in codes_present:
        items.append({
            "color": colors.get(code, "#808080"),
            "label": labels.get(code, f"code {code}"),
            "sub": f"{scores.get(code, float('nan')):.2f}",
        })
    spec = {"kind": "classes", "title": title, "unit": "class · model score",
            "source": source, "items": items}
    if note:
        spec["note"] = note
    return spec


def _nice_ticks(vmin, vmax, n=5):
    return list(np.linspace(vmin, vmax, n))


# ─────────────────────────────────────────────────────────────────────────────
# Click-to-identify readout: quantised, packed and deflated
# ─────────────────────────────────────────────────────────────────────────────

_U16_NODATA = 65535
_U8_NODATA = 255


def _quantise(arr, mask, scale, dtype):
    nodata = _U16_NODATA if dtype == np.uint16 else _U8_NODATA
    valid = _valid(arr, mask)
    q = np.full(arr.shape, nodata, dtype=dtype)
    vals = np.round(np.where(valid, arr, 0) / scale)
    q[valid] = np.clip(vals[valid], 0, nodata - 1).astype(dtype)
    return q


def _pack(fields):
    """fields: list of (key, uint array, scale). uint16 first for alignment."""
    fields = sorted(fields, key=lambda f: 0 if f[1].dtype == np.uint16 else 1)
    meta, chunks, offset = [], [], 0
    for key, arr, scale in fields:
        b = np.ascontiguousarray(arr).astype(arr.dtype.newbyteorder("<")).tobytes()
        meta.append({"key": key, "bytes": 2 if arr.dtype == np.uint16 else 1,
                     "scale": scale, "offset": offset})
        chunks.append(b)
        offset += len(b)
    blob = zlib.compress(b"".join(chunks), 9)
    return meta, base64.b64encode(blob).decode("ascii")


# ─────────────────────────────────────────────────────────────────────────────
# Building the layers
# ─────────────────────────────────────────────────────────────────────────────

def _hydrology(stack, mask):
    """Curve Number and runoff on the analysis grid, as derived_maps.py does."""
    raw = stack["raw_rasters"]
    if "lulc" not in raw or "soil" not in raw:
        return None
    import derived_maps as D
    cn = np.where(mask, D.curve_number_grid(raw["lulc"], raw["soil"]), np.nan)
    depth = np.where(mask, D.scs_runoff(D.DEFAULT_STORM_MM, cn), np.nan)
    return cn, depth, float(D.DEFAULT_STORM_MM)


def _build_static(stack) -> dict:
    """Everything that does not depend on the weights; cached per stack."""
    key = id(stack)
    if key in _static_cache:
        return _static_cache[key]

    transform, shape = stack["transform"], stack["shape"]
    mask = stack["district_mask"]
    if mask is None:
        mask = np.ones(shape, dtype=bool)
    raw = stack["raw_rasters"]
    norm_r = stack["normalized_rasters"]
    rows = _mercator_rows(transform, shape)
    dy_km = abs(transform.e) * 111.32

    layers: dict[str, dict] = {}
    fields = []

    def inside(a):
        return np.asarray(a, dtype=float)[_valid(np.asarray(a, dtype=float), mask)]

    # Rainfall: the 2014–2024 mean the model uses.
    if "rainfall" in raw:
        a = raw["rainfall"]
        v = inside(a)
        nm = Normalize(float(np.floor(v.min())), float(np.ceil(v.max())))
        layers["rainfall"] = {
            "image": _png_uri(_index_ramp(a, mask, "Blues", nm), rows), "crisp": True,
            "legend": _ramp_legend(
                "Mean annual rainfall", "mm/yr",
                "CHIRPS v3.0, mean of the 2014–2024 annual totals. Source cells "
                "≈5.3 km, resampled to the ≈300 m analysis grid.",
                "Blues", nm, _nice_ticks(nm.vmin, nm.vmax), 0),
        }
        fields.append(("rainfall", _quantise(a, mask, 1.0, np.uint16), 1.0))

    if "slope" in raw:
        a = raw["slope"]
        v = inside(a)
        p98 = float(np.percentile(v, 98))
        nm = Normalize(0.0, max(p98, 0.1))
        layers["slope"] = {
            "image": _png_uri(_index_ramp(a, mask, "YlOrRd", nm), rows), "crisp": True,
            "legend": _ramp_legend(
                "Slope", "degrees",
                "HydroSHEDS conditioned DEM, GDAL slope (≈90 m), resampled.",
                "YlOrRd", nm, _nice_ticks(0, nm.vmax), 1,
                note=f"Colour stretched to the 98th percentile ({p98:.1f}°), as "
                     f"QGIS does by default; steeper ground (to {v.max():.0f}°) "
                     "takes the darkest colour."),
        }
        fields.append(("slope", _quantise(a, mask, 0.01, np.uint16), 0.01))

    dd = stack.get("drainage_density")
    if dd is not None:
        v = inside(dd)
        nm = Normalize(0.0, float(np.ceil(v.max() * 10) / 10))
        layers["drainage"] = {
            "image": _png_uri(_index_ramp(dd, mask, "GnBu", nm), rows), "crisp": True,
            "legend": _ramp_legend(
                "Drainage density", "km/km²",
                f"HydroRIVERS v1.0 channel length within "
                f"{C.DRAINAGE_DENSITY_WINDOW_KM:.1f} km, per km².",
                "GnBu", nm, _nice_ticks(0, nm.vmax), 2),
        }
        fields.append(("drainage", _quantise(dd, mask, 0.01, np.uint8), 0.01))

    sd = stack.get("settlement_distance_km")
    if sd is not None:
        v = inside(sd)
        nm = Normalize(0.0, float(np.ceil(v.max())))
        layers["settlement"] = {
            "image": _png_uri(_index_ramp(sd, mask, "viridis", nm), rows), "crisp": True,
            "legend": _ramp_legend(
                "Distance to nearest settlement", "km",
                f"Settlement = a cell with at least "
                f"{C.SETTLEMENT_DENSITY_THRESHOLD:.0f} people/km² (WorldPop 2020).",
                "viridis", nm, _nice_ticks(0, nm.vmax), 0),
        }
        fields.append(("settlement", _quantise(sd, mask, 0.1, np.uint16), 0.1))

    if "population" in raw:
        a = raw["population"]
        v = inside(a)
        vpos = v[v > 0]
        lo, hi = float(max(vpos.min(), 0.5)), float(vpos.max())
        nm = LogNorm(lo, hi, clip=True)
        log_ticks = [t for t in (1, 3, 10, 30, 100, 300, 1000, 3000, 10000)
                     if lo <= t <= hi]
        layers["population"] = {
            "image": _png_uri(_index_ramp(np.where(a > 0, a, lo), mask, "YlOrRd", nm),
                              rows), "crisp": True,
            "legend": _ramp_legend(
                "Population density", "people/km²",
                "WorldPop India 2020 (≈900 m), resampled. Logarithmic colour scale.",
                "YlOrRd", nm, log_ticks, 0,
                marks=[(C.SETTLEMENT_DENSITY_THRESHOLD, "settlement")]),
        }
        fields.append(("population", _quantise(a, mask, 1.0, np.uint16), 1.0))

        # Heatmap: density smoothed with a Gaussian kernel (normalised
        # convolution, so the district edge does not dim the values), on a
        # classic transparent→blue→green→yellow→red ramp.
        sigma_px = HEATMAP_SIGMA_KM / dy_km
        m = mask.astype(float)
        num = gaussian_filter(np.where(mask, np.nan_to_num(a, nan=0.0), 0.0), sigma_px)
        den = gaussian_filter(m, sigma_px)
        with np.errstate(invalid="ignore", divide="ignore"):
            smooth = np.where(mask & (den > 1e-6), num / den, np.nan)
        sv = inside(smooth)
        heat_cmap = LinearSegmentedColormap.from_list(
            "rwh_heat", ["#2c7bb6", "#00c2d1", "#7fd34e", "#ffe31a", "#ff8c1a", "#d7191c"])
        hlo = float(max(np.percentile(sv, 5), 1.0))
        hhi = float(sv.max())
        hn = LogNorm(hlo, hhi, clip=True)
        layers["pop_heat"] = {
            "image": _png_uri(_index_ramp(smooth, mask, heat_cmap, hn,
                                         alpha_ramp=lambda t: 0.15 + 0.85 * t ** 0.8),
                              rows), "crisp": False,
            "legend": _ramp_legend(
                "Population heatmap", "people/km², smoothed",
                f"WorldPop 2020 density smoothed with a {HEATMAP_SIGMA_KM:g} km "
                "Gaussian kernel. Shows where people concentrate; click the map "
                "or use the density layer for cell values.",
                heat_cmap, hn,
                [t for t in (3, 10, 30, 100, 300, 1000, 3000) if hlo <= t <= hhi], 0),
        }

    if "soil" in raw:
        a = raw["soil"]
        codes = sorted(int(c) for c in np.unique(inside(a)))
        layers["soil"] = {
            "image": _png_uri(_index_classes(a, mask, SOIL_COLORS), rows), "crisp": True,
            "legend": _class_legend(
                "Soil texture", "SoilGrids250m, USDA texture class (TEXMHT_M_sl1).",
                codes, SOIL_COLORS, C.SOIL_TEXTURE_LABELS, C.SOIL_TEXTURE_SCORES),
        }
        fields.append(("soil", _quantise(a, mask, 1.0, np.uint8), 1.0))

    if "lulc" in raw:
        a = raw["lulc"]
        codes = sorted(int(c) for c in np.unique(inside(a)))
        layers["lulc"] = {
            "image": _png_uri(_index_classes(a, mask, LULC_COLORS), rows), "crisp": True,
            "legend": _class_legend(
                "Land cover", "MODIS MCD12Q1, IGBP classes (≈463 m).",
                codes, LULC_COLORS, C.LULC_LABELS, C.LULC_SCORES),
        }
        fields.append(("lulc", _quantise(a, mask, 1.0, np.uint8), 1.0))

    hyd = _hydrology(stack, mask)
    if hyd is not None:
        cn, depth, storm = hyd
        v = inside(cn)
        nm = Normalize(float(np.floor(v.min())), 100.0)
        layers["cn"] = {
            "image": _png_uri(_index_ramp(cn, mask, "YlOrBr", nm), rows), "crisp": True,
            "legend": _ramp_legend(
                "SCS Curve Number", "AMC II",
                "IGBP land cover × hydrologic soil group, after USDA TR-55.",
                "YlOrBr", nm, _nice_ticks(nm.vmin, 100), 0,
                note="Supporting surface; not part of the weighted model."),
        }
        nm2 = Normalize(0.0, storm)
        layers["runoff"] = {
            "image": _png_uri(_index_ramp(depth, mask, "PuBu", nm2), rows), "crisp": True,
            "legend": _ramp_legend(
                "Runoff depth", "mm",
                f"SCS-CN runoff for a {storm:.0f} mm design storm (event model).",
                "PuBu", nm2, _nice_ticks(0, storm), 0,
                note="Supporting surface; not part of the weighted model."),
        }
        coef = depth / storm
        nm3 = Normalize(0.0, 1.0)
        layers["runoff_coef"] = {
            "image": _png_uri(_index_ramp(coef, mask, "PuBu", nm3), rows), "crisp": True,
            "legend": _ramp_legend(
                "Runoff coefficient", "runoff ÷ rainfall",
                f"Share of a {storm:.0f} mm design storm that runs off.",
                "PuBu", nm3, _nice_ticks(0, 1), 2,
                note="Supporting surface; not part of the weighted model."),
        }
        fields.append(("cn", _quantise(cn, mask, 1.0, np.uint8), 1.0))
        fields.append(("runoff", _quantise(depth, mask, 0.1, np.uint16), 0.1))

    # Model scores, one image per criterion, on one shared 0–1 ramp.
    scores = {}
    nm = Normalize(0.0, 1.0)
    for crit, arr in norm_r.items():
        method = C.CRITERION_METHOD.get(crit, "")
        note = None
        if crit == "population":
            note = ("The model scores distance to settlement, not density: "
                    "this is that score.")
        scores[crit] = {
            "image": _png_uri(_index_ramp(arr, mask, _SCORE_CMAP, nm), rows),
            "legend": _ramp_legend(
                f"{_CRITERION_NAME.get(crit, crit)} score", "0–1, 1 = most suitable",
                f"Model score used in the weighted overlay. {method}".strip(),
                _SCORE_CMAP, nm, [0, 0.25, 0.5, 0.75, 1.0], 2, note=note),
        }
        fields.append((f"s_{crit}", _quantise(arr, mask, 0.01, np.uint8), 0.01))

    meta, blob = _pack(fields)
    south, west, north, east = _grid_bounds(transform, shape)
    static = {
        "bounds": [[south, west], [north, east]],
        "grid": {"h": int(shape[0]), "w": int(shape[1]), "west": west, "north": north,
                 "dlon": transform.a, "dlat": -transform.e},
        "layers": layers,
        "scores": scores,
        "scoreOf": {k: v for k, v in _SCORE_OF.items() if v in scores},
        "readout": {"fields": meta, "data": blob},
        "soilLabels": {str(k): v for k, v in C.SOIL_TEXTURE_LABELS.items()},
        "lulcLabels": {str(k): v for k, v in C.LULC_LABELS.items()},
        "stormMm": hyd[2] if hyd is not None else None,
        "rows": rows,
    }
    _static_cache[key] = static
    return static


def build_payload(stack, result) -> dict | None:
    """Layer images, legends and readout data for one rendered map."""
    if stack is None or stack.get("status") != "ok":
        return None
    static = _build_static(stack)
    mask = stack["district_mask"]
    if mask is None:
        mask = np.ones(stack["shape"], dtype=bool)

    layers = dict(static["layers"])
    suit_meta, suit_blob = None, None
    suit = result.get("suitability_raster") if result else None
    if suit is not None:
        lo_t, hi_t = C.SUITABILITY_THRESHOLDS
        nm = Normalize(0.2, 1.0)
        layers["suitability"] = {
            "image": _png_uri(_index_ramp(suit, mask, "RdYlGn", nm), static["rows"]),
            "crisp": True,
            "legend": _ramp_legend(
                "Suitability score", "0–1",
                f"{result.get('algorithm', 'AHP + WLC')} composite under the "
                "current weights.",
                "RdYlGn", nm, [0.2, 0.4, 0.6, 0.8, 1.0], 1,
                marks=[(lo_t, f"{lo_t:.2f}"), (hi_t, f"{hi_t:.2f}")],
                note=f"Classes: Low ≤ {lo_t:.2f} < Medium ≤ {hi_t:.2f} < High."),
        }
        suit_meta, suit_blob = _pack([("suitability",
                                       _quantise(suit, mask, 0.001, np.uint16), 0.001)])

    payload = {k: v for k, v in static.items() if k != "rows"}
    payload["layers"] = layers
    payload["suitability"] = ({"fields": suit_meta, "data": suit_blob}
                              if suit_meta else None)
    payload["thresholds"] = list(C.SUITABILITY_THRESHOLDS)
    return payload


def payload_json(payload) -> str:
    """JSON safe to embed inside a <script> block."""
    return json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
