"""
consensus.py
────────────
Which candidate sites survive when the method changes?

Every suitability map in this project rests on choices — how criteria are
weighted (scenario) and how they are aggregated (algorithm). A site chosen by
one configuration might be an artefact of that configuration. A site chosen by
*all* of them is not.

Three views, over two independent axes:

    axis        ALGORITHMS  AHP/Fuzzy-AHP x WLC/TOPSIS, weighting held fixed
                SCENARIOS   the weighting presets, algorithm held fixed

    view        sites       candidate locations, with how many variants picked
                            each, plus a Borda-aggregated consensus ranking
                agreement   per-pixel count of variants classing it High (0..N)

Why this matters while validation is blocked: consensus is **method-agnostic
robustness evidence that needs no ground truth.** "Selected independently by all
four methods" is a claim the project can make today. "More accurate than TOPSIS"
is not, and will not be until known structures exist to score against.
"""

from __future__ import annotations

import numpy as np

DEFAULT_MATCH_KM = 2.0     # inside the 5 km minimum separation, so never ambiguous
DEFAULT_TOP_N = 25


# ─────────────────────────────────────────────────────────────────────────────
# Building the variant sets
# ─────────────────────────────────────────────────────────────────────────────

def variants_by_algorithm(stack: dict, matrix=None, scenario: str | None = None,
                          top_n: int = DEFAULT_TOP_N) -> dict[str, dict]:
    """Score the stack with every algorithm, holding the weighting matrix fixed."""
    from ahp import ahp_engine
    from algorithms import ALGORITHMS, weights_for_algorithm
    from gis_analysis import score_stack

    if matrix is None:
        matrix = (ahp_engine.matrix_for_scenario(scenario) if scenario
                  else ahp_engine.matrix)

    out = {}
    for name in ALGORITHMS:
        weights, aggregator, _label = weights_for_algorithm(
            name, matrix, ahp_engine.criteria)
        out[name] = score_stack(stack, weights, aggregator=aggregator,
                                algorithm=name, top_n=top_n)
    return out


def variants_by_scenario(stack: dict, algorithm: str = "AHP + WLC",
                         top_n: int = DEFAULT_TOP_N) -> dict[str, dict]:
    """Score the stack with every scenario, holding the algorithm fixed."""
    from ahp import ahp_engine, SCENARIOS
    from algorithms import weights_for_algorithm
    from gis_analysis import score_stack

    out = {}
    for name in SCENARIOS:
        matrix = ahp_engine.matrix_for_scenario(name)
        weights, aggregator, _label = weights_for_algorithm(
            algorithm, matrix, ahp_engine.criteria)
        _w, cr = ahp_engine.calculate_weights(matrix)
        out[name] = score_stack(stack, weights, cr, aggregator=aggregator,
                                algorithm=f"{algorithm} / {name}", top_n=top_n)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Consensus sites + Borda aggregation
# ─────────────────────────────────────────────────────────────────────────────

def _haversine_km(lon1, lat1, lon2, lat2) -> float:
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return float(6371.0 * 2 * np.arcsin(np.sqrt(a)))


def consensus_sites(variants: dict[str, dict], match_km: float = DEFAULT_MATCH_KM,
                    top_n: int = DEFAULT_TOP_N) -> list[dict]:
    """Cluster candidate sites across variants and score them by agreement.

    Sites are matched by **position, not rank** — each variant extracts its
    candidates independently, so the same location shifts by a pixel or two
    between runs. The 2 km tolerance sits well inside the 5 km minimum
    separation enforced within a single run, so a cluster can never absorb two
    distinct sites from the same variant.

    **Borda count.** Within one variant a site at rank r of N scores N - r + 1
    points; a site that variant did not select scores 0. Summing across variants
    rewards locations that several methods rank highly, which is the consensus
    notion wanted here. The zero for non-selection is deliberate — a method
    staying silent about a site is not evidence in its favour.
    """
    n_variants = len(variants)
    if n_variants == 0:
        return []

    entries = []
    for label, result in variants.items():
        sites = (result.get("top_locations_details") or [])[:top_n]
        n = len(sites)
        for s in sites:
            entries.append({
                "variant": label,
                "lon": float(s["lon"]), "lat": float(s["lat"]),
                "score": float(s["suitability_score"]),
                "rank": int(s["rank"]),
                "borda": n - int(s["rank"]) + 1,
                "raw": s.get("raw_values", {}),
            })

    # Greedy clustering, strongest site first so cluster centres are the good ones.
    entries.sort(key=lambda e: -e["score"])
    clusters: list[dict] = []
    for e in entries:
        home = None
        for c in clusters:
            if e["variant"] in c["by_variant"]:
                continue                      # one site per variant per cluster
            if _haversine_km(e["lon"], e["lat"], c["lon"], c["lat"]) <= match_km:
                home = c
                break
        if home is None:
            clusters.append({
                "lon": e["lon"], "lat": e["lat"],
                "by_variant": {e["variant"]: e},
                "raw": e["raw"],
            })
        else:
            home["by_variant"][e["variant"]] = e

    out = []
    for c in clusters:
        members = list(c["by_variant"].values())
        scores = [m["score"] for m in members]
        ranks = [m["rank"] for m in members]
        out.append({
            "lon": round(c["lon"], 5), "lat": round(c["lat"], 5),
            "n_variants": len(members),
            "n_possible": n_variants,
            "unanimous": len(members) == n_variants,
            "variants": sorted(c["by_variant"].keys()),
            "best_score": round(max(scores), 3),
            "mean_score": round(float(np.mean(scores)), 3),
            "best_rank": min(ranks),
            "mean_rank": round(float(np.mean(ranks)), 1),
            "borda": sum(m["borda"] for m in members),
            "raw_values": c["raw"],
        })

    # Consensus ranking: Borda first, agreement count as tie-break, then score.
    out.sort(key=lambda d: (-d["borda"], -d["n_variants"], -d["best_score"]))
    for i, d in enumerate(out, start=1):
        d["consensus_rank"] = i
    return out


