"""Agreement page: how the map relates to recorded works, with every caveat."""
import streamlit as st

from ahp import SCENARIOS
from algorithms import ALGORITHMS
from utils import structures as STR
from utils import ui

result = ui.require_result()
active = ui.active()

ui.section("Agreement with recorded works", "fact_check",
           f'<span style="font-size:0.75rem; color:#7d8590;"> · {result.get("algorithm", "")} '
           f'· {st.session_state.get("scenario", "")}</span>')

enrich = ui.works_enrichment(result)

# ─── Caveats first ───────────────────────────────────────────────────────────
confirmed = STR.load_confirmed()
n_strict = sum(c["rule"] == "strict" for c in confirmed)
lines = []
if enrich:
    lines.append(
        "These are category codes, not verified structures: the photo audit found "
        "about 17–50% of them show a harvesting structure. Most works sit on cropland, "
        "which the model also favours, so part of this agreement comes from land "
        "cover alone. Agreement with existing practice, not an accuracy measure.")
lines.append("**MGNREGA water works:** Unverified: category code only. The photo audit "
             "found most works in these categories are not structures.")
if confirmed:
    lines.append(f"**Photo-confirmed structures** ({n_strict} strict · "
                 f"{len(confirmed) - n_strict} lenient): strict means both labellers: "
                 "harvesting structure. Lenient means one labeller of two: harvesting "
                 "structure.")
lines.append(f"**Gold stars on the map:** Within the site's "
             f"{int(STR.OVERLAP_KM * 1000)} m circle. Agreement with where works were "
             "built, not proof of accuracy.")
st.info("\n\n".join(lines), icon=":material/info:")

# ─── Works in High zones ─────────────────────────────────────────────────────
if enrich:
    h = enrich["High"]
    works_col, area_col, ratio_col = st.columns(3)
    with works_col:
        st.metric("Works in High zones", f"{h['points_pct']:.1f}%")
        st.caption(f"All {enrich['n']:,} existing MGNREGA water works (WC/WH) in the "
                   f"scored area")
    with area_col:
        st.metric("District in High zones", f"{h['area_pct']:.2f}%")
        st.caption("Share of the district's area")
    with ratio_col:
        st.metric("High-zone ratio", f"{h['ratio']:.2f}×")
        st.caption("Works share against the area share")
    # The paper's figure describes this view only, so elsewhere it would mislead.
    if (active["scenario"], active["algorithm"]) == (list(SCENARIOS)[0], list(ALGORITHMS)[0]) \
            and not ui.matrix_is_edited():
        st.caption(f"Computed on all {enrich['n']:,} works in the scored area; the paper's "
                   f"1.93× uses 3,119 works thinned to one per neighbourhood.")

st.page_link("views/map.py", label="See these layers on the map",
             icon=":material/map:")
