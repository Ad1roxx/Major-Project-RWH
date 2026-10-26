# Figure Review Protocol

**Read this before touching `tools/make_figures.py` or any file in
`outputs/figures/`.**

This file exists because the paper's figures went through six rounds of
external review, and the standard that emerged lives nowhere else in the repo.
Without it a new session re-learns the same lessons by making the same
mistakes, and — worse — re-opens decisions that are already settled.

Written 3 October 2026. Audience: whoever picks this up next, human or model,
with no memory of the review rounds.

---

## 0. The thirty-second version

```powershell
venv\Scripts\Activate.ps1
python tools/make_figures.py            # all 17, ~2 min; prints every value it plots
python tools/make_figures.py --only 13  # one figure
python tools/smoke_test.py              # 14 checks, ~60 s — run before declaring done
```

`make_figures.py` prints a `⚠` line for every automated defect it finds. **A
clean run prints no `⚠` at all.** If you see one, fix it before anything else.

Then **look at the PNG**. The automated checks catch collisions and arithmetic;
they cannot tell you the figure argues the wrong thing. Most blocking findings
across six rounds were of the second kind.

---

## 1. What the automated checks cover, and what they don't

### `_text_problems` in `tools/make_figures.py`

Runs on every `_save`. Four tests:

| Test | Catches |
|---|---|
| Legend colour vs label | A legend entry drawn in a criterion's or a weighting method's colour without naming it |
| Annotation colour | An annotation in a criterion's colour on a panel that is not about that criterion |
| Baked-in caption | Figure-level prose below the axes, which belongs in the CAPTION key |
| Text near the canvas edge | A label with no breathing room |
| Text ∩ text | Legend over title, two scatter labels on each other |
| Text ∩ artist | A curve, bar or reference line through a label |
| Leader ∩ other text | An annotation's leader drawn across a *different* label |

Three refinements it needs, all learned the hard way — do not "simplify" them
back out:

1. **Measure with `mtext.Text.get_window_extent`, not the artist's own.**
   `Annotation.get_window_extent()` unions in the leader arrow, so every
   correctly-placed label pointing at a curve reports as sitting on it.
2. **Skip text outside the panels.** Axis labels, panel titles and legends live
   in the margins by design.
3. **Skip a label whose colour contrasts with the patch under it.** That is a
   label deliberately set inside its own bar.

Lines are tested as **segments** via `Path.intersects_bbox`, not as vertices.
A vertex test is blind to `axvline`/`axhline`, which have two vertices at the
ends of the axes and can cross anything in between — this hid a defect for a
whole round.

### `_assert_palette`

Runs at startup. Fails if two semantic colours are closer than **CIEDE2000
ΔE 10**, i.e. confusable rather than merely unequal. `CRIT_COLOUR['rainfall']`
and `MEANING['rainfall']` are exempt by name (deliberately the same), as are
soil's pair and `MEANING['method']`/`NEUTRAL_BAR`.

### `tools/smoke_test.py`

Three checks matter for figures:

- **`check_class_shares`** — every path that reports a class share agrees with
  `gis_analysis.class_share_pct` to 0.005 pp.
- **`check_no_rounded_inputs`** — no derived effect is computed by differencing
  a rounded share. Static scan plus a behavioural test.
- **`check_transition_partition`** — a class-transition decomposition must
  partition cells. Asserts the identities and that no component is negative.

### What nothing checks

- Whether the title matches the data.
- Whether the figure measures what its label claims.
- Whether two figures tell contradictory stories.
- Whether a caption's caveats are the ones a referee will want.

These are where the real findings came from. See §3.

---

## 2. Settled decisions — do not re-open without asking

Each of these cost a review round. They are not preferences.