# ─────────────────────────────────────────────────────────────────────────────
# Agreement raster
# ─────────────────────────────────────────────────────────────────────────────

def agreement_raster(variants: dict[str, dict], district_mask=None):
    """Per-pixel count of variants that class the pixel as High suitability."""
    layers = [v["classified_raster"] for v in variants.values()
              if v.get("classified_raster") is not None]
    if not layers:
        return None
    count = np.zeros(layers[0].shape, dtype=np.float32)
    for cl in layers:
        count += (cl == 3).astype(np.float32)
    if district_mask is not None:
        count[~district_mask] = np.nan
    return count


def agreement_stats(count, district_mask, transform, shape) -> dict:
    """Area and share of the district at each agreement level."""
    from gis_analysis import _pixel_area_km2_per_row

    px = _pixel_area_km2_per_row(transform, shape)
    area = np.repeat(px[:, None], shape[1], axis=1)
    valid = ~np.isnan(count)
    total = float(area[valid].sum())

    levels = {}
    n_max = int(np.nanmax(count)) if valid.any() else 0
    for k in range(n_max + 1):
        sel = valid & (count == k)
        km2 = float(area[sel].sum())
        levels[k] = {"area_km2": round(km2, 1),
                     "percent": round(100.0 * km2 / total, 2) if total else 0.0}
    return {"total_km2": round(total, 1), "levels": levels, "n_variants": n_max}


