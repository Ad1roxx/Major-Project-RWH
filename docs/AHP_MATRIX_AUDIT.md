# AHP Comparison Matrix — Retrospective Audit

**Audit conducted: 23 September 2026.**
**This document is not a record of the original elicitation.** No such record
exists. It is an audit of the shipped matrix, performed after the fact, and
every analysis in it was run on the date above.

---

## Why this document exists, and what it replaces

The paper draft contained a placeholder — *"the matrix was revised [N] times
until CR fell below 0.10"* — describing a multi-round elicitation protocol.

**No evidence of such a protocol exists in this project.** There is no version
control, `CHANGELOG.md` never mentions elicitation or matrix revision, and
`ahp.py` contains a single hand-written matrix literal with no intermediate
versions. Writing a round count would assert a process that cannot be
substantiated if a reviewer asks.

This audit replaces that sentence with something stronger and true: rather than
claiming a history we cannot evidence, we characterise the matrix we actually
have — how consistent it is, how sensitive the result is to each individual
judgement, and where it sits within the space of defensible alternatives.

**⚠ Nothing in this document may be presented as having occurred during
development.** If the paper cites it, cite it as a post-hoc audit dated
September 2026.

---

## 1. What the matrix is — established facts

### 1.1 It is hand-specified, not ranking-derived

The codebase contains a helper, `AHPEngine.matrix_from_levels()`, that generates
a pairwise matrix from an importance ranking by snapping each ratio to the Saaty
scale. Matrices built that way are consistent by construction.

**The shipped matrix was not built that way.** Tested against ranking vectors
derived from the shipped weights at five scale factors, the closest
reconstruction differs in **20 of 36 cells**, with a maximum absolute difference
of 3.0 on the Saaty scale.

This matters for two reasons. It confirms the 15 judgements were stated
independently rather than generated from a single ordering — which is what AHP
intends. And it explains why CR = 0.0235 rather than the ~0.003 that
ranking-derived matrices produce: genuine independent judgement carries genuine
residual inconsistency.

### 1.2 The 15 judgements

Saaty 1–9 scale; `a_ij` is how much more important criterion *i* is than *j*.

| Comparison | a_ij |
|---|---|
| slope vs rainfall | 1/3 |
| slope vs drainage | 3 |
| slope vs soil | 2 |
| slope vs lulc | 4 |
| slope vs population | 5 |
| rainfall vs drainage | 5 |
| rainfall vs soil | 3 |
| rainfall vs lulc | 6 |
| rainfall vs population | 7 |
| drainage vs soil | 1/2 |
| drainage vs lulc | 2 |
| drainage vs population | 3 |
| soil vs lulc | 3 |
| soil vs population | 4 |
| lulc vs population | 2 |

Full matrix:

|  | slope | rainfall | drainage | soil | lulc | population |
|---|---|---|---|---|---|---|
| **slope** | 1 | 1/3 | 3 | 2 | 4 | 5 |
| **rainfall** | 3 | 1 | 5 | 3 | 6 | 7 |
| **drainage** | 1/3 | 1/5 | 1 | 1/2 | 2 | 3 |
| **soil** | 1/2 | 1/3 | 2 | 1 | 3 | 4 |
| **lulc** | 1/4 | 1/6 | 1/2 | 1/3 | 1 | 2 |
| **population** | 1/5 | 1/7 | 1/3 | 1/4 | 1/2 | 1 |

λmax = 6.1460 · CI = 0.0292 · RI = 1.24 · **CR = 0.0235**

### 1.3 The stated rationale

Recorded in `ahp.py` as a source comment, verbatim:

> *Rainfall is the water source and dominates; slope governs whether the water
> can be retained at all; soil controls infiltration; drainage locates the
> runoff; LULC and settlement proximity are feasibility/demand modifiers rather
> than primary physical drivers.*

This is the only contemporaneous record of the judgement basis. It establishes
an **importance ordering** — rainfall > slope > soil > drainage > lulc >
population — which the shipped weights reproduce exactly. It does not establish
where the specific Saaty values came from.

---

## 2. Consistency diagnostic

For each judgement, the value implied by perfect consistency is wᵢ/wⱼ. The
deviation ratio is the stated value divided by that. The final column is the CR
the matrix would have if that one judgement were replaced by its consistent
value.