| Decision | Why |
|---|---|
| **Shares are area-weighted, never cell counts.** Read them through `gis_analysis.class_share_pct`. | EPSG:4326 cells shrink with latitude, 0.81% across the district. Two figures once disagreed by 0.05 pp for this reason. |
| **Anything that SUBTRACTS two shares uses `percent_exact`.** | The rounded `percent` field quantises every difference to 0.01 pp. It silently corrupted the factorial effects *and* both sensitivity analyses. |
| **Class breaks: Low is score ≤ 0.65, High is > 0.85.** | `gis_analysis._classify_suitability`. Every legend and label uses this. |
| **Decimals follow provenance.** 3 dp for factorial effects (differences of area shares); 2 dp for anything derived from an already-2-dp input. | Trailing zeros are a claim about precision. |
| **All rounding is half-up via `_r`/`_pp`/`_fx`, applied ONCE, to an unrounded value.** A value stored at 2 dp and printed at 1 dp is double-rounded: 42.849 → 42.85 → 42.9, and 36.946 → 36.95 → 37.0 (Fig 18, fixed 4 Oct 2026 via sensitivity's `*_exact` fields). | Python rounds half-to-even on binary floats, so 15.35→15.3 while 42.85→42.9 in the same panel. |
| **PNG only, 300 dpi. No PDFs.** | User instruction, 2026-10-03: the vector copies were burning usage limits. `_save` says how to re-add them at submission. |
| **Map furniture goes where `_clear_corner` says**, and ONLY via `_place_furniture`. `_add_scalebar` asserts it, and `_map(furniture=True)` now raises. | Fixed by hand on one figure, repeated on two others; Figure 6 then drew its bar in a margin axes of unrelated width, so a "25 km" bar measured about 30 km. |
| **Categorical axes take ticks and names from a class table** (`_category_axis`), never from an automatic locator. | IGBP codes were ticked at 5.0, 7.5, 10.0 — positions that are not classes — and soil was shown as bare codes, which is unverifiable after a legend error. |
| **No figure-level prose below the axes.** It goes in the `CAPTION` key. | A journal cannot typeset text baked into a picture, and it duplicates the caption. |
| **One colour per criterion (`CRIT_COLOUR`), used everywhere.** `NEUTRAL_BAR` for a bare magnitude, `SIGN_COLOUR` only where bars are signed, `OTHER_COLOUR` and `PARTITION` for quantities that are neither. `GENERIC` = (near-black `#1A1A1A`, vermilion) is the house pair for "one series against another" and must NOT be bound to a semantic role. **Near-black, like neutral grey, is ink that carries no meaning**: it is the scoring curve in Fig 5, the ramps in Fig 8 and the top-five ranks in Fig 9 (told apart by marker), and that reuse does not break "one colour, one meaning". It is excluded from `_assert_series_colours` for that reason. | Rainfall was once vermilion in one figure and green in the next; vermilion later meant Fuzzy-AHP, positive change and variance share at once. |
| **One name for the High class: `HIGH_LABEL`.** | Three names were in use for one quantity. |
| **Panels plotting the same quantity share an axis; panels plotting different quantities must not.** | Figures 17 and 18 are the deliberate exceptions. |
| **Titles state the finding and are computed from the data where possible.** | Two titles went stale and one was factually wrong — it named slope as least discriminating when land cover is, by a factor of five. |

### The project's two headline distinctions

A new session gets these wrong by default. Both are load-bearing for the paper.

1. **Weighting METHOD ≠ weighting JUDGEMENTS.** AHP → Fuzzy-AHP on one fixed
   set of judgements moves the High share **0.560 pp**. The *range* across the
   five scenario judgement sets is **16.23 pp** — about 29×. "Weighting barely
   matters" is true only of the method. Figure 12 carries both bars on one axis
   so this cannot be misread.

2. **Contribution to LEVEL ≠ contribution to VARIATION.**
   `single_parameter_sensitivity` measures the share of the score's *level* a
   criterion supplies (Napolitano & Fabbri 1996). It is **not** an influence
   measure. `discrimination_weights` (Pratt index) measures the share of the
   *variance*. They disagree sharply: slope supplies 1.40× its weight in level
   and 0.43× in variance; land cover 1.32× and 0.08×. Never call the first one
   "effective weight" or "realised influence" without qualification.

---

## 3. The recurring defect taxonomy

Six rounds of findings sort into seven classes. Check each one against any
figure you change.

**A. The title claims more than the data shows.**
*"What moves the result depends on which class you look at"* implied the
ranking of drivers changed between panels. It didn't — only one magnitude did.
*"Slope … the least discrimination"* named the wrong criterion outright.
→ State the finding, and compute the names and numbers in it from the data.

**B. The measure isn't what the label says.**
"Effective weight" was a level decomposition presented as influence. An ECDF
was labelled "% of cells" after it became area-weighted.
→ Read the function that produced the number before writing the axis label.

**C. Two figures disagree about one quantity.**
41.08% against 41.04% for the same surface, because two code paths computed
"share of district" differently.
→ One function, called by everything. Assert it in the smoke test.

**D. Precision that wasn't earned.**
Effects quantised to 0.01 pp by differencing a rounded field, then printed to
three decimals. Three Low-class values all ending in zero was the tell.
→ Trace every printed digit to its input.

**E. Overprints.**
Text on text, text on curves, leaders across other labels, furniture on the
data, labels at the image edge.
→ The automated check covers these now. If it fires, fix it; don't suppress it.

**F. Colour or terminology meaning two things.**
Blue meaning AHP in one figure and Slope in the next. Vermilion meaning
Fuzzy-AHP, positive change, and variance share.
→ `CRIT_COLOUR` / `MEANING` / `HIGH_LABEL`, and `_assert_palette`.

**G. A caveat a referee will raise first.**
A range over five scenarios presented beside single pairwise changes. A
variance decomposition that partitions the continuous score, not High-class
membership. A measure defined only for a linear aggregator.
→ Put it in the caption. A referee who finds it unprompted discounts the whole
figure.

---

## 4. Current status

All 17 generated figures pass every automated check as of 3 October 2026.
**This table predates rounds 8–10; §4b is the current status.** Round 8
reopened Figs 12 and 21, round 9 reopened Figs 2, 5, 6, 8, 9 and 22, and all
of them were fixed. Round 10 fixed Fig 10's caption, which contradicted Fig 21,
and made Fig 13's unchanged share area-weighted (87.17%, not 87.16%).

| Figure | Content | Review status |
|---|---|---|
| 2 | Why fixed reclassification replaced min–max | Publishable |
| 5 | Six scoring functions | Publishable |
| 6 | Six criterion surfaces | Publishable |
| 8 | Step vs ramp, tied plateau | Publishable |
| 9 | Parallel coordinates, 25 sites | Publishable |
| 10 | Four MCDA methods, classified | Publishable |
| 11 | Factorial interaction, High share | Publishable |
| 12 | Effect magnitudes, High and Low | Publishable |
| 13 | ECDF + class transitions | Publishable |
| 14 | Percentile-rank difference + edge test | Publishable |
| 15 | Scenario weights + High share | Publishable |
| 16 | Agreement rasters, shared categories | Publishable |
| 17 | Weight perturbation + map removal | Publishable |
| 18 | Level vs variation contribution | Publishable |
| 19 | Criterion correlation matrix | Publishable |
| 21 | Ranking vs cutoff cell partition | Publishable |
| 22 | Stability vs suitability | Publishable |

**Every figure generated by this tool has now been reviewed** (seven rounds,
3 October 2026). Figures 1, 3, 4, 7 and 20 are not generated here — QGIS
layouts and drawing-tool diagrams; see `docs/FIGURE_SPECS.md`. There is no
outstanding "rank displacement" figure: Figure 21 was that scatter and was
replaced by the ranking-versus-cutoff cell partition.

Three dependencies the figures surfaced that belong in the paper's text rather
than in a figure:

- **The shortlist stands on 43 km².** Loam, the only texture scored 1.00, is
  0.376% of the district, and 4 of the top 5 sites sit on it. Limitations.
- **n = 973 is a historical reconstruction.** Under the corrected soil legend
  the same step scheme gives 1. Never quote 973 as current.
- **The level share is a mean of per-cell ratios**, so it is not reproducible
  from Fig. 6's criterion means (38.2% against 36.95% for rainfall). Say so in
  Fig. 18's caption or a reader will report it as an error.

### Figure 21, answered 3 October 2026

It asked whether the WLC → TOPSIS disagreement is **ranking** or
**breakpoints**. The answer is both, for two different questions, and the
figure shows which is which:

- The **+9.03 pp Low-class share shift is a breakpoint artefact** — zero by
  construction once the class sizes are matched. Nothing about the ordering had
  to change for it to appear.
- Of the **12.83% of area that changes class, 50.3% changes under BOTH
  cutoff schemes tested** — two schemes, not "any" (6.46 of 12.83 pp). Note: an earlier netted version of this
  said 77%. That was wrong — it subtracted two totals over different sets of
  cells, and the Low component came out negative. Decompositions of this kind
  must partition CELLS; `tools/smoke_test.py` now asserts it.

So the class-share statistic is the fragile one and the ranking is
comparatively robust. State that as a finding, not a caveat.

**Figure 22 (stability vs suitability) is now the unreviewed one.**


---

## 4b. Review status — 3 October 2026, after round 10

**Every figure generated by `tools/make_figures.py` is publishable.** Round 8's
items on Figures 12 and 21 and round 9's on 2, 5, 6, 8, 9 and 22 are fixed.
What remains is for the paper's TEXT, not the figures:

- **Justify Loam = 1.00 with a citation in the Methods.** It is now the single
  most consequential scoring choice: Loam is 0.376% of the district (42.9 km²)
  and 4 of the top 5 sites sit on it (Fig. 9). The ordering Loam > Sandy Clay
  Loam > Clay Loam > Clay needs a source.
- **Rescore Loam at 0.80 and report how the shortlist moves** — the obvious
  robustness check, not yet run.
- **n = 973 is a historical reconstruction.** Never quote it as current (Fig. 8).
- **The cutoff scheme is an analyst decision.** Range across four standard
  schemes: 36.43 pp on High (Fig. 12). Fixed-scheme Low shift of +9.03 pp is
  a cutoff effect; 50.3% of class-changing cells change under BOTH schemes
  tested — not "any" (Fig. 21).

Not yet reviewed at all: Figures 1, 3, 4, 7, 20 (QGIS / drawing tool, outside
the automated checks; specified in `docs/FIGURE_SPECS.md`).

### Round 9 fixes worth knowing about

- **Figure 8 was drawing bars for empty bins.** `np.maximum(counts, 0.6)` made
  zero-count bins visible on the log axis; the ramp surface has no cells above
  0.96 and the figure showed two bars there. Empty bins are now NaN (undrawn),
  and the artist test ignores non-finite patch extents.
- The artist test now checks **tick labels within the view limits** and tests
  **annotations wherever they sit**, not only inside the data area — Figure
  9's Loam callout had been printed across the x tick labels unflagged.
- Figure 5's categorical panels plot at **ordinal positions** (evenly spaced),
  land cover abbreviated with a key in the caption.

### Round 10 (3 October 2026) — all fixed; verified in code first

- **Fig 8(b) mixed legends** — reviewer right. The ramp series was the current
  composite in both panels. Each panel now holds its legend fixed for both
  series. Ramps on the superseded legend: 0 tied, 18.51% High. Outline
  histograms on 0.01 bins from 0.85; tied bar at 1.00.
- **Fig 22 straddling bin** — no cell was actually impossible (0 cells above 0.85
  with 0 votes, now asserted); a bin ran 0.8476–0.8560. Edges anchored at
  0.85. The caption band was wrong: it is 0.817–0.889 (0.033 below, 0.039 above).
- **Fig 9** — the title now reads from w·SD (soil 0.027, rainfall 0.023), which
  is printed under SD. Rank colours are YlGnBu; plasma rank 4 was ΔE 6.0 from
  Fuzzy-AHP.
- **Fig 5** — settlement is a GENTLE PEAK (0.97 / 1.00 / 0.97 at 1 / 3 / 5 km,
  `criteria.moderate_optimal`), not a plateau; the caption was wrong, not
  the curve. The √-scale bars were squashed by a negative autoscale floor
  folded by √|v|; ylim is pinned at 0, so Loam is 7% of the height.
  Drainage anchors are in the caption. Soil w = 0.1535363 → 0.154 is correct.
- **Fig 2** — retitled, with the chronology in the caption; (d)–(f) share y;
  abbreviations as in Fig 5; "Forest" → DBF.
- **Fig 6/10/16** — graticule on every panel, labelled on outer edges
  (`_outer_graticule`). Fig 6 stats are in the titles, and the caption says
  they are per-cell and unweighted.
- **New generator checks:** `_assert_series_colours` (colormap-sampled series vs
  semantic colours) and `_edges_include` (bin edges contain breakpoints).
  There is no generic "bar x = value" check; Fig 8 no longer offsets bars.
- **`review_pack/FIGURE_DATA.md` is now generated** by
  `tools/build_figure_data.py` (rebuilds every figure in the same run). Never
  edit it by hand.

### Round 11 (3 October 2026) — Figs 10 and 13, all fixed

- **The generic series colour is now near-black `#1A1A1A`** (was Okabe blue
  `#0072B2`, ΔE 5.5 from the High class blue). This affects Figs 5, 8 and 13.
  `_assert_palette` now includes CLASS_COLOURS and GENERIC, so this can't recur.
  SIGN_COLOUR (Fig 17) still uses Okabe blue for "−"; it is not in the assertion.
- Fig 13: (a) WLC solid near-black and TOPSIS dashed vermilion; the 0.65 labels
  sit right of the breakpoint, so no leader crosses a curve; the title gives
  87.17%; the caption names the three small flows in the footer line.
- Fig 10: the title states the finding with "at fixed cutoffs"; the figure is
  narrower and the legend centred; the caption notes 99.99 sums. The graticule
  was already added in round 10.
- FIGURE_SPECS Fig 7: Medium is `#E8E4DC`, matching the generated maps.

### Round 12 (4 October 2026) — Figs 5, 6, 8, 9

- **Fig 9:** axes ordered by w·SD (soil, rainfall, drainage, settlement, slope,
  land cover), matching the title. **Ranks are encoded by MARKER in one colour
  (GENERIC[0]), not by hue.** 15 colormaps were tested and none clears every
  semantic colour by ΔE 10 (YlGnBu rank 3 was 9.2 from High). Don't go back to
  a colour ramp. `_assert_series_colours` now includes CLASS_COLOURS. The
  notes were moved to empty regions.
- **Fig 8:** the caption no longer quotes the 18.51% High (a superseded-legend
  reconstruction; the data key is now `..._RECONSTRUCTION`). It now says the
  tied cells are a subset of the 0.99–1.00 bin.
- **Fig 6:** shortened "Drainage dens." / "Settlement" titles. **Fig 5:** the
  truncation box is moved off the 0.10 floor.
- The reviewer listed Fig 10's title, Fig 13's blue, Fig 13's flows caption
  and the Fig 7 Medium colour as open. All four were fixed in round 11 — the
  reviewer had old PNGs.

### Round 14 (4 October 2026) — Figs 10–19, 21: the generated set is done

- **Fig 21:** "matched: 0.96" overprinted "fixed: 10.53". Rows are now 1.4 apart.
  **The checker missed it because `overlap_frac` was 0.22**; the overlap was a
  sliver. It is now 0.03. That catches this case, and the whole set is silent.
  The caption now has a rounding note.
- **Fig 18:** 42.9 → 42.8 and 37.0 → 36.9, both from double rounding (see §2).
- **Fig 17(c):** bars are NEUTRAL_BAR (SIGN_COLOUR's Okabe blue was ΔE 5.5 from
  High). The title states the finding and is computed.
- **Fig 16:** "majority" → "half or more"; finding title (528 vs 240 km²).
- **Fig 15(b):** "16.23 pp".

## 5. Traps in this codebase

Four things that will waste an hour if you don't know them.

1. **`tools/inspect.py` shadows the stdlib `inspect` module.** Any script that
   puts `tools/` on `sys.path` before importing matplotlib dies with
   `cannot import name 'Parameter' from 'inspect'`. `make_figures.py` strips
   `tools/` from `sys.path` before third-party imports for exactly this reason.

2. **Bash heredocs collapse `\\n` to a real newline**, which turns a Python
   string literal into a syntax error. When patching files with a heredoc
   script, build newlines as `chr(92) + 'n'`, or use the Edit tool instead.
   This bit five times.

3. **`FancyArrowPatch.get_path()` coordinate space varies.** Don't transform it
   to test a leader; build the anchor→label segment explicitly.

4. **`fill_between` bounding boxes are useless for collision testing.** A
   curved ribbon's bbox covers most of the panel. Test the path with
   `intersects_bbox(..., filled=True)`.

---

## 6. Working agreements for this task

- **Do not commit or push** unless explicitly asked. The user said so on
  3 October: *"stop wasting time on committing stuff every change i will tell
  you when to commit and push again."*
- **Do not generate PDFs.** Same date: they ate usage limits.
- **Say when a review finding is wrong.** Two were, across six rounds — slope
  was described as heavily *tied* when it is *concentrated* (0.1% largest tied
  value, 86% above 0.90), and one number was said to have changed when only its
  display precision had. Correcting these improved the figures; accepting them
  would have put a false statement in the caption.
- **If a figure is better made in QGIS, say so instead of making it.** The user
  asked for this directly. `docs/FIGURE_SPECS.md` records the five that are.

---

## 7. Where the numbers live

| Need | File |
|---|---|
| Every value plotted, by figure | `python tools/make_figures.py` prints them |
| Every number cited in the paper, by section | `python tools/paper_figures.py` |
| Audited context for the paper, fact-vs-inference tagged | `docs/RESEARCH_CONTEXT.md` |
| Dated record of what changed and why | `CHANGELOG.md` — the 2026-10-03 entries cover all six review rounds |
| Conventions and current state | `CLAUDE.md` |

**`CHANGELOG.md` is the real history.** If you need to know why something is
the way it is, the four entries dated 2026-10-03 explain every decision in this
file, with the measurements that drove them.
