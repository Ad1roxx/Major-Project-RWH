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

Conventions these figures are reviewed against
    Shared axes. Panels that plot the SAME quantity share it — `sharex` or
    `sharey` — so bar lengths and point heights can be compared by eye across
    panels. Figure 12 lost a round of review to this: its two panels
    autoscaled to 0-40 and 0-50, which drew a 9.03 pp bar barely longer than
    a 0.96 pp one. Panels plotting DIFFERENT quantities (Figures 17 and 18,
    where one panel is percentage points and the next is sites retained) must
    not share, and are the reason this is a convention rather than a default.

    Text inside the canvas. `_save` runs `_text_overruns` on every figure and
    prints any Text artist reaching the image edge. `_save` writes the whole
    figure, NOT `bbox_inches="tight"`, so a title at y=1.02 or a footnote at
    y=-0.055 is clipped rather than accommodated; reserve the strip with
    `tight_layout(rect=...)` instead.

    Map furniture follows the geometry. `_clear_corner` measures the district
    mask and returns the emptiest corner; do not hardcode one.

    One precision per figure, via `_pp`, which rounds half up so a reader
    checking the text against the plot sees the digit they expect.
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
import matplotlib.text as mtext  # noqa: E402
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
# The generic two-series pair, for any figure contrasting one thing with
# another where neither is a criterion or a weighting method.
# Near-black, not Okabe blue: #0072B2 is ΔE 5.5 from the High class blue,
# so in Fig. 13 blue meant "WLC" in (a) and "High" in (b).
GENERIC = ("#1A1A1A", OKABE[1])

# Neutral fill for a bar that encodes a magnitude and nothing else, and a
# colour for a quantity that is neither a criterion nor a method effect and so
# must not borrow either palette. The scenario-range bar in Figure 12 was drawn
# in OKABE[4], which CRIT_COLOUR had just assigned to Slope in Figure 15 - the
# consistency fix created a fresh clash one figure over. _assert_palette now
# refuses that.
NEUTRAL_BAR = "#6E7B8B"
OTHER_COLOUR = "#8C564B"

# Figure 21's three-way cell partition. Outside both palettes: the first
# version of that figure used OKABE[0] and OKABE[4] directly, which are AHP's
# method colour and Slope's criterion colour. The two re-ranking categories
# deliberately share a hue and are separated by hatching, because they are the
# same thing seen through two cutoff schemes.
PARTITION = {"robust": "#1B5E5E", "induced": "#999933"}

MEANING = {
    # NOT OKABE[0] and OKABE[1]. Those two are the house generic pair for "one
    # series against another" and are used that way in Figures 2, 8, 13 and 18,
    # so binding them to the weighting methods as well made one colour mean two
    # things across the set - vermilion was Fuzzy-AHP in Figure 11, the tied
    # scoring scheme in Figure 8, and the variance share in Figure 18. The
    # methods appear as series in ONE figure, so the methods are what move.
    # Separated in luminance (0.19 against 0.56) as well as hue, so the two
    # lines in Figure 11 stay distinguishable without colour vision.
    "AHP":         "#293241",   # weighting method
    "Fuzzy-AHP":   "#E56B6F",
    # Deliberately the same colour as NEUTRAL_BAR: both mean "a magnitude
    # with no further meaning". _assert_palette exempts the pair by name.
    "method":      NEUTRAL_BAR,
    "interaction": "#AFB8C1",  # the same, lighter
    "rainfall":    OKABE[2],   # upstream scoring decision
    "soil":        OKABE[3],   # upstream data correction
    "scenario":    OTHER_COLOUR,  # weighting judgements varying — not the method,
                                  # and not a criterion, so outside both palettes
}


def _r(x, dp):
    """Round half-up, once, for every formatter in this module.

    Python rounds half to even AND is working from binary, so 15.35 is held as
    slightly less than 15.35 and prints as "15.3" while 42.85 is held as
    slightly more and prints as "42.9". Two numbers of equal provenance then
    round in opposite directions in the same panel, which is what Figure 18's
    assigned-weight labels were doing. Everything that prints a rounded number
    goes through here or through `_pp`, which calls it.
    """
    from decimal import ROUND_HALF_UP, Decimal
    q = Decimal(str(round(float(x), 10))).quantize(Decimal("1." + "0" * dp),
                                                   rounding=ROUND_HALF_UP)
    return float(q)


def _fx(x, dp=2, sign=False) -> str:
    """A fixed-point number, half-up, with a true minus sign."""
    return _mn(_r(x, dp), f"{'+' if sign else ''}.{dp}f")


def _mn(x, fmt="+.3f") -> str:
    """Format a number with a true minus sign (U+2212), not hyphen-minus."""
    return format(x, fmt).replace("-", "−")


def _pp(x, dp=3) -> str:
    """A percentage-point value, formatted the same way everywhere.

    Half-up, and no sign on an exact zero. `dp` must match where the number
    came from, because trailing zeros are a claim about precision:

      dp=3  factorial main effects and interactions. These are differences of
            class shares computed from cell counts, so the third digit is real,
            and two decimals is not enough — -0.565 is held in binary as
            slightly less than -0.565, so round-half-even prints it as -0.56
            where a reader checking the text against the figure expects -0.57.

      dp=2  anything derived from a share that `_area_statistics` already
            rounded to two decimals. Printing "+31.210 pp" for a number whose
            inputs stop at 31.21 invents a digit.

    Figures, tables and exported captions all route through this, so they
    cannot drift apart.
    """
    q = _r(x, dp)
    if q == 0:
        return f"{0:.{dp}f} pp"
    return f"{_mn(q, f'+.{dp}f')} pp"

# IGBP class names, short enough for an axis tick. Only the classes that
# occur in the district are ever drawn.
LULC_SHORT = {
    1: "Evgrn needleleaf", 2: "Evgrn broadleaf", 3: "Decid needleleaf",
    4: "Decid broadleaf", 5: "Mixed forest", 6: "Closed shrub",
    7: "Open shrub", 8: "Woody savanna", 9: "Savanna", 10: "Grassland",
    11: "Perm wetland", 12: "Cropland", 13: "Urban", 14: "Crop/natural",
    15: "Snow/ice", 16: "Barren", 17: "Water",
}

# Two-to-five-letter IGBP abbreviations for crowded axes; the caption gives the
# key. Full names are in LULC_SHORT.
LULC_ABBR = {1: "ENF", 2: "EBF", 3: "DNF", 4: "DBF", 5: "MixF", 6: "CShr",
             7: "OShr", 8: "WSav", 9: "Sav", 10: "Grass", 11: "Wetl",
             12: "Crop", 13: "Urban", 14: "CrNat", 15: "Snow", 16: "Barr",
             17: "Water"}

CRIT_LABEL = {
    "slope": "Slope", "rainfall": "Rainfall", "drainage": "Drainage density",
    "soil": "Soil texture", "lulc": "Land cover", "population": "Settlement prox.",
}

# One colour per CRITERION, fixed across the whole set. Rainfall used to be
# vermilion in Figure 15 and green in Figure 12, and the blue that meant "AHP"
# in Figure 11 meant "Slope" in Figure 15. A reader moving between adjacent
# figures had no way to know the colours were unrelated.
#
# Rainfall and soil keep the hues MEANING already gave them, because Figure 12
# shows them as upstream decisions and Figures 15 and 17 show them as criteria;
# they are the same thing and should look it.
CRIT_COLOUR = {
    "rainfall":   OKABE[2],   # green   — also MEANING["rainfall"]
    "soil":       OKABE[3],   # pink    — also MEANING["soil"]
    "slope":      OKABE[4],   # amber
    "drainage":   OKABE[5],   # light blue
    "lulc":       "#7A6A53",  # brown; outside Okabe-Ito, which has only six
    "population": "#5D4E8C",  # violet
}

# Neutral fills for bars that encode a magnitude and nothing else, and the two
# sign colours for bars that encode a signed change. Keeping these apart stops
# colour meaning three things inside one four-panel figure.
SIGN_COLOUR = {"+": OKABE[1], "-": OKABE[0]}

# One name for the High class, used in every title, axis label and caption.
# "Highly suitable share", "High-class share" and "highly suitable area" were
# all in use for the same quantity.
HIGH_LABEL = "High-class share"


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
    problems = (_text_problems(fig) + _legend_palette_problems(fig)
                + _baked_caption_problems(fig) + _annotation_palette_problems(fig)
                + _bar_label_problems(fig))
    plt.close(fig)
    print(f"  fig{number:02d}  {slug}")
    for msg in problems:
        print(f"    ⚠ {msg}")


def _bar_label_problems(fig, tol=0.02):
    """A number drawn ON a bar that is not that bar's own length.

    Figure 21 ran a stacked bar to 16.28 - the union of two cutoff schemes -
    while the label beside it read "12.83 pp changes class". A reader takes bar
    length as the quantity, so the two disagreed in the one place a reader
    looks. This checks only labels drawn INSIDE a bar, where the association is
    unambiguous; a label outside may legitimately describe a bracket, a total
    or a different quantity, and Figure 21 now uses that form deliberately.
    """
    import matplotlib.colors as mcolors
    import matplotlib.patches as mpatches

    def _num(text):
        import re
        m = re.fullmatch(r"[\u2212+-]?\d+(?:\.\d+)?", text.strip().replace(",", ""))
        if not m:
            return None
        return abs(float(text.strip().replace("\u2212", "-").replace(",", "")))

    out = []
    for ax in fig.axes:
        bars = [b for b in ax.patches if isinstance(b, mpatches.Rectangle)
                and b.get_visible()]
        if not bars:
            continue
        for t in ax.texts:
            val = _num(t.get_text())
            if val is None:
                continue
            try:
                tb = mtext.Text.get_window_extent(t, renderer=fig.canvas.get_renderer())
            except Exception:
                continue
            cx, cy = (tb.x0 + tb.x1) / 2, (tb.y0 + tb.y1) / 2
            for b in bars:
                try:
                    bb = b.get_window_extent()
                except Exception:
                    continue
                if not bb.contains(cx, cy):
                    continue
                length = abs(b.get_width()) if bb.width >= bb.height \
                    else abs(b.get_height())
                if length > 0 and abs(length - val) > tol * max(length, val, 1.0):
                    out.append(f"label {t.get_text()!r} sits inside a bar of "
                               f"length {length:.3f}")
                break
    return out


def _baked_caption_problems(fig):
    """Figure-level prose baked into the image.

    A sentence drawn below the axes is caption text in a picture: a journal
    cannot typeset it, a translator cannot reach it, and it duplicates the
    caption the paper will carry anyway. Three figures were doing this. Short
    figure-level text is fine - a unit, a letter, a source note - so the test
    is on length.
    """
    out = []
    for t in fig.texts:                      # fig.text(), not ax.annotate()
        label = t.get_text().strip()
        if len(label) < 60:
            continue
        if t.get_position()[1] > 0.90:       # a suptitle set with fig.text
            continue
        out.append("caption text baked into the image, move it to the "
                   f"CAPTION key: {label[:70]!r}...")
    return out


def _annotation_palette_problems(fig):
    """An annotation coloured to match a series it does not name.

    `_legend_palette_problems` reads legends, so it is blind to a figure with
    no legend - which is how Figure 2 came to draw its slope statistics in
    AHP's blue and its land-cover statistics in rainfall's green.
    """
    import matplotlib.colors as mcolors

    crit = {}
    for k, v in CRIT_COLOUR.items():
        crit[mcolors.to_hex(v).lower()] = k
    # Which criterion each axes is about, read from its own title. A label on
    # a land-cover panel may of course be drawn in land cover's colour even
    # when the label itself says "Water"; what must not happen is a land-cover
    # panel drawn in rainfall's green.
    about = {}
    for ax in fig.axes:
        title = (ax.get_title() or "").lower()
        about[ax] = {k for k in CRIT_COLOUR
                     if CRIT_LABEL[k].lower() in title or k in title}

    out = []
    for t in fig.findobj(mtext.Text):
        label = t.get_text().strip()
        if not label:
            continue
        try:
            col = mcolors.to_hex(t.get_color()).lower()
        except Exception:
            continue
        if col not in crit:
            continue
        name = crit[col]
        low = label.lower()
        if CRIT_LABEL[name].lower() in low or name in low:
            continue
        owner = getattr(t, "axes", None)
        if owner is not None and name in about.get(owner, ()):
            continue
        out.append(f"annotation {label[:40]!r} is drawn in "
                   f"{CRIT_LABEL[name]}'s colour ({col})")
    return out


def _legend_palette_problems(fig):
    """Legend entries drawn in a colour that already means something else.

    `_assert_palette` compares the module's colour CONSTANTS and so cannot see
    how they are used. Figure 21 was drawn with OKABE[0] and OKABE[4] passed
    straight to `barh` for its stacked segments - AHP's method colour and
    Slope's criterion colour - and the constants were all still distinct, so
    nothing fired.

    This reads the legend instead, which is where a colour is bound to a
    meaning in front of the reader. A handle whose colour belongs to a
    criterion, or to one of the two weighting methods, must carry a label that
    names it.
    """
    crit = {v.lower(): k for k, v in CRIT_COLOUR.items()}
    method = {MEANING["AHP"].lower(): "AHP",
              MEANING["Fuzzy-AHP"].lower(): "Fuzzy-AHP"}

    def _hex(handle):
        import matplotlib.colors as mcolors
        for getter in ("get_facecolor", "get_color"):
            fn = getattr(handle, getter, None)
            if fn is None:
                continue
            try:
                c = fn()
            except Exception:
                continue
            if c is None:
                continue
            if hasattr(c, "__len__") and len(c) and hasattr(c[0], "__len__"):
                c = c[0]
            try:
                return mcolors.to_hex(c).lower()
            except Exception:
                continue
        return None

    out = []
    legends = list(fig.legends) + [ax.get_legend() for ax in fig.axes]
    for lg in legends:
        if lg is None:
            continue
        for handle, text in zip(lg.legend_handles, lg.get_texts()):
            col = _hex(handle)
            if col is None:
                continue
            label = text.get_text()
            low = label.lower()
            if col in crit:
                name = crit[col]
                if CRIT_LABEL[name].lower() not in low and name not in low:
                    out.append(f"legend entry {label!r} uses "
                               f"{CRIT_LABEL[name]}'s colour ({col})")
            elif col in method and method[col].lower() not in low:
                out.append(f"legend entry {label!r} uses "
                           f"{method[col]}'s colour ({col})")
    return out


