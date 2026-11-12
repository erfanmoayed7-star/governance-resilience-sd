"""A3 (R2.2): smart contracts vs conventional digital workflow automation.

Conventional workflow automation (e-approval routing, document management,
checklist-based verification, shared dashboards) is represented with the same
four policy channels as the smart-contract configuration, but with lower
activation and without the two functions that require self-executing,
tamper-evident code: automated dispute workflow (SC_DisputeWF) and the shared
ledger behind SC_Transparency. Activation levels are assumptions, so a grid
over the two contested channels is reported alongside the named configurations.

Scenario: data-driven MCE/LTE (the scenario behind the paper's headline RI
values). Stakeholder loops B1-B4 are active in every arm.
"""
import csv
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import governance_system_dynamics as g  # noqa: E402
import data_inputs as di  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "a3_workflow_comparator")
os.makedirs(OUT, exist_ok=True)

# (auto_verify, rule_exec, dispute_wf, transparency)
CONFIGS = {
    "No-SC (traditional)": (0.0, 0.0, 0.0, 0.0),
    "Workflow, conservative": (0.50, 0.50, 0.00, 0.00),
    "Workflow, standard": (0.75, 0.75, 0.00, 0.25),
    "Workflow, generous": (1.00, 1.00, 0.25, 0.50),
    "Full-SC": (1.0, 1.0, 1.0, 1.0),
}


def policy(av, re, dw, tp):
    return g.make_policy(sc_rule_exec=re, sc_auto_verify=av,
                         sc_transparency=tp, sc_dispute_wf=dw)


def terminal(params, pol, exo):
    t, x, out = g.run_simulation(params, pol, "data", exogenous_override=exo)
    o = out[-1]
    return {k: float(o[k]) for k in ("RI", "COI", "AD", "TR", "VB", "AB", "SD")}


def main():
    params = g.get_default_params()
    exo, _ = di.get_data_driven_exogenous("data", t_weeks=g.DEFAULT_T_WEEKS, scale_stress=1.0)

    # 1. Named configurations
    res = {name: terminal(params, policy(*lv), exo) for name, lv in CONFIGS.items()}
    ri0, ri_sc = res["No-SC (traditional)"]["RI"], res["Full-SC"]["RI"]
    with open(os.path.join(OUT, "configs.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Config", "AV", "RE", "DW", "TP", "RI", "dRI_vs_NoSC",
                    "share_of_FullSC_gain", "AD", "TR", "COI", "SD"])
        for name, lv in CONFIGS.items():
            r = res[name]
            w.writerow([name, *lv, round(r["RI"], 5), round(r["RI"] - ri0, 5),
                        round((r["RI"] - ri0) / (ri_sc - ri0), 4),
                        round(r["AD"], 4), round(r["TR"], 4), round(r["COI"], 4), round(r["SD"], 4)])
            print(f"{name:26s} RI={r['RI']:.4f}  dRI={r['RI']-ri0:+.4f}  "
                  f"share={(r['RI']-ri0)/(ri_sc-ri0):6.1%}  AD={r['AD']:.3f} TR={r['TR']:.3f}")

    # 2. Grid: full-strength verification and routing, varying how much
    #    dispute handling and transparency conventional tools can deliver
    levels = [0.0, 0.25, 0.5, 0.75, 1.0]
    with open(os.path.join(OUT, "grid_dw_tp.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["DW_level", "TP_level", "RI", "share_of_FullSC_gain"])
        print("\nShare of Full-SC gain (rows DW, cols TP), AV=RE=1:")
        print("DW\\TP " + " ".join(f"{t:>6.2f}" for t in levels))
        for dw in levels:
            row = []
            for tp in levels:
                ri = terminal(params, policy(1, 1, dw, tp), exo)["RI"]
                s = (ri - ri0) / (ri_sc - ri0)
                row.append(s)
                w.writerow([dw, tp, round(ri, 5), round(s, 4)])
            print(f"{dw:5.2f} " + " ".join(f"{s:6.1%}" for s in row))

    # 3. Monte Carlo over the effect-size ranges: gap Full-SC minus standard workflow
    rng = np.random.default_rng(g.MC_SEED)
    gaps, wf_d, sc_d = [], [], []
    for _ in range(g.MC_N_RUNS):
        p = dict(params)
        for key, (lo, hi) in g.SC_EFFECT_RANGES.items():
            if key in p:
                p[key] = float(rng.uniform(lo, hi))
        r0 = terminal(p, policy(0, 0, 0, 0), exo)["RI"]
        rw = terminal(p, policy(*CONFIGS["Workflow, standard"]), exo)["RI"]
        rs = terminal(p, policy(1, 1, 1, 1), exo)["RI"]
        wf_d.append(rw - r0); sc_d.append(rs - r0); gaps.append(rs - rw)
    gaps, wf_d, sc_d = map(np.array, (gaps, wf_d, sc_d))
    with open(os.path.join(OUT, "mc_gap.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["dRI_workflow_standard", "dRI_fullSC", "gap_SC_minus_workflow"])
        w.writerows(zip(wf_d, sc_d, gaps))
    print(f"\nMC (N={g.MC_N_RUNS}, seed {g.MC_SEED}): workflow dRI mean {wf_d.mean():+.4f}; "
          f"Full-SC dRI mean {sc_d.mean():+.4f}; gap mean {gaps.mean():+.4f} "
          f"[5th {np.percentile(gaps,5):+.4f}, 95th {np.percentile(gaps,95):+.4f}]; "
          f"gap>0 in {np.mean(gaps>0):.0%} of draws")


if __name__ == "__main__":
    main()
