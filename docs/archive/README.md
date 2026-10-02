# Archive — superseded documents

Nothing here describes the current system. These files are kept because they
record how the project got to where it is, not because they are accurate.

**Do not cite anything in this folder.** Every file predates at least one
correction that changed the results.

---

## The seven `AHP_*.md` explainers (April 2026)

Written before the first methodological sprint. They describe the system as it
was when:

- criterion scores came from **min–max rescaling** of the observed data range,
  which left 95.8% of slope cells above 0.90 and scored categorical layers by
  their class code number;
- suitability was classified by a **33rd/67th percentile split**, which reports
  roughly a third of any district as highly suitable regardless of the data;
- the drainage criterion measured **distance to the nearest river** rather than
  drainage density.

All three were replaced. The weights quoted in these files (soil 0.136, and so
on) are not the current weights either.

**Current equivalent:** `docs/METHODOLOGY.md` for the scoring rules and
`docs/AHP_MATRIX_AUDIT.md` for the pairwise matrix.

| File | Was |
|---|---|
| `AHP_ANALYSIS_GUIDE.md` | Overview of the AHP step |
| `AHP_CALCULATION_EXAMPLE.md` | Worked weight calculation |
| `AHP_DECISION_LOGIC.md` | Criterion reasoning |
| `AHP_MATCHUP_ANALYSIS.md` | Pairwise comparison notes |
| `AHP_MCDA_LOGIC_AND_CALCULATIONS.md` | Combined AHP + overlay walkthrough |
| `AHP_PYTHON_CODE.md` | Code snippets, since superseded by `ahp.py` |
| `AHP_REAL_EXAMPLES.md` | Hand-worked site examples |

## `CHANGES_SINCE_INITIAL_ZIP.md` (April 2026)

Reconstructed change list from before `CHANGELOG.md` existed. Covers the move
from the original prototype to the first working AHP pipeline. Superseded by
`CHANGELOG.md`, which has carried every change since 29 July 2026.

## `PROGRESS_UPDATE.md` (4 August 2026)

A plain-language status note written for the project supervisor. Accurate on the
day it was written; every result in it has since changed — most significantly by
the soil legend correction of 2 October 2026, which moved the highly suitable
share from 18.51% to 6.44%.

**Current equivalent:** `docs/presentation/FINAL_PROJECT_DOCUMENTATION.md`.

---

## Why these were kept rather than deleted

Three of the project's findings are about defects in its own earlier versions —
the min–max flattening, the tied-plateau scoring, and the soil legend error. The
paper reports all three. These files are the contemporaneous record of the state
those findings describe, so deleting them would remove the evidence that the
"before" condition was real.
