# Photo labelling protocol

> Completed on 2026-10-16, **after labelling had started and before `key.csv`
> was opened**. Don't edit sections 1–6 again. Any later change goes at the
> bottom under "Deviations", with the date and the reason.
>
> The procedure is in [PHOTO_LABELLING_GUIDE.md](PHOTO_LABELLING_GUIDE.md).

**Completed on:** 2026-10-16  **By:** [ name ]

**Labeller A:** [ name ]  **Labeller B:** [ name ]  **Coordinator (holds key.csv):** Labeller B. The key stays unopened until both sheets are final.

---

## 1. Labels

Allowed labels (fixed): `storage`, `recharge`, `well`, `catchment`, `other`, `unclear`.

The **draft definitions in the guide, §4, were used unchanged** by both
labellers. They were not separately confirmed before labelling began (see
Deviations).

| Label | Definition |
|---|---|
| storage | A structure built to hold surface water: an open water body, or an embankment, wall or dam that impounds water. Dry is fine if the structure is clearly there |
| recharge | A structure built mainly to put water into the ground, without a visible open body of water |
| well | A structure for taking water out of the ground |
| catchment | Treatment of land or slopes to slow runoff and hold soil, with no storage or recharge structure in view |
| other | Clearly not a water work (house, road, building, cattle shed, toilet, plantation, any non-water asset) |
| unclear | Can't be decided from the photo |

## 2. Edge cases

The guide's draft answers (§4) were used unchanged:

| Case | Decision |
|---|---|
| Percolation tank | storage |
| Check dam with no water, wall visible | storage |
| Check dam with no water, wall not clear | unclear |
| Gully plug / loose-boulder structure | catchment |
| Only a signboard, no structure visible | unclear |
| Signboard plus a visible structure: may the board's text be used? | no; label the structure, write "board" in notes |
| Two structures in one photo | label the main one, note the other |
| Structure under construction | unclear if too early to tell what it is; otherwise label what it is |

## 3. What counts as a positive

**`storage` and `recharge` both count as rainwater-harvesting positives.**
Reason: the study is explicitly recharge-oriented (harvesting runoff so it
reaches groundwater), so excluding recharge structures would contradict its
stated objective.

**`well`, `catchment` and `other` are not positive.** Wells extract water
rather than harvest it, and catchment treatment is spread over an area, not a
point structure.

**`unclear` photos are excluded from the denominator.**

## 4. Inclusion rule for a category segment

A category segment (WC, WH, RS, DP, IF, LD, FP) enters the validation positive
set if **both** of the following hold:

- at least **50%** of its photos with a final label other than `unclear` are
  positive (§3); and
- the lower bound of the **95% Wilson interval** for that share is at least
  **30%**.

**Segments that are never positives, whatever the photos show:** IF/IAY
(individual household works and housing).

**Records within an included segment:** all are used. Accuracy thresholds,
stage choice and out-of-district handling are decided separately, before the
validation is run, and recorded under Deviations with their reasons.

## 5. Agreement and resolution

Agreement is reported as **Cohen's kappa on the raw sheets**, before any
resolution, as it comes out.

**If kappa is below 0.6, the result is reported as it is and the analysis
proceeds.** The low agreement is stated as a limitation. There is no
relabelling.

**Resolution without a joint session** (replaces guide §5, steps 3–4):

- Where both labellers agree, the final label is the shared label.
- Where both said `unclear`, the photo is excluded.
- **Any other disagreement makes the photo NOT positive** (the strict rule),
  and it stays in the denominator.

**Sensitivity check:** the inclusion rule is also reported under a lenient
rule, where a photo is positive if either labeller marked it positive. The
strict rule is the primary result.

## 6. Sign-off

[ name ], 2026-10-16

---

## Deviations (add only after labelling has started)

| Date | Change | Reason |
|---|---|---|
| 2026-10-16 | The protocol was completed after labelling had started. Sections 1–2 record the guide's draft definitions and edge-case answers, which both labellers used unchanged. Sections 3–5 were fixed on this date, before `key.csv` was opened | The protocol was not completed before the labelling packs were sent out |
| 2026-10-16 | Disagreements are resolved by a fixed strict rule (§5) instead of a joint session | The labellers could not meet for a joint review |
| 2026-10-18 | Claude Code opened `key.csv` before labeller A's corrected sheet was in, while checking an agreement of kappa ≈ 0. Labeller A's label column appears shifted one row down: the label on row P(n) fits photo P(n−1), and there is an extra 241st label. Neither labeller has seen the key. Labeller A is asked to confirm or correct the alignment against the photos themselves; the sheet is not re-aligned without that confirmation | Agreement at chance level indicated a data-entry fault rather than a labelling result |
| 2026-10-18 | Labeller A's sheet was re-aligned by one row (row P(n+1)'s label assigned to P(n); the stray row 144 ID cell ignored) **on the coordinator's instruction, without labeller A's confirmation**. Raw sheet kept as `returned/labels_A_raw.csv`. Labeller B's one out-of-set label (P156, "toilet") was mapped to `other` | Time constraints. The shift is consistent across the whole sheet (kappa 0.38–0.62 in each third after shifting, about 0 before) |
