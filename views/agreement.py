"""Agreement page: how the map relates to recorded works, with every caveat."""
import streamlit as st

from utils import structures as STR
from utils import ui

result = ui.require_result()

ui.section("Agreement with recorded works", "fact_check",
           f'<span style="font-size:0.75rem; color:#7d8590;"> · {result.get("algorithm", "")} '
           f'· {st.session_state.get("scenario", "")}</span>')

enrich = ui.works_enrichment(result)
if enrich:
    h = enrich["High"]
    st.caption(
        f"Existing MGNREGA water works (WC/WH, {enrich['n']:,} in the scored area): "
        f"{h['points_pct']:.1f}% lie in High zones, which cover {h['area_pct']:.2f}% "
        f"of the district ({h['ratio']:.2f}× the area share). These are category "
        f"codes, not verified structures: the photo audit found about 17–49% of "
        f"them show a harvesting structure. Most works sit on cropland, which "
        f"the model also favours, so part of this agreement comes from land "
        f"cover alone. Agreement with existing practice, not an accuracy measure.")

confirmed = STR.load_confirmed()
n_strict = sum(c["rule"] == "strict" for c in confirmed)
lines = ["**MGNREGA water works:** Unverified: category code only. The photo audit "
         "found most works in these categories are not structures."]
if confirmed:
    lines.append(f"**Photo-confirmed structures** ({n_strict} strict · "
                 f"{len(confirmed) - n_strict} lenient): strict means both labellers: "
                 "harvesting structure. Lenient means one labeller of two: harvesting "
                 "structure.")
lines.append(f"**Gold stars on the map:** Within the site's "
             f"{int(STR.OVERLAP_KM * 1000)} m circle. Agreement with where works were "
             "built, not proof of accuracy.")
for line in lines:
    st.markdown(f"• {line}")

st.page_link("views/map.py", label="See these layers on the map",
             icon=":material/map:")
