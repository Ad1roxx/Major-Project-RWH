# Photo labelling guide — MGNREGA geotag audit

**What this is for.** The validation set is built from MGNREGA geotags. Each
geotag carries only a workcode category segment (WC, WH, RS, DP, IF, LD, FP …),
and nobody yet knows which segments actually mark rainwater-harvesting
structures. Two people label a sample of the geotag photos without seeing the
categories. The labels then decide which segments count as positives. Because
the labels choose the validation set, they have to come from people, with their
agreement measured.

**Who reads this:** the coordinator, both labellers, and whoever writes the
protocol.

---

## 1. Order of work — do not change it

| Step | Who | What | Done when |
|---|---|---|---|
| 1 | Team | Fill in [PHOTO_LABELLING_PROTOCOL.md](PHOTO_LABELLING_PROTOCOL.md): label definitions, the edge cases, whether *recharge* counts as a positive, and the inclusion threshold | Saved and dated, **before anyone opens a photo** |
| 2 | Claude Code | Build the blinded set: random IDs, the viewer page and empty sheets | **Done** — `reports/photo_audit/blind/` |
| 3 | Coordinator | Hand each labeller the blinded folder **without `key.csv`** | Both labellers have their folder |
| 4 | Two labellers | Label all 240 photos independently (§3) | `labels_A.csv` and `labels_B.csv` returned |
| 5 | Claude Code | Compute agreement on the **raw, unresolved** sheets and list the disagreements | Kappa reported |
| 6 | Both labellers | Resolve the disagreements together, still blind (§5) | `labels_final.csv` saved |
| 7 | Claude Code | Unblind with the key; compute shares per segment with intervals; apply the protocol's rule; build the positive set; run the validation | Validation report |

Step 1 comes first so the rules are fixed before anyone has seen the data. If
the rules were written after looking at the photos, a reviewer could fairly say
they were tuned to the result.

---

## 2. What is in the folder

`reports/photo_audit/blind/` (git-ignored, because field photos may show people):

| File | Who uses it |
|---|---|
| `P001.jpg` … `P240.jpg` | Labellers. The IDs are random and carry no category, stage or work information |
| `view.html` | Labellers. Open it in any browser; it shows each photo large with its ID, in a random order. It works offline |
| `labels_A.csv`, `labels_B.csv` | One per labeller. Columns: `random_id, label, notes` |
| `key.csv` | **Coordinator only.** It maps each ID to category, stage and workcode. **A labeller who opens it can no longer label blind.** |

**Coordinator: before step 3,** copy the folder for each labeller and delete
`key.csv` from each copy. Keep the original folder, with the key, yourself.

The sample is 30 photos from each of WC, WH, RS, DP, IF, LD and FP, plus 30 from
IF/IAY as a check. Labellers aren't told this breakdown, and shouldn't try to
work it out.

---

## 3. How to label (labellers)

1. Open `view.html` in a browser, and your own sheet (`labels_A.csv` **or**
   `labels_B.csv`) in Excel, LibreOffice or a text editor.
2. For each photo, find its ID in your sheet and type **one** label in the
   `label` column, exactly as written, in lower case:

   `storage` · `recharge` · `well` · `catchment` · `other` · `unclear`

   Their definitions are in the protocol (§4 below gives the draft). Label what
   the photo **shows**, not what you think the work was meant to be.
3. Use `notes` for anything that helped you decide or made it hard, such as
   "dry", "under construction", "only a signboard", "two structures", "blurred".
   Keep notes short.
4. **If you can't tell, use `unclear`.** Don't guess: an honest `unclear` costs
   nothing, and a guess adds noise that looks like signal.
5. Label every row. The view order differs from the ID order on purpose, so
   always check the ID printed above the photo.
6. Save as **CSV**, keeping the columns and row order. In Excel, choose "CSV
   UTF-8"; don't save as .xlsx or sort the rows.

**Rules that keep it blind and independent:**

- Don't open `key.csv`, the raw data, the reports, or the original
  `photo_audit/<category>/` folders.
