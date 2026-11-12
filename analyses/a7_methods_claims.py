"""A7: run the two analyses the round-2 Methods describe (paragraphs 89 and 91).

Part 1. Joint Monte Carlo over 8 parameters: the four SC effect sizes (MC
ranges) and four stakeholder-loop gains, one per loop, at their disclosed
ranges: cb_pee (B1, payment effort -> cash buffer), pf_pee (B2, payment
effort -> payment friction), k_rme (B3, relationship management effort) and
k_gre (B4, governance redesign effort). N = 300, seed 42, uniform sampling.

Part 2. Second rival specification: smart contracts also reduce COI directly,
bypassing the governance stocks, at strength s (sweep). Reports the SC gain
relative to the base specification.

Scenario: data-driven exposure. Measure: horizon-mean RI (primary), terminal
RI at week 52 (secondary).
"""
import csv
import os

import numpy as np

from metrics import g, data_exogenous, ri_measures, HERE

OUT = os.path.join(HERE, "..", "results", "a7_methods_claims")
LOOP_PARAMS = {"cb_pee": g.STAKEHOLDER_LOOP_PARAM_RANGES["cb_pee"][1:3],
               "pf_pee": g.STAKEHOLDER_LOOP_PARAM_RANGES["pf_pee"][1:3],
               "k_rme": g.STAKEHOLDER_LOOP_PARAM_RANGES["k_rme"][1:3],
               "k_gre": g.B4_PARAM_RANGES["k_gre"][1:3]}


def gain(p, exo):
    no = ri_measures(p, g.make_no_sc_policy(), exo)
    full = ri_measures({**p, "sc_direct_level": 1.0}, g.make_full_sc_policy(), exo)
    return {m: full[m] - no[m] for m in ("mean", "terminal")}


def main():
    os.makedirs(OUT, exist_ok=True)
    exo = data_exogenous()
    base = g.get_default_params()

    rng = np.random.default_rng(g.MC_SEED)
    rows = []
    for _ in range(g.MC_N_RUNS):
        p = dict(base)
        for k, (lo, hi) in {**g.SC_EFFECT_RANGES, **LOOP_PARAMS}.items():
            p[k] = float(rng.uniform(lo, hi))
        d = gain(p, exo)
        rows.append({**{k: p[k] for k in {**g.SC_EFFECT_RANGES, **LOOP_PARAMS}},
                     "dRI_mean": d["mean"], "dRI_terminal": d["terminal"]})
    with open(os.path.join(OUT, "mc_joint8.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for m in ("mean", "terminal"):
        x = np.array([r[f"dRI_{m}"] for r in rows])
        print(f"Joint 8-parameter MC ({m}): dRI mean {x.mean():+.4f}, median {np.median(x):+.4f}, "
              f"5th {np.percentile(x, 5):+.4f}, 95th {np.percentile(x, 95):+.4f}, reversals {np.mean(x < 0):.1%}")
    half = [np.array([r["dRI_mean"] for r in rows[:n]]).mean() for n in (100, 200, 300)]
    print(f"Convergence of MC mean (horizon-mean dRI) at N = 100/200/300: "
          f"{half[0]:+.4f} / {half[1]:+.4f} / {half[2]:+.4f}")

    b = gain(base, exo)
    out = []
    print(f"\nSecond rival spec (direct SC -> COI). Base-spec gain: mean {b['mean']:+.4f}, terminal {b['terminal']:+.4f}")
    for s in (0.01, 0.02, 0.03, 0.05):
        d = gain({**base, "alt2_spec_active": 1.0, "sc_coi_direct": s}, exo)
        r = {"sc_coi_direct": s, "gain_mean": d["mean"], "gain_terminal": d["terminal"],
             "change_vs_base_pct_mean": 100 * (d["mean"] / b["mean"] - 1),
             "change_vs_base_pct_terminal": 100 * (d["terminal"] / b["terminal"] - 1)}
        out.append(r)
        print(f"  s={s:.2f}: gain mean {d['mean']:+.4f} ({r['change_vs_base_pct_mean']:+.1f}% vs base), "
              f"terminal {d['terminal']:+.4f} ({r['change_vs_base_pct_terminal']:+.1f}%)")
    with open(os.path.join(OUT, "rival2_sc_direct_coi.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main()
