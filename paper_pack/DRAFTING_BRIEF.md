# Drafting brief — RWH GIS-MCDA paper, draft v4

**You are revising a journal manuscript.** Draft v3 (attached, as `.tex` or PDF)
was written before a data correction changed almost every result. Produce draft
v4: the same paper and structure, with every number, table, claim and caption
brought up to date, and with the new results added. **No validation results
exist yet. Do not invent any.**

Read this file first. It tells you what each attachment is and which one wins
when two disagree.

---

## 1. The attachments, in order of authority

| File | What it is | How to use it |
|---|---|---|
| `PAPER_NUMBERS.txt` | Live output of the analysis code (`tools/paper_figures.py`), 4 Oct 2026 | **Highest authority for any number.** If anything else disagrees with it, it wins |
| `FIGURE_DATA.md` | Every value plotted in the 17 generated figures, plus each figure's **final caption** | Use these captions (edited to the paper's voice) and these numbers |
| `figures/fig*.png` | The 17 generated figures, final | Look at them; captions must describe what is drawn |
| `PAPER_REVISIONS.md` | A section-by-section edit list against v3: what each passage says now and what it should say, with all the replacement tables | **Your main work list.** Apply all of §2, add the material in §3, never use the values in §4 |
| `SOIL_LEGEND_CORRECTION.md` | The record of the data correction behind all the changes | Use it for the Limitations and Methods wording on soil |
| v3 manuscript | The current text | Keep its structure, voice and argument wherever the edit list doesn't change them |

If a number appears in v3 but in none of the first four files, **don't keep it
silently.** List it under "Unverified numbers" in your change log (§6).

---

## 2. What changed, in one paragraph

Soil code 4, which covers 77.8% of Chandrapur, had been read as Silt Loam and
scored 1.00. It is in fact Clay Loam, scoring 0.60. Codes 1 and 7 were also
mislabelled. With the legend corrected, the High class falls from 18.51% to
**6.44%**, and the shortlist now spans three soil textures. Several of v3's
central claims reverse:

- **Aggregation versus weighting.** On area the two effects are now similar
  (−0.957 against −0.560 pp, ratio 1.7, not 11.6). On the **shortlist**,
  aggregation replaces half of it (TOPSIS keeps 5/10) and weighting replaces
  none (Fuzzy-AHP keeps 10/10).
- **Drainage.** It no longer dominates. Soil is first under ±20% perturbation;
  removing rainfall leaves 0/10 of the top sites.
- **Scenarios.** "Maximise recharge" now **lowers** the High share. Four of the
  five scenarios pick the same top site.
- **"Effective weight"** is now two separate measures: **level contribution**
  and **variance share** (Pratt index).

## 3. The new storyline: put it in the Abstract, §1.4, §5 and §6

1. **Analyst decisions dominate algorithm choice.** On one surface:
   - rainfall scoring moves the High share by +31.21 pp;
   - the classification cutoff scheme by 36.43 pp (a range over four schemes);
   - the weighting judgements by 16.23 pp (a range over five scenarios);
   - the soil-legend data error by −12.07 pp;
   - while aggregation moves it by −0.957 pp and the weighting method by
     −0.560 pp. (Fig. 12)
2. **The one large algorithm effect is a cutoff effect.** WLC → TOPSIS moves the
   Low share by +9.03 pp. Matching the class sizes removes that shift, and doing
   so takes a 0.050 move of the lower cutoff against 0.005 for the upper one.
   Of the area that changes class, **50.3%** changes under **both** cutoff
   schemes tested. (Fig. 21)
3. **Method disagreement is confined to a narrow score band**, 0.817–0.889 around
   the 0.85 breakpoint. 22 of the 25 sites are unanimous, and the three that
   aren't are ranks 23–25. (Fig. 22)
4. **The shortlist rests on a scarce soil class.** Four of the top 5 sites sit on
   Loam, which covers 0.38% of the district. Rescoring Loam from 1.00 to 0.80
   keeps 2/5 of the top 5 and 6/10 of the top 10, while the High share barely
   moves (6.44 → 6.40%). (PAPER_REVISIONS §0.1)

Put points 1–3 in a **new §5.3.5, "Breakpoints and analyst decisions"**, and
point 4 in a **new §5.8.6** (or in §5.11).

---

## 4. Structure and figures

- Keep v3's section order. Add §5.3.5 and §5.8.6 as above.
- **Figure numbering:** follow the mapping table in `PAPER_REVISIONS.md` §1.
  Generated figures 12, 21 and 22 have no slot in v3: place them in §5.3.5 and
  renumber everything after them consistently.
- **Figures not yet made** (QGIS or drawing tool): study area (v3 Fig 1),
  preprocessing chain (3), architecture (4), baseline map (7), hydrological
  surfaces (18), and field workflow (20). Keep them as boxed placeholders with
  `[To be prepared.]`, and update their captions to current numbers.
  - The workflow figure's consensus box reads "15 sites picked by all 4 methods,
    528.5 km²". **Not** "15 unanimous sites": that is a different quantity from
    Fig. 22's 22 of 25.
  - v3's Fig 15(c) is **dropped**. Put the top-site-per-scenario result in
    Table 15 and the text.
- Tables 12 and 13 were empty in v3. They are now filled (PAPER_REVISIONS §0.2,
  §0.3). For Table 12, use Pearson r and say why: soil and land cover have so few
  distinct values that rank correlations are unreliable. For Table 13, say the
  fixed rainfall bands were defined for this comparison and do not come from a
  published classification.

---

## 5. Rules — a reviewer will check these

**Numbers**
- Every number comes from the attachments. Never compute a new number from
  rounded ones.