| Comparison | Stated | Implied | Deviation | CR if corrected |
|---|---|---|---|---|
| slope vs rainfall | 1/3 | 0.53 | **0.634** | 0.0159 |
| rainfall vs population | 7 | 10.80 | **0.648** | 0.0167 |
| slope vs soil | 2 | 1.47 | 1.363 | 0.0201 |
| lulc vs population | 2 | 1.51 | 1.328 | 0.0206 |
| drainage vs lulc | 2 | 1.56 | 1.282 | 0.0213 |
| drainage vs population | 3 | 2.35 | 1.277 | 0.0214 |
| slope vs drainage | 3 | 2.42 | 1.241 | 0.0219 |
| drainage vs soil | 1/2 | 0.61 | 0.824 | 0.0222 |
| rainfall vs lulc | 6 | 7.17 | 0.837 | 0.0224 |
| soil vs lulc | 3 | 2.57 | 1.167 | 0.0227 |
| slope vs population | 5 | 5.68 | 0.880 | 0.0230 |
| rainfall vs drainage | 5 | 4.60 | 1.087 | 0.0233 |
| rainfall vs soil | 3 | 2.79 | 1.075 | 0.0234 |
| slope vs lulc | 4 | 3.77 | 1.060 | 0.0234 |
| soil vs population | 4 | 3.87 | 1.034 | 0.0235 |

**Reading.** The two largest departures are *slope vs rainfall* (stated 1/3
against an implied 0.53) and *rainfall vs population* (stated 7 against an
implied 10.8). Both concern rainfall, and both understate it relative to
consistency — the analyst was, if anything, conservative about the criterion
they weighted highest.

**No single correction moves CR much.** Correcting the worst judgement takes CR
from 0.0235 to 0.0159. The inconsistency is distributed across the matrix rather
than concentrated in one bad judgement, which is the expected signature of
genuine independent elicitation rather than a transcription error.

---

## 3. Single-judgement perturbation

Each of the 15 judgements moved one step in each direction on the Saaty scale —
30 perturbations.

| Result | Value |
|---|---|
| Perturbations tested | 30 |
| **Worst CR reached** | **0.0336** (threshold 0.10) |
| Perturbations failing CR < 0.10 | **0** |
| Perturbations that change the criterion rank order | **0** |
| Largest weight shift from any single perturbation | **0.0234** (slope, via *slope vs soil*) |

**Reading.** No single judgement is load-bearing. Every one can be moved a full
step in either direction and the matrix remains consistent, the criterion
ordering survives, and no weight moves by more than 0.024. The matrix is not
sitting near any boundary.

Two useful specifics, taking each judgement's larger effect across its two
directions: the most influential single judgement is *slope vs soil* (0.0234),
and the least influential is *drainage vs population* (0.0058).

Reproduce with `python tools/ahp_audit.py --part B`.

---

## 4. Monte Carlo over the space of defensible matrices

This is the analysis that best answers the reviewer's real question: *how much
of your result rests on these particular fifteen numbers, as opposed to the
ordering behind them?*

**Method.** Each of the 15 judgements was independently perturbed by up to ±2
Saaty steps, drawn uniformly. A draw was accepted only if the resulting matrix
satisfied CR < 0.10 **and** preserved the criterion importance ordering stated
in §1.3. 4,000 matrices drawn; **1,013 accepted** (1,553 rejected on CR, 1,434
on ordering).

Every accepted matrix is a defensible alternative elicitation: same stated
reasoning, different numbers.

### 4.1 Where the shipped weights sit

| Criterion | Shipped | MC mean | MC sd | p5 | p95 | Shipped percentile |
|---|---|---|---|---|---|---|
| slope | 0.2254 | 0.2343 | 0.0404 | 0.1736 | 0.3060 | 43% |
| rainfall | 0.4285 | 0.4090 | 0.0478 | 0.3295 | 0.4837 | 63% |
| drainage | 0.0932 | 0.0965 | 0.0191 | 0.0693 | 0.1325 | 48% |
| soil | 0.1535 | 0.1547 | 0.0286 | 0.1113 | 0.2034 | 51% |
| lulc | 0.0597 | 0.0634 | 0.0115 | 0.0474 | 0.0848 | 40% |
| population | 0.0397 | 0.0421 | 0.0075 | 0.0312 | 0.0557 | 41% |

**Every shipped weight falls between the 40th and 63rd percentile of the
distribution of defensible alternatives.** The matrix is not an outlier, and it
was not selected from the tail of judgement space.

**A second observation worth reporting.** The shipped matrix's CR of 0.0235 sits
far below the median CR of accepted alternatives (**0.0783**). Among matrices
that encode the same importance ordering, the shipped one is unusually
self-consistent.

### 4.2 Downstream effect on the actual result

200 of the accepted matrices were scored through the full pipeline.

| Measure | Result |
|---|---|
| High-suitability share, shipped | 18.51% |
| High-suitability share, MC mean | 18.75% (sd 2.24) |
| Range across 200 matrices | 14.19% – 26.94% |
| Top-10 site retention vs shipped, mean | 7.8 / 10 |
| Top-10 retention, median | 8 / 10 |
| Top-10 retention, minimum | 5 / 10 |
| Matrices retaining ≥ 8 of 10 | 53% |
| Matrices retaining 10 of 10 | 12% |

**Reading.** The shipped result sits essentially at the mean of what any
defensible elicitation of the same reasoning would produce (18.51% against a
mean of 18.75%). The classified map is stable: even the full ±2-step
re-elicitation moves the High share within a ~±2 pp band for most draws.

