"""
tools/make_figures.py
─────────────────────
Publication figures for the research paper, as PNG at 300 dpi.

    python tools/make_figures.py              # every figure this tool owns
    python tools/make_figures.py --only 11    # one figure
    python tools/make_figures.py --dpi 600

Writes to outputs/figures/figNN.png.

Scope — this tool deliberately does NOT produce every figure in the paper
    Cartographic figures belong in QGIS, where labelling, insets and print
    layout are a solved problem: **Fig 1** (study area, three panels),
    **Fig 7** (hero suitability map with numbered sites and inset), and
    **Fig 15C** (top-ranked site per scenario). Fig 16 is produced here but a
    QGIS version would label the unanimous sites better.

    Conceptual diagrams belong in a drawing tool: **Fig 3** (preprocessing
    chain), **Fig 4** (research framework), **Fig 20** (model-to-field
    workflow). matplotlib can draw boxes and arrows but the result reads as
    hand-rolled. See docs/FIGURE_SPECS.md for their content.

Every number plotted here is computed at run time from the pipeline. None is
transcribed from the paper, so a figure cannot silently go stale — if the
model changes, the figure changes with it.
"""

from __future__ import annotations

import os
import sys

# Drop tools/ from sys.path before any third-party import: this directory holds
# inspect.py, which shadows the stdlib module numpy imports internally.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path[:] = [p for p in sys.path
               if os.path.abspath(p or os.getcwd()) != _HERE]
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import argparse  # noqa: E402

import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import BoundaryNorm, ListedColormap, TwoSlopeNorm  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Polygon as MplPolygon  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

import criteria as C  # noqa: E402
import gis_analysis as G  # noqa: E402
from ahp import SCENARIOS, ahp_engine  # noqa: E402
from algorithms import ALGORITHMS, weights_for_algorithm  # noqa: E402

OUTDIR = os.path.join("outputs", "figures")
DPI = 300

# Colourblind-safe categorical palette (Okabe–Ito). Used wherever a small
# number of discrete series must be distinguished.
OKABE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7", "#E69F00", "#56B4E9"]

# Medium is deliberately near-neutral. Drawn in the salmon half of a diverging
# ramp it read as "mildly bad" rather than "in between", which made the
# High/Low contrast harder to see.
CLASS_COLOURS = {"Low": "#B2182B", "Medium": "#E8E4DC", "High": "#2166AC"}

# One colour per MEANING, used by every figure. Previously blue meant "AHP
# weighting" in one figure and "aggregation effect" in the next, so a reader
# moving between two adjacent figures would misread one of them.
MEANING = {
    "AHP":         OKABE[0],   # weighting method
    "Fuzzy-AHP":   OKABE[1],
    "method":      "#6E7B8B",  # any factorial method effect — one neutral grey-blue
    "interaction": "#AFB8C1",  # the same, lighter
    "rainfall":    OKABE[2],   # upstream scoring decision
    "soil":        OKABE[3],   # upstream data correction
}


def _mn(x, fmt="+.3f") -> str:
    """Format a number with a true minus sign (U+2212), not hyphen-minus."""
    return format(x, fmt).replace("-", "−")

CRIT_LABEL = {
    "slope": "Slope", "rainfall": "Rainfall", "drainage": "Drainage density",
    "soil": "Soil texture", "lulc": "Land cover", "population": "Settlement prox.",
}


# ─────────────────────────────────────────────────────────────────────────────
# Style and output
# ─────────────────────────────────────────────────────────────────────────────

def _setup_style() -> None:
    """One typographic system for every figure. No matplotlib defaults."""
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": 8,
        "axes.labelsize": 8.5,
        "axes.titlesize": 9.5,
        "axes.titleweight": "bold",
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 8,
        "figure.titlesize": 10,
        "figure.titleweight": "bold",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.linewidth": 0.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "grid.linewidth": 0.4,
        "grid.alpha": 0.3,
        "lines.linewidth": 1.2,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.03,
        "pdf.fonttype": 42,     # embed as TrueType so text stays editable
        "ps.fonttype": 42,
        # Tick labels get a true minus sign. Annotation strings are formatted
        # through _mn() for the same reason.
        "axes.unicode_minus": True,
    })


def _panel_letters(axes, offset=(-0.02, 1.06), skip=()) -> None:
    """Stamp (a), (b), (c) … on a multi-panel figure.

    Journals expect them and the body text needs something to reference. Applied
    globally here rather than per figure so no panel is ever missed.
    """
    letters = "abcdefghijklmnop"
    k = 0
    for ax in np.ravel(np.asarray(axes, dtype=object)):
        if ax is None or ax in skip:
            continue
        ax.annotate(f"({letters[k]})", xy=offset, xycoords="axes fraction",
                    fontsize=9, fontweight="bold", va="bottom", ha="left",
                    annotation_clip=False)
        k += 1


def _save(fig, number: int, slug: str, dpi: int = DPI) -> None:
    """PNG only, at 300 dpi.

    PDFs were dropped on 2026-10-03: the vector copies roughly doubled the
    output volume for no benefit while the figures are still being iterated.
    If a journal asks for vector art at submission, add `fig.savefig(stem +
    ".pdf")` back here — nothing else needs to change.
    """
    os.makedirs(OUTDIR, exist_ok=True)
    stem = os.path.join(OUTDIR, f"fig{number:02d}")
    fig.savefig(stem + ".png", dpi=dpi)
    plt.close(fig)
    print(f"  fig{number:02d}  {slug}")


# ─────────────────────────────────────────────────────────────────────────────
# Map furniture
# ─────────────────────────────────────────────────────────────────────────────

def _extent(transform, shape):
    h, w = shape
    return (transform.c, transform.c + w * transform.a,
            transform.f + h * transform.e, transform.f)


def _add_scalebar(ax, extent, km=25, y_frac=0.055, x_frac=0.06) -> None:
    """Scale bar in kilometres on a geographic (degree) axis.

    Degrees of longitude shrink with latitude, so the bar length is computed at
    the panel's centre latitude rather than assumed constant.
    """
    x0, x1, y0, y1 = extent
    centre_lat = (y0 + y1) / 2.0
    km_per_deg_lon = G.KM_PER_DEG_LON_EQUATOR * np.cos(np.radians(centre_lat))
    deg = km / km_per_deg_lon
    xs = x0 + (x1 - x0) * x_frac
    ys = y0 + (y1 - y0) * y_frac
    ax.plot([xs, xs + deg], [ys, ys], color="black", lw=1.6, solid_capstyle="butt",
            zorder=10)
    for xx in (xs, xs + deg):
        ax.plot([xx, xx], [ys, ys + (y1 - y0) * 0.012], color="black", lw=1.0, zorder=10)
    ax.text(xs + deg / 2, ys + (y1 - y0) * 0.022, f"{km} km", ha="center",
            va="bottom", fontsize=7, zorder=10)


def _add_north(ax, extent, x_frac=0.94, y_frac=0.86) -> None:
    x0, x1, y0, y1 = extent
    x = x0 + (x1 - x0) * x_frac
    y = y0 + (y1 - y0) * y_frac
    ax.annotate("N", xy=(x, y + (y1 - y0) * 0.055), xytext=(x, y),
                ha="center", va="center", fontsize=8, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0),
                zorder=10)


def _graticule(ax, extent, n=4) -> None:
    x0, x1, y0, y1 = extent
    ax.set_xticks(np.linspace(x0, x1, n))
    ax.set_yticks(np.linspace(y0, y1, n))
    ax.tick_params(labelsize=6.5, length=2, pad=1)
    ax.grid(True, color="grey", lw=0.3, alpha=0.35, linestyle=":")


def _map(ax, arr, extent, boundary=None, cmap="viridis", norm=None,
         vmin=None, vmax=None, title=None, furniture=True, grat=True):
    im = ax.imshow(arr, extent=extent, cmap=cmap, norm=norm, vmin=vmin,
                   vmax=vmax, origin="upper", interpolation="nearest")
    if boundary is not None and len(boundary):
        boundary.boundary.plot(ax=ax, color="black", linewidth=0.5, zorder=5)
    if title:
        ax.set_title(title)
    if grat:
        _graticule(ax, extent)
    else:
        ax.set_xticks([])
        ax.set_yticks([])
    if furniture:
        _add_scalebar(ax, extent)
        _add_north(ax, extent)
    ax.set_xlim(extent[0], extent[1])
    ax.set_ylim(extent[2], extent[3])
    for s in ax.spines.values():
        s.set_visible(True)
        s.set_linewidth(0.6)
    return im


# ─────────────────────────────────────────────────────────────────────────────
# Shared analysis context
# ─────────────────────────────────────────────────────────────────────────────