- Rounding is half-up, applied **once**, to an unrounded value. These four are
  the double-rounding traps:

  | Quantity | Correct | Not |
  |---|---|---|
  | Rainfall weight | 42.8% (42.85% at 2 dp) | 42.9% |
  | Rainfall level share | 36.9% | 37.0% |
  | Soil variance share | 9.7% | 9.8% |
  | Soil variance ratio | 0.63× | 0.64× |

- Class shares are **area-weighted** (say so once in Methods). Use 87.17%
  unchanged, not 87.16%.
- The classes are **Low ≤ 0.65, Medium, High > 0.85**, with those signs everywhere.
- The interaction uses the standard factorial convention,
  ½(Δ_agg^fuzzy − Δ_agg^crisp) = **−0.162 pp**. Fix v3's Equation 12 sign to match.
- 973 tied cells and 18.51% are **historical reconstructions** on the superseded
  legend. Mention them only as that.

**Wording**
- "under **both** cutoff schemes tested", never "any".
- Consensus categories are never / minority / **half or more** / unanimous, not
  "majority".
- The baseline scenario is "Baseline (rainfall-led)", not "(balanced)".
- Sensitivity analyses are "complementary", not "independent" and not
  "converging".
- Say "level contribution" or "variance share", never just "effective weight".

**Placeholders the authors must fill (leave them visible in the text)**
- **The soil-texture ordering, cited to two free sources, both checked.**
  - USDA TR-55 [28], already in the reference list. Appendix A, p. A-1, table
    under "Disturbed soil profiles": B = silt loam or loam; C = sandy clay loam;
    D = clay loam, silty clay loam, sandy clay, silty clay or clay. (TR-55 gives
    this texture-based assignment for profiles whose survey classification no
    longer applies, so cite it as "texture-based hydrologic soil group".)
  - New reference: C. Brouwer, K. Prins, M. Kay and M. Heibloem, *Irrigation
    Water Management: Training Manual No. 5 – Irrigation Methods*, FAO, Rome,
    1988. Annex 2, Table 7, "Basic infiltration rates for various soil types":
    loam 10–20, clay loam 5–10, clay 1–5 mm/h. Authors confirmed from the title page (provisional edition). `[VERIFY: year; the title page shows none, 1988 is the usual citation
    ]`.
  - Keep the two kinds of evidence separate: hydrologic groups come from TR-55,
    the mm/h rates from FAO. FAO has no Sandy Clay Loam row, and TR-55 puts
    Clay Loam and Clay in the same group.
  - Add this sentence to §4.2: "Texture scores follow the ordering of the four
    classes present in two sources: the texture-based hydrologic soil groups of
    USDA TR-55 [28, Appendix A], which place Loam in group B, Sandy Clay Loam
    in group C, and Clay Loam and Clay in group D; and FAO basic infiltration
    rates [FAO, Annex 2, Table 7], which rank Loam (10–20 mm/h) above Clay Loam
    (5–10 mm/h) and Clay (1–5 mm/h). Neither source prescribes score values;
    these are a modelling judgement, and their influence on the shortlist is
    tested in Section 5.8.6."
  - **Do not cite** Rawls et al. 1982 (inaccessible) or FAO Training Manual
    No. 1 (it has no such table).
- **Table 2** (criterion frequency across the eight studies): the "8 of 8" counts
  are **not yet verified** against the papers. Keep the table and add
  `[VERIFY: eight-paper coding pending]`.
- Author names, ORCIDs, funding statement, repository URL or DOI, and the target
  journal: keep them as placeholders.

**Style**
- British spelling, as in v3 ("normalisation", "colour").
- If you write LaTeX, plain ASCII only: no em dashes (use `--` or reword), no
  curly quotes, and LaTeX commands for special characters (`$^\circ$`,
  `km$^2$`).
- Keep v3's measured, non-promotional tone. No new claims beyond the attachments.

---

## 6. Validation status: what to say, and what not to

Validation has **not** been run. Keep "no accuracy metric is reported" in the
Abstract and Conclusion. Update the Limitations (§5.11) and Future scope (§5.12)
with what now exists:

- **A validation source has been identified and pulled:** Bhuvan Bhugram MGNREGA
  accepted geotags for Chandrapur.
  - 82,289 geotag records across all 15 blocks.
  - Phase I (works started before November 2017, tagged retrospectively) and
    Phase II (geotagged at completion).
  - 99.2% of the points fall inside the district boundary.
  - Reported GPS accuracy is at most 20 m (median 4 m).
- **Records carry only a work-category code**, not a structure type. Which codes
  count as harvesting structures is being decided by a **blinded two-labeller
  photo audit**: 240 geotag photos, 30 per code, with the protocol fixed before
  labelling and agreement measured by Cohen's kappa. Only then will the AUC for
  each method be computed.
- The caveats belong in the text now:
  - the data are presence-only;
  - structures sit where people chose to build, which reflects land access and
    budgets as well as suitability;
  - several geotags can belong to one work.

**Do not** report or imply an AUC, a hit rate, a share of structures in High,
or any comparison of methods against reality.

---

## 7. What to hand back

Work section by section; the paper is long. Start with the Abstract and §1,
then §4, §5, §6 and the Declarations, then the captions. For each section give:

1. **The revised text**, in LaTeX if the `.tex` was attached, otherwise in the
   same structure as the PDF.
2. **A change log:** every number you changed (old → new → source file), every
   claim you reversed or removed, and every placeholder you left.
3. **Unverified numbers:** anything kept from v3 that you couldn't trace to an
   attachment.

When unsure, choose the conservative wording and flag it in the change log.
Don't guess.
