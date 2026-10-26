# START HERE

**For a session with no history of this project.** Read this file, then follow
the steps for your task. Nothing else is required reading.

Total to be useful: **~4,300 tokens**. Do not read `CHANGELOG.md`,
`docs/RESEARCH_CONTEXT.md` or `tools/make_figures.py` end to end — they are
~19k, ~20k and ~21k tokens. Grep them.

---

## The project in six lines

BTech major project: **GIS multi-criteria site selection for rainwater
harvesting, Chandrapur district, Maharashtra.** Python + Streamlit. Six
criteria, AHP weights, weighted linear combination, Low/Medium/High map plus 25
ranked sites. A research paper and a presentation are being written from it.
The analysis works and is stable; the live work is **the paper's figures**.

No git history — `CHANGELOG.md` stands in for it.

---

## Step 1 — always (~1,550 tokens)

Read **`CLAUDE.md`**. Pipeline, key files, conventions, current state,
commands. If you read one file, this is it.

## Step 2 — pick your task

### Working on figures (the usual case) — +~2,750 tokens

Read **`docs/FIGURE_REVIEW_PROTOCOL.md`**.

The figures went through six rounds of external review. That file holds the
standard, the settled decisions, the recurring defect taxonomy, the per-figure
status and the traps. Working on figures without it means repeating findings
that are already closed.

Then:

```powershell
venv\Scripts\Activate.ps1
python tools/make_figures.py        # all 17 + every value plotted, ~2 min
python tools/build_figure_data.py   # same, and writes review_pack/FIGURE_DATA.md
python tools/smoke_test.py          # 14 checks, ~60 s
```

A clean run prints **no `⚠` lines**. Then open the PNG in
`outputs/figures/` and look at it — the automated checks cannot tell you a
figure argues the wrong thing, and that is where most findings come from.

**Every generated figure is publishable.** What remains is listed in §4b of
the protocol: text for the paper (Loam justification, a robustness check) and
the five QGIS/diagram figures, which have not been reviewed.

### Writing or checking paper numbers — +~1,700 tokens

Run `python tools/paper_figures.py` — it prints every number cited in the
paper, by section, computed live. Never transcribe a number from a document;
regenerate it.

For audited context with fact-vs-inference tags, **grep**
`docs/RESEARCH_CONTEXT.md` for the section you need. Read its top banner
(~1,700 tokens) before quoting any result from it: it was written 2026-08-26
and every result-tier number in the body is superseded.

**Updating the manuscript?** `docs/PAPER_REVISIONS.md` lists every number,
claim and Methods description that changed after the soil correction
(2 Oct 2026), old → new, plus the three text items still to do.

### Changing the analysis itself — +~5,400 tokens

Read `docs/METHODOLOGY.md`. Every threshold and lookup in `criteria.py` is
justified there. Scoring lives in `criteria.py` and nowhere else.

### Needing a command — +~1,550 tokens

`RUNBOOK.md`. Every command with purpose, outputs, runtime and troubleshooting.

---

## Step 3 — the four things that will trip you up

1. **`tools/inspect.py` shadows the stdlib `inspect`.** Anything that puts
   `tools/` on `sys.path` before importing matplotlib dies with
   `cannot import name 'Parameter' from 'inspect'`.
2. **Bash heredocs collapse `\n`**, turning Python string literals into syntax
   errors. Patch files with the Edit tool, or build newlines as `chr(92)+'n'`.
3. **Class shares are area-weighted.** Read them through
   `gis_analysis.class_share_pct`. Anything that *subtracts* two shares must
   use `percent_exact` — the rounded `percent` field quantises differences to
   0.01 pp and has silently corrupted results twice.
4. **The soil legend was corrected on 2026-10-02.** Any document quoting
   **High 18.5%** is superseded; the current figure is **6.44%**.

---

## Step 4 — standing instructions from the user

- **Do not commit or push** unless explicitly told to.
- **Do not generate PDFs** — PNG only. They ate usage limits.
- **If a figure would be better made in QGIS, say so instead of making it.**
- **Say when a review finding is wrong.** Two were, across six rounds.
  Verify before accepting.
- **No invented numbers.** Anything reported must be traceable to a command
  that can be rerun.

---

## How to find things without reading whole files

```powershell
# why is something the way it is — the 2026-10-03 entries cover all six review rounds
Select-String -Path CHANGELOG.md -Pattern "2026-10-03" -Context 0,40

# where a number comes from
Select-String -Path tools/*.py,*.py -Pattern "<the number>"

# what a figure plots
Select-String -Path tools/make_figures.py -Pattern "def fig_13" -Context 0,60
```

| Question | Answer lives in |
|---|---|
| What does the pipeline do? | `CLAUDE.md` |
| How should figures look, and what's already settled? | `docs/FIGURE_REVIEW_PROTOCOL.md` |
| Why was this changed? | `CHANGELOG.md` (grep) |
| What is every number in the paper? | `python tools/paper_figures.py` |
| What is every value in a figure? | `python tools/make_figures.py` |
| Why is this threshold 0.65? | `docs/METHODOLOGY.md` |
| How do I run X? | `RUNBOOK.md` |
| The five figures made outside this repo | `docs/FIGURE_SPECS.md` |
| The soil legend error, in full | `docs/SOIL_LEGEND_CORRECTION.md` |