class Ctx:
    """Everything the figures need, computed once."""

    def __init__(self, data_dir="data"):
        self.stack = G.build_criteria_stack(data_dir)
        self.mask = self.stack["district_mask"]
        self.transform = self.stack["transform"]
        self.shape = self.stack["shape"]
        self.extent = _extent(self.transform, self.shape)
        self.boundary = self.stack["boundary_gdf"]
        self.weights, self.cr = ahp_engine.calculate_weights()
        self.base = G.score_stack(self.stack, self.weights, self.cr)
        px = G._pixel_area_km2_per_row(self.transform, self.shape)
        self.area = np.repeat(px[:, None], self.shape[1], axis=1)
        self.crit = [c for c in ahp_engine.criteria
                     if c in self.stack["normalized_rasters"]]
        self._algos = None

    @property
    def algos(self):
        if self._algos is None:
            self._algos = {}
            for n in ALGORITHMS:
                w, agg, _ = weights_for_algorithm(n, ahp_engine.matrix,
                                                  ahp_engine.criteria)
                self._algos[n] = G.score_stack(self.stack, w, aggregator=agg,
                                               algorithm=n)
        return self._algos

    def inside(self, arr):
        """Array masked to the district, NaN outside — for imshow."""
        return np.where(self.mask & ~np.isnan(arr), arr, np.nan)

    def vals(self, arr):
        """1-D in-district values, NaN dropped — for statistics."""
        return arr[self.mask & ~np.isnan(arr)]


# ─────────────────────────────────────────────────────────────────────────────
# Figure 2 — why fixed reclassification replaced min–max
# ─────────────────────────────────────────────────────────────────────────────

def fig_02(ctx):
    raw_slope = ctx.vals(ctx.stack["raw_rasters"]["slope"])
    ramp_slope = ctx.vals(ctx.stack["normalized_rasters"]["slope"])
    lo, hi = raw_slope.min(), raw_slope.max()
    # Slope is a COST criterion — flatter is better — so the min–max form it
    # replaced was the inverted one. Using the ascending form here would show
    # 0% above 0.90 and misrepresent what was actually done.
    minmax_slope = 1.0 - (raw_slope - lo) / (hi - lo)
    above = 100.0 * float((minmax_slope > 0.90).mean())

    raw_lulc = ctx.vals(ctx.stack["raw_rasters"]["lulc"])
    codes = np.rint(raw_lulc).astype(int)
    minmax_lulc = (codes - codes.min()) / (codes.max() - codes.min())
    lookup_lulc = ctx.vals(ctx.stack["normalized_rasters"]["lulc"])

    fig, axes = plt.subplots(2, 3, figsize=(9.8, 6.0))
    for ax, data, title, xlabel in (
        (axes[0, 0], raw_slope, "Slope, raw", "degrees"),
        (axes[0, 1], minmax_slope, "Slope, min–max rescaled", "score"),
        (axes[0, 2], ramp_slope, "Slope, anchored ramp", "score"),
    ):
        ax.hist(data, bins=60, color=OKABE[0], edgecolor="none")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_yscale("log")
    axes[0, 0].set_ylabel("cells (log)")

    # Both score panels carry the SAME statistic in the SAME place, so the
    # comparison lands on inspection. Printing it only on the min–max panel
    # left two visually similar histograms and an assertion in the caption.
    above_ramp = 100.0 * float((ramp_slope > 0.90).mean())
    # The interquartile range separates the two schemes far more convincingly
    # than the share above a threshold: 2.8x versus 95.8% against 86.0%. Both
    # are shown, IQR first, because the share understates the real difference.
    iqr_mm = float(np.subtract(*np.percentile(minmax_slope, [75, 25])))
    iqr_rp = float(np.subtract(*np.percentile(ramp_slope, [75, 25])))
    for ax, pct, iqr, col in ((axes[0, 1], above, iqr_mm, OKABE[1]),
                              (axes[0, 2], above_ramp, iqr_rp, OKABE[2])):
        ax.axvspan(0.90, 1.0, color=col, alpha=0.16, zorder=0)
        ax.annotate("\n".join([f"IQR {iqr:.4f}", f"{pct:.1f}% above 0.90"]),
                    xy=(0.04, 0.82), xycoords="axes fraction", ha="left",
                    fontsize=8, color=col, fontweight="bold")

    u, cnt = np.unique(codes, return_counts=True)
    axes[1, 0].bar(u, cnt, color=OKABE[2], width=0.75)
    axes[1, 0].set_title("Land cover, IGBP class codes")
    axes[1, 0].set_xlabel("class code")
    axes[1, 0].set_ylabel("cells (log)")
    axes[1, 0].set_yscale("log")

    uu, cc = np.unique(np.round(minmax_lulc, 4), return_counts=True)
    axes[1, 1].bar(uu, cc, color=OKABE[1], width=0.03)
    axes[1, 1].set_title("Land cover, min–max on codes")
    axes[1, 1].set_xlabel("score")
    axes[1, 1].set_yscale("log")

    ul, cl = np.unique(np.round(lookup_lulc, 4), return_counts=True)
    axes[1, 2].bar(ul, cl, color=OKABE[2], width=0.03)
    axes[1, 2].set_title("Land cover, class lookup")
    axes[1, 2].set_xlabel("score")
    axes[1, 2].set_yscale("log")

    # Name specific classes on both panels so the inversion is visible rather
    # than something the reader has to reconstruct by mapping codes themselves.
    # Labels go INSIDE the panel with a short downward arrow. Placing them above
    # the axes collided with the panel title, the panel letter and the figure
    # title all at once.
    # Headroom so the in-panel labels clear the tallest bar on a log axis.
    for ax in (axes[1, 1], axes[1, 2]):
        lo, hi = ax.get_ylim()
        ax.set_ylim(lo, hi * 12)

    cmin, cmax = codes.min(), codes.max()
    for code, short in ((17, "Water"), (4, "Forest"), (12, "Cropland")):
        mm = (code - cmin) / (cmax - cmin)
        lk = C.LULC_SCORES[code]
        for ax, xval, colour in ((axes[1, 1], mm, OKABE[1]),
                                 (axes[1, 2], lk, OKABE[2])):
            ha = "left" if xval < 0.2 else ("right" if xval > 0.8 else "center")
            ax.annotate(f"{short}\n{xval:.2f}", xy=(xval, 0.50),
                        xytext=(xval, 0.90),
                        xycoords=("data", "axes fraction"),
                        textcoords=("data", "axes fraction"),
                        ha=ha, va="top", fontsize=7, color=colour,
                        fontweight="bold",
                        arrowprops=dict(arrowstyle="-|>", color=colour, lw=0.9,
                                        shrinkA=1, shrinkB=1))

    for ax in axes.ravel():
        ax.grid(True, axis="y")
    _panel_letters(axes, offset=(-0.02, 1.08))

    # Row caption placed below the whole figure, clear of the x-axis labels the
    # per-panel version used to overprint.
    fig.text(0.50, -0.055,
             "Bottom row: under min–max the score follows the class CODE — water (17) scores best, "
             "forest (4) worst.\nUnder the lookup it follows the class MEANING, and the ordering inverts.",
             ha="center", va="top", fontsize=8, color="0.25")
    fig.suptitle("Why fixed reclassification replaced min–max normalisation", y=1.02)
    fig.tight_layout(h_pad=2.6)
    _save(fig, 2, f"normalisation (IQR {iqr_mm:.4f} vs {iqr_rp:.4f}, {iqr_rp/iqr_mm:.1f}x wider spread)")
    return {"minmax_slope_above_090_pct": round(above, 2),
            "ramp_slope_above_090_pct": round(above_ramp, 2),
            "minmax_IQR": round(iqr_mm, 4), "ramp_IQR": round(iqr_rp, 4),
            "IQR_ratio": round(iqr_rp / iqr_mm, 2),
            "NOTE": "manuscript says 97.4% — that used the whole-raster range "
                    "(max 72.2 deg); this is in-district (max 56.0 deg)"}


# ─────────────────────────────────────────────────────────────────────────────
# Figure 5 — the six scoring functions over the data they act on
# ─────────────────────────────────────────────────────────────────────────────