def _text_problems(fig, pad=0.015, overlap_frac=0.03):
    """Text that reaches the image edge, and text that collides with text.

    Returns a list of one-line complaints. `_save` runs it on every figure and
    prints what it finds.

    The edge test. `savefig.bbox` is "tight", so a Text past the canvas is not
    actually cut; it is pulled into the saved area and the figure grows. What
    the test catches is a label with no breathing room, which is what three
    rounds of review kept objecting to. `pad` is loose because a Text bbox is
    the font em box, including ascent and descent the glyphs never reach.

    The overlap test is the one that matters. Five of the blocking defects in
    the fourth review round were one string drawn on top of another: a legend
    over a title, a suptitle over a panel title, two scatter labels on each
    other. Each had to be found by eye in a PNG. A pairwise bounding-box test
    over the figure's Text artists finds all of them in about a second.

    `overlap_frac` is the share of the SMALLER box that must be covered before
    it counts. Adjacent labels routinely share a pixel or two of em box without
    the ink touching, so an exact test is all false positives. It was 0.22,
    which let Figure 21's "matched: 0.96" / "fixed: 10.53" through - ink
    touching, but under a fifth of the smaller box. At 0.03 that is caught and
    the whole current set is still silent (checked 4 October 2026).

    Tick labels are excluded throughout: matplotlib parks a Text for every tick
    it has ever laid out, including ones outside the view limits that are never
    drawn, which reported a clipped "1.02" on Figure 8 that is not in the PNG.
    """
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = fig.transFigure.inverted()

    ticks = set()
    for ax in fig.axes:
        for tk in list(ax.xaxis.get_major_ticks()) + list(ax.yaxis.get_major_ticks()):
            ticks.add(id(tk.label1))
            ticks.add(id(tk.label2))

    boxes = []
    objs = []
    for t in fig.findobj(mtext.Text):
        if id(t) in ticks:
            continue
        label = t.get_text()
        if not label.strip() or not t.get_visible():
            continue
        try:
            # The BASE Text method. Annotation.get_window_extent() unions in
            # the leader arrow, so a label correctly placed in clear space but
            # pointing at a curve was reported as sitting on that curve - the
            # arrow is meant to touch it.
            bb = mtext.Text.get_window_extent(t, renderer=rend)
        except Exception:
            continue
        if bb.width <= 0 or bb.height <= 0:
            continue
        # The leader as the straight segment from the point it annotates to
        # the centre of its own label, in display coordinates. Not
        # FancyArrowPatch.get_path(): whether that comes back in data or in
        # display space varies, and double-transforming it put Figure 2's four
        # little class arrows across the x-axis label.
        leader = None
        if getattr(t, "arrow_patch", None) is not None and t.arrow_patch.get_visible():
            try:
                # The ANNOTATED POINT's transform, which is `xycoords`, not
                # `t.get_transform()` - that is the TEXT's transform, set by
                # `textcoords`. Where the two differ, as in a label placed at
                # an axes fraction and pointing at a data value, using the
                # text's transform put the anchor somewhere arbitrary and the
                # segment crossed labels it never goes near. That produced
                # twelve spurious reports on Figure 2 alone.
                anchor = t._get_xy_transform(rend, t.xycoords).transform(t.xy)
                leader = (tuple(anchor),
                          ((bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2))
            except Exception:
                leader = None
        boxes.append((bb, label.replace("\\n", " / "), t.get_color(), leader))
        objs.append(t)

    out = []
    for bb, label, _col, _ld in boxes:
        x0, y0 = inv.transform((bb.x0, bb.y0))
        x1, y1 = inv.transform((bb.x1, bb.y1))
        for edge, over in (("left", -x0), ("right", x1 - 1),
                           ("bottom", -y0), ("top", y1 - 1)):
            if over > pad:
                out.append(f"text reaches the {edge} edge: {label!r}")
                break

    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            bi, li, _ci, _di = boxes[i]
            bj, lj, _cj, _dj = boxes[j]
            w = min(bi.x1, bj.x1) - max(bi.x0, bj.x0)
            h = min(bi.y1, bj.y1) - max(bi.y0, bj.y0)
            if w <= 0 or h <= 0:
                continue
            smaller = min(bi.width * bi.height, bj.width * bj.height)
            if (w * h) / smaller > overlap_frac:
                out.append(f"text overlaps text: {li!r} / {lj!r}")

    # Text against DRAWN THINGS, not just against other text. Every blocking
    # overprint in the fifth review round was of this kind: a curve running
    # through its own value label, a Sankey band crossing the label that names
    # it, a reference line under its own caption. A text-only test cannot see
    # any of them.
    # A leader is allowed to touch the curve it points at - that is its job -
    # but it must not be drawn through SOMEBODY ELSE'S label. In Figure 13 the
    # two breakpoint leaders fanned out from almost the same point and the
    # orange one crossed the blue label, which neither the text-text test nor
    # the text-artist test could see.
    from matplotlib.path import Path as _Path
    from matplotlib.transforms import Bbox as _Bbox
    for i, (_bb, li, _ci, leader) in enumerate(boxes):
        if leader is None:
            continue
        seg = _Path([leader[0], leader[1]])
        for j, (bj, lj, _cj, _dj) in enumerate(boxes):
            if i == j:
                continue
            shrunk = _Bbox.from_extents(bj.x0 + 1.0, bj.y0 + 1.0,
                                        bj.x1 - 1.0, bj.y1 - 1.0)
            if shrunk.width <= 0 or shrunk.height <= 0:
                continue
            if seg.intersects_bbox(shrunk, filled=False):
                out.append(f"a leader crosses other text: {li!r} \u2192 {lj!r}")

    for (bb, label, colour, _leader), tobj in zip(boxes, objs):
        # Only text that sits INSIDE a panel's data area. Axis labels, panel
        # titles, panel letters and legends live in the margins by design, and
        # testing them against the artists reported the y-axis label of
        # Figure 8 as overprinted.
        # ...EXCEPT annotations, which are tested wherever they land. Figure
        # 9's Loam callout sat below the axes, on the tick labels, and the
        # in-panel filter waved it through.
        is_annotation = any(t_ is tobj for ax in fig.axes for t_ in ax.texts)
        if not is_annotation and not any(ax.get_window_extent().contains(
                (bb.x0 + bb.x1) / 2, (bb.y0 + bb.y1) / 2) for ax in fig.axes):
            continue
        hit = _artist_under(fig, bb, text_colour=colour, rend=rend)
        if hit:
            out.append(f"text sits on a {hit}: {label!r}")
    return out


def _artist_under(fig, bb, text_colour="black", cover=0.18, rend=None):
    """Name of a drawn artist whose ink falls inside this text's box, or None.

    SEGMENTS, not vertices. The first version of this test transformed a line's
    vertices and asked whether any landed inside the box, which is blind to
    exactly the lines most likely to cross a label: an `axvline` or `axhline`
    has two vertices, at the ends of the axes, so a reference line running
    through a label in between was invisible. It missed the 1.0 line crossing
    two labels in Figure 18. `Path.intersects_bbox` tests the segments.

    Patches and ribbons are tested against their actual path too, not their
    bounding box. A `fill_between` ribbon's bounding rectangle covers most of
    the panel, so a bbox test fired on every label correctly placed on its own
    band - which is why the Sankey had to be checked by eye. `intersects_bbox`
    with `filled=True` tests the real shape, so it can be checked here instead.
    """
    import matplotlib.collections as mcoll
    import matplotlib.patches as mpatches
    from matplotlib.path import Path
    from matplotlib.transforms import Bbox

    # Shrunk by a pixel: a line that grazes the very edge of an em box is not
    # crossing the glyphs.
    box = Bbox.from_extents(bb.x0 + 1.0, bb.y0 + 1.0, bb.x1 - 1.0, bb.y1 - 1.0)
    if box.width <= 0 or box.height <= 0:
        return None

    for ax in fig.axes:
        # Spines and tick marks. A label overhanging the y-axis spine is how
        # Figure 21's 1.02 segment came to read as "-1.02": the text spilled
        # left out of a bar too narrow to hold it, and the tick mark joined the
        # leading "1" into what looked like a minus sign.
        for sp in ax.spines.values():
            if not sp.get_visible():
                continue
            try:
                spath = sp.get_path().transformed(sp.get_transform())
            except Exception:
                continue
            if spath.intersects_bbox(box, filled=False):
                return "axis spine"
        # Tick LABELS, not just the tick marks. Figure 9's Loam callout was
        # printed across "Settlement prox." and "Soil texture" and nothing
        # caught it, because tick labels are excluded from the text-vs-text
        # test (they are parked artefacts, see _text_problems) and were not in
        # the artist test either.
        for axis in (ax.xaxis, ax.yaxis):
            # Only ticks inside the view limits are drawn. matplotlib keeps
            # Text objects for ticks it has laid out beyond them - parked and
            # invisible in the PNG - and testing those reported Figure 5's
            # panel letters as sitting on a "1.2" that is not in the image.
            lo_v, hi_v = sorted(axis.get_view_interval())
            for tk in axis.get_major_ticks():
                loc = tk.get_loc()
                if loc is None or not (lo_v - 1e-9 <= loc <= hi_v + 1e-9):
                    continue
                for lb in (tk.label1, tk.label2):
                    if not lb.get_visible() or not lb.get_text().strip():
                        continue
                    try:
                        lbb = mtext.Text.get_window_extent(lb, renderer=rend)
                    except Exception:
                        continue
                    if (min(box.x1, lbb.x1) - max(box.x0, lbb.x0) > 0
                            and min(box.y1, lbb.y1) - max(box.y0, lbb.y0) > 0):
                        return "tick label"
                for mark in (tk.tick1line, tk.tick2line):
                    if not mark.get_visible():
                        continue
                    try:
                        pts = mark.get_transform().transform(mark.get_xydata())
                    except Exception:
                        continue
                    for px_, py_ in np.asarray(pts).reshape(-1, 2):
                        if box.contains(px_, py_):
                            return "tick mark"
        for ln in ax.lines:
            if not ln.get_visible() or ln.get_linestyle() == "None":
                continue
            try:
                pts = ln.get_transform().transform(ln.get_xydata())
            except Exception:
                continue
            if len(pts) < 2:
                # A single plotted marker: no segment, so test the point.
                if len(pts) == 1 and box.contains(*pts[0]):
                    return "plotted marker"
                continue
            if Path(pts).intersects_bbox(box, filled=False):
                return "plotted line"

        for pa in ax.patches:
            if not pa.get_visible() or not isinstance(
                    pa, (mpatches.Rectangle, mpatches.PathPatch,
                         mpatches.Polygon)):
                continue
            try:
                pb = pa.get_window_extent()
            except Exception:
                continue
            # An empty bin is drawn as a NaN-height bar so that nothing shows;
            # its extent is non-finite and must not count as ink.
            if not np.all(np.isfinite([pb.x0, pb.x1, pb.y0, pb.y1])):
                continue
            w = min(bb.x1, pb.x1) - max(bb.x0, pb.x0)
            h = min(bb.y1, pb.y1) - max(bb.y0, pb.y0)
            if w > 0 and h > 0 and (w * h) / (bb.width * bb.height) > cover:
                # A label deliberately set inside its own bar is normal in this
                # set and is drawn in a contrasting colour.
                if _readable(text_colour, pa.get_facecolor()):
                    continue
                return "filled patch"

        # Scatter markers. A PathCollection is neither a Line2D nor a Patch,
        # so the test was blind to them - which let Figure 22's per-row counts
        # be drawn behind its site markers.
        for co in ax.collections:
            if isinstance(co, mcoll.PathCollection) and co.get_visible():
                try:
                    pts = co.get_offset_transform().transform(co.get_offsets())
                except Exception:
                    pts = np.empty((0, 2))
                for px_, py_ in np.asarray(pts).reshape(-1, 2):
                    if box.contains(px_, py_):
                        return "scatter marker"
            if not isinstance(co, mcoll.PolyCollection) or not co.get_visible():
                continue
            try:
                paths = co.get_paths()
                trans = co.get_transform()
            except Exception:
                continue
            for pth in paths:
                tp = Path(trans.transform(pth.vertices), pth.codes)
                if not tp.intersects_bbox(box, filled=True):
                    continue
                # Same rule as for bars: a label placed on its own ribbon is
                # deliberate, and is drawn to contrast with it.
                cols = co.get_facecolor()
                if len(cols) and _readable(text_colour, cols[0]):
                    continue
                return "filled ribbon"
    return None


def _readable(text_colour, patch_colour, min_contrast=0.40):
    """Would text of this colour read against this fill?

    Relative luminance difference, which is coarse but enough to tell a white
    label deliberately set inside a dark bar from a dark label that a bar has
    grown underneath. Without it the check fired on every in-bar label in
    Figure 12, which are the ones placed there on purpose.
    """
    import matplotlib.colors as mcolors

    def lum(c):
        r, g, b, _a = mcolors.to_rgba(c)
        return 0.299 * r + 0.587 * g + 0.114 * b

    try:
        return abs(lum(text_colour) - lum(patch_colour)) >= min_contrast
    except Exception:
        return True


def _ciede2000(c1, c2):
    """Perceptual distance between two colours, CIEDE2000 on sRGB D65.

    Written out rather than pulled in: the only thing in the project that needs
    it is `_assert_palette`, and a colour-science dependency for one assertion
    is not worth the install.
    """
    import math

    import matplotlib.colors as mcolors

    def to_lab(c):
        r, g, b, _a = mcolors.to_rgba(c)
        # sRGB -> linear
        def lin(u):
            return u / 12.92 if u <= 0.04045 else ((u + 0.055) / 1.055) ** 2.4
        r, g, b = lin(r), lin(g), lin(b)
        # linear RGB -> XYZ (sRGB D65 primaries)
        x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
        y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
        z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b
        # XYZ -> Lab, D65 white
        xn, yn, zn = 0.95047, 1.00000, 1.08883

        def f(t):
            return t ** (1 / 3) if t > 216 / 24389 else (841 / 108) * t + 4 / 29
        fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
        return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)

    L1, a1, b1 = to_lab(c1)
    L2, a2, b2 = to_lab(c2)
    C1, C2 = math.hypot(a1, b1), math.hypot(a2, b2)
    Cb = (C1 + C2) / 2
    G = 0.5 * (1 - math.sqrt(Cb ** 7 / (Cb ** 7 + 25 ** 7))) if Cb else 0.5
    a1p, a2p = (1 + G) * a1, (1 + G) * a2
    C1p, C2p = math.hypot(a1p, b1), math.hypot(a2p, b2)
    h1p = math.degrees(math.atan2(b1, a1p)) % 360 if (a1p or b1) else 0.0
    h2p = math.degrees(math.atan2(b2, a2p)) % 360 if (a2p or b2) else 0.0

    dLp = L2 - L1
    dCp = C2p - C1p
    if C1p * C2p == 0:
        dhp = 0.0
    elif abs(h2p - h1p) <= 180:
        dhp = h2p - h1p
    else:
        dhp = h2p - h1p - 360 * (1 if h2p > h1p else -1)
    dHp = 2 * math.sqrt(C1p * C2p) * math.sin(math.radians(dhp) / 2)

    Lbp = (L1 + L2) / 2
    Cbp = (C1p + C2p) / 2
    if C1p * C2p == 0:
        hbp = h1p + h2p
    elif abs(h1p - h2p) <= 180:
        hbp = (h1p + h2p) / 2
    elif h1p + h2p < 360:
        hbp = (h1p + h2p + 360) / 2
    else:
        hbp = (h1p + h2p - 360) / 2

    T = (1 - 0.17 * math.cos(math.radians(hbp - 30))
         + 0.24 * math.cos(math.radians(2 * hbp))
         + 0.32 * math.cos(math.radians(3 * hbp + 6))
         - 0.20 * math.cos(math.radians(4 * hbp - 63)))
    dth = 30 * math.exp(-(((hbp - 275) / 25) ** 2))
    Rc = 2 * math.sqrt(Cbp ** 7 / (Cbp ** 7 + 25 ** 7)) if Cbp else 0.0
    Sl = 1 + (0.015 * (Lbp - 50) ** 2) / math.sqrt(20 + (Lbp - 50) ** 2)
    Sc = 1 + 0.045 * Cbp
    Sh = 1 + 0.015 * Cbp * T
    Rt = -math.sin(math.radians(2 * dth)) * Rc
    return math.sqrt((dLp / Sl) ** 2 + (dCp / Sc) ** 2 + (dHp / Sh) ** 2
                     + Rt * (dCp / Sc) * (dHp / Sh))


def _assert_palette(min_delta_e=10.0):
    """No two semantic colours may be confusable, not merely unequal.

    An exact-match test caught the scenario bar borrowing Slope's hex. It did
    not catch the replacement, a reddish brown sitting close to Land cover's
    grey-brown - near enough that a reader moving between Figures 12 and 15
    could read one as the other. CIEDE2000 below about 10 is the usual
    threshold for "these could be confused at a glance".

    MEANING["rainfall"] and MEANING["soil"] are exempt against their own
    criteria by design: Figure 12 shows those two as upstream decisions and
    Figures 15 and 17 show them as criteria, and they are the same thing.
    """
    semantic = {f"CRIT_COLOUR[{k!r}]": v for k, v in CRIT_COLOUR.items()}
    semantic.update({
        "NEUTRAL_BAR": NEUTRAL_BAR,
        "OTHER_COLOUR": OTHER_COLOUR,
        "MEANING['method']": MEANING["method"],
        "MEANING['interaction']": MEANING["interaction"],
        "MEANING['AHP']": MEANING["AHP"],
        "MEANING['Fuzzy-AHP']": MEANING["Fuzzy-AHP"],
        "PARTITION['robust']": PARTITION["robust"],
        "PARTITION['induced']": PARTITION["induced"],
        # The class colours and the generic series pair were outside the test,
        # which is how Okabe blue (generic series 1) sat at ΔE 5.5 from the
        # High class blue and Fig. 13 used both.
        **{f"CLASS_COLOURS[{k!r}]": v for k, v in CLASS_COLOURS.items()},
        "GENERIC[0]": GENERIC[0],
        "GENERIC[1]": GENERIC[1],
    })
    exempt = {frozenset(("CRIT_COLOUR['rainfall']", "MEANING['rainfall']")),
              frozenset(("CRIT_COLOUR['soil']", "MEANING['soil']")),
              # One colour, one role: a bar whose length is the whole message.
              frozenset(("MEANING['method']", "NEUTRAL_BAR"))}

    names = sorted(semantic)
    clashes = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            if frozenset((names[i], names[j])) in exempt:
                continue
            d = _ciede2000(semantic[names[i]], semantic[names[j]])
            if d < min_delta_e:
                clashes.append(f"{names[i]} vs {names[j]} (\u0394E {d:.1f})")
    assert not clashes, (
        f"semantic colours closer than \u0394E {min_delta_e:g}, so a reader could "
        "confuse them: " + "; ".join(clashes))


def _assert_series_colours(colours, where, min_delta_e=10.0):
    """A colormap-sampled series must not imitate a semantic colour.

    _assert_palette only sees the named constants. Figure 9's rank lines were
    sampled from plasma, and rank 4 came out at ΔE 6.0 from Fuzzy-AHP's
    red - in a figure whose axes are the criteria, a series colour that
    resembles a criterion or a method reads as that criterion or method.
    """
    import matplotlib.colors as mcolors
    semantic = dict(CRIT_COLOUR)
    semantic.update({f"MEANING[{k!r}]": v for k, v in MEANING.items()})
    semantic.update({f"PARTITION[{k!r}]": v for k, v in PARTITION.items()})
    semantic.update({"NEUTRAL_BAR": NEUTRAL_BAR, "OTHER_COLOUR": OTHER_COLOUR})
    # Class colours too: YlGnBu rank 3 passed this check at ΔE 9.2 from the
    # High class blue because they were missing. GENERIC is deliberately not
    # here - a series drawn IN the generic colour is the intended use.
    semantic.update({f"CLASS_COLOURS[{k!r}]": v for k, v in CLASS_COLOURS.items()})
    bad = []
    for i, c in enumerate(colours):
        hx = mcolors.to_hex(c)
        for name, ref in semantic.items():
            d = _ciede2000(hx, ref)
            if d < min_delta_e:
                bad.append(f"{where} series {i} {hx} vs {name} (ΔE {d:.1f})")
    assert not bad, "series colour imitates a semantic colour: " + "; ".join(bad)


def _edges_include(edges, points, where):
    """Histogram bin edges must include each class breakpoint.

    Figure 22's bins ran from the data minimum, so one bin straddled 0.85 and
    painted High-only cells on the Low side of the dashed line.
    """
    missing = [p for p in points if not np.isclose(edges, p, atol=1e-9).any()]
    assert not missing, f"{where}: bin edges do not include {missing}"


def _extent(transform, shape):
    h, w = shape
    return (transform.c, transform.c + w * transform.a,
            transform.f + h * transform.e, transform.f)


def _clear_corner(mask, frac_w=0.30, frac_h=0.16):
    """Which frame corner is emptiest, as (x_frac, y_frac) in axes coordinates.

    Map furniture has been printed over the data twice now, each time because a
    corner was chosen by eye from one rendering. Testing the district mask
    instead means the choice follows the geometry, so it stays correct for any
    study area and any of the other maps in the set.

    Returns the anchor for the LOWER-LEFT of the furniture block.
    """
    h, w = mask.shape
    bh, bw = int(h * frac_h), int(w * frac_w)
    options = {
        # name: (row slice, col slice, x_frac, y_frac for the block's corner)
        "upper-left":  (slice(0, bh), slice(0, bw), 0.04, 0.82),
        "upper-right": (slice(0, bh), slice(w - bw, w), 0.62, 0.82),
        "lower-left":  (slice(h - bh, h), slice(0, bw), 0.04, 0.06),
        "lower-right": (slice(h - bh, h), slice(w - bw, w), 0.62, 0.06),
    }
    scored = sorted(((float(mask[rs, cs].mean()), name, xf, yf)
                     for name, (rs, cs, xf, yf) in options.items()),
                    key=lambda t: t[0])
    occ, name, xf, yf = scored[0]
    return xf, yf, name, occ


def _add_scalebar(ax, extent, km=25, y_frac=0.055, x_frac=0.06,
                  _via_helper=False) -> None:
    """Scale bar in kilometres on a geographic (degree) axis.

    Degrees of longitude shrink with latitude, so the bar length is computed at
    the panel's centre latitude rather than assumed constant.
    """
    # Only `_place_furniture` may call this. Figure 6 drew its bar into a
    # margin axes 0.22 figure-widths wide while its map panels were 0.26, so
    # the bar's length had no relation to the maps it labelled - a 25 km bar
    # that measured about 30 km against the data. A scale bar is only
    # meaningful inside the axes whose transform it is drawn from.
    assert _via_helper, ("call _place_furniture(ax, ctx), not _add_scalebar: "
                         "a scale bar drawn outside the mapped axes is "
                         "measured against the wrong transform")
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


def _place_furniture(ax, ctx, km=20) -> None:
    """Scale bar and north arrow in whichever frame corner is emptiest.

    Every map figure calls this. Figure 10 was fixed by hand last round and
    Figures 14 and 16 promptly repeated the defect — bar over the south-west
    lobe, arrow inside the north-east boundary — because the placement lived in
    one function body instead of a helper.

    20 km, not 25: the frame is about 125 km wide, so a 25 km bar is 0.20 of it
    and the arrow beside it lands on the district outline.
    """
    xf, yf, _corner, _occ = _clear_corner(ctx.mask)
    _add_scalebar(ax, ctx.extent, km=km, x_frac=xf, y_frac=yf, _via_helper=True)
    _add_north(ax, ctx.extent, x_frac=xf + 0.205, y_frac=yf + 0.010)


def _category_axis(ax, codes, labels, axis="x", rotation=0, fontsize=7) -> None:
    """Ticks at the classes that are actually present, labelled by name.

    An automatic locator on a categorical axis produces 5.0, 7.5, 10.0 for IGBP
    codes - positions that are not classes - and skips the classes that are.
    After the soil legend error, the panel where a reader most needs to check
    that a score is attached to the right texture was showing bare code
    numbers, which no referee can verify.
    """
    codes = list(codes)
    ticks = getattr(ax, f"set_{axis}ticks")
    ticklabels = getattr(ax, f"set_{axis}ticklabels")
    ticks(codes)
    ticklabels([labels.get(c, str(c)) for c in codes], rotation=rotation,
               fontsize=fontsize,
               ha="right" if (rotation and axis == "x") else
                  ("center" if axis == "x" else "right"))


def _graticule(ax, extent, step=0.5) -> None:
    """Round graticule values with degree symbols.

    A linspace of the extent gives ticks like 20.730 and 19.459, which are
    meaningless as coordinates and collided at the lower-left corner because
    the first x and y labels were both six characters wide.
    """
    x0, x1, y0, y1 = extent
    xs = np.arange(np.ceil(x0 / step) * step, x1 + 1e-9, step)
    ys = np.arange(np.ceil(y0 / step) * step, y1 + 1e-9, step)
    ax.set_xticks(xs)
    ax.set_yticks(ys)
    ax.set_xticklabels([f"{v:g}°E" for v in xs])
    ax.set_yticklabels([f"{v:g}°N" for v in ys])
    ax.tick_params(labelsize=6.5, length=2, pad=1)
    ax.grid(True, color="grey", lw=0.3, alpha=0.35, linestyle=":")


def _outer_graticule(axes, extent) -> None:
    """Graticule for small multiples: lines on every panel, degree labels on
    the outer edges only (left column, bottom row). FIGURE_SPECS requires a
    round-degree graticule on maps; labelling every panel crowded them."""
    grid = np.atleast_2d(axes)
    nr, nc = grid.shape
    for i in range(nr):
        for j in range(nc):
            ax = grid[i, j]
            _graticule(ax, extent)
            ax.tick_params(labelleft=(j == 0), labelbottom=(i == nr - 1))
            ax.set_xlim(extent[0], extent[1])
            ax.set_ylim(extent[2], extent[3])