- Don't discuss photos, or compare sheets, with the other labeller until
  **both** sheets are handed in.
- Don't change your labels after handing them in. Disagreements are settled in
  step 6, and the original sheets are kept as they were.
- At a few seconds a photo this takes 20–30 minutes. Take a break halfway, not
  in the middle of a doubtful photo.

**Signboards.** Many MGNREGA photos show the work's information board, which can
name the work ("farm pond", "recharge pit"). Reading it would partly unblind
you. Follow whatever rule the protocol sets for this; the draft rule is in §4.

---

## 4. Label definitions — DRAFT, confirm in the protocol

These are working definitions for MGNREGA works. **The team must confirm or
change them in the protocol before labelling.** They are listed here so
labellers see what they will be applying.

| Label | Use when the photo shows… | Typical works |
|---|---|---|
| `storage` | A structure built to **hold surface water**: an open water body, or an embankment, wall or dam that impounds water. Dry is fine if the structure is clearly there | Farm pond, village tank or pond, check dam or stop dam with its impounded reach, percolation tank, desilted tank |
| `recharge` | A structure built mainly to **put water into the ground**, without a visible open body of water | Recharge pit or shaft, recharge trench, well-recharge structure, soak-away for runoff |
| `well` | A structure for **taking water out of the ground** | Dug or open well, ring well, borewell with platform |
| `catchment` | **Treatment of land or slopes** to slow runoff and hold soil, with no storage or recharge structure in view | Contour or field bunds, continuous or staggered contour trenches, gully plugs and loose-boulder structures, land levelling, bund plantation |
| `other` | Clearly **not** a water work | House (e.g. IAY), road, building, cattle shed, toilet, roadside or block plantation, any non-water asset |
| `unclear` | You can't decide from the photo | Blurred or dark photo, only people, only a signboard (see below), a close-up with no context, too early in construction to tell |

**Edge cases the protocol must settle** (draft answers in brackets):

- Percolation tank: storage or recharge? [**storage**, because it holds open water]
- Check dam with no water and no visible impounded reach? [**storage** if the dam
  wall is clear; otherwise **unclear**]
- Gully plug or loose-boulder structure across a stream? [**catchment**]
- Only a signboard, with no structure visible? [**unclear**, even if the board
  names the work]
- A signboard plus a visible structure? [Label the **structure**; write "board"
  in notes]
- Two structures in one photo? [Label the main one and note the other]

---

## 5. Resolving disagreements (both labellers, step 6)

1. Claude Code first reports agreement (Cohen's kappa) on the **raw** sheets.
   That figure goes in the paper as it is, before any resolution.
2. It then gives you a list of only the IDs you labelled differently, with both
   labels.
3. Sit together with `view.html`, still **without the key**. For each disputed
   ID, look again, discuss briefly and agree one final label. If you can't agree,
   the final label is `unclear`. Don't revisit IDs you already agreed on.
4. Record the result in `labels_final.csv`, with columns
   `random_id, label_A, label_B, final_label, resolution_note`, one row per photo
   (agreed rows simply copy the shared label).
5. Only after the final labels are saved does the coordinator release
   `key.csv`, and only to Claude Code.

---

## 6. What happens next (Claude Code, step 7)

Using `labels_final.csv`, the key and the protocol's rule:

- the share of each category segment labelled `storage` (and `recharge`, if the
  protocol counts it), with a confidence interval, out of 30;
- the rule applied as written in the protocol, to decide which segments enter
  the positive set;
- the positive point set built from the full MGNREGA table;
- the validation (AUC for each method) run on that set.

None of this changes the labels or the protocol. If the result looks wrong, it
is reported as it is, and any change to the rule is recorded as a deviation
from the protocol with its reason.

---

## 7. Could an AI label the photos instead?

Not as the labeller of record. The labels decide the validation set, and a
reviewer would then have to accept a model's judgement of structure types from
field photos, with no ground truth behind it. Two people with measured
agreement is the standard approach and easy to defend. An AI may be added
afterwards as a **third** labeller, for comparison only; it doesn't replace
either of you.