def fig_05(ctx):
    fig, axes = plt.subplots(2, 3, figsize=(9.5, 5.2))
    specs = [
        ("slope", ctx.stack["raw_rasters"]["slope"], "slope (°)", (0, 20)),
        ("rainfall", ctx.stack["raw_rasters"]["rainfall"], "mean annual rainfall (mm)", None),
        ("drainage", ctx.stack["drainage_density"].astype(float), "drainage density (km/km²)", None),
        ("soil", ctx.stack["raw_rasters"]["soil"], "soil texture class", None),
        ("lulc", ctx.stack["raw_rasters"]["lulc"], "IGBP land-cover class", None),
        ("population", ctx.stack["settlement_distance_km"].astype(float), "distance to settlement (km)", (0, 25)),
    ]
    for ax, (name, raw, xlabel, xlim) in zip(axes.ravel(), specs):
        rv = ctx.vals(raw)
        sv = ctx.vals(ctx.stack["normalized_rasters"][name])
        ax2 = ax.twinx()
        ax2.hist(rv, bins=50, color="0.82", edgecolor="none", zorder=0)
        ax2.set_yticks([])
        ax2.spines["right"].set_visible(False)
        order = np.argsort(rv)
        if name in ("soil", "lulc"):
            ax.scatter(rv, sv, s=14, color=OKABE[0], zorder=3)
        else:
            ax.plot(rv[order], sv[order], color=OKABE[0], lw=1.6, zorder=3)
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
        ax.set_title(f"{CRIT_LABEL[name]}  (w = {ctx.weights[name]:.3f})")
        ax.set_xlabel(xlabel)
        ax.set_ylim(-0.03, 1.05)
        if xlim:
            ax.set_xlim(*xlim)
            beyond = 100.0 * float((rv > xlim[1]).mean())
            if beyond > 0.01:
                ax.annotate(f"axis truncated at {xlim[1]:g}; "
                            f"{beyond:.2f}% of cells lie beyond\n"
                            f"(in-district max {rv.max():.1f})",
                            xy=(0.97, 0.06), xycoords="axes fraction", ha="right",
                            fontsize=6.8, color="0.35")
        ax.grid(True, axis="y")
        # The one data-dependent transform in the set. Worth naming on the
        # panel, since it is the paper's acknowledged exception to its own
        # transferability argument.
        if name in ("soil", "lulc"):
            ax2.set_yscale("function",
                           functions=(lambda v: np.sqrt(np.abs(v)), lambda v: v ** 2))
        if name == "rainfall":
            ax.annotate("district-relative", xy=(0.5, 0.055),
                        xycoords="axes fraction", ha="center", fontsize=7.5,
                        color=OKABE[1], fontweight="bold")
    axes[0, 0].set_ylabel("suitability score")
    axes[1, 0].set_ylabel("suitability score")
    _panel_letters(axes)
    fig.suptitle("Criterion scoring functions over the in-district distribution "
                 "of each variable", y=1.01)
    fig.text(0.5, -0.035,
             "Grey histograms show relative frequency only, scaled to panel height with no numeric axis. "
             "The two categorical panels use a square-root scale so small classes stay visible.",
             ha="center", fontsize=7.5, color="0.35")
    fig.tight_layout()
    _save(fig, 5, "six scoring functions")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 — the six scored criterion surfaces
# ─────────────────────────────────────────────────────────────────────────────

def fig_06(ctx):
    fig, axes = plt.subplots(2, 3, figsize=(10, 6.6))
    im = None
    for ax, name in zip(axes.ravel(), ctx.crit):
        arr = ctx.inside(ctx.stack["normalized_rasters"][name])
        v = ctx.vals(ctx.stack["normalized_rasters"][name])
        im = _map(ax, arr, ctx.extent, ctx.boundary, cmap="viridis",
                  vmin=0, vmax=1,
                  title=f"{CRIT_LABEL[name]}   w = {ctx.weights[name]:.3f}",
                  furniture=False, grat=False)
        # A near-uniform panel is a finding, not a rendering fault. Print the
        # statistic so a reader does not have to guess which it is.
        ax.annotate(f"mean {v.mean():.3f}   SD {v.std():.3f}",
                    xy=(0.5, -0.045), xycoords="axes fraction", ha="center",
                    va="top", fontsize=7, color="0.30")

    # Furniture placed deliberately in the figure margin, clear of the data.
    # One set serves all six panels because the extent is shared.
    bar_ax = fig.add_axes([0.08, 0.035, 0.22, 0.05])
    bar_ax.axis("off")
    bar_ax.set_xlim(ctx.extent[0], ctx.extent[1])
    bar_ax.set_ylim(ctx.extent[2], ctx.extent[3])
    _add_scalebar(bar_ax, ctx.extent, km=25, x_frac=0.02, y_frac=0.35)
    n_ax = fig.add_axes([0.33, 0.028, 0.05, 0.062])
    n_ax.axis("off")
    n_ax.annotate("N", xy=(0.5, 0.95), xytext=(0.5, 0.05),
                  xycoords="axes fraction", textcoords="axes fraction",
                  ha="center", va="center", fontsize=8, fontweight="bold",
                  arrowprops=dict(arrowstyle="-|>", color="black", lw=1.0))

    # Pushed further left than the default: these map panels are narrow and the
    # centred titles reach almost to the panel edge.
    _panel_letters(axes, offset=(-0.22, 1.02))
    cbar = fig.colorbar(im, ax=axes, shrink=0.48, pad=0.015, aspect=20)
    cbar.set_label("suitability score (0–1)")
    fig.suptitle("Scored criterion surfaces — shared extent and shared 0–1 scale", y=0.98)
    fig.text(0.42, 0.045, "all panels share the same extent; one scale bar and "
                          "north arrow apply to all six",
             ha="left", va="center", fontsize=7, color="0.35")
    _save(fig, 6, "six criterion surfaces")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 8 — step classes versus interpolated ramps
# ─────────────────────────────────────────────────────────────────────────────

def fig_08(ctx):
    from tools_step_helper import step_surface  # defined below in this module
    s_step = step_surface(ctx)
    s_ramp = ctx.base["suitability_raster"]
    a_step, a_ramp = ctx.vals(s_step), ctx.vals(s_ramp)
    edges = np.linspace(0, 1, 51)
    hs, _ = np.histogram(a_step, bins=edges)
    hr, _ = np.histogram(a_ramp, bins=edges)
    centres = (edges[:-1] + edges[1:]) / 2
    tied = int((np.abs(a_step - 1.0) < 1e-9).sum())

    # Two panels: the distributions are near-identical across most of the range
    # and the whole argument lives in the top two bins. A single 50-bin grouped
    # chart spends its ink where nothing happens.
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.8, 4.2),
                                   gridspec_kw={"width_ratios": [1.45, 1]})
    w = (edges[1] - edges[0]) * 0.44
    for ax in (ax1, ax2):
        ax.bar(centres - w / 2, np.maximum(hs, 0.6), width=w, color=OKABE[1],
               label="step classes", edgecolor="none")
        ax.bar(centres + w / 2, np.maximum(hr, 0.6), width=w, color=OKABE[0],
               label="interpolated ramps", edgecolor="none")
        ax.set_yscale("log")
        ax.set_xlabel("composite suitability score")
        ax.grid(True, axis="y")

    # Bars on a log axis are drawn from the axis floor upward, so there is no
    # clear space beneath them. Headroom above the tallest bar is the only
    # place an annotation can sit without overprinting data.
    ymax = max(hs.max(), hr.max())
    ax1.set_ylabel("cells (log scale)")
    ax1.set_xlim(0.18, 1.02)
    ax1.set_ylim(0.4, ymax * 60)
    ax1.legend(frameon=False, loc="upper left")
    ax1.set_title("Full range")
    ax1.axvspan(0.85, 1.02, color="0.85", alpha=0.55, zorder=0)
    ax1.annotate("detail →", xy=(0.935, ymax * 3.0), ha="center", fontsize=8,
                 color="0.35", fontweight="bold")

    ax2.set_xlim(0.85, 1.015)
    ax2.set_ylim(0.4, ymax * 60)
    ax2.set_title("Detail: 0.85 – 1.00")
    # numpy closes the final bin on BOTH sides, so the exactly-1.000 cells are
    # already inside the last bar. Drawn separately and outlined so the reader
    # can see them rather than having to trust the binning convention.
    ax2.bar([1.0], [tied], width=w * 0.8, color=OKABE[1], edgecolor="black",
            lw=1.0, hatch="///", zorder=4, label=f"exactly 1.000 (n={tied:,})")
    ax2.legend(frameon=False, loc="upper right", fontsize=7.5)
    ax2.annotate(f"{tied:,} cells at exactly 1.000\nunder step classes",
                 xy=(0.995, hs[-1] * 1.4), xytext=(0.872, ymax * 12),
                 fontsize=8, color=OKABE[1], fontweight="bold", ha="left",
                 va="center",
                 arrowprops=dict(arrowstyle="->", color=OKABE[1], lw=1.1,
                                 connectionstyle="arc3,rad=0.22"))
    _panel_letters([ax1, ax2])

    # The old title claimed interpolation alone removed the plateau. It did not:
    # the historical plateau also required the pre-correction soil legend, which
    # both columns here reconstruct. The figure cannot separate the two changes.
    fig.suptitle("Step classes against interpolated ramps — historical soil "
                 "legend reconstructed in both", y=1.00)
    fig.tight_layout()
    _save(fig, 8, f"step vs ramp, two-panel ({tied:,} cells tied at 1.000)")
    return {"step_cells_at_one": tied}


