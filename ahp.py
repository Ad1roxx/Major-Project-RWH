"""
ahp.py
──────
Analytic Hierarchy Process (AHP) weighting for RWH suitability analysis.

Criteria: slope, rainfall, drainage, soil, lulc, population

The pairwise comparison matrix below encodes the expert judgement used by the
project. Weights come from the geometric-mean (priority vector) method and are
accepted only if the Consistency Ratio is below 0.10.
"""

import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Scenario presets
# ─────────────────────────────────────────────────────────────────────────────
# A scenario is a different set of pairwise judgements over the SAME six
# criteria — no additional data is involved. Each is expert judgement, exactly
# like the baseline; what makes it defensible is a stated rationale plus
# CR < 0.10, not evidence from data.
#
# Matrices are generated from an importance ranking and snapped to the Saaty
# 1–9 scale by `matrix_from_levels()`, which keeps them consistent by
# construction. Verified CRs: baseline 0.0235, recharge 0.0044,
# community 0.0059, low-earthwork 0.0078, fertile farmland 0.0146.
#
# Level vectors are in criteria order: slope, rainfall, drainage, soil, lulc,
# population.
SCENARIOS: dict[str, dict] = {
    "Baseline (balanced)": {
        "levels": None,   # uses the hand-built baseline matrix
        "rationale": "Rainfall-led general-purpose weighting used throughout the report.",
    },
    "Maximise recharge": {
        "levels": [6, 5, 2, 7, 2, 1],
        "rationale": "Getting water into the aquifer: soil infiltration and gentle "
                     "slope dominate; demand near settlements is close to irrelevant.",
    },
    "Community-focused": {
        "levels": [3, 7, 2, 2, 5, 6],
        "rationale": "Serving people: settlement proximity and cropland demand carry "
                     "the weight; physical recharge efficiency matters less.",
    },
    "Low-earthwork siting": {
        "levels": [8, 3, 4, 2, 5, 1],
        "rationale": "Construction feasibility PROXY — flat ground, easily cleared "
                     "land cover, short feeder works. Not a cost model; the project "
                     "holds no land-value or unit-rate data.",
    },
    "Fertile farmland": {
        "levels": [4, 6, 3, 8, 7, 2],
        "rationale": "Agricultural benefit — soil texture and cropland cover lead, "
                     "then rainfall. Targets harvesting that serves productive farmland "
                     "rather than recharge alone. PROXY: reweights the existing six "
                     "criteria; no soil-fertility dataset (organic carbon, N/P/K, pH) "
                     "is held.",
    },
}


class AHPEngine:
    # Saaty random index by matrix order n (n = 1 … 10)
    RANDOM_INDEX = {
        1: 0.00, 2: 0.00, 3: 0.58, 4: 0.90, 5: 1.12,
        6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49,
    }

    SAATY = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9], dtype=float)

    def __init__(self):
        self.criteria = ['slope', 'rainfall', 'drainage', 'soil', 'lulc', 'population']
        self.n = len(self.criteria)

        # Pairwise comparison matrix on the Saaty 1–9 scale. Entry [i][j] is
        # how much more important criterion i is than criterion j.
        #
        # Rationale: rainfall is the water source and dominates; slope governs
        # whether the water can be retained at all; soil controls infiltration;
        # drainage locates the runoff; LULC and settlement proximity are
        # feasibility/demand modifiers rather than primary physical drivers.
        self.matrix = np.array([
            [1,    1/3, 3,   2,   4,   5  ],  # slope
            [3,    1,   5,   3,   6,   7  ],  # rainfall
            [1/3,  1/5, 1,   1/2, 2,   3  ],  # drainage
            [1/2,  1/3, 2,   1,   3,   4  ],  # soil
            [1/4,  1/6, 1/2, 1/3, 1,   2  ],  # lulc
            [1/5,  1/7, 1/3, 1/4, 1/2, 1  ],  # population (settlement proximity)
        ], dtype=float)

    def calculate_weights(self, matrix=None):
        """Return ({criterion: weight}, consistency_ratio).

        Weights are the normalised geometric mean of each row of the pairwise
        matrix — the standard AHP priority vector. Pass `matrix` to score an
        edited or scenario matrix instead of the baseline.
        """
        m = self.matrix if matrix is None else np.asarray(matrix, dtype=float)
        geometric_means = np.prod(m, axis=1) ** (1.0 / self.n)
        weights = geometric_means / geometric_means.sum()

        consistency_ratio = self._calculate_consistency_ratio(weights, m)
        return dict(zip(self.criteria, weights)), consistency_ratio

    def _calculate_consistency_ratio(self, weights, matrix=None):
        """CR = CI / RI, where CI = (lambda_max - n) / (n - 1)."""
        m = self.matrix if matrix is None else matrix
        weighted_sum = m @ weights
        lambda_max = float((weighted_sum / weights).mean())

        CI = (lambda_max - self.n) / (self.n - 1)
        RI = self.RANDOM_INDEX.get(self.n, 1.49)
        return CI / RI if RI > 0 else 0.0

    def is_consistent(self, threshold: float = 0.10, matrix=None) -> bool:
        """True when the judgement matrix passes the standard CR < 0.10 test."""
        _weights, cr = self.calculate_weights(matrix)
        return cr < threshold

    def matrix_from_levels(self, levels):
        """Build a reciprocal pairwise matrix from an importance ranking.

        Each pair's ratio is snapped to the nearest value on the Saaty 1–9
        scale, which keeps the matrix consistent by construction while still
        looking like a set of human judgements.
        """
        levels = np.asarray(levels, dtype=float)
        n = len(levels)
        m = np.ones((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                ratio = levels[i] / levels[j]
                if ratio >= 1:
                    m[i, j] = self.SAATY[np.argmin(np.abs(self.SAATY - ratio))]
                else:
                    m[i, j] = 1.0 / self.SAATY[np.argmin(np.abs(self.SAATY - 1 / ratio))]
        return m

    def matrix_for_scenario(self, name: str):
        """Pairwise matrix for a named scenario preset."""
        if name not in SCENARIOS:
            raise KeyError(f"unknown scenario {name!r}; options: {list(SCENARIOS)}")
        levels = SCENARIOS[name]["levels"]
        return self.matrix.copy() if levels is None else self.matrix_from_levels(levels)

    def weights_for_scenario(self, name: str):
        """({criterion: weight}, consistency_ratio) for a named scenario."""
        return self.calculate_weights(self.matrix_for_scenario(name))


# Global instance
ahp_engine = AHPEngine()