The shortlist is more sensitive: a median of 8 of the top 10 survive. That is
real and should be reported as such.

### 4.3 Reconciling this with the ±20% sensitivity result

These two numbers look inconsistent and are not. The ±20% one-way analysis
retains 90% of the top 10; this analysis retains a median of 80%. The difference
is the size of the perturbation:

- **±20% one-way** moves **one weight at a time** by a fifth.
- **This analysis** moves **all fifteen judgements at once** by up to two full
  Saaty steps each.

The second is a far larger excursion. Reporting both is more informative than
reporting either: the result is highly stable to individual weight uncertainty
and moderately stable to wholesale re-elicitation.

---

## 5. Suggested Methods-section wording

Replace the `[N]` sentence with the following. Every clause is supported above.

> Criterion weights were derived by the Analytic Hierarchy Process from a single
> pairwise comparison matrix over the six criteria, specified on the Saaty 1–9
> scale. The judgement basis was an importance ordering — rainfall > slope >
> soil > drainage density > land cover > settlement proximity — reflecting the
> role of each criterion in the recharge process: rainfall as the water source,
> slope as the control on retention, soil as the control on infiltration,
> drainage density as the indicator of runoff concentration, and land cover and
> settlement proximity as feasibility and demand modifiers. The fifteen pairwise
> judgements were stated independently rather than generated from the ordering.
> **The matrix was specified once and accepted without revision**, achieving a
> consistency ratio of 0.0235 on first evaluation — below the conventional 0.10
> acceptance threshold.
>
> Because the specific Saaty values, unlike the ordering, are not derivable from
> the literature, the matrix was subjected to a three-part audit. First, a
> per-judgement consistency diagnostic established that no single comparison
> accounts for the residual inconsistency: correcting the largest deviation
> reduces CR only from 0.0235 to 0.0159. Second, perturbing each judgement by
> one step in each direction (30 perturbations) left the matrix consistent in
> every case (worst CR 0.0336), preserved the criterion ordering in every case,
> and moved no weight by more than 0.024. Third, a Monte Carlo over judgement
> space perturbed all fifteen comparisons simultaneously by up to two Saaty
> steps, retaining the 1,013 of 4,000 draws that satisfied both CR < 0.10 and
> the stated ordering. Every shipped weight falls between the 40th and 63rd
> percentile of this distribution, and scoring 200 of these alternative matrices
> through the full pipeline yielded a highly-suitable share of 18.75 ± 2.24%
> against the reported 18.51%, with a median of 8 of the top 10 candidate sites
> retained.

**What this wording does not claim:** any group elicitation procedure, any
external expert panel, or any supervisory review. Those did not happen (§6).

---

## 6. Provenance — confirmed by the team, 23 September 2026

Two facts were outstanding when this audit was written. Both have now been
confirmed by the authors:

1. **The matrix was specified once and never revised.** There were no
   elicitation rounds, no intermediate matrices, and no consistency-driven
   adjustment. CR = 0.0235 was achieved on first evaluation. This is consistent
   with what the repository shows (a single matrix literal, no revision history)
   and §5 now states it directly.
2. **The matrix has not been externally reviewed.** It is the authors' own
   judgement. No supervisory sign-off, no expert panel, no Delphi process.
   **Do not add a review clause to §5.**

### Why fact 2 is a strength here, not a gap

An unreviewed expert-judgement matrix is a legitimate thing for a reviewer to
challenge — and the honest answer is that external validation of the *weights*
was never available to this project. What the audit establishes instead is that
**it does not matter very much.**

Section 4 shows that across 1,013 alternative matrices, each encoding the same
stated reasoning but different Saaty values, the highly-suitable share moves
from 18.51% to a mean of 18.75% ± 2.24. A different analyst applying the same
ordering would have landed in the same place. That is a stronger claim than
"our supervisor approved the matrix", because it is quantified and reproducible.

**Suggested response if challenged in review or viva:**

> "The matrix is our own judgement and was not externally reviewed — we say so
> in the paper. Rather than appeal to authority, we tested how much the result
> depends on it: across a thousand alternative matrices encoding the same
> importance ordering, the highly-suitable area moves by about two percentage
> points and our weights sit at the centre of that distribution. The ordering is
> what carries the result, and the ordering comes from the reviewed literature."

---

## 7. Reproduction

Committed as `tools/ahp_audit.py`.

```bash
python tools/ahp_audit.py            # all three parts
python tools/ahp_audit.py --part A   # consistency diagnostic
python tools/ahp_audit.py --part B   # single-judgement perturbation
python tools/ahp_audit.py --part C   # Monte Carlo (~1 min)
```

Monte Carlo seed **20260923**, 4,000 draws, 200 scored. Re-running reproduces
every figure in §4 exactly. Verified 25 September 2026.