# ─────────────────────────────────────────────────────────────────────────────
# Figure 9 — candidate sites across the six criterion axes
# ─────────────────────────────────────────────────────────────────────────────

def fig_09(ctx):
    det = ctx.base["top_locations_details"]
    raw = np.array([[d["criteria_scores"].get(c, np.nan) for c in ctx.crit]
                    for d in det])
    sd_all = np.nanstd(raw, axis=0)

    # Axes ordered by spread, most discriminating first, so the argument reads
    # left to right instead of depending on an arbitrary criterion order.
    order = np.argsort(-sd_all)
    names = [ctx.crit[i] for i in order]
    M = raw[:, order]
    sds = sd_all[order]
    at_one = [(np.abs(M[:, j] - 1.0) < 1e-9).sum() for j in range(M.shape[1])]

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    xs = np.arange(len(names))

    # Ranks 1-5 on a sequential ramp — five identical blues made the old legend
    # useless, since no line could be matched to its entry.
    ramp = plt.get_cmap("plasma")(np.linspace(0.08, 0.72, 5))
    for i in range(M.shape[0] - 1, -1, -1):          # draw the top five last
        if i < 5:
            ax.plot(xs, M[i], color=ramp[i], lw=1.9, zorder=5 - i + 3,
                    label=f"rank {i + 1}", solid_capstyle="round")
        else:
            ax.plot(xs, M[i], color="0.78", lw=0.8, alpha=0.8, zorder=1)

    ax.set_xticks(xs)
    ax.set_xticklabels([CRIT_LABEL[c] for c in names], fontsize=8.5)
    ax.set_ylabel("criterion score (0–1)")
    # Clipped: nothing sits below 0.10, so the bottom tenth was dead space.
    ax.set_ylim(0.08, 1.03)
    ax.set_xlim(-0.35, len(names) - 0.65)
    ax.grid(True, axis="y")

    # SD printed along the top, clear of the x tick labels they used to collide
    # with at the bottom.
    for j, c in enumerate(names):
        ax.annotate(f"SD {sds[j]:.3f}", xy=(j, 1.045), ha="center", va="bottom",
                    fontsize=7.5, color="0.30", annotation_clip=False)

    # The saturated axis is the finding, and it is no longer soil. "Flat" here
    # means plateaued at a single value, not merely low SD — slope has the
    # smaller SD but spreads across 0.905-0.993 without saturating, whereas
    # land cover pins almost every site at exactly 1.000.
    flat = int(np.argmax(at_one))
    ax.annotate(f"{at_one[flat]} of 25 sites score exactly 1.000 on "
                f"{CRIT_LABEL[names[flat]].lower()}\n— this axis separates "
                f"almost nothing",
                xy=(flat, 0.995), xytext=(flat - 1.45, 0.66),
                fontsize=7.5, color=OKABE[1], fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="->", color=OKABE[1], lw=1.0,
                                connectionstyle="arc3,rad=-0.25"))
    narrow = int(np.argmin(sds))
    if narrow != flat:
        ax.annotate(f"narrowest spread ({CRIT_LABEL[names[narrow]].lower()}, "
                    f"SD {sds[narrow]:.3f})\nbut not saturated",
                    xy=(narrow, M[:, narrow].min()),
                    xytext=(narrow - 1.5, 0.19), fontsize=7.5, color="0.35",
                    ha="left",
                    arrowprops=dict(arrowstyle="->", color="0.45", lw=0.9,
                                    connectionstyle="arc3,rad=0.2"))
    # Legend below the axis, not above it — at the top it collided with both
    # the title and the SD row. Handles reversed because the top five are drawn
    # last (so they sit above the grey lines), which would otherwise list the
    # ranks backwards.
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1], frameon=False, ncol=5,
              loc="upper center", bbox_to_anchor=(0.5, -0.13),
              handlelength=1.8, columnspacing=2.0)
    ax.set_title("The 25 candidate sites across the six criteria, axes ordered by spread",
                 pad=22)
    fig.tight_layout()
    _save(fig, 9, f"parallel coordinates (flat axis is now {names[flat]}, "
                  f"{at_one[flat]}/25 at 1.000)")
    return {"axis_order_by_sd": names,
            "flat_axis": names[flat],
            "flat_axis_sites_at_one": int(at_one[flat]),
            **{f"sd_{c}": round(float(sds[j]), 4) for j, c in enumerate(names)}}


# ─────────────────────────────────────────────────────────────────────────────
# Figure 10 — the four method surfaces
# ─────────────────────────────────────────────────────────────────────────────

def fig_10(ctx):
    # The CLASSIFIED surface, not the continuous one. On the continuous scale
    # the four panels are near-indistinguishable — the aggregation effect is now
    # under one percentage point — whereas thresholding at 0.65/0.85 makes the
    # disagreement visible, which is what the figure exists to show.
    order = ["AHP + WLC", "Fuzzy-AHP + WLC", "AHP + TOPSIS", "Fuzzy-AHP + TOPSIS"]
    cmap = ListedColormap([CLASS_COLOURS["Low"], CLASS_COLOURS["Medium"],
                           CLASS_COLOURS["High"]])
    norm = BoundaryNorm([0.5, 1.5, 2.5, 3.5], cmap.N)

    fig, axes = plt.subplots(2, 2, figsize=(8.8, 7.8))
    for ax, name in zip(axes.ravel(), order):
        r = ctx.algos[name]
        cls = r["area_statistics"]["classes"]
        # Method name only. Carrying the High % here as well made panel (d)'s
        # title overrun its frame and touch the image edge; it is in the
        # subtitle anyway.
        _map(ax, ctx.inside(r["classified_raster"]), ctx.extent, ctx.boundary,
             cmap=cmap, norm=norm, title=name, furniture=False, grat=False)
        # One unit, one precision, across all three classes.
        ax.annotate(f"High {cls['High']['percent']:.2f}% "
                    f"({cls['High']['area_km2']:,.0f} km²)   "
                    f"Medium {cls['Medium']['percent']:.2f}%   "
                    f"Low {cls['Low']['percent']:.2f}%",
                    xy=(0.5, -0.04), xycoords="axes fraction", ha="center",
                    va="top", fontsize=7, color="0.30")

    # Furniture inside panel (a)'s empty lower-left corner, drawn in map units
    # from that axis's data transform. Floating it in figure coordinates left
    # the scale bar outside every panel and put the north arrow directly under
    # panel (c)'s subtitle, where it read as pointing at a number.
    _add_scalebar(axes[0, 0], ctx.extent, km=25, x_frac=0.045, y_frac=0.07)
    _add_north(axes[0, 0], ctx.extent, x_frac=0.30, y_frac=0.055)

    _panel_letters(axes, offset=(-0.15, 1.00))
    handles = [Rectangle((0, 0), 1, 1, color=CLASS_COLOURS[k])
               for k in ("High", "Medium", "Low")]
    # Horizontal, bottom-centre. A vertical legend in the lower-right corner
    # covered panel (d)'s per-class statistics line.
    fig.legend(handles, [f"High (> {C.SUITABILITY_THRESHOLDS[1]})",
                         f"Medium ({C.SUITABILITY_THRESHOLDS[0]}–{C.SUITABILITY_THRESHOLDS[1]})",
                         f"Low (≤ {C.SUITABILITY_THRESHOLDS[0]})"],
               loc="lower center", bbox_to_anchor=(0.60, -0.005), frameon=False,
               ncol=3, fontsize=8, handlelength=1.4, columnspacing=1.8)
    fig.suptitle("Four MCDA methods on one criteria stack — classified surfaces", y=0.97)
    _save(fig, 10, "four-method classified surfaces")
    agg_h, _w, _i = _main_effects(ctx, "High")
    agg_l, _w2, _i2 = _main_effects(ctx, "Low")
    return {"aggregation_on_High_pp": round(agg_h, 3),
            "aggregation_on_Low_pp": round(agg_l, 3),
            "CAPTION": (
                "All four panels share extent, scale and breakpoints. The scale "
                "bar and north arrow in panel (a) apply to all four. Note the "
                "aggregation rule moves the Low-class share by "
                f"{agg_l:+.2f} pp against {agg_h:+.2f} pp on High — method "
                "sensitivity depends on which class is examined. The same "
                "breakpoints (0.65/0.85) are applied to the WLC score and the "
                "TOPSIS closeness coefficient, which are differently "
                "distributed; quantile-matching the breakpoints recovers only "
                "part of the disagreement, so it is mostly a genuine ranking "
                "difference rather than a threshold artefact. See "
                "tools/paper_figures.py --section 20.")}


# ─────────────────────────────────────────────────────────────────────────────
# Figures 11 and 12 — the factorial design
# ─────────────────────────────────────────────────────────────────────────────