def agreement_png(count, n_variants: int, boundary_gdf, transform,
                  title: str, dpi: int = 150) -> bytes:
    """Agreement map as a PNG, for the report."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, BoundaryNorm

    h, w = count.shape
    extent = (transform.c, transform.c + w * transform.a,
              transform.f + h * transform.e, transform.f)

    shades = ["#f7f7f7", "#dbe9d3", "#a8cf99", "#5fa14b", "#2c6b1f", "#123d0c"]
    cmap = ListedColormap(shades[:n_variants + 1])
    norm = BoundaryNorm(np.arange(-0.5, n_variants + 1.5, 1), cmap.N)

    fig, ax = plt.subplots(figsize=(9, 9))
    im = ax.imshow(count, extent=extent, cmap=cmap, norm=norm, origin="upper")
    if boundary_gdf is not None and len(boundary_gdf):
        boundary_gdf.boundary.plot(ax=ax, color="black", linewidth=1.0)
    cbar = fig.colorbar(im, ax=ax, shrink=0.8, ticks=range(n_variants + 1))
    cbar.set_label(f"variants classing the pixel High (0-{n_variants})")
    ax.set_title(title, fontsize=12, fontweight="bold")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, dpi=dpi, format="png")
    plt.close(fig)
    return buf.getvalue()


def consensus_report(stack: dict, axis: str = "algorithms", **kwargs) -> dict:
    """Full consensus view for one axis: 'algorithms' or 'scenarios'."""
    if axis == "algorithms":
        variants = variants_by_algorithm(stack, scenario=kwargs.get("scenario"))
    elif axis == "scenarios":
        variants = variants_by_scenario(
            stack, algorithm=kwargs.get("algorithm", "AHP + WLC"))
    else:
        raise ValueError("axis must be 'algorithms' or 'scenarios'")

    count = agreement_raster(variants, stack["district_mask"])
    sites = consensus_sites(variants)
    stats = (agreement_stats(count, stack["district_mask"], stack["transform"],
                             stack["shape"]) if count is not None else {})

    return {"axis": axis, "variants": list(variants), "results": variants,
            "sites": sites, "agreement": count, "agreement_stats": stats}


def consensus_csv(rep: dict) -> bytes:
    """Consensus site table as CSV."""
    import pandas as pd

    rows = []
    for s in rep["sites"]:
        raw = s.get("raw_values", {}) or {}
        rows.append({
            "consensus_rank": s["consensus_rank"],
            "longitude": s["lon"], "latitude": s["lat"],
            "variants_selecting": s["n_variants"],
            "of_possible": s["n_possible"],
            "unanimous": s["unanimous"],
            "borda_score": s["borda"],
            "best_score": s["best_score"], "mean_score": s["mean_score"],
            "best_rank": s["best_rank"], "mean_rank": s["mean_rank"],
            "selected_by": "; ".join(s["variants"]),
            "slope_deg": raw.get("slope_deg"),
            "soil_class": raw.get("soil_class"),
            "lulc_class": raw.get("lulc_class"),
            "drainage_density": raw.get("drainage_density"),
            "settlement_km": raw.get("settlement_km"),
        })
    header = (f"# consensus across {len(rep['variants'])} {rep['axis']}\n"
              f"# variants: {'; '.join(rep['variants'])}\n")
    if not rows:
        return header.encode("utf-8")
    return (header + pd.DataFrame(rows).to_csv(index=False)).encode("utf-8")


def _print_report(rep: dict) -> None:
    n = len(rep["variants"])
    print(f"\n=== consensus across {n} {rep['axis']} ===")
    for v in rep["variants"]:
        print(f"    - {v}")

    sites = rep["sites"]
    unanimous = [s for s in sites if s["unanimous"]]
    print(f"\n{len(sites)} distinct locations proposed; "
          f"{len(unanimous)} selected by all {n}")

    print(f"\n{'rank':>4} {'lon':>9} {'lat':>9} {'picked':>8} {'borda':>6} "
          f"{'best':>6} {'mean rank':>10}")
    for s in sites[:15]:
        print(f"{s['consensus_rank']:>4} {s['lon']:>9.4f} {s['lat']:>9.4f} "
              f"{s['n_variants']:>5}/{s['n_possible']:<2} {s['borda']:>6} "
              f"{s['best_score']:>6.3f} {s['mean_rank']:>10.1f}")

    st = rep.get("agreement_stats") or {}
    if st:
        print(f"\nagreement raster over {st['total_km2']:,.0f} km2:")
        for k, v in sorted(st["levels"].items(), reverse=True):
            print(f"    {k}/{n} variants High : {v['percent']:>5.2f}%  "
                  f"{v['area_km2']:>8,.1f} km2")


def write_outputs(rep: dict, outdir: str = "outputs") -> list[str]:
    """Write the consensus table and agreement map for one axis."""
    import os

    os.makedirs(outdir, exist_ok=True)
    axis = rep["axis"]
    written = []

    csv_path = os.path.join(outdir, f"consensus_{axis}.csv")
    with open(csv_path, "wb") as fh:
        fh.write(consensus_csv(rep))
    written.append(csv_path)

    if rep.get("agreement") is not None:
        first = next(iter(rep["results"].values()))
        png = agreement_png(rep["agreement"], len(rep["variants"]),
                            first.get("boundary_gdf"),
                            first["suitability_transform"],
                            f"Agreement across {len(rep['variants'])} {axis} - Chandrapur")
        png_path = os.path.join(outdir, f"agreement_{axis}.png")
        with open(png_path, "wb") as fh:
            fh.write(png)
        written.append(png_path)
    return written


if __name__ == "__main__":
    import argparse
    import os

    from gis_analysis import build_criteria_stack

    ap = argparse.ArgumentParser(description="Consensus across method variations.")
    ap.add_argument("--write", action="store_true",
                    help="also write CSV + agreement PNG to outputs/")
    ap.add_argument("--data-dir", default="data")
    args = ap.parse_args()

    stack = build_criteria_stack(args.data_dir)
    for axis in ("algorithms", "scenarios"):
        rep = consensus_report(stack, axis=axis)
        _print_report(rep)
        if args.write:
            for path in write_outputs(rep):
                print(f"    wrote {path}  ({os.path.getsize(path):,} B)")
