"""Robustness page: sensitivity, consensus and algorithm comparison.

Each analysis runs only when its button is pressed, and its stored result survives
changing page.
"""
import pandas as pd
import streamlit as st

from ahp import ahp_engine
from algorithms import compare_algorithms
import consensus as CONS
from gis_analysis import build_criteria_stack
from sensitivity import (one_way_sensitivity, summary_sentence,
                         map_removal_sensitivity, single_parameter_sensitivity)
from utils import ui
from utils.labels import criterion_label

result = ui.require_result()
active = ui.active()
active_weights = active["weights"]
matrix = active["matrix"]

tab_sens, tab_cons, tab_algo = st.tabs(["Sensitivity", "Consensus", "Algorithm comparison"])

# ─── Sensitivity analysis ────────────────────────────────────────────────────
with tab_sens:
    ui.section("Sensitivity Analysis", "tune")
    ui.muted("Varies each weight up and down and measures how far the ranking moves. "
             "This is the answer to \"your AHP weights are subjective\".")

    ui.restore_widget("sens_delta", [10, 20, 30], 20)
    sens_col1, sens_col2 = st.columns([1, 3])
    with sens_col1:
        delta_pct = st.select_slider("Vary weights by", [10, 20, 30], key="sens_delta",
                                     format_func=lambda v: f"±{v}%",
                                     on_change=ui.remember_widget, args=("sens_delta",))
        run_sens = st.button("Run sensitivity", use_container_width=True)

    if run_sens:
        with st.spinner("Re-scoring across perturbed weights…"):
            stack = build_criteria_stack(ui.DATA_DIR)
            st.session_state["sensitivity"] = one_way_sensitivity(
                stack, active_weights, delta=delta_pct / 100.0)
            st.session_state["map_removal"] = map_removal_sensitivity(
                stack, active_weights)
            st.session_state["single_param"] = single_parameter_sensitivity(
                stack, active_weights)

    sens = st.session_state.get("sensitivity")
    if sens:
        m1, m2, m3 = st.columns(3)
        m1.metric("Top-10 retained (mean)", f"{sens['mean_retained_pct']:.0f}%")
        m2.metric("Worst case", f"{sens['worst_retained_pct']:.0f}%")
        m3.metric("Max rank shift", sens["max_rank_shift"])

        st.markdown(f"**{summary_sentence(sens)}**")

        df = pd.DataFrame(sens["runs"])[
            ["criterion", "direction", "weight_from", "weight_to",
             "retained", "max_rank_shift", "high_pct", "high_pct_delta"]]
        df.columns = ["Criterion", "Dir", "Weight from", "Weight to",
                      f"Retained /{sens['top_n']}", "Max shift", "High %", "Δ High %"]
        df["Criterion"] = df["Criterion"].map(criterion_label)
        st.dataframe(df, use_container_width=True, hide_index=True)

        st.caption(
            "Influence on highly-suitable area (mean absolute change, "
            "percentage points): "
            + " · ".join(f"{criterion_label(k)} {v:.2f}" for k, v in sens["influence_high_pct"].items()))

        mr = st.session_state.get("map_removal")
        if mr:
            st.markdown("**Map removal sensitivity** (Lodwick et al., 1990)")
            st.caption(
                "Each criterion layer is dropped entirely and the remaining "
                "weights renormalise. S index = mean |V − V′| / V × 100 over "
                "district pixels — how far the map moves when the layer is gone."
            )
            mdf = pd.DataFrame(mr["rows"])[
                ["criterion", "weight", "sensitivity_index", "max_index",
                 "mean_abs_change", "retained", "high_pct", "high_pct_delta"]]
            mdf.columns = ["Criterion", "Weight", "S index %", "Max %",
                           "Mean |ΔV|", f"Retained /{mr['top_n']}",
                           "High %", "Δ High %"]
            mdf["Criterion"] = mdf["Criterion"].map(criterion_label)
            st.dataframe(mdf, use_container_width=True, hide_index=True)

        sp = st.session_state.get("single_param")
        if sp:
            st.markdown("**Single-parameter sensitivity** (Napolitano & Fabbri, 1996)")
            st.caption(
                "Effective weight = mean of (wᵢ·rᵢ)/V × 100 — the share of the "
                "final score a criterion actually contributes, against the "
                "theoretical weight AHP assigned it. Ratio > 1 means the "
                "criterion punches above its assigned weight across the district."
            )
            # Named columns, not positional: the rows also carry unrounded
            # *_exact fields for the figures, which the table does not show.
            sdf = pd.DataFrame(sp["rows"])[
                ["criterion", "theoretical_pct", "effective_pct",
                 "effective_sd", "ratio"]]
            sdf.columns = ["Criterion", "Theoretical %", "Effective %",
                           "SD", "Ratio"]
            sdf["Criterion"] = sdf["Criterion"].map(criterion_label)
            st.dataframe(sdf, use_container_width=True, hide_index=True)