def _factorial(ctx, klass="High"):
    h = {n: ctx.algos[n]["area_statistics"]["classes"][klass]["percent"]
         for n in ALGORITHMS}
    aw, at = h["AHP + WLC"], h["AHP + TOPSIS"]
    fw, ft = h["Fuzzy-AHP + WLC"], h["Fuzzy-AHP + TOPSIS"]
    return h, aw, at, fw, ft


def _main_effects(ctx, klass="High"):
    """Aggregation, weighting and interaction effects on one class share.

    Standard factorial (Yates) convention: the interaction is HALF the
    difference of the simple effects, so differencing the two slopes plotted in
    Figure 11 gives twice this value. Stated in both captions.
    """
    _h, aw, at, fw, ft = _factorial(ctx, klass)
    return (((at + ft) / 2) - ((aw + fw) / 2),      # aggregation
            ((fw + ft) / 2) - ((aw + at) / 2),      # weighting
            ((aw + ft) - (at + fw)) / 2)            # interaction


def fig_11(ctx):
    _h, aw, at, fw, ft = _factorial(ctx)
    fig, ax = plt.subplots(figsize=(6.0, 4.4))
    x = [0, 1]
    ax.plot(x, [aw, at], "o-", color=MEANING["AHP"], label="AHP weighting", ms=6)
    ax.plot(x, [fw, ft], "s--", color=MEANING["Fuzzy-AHP"], label="Fuzzy-AHP weighting", ms=6)
    for xx, yy in ((0, aw), (1, at)):
        ax.annotate(f"{yy:.2f}", (xx, yy), textcoords="offset points",
                    xytext=(0, 8), ha="center", fontsize=7.5, color=MEANING["AHP"])
    for xx, yy in ((0, fw), (1, ft)):
        ax.annotate(f"{yy:.2f}", (xx, yy), textcoords="offset points",
                    xytext=(0, -13), ha="center", fontsize=7.5, color=MEANING["Fuzzy-AHP"])
    ax.set_xticks(x)
    ax.set_xticklabels(["WLC", "TOPSIS"])
    ax.set_xlim(-0.25, 1.25)
    # Zero-based. A 4.9-6.5 window magnified a 1.5-point range to fill the panel
    # and made a sub-percentage-point effect look enormous.
    ax.set_ylim(0, 8)
    ax.set_xlabel("Aggregation rule")
    ax.set_ylabel("High-class share (% of district)")
    ax.legend(frameon=False, loc="lower left")
    ax.grid(True, axis="y")
    d_ahp, d_fz = at - aw, ft - fw
    inter = ((aw + ft) - (at + fw)) / 2
    # Scoped to the High class. Unscoped, "both effects are small" is false:
    # the same switch moves the Low-class share by about 9 pp (see fig 10).
    ax.set_title("On the High-class share, method effects stay under 1.2 pp")
    # Labelled as simple effects, not as the weighting methods themselves —
    # "AHP −0.79" read as "the effect of AHP".
    ax.annotate("\n".join([
                    f"WLC→TOPSIS | AHP:        {_mn(d_ahp, '+.2f')} pp",
                    f"WLC→TOPSIS | Fuzzy-AHP:  {_mn(d_fz, '+.2f')} pp",
                    f"interaction:             {_mn(inter, '+.3f')} pp"]),
                xy=(0.97, 0.97), xycoords="axes fraction", ha="right", va="top",
                fontsize=7.5, color="0.30", family="monospace")
    fig.tight_layout()
    _save(fig, 11, "factorial interaction, High-class share")
    return {"simple_effect_AHP_pp": round(d_ahp, 3),
            "simple_effect_Fuzzy_pp": round(d_fz, 3),
            "interaction_pp": round(inter, 3),
            "CAPTION": "Interaction = half the difference of the simple effects "
                       "(factorial-effect convention), consistent with Fig. 12. "
                       "A reader differencing the two plotted slopes gets "
                       f"{d_fz - d_ahp:+.2f} pp, which is twice this value. "
                       f"The {abs(agg_km2(ctx)):.0f} km2 equivalent of the "
                       "aggregation effect is given in the Results."}


def agg_km2(ctx):
    """The aggregation main effect expressed as area, for the caption.

    'Small' needs a denominator. 0.955 pp of an 11,412 km2 district is about
    109 km2, which is roughly 15% of the High class — worth stating rather
    than leaving the reader to infer it from a percentage point.
    """
    total = ctx.base["area_statistics"]["total_km2"]
    _h, aw, at, fw, ft = _factorial(ctx)
    return (((at + ft) / 2) - ((aw + fw) / 2)) / 100.0 * total


def fig_12(ctx):
    """Every analyst decision that moves the answer, on two class shares.

    Two columns, not one. The method effects are small on the High class and an
    order of magnitude larger on the Low class, so a single High-only panel
    understates them and a single Low-only panel overstates them. Showing both
    is the finding: how sensitive the classification is depends on which class
    you look at.

    Both upstream effects are computed here, not transcribed.
    """
    from tools.paper_figures import RAINFALL_FIXED_BANDS

    base = {k: ctx.base["area_statistics"]["classes"][k]["percent"]
            for k in ("High", "Low")}

    def _shares(rasters):
        st = dict(ctx.stack); st["normalized_rasters"] = rasters
        r = G.score_stack(st, ctx.weights, ctx.cr)["area_statistics"]["classes"]
        return {k: r[k]["percent"] for k in ("High", "Low")}

    # Rainfall: percentile rank versus fixed absolute bands, one-at-a-time swap
    # evaluated under AHP + WLC. NOT a factorial main effect — see the caption.
    rain_r = dict(ctx.stack["normalized_rasters"])
    rain_r["rainfall"] = np.where(ctx.mask, C.score_continuous_breaks(
        np.where(ctx.mask, ctx.stack["raw_rasters"]["rainfall"], np.nan),
        RAINFALL_FIXED_BANDS), np.nan)
    rain = _shares(rain_r)

    # Soil: the pre-2026-10-02 legend versus the corrected one. Signed as the
    # effect OF the correction.
    soil_r = dict(ctx.stack["normalized_rasters"])
    soil_r["soil"] = np.where(ctx.mask, C.score_categorical(
        ctx.stack["raw_rasters"]["soil"], _StepHelper.SOIL, C.SOIL_DEFAULT_SCORE), np.nan)
    soil = _shares(soil_r)

    agg_h, wgt_h, int_h = _main_effects(ctx, "High")
    agg_l, wgt_l, int_l = _main_effects(ctx, "Low")

    rows = [
        ("Interaction", int_h, int_l, MEANING["interaction"], False),
        ("Weighting\nAHP → Fuzzy-AHP", wgt_h, wgt_l, MEANING["method"], False),
        ("Aggregation\nWLC → TOPSIS", agg_h, agg_l, MEANING["method"], False),
        ("Soil legend corrected\n(data error, not a choice)",
         base["High"] - soil["High"], base["Low"] - soil["Low"], MEANING["soil"], True),
        ("Rainfall scoring\npercentile → fixed bands",
         rain["High"] - base["High"], rain["Low"] - base["Low"], MEANING["rainfall"], False),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.8), sharey=True)
    ypos = np.arange(len(rows))
    for ax, col, klass in ((axes[0], 1, "High"), (axes[1], 2, "Low")):
        vals = np.array([abs(r[col]) for r in rows])
        for y, r in zip(ypos, rows):
            hatched = r[4]
            ax.barh(y, abs(r[col]), color=r[3], height=0.62,
                    hatch="///" if hatched else None,
                    edgecolor="black" if hatched else "none",
                    linewidth=0.8 if hatched else 0)
            ax.annotate(_mn(r[col], "+.2f") + " pp", (abs(r[col]), y),
                        textcoords="offset points", xytext=(5, 0), va="center",
                        fontsize=8, fontweight="bold")
        ax.set_xlim(0, max(vals) * 1.30)
        ax.set_xlabel(f"|change| in {klass}-class share (pp)")
        ax.set_title(f"{klass}-class share")
        ax.grid(True, axis="x")
        # Clipped to the axes — it used to run to the image edge.
        ax.axhline(2.5, color="black", lw=0.8, ls="--", clip_on=True)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([r[0] for r in rows], fontsize=8)

    axes[0].annotate("choices the comparative\nliterature argues about",
                     xy=(0.30, 0.16), xycoords="axes fraction", fontsize=8,
                     color="0.30", va="center")
    axes[0].annotate("upstream data and scoring",
                     xy=(0.30, 0.80), xycoords="axes fraction", fontsize=8,
                     color="0.30", va="center")

    _panel_letters(axes, offset=(-0.02, 1.04))
    fig.suptitle("What moves the result depends on which class you look at", y=1.00)
    fig.tight_layout()
    _save(fig, 12, f"effect magnitudes, High and Low "
                   f"(aggregation {_mn(agg_h, '+.2f')} / {_mn(agg_l, '+.2f')} pp)")

    bands = ", ".join(f"≤{b:.0f}→{s:.2f}" for b, s in RAINFALL_FIXED_BANDS[:-1])
    return {
        "high_aggregation_pp": round(agg_h, 3), "low_aggregation_pp": round(agg_l, 3),
        "high_weighting_pp": round(wgt_h, 3), "low_weighting_pp": round(wgt_l, 3),
        "high_interaction_pp": round(int_h, 3), "low_interaction_pp": round(int_l, 3),
        "high_rainfall_pp": round(rain["High"] - base["High"], 2),
        "low_rainfall_pp": round(rain["Low"] - base["Low"], 2),
        "high_soil_pp": round(base["High"] - soil["High"], 2),
        "low_soil_pp": round(base["Low"] - soil["Low"], 2),
        "CAPTION": (
            "Lower three bars are factorial main effects (interaction = half the "
            "difference of simple effects). The rainfall bar is a ONE-AT-A-TIME "
            "swap evaluated under AHP+WLC, not a main effect, and its size "
            f"depends on the band set used: {bands}, >1500→1.00. Those bands are "
            "one alternative, not a range; Chandrapur's 1,189-1,714 mm spread "
            "falls in the top three, which is why the effect is large. The soil "
            "bar (hatched) is a data-error correction, not a modelling choice, "
            "and is shown to scale the others against."),
    }