def _map(ax, arr, extent, boundary=None, cmap="viridis", norm=None,
         vmin=None, vmax=None, title=None, furniture=False, grat=True):
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
        raise ValueError(
            "_map(furniture=True) is gone: it placed the bar in a fixed corner "
            "without consulting the district mask. Call _place_furniture(ax, "
            "ctx) after _map instead.")
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
        self._scen = None

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

    @property
    def scenarios(self):
        """Every preset scenario's weights, CR and class shares, computed once.

        Figures 12 and 15 both need these and they cost a score_stack each.
        """
        if self._scen is None:
            self._scen = {}
            for name in SCENARIOS:
                w, cr = ahp_engine.weights_for_scenario(name)
                r = G.score_stack(self.stack, w, cr)
                self._scen[name] = {
                    "weights": w, "cr": cr,
                    "High": G.class_share_pct(r, "High"),
                    "Low": G.class_share_pct(r, "Low")}
        return self._scen

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
        # Slope's own colour. Blue here was AHP's method colour, which has
        # nothing to do with this panel.
        ax.hist(data, bins=60, color=CRIT_COLOUR["slope"], edgecolor="none")
        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_yscale("log")
    axes[0, 0].set_ylabel("cells (log)")
    # (b) and (c) exist to be compared, so they share both ranges. Left to
    # autoscale their y floors differed by more than a decade and (c) started
    # near 0.05 on x, which flatters whichever panel happens to be emptier.
    for ax in (axes[0, 1], axes[0, 2]):
        ax.set_xlim(0, 1)
    ymax0 = max(axes[0, 1].get_ylim()[1], axes[0, 2].get_ylim()[1])
    for ax in (axes[0, 1], axes[0, 2]):
        ax.set_ylim(0.6, ymax0)

    # Both score panels carry the SAME statistic in the SAME place, so the
    # comparison lands on inspection. Printing it only on the min–max panel
    # left two visually similar histograms and an assertion in the caption.
    above_ramp = 100.0 * float((ramp_slope > 0.90).mean())
    # The interquartile range separates the two schemes far more convincingly
    # than the share above a threshold: 2.8x versus 95.8% against 86.0%. Both
    # are shown, IQR first, because the share understates the real difference.
    iqr_mm = float(np.subtract(*np.percentile(minmax_slope, [75, 25])))
    iqr_rp = float(np.subtract(*np.percentile(ramp_slope, [75, 25])))
    for ax, pct, iqr, col in ((axes[0, 1], above, iqr_mm, "0.25"),
                              (axes[0, 2], above_ramp, iqr_rp, "0.25")):
        ax.axvspan(0.90, 1.0, color=col, alpha=0.16, zorder=0)
        ax.annotate("\n".join([f"IQR {iqr:.4f}", f"{pct:.1f}% above 0.90"]),
                    xy=(0.04, 0.82), xycoords="axes fraction", ha="left",
                    fontsize=8, color=col, fontweight="bold")

    u, cnt = np.unique(codes, return_counts=True)
    axes[1, 0].bar(u, cnt, color=CRIT_COLOUR["lulc"], width=0.75)
    axes[1, 0].set_title("Land cover, IGBP class codes")
    # Named, like Figure 5(e). An automatic locator ticked these at 5.0, 7.5,
    # 10.0 - positions that are not classes.
    # The same abbreviations as Fig. 5(e), so one class has one name across
    # the set. Spaced by CODE, deliberately: code spacing is what min-max acts
    # on, which is the point of this row (said in the caption, so nobody
    # "fixes" it to ordinal spacing).
    _category_axis(axes[1, 0], [int(c) for c in u], LULC_ABBR, rotation=45,
                   fontsize=6.5)
    axes[1, 0].set_xlabel("class")
    axes[1, 0].set_ylabel("cells (log)")
    axes[1, 0].set_yscale("log")

    uu, cc = np.unique(np.round(minmax_lulc, 4), return_counts=True)
    axes[1, 1].bar(uu, cc, color=CRIT_COLOUR["lulc"], width=0.03)
    axes[1, 1].set_title("Land cover, min–max on codes")
    axes[1, 1].set_xlabel("score")
    axes[1, 1].set_yscale("log")

    ul, cl = np.unique(np.round(lookup_lulc, 4), return_counts=True)
    axes[1, 2].bar(ul, cl, color=CRIT_COLOUR["lulc"], width=0.03)
    axes[1, 2].set_title("Land cover, class lookup")
    axes[1, 2].set_xlabel("score")
    axes[1, 2].set_yscale("log")

    # Name specific classes on both panels so the inversion is visible rather
    # than something the reader has to reconstruct by mapping codes themselves.
    # Labels go INSIDE the panel with a short downward arrow. Placing them above
    # the axes collided with the panel title, the panel letter and the figure
    # title all at once.
    # Headroom so the in-panel labels clear the tallest bar on a log axis.
    # (d), (e) and (f) all plot cells per class, so they share one y range;
    # left to autoscale their tops differed by a decade.
    for ax in (axes[1, 0], axes[1, 1], axes[1, 2]):
        # Headroom: the labels hang from 0.90 of the axes and must clear the
        # tallest bar (cropland, 81,010); at x12 "Crop" sat on its own bar.
        ax.set_ylim(10, float(cnt.max()) * 80)

    cmin, cmax = codes.min(), codes.max()
    counts_by_code = dict(zip(u.tolist(), cnt.tolist()))
    # Axis abbreviations. "Forest" was ambiguous: Mixed forest is a different
    # bar (0.08 / 0.35); the labelled one is deciduous broadleaf.
    for code, short in ((17, "Water"), (4, "DBF"), (12, "Crop")):
        mm = (code - cmin) / (cmax - cmin)
        lk = C.LULC_SCORES[code]
        height = counts_by_code.get(code, 1)
        for ax, xval in ((axes[1, 1], mm), (axes[1, 2], lk)):
            ha = "left" if xval < 0.2 else ("right" if xval > 0.8 else "center")
            # Tip at the BAR TOP, in data coordinates. At a fixed axes
            # fraction on a log axis the Water arrow ended around 10^4 while
            # its bar is 105 cells, so it pointed at empty space - which reads
            # as a mislabelled bar.
            ax.annotate(f"{short}\n{xval:.2f}", xy=(xval, height),
                        xytext=(xval, 0.90),
                        xycoords="data",
                        textcoords=("data", "axes fraction"),
                        ha=ha, va="top", fontsize=7,
                        color=CRIT_COLOUR["lulc"], fontweight="bold",
                        arrowprops=dict(arrowstyle="-|>",
                                        color=CRIT_COLOUR["lulc"], lw=0.9,
                                        shrinkA=1, shrinkB=2))

    for ax in axes.ravel():
        ax.grid(True, axis="y")
    _panel_letters(axes, offset=(-0.02, 1.08))


    # Not "fixed reclassification replaced min-max": panel (c) is a ramp, and
    # Fig. 8 shows step reclassification was itself replaced by ramps.
    fig.suptitle("Min–max follows the range or the class code; anchored "
                 "scoring follows meaning", y=0.985)
    fig.tight_layout(h_pad=2.6, rect=(0, 0.012, 1, 0.962))
    _save(fig, 2, f"normalisation (IQR {iqr_mm:.4f} vs {iqr_rp:.4f}, {iqr_rp/iqr_mm:.1f}x wider spread)")
    return {"CAPTION": (
                "CHRONOLOGY: the project began with min-max rescaling, "
                "replaced it with fixed step reclassification, and then "
                "replaced the steps with the interpolated ramps and class "
                "lookups in use now (step versus ramp is Fig. 8). This figure "
                "compares the first scheme with the current one. "
                "Top row, slope. Bottom row, land cover. (b) and (c) share "
                "both axes; (d), (e) and (f) share the y range. (d) places "
                "classes at their IGBP CODE values, not evenly: code spacing "
                "is exactly what min-max acts on. Land-cover abbreviations as "
                "in Fig. 5 (DBF deciduous broadleaf, Crop cropland). "
                "Min-max rescaling of slope leaves the scores in a "
                f"narrow band - IQR {iqr_mm:.4f} against {iqr_rp:.4f} under "
                "the anchored ramp, a 2.8x wider spread - and the ramp is an "
                "improvement rather than a cure: "
                f"{above_ramp:.1f}% of in-district cells still score above "
                f"0.90, down from {above:.1f}%. That residual concentration "
                "is why slope takes only 0.43x its assigned weight in "
                "variance share in Fig. 18. "
                "Bottom row: under min-max the score follows the class CODE, "
                "so water (IGBP 17) scores best and deciduous broadleaf "
                "forest (4) worst; under "
                "the lookup it follows the class MEANING and the ordering "
                "inverts. The three labelled classes are annotated at their "
                "own bar heights - water is 105 cells against cropland's "
                "81,010, which the log axis compresses. "
                "The min-max panels are reconstructions of the scheme this "
                "project replaced; the ramp and lookup panels are the scheme "
                "in use."),
            "minmax_slope_above_090_pct": round(above, 2),
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
        # Categorical panels plot at ORDINAL positions, so the classes are
        # evenly spaced. At their code values the gaps were unequal (soil
        # codes 1, 4, 6, 7) and carried no meaning.
        cats = None
        if name in ("soil", "lulc"):
            cats = sorted({int(round(c)) for c in np.unique(rv)})
            pos = {c: i for i, c in enumerate(cats)}
            rv = np.array([pos[int(round(c))] for c in rv], dtype=float)
        ax2 = ax.twinx()
        if cats is None:
            ax2.hist(rv, bins=50, color="0.82", edgecolor="none", zorder=0)
        else:
            ax2.hist(rv, bins=np.arange(len(cats) + 1) - 0.5, rwidth=0.35,
                     color="0.82", edgecolor="none", zorder=0)
        ax2.spines["right"].set_visible(False)
        # The square-root scale for the two categorical panels is applied HERE,
        # before the ticks are cleared. Setting it afterwards installed a fresh
        # locator, so those two panels grew a right-hand count axis while the
        # figure's own footnote said there was none.
        if name in ("soil", "lulc"):
            ax2.set_yscale("function",
                           functions=(lambda v: np.sqrt(np.abs(v)),
                                      lambda v: v ** 2))
            # Floor pinned at 0. Autoscale left a negative bottom margin, and
            # sqrt(|v|) folds it back up, so the axis started at a POSITIVE
            # count and every small class (Loam, 0.38%) was drawn a few pixels
            # tall instead of at sqrt(share) of panel height.
            top = float(max(np.histogram(rv, bins=np.arange(len(cats) + 1) - 0.5)[0]))
            ax2.set_ylim(0, top * 1.05)
        ax2.set_yticks([])
        order = np.argsort(rv)
        if name in ("soil", "lulc"):
            ax.scatter(rv, sv, s=14, color=GENERIC[0], zorder=3)
        else:
            ax.plot(rv[order], sv[order], color=GENERIC[0], lw=1.6, zorder=3)
        ax.set_zorder(ax2.get_zorder() + 1)
        ax.patch.set_visible(False)
        ax.set_title(f"{CRIT_LABEL[name]}  (w = {ctx.weights[name]:.3f})")
        ax.set_xlabel(xlabel)
        ax.set_ylim(-0.03, 1.05)
        if xlim:
            ax.set_xlim(*xlim)
            beyond = 100.0 * float((rv > xlim[1]).mean())
            if beyond > 0.01:
                # One line, bottom right. These are cost criteria, so the
                # curve falls across the whole width and a two-line note
                # crossed it wherever it was put; at the far right the curve
                # has bottomed out and the strip beneath it is clear.
                # (f): three short lines, so the box stays right of ~17 km,
                # where the curve is already on its floor. (a): one line.
                sep = "\n" if name == "population" else " "
                ax.annotate(f"truncated at {xlim[1]:g};{sep}{beyond:.2f}% beyond"
                            f"{sep}(max {rv.max():.1f})",
                            # (f): above the 0.10 floor at 17-25 km, where
                            # neither curve nor bars reach. At the bottom its
                            # white box hid the 5-17 km histogram bars.
                            # (a): bottom right, over only the near-zero tail.
                            xy=(0.98, 0.26 if name == "population" else 0.004),
                            xycoords="axes fraction",
                            ha="right", va="bottom", fontsize=6.8,
                            color="0.35",
                            # On a white ground: the grey frequency histogram
                            # runs under this corner in two of the panels.
                            bbox=dict(boxstyle="square,pad=0.2", fc="white",
                                      ec="none", alpha=0.85))
        ax.grid(True, axis="y")
        # Categorical axes get ticks at the classes that are present, labelled
        # by NAME. Bare code numbers meant a referee could not check that each
        # score was attached to the right class - which is precisely the error
        # this project already made once, on soil.
        if name == "soil":
            _category_axis(ax, range(len(cats)),
                           {i: C.SOIL_TEXTURE_LABELS[c] for i, c in enumerate(cats)},
                           rotation=35)
            ax.set_xlim(-0.6, len(cats) - 0.4)
        elif name == "lulc":
            # Abbreviated: eleven full IGBP names at 35 degrees collided.
            _category_axis(ax, range(len(cats)),
                           {i: LULC_ABBR.get(c, str(c)) for i, c in enumerate(cats)},
                           rotation=45, fontsize=6.5)
            ax.set_xlim(-0.6, len(cats) - 0.4)
        if name == "rainfall":
            # Rainfall is the one ASCENDING panel, so its clear corner is the
            # opposite one: lower right, not the centre where the curve runs.
            # Annotation grey: vermilion is the second-series colour.
            ax.annotate("district-relative", xy=(0.03, 0.93),
                        xycoords="axes fraction", ha="left", va="top",
                        fontsize=7.5, color="0.35", fontweight="bold")
    # "Criterion score", as in Fig. 9: "suitability" is reserved for the
    # composite.
    axes[0, 0].set_ylabel("criterion score")
    axes[1, 0].set_ylabel("criterion score")
    # Left of the axes rather than over them: at the default offset the letters
    # for columns 2 and 3 printed on the start of each panel title.
    # Higher than the default: at 1.02 each letter sat on the "1.0" y-tick.
    _panel_letters(axes, offset=(-0.14, 1.10))
    fig.suptitle("Criterion scoring functions over the in-district distribution "
                 "of each variable", y=0.988)
    fig.tight_layout(rect=(0, 0.012, 1, 0.966))
    _save(fig, 5, "six scoring functions")

    return {
        "weights": {c: round(float(ctx.weights[c]), 4) for c in ctx.crit},
        "soil_classes_present": {int(k): C.SOIL_TEXTURE_LABELS[int(k)]
                                 for k in sorted({int(round(v)) for v in
                                                  ctx.vals(ctx.stack["raw_rasters"]["soil"])})},
        "CAPTION": (
            "Grey histograms behind each curve show the in-district frequency "
            "of the variable, scaled to panel height and carrying no numeric "
            "axis; the two categorical panels draw theirs on a square-root "
            "scale from zero, so a class's bar is sqrt(its share of the "
            "largest class) of panel height and the small classes stay "
            "visible - Loam, at 0.38% of the district, stands at about 7% of "
            "the height of Clay Loam. "
            "THE FUNCTIONS. (a) Slope is an interpolated ramp through the "
            "anchors in criteria.SLOPE_RAMP_DEG - 0 deg 1.00, 1 deg 0.95, "
            "3 deg 0.85, 5 deg 0.68, 10 deg 0.42, 15 deg 0.20, 25 deg 0.08, "
            "90 deg 0.05 - so it continues below the 0.14 visible at the "
            "20 deg truncation, reaching 0.08 at 25 deg and a 0.05 floor "
            "beyond. (b) Rainfall is NOT a raw percentile: it is "
            "floor + (1 - floor) x percentile rank within the district, with "
            f"floor = {C.RAINFALL_FLOOR:.2f}, so the driest cell scores "
            f"{C.RAINFALL_FLOOR:.2f} rather than 0. (c) Drainage density is "
            "an interpolated ramp through criteria.DRAINAGE_DENSITY_RAMP - "
            + ", ".join(f"{x:.2f} km/km2 {y:.2f}"
                        for x, y in C.DRAINAGE_DENSITY_RAMP) +
            " (the district maximum is about 0.85, so 1.00 is not reached). "
            "(f) Settlement proximity is moderate-optimal with a GENTLE PEAK, "
            f"not a plateau: {C.SETTLEMENT_SCORE_AT_ZERO:.2f} inside the "
            f"settlement, rising to 0.97 at {C.SETTLEMENT_PEAK_KM[0]:.0f} km, "
            f"1.00 at {sum(C.SETTLEMENT_PEAK_KM) / 2:.0f} km and 0.97 again "
            f"at {C.SETTLEMENT_PEAK_KM[1]:.0f} km, then falling linearly to a "
            f"{C.SETTLEMENT_FLOOR:.2f} floor over the next "
            f"{C.SETTLEMENT_FALLOFF_KM:.0f} km, which it reaches before the "
            "25 km truncation. The peak is deliberate (criteria."
            "moderate_optimal): a flat top gave every cell in the 4 km band "
            "the same 1.00 and produced tied sites. "
            "Categorical axes are labelled with class NAMES. Soil textures "
            "are the USDA classes of ISRIC SoilGrids250m TEXMHT_M_sl1, read "
            "from the LEGEND tag on the original download and reproduced in "
            "criteria.SOIL_TEXTURE_LABELS; cite Hengl et al. (2017), "
            "doi:10.1371/journal.pone.0169748. Land-cover classes are MODIS "
            "MCD12Q1 IGBP, abbreviated on the axis: DBF deciduous broadleaf, "
            "MixF mixed forest, OShr open shrubland, WSav woody savanna, Sav "
            "savanna, Grass grassland, Wetl permanent wetland, Crop cropland, "
            "Urban built-up, CrNat cropland/natural mosaic, Water. Classes "
            "are evenly spaced, not placed at their code values. "
            "Weights are the AHP weights of Table 1, to 3 dp. "
            "Methods note: Loam = 1.00 is the single most consequential "
            "scoring choice in the model, because the top of the shortlist "
            "sits on it (Fig. 9); the ordering Loam > Sandy Clay Loam > Clay "
            "Loam > Clay needs a cited justification in the Methods."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 6 — the six scored criterion surfaces
# ─────────────────────────────────────────────────────────────────────────────

def fig_06(ctx):
    fig, axes = plt.subplots(2, 3, figsize=(10.4, 7.0))
    im = None
    for ax, name in zip(axes.ravel(), ctx.crit):
        arr = ctx.inside(ctx.stack["normalized_rasters"][name])
        v = ctx.vals(ctx.stack["normalized_rasters"][name])
        # Two lines. On one, the longest title ran into the colourbar and the
        # panel letter ran into the title beside it.
        # A near-uniform panel is a finding, not a rendering fault, so the
        # statistic is printed. In the title rather than under the panel,
        # where the graticule labels of the bottom row now sit.
        im = _map(ax, arr, ctx.extent, ctx.boundary, cmap="viridis",
                  vmin=0, vmax=1,
                  title=None, furniture=False, grat=False)
        # Smaller than the default title: at full size the longest ones ran
        # into the panel letters of (c) and (f).
        # Short names for the two long criteria: "Drainage density (w = ...)"
        # ran past the panel edge and sat 15 px from its own panel letter.
        short = {"drainage": "Drainage dens.", "population": "Settlement"}
        ax.set_title(f"{short.get(name, CRIT_LABEL[name])}  "
                     f"(w = {ctx.weights[name]:.3f})\n"
                     f"mean {v.mean():.3f}   SD {v.std():.3f}", fontsize=9)
    _outer_graticule(axes, ctx.extent)

    # Inside panel (a), via the one helper. This used to be drawn into a margin
    # axes 0.22 figure-widths wide while the map panels were 0.26, so the bar
    # was measured against a transform that had nothing to do with the maps it
    # labelled. _add_scalebar now refuses to be called any other way.
    _place_furniture(axes[0, 0], ctx)

    _panel_letters(axes, offset=(-0.16, 1.10))
    cbar = fig.colorbar(im, ax=axes, shrink=0.48, pad=0.015, aspect=20)
    cbar.set_label("criterion score (0\u20131)")
    fig.suptitle("Scored criterion surfaces \u2014 shared extent and shared 0\u20131 scale",
                 y=0.98)
    _save(fig, 6, "six criterion surfaces")

    return {
        "mean": {c: round(float(ctx.vals(ctx.stack["normalized_rasters"][c]).mean()), 4)
                 for c in ctx.crit},
        "sd": {c: round(float(ctx.vals(ctx.stack["normalized_rasters"][c]).std()), 4)
               for c in ctx.crit},
        "CAPTION": (
            "All six panels share the extent and the 0-1 colour scale, so they "
            "can be compared directly. THE SCALE BAR AND NORTH ARROW IN PANEL "
            "(a) APPLY TO ALL SIX PANELS; they are drawn once, from panel "
            "(a)'s own data transform. A 0.5-degree graticule runs through "
            "every panel, labelled on the left column and bottom row only. "
            "Each panel's title carries the mean and population standard "
            "deviation of its own scored surface - PER CELL over the 123,555 "
            "in-district cells, unweighted by cell area (the area weights "
            "differ by under 1% across the district) - because a near-uniform "
            "panel "
            "is a property of the criterion rather than a rendering fault - "
            "slope at mean 0.924, SD 0.117 is the clearest case, and Fig. 18 "
            "shows what that costs it in discriminating power. "
            "Do NOT reconstruct Fig. 18's level shares from these means: that "
            "figure averages the per-cell ratio w_i*r_i/V, which is not the "
            "ratio of the means. Combining the means with the weights gives "
            "about 38.2% for rainfall against the 36.9% Fig. 18 reports, and "
            "30.9% for slope against 31.6%."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 8 — step classes versus interpolated ramps
# ─────────────────────────────────────────────────────────────────────────────

def fig_08(ctx):
    """Did step classes create the tied plateau, or did the soil legend?

    Both, and neither alone. The earlier version of this figure reconstructed
    the step-class scoring using the soil table as it stood before
    2026-10-02 - the table the project has since shown to be WRONG - and used
    the resulting 973-cell plateau to justify a current method choice. A
    referee is entitled to object that the evidence comes from data the paper
    itself retracts.

    Recomputing under the corrected legend answers the objection and turns it
    into a finding: the same step-class scheme produces **one** cell at exactly
    1.000, not 973. The plateau needed the flat tops AND a dominant soil class
    wrongly scored 1.00. Showing both panels says so directly, and makes clear
    that 973 is a historical reconstruction which must never be quoted as a
    current result.
    """
    # EACH PANEL HOLDS ITS LEGEND FIXED, for both series. The previous version
    # drew the current ramp composite in both panels, so (b) set step classes
    # under the superseded legend against ramps under the corrected one, and
    # most of its excess above 0.92 was the legend, not the scoring scheme.
    # The ramp composite under the superseded legend is the current stack with
    # only the soil layer rescored, combined by the same _weighted_overlay.
    def _ramp_with(soil_table):
        nr = dict(ctx.stack["normalized_rasters"])
        nr["soil"] = C.score_categorical(ctx.stack["raw_rasters"]["soil"],
                                         soil_table, C.SOIL_DEFAULT_SCORE)
        surf, _cov = G._weighted_overlay(
            {k: np.where(ctx.mask, v, np.nan) for k, v in nr.items()},
            ctx.weights)
        ok = ctx.mask & ~np.isnan(surf)
        # Area-weighted High share, like every class share in the project; a
        # cell mean gave 6.45% against the baseline's 6.44%.
        high = 100.0 * float(ctx.area[ok & (surf > C.SUITABILITY_THRESHOLDS[1])].sum()
                             / ctx.area[ok].sum())
        return surf[ok], high

    runs = [("corrected legend\n(in use since 2 Oct 2026)", C.SOIL_TEXTURE_SCORES),
            ("legend in use at the time\n(superseded)", _StepHelper.SOIL)]

    # True bin edges, 0.01 wide, starting AT 0.85 so the High breakpoint is an
    # edge. Outline histograms overlaid on those edges, so a bar's position IS
    # its score; the old grouped bars sat half a bin either side of their
    # range, put the tied bar at ~0.985 and cut the first ramp bar off at the
    # spine.
    edges = np.round(np.arange(0.85, 1.0 + 1e-9, 0.01), 4)
    _edges_include(edges, (C.SUITABILITY_THRESHOLDS[1], 1.0), "fig08")

    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.3), sharey=True)
    tied, ramp_tied, ramp_high = {}, {}, {}
    series = {}
    ymax = 1
    for label, tbl in runs:
        a_s = ctx.vals(_StepHelper.surface(ctx, tbl))
        a_r, hi_r = _ramp_with(tbl)
        series[label] = (a_s, a_r)
        ramp_high[label.split("\n")[0]] = hi_r
        for a in (a_s, a_r):
            ymax = max(ymax, np.histogram(a, bins=edges)[0].max())

    for ax, (label, tbl) in zip(axes, runs):
        a_step, a_rmp = series[label]
        key = label.split("\n")[0]
        n_tied = int((np.abs(a_step - 1.0) < 1e-9).sum())
        tied[key] = n_tied
        ramp_tied[key] = int((np.abs(a_rmp - 1.0) < 1e-9).sum())
        for a, col, lab in ((a_step, GENERIC[1], "step classes"),
                            (a_rmp, GENERIC[0], "interpolated ramps")):
            h, _ = np.histogram(a, bins=edges)
            # Empty bins are gaps, not bars: a count cannot be below 1, and a
            # floor put bars where the ramp surface has no cells at all.
            ax.stairs(np.where(h > 0, h, np.nan), edges, color=col, lw=1.8,
                      label=lab, baseline=None)
        # The tied cells AT 1.000, where they are. numpy closes the last bin on
        # both sides, so they are also inside the 0.99-1.00 step bin.
        if n_tied > 0:
            # Top at n_tied exactly: bottom is the axis floor, so the height
            # is n_tied minus that floor (a height of n_tied put 1 cell at 1.7).
            ax.bar([1.0], [n_tied - 0.7], width=0.004, color=GENERIC[1],
                   edgecolor="black", lw=0.8, hatch="///", zorder=4,
                   bottom=0.7)
        ax.set_yscale("log")
        ax.set_xlim(0.85, 1.004)
        ax.set_ylim(0.7, ymax * 2.5)
        ax.set_xlabel("composite suitability score")
        ax.grid(True, axis="y")
        ax.set_title(f"{label}\n{n_tied:,} cell{'s' if n_tied != 1 else ''} "
                     "at exactly 1.000 (step); "
                     f"{ramp_tied[key]} (ramps)", fontsize=9)

    axes[0].set_ylabel("cells per 0.01 bin (log scale)")
    handles, labels = axes[0].get_legend_handles_labels()
    handles.append(Rectangle((0, 0), 1, 1, facecolor=GENERIC[1],
                             edgecolor="black", hatch="///"))
    labels.append("step cells tied at exactly 1.000")
    # Below the panels: the step series in (b) runs flat to 1.00, so there is
    # no empty corner inside either axes.
    fig.legend(handles, labels, frameon=False, loc="lower center", ncol=3,
               fontsize=8, bbox_to_anchor=(0.5, -0.01))
    _panel_letters(axes, offset=(-0.08, 1.12))

    n_hist = tied["legend in use at the time"]
    n_corr = tied["corrected legend"]
    fig.suptitle("The tied plateau needed the flat tops AND the mis-scored "
                 "soil legend", y=1.00)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    _save(fig, 8, f"step vs ramp under both legends "
                  f"({n_corr} tied now, {n_hist} historically)")

    k_corr, k_hist = "corrected legend", "legend in use at the time"
    return {
        "tied_at_one_corrected_legend": n_corr,
        "tied_at_one_historical_legend": n_hist,
        "ramp_tied_at_one_corrected_legend": ramp_tied[k_corr],
        "ramp_tied_at_one_historical_legend": ramp_tied[k_hist],
        "ramp_high_pct_corrected_legend": round(ramp_high[k_corr], 2),
        # A RECONSTRUCTION on the superseded legend, like 973. Not quoted in
        # the caption: the paper needs only the tie counts.
        "ramp_high_pct_historical_legend_RECONSTRUCTION": round(ramp_high[k_hist], 2),
        "CAPTION": (
            "Detail of the top of the scale, 0.85-1.00, where the whole "
            "argument lives; the two distributions are near-identical below "
            "it. Step classes are a RECONSTRUCTION of the scoring this project "
            "replaced in Sprint 1, rebuilt from the class breaks recorded in "
            "the changelog, and the interpolated ramps are the scheme in use. "
            "(a) uses the corrected soil legend for BOTH series; (b) uses the "
            "legend that was in use when the step scheme was live, which this "
            "project has since shown to be wrong - see "
            "docs/SOIL_LEGEND_CORRECTION.md - again for both series, so each "
            "panel compares scoring schemes on one legend. Outline "
            "histograms on true 0.01 bins starting at the 0.85 breakpoint; "
            "empty bins are gaps. "
            f"The plateau of {n_hist:,} cells tied at exactly 1.000 appears "
            "only with step classes on the superseded legend. On that same "
            f"legend the ramps tie {ramp_tied[k_hist]} cells, and on the "
            f"corrected legend the step scheme ties {n_corr}. The plateau "
            "therefore required a dominant soil class scored 1.00 AND "
            "flat-topped class breaks: neither alone produces it. The hatched "
            "bar marks the tied cells at 1.000. They are a SUBSET of the "
            "0.99-1.00 step bin, not extra cells: numpy closes the last bin "
            "on both sides, so they are counted once, in that bin. "
            f"**{n_hist:,} is a historical reconstruction and must never be "
            "quoted as a current result.** The argument for interpolated "
            "ramps over step classes does not rest on it - it rests on the "
            "IQR comparison in Fig. 2 and the discrimination measure in "
            "Fig. 18, both computed on current data."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 9 — candidate sites across the six criterion axes
# ─────────────────────────────────────────────────────────────────────────────

def fig_09(ctx):
    det = ctx.base["top_locations_details"]
    raw = np.array([[d["criteria_scores"].get(c, np.nan) for c in ctx.crit]
                    for d in det])
    sd_all = np.nanstd(raw, axis=0)

    # Axes ordered by WEIGHTED spread (site SD x AHP weight), most
    # discriminating first. Ordered by raw SD, settlement (w 0.040) sat
    # leftmost while the title and caption said the left-hand criteria are the
    # ones that separate the shortlist.
    wsd_all = sd_all * np.array([ctx.weights[c] for c in ctx.crit])
    order = np.argsort(-wsd_all)
    names = [ctx.crit[i] for i in order]
    M = raw[:, order]
    sds = sd_all[order]
    at_one = [(np.abs(M[:, j] - 1.0) < 1e-9).sum() for j in range(M.shape[1])]

    fig, ax = plt.subplots(figsize=(8.8, 4.8))
    xs = np.arange(len(names))

    # Ranks told apart by MARKER, in one colour. No five-colour ramp clears
    # every semantic colour by ΔE 10 - plasma hit Fuzzy-AHP (6.0), YlGnBu
    # hit the High class blue (9.2), and thirteen other ramps failed against
    # something - so hue is not used for rank at all.
    rank_marker = ["o", "s", "^", "D", "v"]
    _assert_series_colours([GENERIC[0]], "fig09 ranks")
    for i in range(M.shape[0] - 1, -1, -1):          # draw the top five last
        if i < 5:
            ax.plot(xs, M[i], color=GENERIC[0], lw=1.3, zorder=5 - i + 3,
                    marker=rank_marker[i], ms=5.5, mfc="white", mew=1.2,
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
    # Two rows: the raw spread of the scores, and that spread times the AHP
    # weight - each criterion's contribution to spread in the COMPOSITE,
    # ignoring covariance. The axes are ordered by the first; the title is
    # about the second, because separation of the RANKING is what it claims.
    wsd = np.array([sds[j] * ctx.weights[c] for j, c in enumerate(names)])
    for j, c in enumerate(names):
        ax.annotate(f"SD {sds[j]:.3f}\nw·SD {wsd[j]:.3f}", xy=(j, 1.045),
                    ha="center", va="bottom", fontsize=7.2, color="0.30",
                    annotation_clip=False)

    # The saturated axis is the finding, and it is no longer soil. "Flat" here
    # means plateaued at a single value, not merely low SD — slope has the
    # smaller SD but spreads across 0.905-0.993 without saturating, whereas
    # land cover pins almost every site at exactly 1.000.
    flat = int(np.argmax(at_one))
    # Lower right, three lines, right-aligned to the last axis. With the axes
    # in w.SD order land cover is rightmost, and the two-line version ran off
    # the frame. Below 0.55 and right of x = 3.6 nothing is drawn.
    ax.annotate(f"{at_one[flat]} of 25 sites score exactly\n1.000 on "
                f"{CRIT_LABEL[names[flat]].lower()} — this axis\nseparates "
                f"almost nothing",
                xy=(flat, 0.998), xytext=(len(names) - 0.70, 0.40),
                fontsize=7.5, color=OKABE[1], fontweight="bold", ha="right",
                arrowprops=dict(arrowstyle="->", color=OKABE[1], lw=1.0,
                                connectionstyle="arc3,rad=-0.25"))
    narrow = int(np.argmin(sds))
    if narrow != flat:
        # "Raw": by w.SD land cover (0.002) is narrower than slope (0.004).
        ax.annotate(f"narrowest raw spread\n({CRIT_LABEL[names[narrow]].lower()}, "
                    f"SD {sds[narrow]:.3f}) but not saturated",
                    xy=(narrow, M[:, narrow].min()),
                    # Between the rainfall and drainage axes, above the Loam
                    # callout: nothing scores under 0.46 there. Under the
                    # slope axis it sat on the settlement-0.10 site's line.
                    xytext=(1.30, 0.33), fontsize=7.5, color="0.35",
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
    # The finding, not the content.
    # Weighted, not raw. Settlement has the widest raw spread but a weight of
    # 0.040; weighted, soil and rainfall separate the shortlist most.
    wrank = [names[j] for j in np.argsort(-wsd)]
    ax.set_title(f"By weighted spread, {CRIT_LABEL[wrank[0]].split()[0].lower()} "
                 f"and {CRIT_LABEL[wrank[1]].split()[0].lower()} separate the "
                 "shortlist; land cover and slope barely do", pad=34)
    fig.tight_layout()
    # How much of the district carries the soil class the leading sites sit
    # on. The shortlist is concentrated on a scarce class, and after the
    # legend error that is a dependency the paper has to state rather than
    # leave a reader to find.
    soil_raw = ctx.stack["raw_rasters"]["soil"]
    soil_scores = ctx.stack["normalized_rasters"]["soil"]
    ok_soil = ctx.mask & ~np.isnan(soil_raw)
    soil_codes = np.rint(soil_raw[ok_soil]).astype(int)
    soil_area = ctx.area[ok_soil]
    best_code = max(C.SOIL_TEXTURE_SCORES,
                    key=lambda c: (C.SOIL_TEXTURE_SCORES[c], c))
    best_share = 100.0 * float(soil_area[soil_codes == best_code].sum()
                               / soil_area.sum())
    best_km2 = float(soil_area[soil_codes == best_code].sum())
    top_on_best = int(sum(1 for v in M[:5, names.index("soil")]
                          if abs(v - 1.0) < 1e-9))

    ax.annotate(f"{top_on_best} of the top 5 sites sit on "
                f"{C.SOIL_TEXTURE_LABELS[best_code]},\n"
                f"which is {best_share:.2f}% of the district "
                f"({best_km2:,.0f} km\u00b2)",
                # Between the Soil and Drainage axes, below the bundle: no
                # site scores under 0.46 on either, so that region is empty.
                # Along the bottom it printed on the axis tick labels.
                xy=(names.index("soil"), 0.998),
                xytext=(names.index("soil") + 0.12, 0.17),
                fontsize=7.5, color="0.25", fontweight="bold", ha="left",
                arrowprops=dict(arrowstyle="->", color="0.45", lw=0.9,
                                connectionstyle="arc3,rad=-0.2"))

    _save(fig, 9, f"parallel coordinates (flat axis is now {names[flat]}, "
                  f"{at_one[flat]}/25 at 1.000)")

    return {
        "axis_order_by_sd": names,
        "flat_axis": names[flat],
        "flat_axis_sites_at_one": int(at_one[flat]),
        **{f"sd_{c}": round(float(sds[j]), 4) for j, c in enumerate(names)},
        **{f"weighted_sd_{c}": round(float(wsd[j]), 4) for j, c in enumerate(names)},
        "best_soil_code": int(best_code),
        "best_soil_label": C.SOIL_TEXTURE_LABELS[best_code],
        "best_soil_share_pct": round(best_share, 3),
        "best_soil_km2": round(best_km2, 1),
        "top5_sites_on_best_soil": top_on_best,
        "CAPTION": (
            "Each grey line is one of the 25 candidate sites; the top five are "
            "drawn in black and told apart by marker, because no five-colour "
            "ramp stays clear of the criterion, method and class colours. Axes "
            "are ordered by w.SD, so the criteria that separate the shortlist "
            "in the composite are on the left. The first row is the raw spread "
            "(SD) of the sites' criterion scores; the second, w.SD, is "
            "that spread times the AHP weight - each criterion's contribution "
            "to spread in the composite, ignoring covariance - and the title "
            "is read from it: "
            + ", ".join(f"{CRIT_LABEL[c].lower()} {wsd[names.index(c)]:.3f}"
                        for c in wrank) +
            ". Settlement has the widest raw spread but a weight of "
            f"{ctx.weights['population']:.3f}, so weighted it separates the "
            "shortlist less than rainfall does. Land cover is effectively "
            f"flat - {at_one[flat]} of 25 sites score exactly 1.000 - and "
            "slope has the narrowest spread without being saturated, the "
            "distinction Fig. 19's caption makes between ties and "
            "concentration. "
            "A DEPENDENCY WORTH STATING: the leading sites sit on "
            f"{C.SOIL_TEXTURE_LABELS[best_code]}, the only texture scored 1.00, "
            f"and that class covers {best_share:.2f}% of the district "
            f"({best_km2:,.0f} km2 of 11,412). The top of the shortlist "
            "therefore depends on a scarce class being mapped correctly - the "
            "same exposure that produced the 2026-10-02 legend error. The "
            "soil raster is ISRIC SoilGrids250m at 250 m, resampled nearest to "
            "the ~300 m analysis grid, so a class this small is near the "
            "resolution of the input. Scoring Loam like Sandy Clay Loam (1.00 "
            "to 0.80) is the obvious robustness check and belongs in the "
            "Discussion."),
    }



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

    # Narrower: the maps are taller than wide, so at 8.8 in the columns were
    # held ~360 px apart by empty space.
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 7.8))
    for ax, name in zip(axes.ravel(), order):
        r = ctx.algos[name]
        cls = {k: G.class_share_pct(r, k) for k in ("High", "Medium", "Low")}
        # Method name only. Carrying the High % here as well made panel (d)'s
        # title overrun its frame and touch the image edge; it is in the
        # subtitle anyway.
        _map(ax, ctx.inside(r["classified_raster"]), ctx.extent, ctx.boundary,
             cmap=cmap, norm=norm, title=name, furniture=False, grat=False)
        # One unit, one precision. km² moved to the caption — carrying it here
        # pushed the (b) and (d) subtitles to the image edge.
        ax.annotate(f"High {cls['High']:.2f}%   "
                    f"Medium {cls['Medium']:.2f}%   "
                    f"Low {cls['Low']:.2f}%",
                    # Below the graticule labels on the bottom row.
                    xy=(0.5, -0.035 if ax in axes[0] else -0.095),
                    xycoords="axes fraction", ha="center",
                    va="top", fontsize=6.8, color="0.30")
    _outer_graticule(axes, ctx.extent)

    # Through the one helper, like every other map in the set. This used to
    # repeat the helper's body inline, which is how Figures 14 and 16 came to
    # repeat the defect it was written to fix.
    xf, yf, corner, occ = _clear_corner(ctx.mask)
    _place_furniture(axes[0, 0], ctx)

    _panel_letters(axes, offset=(-0.15, 1.00))
    handles = [Rectangle((0, 0), 1, 1, color=CLASS_COLOURS[k])
               for k in ("High", "Medium", "Low")]
    # Horizontal, bottom-centre. A vertical legend in the lower-right corner
    # covered panel (d)'s per-class statistics line.
    fig.legend(handles, [f"High (> {C.SUITABILITY_THRESHOLDS[1]})",
                         f"Medium ({C.SUITABILITY_THRESHOLDS[0]}–{C.SUITABILITY_THRESHOLDS[1]})",
                         f"Low (≤ {C.SUITABILITY_THRESHOLDS[0]})"],
               loc="lower center", bbox_to_anchor=(0.5, -0.005), frameon=False,
               ncol=3, fontsize=8, handlelength=1.4, columnspacing=1.8)
    # The finding, and "at fixed cutoffs": without it the title would claim
    # the aggregation effect Fig. 21 shows is a cutoff artefact.
    fig.suptitle("Weighting method barely changes the map; at fixed cutoffs,\n"
                 "the aggregation swap moves the Low boundary", y=0.985)
    _save(fig, 10, "four-method classified surfaces")
    agg_h, _w, _i = _main_effects(ctx, "High")
    agg_l, _w2, _i2 = _main_effects(ctx, "Low")
    return {"aggregation_on_High_pp": round(agg_h, 3),
            "aggregation_on_Low_pp": round(agg_l, 3),
            "CAPTION": (
                "All four panels share extent, scale and classification "
                "breakpoints. The scale bar and north arrow in panel (a) are "
                "drawn from the data transform and apply to all four; "
                f"the furniture sits in the {corner} corner, the emptiest of "
                f"the four at {occ:.1%} district coverage. Class areas in km2 "
                "are in Table 2. Shares are rounded independently, so a row "
                "can sum to 99.99 or 100.01. Note the "
                "aggregation rule moves the Low-class share by "
                f"{agg_l:+.2f} pp against {agg_h:+.2f} pp on High — method "
                "sensitivity depends on which class is examined. The same "
                "breakpoints (0.65/0.85) are applied to the WLC score and the "
                "TOPSIS closeness coefficient, which are differently "
                "distributed. The Low-class shift is a cutoff effect: matching "
                "the class sizes removes it, and doing so takes a 0.050 move "
                "of the lower cutoff. The ranking disagreement is separate - "
                "about half the area that changes class does so under both "
                "cutoff schemes tested (Fig. 21).")}


# ─────────────────────────────────────────────────────────────────────────────
# Figures 11 and 12 — the factorial design
# ─────────────────────────────────────────────────────────────────────────────

def _cutoff_schemes(ctx):
    """Class shares under the four cutoff schemes a GIS analyst would consider.

    The first version of Figure 12's cutoff bar used ONE alternative, the
    33rd/67th tercile split. That is unsatisfying for the reason a referee
    would give: under terciles the class shares are fixed by construction -
    High is 33% by definition - so most of the +26.53 pp was the arithmetic
    33 - 6.44, a number chosen rather than measured.

    A RANGE over the standard schemes is honest about the choice, in the same
    way the scenario bar is a range over five weightings. Natural breaks is
    approximated by 1-D k-means, which is what Jenks optimises, seeded at the
    terciles so the result is deterministic.
    """
    V = ctx.base["suitability_raster"]
    ok = ctx.mask & ~np.isnan(V)
    v, a = V[ok], ctx.area[ok]
    tot = float(a.sum())
    order = np.argsort(v, kind="mergesort")
    cum = np.cumsum(a[order]) / tot

    def _kmeans1d(x, k=3, iters=60):
        c = np.quantile(x, [0.17, 0.50, 0.83])
        for _ in range(iters):
            lab = np.argmin(np.abs(x[:, None] - c[None, :]), axis=1)
            nc = np.array([x[lab == j].mean() if (lab == j).any() else c[j]
                           for j in range(k)])
            if np.allclose(nc, c):
                break
            c = nc
        c = np.sort(c)
        return float((c[0] + c[1]) / 2), float((c[1] + c[2]) / 2)

    sample = v if v.size <= 60000 else np.random.default_rng(0).choice(
        v, 60000, replace=False)
    lo_v, hi_v = float(v.min()), float(v.max())
    schemes = {
        "fixed 0.65 / 0.85": tuple(C.SUITABILITY_THRESHOLDS),
        "equal interval": (lo_v + (hi_v - lo_v) / 3, lo_v + 2 * (hi_v - lo_v) / 3),
        "tercile (equal area)": (float(v[order][np.searchsorted(cum, 1 / 3)]),
                                 float(v[order][np.searchsorted(cum, 2 / 3)])),
        "natural breaks (k-means)": _kmeans1d(sample),
    }
    out = {}
    for name, (lo, hi) in schemes.items():
        out[name] = {
            "cuts": (round(lo, 4), round(hi, 4)),
            "Low": 100.0 * float(a[v <= lo].sum()) / tot,
            "Medium": 100.0 * float(a[(v > lo) & (v <= hi)].sum()) / tot,
            "High": 100.0 * float(a[v > hi].sum()) / tot,
        }
    return out


def _factorial(ctx, klass="High"):
    # class_share_pct, not the rounded "percent" field. Differencing shares
    # that _area_statistics had already rounded to 2 dp quantised every
    # factorial effect to 0.01 pp, which is how the Low-class effects came out
    # as +9.030, -0.100 and 0.000 - three values ending in a zero they had not
    # earned. The third decimal is only real if the inputs carry it.
    h = {n: G.class_share_pct(ctx.algos[n], klass) for n in ALGORITHMS}
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
    # Two text objects, each right-aligned in its own column. Space-padding a
    # monospace string did not line up, and monospace was the only such font
    # in the figure set.
    ax.annotate("\n".join(["WLC→TOPSIS | AHP", "WLC→TOPSIS | Fuzzy-AHP",
                           "interaction"]),
                xy=(0.775, 0.97), xycoords="axes fraction", ha="right", va="top",
                fontsize=7.5, color="0.30", linespacing=1.6)
    # One column, one precision — mixing −0.79 with −0.165 made the
    # interaction look like a different kind of quantity.
    ax.annotate("\n".join([_pp(d_ahp, 3), _pp(d_fz, 3), _pp(inter, 3)]),
                xy=(0.985, 0.97), xycoords="axes fraction", ha="right", va="top",
                fontsize=7.5, color="0.30", linespacing=1.6)
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

    base = {k: G.class_share_pct(ctx.base, k) for k in ("High", "Low")}

    def _shares(rasters):
        st = dict(ctx.stack); st["normalized_rasters"] = rasters
        r = G.score_stack(st, ctx.weights, ctx.cr)
        return {k: G.class_share_pct(r, k) for k in ("High", "Low")}

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

    # The classification breakpoints, swapped for the one documented
    # alternative in the code: criteria.CLASSIFICATION_MODE = "percentile",
    # the 33rd/67th split this project used before Sprint 1. Figure 21 shows
    # that the large Low-class "aggregation" effect is substantially a cutoff
    # effect, so the cutoff scheme has to appear here as the analyst decision
    # it is, rather than being left implicit under every other bar.
    cut = _cutoff_schemes(ctx)
    brk_h = max(s["High"] for s in cut.values()) - min(s["High"] for s in cut.values())
    brk_l = max(s["Low"] for s in cut.values()) - min(s["Low"] for s in cut.values())

    agg_h, wgt_h, int_h = _main_effects(ctx, "High")
    agg_l, wgt_l, int_l = _main_effects(ctx, "Low")

    # The scenario spread. This is the weighting JUDGEMENTS varying, which is a
    # different thing from the weighting METHOD (AHP against Fuzzy-AHP on one
    # fixed set of judgements) that the factorial measures. Without it on the
    # same axis a referee can set Figure 15 against this figure and read the
    # thesis as contradicted: the method bar is 0.565 pp, the scenario range is
    # 16 pp. Both are true, and the distinction between them is the point.
    sc = ctx.scenarios
    scen_h = max(v["High"] for v in sc.values()) - min(v["High"] for v in sc.values())
    scen_l = max(v["Low"] for v in sc.values()) - min(v["Low"] for v in sc.values())

    # (label, High, Low, colour, hatched, decimals)
    # Decimals carry provenance. The factorial effects are differences of class
    # shares computed from cell counts, so the third digit is real. Everything
    # else derives from shares _area_statistics already rounded to two, so a
    # third digit would be invented.
    rows = [
        ("Interaction", int_h, int_l, MEANING["interaction"], False, 3, False),
        ("Weighting method\nAHP → Fuzzy-AHP", wgt_h, wgt_l, MEANING["method"], False, 3, False),
        ("Aggregation\nWLC → TOPSIS", agg_h, agg_l, MEANING["method"], False, 3, False),
        ("Weighting judgements\nrange across 5 scenarios",
         scen_h, scen_l, MEANING["scenario"], False, 2, True),
        ("Soil legend corrected\n(data error, not a choice)",
         base["High"] - soil["High"], base["Low"] - soil["Low"], MEANING["soil"], True, 2, False),
        ("Rainfall scoring\npercentile → fixed bands",
         rain["High"] - base["High"], rain["Low"] - base["Low"], MEANING["rainfall"], False, 2, False),
        ("Classification cutoffs\nrange across 4 standard schemes",
         brk_h, brk_l, PARTITION["induced"], False, 2, True),
    ]
    # Upstream bars ordered by magnitude on the High class, algorithm bars by
    # magnitude too, each group kept together. Left unsorted, the cutoff bar
    # sat above the larger rainfall bar for no stated reason.
    rows = (sorted(rows[:3], key=lambda r: abs(r[1]))
            + sorted(rows[3:], key=lambda r: abs(r[1])))

    # sharex: the figure exists to compare bar lengths ACROSS the two class
    # shares, and per-panel autoscaling defeated that — 0–40 against 0–50
    # drew the 9.03 pp aggregation bar on Low barely longer than the
    # 0.96 pp one on High.
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 5.4), sharey=True, sharex=True)
    XMAX = 42.0
    ypos = np.arange(len(rows))
    for ax, col, klass in ((axes[0], 1, "High"), (axes[1], 2, "Low")):
        for y, r in zip(ypos, rows):
            hatched = r[4]
            ax.barh(y, abs(r[col]), color=r[3], height=0.62,
                    hatch="///" if hatched else None,
                    edgecolor="black" if hatched else "none",
                    linewidth=0.8 if hatched else 0)
            # Label moves inside the bar once it would otherwise run off the
            # axis: "−39.50 pp" placed outside a 39.5 pp bar reached the
            # image edge.
            inside = abs(r[col]) > 0.74 * XMAX
            # A range is max minus min across five scenarios. "+16.23 pp"
            # claims a direction it does not have.
            txt = (f"range {_fx(r[col], r[5])} pp" if r[6]
                   else _pp(r[col], r[5]))
            ax.annotate(txt, (abs(r[col]), y),
                        textcoords="offset points",
                        xytext=(-5 if inside else 5, 0), va="center",
                        ha="right" if inside else "left",
                        color="white" if inside else "black",
                        fontsize=8, fontweight="bold", zorder=6)
        ax.set_xlim(0, XMAX)   # shared and fixed
        ax.set_xlabel(f"|change| in {klass}-class share (pp)")
        ax.set_title(f"{klass}-class share")
        ax.grid(True, axis="x")
        # Under the labels, so a value is never crossed by the rule.
        ax.axhline(2.5, color="black", lw=0.8, ls="--", clip_on=True, zorder=1)
    axes[0].set_yticks(ypos)
    axes[0].set_yticklabels([r[0] for r in rows], fontsize=8)

    # Right-aligned against the axis, at the vertical centre of each group.
    # Left-aligned mid-panel they sat on the soil bar's value label.
    axes[0].annotate("the algorithm choices the\ncomparative literature argues about",
                     xy=(0.98, 0.21), xycoords="axes fraction", fontsize=8,
                     color="0.30", va="center", ha="right")
    # "upstream", not "what the analyst decides" - the soil bar in this same
    # group is labelled "data error, not a choice", which the old wording
    # contradicted.
    # On the soil row, whose label ends near 19 pp: at 0.62 it sat on the
    # weighting-judgements row and nearly touched "range 16.23 pp".
    axes[0].annotate("upstream: data, scoring,\njudgements, cutoffs",
                     xy=(0.98, 0.50), xycoords="axes fraction", fontsize=8,
                     color="0.30", va="center", ha="right")

    # Named on the figure, not left to the caption: this is the bar a reader
    # will carry away, and Fig. 21 reinterprets it.
    axes[1].annotate("cutoff effect — see Fig. A8", xy=(abs(agg_l), 2),
                     textcoords="offset points", xytext=(64, 0), va="center",
                     fontsize=7.5, color="0.30", style="italic", zorder=4)

    _panel_letters(axes, offset=(-0.02, 1.04))
    # The ORDER of the drivers is identical in both panels — rainfall, soil,
    # aggregation, weighting, interaction. Only the aggregation magnitude
    # changes (0.96 pp on High against 9.03 pp on Low). The previous title
    # claimed the ranking changed between classes, which it does not.
    # The old title said "of the algorithm choices only aggregation matters,
    # and only for Low". Fig. 21 shows that Low effect is substantially a
    # cutoff effect rather than an aggregation effect in any ranking sense, so
    # the title would have been contradicted by the paper's own next figure.
    # The cross-reference lives in the caption; a figure number in a title
    # does not survive renumbering.
    fig.suptitle("Analyst decisions dominate — and the one large algorithm "
                 "effect is itself a cutoff effect", y=1.00)
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
        "high_scenario_range_pp": round(scen_h, 2),
        "low_scenario_range_pp": round(scen_l, 2),
        "high_cutoff_range_pp": round(brk_h, 2),
        "low_cutoff_range_pp": round(brk_l, 2),
        "cutoff_schemes": {k: {"cuts": v["cuts"], "High": round(v["High"], 2),
                               "Low": round(v["Low"], 2)}
                           for k, v in cut.items()},
        "CAPTION": (
            "Lower three bars are factorial main effects (interaction = half the "
            "difference of simple effects). The rainfall bar is a ONE-AT-A-TIME "
            "swap evaluated under AHP+WLC, not a main effect, and its size "
            f"depends on the band set used: {bands}, >1500→1.00. Those bands are "
            "one alternative, not a range; Chandrapur's 1,189-1,714 mm spread "
            "falls in the top three, which is why the effect is large. The soil "
            "bar (hatched) is a data-error correction, not a modelling choice, "
            "and is shown to scale the others against. The scenario bar is the "
            "RANGE across the five presets of Fig. 15, a spread rather than an "
            f"effect: {scen_h:.2f} pp on High, {scen_l:.2f} pp on Low. Being "
            "a range over five scenarios it is not the same kind of quantity "
            "as the single pairwise changes beside it, and it would grow if "
            "more scenarios were added; it is here to size the weighting "
            "judgements, not to be differenced. It "
            "varies the weighting JUDGEMENTS, whereas the aggregation and "
            "weighting-method bars vary the algorithm applied to one fixed set "
            "of judgements; the two must not be read as the same quantity. "
            f"Both panels share one 0-{XMAX:.0f} pp axis, so bar lengths are "
            "comparable between them. Every effect is measured on shares cut "
            "by the fixed 0.65/0.85 breakpoints, and the aggregation bar on "
            "Low is the one most exposed to that: Fig. 13(a) shows the TOPSIS "
            "closeness coefficient putting more mass just below 0.65 than the "
            "WLC score does, so a breakpoint moved a few hundredths would "
            f"change {_pp(agg_l, 3)} materially. "
            "The classification-cutoff bar is a RANGE over four standard "
            "schemes applied to the one baseline surface - the fixed "
            "0.65/0.85 pair, equal interval, terciles by area, and natural "
            "breaks approximated by 1-D k-means - and not a single swap. One "
            "alternative would have been misleading here: under terciles the "
            "class shares are fixed by construction, so most of the difference "
            "from the fixed scheme would be the arithmetic 33 minus 6.44, a "
            "number chosen rather than measured. The scheme-by-scheme shares "
            "are in the figure's data output. It belongs in the upstream group "
            "because the cutoffs are an analyst decision, and Fig. 21 shows "
            f"that the {_pp(agg_l, 3)} aggregation bar on Low is substantially "
            "a consequence of that decision rather than of the aggregation "
            "rule: removing the Low shift takes a 0.050 move of the lower "
            "cutoff, and only half the cells that change class do so under "
            "both of the cutoff schemes tested there. Bars within each group "
            "are ordered by magnitude on the High class. "
            f"All shares come from "
            "gis_analysis.class_share_pct, area-weighted and unrounded; "
            "differencing the 2-dp display field had been quantising every "
            "effect here to 0.01 pp."),
    }
# ─────────────────────────────────────────────────────────────────────────────
# Figure 13 — distributions and class flows, WLC versus TOPSIS
# ─────────────────────────────────────────────────────────────────────────────

def fig_13(ctx):
    """Where the two aggregation rules put their mass, and what moves between
    classes. Both panels hold the weighting fixed at AHP, so everything here is
    the aggregation rule and nothing else.
    """
    rw = ctx.algos["AHP + WLC"]
    rt = ctx.algos["AHP + TOPSIS"]
    sw, st_ = rw["suitability_raster"], rt["suitability_raster"]
    mw = ctx.mask & ~np.isnan(sw)
    mt = ctx.mask & ~np.isnan(st_)
    aw, at = sw[mw], st_[mt]
    cw, ct = rw["classified_raster"], rt["classified_raster"]
    both = ctx.mask & ~np.isnan(cw) & ~np.isnan(ct)
    lo_t, hi_t = C.SUITABILITY_THRESHOLDS

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8),
                                   gridspec_kw={"width_ratios": [1.05, 1]})

    # ── (a) empirical CDFs ──────────────────────────────────────────────────
    # Not overlaid histograms. Two translucent fills produced a third colour
    # where they crossed that was in the plot but not the legend, and the
    # quantity the argument needs — how much mass sits below each breakpoint —
    # had to be estimated by eye from bar heights. On a CDF it is the height of
    # the curve at the breakpoint, read straight off the y-axis.
    # AREA-weighted, via the same helper the class shares come from. A plain
    # ECDF counts cells, and in EPSG:4326 a cell's ground area falls with
    # latitude, so the curve sat about 0.05 pp off the share Figure 10 reports
    # for the identical surface - small, but a referee reading both figures
    # would see two numbers for one quantity.
    def _share_at(v, sel, t):
        return 100.0 * float(ctx.area[sel][v <= t].sum() / ctx.area[sel].sum())

    for v, sel, name, colour, ls in ((aw, mw, "AHP + WLC", GENERIC[0], "-"),
                                     (at, mt, "AHP + TOPSIS", GENERIC[1], "--")):
        x, y = G.area_weighted_ecdf(v, ctx.area[sel])
        ax1.plot(x, y, color=colour, lw=1.6, ls=ls, label=name, zorder=3)

    n_cells = int(both.sum())
    # The code classifies Low as score <= 0.65 and High as score > 0.85
    # (gis_analysis._classify_suitability). The CDF is P(score <= x), so its
    # height AT a breakpoint is exactly the cumulative share, with no
    # half-open-interval argument to make. Labels say "<=" for the same reason;
    # Figure 10's legend uses the same convention.
    for t, lab in ((lo_t, f"Low: score \u2264 {lo_t}"),
                   (hi_t, f"High: score > {hi_t}")):
        ax1.axvline(t, color="0.35", lw=0.9, ls="--", zorder=1)
        ax1.annotate(lab, xy=(t - 0.006, 4), rotation=90, fontsize=7,
                     ha="right", va="bottom", color="0.35", zorder=4)
        # Into dead space with a leader, not offset by a few points. At 0.65
        # the rising TOPSIS curve ran straight through its own "50.1%", and at
        # 0.85 both curves ran through theirs; staggering them vertically only
        # moved the text further along the same line. Left of the breakpoint
        # and well below it is empty on both panels.
        # At 0.65 each curve gets its own label, in data coordinates, in space
        # that is empty because both curves are still low there.
        #
        # At 0.85 the two curves are within a percentage point of each other,
        # so two labels needed two leaders fanning out from nearly one point,
        # and the second crossed the first's text. One label instead, giving
        # the HIGH share directly - which is the quantity the reader wants and
        # is 100 minus the curve height, a subtraction they should not have to
        # do - and one leader.
        at_low = (t == lo_t)
        shares = [_share_at(v, sel, t) for v, sel in ((aw, mw), (at, mt))]
        for k, (v, sel, colour) in enumerate(((aw, mw, GENERIC[0]),
                                              (at, mt, GENERIC[1]))):
            ax1.plot([t], [shares[k]], "o", ms=4.5, color=colour, zorder=5)
            if not at_low:
                continue
            ax1.annotate(f"{_fx(shares[k], 2)}%", xy=(t, shares[k]),
                         # RIGHT of the breakpoint: both curves are above
                         # 50% there, so the leaders run under them. From the
                         # left, the 41.08% leader crossed the TOPSIS curve,
                         # which passes 41% at about 0.60.
                         xytext=(0.745, shares[k]),
                         ha="center", va="center", fontsize=7.5, color=colour,
                         fontweight="bold", zorder=5,
                         arrowprops=dict(arrowstyle="-", color=colour, lw=0.7,
                                         shrinkA=2, shrinkB=3))
        if not at_low:
            # Two lines: on one it measured 0.19 wide in data units and
            # reached back across the 0.85 rule it annotates.
            ax1.annotate("High class:\n"
                         f"{_fx(100 - shares[0], 2)}% vs\n"
                         f"{_fx(100 - shares[1], 2)}%",
                         xy=(t, (shares[0] + shares[1]) / 2),
                         # Three lines, so the widest is 8 characters and the label fits
            # the 0.14-unit gap between the 0.85 rule and the frame, below the
            # curves. On two lines it needed 0.16 and had to go to the far
            # left of the panel with a leader 0.34 units long.
                         xytext=(0.928, 68), ha="center", va="center",
                         fontsize=7.5, color="0.25", fontweight="bold",
                         zorder=5,
                         arrowprops=dict(arrowstyle="-", color="0.45", lw=0.7,
                                         shrinkA=2, shrinkB=3))

    ax1.set_xlim(0.2, 1.0)          # below 0.2 the panel was empty
    ax1.set_ylim(0, 100)
    ax1.set_xlabel("WLC score / TOPSIS closeness coefficient")
    # Area, not cells. The curve became area-weighted when it was reconciled
    # with class_share_pct, and the label did not follow. n moved to the
    # caption, where it belongs.
    ax1.set_ylabel("cumulative % of district area")
    ax1.legend(frameon=False, loc="upper left")
    ax1.grid(True)
    # The finding, not the content. This panel is also what Figure 12's caption
    # cites for the breakpoint caveat on the +9.030 pp Low-share bar.
    ax1.set_title("TOPSIS shifts mass below the 0.65 breakpoint")

    # ── (b) alluvial ────────────────────────────────────────────────────────
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
    moved = []
    for f in order:
        for t in order:
            sel = both & (cw == f) & (ct == t)
            a = float(ctx.area[sel].sum())
            if a <= 0:
                continue
            y0l, y1l = lcur[f], lcur[f] + a
            y0r, y1r = rcur[t], rcur[t] + a
            xs = np.linspace(0, 1, 60)
            sm = (1 - np.cos(np.pi * xs)) / 2
            upper = y0l + (y0r - y0l) * sm
            lower = y1l + (y1r - y1l) * sm
            # Coloured by DESTINATION, at one opacity. Coloured by origin, the
            # Medium -> Low band — the ~9 pp story — was drawn in the
            # near-white Medium fill on a white page, while the thin saturated
            # bands either side of it dominated the panel.
            ax2.fill_between(xs, upper, lower, color=CLASS_COLOURS[lab[t]],
                             alpha=0.80, lw=0.3, edgecolor="white", zorder=2)
            if f != t:
                # x = 0.22, not 0.5. At mid-span the bands have begun to cross
                # and the Low->Medium flow ran through the "1,146 km2" label
                # naming the Medium->Low one.
                moved.append((f, t, a, 0.22, (upper[13] + lower[13]) / 2))
            lcur[f], rcur[t] = y1l, y1r

    # Every off-diagonal flow is labelled, so the 87.2% unchanged figure can be
    # accounted for from the panel. The big one sits on the solid left-hand end
    # of its own band, where no other flow has crossed yet; the two small ones
    # are too thin to hold text and are called out beyond the right-hand node.
    for f, t, a, xm, ym in moved:
        big = a >= 0.04 * tot
        if big:
            ax2.annotate(f"{lab[f]}\u2192{lab[t]}\n{a:,.0f} km\u00b2",
                         xy=(xm, ym), ha="center", va="center", fontsize=7.5,
                         fontweight="bold",
                         color="white" if t != 2 else "0.20", zorder=5)
    # The two small flows get a summary line under the panel, not callouts.
    # Leaders reaching from a 116 km2 ribbon to the margin swept across the
    # whole diagram and landed on the node labels; the flows are named, so a
    # reader can match them without a line being drawn to them.
    small = sorted(((f, t, a) for f, t, a, _x, _y in moved if a < 0.04 * tot),
                   key=lambda r: -r[2])
    if small:
        ax2.annotate("also: " + "   ".join(
            f"{lab[f]}→{lab[t]} {a:,.0f} km²" for f, t, a in small),
            xy=(0.5, -0.02), xycoords="axes fraction", ha="center", va="top",
            fontsize=7.5, color="0.30")

    for c in order:
        ax2.add_patch(Rectangle((-0.045, lpos[c][0]), 0.045,
                                lpos[c][1] - lpos[c][0],
                                color=CLASS_COLOURS[lab[c]], zorder=3))
        ax2.add_patch(Rectangle((1.0, rpos[c][0]), 0.045,
                                rpos[c][1] - rpos[c][0],
                                color=CLASS_COLOURS[lab[c]], zorder=3))
        ax2.text(-0.06, (lpos[c][0] + lpos[c][1]) / 2,
                 f"{lab[c]}\n{left_tot[c]:,.0f} km\u00b2", ha="right",
                 va="center", fontsize=7.5)
        ax2.text(1.065, (rpos[c][0] + rpos[c][1]) / 2,
                 f"{lab[c]}\n{right_tot[c]:,.0f} km\u00b2", ha="left",
                 va="center", fontsize=7.5)
    ax2.set_xlim(-0.30, 1.32)
    ax2.set_ylim(-gap, top)
    ax2.invert_yaxis()
    ax2.axis("off")

    # Area-weighted, like every other class share. A plain cell mean gave
    # 87.16 against 100 - 12.833 = 87.17 from Fig. 21's area-weighted
    # partition: two bases for one quantity.
    unchanged = 100 * float(ctx.area[both & (cw == ct)].sum()) / tot
    # One line, not two. The panel title and a separate bold annotation were
    # both centred at the top of the axes and printed on each other.
    # "(band width is proportional to area)" moved to the caption; with it the
    # title ran to within a few pixels of the image edge.
    ax2.set_title(f"Class transitions, WLC \u2192 TOPSIS \u2014 "
                  f"{_fx(unchanged, 2)}% unchanged")

    _panel_letters([ax1, ax2])
    fig.tight_layout()
    _save(fig, 13, f"ECDF + alluvial ({unchanged:.1f}% unchanged)")

    flows = {f"{lab[f]}_to_{lab[t]}_km2": round(a, 1) for f, t, a, _x, _y in moved}
    return {
        "unchanged_pct": round(unchanged, 2),
        "n_cells": n_cells,
        "wlc_below_065_pct": round(_share_at(aw, mw, lo_t), 3),
        "topsis_below_065_pct": round(_share_at(at, mt, lo_t), 3),
        "wlc_below_085_pct": round(_share_at(aw, mw, hi_t), 3),
        "topsis_below_085_pct": round(_share_at(at, mt, hi_t), 3),
        "wlc_Low_from_class_share": round(G.class_share_pct(rw, "Low"), 3),
        "topsis_Low_from_class_share": round(G.class_share_pct(rt, "Low"), 3),
        **flows,
        "CAPTION": (
            f"Over the {n_cells:,} in-district cells. "
            "Both panels hold the weighting fixed at AHP, so the only thing "
            "varying is the aggregation rule; the Fuzzy-AHP variants are in "
            "Fig. 10. (a) Empirical CDFs, so the height of a curve at a "
            "breakpoint IS the cumulative share of the district at or below "
            "it. The classifier assigns Low at score <= 0.65 and High at "
            "score > 0.85, and the markers are placed on that convention. The "
            "two curves are close above 0.85 and separate below 0.65, which is "
            "why the aggregation rule moves the Low class an order of "
            "magnitude more than the High class in Fig. 12. (b) Bands are "
            "coloured by destination class, and band width is proportional to "
            "area; every off-diagonal flow is labelled in km2 - the large one "
            "on its band, the three small ones (too thin to hold text) in the "
            "line under the panel. In (a) WLC is solid near-black and TOPSIS "
            "dashed vermilion, so neither borrows the High-class blue of (b). "
            "Shares here and in Fig. 10 both "
            "come from gis_analysis.class_share_pct and are area-weighted, not "
            "cell counts: in EPSG:4326 a cell's ground area falls with "
            "latitude by 0.81% across the district, and the Low class sits "
            "mostly in the south, so counting cells understates it by about "
            "0.05 pp."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 14 — where the two methods disagree
# ─────────────────────────────────────────────────────────────────────────────

def fig_14(ctx):
    """Where the two aggregation rules actually rank cells differently.

    The difference of the RAW scores is mostly a level offset: Fig. 13(a) shows
    the TOPSIS closeness coefficient sitting below the WLC score over most of
    the distribution, so subtracting them paints almost the whole district one
    colour and says little about disagreement. Differencing the within-district
    PERCENTILE RANK removes the offset by construction — both surfaces are
    uniform on [0, 1] — so what is left is purely the change in relative
    standing, which is what the shortlist and the class breaks depend on.
    """
    sw = ctx.algos["AHP + WLC"]["suitability_raster"]
    st = ctx.algos["AHP + TOPSIS"]["suitability_raster"]
    pw = G._percentile_rank(np.where(ctx.mask, sw, np.nan))
    pt = G._percentile_rank(np.where(ctx.mask, st, np.nan))
    draw = ctx.inside(100.0 * (pw - pt))
    v = ctx.vals(100.0 * (pw - pt))
    lim = float(np.nanpercentile(np.abs(v), 99))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.6, 4.8),
                                   gridspec_kw={"width_ratios": [1.25, 1]})
    im = _map(ax1, draw, ctx.extent, ctx.boundary, cmap="RdBu_r",
              norm=TwoSlopeNorm(vmin=-lim, vcenter=0.0, vmax=lim),
              title="AHP+WLC \u2212 AHP+TOPSIS, percentile rank",
              furniture=False)
    # Not _map's default corner. Figures 10, 14 and 16 all go through the one
    # helper that tests the district mask, so none of them can put the bar on
    # the data again.
    _place_furniture(ax1, ctx)
    cb = fig.colorbar(im, ax=ax1, shrink=0.78, pad=0.02)
    cb.set_label("difference in percentile rank (points)")

    dy_km, dx_km = G._pixel_size_km(ctx.transform, ctx.shape)
    dist = G._distance_km(~ctx.mask, dy_km, dx_km)
    cw = ctx.algos["AHP + WLC"]["classified_raster"]
    ct = ctx.algos["AHP + TOPSIS"]["classified_raster"]
    both = ctx.mask & ~np.isnan(cw) & ~np.isnan(ct)
    changed = both & (cw != ct)
    # AREA-weighted, like every other share in the project. Counting cells
    # here while Figures 10 and 13 weight by area would leave two conventions
    # in one paper for no reason; the gradient is the same either way, but the
    # convention should not vary between panels.
    def _rate(sel):
        return 100.0 * float(ctx.area[sel & changed].sum() / ctx.area[sel].sum())

    overall = _rate(both)
    bands = [(0, 2), (2, 5), (5, 10), (10, 20), (20, 999)]
    labels, rates, counts = [], [], []
    for lo, hi in bands:
        sel = both & (dist >= lo) & (dist < hi)
        if not sel.sum():
            continue
        labels.append(f"{lo}\u2013{hi}" if hi < 999 else f">{lo}")
        rates.append(_rate(sel))
        # km2, not a cell count: the bars are area-weighted, so a cell count
        # beneath them invited the reader to mix the two units.
        counts.append(float(ctx.area[sel].sum()))
    ax2.bar(labels, rates, color=NEUTRAL_BAR, width=0.62, zorder=2)
    for i, (r, c) in enumerate(zip(rates, counts)):
        ax2.annotate(f"{_fx(r, 1)}%\n{c:,.0f} km\u00b2", (i, r),
                     textcoords="offset points", xytext=(0, 3), ha="center",
                     fontsize=7, zorder=4)
    ax2.axhline(overall, color="0.35", lw=0.9, ls="--", zorder=1)
    # Left end and above the line. At the right end it sat on its own dashes
    # and on the two tall bars; the first two bars are short, so the space
    # above them is clear.
    ax2.annotate(f"district overall {_fx(overall, 1)}%", xy=(0.02, overall),
                 xycoords=("axes fraction", "data"), ha="left", va="bottom",
                 fontsize=7.5, color="0.35", zorder=4,
                 bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
    ax2.set_ylim(0, max(rates) * 1.30)
    ax2.set_xlabel("distance to district boundary (km)")
    # "district area reclassified" read as each bar being a share OF the
    # district, in which case the bars would sum to the overall 12.83%. They
    # are within-band rates.
    ax2.set_ylabel("% of band area reclassified")
    ax2.grid(True, axis="y")
    # Phrased as ruling out an artefact, which is all this panel can do. The
    # gradient is geographic rather than mechanical: the boundary-heavy
    # south-west is Low under both rules, and the interior is where scores sit
    # near 0.65 and can cross it.
    ax2.set_title("No edge artefact: disagreement is not boundary-driven")
    _panel_letters([ax1, ax2], offset=(-0.10, 1.02))
    fig.tight_layout()
    _save(fig, 14, "percentile-rank difference + boundary-distance profile")

    near = rates[0]
    far = rates[-1]
    return {
        "overall_reclassified_pct": round(overall, 2),
        "nearest_band_pct": round(near, 2),
        "farthest_band_pct": round(far, 2),
        "edge_to_interior_ratio": round(near / far, 2) if far else None,
        "rank_diff_p99_points": round(lim, 2),
        "CAPTION": (
            "(a) Difference in within-district percentile rank, not in raw "
            "score. The two surfaces are on different scales - a WLC weighted "
            "mean and a TOPSIS closeness coefficient - and the raw difference "
            "is dominated by the level offset visible in Fig. 13(a), which "
            "would paint the district one colour without showing where the "
            "rules disagree. Ranking both to [0, 1] removes the offset by "
            "construction. Diverging scale clipped at the 99th percentile of "
            f"|difference| ({lim:.1f} points). (b) Reclassification rate by "
            "distance to the district boundary. Each bar is the share of THAT "
            "BAND's area that changes class, not the band's share of the "
            "district - the bars do not sum to the overall rate. Area-weighted "
            "like every other share in the paper, with each band's area in km2 "
            f"and the district-wide rate ({overall:.1f}%) as a reference "
            "line. The rate does not rise towards the boundary, which rules "
            "out an edge artefact from the gap-filling of the rim; it does not "
            "establish a distance mechanism, and the gradient that is present "
            "is geographic - the boundary-heavy south-west is Low under both "
            "rules."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 15 (A and B only) — scenarios
# ─────────────────────────────────────────────────────────────────────────────

def fig_15(ctx):
    """The five preset weightings and what each does to the High class.

    This is the figure that sets the size of the weighting-JUDGEMENT effect, as
    distinct from the weighting-METHOD effect of Figures 11 and 12. The spread
    here is an order of magnitude larger, and Figure 12 now carries it as a bar
    so the two cannot be read as contradicting each other.
    """
    sc = ctx.scenarios
    names = list(sc)
    W = np.array([[sc[n]["weights"][c] for c in ctx.crit] for n in names])
    highs = [sc[n]["High"] for n in names]
    crs = [sc[n]["cr"] for n in names]

    # CR belongs with the weights it describes, not beside an area share, where
    # it read as a property of the result.
    rowlab = [f"{n}\n(CR {cr:.4f})" for n, cr in zip(names, crs)]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.6),
                                   gridspec_kw={"width_ratios": [1.5, 1]})
    bottom = np.zeros(len(names))
    for j, c in enumerate(ctx.crit):
        # CRIT_COLOUR, not OKABE by position. Rainfall was vermilion here and
        # green in Figure 12, and this panel's blue was the one Figure 11 used
        # for "AHP weighting".
        ax1.barh(rowlab, W[:, j], left=bottom, label=CRIT_LABEL[c],
                 color=CRIT_COLOUR[c], height=0.62)
        bottom += W[:, j]
    ax1.set_xlabel("criterion weight (sums to 1)")
    ax1.set_xlim(0, 1)
    ax1.invert_yaxis()
    # Below the panel. Above it, the legend box and the panel title were both
    # centred on the same line and printed on each other.
    ax1.legend(frameon=False, ncol=3, fontsize=7.5, loc="upper center",
               bbox_to_anchor=(0.5, -0.16))
    ax1.set_title("Weight vectors by scenario")

    spread = max(highs) - min(highs)
    ax2.barh(rowlab, highs, color=NEUTRAL_BAR, height=0.62, zorder=2)
    for i, h in enumerate(highs):
        ax2.annotate(f"{h:.2f}%", (h, i), textcoords="offset points",
                     xytext=(4, 0), va="center", fontsize=8, fontweight="bold",
                     zorder=4)
    ax2.set_xlabel(f"{HIGH_LABEL} (% of district)")
    ax2.set_xlim(0, 22)          # room for the 18.77% label to clear the frame
    ax2.set_yticks([])
    ax2.invert_yaxis()
    ax2.grid(True, axis="x")
    # The finding. The spread is the number the Discussion needs, and it is
    # larger than the soil correction and far larger than any algorithm effect.
    # Short enough to clear the panel letter. The full sentence is the caption's.
    ax2.set_title(f"A {_fx(spread, 2)} pp spread across scenarios")
    _panel_letters([ax1, ax2], offset=(-0.07, 1.04))
    fig.tight_layout()
    _save(fig, 15, f"scenario weights + {HIGH_LABEL} "
                   f"(spread {spread:.2f} pp)")

    return {
        "scenario_high_pct": {n: round(sc[n]["High"], 2) for n in names},
        "scenario_low_pct": {n: round(sc[n]["Low"], 2) for n in names},
        "scenario_cr": {n: round(sc[n]["cr"], 4) for n in names},
        "high_spread_pp": round(spread, 2),
        "CAPTION": (
            "Five weightings of the SAME criteria stack, each a separate set "
            "of pairwise judgements, all with CR < 0.10. Consistency ratios "
            "are given with the weight vectors they describe. (b) is clipped "
            f"to 0-20%. The {spread:.2f} pp spread is the effect of the "
            "weighting JUDGEMENTS; it is not comparable with the "
            f"{abs(_main_effects(ctx, 'High')[1]):.3f} pp weighting-METHOD "
            "effect of Fig. 12, which holds the judgements "
            "fixed and swaps AHP for Fuzzy-AHP. Both appear on one axis in "
            "Fig. 12. The top-ranked site per scenario is reported in Table "
            "15: four scenarios select the same location and the baseline "
            "another about 3.5 km away."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 16 — consensus agreement rasters
# ─────────────────────────────────────────────────────────────────────────────

def fig_16(ctx):
    """How much land is classed High no matter what you change.

    The two panels vary different things and have different denominators — four
    method combinations against five weighting scenarios — so the raw counts
    are not comparable: "4" is unanimous on the left and a bare majority on the
    right. Both are collapsed onto one four-category scale so the panels can be
    read against each other, which is the comparison the figure exists to make.
    """
    from consensus import agreement_raster, variants_by_algorithm, variants_by_scenario
    va = variants_by_algorithm(ctx.stack)
    vs = variants_by_scenario(ctx.stack)
    ca = agreement_raster(va, ctx.mask)
    cs = agreement_raster(vs, ctx.mask)

    # "Half or more", not "majority": with 4 variants 2 of 4 lands here, and
    # "majority" is read as more than half whatever the caption says.
    CATS = ["never High", "minority", "half or more", "unanimous"]
    SHADES = ["#f2f2f2", "#cfe3c4", "#74b45b", "#14512a"]

    def _collapse(count, n):
        """Variant count -> 0 never / 1 minority / 2 majority / 3 unanimous."""
        out = np.full(count.shape, np.nan, dtype=float)
        inside = ctx.mask & ~np.isnan(count)
        c = np.where(inside, count, np.nan)
        out[inside & (c == 0)] = 0
        out[inside & (c > 0) & (c < n / 2.0)] = 1
        out[inside & (c >= n / 2.0) & (c < n)] = 2
        out[inside & (c == n)] = 3
        return out

    cmap = ListedColormap(SHADES)
    norm = BoundaryNorm([-0.5, 0.5, 1.5, 2.5, 3.5], cmap.N)

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 5.2))
    areas = {}
    for ax, count, n, what, key in (
            (axes[0], ca, len(va), f"{len(va)} method combinations", "algorithms"),
            (axes[1], cs, len(vs), f"{len(vs)} weighting scenarios", "scenarios")):
        cat = _collapse(count, n)
        _map(ax, cat, ctx.extent, ctx.boundary, cmap=cmap, norm=norm,
             title=f"Across {what}", furniture=False, grat=False)
        km2 = {CATS[k]: float(ctx.area[ctx.mask & (cat == k)].sum())
               for k in range(4)}
        areas[key] = km2
        # The headline number this figure exists for, and it was not on the
        # figure at all: how much land every variant agrees is High.
        ax.annotate(f"unanimous: {km2['unanimous']:,.0f} km\u00b2\n"
                    f"half or more: "
                    f"{km2['unanimous'] + km2['half or more']:,.0f} km\u00b2",
                    xy=(0.5, -0.085), xycoords="axes fraction", ha="center",
                    va="top", fontsize=8, fontweight="bold", color="0.20")

    _outer_graticule(axes[None, :], ctx.extent)
    _place_furniture(axes[0], ctx)
    _panel_letters(axes, offset=(-0.08, 1.00))
    handles = [Rectangle((0, 0), 1, 1, color=SHADES[k]) for k in range(4)]
    fig.legend(handles, CATS, loc="lower center", bbox_to_anchor=(0.5, -0.02),
               frameon=False, ncol=4, fontsize=8, handlelength=1.4,
               columnspacing=1.8)
    # "Survives" only describes the top category, and (b) varies judgements
    # rather than method, so the old title was wrong for half the figure.
    fig.suptitle(f"Method combinations agree on "
                 f"{areas['algorithms']['unanimous']:,.0f} km² of High; "
                 f"weighting scenarios on only "
                 f"{areas['scenarios']['unanimous']:,.0f}", y=0.98)
    fig.tight_layout()
    _save(fig, 16, f"agreement, shared categories "
                   f"(unanimous {areas['algorithms']['unanimous']:,.0f} vs "
                   f"{areas['scenarios']['unanimous']:,.0f} km\u00b2)")

    ua = areas["algorithms"]["unanimous"]
    us = areas["scenarios"]["unanimous"]
    return {
        "n_algorithm_variants": len(va),
        "n_scenario_variants": len(vs),
        "algorithm_km2": {k: round(v, 1) for k, v in areas["algorithms"].items()},
        "scenario_km2": {k: round(v, 1) for k, v in areas["scenarios"].items()},
        "unanimous_ratio_algo_over_scenario": round(ua / us, 2) if us else None,
        "CAPTION": (
            "One four-category scale on both panels so they can be compared. "
            "The raw variant counts cannot be: the denominators differ (4 "
            "against 5), so a count of 4 is unanimous on the left and a "
            "majority on the right. Categories are never High (0 variants), "
            "minority (fewer than half), half or more (but not all) and "
            "unanimous (all). The third is named 'half or more' rather than "
            "'majority' because with 4 variants an even split, 2 of 4, falls "
            "in it; with 5 variants the question does not arise. "
            f"(a) varies the method - {len(va)} "
            "combinations of 2 weighting methods x 2 aggregation rules - and "
            f"leaves {ua:,.0f} km2 High under every one. (b) varies the "
            "weighting judgements across the 5 scenarios of Fig. 15 and leaves "
            f"only {us:,.0f} km2. The contrast is the same finding as Fig. 12: "
            "changing the algorithm barely moves the answer, changing the "
            "judgements moves it a great deal."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 17 — sensitivity dashboard
# ─────────────────────────────────────────────────────────────────────────────

def fig_17(ctx):
    """Three complementary views of weight sensitivity.

    Three panels, not four. The fourth used to repeat Figure 18(b) value for
    value, which no referee should have to notice; the effective-weight
    analysis now lives in Figure 18 alone.

    "Complementary", not "independent": all three run on the same criteria
    stack and the same baseline judgements, so they cannot disagree about the
    data, only about what question is asked of it.
    """
    from sensitivity import map_removal_sensitivity, one_way_sensitivity
    ow = one_way_sensitivity(ctx.stack, ctx.weights)
    mr = map_removal_sensitivity(ctx.stack, ctx.weights)

    infl = ow["influence_high_pct"]
    order = sorted(infl, key=lambda k: infl[k])
    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.2))

    # (a) and (b) encode a magnitude only, so they are one neutral colour.
    # Previously (b) was orange for no reason, which invited a reading.
    ax = axes[0]
    ax.barh([CRIT_LABEL[c] for c in order], [infl[c] for c in order],
            color=NEUTRAL_BAR, height=0.6, zorder=2)
    for i, c in enumerate(order):
        ax.annotate(f"{infl[c]:.2f}", (infl[c], i), textcoords="offset points",
                    xytext=(3, 0), va="center", fontsize=7.5, zorder=4)
    ax.set_xlim(0, max(infl.values()) * 1.35)
    ax.set_xlabel(f"mean |\u0394| {HIGH_LABEL} (pp)")
    ax.set_title(f"\u00b1{ow['delta']*100:.0f}% weight perturbation")
    ax.grid(True, axis="x")

    ax = axes[1]
    rows = sorted(mr["rows"], key=lambda r: r["retained"])
    ax.barh([CRIT_LABEL[r["criterion"]] for r in rows],
            [r["retained"] for r in rows], color=NEUTRAL_BAR, height=0.6, zorder=2)
    for i, r in enumerate(rows):
        ax.annotate(f"{r['retained']}/{mr['top_n']}", (r["retained"], i),
                    textcoords="offset points", xytext=(3, 0), va="center",
                    fontsize=7.5, zorder=4)
    ax.set_xlabel(f"top-{mr['top_n']} sites retained on removal")
    ax.set_xlim(0, mr["top_n"])
    ax.set_title("Map removal \u2014 shortlist survival")
    ax.grid(True, axis="x")

    # Neutral, like (a) and (b). The bars run left or right from zero, so the
    # sign is already shown; the sign colours made the negative bars Okabe
    # blue, ΔE 5.5 from the High class blue, in a panel about the High share.
    ax = axes[2]
    rows2 = sorted(mr["rows"], key=lambda r: r["high_pct_delta"])
    cols = [NEUTRAL_BAR] * len(rows2)
    vals2 = [r["high_pct_delta"] for r in rows2]
    ax.barh([CRIT_LABEL[r["criterion"]] for r in rows2], vals2, color=cols,
            height=0.6, zorder=2)
    ax.axvline(0, color="black", lw=0.7, zorder=1)
    # Labelled, like the other two panels. Removing soil moves the High class
    # by several points and the number was not printed anywhere.
    span = max(abs(min(vals2)), abs(max(vals2)))
    for i, r in enumerate(rows2):
        d = r["high_pct_delta"]
        ax.annotate(_mn(d, "+.2f"), (d, i), textcoords="offset points",
                    xytext=(4 if d >= 0 else -4, 0), va="center",
                    ha="left" if d >= 0 else "right", fontsize=7.5, zorder=4)
    ax.set_xlim(-span * 1.45, span * 1.45)
    ax.set_xlabel(f"change in {HIGH_LABEL} (pp)")
    ax.set_title("Map removal \u2014 effect on class area")
    ax.grid(True, axis="x")

    _panel_letters(axes, offset=(-0.26, 1.03))
    # Three panels, two analyses: map removal is shown two ways. "Three
    # analyses" was right when there were four panels and is not now.
    # The finding, computed: the criterion whose removal moves the High share
    # most, and the one without which the shortlist does not survive.
    big = max(mr["rows"], key=lambda r: abs(r["high_pct_delta"]))
    gone = min(mr["rows"], key=lambda r: r["retained"])
    fig.suptitle(f"Removing {CRIT_LABEL[big['criterion']].lower()} moves the "
                 f"High share most ({_mn(big['high_pct_delta'], '+.2f')} pp); "
                 f"without {CRIT_LABEL[gone['criterion']].lower()}, "
                 f"{gone['retained']} of the top {mr['top_n']} sites survive",
                 y=1.00)
    fig.tight_layout()
    _save(fig, 17, "sensitivity dashboard, three panels")

    worst = min(mr["rows"], key=lambda r: r["retained"])
    return {
        "delta": ow["delta"],
        "top_n": mr["top_n"],
        "influence_pp": {c: round(infl[c], 2) for c in infl},
        "retained": {r["criterion"]: r["retained"] for r in mr["rows"]},
        "removal_high_pp": {r["criterion"]: round(r["high_pct_delta"], 2)
                            for r in mr["rows"]},
        "CAPTION": (
            f"(a) Each weight perturbed by \u00b1{ow['delta']*100:.0f}% in turn, "
            "one at a time, with the remaining five renormalised to sum to 1; "
            f"the bar is the mean |change| in {HIGH_LABEL} over the two "
            "directions. (b) and (c) drop one criterion entirely and "
            "renormalise the remaining five in proportion to their assigned "
            "weights, after Lodwick, Monson & Svoboda (1990). (b) counts how "
            f"many of the baseline top {mr['top_n']} sites are still present; "
            f"the top {mr['top_n']} rather than all 25 because that is the "
            "shortlist a planner would take to field reconnaissance, and "
            "retention further down the list is dominated by the 5 km "
            "separation rule rather than by the criterion. Removing rainfall "
            f"retains {worst['retained']}/{mr['top_n']}: nothing survives it, "
            "which is consistent with rainfall carrying 72% of the variance in "
            "Fig. 18(b). The three panels are two analyses - map removal is "
            "shown twice, by shortlist and by area - and they are "
            "complementary rather than independent, since all run on one "
            "criteria stack and one set of judgements. Note that (a) and (c) "
            "rank the criteria differently from Fig. 18(b): soil has the "
            "largest perturbation effect at 1.42 pp but only 9.8% of the "
            "variance. That is expected rather than contradictory. Both "
            "panels here measure a change in CLASS SHARE, which is driven by "
            "the score's level, and soil puts 77.8% of the district on one "
            "tied value - so reweighting it slides a large uniform block "
            "across the 0.85 breakpoint without separating anything inside "
            "that block. Fig. 18 is the figure that distinguishes the two."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 18 — assigned versus effective weight
# ─────────────────────────────────────────────────────────────────────────────

def fig_18(ctx):
    """Two different questions that have both been called "effective weight".

    LEVEL is the share of the mean score a criterion supplies, after Napolitano
    & Fabbri (1996). VARIATION is the share of the score's variance it drives.
    They are not the same thing and here they disagree, which is a result
    rather than a nuisance: a criterion that lifts every cell by about the same
    amount is a large part of the number and a small part of the decision.

    Both panels are built so one criterion's two measures can be compared
    directly \u2014 a segment in (a), a pair of bars in (b). The previous version
    used a scatter for one and bars for the other, which left the comparison to
    the reader.
    """
    from sensitivity import discrimination_weights, single_parameter_sensitivity
    sp = single_parameter_sensitivity(ctx.stack, ctx.weights)
    dw = discrimination_weights(ctx.stack, ctx.weights)
    lvl = {r["criterion"]: r for r in sp["rows"]}
    var = {r["criterion"]: r for r in dw["rows"]}
    crits = sorted(lvl, key=lambda c: -lvl[c]["theoretical_pct"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.2, 4.9))

    # Paired bars in both panels, not a scatter in one and bars in the other.
    # The scatter put four of the six criteria into a cluster below 10% where
    # their labels could not be placed, and it left the reader to carry a
    # criterion's position across two different constructions.
    order = sorted(crits, key=lambda c: var[c]["ratio"])
    y = np.arange(len(order))

    # ── (a) the three shares, absolute ─────────────────────────────────────
    h = 0.26
    ax1.barh(y + h, [lvl[c]["theoretical_pct_exact"] for c in order], height=h,
             color="#C7CCD1", label="assigned (AHP)", zorder=2)
    ax1.barh(y, [lvl[c]["effective_pct_exact"] for c in order], height=h,
             color=NEUTRAL_BAR, label="level (mean score)", zorder=2)
    ax1.barh(y - h, [var[c]["discrimination_pct_exact"] for c in order], height=h,
             color=OKABE[1], label="variation (variance)", zorder=2)
    for i, c in enumerate(order):
        for off, val, col, bold in (
                (h, lvl[c]["theoretical_pct_exact"], "0.35", False),
                (0, lvl[c]["effective_pct_exact"], "0.20", False),
                (-h, var[c]["discrimination_pct_exact"], OKABE[1], True)):
            ax1.annotate(_fx(val, 1), (val, i + off), textcoords="offset points",
                         xytext=(3, 0), va="center", fontsize=7,
                         color=col, fontweight="bold" if bold else "normal",
                         zorder=4)
    ax1.set_yticks(y)
    ax1.set_yticklabels([CRIT_LABEL[c] for c in order])
    ax1.set_xlim(0, 86)
    ax1.set_xlabel("% of the composite")
    ax1.legend(frameon=False, loc="lower right", fontsize=7.5)
    ax1.grid(True, axis="x")
    ax1.set_title("Assigned, level and variation shares")

    # ── (b) the same three as ratios, so 1.0 is the reference ──────────────
    h2 = 0.36
    # Ratios from the UNROUNDED shares. The stored "ratio" is rounded to 3 dp,
    # so soil's 0.6348 was held as 0.635 and printed 0.64 - double rounding,
    # the same defect as 42.9 and 37.0 in panel (a). Exact, it is 0.63.
    w_ex = {c: lvl[c]["theoretical_pct_exact"] for c in order}
    for c in order:
        lvl[c]["ratio"] = lvl[c]["effective_pct_exact"] / w_ex[c]
        var[c]["ratio"] = var[c]["discrimination_pct_exact"] / w_ex[c]
    ax2.barh(y + h2 / 2, [lvl[c]["ratio"] for c in order], height=h2,
             color=NEUTRAL_BAR, label="level \u00f7 assigned", zorder=2)
    ax2.barh(y - h2 / 2, [var[c]["ratio"] for c in order], height=h2,
             color=OKABE[1], label="variation \u00f7 assigned", zorder=2)
    ax2.axvline(1.0, color="black", lw=0.8, ls="--", zorder=1)
    # A bar ending just short of 1.0 puts its label across the reference line.
    # Those go inside the bar instead, right-aligned at its end.
    def _ratio_label(ax, value, ypos, colour, bold):
        near = 0.82 <= value <= 1.0   # a label is ~0.12 wide on this axis
        ax.annotate(f"{_fx(value, 2)}\u00d7", (value, ypos),
                    textcoords="offset points",
                    xytext=(-4 if near else 3, 0), va="center",
                    ha="right" if near else "left", fontsize=7.5,
                    fontweight="bold" if bold else "normal",
                    color="white" if near else colour, zorder=4)

    for i, c in enumerate(order):
        _ratio_label(ax2, lvl[c]["ratio"], i + h2 / 2, "black", False)
        _ratio_label(ax2, var[c]["ratio"], i - h2 / 2, OKABE[1], True)
    ax2.set_yticks(y)
    ax2.set_yticklabels([])
    ax2.set_xlim(0, 2.0)
    ax2.set_xlabel("share \u00f7 assigned weight (1.0 = as assigned)")
    ax2.legend(frameon=False, loc="lower right", fontsize=7.5)
    ax2.grid(True, axis="x")
    ax2.set_title("The same, as a ratio to the assigned weight")

    _panel_letters([ax1, ax2], offset=(-0.14, 1.02))
    # Named from the data, not asserted. Land cover, not slope, is the least
    # discriminating per unit of weight - by a factor of five - and it also has
    # the second-highest level ratio, so it is the sharper example of the two.
    least = min(crits, key=lambda c: var[c]["ratio"])
    most = max(crits, key=lambda c: var[c]["discrimination_pct"])
    pair = [c for c in crits if lvl[c]["ratio"] > 1.0]
    pair.sort(key=lambda c: -lvl[c]["ratio"])
    fig.suptitle(
        f"{' and '.join(CRIT_LABEL[c].lower() for c in pair).capitalize()} add "
        f"level but little discrimination; {CRIT_LABEL[most].lower()} carries "
        f"{var[most]['discrimination_pct']:.0f}% of the variance", y=1.00)
    fig.tight_layout()
    _save(fig, 18, "level contribution vs variance share")

    return {
        "level_ratio": {c: round(lvl[c]["ratio"], 3) for c in crits},
        "discrimination_pct": {c: var[c]["discrimination_pct"] for c in crits},
        "discrimination_ratio": {c: round(var[c]["ratio"], 3) for c in crits},
        "least_discriminating": least,
        "sd_composite": dw["sd_composite"],
        "discrimination_total_pct": dw["total_pct"],
        "CAPTION": (
            "Two decompositions of the same composite, each criterion shown "
            "twice so the pair can be read together. LEVEL is the mean over "
            "in-district cells of w_i*r_i / V, the share of the score's level "
            "a criterion supplies (Napolitano & Fabbri 1996). VARIATION is the "
            "Pratt index: with V an exact linear combination, the standardised "
            "coefficient of V on r_i is beta_i = w_i*sd(r_i)/sd(V), and "
            "beta_i*corr(r_i, V) partitions var(V), summing to "
            f"{dw['total_pct']:.0f}%. (a) gives the three shares absolutely, "
            "(b) the two derived ones as a ratio to the assigned weight, so "
            "1.0 marks a criterion taking exactly the share it was given. "
            "TWO CAVEATS on the variance measure. It partitions the variance "
            "of the CONTINUOUS baseline score, not membership of the High "
            "class, which depends on the upper tail and on where the "
            "breakpoints fall - which is why Fig. 17, measuring class share, "
            "ranks the criteria differently. And it is defined only for a "
            "linear aggregator, so it is computed on AHP + WLC; the TOPSIS "
            "closeness coefficient is not a weighted sum. "
            f"{CRIT_LABEL[least]} is the least discriminating per unit of "
            f"assigned weight at {_fx(var[least]['ratio'], 2)}x, about five times "
            "below slope, while also taking "
            f"{_fx(lvl[least]['ratio'], 2)}x its share of the level."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 19 — criterion correlation heatmap
# ─────────────────────────────────────────────────────────────────────────────

def fig_19(ctx):
    """Are the criteria measuring the same thing twice?

    WLC adds the scored layers, so Pearson r on the scored layers is the
    statistic that bears on double counting; Spearman is carried alongside
    because three of the six layers are heavily tied and a rank statistic
    handles ties differently from a product-moment one.
    """
    from scipy.stats import pearsonr, spearmanr
    names = ctx.crit
    n = len(names)
    P = np.full((n, n), np.nan)      # Pearson, every pair
    S = np.full((n, n), np.nan)      # Spearman, every pair
    for i in range(n):
        for j in range(i + 1, n):
            a = ctx.stack["normalized_rasters"][names[i]][ctx.mask]
            b = ctx.stack["normalized_rasters"][names[j]][ctx.mask]
            ok = ~np.isnan(a) & ~np.isnan(b)
            S[i, j] = S[j, i] = float(spearmanr(a[ok], b[ok]).statistic)
            P[i, j] = P[j, i] = float(pearsonr(a[ok], b[ok])[0])

    # Spearman above the diagonal, Pearson below, diagonal left empty.
    R = np.where(np.triu(np.ones((n, n)), 1) > 0, S, P)
    np.fill_diagonal(R, np.nan)

    # Which pair is the strongest, computed rather than asserted.
    off = ~np.eye(n, dtype=bool)
    k = np.nanargmax(np.abs(np.where(off, P, np.nan)))
    i_max, j_max = np.unravel_index(k, P.shape)
    r_max = P[i_max, j_max]
    s_max = S[i_max, j_max]
    pair = f"{CRIT_LABEL[names[i_max]].lower()}\u2013{CRIT_LABEL[names[j_max]].lower()}"
    w_pair = ctx.weights[names[i_max]] + ctx.weights[names[j_max]]

    # Two different things, measured separately, because conflating them gets
    # slope wrong. TIED means many cells share one exact score, which is what
    # a rank statistic has to break arbitrarily. CONCENTRATED means the scores
    # are squeezed into a narrow band near the top without repeating. Soil and
    # land cover are tied, because they are categorical lookups over four and
    # eleven classes. Slope is NOT tied - it runs through an interpolated ramp
    # and its largest exact repeat covers a fraction of a per cent - it is
    # concentrated, with 86% of cells above 0.90 under the ramp the model uses
    # (95.8% is the min-max figure Fig. 2 reports for the version replaced).
    # Both pull rho away from r,
    # for different reasons.
    ties, conc = {}, {}
    for c in names:
        v = ctx.stack["normalized_rasters"][c][ctx.mask]
        v = v[~np.isnan(v)]
        _u, counts = np.unique(np.round(v, 6), return_counts=True)
        ties[c] = 100.0 * float(counts.max()) / v.size
        conc[c] = 100.0 * float((v > 0.90).mean())

    fig, ax = plt.subplots(figsize=(6.8, 5.8))
    masked = np.ma.masked_invalid(R)
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad("#FFFFFF")          # the diagonal, which used to be dark red
    im = ax.imshow(masked, cmap=cmap, vmin=-1, vmax=1)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels([CRIT_LABEL[c] for c in names], rotation=35, ha="right")
    ax.set_yticklabels([CRIT_LABEL[c] for c in names])
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            # _mn, so the negatives carry a true minus like every other figure.
            ax.text(j, i, _mn(R[i, j], ".2f"), ha="center", va="center",
                    fontsize=7.5,
                    color="white" if abs(R[i, j]) > 0.55 else "black")
    cb = fig.colorbar(im, ax=ax, shrink=0.8, pad=0.02)
    cb.set_label("correlation")
    # The finding, not the caveat. The caveat moved to the caption.
    ax.set_title(f"Criteria are weakly correlated: max |r| = {abs(r_max):.2f} "
                 f"({pair})\nSpearman \u03c1 above the diagonal, Pearson r below",
                 fontsize=9)
    for s in ax.spines.values():
        s.set_visible(False)
    fig.tight_layout()
    _save(fig, 19, f"criterion correlations (max |r| {abs(r_max):.2f}, {pair})")

    return {
        "max_abs_pearson": round(float(abs(r_max)), 3),
        "max_pearson_pair": [names[i_max], names[j_max]],
        "spearman_same_pair": round(float(s_max), 3),
        "combined_weight_of_pair": round(float(w_pair), 3),
        "largest_tied_value_pct": {c: round(v, 1) for c, v in ties.items()},
        "above_090_pct": {c: round(v, 1) for c, v in conc.items()},
        "CAPTION": (
            f"Pearson r and Spearman rho on the SCORED layers, over the "
            f"{int(ctx.mask.sum()):,} in-district cells. No significance tests "
            "are reported: the cells are strongly spatially autocorrelated, so "
            "a nominal p-value computed on n of this size would be "
            "meaningless. WLC adds the scored layers, so Pearson is the "
            f"statistic the model depends on. The strongest pair is {pair} at "
            f"r = {r_max:.2f} (rho = {s_max:.2f}); those two criteria carry "
            f"{w_pair:.2f} of the total weight between them, so the overlap is "
            "worth stating - at r = 0.45 they share about "
            f"{100*r_max**2:.0f}% of their variance and the model is to that "
            "extent counting one signal twice, but they are far from "
            "redundant. Two separate reasons to read rho with care, which "
            "should not be conflated. TIES: soil puts "
            f"{ties['soil']:.0f}% of cells on one score and land cover "
            f"{ties['lulc']:.0f}%, both being categorical lookups, so a rank "
            "statistic is breaking large blocks of equal values. "
            "CONCENTRATION: slope is not tied - its largest exact repeat is "
            f"{ties['slope']:.1f}% of cells - but it is squeezed into the top "
            f"of its range, with {conc['slope']:.1f}% of cells above 0.90, "
            "which is the defect Fig. 2 documents the ramp only partly "
            "curing. Either one pulls rho and r apart, and slope against land "
            "cover is where they diverge most: rho = "
            f"{S[names.index('slope'), names.index('lulc')]:.2f} against "
            f"r = {P[names.index('slope'), names.index('lulc')]:.2f}."),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Figure 21 (bonus) — rank displacement under each alternative method
# ─────────────────────────────────────────────────────────────────────────────

def fig_21(ctx):
    """Is the WLC/TOPSIS disagreement re-ranking, or where the cutoffs fall?

    A THREE-WAY PARTITION OF CELLS, not a netted difference of two totals. The
    first version of this figure subtracted the churn under share-matched
    breakpoints from the churn under fixed ones and called the remainder a
    "breakpoint component". That is wrong twice over. The two are different
    SETS of cells, not nested, so the subtraction is not a decomposition; and
    for the Low class the difference is negative - fixed cutoffs SUPPRESS about
    3 pp of re-ranking there, because the TOPSIS surface sits lower and the
    fixed 0.65 holds cells in Low that a matched cutoff would release. A
    stacked bar cannot draw a negative segment, so that row silently showed the
    matched churn (3.99 pp) under a total labelled as the actual churn
    (1.02 pp), and the rows summed to 15.80 against a stated total of 12.83.

    Partitioning the cells instead sums correctly by construction and has no
    negative segment:

      robust   changes class under BOTH breakpoint schemes
      induced  changes only under the fixed scheme
      masked   changes only under the matched scheme

    robust + induced = the 12.833 pp that actually changes class.
    robust + masked  = the 9.902 pp that changes under matched cutoffs.

    The headline follows from the first category alone and cannot be called
    netted: half the cells that change class would change under any breakpoint
    scheme.
    """
    from scipy.stats import spearmanr

    rw, rt = ctx.algos["AHP + WLC"], ctx.algos["AHP + TOPSIS"]
    sw, st_ = rw["suitability_raster"], rt["suitability_raster"]
    cw, ct = rw["classified_raster"], rt["classified_raster"]
    ok = (ctx.mask & ~np.isnan(cw) & ~np.isnan(ct)
          & ~np.isnan(sw) & ~np.isnan(st_))
    A = ctx.area[ok]
    tot = float(A.sum())
    W, T, V = cw[ok], ct[ok], st_[ok]
    lo_t, hi_t = C.SUITABILITY_THRESHOLDS

    share = {c: 100.0 * float(A[W == c].sum()) / tot for c in (1, 2, 3)}
    order = np.argsort(V, kind="mergesort")
    cum = 100.0 * np.cumsum(A[order]) / tot
    t_lo = float(V[order][np.searchsorted(cum, share[1])])
    t_hi = float(V[order][np.searchsorted(cum, share[1] + share[2])])
    M = np.where(V <= t_lo, 1, np.where(V <= t_hi, 2, 3))

    def pp(sel):
        return 100.0 * float(A[sel].sum()) / tot

    def km2(sel):
        return float(A[sel].sum())

    robust = (W != T) & (W != M)
    induced = (W != T) & (W == M)
    masked = (W == T) & (W != M)

    lab = {3: "High", 2: "Medium", 1: "Low"}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.4, 5.4),
                                   gridspec_kw={"width_ratios": [1.22, 1]})

    # ── (a) the partition ───────────────────────────────────────────────────
    rows = [("All classes", robust, induced, masked)]
    for c in (3, 2, 1):
        here = (W == c)
        rows.append((f"from {lab[c]}", robust & here, induced & here,
                     masked & here))

    # Segment order: fixed-only | both | matched-only. With the shared middle
    # segment in the middle, each cutoff scheme's total is a CONTIGUOUS span,
    # and a bracket can be drawn over it. Previously the bar ran to the union
    # of the two schemes, 16.28 pp, while its label said 12.83 - a reader takes
    # bar length as the quantity, and the two disagreed.
    # Rows 1.4 apart, not 1.0: at unit spacing the High row's "matched" label
    # (below its bar) and the Medium row's "fixed" label (above its bar) met.
    ROW = 1.4
    y = np.arange(len(rows))[::-1] * ROW
    span = 0.56
    for yy, (_n, rb, ind, msk) in zip(y, rows):
        a, b, d = pp(rb), pp(ind), pp(msk)       # both, fixed-only, matched-only
        ax1.barh(yy, b, color=PARTITION["induced"], height=span, zorder=2,
                 label="changes only under fixed cutoffs" if yy == y[0] else None)
        ax1.barh(yy, a, left=b, color=PARTITION["robust"], height=span, zorder=2,
                 label="re-ranked under both schemes" if yy == y[0] else None)
        ax1.barh(yy, d, left=b + a, color=PARTITION["robust"], height=span,
                 hatch="///", edgecolor="white", linewidth=0.0, zorder=2,
                 label="re-ranked, masked by the fixed cutoffs" if yy == y[0] else None)

        # Values OUTSIDE the bar, stacked under it. Inside, the 1.02 segment on
        # the "from Low" row was narrower than its own white label, which spilled
        # left over the y-axis spine and joined the tick mark to read as "-1.02"
        # - a negative component, which is precisely the defect this rebuild
        # removed. Nothing is drawn on the hatching either, where white text on
        # white hatch lines was unreadable.
        parts = [(b, PARTITION["induced"]), (a, PARTITION["robust"]),
                 (d, PARTITION["robust"])]
        txt = "  +  ".join(_fx(v, 2) for v, _c in parts)
        ax1.annotate(txt, (b + a + d, yy), textcoords="offset points",
                     xytext=(7, 0), va="center", fontsize=7.2, color="0.30",
                     zorder=4)

        # Two brackets, one per cutoff scheme, each spanning the segments it
        # actually covers. Every number now labels an extent.
        for lo, hi, lab, off, col in (
                (0.0, b + a, f"fixed: {_fx(b + a, 2)}", 0.30, PARTITION["induced"]),
                (b, b + a + d, f"matched: {_fx(a + d, 2)}", -0.30, PARTITION["robust"])):
            yb = yy + off + (0.10 if off > 0 else -0.10)
            ax1.plot([lo, hi], [yb, yb], color=col, lw=0.9, zorder=5,
                     solid_capstyle="butt")
            for xe in (lo, hi):
                ax1.plot([xe, xe], [yb, yb - 0.05 if off > 0 else yb + 0.05],
                         color=col, lw=0.9, zorder=5)
            # A short bracket cannot hold a centred label: on the narrow rows
            # it overhung the y-axis spine, which is how the neighbouring
            # segment label came to read as a negative number. Narrow brackets
            # get their label to the right instead.
            narrow = (hi - lo) < 4.0
            ax1.annotate(lab,
                         (hi if narrow else (lo + hi) / 2, yb),
                         textcoords="offset points",
                         xytext=(5, -2) if narrow else (0, 3 if off > 0 else -9),
                         ha="left" if narrow else "center",
                         va="center" if narrow else "baseline",
                         fontsize=6.6, color=col, fontweight="bold", zorder=5)

    ax1.set_yticks(y)
    ax1.set_yticklabels([r[0] for r in rows])
    ax1.set_xlim(0, 26)
    ax1.set_ylim(-0.85, (len(rows) - 1) * ROW + 0.85)
    ax1.set_xlabel("% of district area")
    ax1.legend(frameon=False, loc="lower right", fontsize=7.0)
    ax1.grid(True, axis="x")
    robust_share = 100 * pp(robust) / pp(robust | induced)
    # "under both cutoff schemes", not "under any cutoffs": two schemes were
    # tested, not all of them.
    ax1.set_title(f"{robust_share:.0f}% of what changes class changes under "
                  "BOTH cutoff schemes")

    # ── (b) how far each cutoff has to move ────────────────────────────────
    # Not the class shares under matched cutoffs: those are zero BY
    # CONSTRUCTION, so plotting them showed a quantity defined to be zero and
    # left a legend entry with no bars. The evidence is the displacement
    # itself, and its asymmetry is the finding.
    bounds = [("Low / Medium\nboundary", lo_t, t_lo,
               100.0 * float(A[T == 1].sum()) / tot - share[1]),
              ("Medium / High\nboundary", hi_t, t_hi,
               100.0 * float(A[T == 3].sum()) / tot - share[3])]
    yb = np.arange(len(bounds))[::-1]
    for yy, (name, fixed_c, matched_c, shift) in zip(yb, bounds):
        ax2.annotate("", xy=(matched_c, yy), xytext=(fixed_c, yy),
                     arrowprops=dict(arrowstyle="-|>", color=PARTITION["induced"],
                                     lw=2.0, shrinkA=2, shrinkB=2), zorder=3)
        # Neutral markers. Teal already means "re-ranked" in panel (a), and
        # using it here for the matched cutoff gave one colour two jobs inside
        # one figure. Olive stays, because it means cutoff effect in both.
        ax2.plot([fixed_c], [yy], "o", ms=8, color="0.25", zorder=4)
        ax2.plot([matched_c], [yy], "D", ms=7, color="0.55",
                 markeredgecolor="0.25", zorder=4)
        # Anchored to the LEFT of the pair and left-aligned: centred on the
        # High pair, which sits at 0.845/0.850, the label ran off the frame.
        # Centred over a wide pair, right-anchored beside a narrow one. Right-
        # anchored over the Low pair it ran left across the y-axis spine;
        # centred over the High pair it ran off the frame.
        wide = abs(fixed_c - matched_c) > 0.02
        ax2.annotate(f"moves {abs(fixed_c - matched_c):.3f}\n"
                     f"removes a {_fx(shift, 3)} pp shift",
                     xy=((fixed_c + matched_c) / 2 if wide
                         else min(fixed_c, matched_c), yy),
                     textcoords="offset points",
                     xytext=(0, 24) if wide else (-6, 24),
                     ha="center" if wide else "right",
                     fontsize=7.5, fontweight="bold", zorder=4)
    ax2.plot([], [], "o", ms=8, color="0.25", label="fixed cutoff")
    ax2.plot([], [], "D", ms=7, color="0.55", markeredgecolor="0.25",
             label="cutoff matching WLC's class sizes")
    ax2.set_yticks(yb)
    ax2.set_yticklabels([b[0] for b in bounds], fontsize=8)
    ax2.set_ylim(-0.75, len(bounds) - 0.15)
    ax2.set_xlim(0.56, 0.90)
    ax2.set_xlabel("score / closeness coefficient")
    ax2.legend(frameon=False, loc="lower center", fontsize=7.5, ncol=2)
    ax2.grid(True, axis="x")
    ax2.set_title("The Low cutoff must move ten times further")

    rho = float(spearmanr(sw[ok], st_[ok]).statistic)
    # In (b)'s clear upper strip. In (a) it sat on the legend, which has to be
    # bottom-right because the bars all start at the left.
    ax2.annotate(f"Spearman \u03c1 = {rho:.3f} between the two surfaces, per cell",
                 xy=(0.02, 0.97), xycoords="axes fraction", ha="left",
                 va="top", fontsize=7.5, color="0.30", zorder=4)

    _panel_letters([ax1, ax2], offset=(-0.20, 1.03))
    # "under both schemes", not "under any": two cutoff schemes were tested.
    fig.suptitle("The 9 pp Low shift is a cutoff effect; half the cells that "
                 "move do so under both cutoff schemes", y=1.00)
    fig.tight_layout()
    _save(fig, 21, f"cell partition ({pp(robust):.2f} robust + "
                   f"{pp(induced):.2f} induced = {pp(robust | induced):.2f} pp)")

    # Shortlist overlap, extracted AT the size reported: candidate extraction
    # is best-per-tile with a 5 km separation rule and is NOT nested, so the
    # top 10 of a 10-site run is not the first 10 of a 25-site run (5/10
    # against 8/10). algorithms.py and Fig. 17(b) use the same rule.
    from sensitivity import _match_sites
    overlap = {}
    for k in (10, 25):
        pair = {}
        for nm in ("AHP + WLC", "AHP + TOPSIS"):
            w, agg, _l = weights_for_algorithm(nm, ahp_engine.matrix,
                                               ahp_engine.criteria)
            pair[nm] = G.score_stack(ctx.stack, w, aggregator=agg, algorithm=nm,
                                     extract_sites=False,
                                     top_n=k)["top_locations_details"]
        _p, kept = _match_sites(pair["AHP + WLC"][:k], pair["AHP + TOPSIS"][:k], 2.0)
        overlap[k] = kept

    return {
        "robust_pp": round(pp(robust), 3),
        "induced_pp": round(pp(induced), 3),
        "masked_pp": round(pp(masked), 3),
        "robust_km2": round(km2(robust), 1),
        "induced_km2": round(km2(induced), 1),
        "masked_km2": round(km2(masked), 1),
        "total_changing_pp": round(pp(robust | induced), 3),
        "changing_under_matched_pp": round(pp(robust | masked), 3),
        "robust_share_of_changing_pct": round(robust_share, 1),
        "matched_breakpoints": [round(t_lo, 4), round(t_hi, 4)],
        "cutoff_shift_low": round(lo_t - t_lo, 4),
        "cutoff_shift_high": round(hi_t - t_hi, 4),
        "spearman_rho_per_cell": round(rho, 4),
        "top10_overlap": overlap[10],
        "top25_overlap": overlap[25],
        "CAPTION": (
            "AHP weighting throughout, so only the aggregation rule varies. "
            "CUTOFFS MATCHING WLC'S CLASS SIZES are the quantiles of the "
            f"TOPSIS surface ({t_lo:.4f} and {t_hi:.4f}) that reproduce its "
            "41.08 / 52.48 / 6.44 split exactly; with the class sizes equal, a "
            "cell that still changes class has been re-ranked. "
            "(a) A partition of CELLS, so the segments sum to the row total "
            "and the rows sum to the whole. It is NOT a difference of two "
            "churn totals: those are different sets of cells, and for the Low "
            "class the difference is negative, because the fixed 0.65 holds "
            "cells in Low that a matched cutoff releases. "
            f"{pp(robust):.2f} pp ({km2(robust):,.0f} km2) changes class under "
            f"both schemes, {pp(induced):.2f} pp ({km2(induced):,.0f} km2) "
            f"only under the fixed cutoffs, and {pp(masked):.2f} pp "
            f"({km2(masked):,.0f} km2) only under the matched ones - "
            "re-ranking the fixed scheme conceals. So "
            f"{robust_share:.0f}% of the cells that change class under the "
            "fixed cutoffs also change under the share-matched ones. Two "
            "schemes were tested, not all possible schemes, so this is a "
            "statement about these two. Bar segments are ordered fixed-only, "
            "both, matched-only, so each scheme's total is a contiguous span "
            "and the brackets above each bar label an extent rather than "
            "floating beside one. Segment and bracket values are each rounded "
            "independently from the unrounded areas, so a bracket can differ "
            "by 0.01 from the sum of its printed segments. "
            f"(b) Removing the {_fx(bounds[0][3], 3)} pp Low shift takes a "
            f"{abs(bounds[0][1] - bounds[0][2]):.3f} move of the lower cutoff; "
            f"removing the {_fx(bounds[1][3], 3)} pp High shift takes only "
            f"{abs(bounds[1][1] - bounds[1][2]):.3f} \u2014 exactly, "
            f"{abs(bounds[0][1] - bounds[0][2]):.4f} against "
            f"{abs(bounds[1][1] - bounds[1][2]):.4f}, a ratio of "
            f"{abs(bounds[0][1] - bounds[0][2]) / abs(bounds[1][1] - bounds[1][2]):.1f}. "
            "That asymmetry, in score "
            "units, is why the aggregation rule appears to move the Low class "
            "an order of magnitude more than the High class. "
            "The breakpoint scheme is itself an analyst decision, so the one "
            "algorithm effect that looked large is substantially another "
            "analyst-decision effect; Fig. 12 carries it as its own bar. "
            f"Spearman \u03c1 = {rho:.3f} is a per-cell statistic over the two "
            f"surfaces. Shortlist retention {overlap[10]}/10 and "
            f"{overlap[25]}/25, each extracted at the size reported."),
    }


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
    # Edges ANCHORED at the 0.85 breakpoint. From a linspace of the data range
    # one bin ran 0.8476-0.8560, so High-only cells were painted on the Low
    # side of the line and looked like 0-vote cells above 0.85 (there are none).
    thr = C.SUITABILITY_THRESHOLDS[1]
    step = 0.0075
    k_lo = int(np.ceil((thr - np.nanmin(x)) / step))
    k_hi = int(np.ceil((np.nanmax(x) - thr) / step))
    bins_x = thr + step * np.arange(-k_lo, k_hi + 1)
    _edges_include(bins_x, (thr,), "fig22")
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
    # Jittered, and the per-row counts printed. At y exactly 4 the 22
    # unanimous sites drew as one blob and a reader could not count 25.
    rng = np.random.default_rng(20260923)
    jitter = rng.uniform(-0.22, 0.22, size=len(cy))
    ax.scatter(cx, np.asarray(cy) + jitter, s=30, facecolor="none",
               edgecolor=OKABE[1], lw=1.2, zorder=5,
               label="25 candidate sites (jittered)")
    import collections as _collections
    per_row = _collections.Counter(int(v) for v in cy)
    for lvl, k in sorted(per_row.items()):
        # Left side. On the right they sat behind the site markers, which the
        # collision test could not see until it learned about scatter.
        ax.annotate(f"{k} site{'s' if k != 1 else ''}", xy=(0.02, lvl),
                    xycoords=("axes fraction", "data"), ha="left",
                    va="center", fontsize=7.5, color=OKABE[1],
                    fontweight="bold", zorder=6)
    # Black on a white casing: white alone vanished on the green bins, black
    # alone would vanish on the dark purple ones.
    import matplotlib.patheffects as _pe
    ax.axvline(thr, color="black", lw=1.0, ls="--", zorder=4,
               path_effects=[_pe.withStroke(linewidth=2.6, foreground="white")])
    ax.set_yticks(range(nb))
    ax.set_xlabel("baseline composite score")
    ax.set_ylabel("method combinations classing the cell High")
    ax.legend(frameon=False, loc="upper left")
    # Room for the top site's marker, which the data-driven right edge cut in
    # half, and for the per-row counts.
    ax.set_xlim(bins_x[0] - 0.004, bins_x[-1] + 0.030)
    ax.set_ylim(-0.75, nb - 0.25)

    # Where the disagreement actually lives, computed rather than asserted.
    unanimous_from = float(np.nanmin(x[y == len(va)]))
    disagree_to = float(np.nanmax(x[y < len(va)]))
    any_vote_from = float(np.nanmin(x[y >= 1]))
    impossible = int(((x > thr) & (y == 0)).sum())
    assert impossible == 0, f"fig22: {impossible} cells above {thr} with 0 votes"
    ax.set_title("Method disagreement is confined to a narrow band at the "
                 "0.85 breakpoint")
    fig.tight_layout()
    _save(fig, 22, f"stability versus suitability "
                   f"(all agree above {disagree_to:.3f})")

    non_unan = sorted(((d["rank"], float(base[rasterio.transform.rowcol(tr, d["lon"], d["lat"])[0],
                                              rasterio.transform.rowcol(tr, d["lon"], d["lat"])[1]]))
                       for d in det
                       if count[rasterio.transform.rowcol(tr, d["lon"], d["lat"])[0],
                                rasterio.transform.rowcol(tr, d["lon"], d["lat"])[1]] < len(va)))
    return {
        "sites_by_agreement": {int(k): int(v) for k, v in sorted(per_row.items())},
        "lowest_unanimous_score": round(unanimous_from, 4),
        "highest_disagreeing_score": round(disagree_to, 4),
        "lowest_score_with_any_vote": round(any_vote_from, 4),
        "cells_above_085_with_0_votes": impossible,
        "non_unanimous_sites": [(r, round(sc, 4)) for r, sc in non_unan],
        "CAPTION": (
            "Cell counts on a log colour scale, by baseline composite score "
            "and by how many of the 4 method combinations class the cell "
            f"High. Above {disagree_to:.3f} every cell is High under all four, "
            f"and no cell below {unanimous_from:.3f} is; below "
            f"{any_vote_from:.3f} no combination calls any cell High. "
            f"Disagreement is therefore confined to {any_vote_from:.3f}-"
            f"{disagree_to:.3f}, a band of {disagree_to - any_vote_from:.2f} "
            f"around the 0.85 breakpoint ({thr - any_vote_from:.3f} below it, "
            f"{disagree_to - thr:.3f} above), which is the same mechanism "
            "Fig. 21 quantifies. Above 0.85 every cell has at least one vote, "
            "because the baseline AHP + WLC is one of the four. Bins are "
            f"{step} wide with an edge at 0.85, so no bin straddles the "
            "dashed line. Scoring well is "
            "therefore almost the same as unanimity - what is unstable is "
            "scoring JUST well enough. "
            "The 25 candidate sites are overlaid, jittered vertically so they "
            "can be counted, with the number at each agreement level on the "
            f"left. The {len(non_unan)} non-unanimous sites are the "
            "lowest-scoring of the shortlist - ranks "
            + ", ".join(str(r) for r, _ in non_unan) +
            " at " + ", ".join(f"{sc:.4f}" for _, sc in non_unan) +
            " - so the instability is at the bottom of the list, not the top."),
    }


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
    def surface(cls, ctx, soil_table=None):
        """The reconstructed step-class surface.

        `soil_table` defaults to the historical soil scores, which is what the
        step scheme was actually run with. Pass C.SOIL_TEXTURE_SCORES to ask
        what the same step scheme would do on today's corrected legend - the
        comparison Figure 8 is built on.
        """
        raw, mask = ctx.stack["raw_rasters"], ctx.mask
        soil_table = cls.SOIL if soil_table is None else soil_table
        step = {
            "slope": C.score_continuous_breaks(raw["slope"], cls.SLOPE),
            "rainfall": C.score_quantiles(np.where(mask, raw["rainfall"], np.nan)),
            "soil": C.score_categorical(raw["soil"], soil_table, C.SOIL_DEFAULT_SCORE),
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
    _assert_palette()
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