# ─── Consensus across method variations ──────────────────────────────────────
with tab_cons:
    ui.section("Consensus Sites", "handshake")
    ui.muted("Which sites survive when the method changes. A site chosen by one "
             "configuration may be an artefact of it; a site chosen by all of them "
             "is not. This is robustness evidence that needs no ground-truth data.")

    ui.restore_widget("consensus_axis", ["Algorithms", "Scenarios"], "Algorithms")
    c_axis = st.radio(
        "Vary", ["Algorithms", "Scenarios"], horizontal=True, key="consensus_axis",
        help="Algorithms: same weights, different maths. "
             "Scenarios: same maths, different weights.",
        on_change=ui.remember_widget, args=("consensus_axis",))

    if st.button("Compute consensus"):
        with st.spinner(f"Scoring every {c_axis.lower()[:-1]} variant…"):
            stack = build_criteria_stack(ui.DATA_DIR)
            axis = "algorithms" if c_axis == "Algorithms" else "scenarios"
            kw = ({"scenario": st.session_state.get("scenario")} if axis == "algorithms"
                  else {"algorithm": st.session_state.get("algorithm", "AHP + WLC")})
            st.session_state["consensus"] = CONS.consensus_report(stack, axis=axis, **kw)

    rep = st.session_state.get("consensus")
    if rep:
        n_var = len(rep["variants"])
        sites = rep["sites"]
        unanimous = [s for s in sites if s["unanimous"]]
        stats = rep.get("agreement_stats") or {}
        top_level = (stats.get("levels") or {}).get(n_var, {})

        k1, k2, k3 = st.columns(3)
        k1.metric("Locations proposed", len(sites))
        k2.metric(f"Chosen by all {n_var}", len(unanimous))
        k3.metric(f"District High in all {n_var}",
                  f"{top_level.get('percent', 0):.1f}%",
                  f"{top_level.get('area_km2', 0):,.0f} km²", delta_color="off")

        st.caption("Varied: " + " · ".join(rep["variants"]))

        rows = [{
            "Consensus rank": s["consensus_rank"],
            "Longitude": s["lon"], "Latitude": s["lat"],
            "Chosen by": f"{s['n_variants']}/{s['n_possible']}",
            "Borda": s["borda"],
            "Best score": s["best_score"],
            "Mean rank": s["mean_rank"],
            "Land cover": (s.get("raw_values") or {}).get("lulc_class", ""),
        } for s in sites[:20]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            "Ranked by Borda count: within each variant a site at rank r of N "
            "scores N−r+1, and a variant that did not select the site scores it 0. "
            "Sites are matched across variants by position (2 km), not by rank."
        )

        if rep.get("agreement") is not None:
            png = CONS.agreement_png(
                rep["agreement"], n_var, result.get("boundary_gdf"),
                result["suitability_transform"],
                f"Agreement across {n_var} {rep['axis']} — Chandrapur")
            st.image(png, use_container_width=True)
            d1, d2 = st.columns(2)
            with d1:
                st.download_button("Consensus sites (CSV)", CONS.consensus_csv(rep),
                                   f"consensus_{rep['axis']}.csv", "text/csv",
                                   use_container_width=True)
            with d2:
                st.download_button("Agreement map (PNG)", png,
                                   f"agreement_{rep['axis']}.png", "image/png",
                                   use_container_width=True)

# ─── Algorithm comparison ────────────────────────────────────────────────────
with tab_algo:
    ui.section("Algorithm Comparison", "science")
    ui.muted("Runs every algorithm on the same criteria stack, so any difference is "
             "attributable to the method alone. WLC is fully compensatory; TOPSIS "
             "penalises a site that is weak on any high-weight criterion.")

    if st.button("Compare all algorithms"):
        with st.spinner("Scoring every algorithm…"):
            stack = build_criteria_stack(ui.DATA_DIR)
            st.session_state["algo_comparison"] = compare_algorithms(
                stack, matrix, ahp_engine.criteria)

    comp = st.session_state.get("algo_comparison")
    if comp:
        rows = [{
            "Algorithm": r["algorithm"],
            "Weighting": r["weighting"],
            "Aggregation": r["aggregation"],
            "High %": r["high_pct"],
            "Mean score": r["score_mean"],
            f"Top-{comp['top_n']} shared": r["top_overlap"],
            "Surface corr": r["surface_corr"],
            "Class agreement %": r["class_agreement_pct"],
        } for r in comp["rows"]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption(
            f"Compared against **{comp['baseline']}**. 'Top-N shared' counts how many "
            f"of the baseline's top {comp['top_n']} sites the algorithm also selects "
            "(matched by position within 2 km)."
        )

        wrows = [{"Algorithm": r["algorithm"], **{criterion_label(k): v
                  for k, v in r["weights"].items()}} for r in comp["rows"]]
        st.markdown("**Weights by algorithm**")
        st.dataframe(pd.DataFrame(wrows), use_container_width=True, hide_index=True)