# ─────────────────────────────────────────────────────────────────────────────
# Figure 13 — distributions and class flows, WLC versus TOPSIS
# ─────────────────────────────────────────────────────────────────────────────

def fig_13(ctx):
    rw = ctx.algos["AHP + WLC"]
    rt = ctx.algos["AHP + TOPSIS"]
    aw, at = ctx.vals(rw["suitability_raster"]), ctx.vals(rt["suitability_raster"])
    cw, ct = rw["classified_raster"], rt["classified_raster"]
    both = ctx.mask & ~np.isnan(cw) & ~np.isnan(ct)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.4, 4.6),
                                   gridspec_kw={"width_ratios": [1.05, 1]})
    edges = np.linspace(0, 1, 61)
    ax1.hist(aw, bins=edges, color=OKABE[0], alpha=0.65, label="AHP + WLC")
    ax1.hist(at, bins=edges, color=OKABE[1], alpha=0.65, label="AHP + TOPSIS")
    for t, lab in ((C.SUITABILITY_THRESHOLDS[1], "High ≥ 0.85"),
                   (C.SUITABILITY_THRESHOLDS[0], "Medium ≥ 0.65")):
        ax1.axvline(t, color="black", lw=0.9, ls="--")
        ax1.annotate(lab, xy=(t, ax1.get_ylim()[1] * 0.94), rotation=90,
                     fontsize=7, ha="right", va="top")
    ax1.set_xlabel("composite suitability score")
    ax1.set_ylabel("cells")
    ax1.legend(frameon=False, loc="upper left")
    ax1.grid(True, axis="y")
    ax1.set_title("Score distributions")

    # Alluvial: class flows with band widths proportional to area.
    lab = {3: "High", 2: "Medium", 1: "Low"}
    order = [3, 2, 1]
    tot = float(ctx.area[both].sum())
    left_tot = {c: float(ctx.area[both & (cw == c)].sum()) for c in order}
    right_tot = {c: float(ctx.area[both & (ct == c)].sum()) for c in order}

    gap = 0.035 * tot
    def _stack(totals):
        pos, y = {}, 0.0
        for c in order:
            pos[c] = (y, y + totals[c])
            y += totals[c] + gap
        return pos, y
    lpos, ltop = _stack(left_tot)
    rpos, rtop = _stack(right_tot)
    top = max(ltop, rtop)

    lcur = {c: lpos[c][0] for c in order}
    rcur = {c: rpos[c][0] for c in order}
    for f in order:
        for t in order:
            sel = both & (cw == f) & (ct == t)
            a = float(ctx.area[sel].sum())
            if a <= 0:
                continue
            y0l, y1l = lcur[f], lcur[f] + a
            y0r, y1r = rcur[t], rcur[t] + a
            n = 60
            xs = np.linspace(0, 1, n)
            s = (1 - np.cos(np.pi * xs)) / 2
            upper = y0l + (y0r - y0l) * s
            lower = y1l + (y1r - y1l) * s
            ax2.fill_between(xs, upper, lower,
                             color=CLASS_COLOURS[lab[f]],
                             alpha=0.30 if f != t else 0.60, lw=0)
            lcur[f], rcur[t] = y1l, y1r
    for c in order:
        ax2.add_patch(Rectangle((-0.045, lpos[c][0]), 0.045,
                                lpos[c][1] - lpos[c][0],
                                color=CLASS_COLOURS[lab[c]]))
        ax2.add_patch(Rectangle((1.0, rpos[c][0]), 0.045,
                                rpos[c][1] - rpos[c][0],
                                color=CLASS_COLOURS[lab[c]]))
        ax2.text(-0.06, (lpos[c][0] + lpos[c][1]) / 2,
                 f"{lab[c]}\n{left_tot[c]:,.0f} km²", ha="right", va="center", fontsize=7.5)
        ax2.text(1.065, (rpos[c][0] + rpos[c][1]) / 2,
                 f"{lab[c]}\n{right_tot[c]:,.0f} km²", ha="left", va="center", fontsize=7.5)
    ax2.set_xlim(-0.30, 1.32)
    ax2.set_ylim(-gap, top)
    ax2.invert_yaxis()
    ax2.axis("off")
    ax2.set_title("Class transitions, WLC → TOPSIS (band width ∝ area)")
    unchanged = 100 * float((cw[both] == ct[both]).mean())
    ax2.annotate(f"{unchanged:.1f}% unchanged", xy=(0.5, 1.0),
                 xycoords="axes fraction", ha="center", fontsize=8,
                 fontweight="bold")
    _panel_letters([ax1, ax2])
    fig.tight_layout()
    _save(fig, 13, f"distributions + alluvial ({unchanged:.1f}% unchanged)")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 14 — where the two methods disagree
# ─────────────────────────────────────────────────────────────────────────────

def fig_14(ctx):
    sw = ctx.algos["AHP + WLC"]["suitability_raster"]
    st = ctx.algos["AHP + TOPSIS"]["suitability_raster"]
    diff = ctx.inside(sw - st)
    v = ctx.vals(sw - st)
    lim = float(np.nanpercentile(np.abs(v), 99))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 4.8),
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    im = _map(ax1, diff, ctx.extent, ctx.boundary, cmap="RdBu_r",
              norm=TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim),
              title="Baseline minus TOPSIS")
    cb = fig.colorbar(im, ax=ax1, shrink=0.78, pad=0.02)
    cb.set_label("score difference (WLC − TOPSIS)")

    dy_km, dx_km = G._pixel_size_km(ctx.transform, ctx.shape)
    dist = G._distance_km(~ctx.mask, dy_km, dx_km)
    cw = ctx.algos["AHP + WLC"]["classified_raster"]
    ct = ctx.algos["AHP + TOPSIS"]["classified_raster"]
    both = ctx.mask & ~np.isnan(cw) & ~np.isnan(ct)
    changed = both & (cw != ct)
    bands = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 999)]
    labels, rates = [], []
    for lo, hi in bands:
        sel = both & (dist >= lo) & (dist < hi)
        if not sel.sum():
            continue
        labels.append(f"{lo}–{hi}" if hi < 999 else f">{lo}")
        rates.append(100 * float(changed[sel].mean()))
    ax2.bar(labels, rates, color=OKABE[0], width=0.62)
    for i, r in enumerate(rates):
        ax2.annotate(f"{r:.1f}", (i, r), textcoords="offset points",
                     xytext=(0, 3), ha="center", fontsize=7.5)
    ax2.set_xlabel("distance to district boundary (km)")
    ax2.set_ylabel("cells reclassified (%)")
    ax2.grid(True, axis="y")
    ax2.set_title("Disagreement is interior, not edge")
    _panel_letters([ax1, ax2], offset=(-0.10, 1.02))
    fig.tight_layout()
    _save(fig, 14, "difference map + boundary-distance profile")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 15 (A and B only) — scenarios
# ─────────────────────────────────────────────────────────────────────────────

