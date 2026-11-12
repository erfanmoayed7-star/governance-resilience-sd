"""A1 (R2.3, R4.3, R1.4): how far the adverse-implementation result depends on its assumptions.

Each draw samples the four SC effect sizes. A mechanism is "adverse" when its
effect is drawn from its adverse range (sign reversed through the existing
equations), otherwise from its beneficial range. Outcome per draw:
dRI = RI(Full-SC) - RI(No-SC) at week 52, data-driven exposure, B1-B4 active.

Experiments
  E1  independent failures, p_adverse = 0.00 ... 0.50
  E2  correlated failures via a shared implementation-quality factor
      (Gaussian copula, correlation rho), p_adverse = 0.10, 0.25, 0.40
  E3  exactly k of 4 mechanisms fail (k = 0..4), failing set drawn at random;
      plus each single mechanism failing alone
  E4  alternative adverse-magnitude distribution: mirror of the beneficial
      range (symmetric) instead of the baseline half-size range
Reversal rate = share of draws with dRI < 0, reported with a Wilson 95% CI
and the binomial standard error. Seeds are fixed per condition.
"""
import csv
import math
import os
import sys
from itertools import combinations
from multiprocessing import Pool

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import governance_system_dynamics as g  # noqa: E402
import data_inputs as di  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "a1_adverse_sweep")
N = g.MC_N_RUNS
KEYS = list(g.SC_EFFECT_RANGES)  # vb_sc_av, ab_sc_re, ad_sc_dw, tr_sc_tp
NAMES = {"vb_sc_av": "SC_AutoVerify", "ab_sc_re": "SC_RuleExec",
         "ad_sc_dw": "SC_DisputeWF", "tr_sc_tp": "SC_Transparency"}
ADV_BASE = g.SC_EFFECT_RANGES_ADVERSE
ADV_SYM = {k: (-hi, -lo) for k, (lo, hi) in g.SC_EFFECT_RANGES.items()}

_P = _EXO = None


def _init():
    global _P, _EXO
    _P = g.get_default_params()
    _EXO, _ = di.get_data_driven_exogenous("data", t_weeks=g.DEFAULT_T_WEEKS, scale_stress=1.0)


def _drI(effects):
    p = dict(_P)
    p.update(effects)
    no = g.run_simulation(p, g.make_no_sc_policy(), "data", exogenous_override=_EXO)[2][-1]["RI"]
    sc = g.run_simulation(p, g.make_full_sc_policy(), "data", exogenous_override=_EXO)[2][-1]["RI"]
    return float(sc - no)


def draw_effects(rng, fail_mask, adv):
    return {k: float(rng.uniform(*(adv[k] if fail else g.SC_EFFECT_RANGES[k])))
            for k, fail in zip(KEYS, fail_mask)}


def masks_independent(rng, p):
    return rng.uniform(size=(N, 4)) < p


def masks_copula(rng, p, rho):
    zc = rng.standard_normal((N, 1))
    zi = math.sqrt(rho) * zc + math.sqrt(1 - rho) * rng.standard_normal((N, 4))
    return norm.cdf(zi) < p


def masks_k(rng, k):
    m = np.zeros((N, 4), bool)
    for i in range(N):
        m[i, rng.choice(4, size=k, replace=False)] = True
    return m


def stats(d):
    n, x = len(d), int(np.sum(d < 0))
    ph = x / n
    z = 1.96
    c = (ph + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return {"reversal_rate": ph, "se": math.sqrt(ph * (1 - ph) / n), "ci_lo": max(0, c - h),
            "ci_hi": min(1, c + h), "mean_dRI": float(np.mean(d)),
            "p5_dRI": float(np.percentile(d, 5)), "p95_dRI": float(np.percentile(d, 95))}


def run_condition(pool, label, seed, mask_fn, adv=ADV_BASE):
    rng = np.random.default_rng(seed)
    masks = mask_fn(rng)
    effects = [draw_effects(rng, m, adv) for m in masks]
    d = np.array(pool.map(_drI, effects, chunksize=10))
    s = stats(d)
    s.update({"condition": label, "mean_failed_mechanisms": float(masks.sum(1).mean()),
              "share_draws_ge2_failed": float((masks.sum(1) >= 2).mean())})
    print(f"{label:48s} rev={s['reversal_rate']:6.1%} (SE {s['se']*100:4.1f} pp, "
          f"CI {s['ci_lo']:.1%}-{s['ci_hi']:.1%})  mean dRI={s['mean_dRI']:+.4f}  "
          f">=2 failed={s['share_draws_ge2_failed']:.0%}", flush=True)
    return s


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    with Pool(os.cpu_count(), initializer=_init) as pool:
        print("E1 independent failures")
        for i, p in enumerate(np.round(np.arange(0, 0.501, 0.05), 2)):
            rows.append({"experiment": "E1", "p_adverse": p, "rho": 0.0,
                         **run_condition(pool, f"E1 p={p:.2f}", 1000 + i,
                                         lambda r, p=p: masks_independent(r, p))})
        print("E2 correlated failures (shared implementation quality)")
        for p in (0.10, 0.25, 0.40):
            for rho in (0.25, 0.5, 0.75, 1.0):
                rows.append({"experiment": "E2", "p_adverse": p, "rho": rho,
                             **run_condition(pool, f"E2 p={p:.2f} rho={rho:.2f}",
                                             2000 + int(p * 100) * 10 + int(rho * 4),
                                             lambda r, p=p, rho=rho: masks_copula(r, p, rho))})
        print("E3 forced joint failure")
        for k in range(5):
            rows.append({"experiment": "E3", "k_failed": k,
                         **run_condition(pool, f"E3 exactly {k} of 4 fail", 3000 + k,
                                         lambda r, k=k: masks_k(r, k))})
        for j, key in enumerate(KEYS):
            m = np.zeros(4, bool); m[j] = True
            rows.append({"experiment": "E3", "k_failed": 1, "failed": NAMES[key],
                         **run_condition(pool, f"E3 only {NAMES[key]} fails", 3100 + j,
                                         lambda r, m=m: np.tile(m, (N, 1)))})
        for a, b in combinations(range(4), 2):
            m = np.zeros(4, bool); m[[a, b]] = True
            lab = f"{NAMES[KEYS[a]]}+{NAMES[KEYS[b]]}"
            rows.append({"experiment": "E3", "k_failed": 2, "failed": lab,
                         **run_condition(pool, f"E3 only {lab} fail", 3200 + a * 4 + b,
                                         lambda r, m=m: np.tile(m, (N, 1)))})
        print("E4 symmetric adverse magnitudes")
        for i, p in enumerate((0.10, 0.25, 0.40)):
            rows.append({"experiment": "E4", "p_adverse": p, "rho": 0.0,
                         **run_condition(pool, f"E4 symmetric p={p:.2f}", 4000 + i,
                                         lambda r, p=p: masks_independent(r, p), ADV_SYM)})

    cols = ["experiment", "condition", "p_adverse", "rho", "k_failed", "failed", "reversal_rate",
            "se", "ci_lo", "ci_hi", "mean_dRI", "p5_dRI", "p95_dRI",
            "mean_failed_mechanisms", "share_draws_ge2_failed"]
    with open(os.path.join(OUT, "a1_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})


if __name__ == "__main__":
    main()