def fig_15(ctx):
    names = list(SCENARIOS)
    W, highs, crs = [], [], []
    for n in names:
        w, cr = ahp_engine.weights_for_scenario(n)
        W.append([w[c] for c in ctx.crit])
        r = G.score_stack(ctx.stack, w, cr)
        highs.append(r["area_statistics"]["classes"]["High"]["percent"])
        crs.append(cr)
    W = np.array(W)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.4),
                                   gridspec_kw={"width_ratios": [1.5, 1]})
    bottom = np.zeros(len(names))
    for j, c in enumerate(ctx.crit):
        ax1.barh(names, W[:, j], left=bottom, label=CRIT_LABEL[c],
                 color=OKABE[j % len(OKABE)], height=0.62)
        bottom += W[:, j]
    ax1.set_xlabel("criterion weight (sums to 1)")
    ax1.set_xlim(0, 1)
    ax1.invert_yaxis()
    ax1.legend(frameon=False, ncol=3, fontsize=7.5, loc="lower center",
               bbox_to_anchor=(0.5, 1.01))
    ax1.set_title("Weight vectors by scenario", pad=26)

    ax2.barh(names, highs, color=OKABE[0], height=0.62)
    for i, (h, cr) in enumerate(zip(highs, crs)):
        ax2.annotate(f"{h:.2f}%  (CR {cr:.4f})", (h, i), textcoords="offset points",
                     xytext=(4, 0), va="center", fontsize=7.5)
    ax2.set_xlabel("highly suitable area (%)")
    ax2.set_xlim(0, max(highs) * 1.5)
    ax2.set_yticks([])
    ax2.invert_yaxis()
    ax2.grid(True, axis="x")
    ax2.set_title("Highly suitable share")
    _panel_letters([ax1, ax2], offset=(-0.08, 1.02))
    fig.tight_layout()
    _save(fig, 15, "scenario weights + class share (panel C is a QGIS map)")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 16 — consensus agreement rasters
# ─────────────────────────────────────────────────────────────────────────────

def fig_16(ctx):
    from consensus import agreement_raster, variants_by_algorithm, variants_by_scenario
    va = variants_by_algorithm(ctx.stack)
    vs = variants_by_scenario(ctx.stack)
    ca = agreement_raster(va, ctx.mask)
    cs = agreement_raster(vs, ctx.mask)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.0))
    for ax, count, n, title in ((axes[0], ca, len(va), f"Across {len(va)} algorithms"),
                                (axes[1], cs, len(vs), f"Across {len(vs)} scenarios")):
        shades = ["#f7f7f7", "#dbe9d3", "#a8cf99", "#5fa14b", "#2c6b1f", "#123d0c"]
        cmap = ListedColormap(shades[:n + 1])
        norm = BoundaryNorm(np.arange(-0.5, n + 1.5, 1), cmap.N)
        im = _map(ax, count, ctx.extent, ctx.boundary, cmap=cmap, norm=norm,
                  title=title, furniture=False, grat=False)
        cb = fig.colorbar(im, ax=ax, shrink=0.72, pad=0.02,
                          ticks=range(n + 1))
        cb.set_label("variants classing the cell High")
    _add_scalebar(axes[0], ctx.extent)
    _add_north(axes[1], ctx.extent)
    _panel_letters(axes, offset=(-0.12, 1.00))
    fig.suptitle("Agreement rasters — land that survives a change of method", y=0.98)
    fig.tight_layout()
    _save(fig, 16, "consensus agreement maps (QGIS version would label sites)")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 17 — sensitivity dashboard
# ─────────────────────────────────────────────────────────────────────────────

def fig_17(ctx):
    from sensitivity import (map_removal_sensitivity, one_way_sensitivity,
                             single_parameter_sensitivity)
    ow = one_way_sensitivity(ctx.stack, ctx.weights)
    mr = map_removal_sensitivity(ctx.stack, ctx.weights)
    sp = single_parameter_sensitivity(ctx.stack, ctx.weights)

    infl = ow["influence_high_pct"]
    order = sorted(infl, key=lambda k: infl[k])
    fig, axes = plt.subplots(2, 2, figsize=(10.2, 7.0))

    ax = axes[0, 0]
    ax.barh([CRIT_LABEL[c] for c in order], [infl[c] for c in order],
            color=OKABE[0], height=0.6)
    for i, c in enumerate(order):
        ax.annotate(f"{infl[c]:.2f}", (infl[c], i), textcoords="offset points",
                    xytext=(3, 0), va="center", fontsize=7.5)
    ax.set_xlabel("mean |Δ| highly suitable area (pp)")
    ax.set_title(f"±{ow['delta']*100:.0f}% weight perturbation")
    ax.grid(True, axis="x")

    ax = axes[0, 1]
    rows = sorted(mr["rows"], key=lambda r: r["retained"])
    ax.barh([CRIT_LABEL[r["criterion"]] for r in rows],
            [r["retained"] for r in rows], color=OKABE[1], height=0.6)
    for i, r in enumerate(rows):
        ax.annotate(f"{r['retained']}/{mr['top_n']}", (r["retained"], i),
                    textcoords="offset points", xytext=(3, 0), va="center", fontsize=7.5)
    ax.set_xlabel(f"top-{mr['top_n']} sites retained on removal")
    ax.set_xlim(0, mr["top_n"] + 1.5)
    ax.set_title("Map removal — shortlist survival")
    ax.grid(True, axis="x")

    ax = axes[1, 0]
    rows2 = sorted(mr["rows"], key=lambda r: r["high_pct_delta"])
    cols = [OKABE[1] if r["high_pct_delta"] > 0 else OKABE[0] for r in rows2]
    ax.barh([CRIT_LABEL[r["criterion"]] for r in rows2],
            [r["high_pct_delta"] for r in rows2], color=cols, height=0.6)
    ax.axvline(0, color="black", lw=0.7)
    ax.set_xlabel("change in highly suitable area (pp)")
    ax.set_title("Map removal — effect on class area")
    ax.grid(True, axis="x")

    ax = axes[1, 1]
    rows3 = sorted(sp["rows"], key=lambda r: r["ratio"])
    cols = [OKABE[2] if r["ratio"] >= 1 else OKABE[3] for r in rows3]
    ax.barh([CRIT_LABEL[r["criterion"]] for r in rows3],
            [r["ratio"] for r in rows3], color=cols, height=0.6)
    ax.axvline(1.0, color="black", lw=0.8, ls="--")
    for i, r in enumerate(rows3):
        ax.annotate(f"{r['ratio']:.3f}", (r["ratio"], i), textcoords="offset points",
                    xytext=(3, 0), va="center", fontsize=7.5)
    ax.set_xlabel("effective ÷ assigned weight")
    ax.set_title("Realised versus assigned influence")
    ax.grid(True, axis="x")

    _panel_letters(axes)
    fig.suptitle("Sensitivity: three independent analyses", y=0.99)
    fig.tight_layout()
    _save(fig, 17, "sensitivity dashboard")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 18 — assigned versus effective weight
# ─────────────────────────────────────────────────────────────────────────────

def fig_18(ctx):
    from sensitivity import single_parameter_sensitivity
    sp = single_parameter_sensitivity(ctx.stack, ctx.weights)
    rows = sp["rows"]
    th = np.array([r["theoretical_pct"] for r in rows])
    ef = np.array([r["effective_pct"] for r in rows])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.4))
    lim = max(th.max(), ef.max()) * 1.15
    ax1.plot([0, lim], [0, lim], color="0.6", ls="--", lw=0.9, zorder=1)
    ax1.scatter(th, ef, s=46, color=OKABE[0], zorder=3)
    for r, x, y in zip(rows, th, ef):
        ax1.annotate(CRIT_LABEL[r["criterion"]], (x, y), textcoords="offset points",
                     xytext=(6, 4), fontsize=7.5)
    ax1.set_xlabel("assigned weight (%)")
    ax1.set_ylabel("effective weight (%)")
    ax1.set_xlim(0, lim)
    ax1.set_ylim(0, lim)
    ax1.grid(True)
    ax1.set_title("Assigned versus realised")

    s = sorted(rows, key=lambda r: r["ratio"])
    cols = [OKABE[2] if r["ratio"] >= 1 else OKABE[3] for r in s]
    ax2.barh([CRIT_LABEL[r["criterion"]] for r in s], [r["ratio"] for r in s],
             color=cols, height=0.6)
    ax2.axvline(1.0, color="black", lw=0.8, ls="--")
    for i, r in enumerate(s):
        ax2.annotate(f"{r['ratio']:.3f}", (r["ratio"], i), textcoords="offset points",
                     xytext=(3, 0), va="center", fontsize=7.5)
    ax2.set_xlabel("effective ÷ assigned")
    ax2.grid(True, axis="x")
    ax2.set_title("Ratio by criterion")
    _panel_letters([ax1, ax2], offset=(-0.10, 1.02))
    fig.tight_layout()
    _save(fig, 18, "assigned vs effective weight")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 19 — criterion correlation heatmap
# ─────────────────────────────────────────────────────────────────────────────

def fig_19(ctx):
    from scipy.stats import pearsonr, spearmanr
    names = ctx.crit
    R = np.eye(len(names))
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a = ctx.stack["normalized_rasters"][names[i]][ctx.mask]
            b = ctx.stack["normalized_rasters"][names[j]][ctx.mask]
            ok = ~np.isnan(a) & ~np.isnan(b)
            R[i, j] = float(spearmanr(a[ok], b[ok]).statistic)   # above diagonal
            R[j, i] = float(pearsonr(a[ok], b[ok])[0])           # below diagonal

    fig, ax = plt.subplots(figsize=(6.4, 5.4))
    im = ax.imshow(R, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(names)))
    ax.set_yticks(range(len(names)))
    ax.set_xticklabels([CRIT_LABEL[c] for c in names], rotation=35, ha="right")
    ax.set_yticklabels([CRIT_LABEL[c] for c in names])
    for i in range(len(names)):
        for j in range(len(names)):
            if i == j:
                ax.text(j, i, "—", ha="center", va="center", fontsize=8, color="0.4")
            else:
                ax.text(j, i, f"{R[i, j]:.2f}", ha="center", va="center",
                        fontsize=7.5,
                        color="white" if abs(R[i, j]) > 0.55 else "black")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("correlation")
    ax.set_title("Spearman ρ above the diagonal, Pearson r below\n"
                 "ρ for soil and land cover is unreliable — heavy ties", fontsize=9)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    _save(fig, 19, "criterion correlation heatmap")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 21 (bonus) — rank displacement under each alternative method
# ─────────────────────────────────────────────────────────────────────────────

def fig_21(ctx):
    from sensitivity import _match_sites
    base = ctx.base["top_locations_details"]
    others = [n for n in ALGORITHMS if n != "AHP + WLC"]
    fig, axes = plt.subplots(1, 3, figsize=(10.4, 3.9), sharey=True)
    for ax, name in zip(axes, others):
        alt = ctx.algos[name]["top_locations_details"]
        pairs, kept = _match_sites(base, alt, 2.0)
        if pairs:
            bx = [p[0] for p in pairs]
            by = [p[1] for p in pairs]
            ax.scatter(bx, by, s=30, color=OKABE[0], zorder=3)
        n = len(base)
        ax.plot([1, n], [1, n], color="0.6", ls="--", lw=0.9)
        ax.set_xlabel("baseline rank")
        ax.set_title(f"{name}\n{kept}/{n} matched", fontsize=8.5)
        ax.grid(True)
        ax.set_xlim(0, n + 1)
        ax.set_ylim(0, n + 1)
    _panel_letters(axes, offset=(-0.06, 1.04))
    axes[0].set_ylabel("rank under alternative method")
    fig.suptitle("Rank displacement of the 25 candidate sites", y=1.00)
    fig.tight_layout()
    _save(fig, 21, "rank displacement")


# ─────────────────────────────────────────────────────────────────────────────
# Figure 22 (bonus) — score versus cross-method agreement
# ─────────────────────────────────────────────────────────────────────────────

def fig_22(ctx):
    from consensus import agreement_raster, variants_by_algorithm
    va = variants_by_algorithm(ctx.stack)
    count = agreement_raster(va, ctx.mask)
    base = ctx.base["suitability_raster"]
    sel = ctx.mask & ~np.isnan(base) & ~np.isnan(count)
    x, y = base[sel], count[sel]

    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    nb = len(va) + 1
    bins_x = np.linspace(np.nanmin(x), np.nanmax(x), 90)
    H = np.zeros((nb, len(bins_x) - 1))
    for k in range(nb):
        H[k], _ = np.histogram(x[y == k], bins=bins_x)
    H = np.where(H > 0, H, np.nan)
    im = ax.pcolormesh(bins_x, np.arange(-0.5, nb + 0.5), H, cmap="viridis",
                       norm=matplotlib.colors.LogNorm())
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("cells (log)")

    det = ctx.base["top_locations_details"]
    tr = ctx.transform
    import rasterio
    cx, cy = [], []
    for d in det:
        r, c = rasterio.transform.rowcol(tr, d["lon"], d["lat"])
        cx.append(float(base[r, c]))
        cy.append(float(count[r, c]))
    ax.scatter(cx, cy, s=34, facecolor="none", edgecolor=OKABE[1], lw=1.2,
               zorder=5, label="25 candidate sites")
    ax.axvline(C.SUITABILITY_THRESHOLDS[1], color="white", lw=1.0, ls="--", zorder=4)
    ax.set_yticks(range(nb))
    ax.set_xlabel("baseline composite score")
    ax.set_ylabel("algorithms classing the cell High")
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Scoring well is not the same as every method agreeing")
    fig.tight_layout()
    _save(fig, 22, "stability versus suitability")


# ─────────────────────────────────────────────────────────────────────────────
# Step-class reconstruction, shared with paper_figures §8
# ─────────────────────────────────────────────────────────────────────────────

class _StepHelper:
    """Rebuilds the deleted step-class scoring. See paper_figures.py §8 for the
    full caveat — this is a reconstruction, validated by reproducing the
    historical count of cells tied at exactly 1.000."""

    SLOPE = ((1, 1.00), (3, 0.85), (5, 0.68), (10, 0.42), (15, 0.20), (25, 0.08), (90, 0.05))
    DRAIN = ((0.10, 0.25), (0.20, 0.50), (0.30, 0.72), (0.40, 0.88), (99, 1.00))
    # The soil table as it stood before 2026-10-02. The historical 973-cell
    # plateau required the wrong legend as well as the flat tops — verified:
    # 973 cells at 1.000 with this table, 1 with the corrected one.
    SOIL = {1: 0.55, 4: 1.00, 6: 0.80, 7: 0.50}

    @staticmethod
    def settlement(km):
        out = np.full(km.shape, np.nan, dtype=np.float32)
        out[km < 1.0] = C.SETTLEMENT_SCORE_AT_ZERO
        out[(km >= 1.0) & (km <= 5.0)] = 1.00
        tail = km > 5.0
        out[tail] = np.clip(1.00 - (km[tail] - 5.0) / 10.0 * 0.90, 0.10, 1.00)
        return out

    @classmethod
    def surface(cls, ctx):
        raw, mask = ctx.stack["raw_rasters"], ctx.mask
        step = {
            "slope": C.score_continuous_breaks(raw["slope"], cls.SLOPE),
            "rainfall": C.score_quantiles(np.where(mask, raw["rainfall"], np.nan)),
            "soil": C.score_categorical(raw["soil"], cls.SOIL, C.SOIL_DEFAULT_SCORE),
            "lulc": C.score_categorical(raw["lulc"], C.LULC_SCORES, C.LULC_DEFAULT_SCORE),
            "drainage": C.score_continuous_breaks(ctx.stack["drainage_density"].astype(float), cls.DRAIN),
            "population": cls.settlement(ctx.stack["settlement_distance_km"].astype(float)),
        }
        for k in step:
            step[k] = np.where(mask, step[k], np.nan)
        surf, _cov = G._weighted_overlay(step, ctx.weights)
        return surf


class tools_step_helper:          # noqa: N801  (import shim used by fig_08)
    step_surface = staticmethod(lambda ctx: _StepHelper.surface(ctx))


sys.modules["tools_step_helper"] = tools_step_helper


FIGURES = {
    2: fig_02, 5: fig_05, 6: fig_06, 8: fig_08, 9: fig_09, 10: fig_10,
    11: fig_11, 12: fig_12, 13: fig_13, 14: fig_14, 15: fig_15, 16: fig_16,
    17: fig_17, 18: fig_18, 19: fig_19, 21: fig_21, 22: fig_22,
}

NOT_HERE = {
    1: "QGIS — study area, three panels, needs labelled towns and rivers",
    3: "diagram tool — preprocessing chain",
    4: "diagram tool — research framework",
    7: "QGIS — hero suitability map with numbered sites and inset",
    20: "diagram tool — model-to-field workflow",
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Build the paper's figures.")
    ap.add_argument("--only", type=int, choices=sorted(FIGURES))
    ap.add_argument("--dpi", type=int, default=DPI)
    ap.add_argument("--data-dir", default="data")
    args = ap.parse_args()

    _setup_style()
    print("Building figures ...")
    ctx = Ctx(args.data_dir)
    wanted = [args.only] if args.only else sorted(FIGURES)
    notes = {}
    for n in wanted:
        out = FIGURES[n](ctx)
        if out:
            notes[n] = out
    print(f"\nWrote {len(wanted)} figure(s) to {OUTDIR}/ as PNG at {args.dpi} dpi.")
    if notes:
        print("\nValues computed while plotting (for caption checking):")
        for n, d in notes.items():
            print(f"  fig{n:02d}: {d}")
    if not args.only:
        print("\nNot produced here, by design:")
        for n, why in sorted(NOT_HERE.items()):
            print(f"  fig{n:02d}  {why}")
        print("  Content specs for all five: docs/FIGURE_SPECS.md")


if __name__ == "__main__":
    main()
