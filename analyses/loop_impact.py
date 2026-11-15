"""Isolated loop impact: which feedback loops matter most for resilience.

Each loop is deactivated by cutting one causal link that belongs to that loop
only, and the model is re-run under data-driven exposure:
  R1 trust erosion        AD -> TR      tr_ad   = 0
  R2 friction-buffer      AD -> PF      pf_ad   = 0
  B1 liquidity recovery   PEE -> CB     cb_pee  = 0
  B2 friction relief      PEE -> PF     pf_pee  = 0
  B3 trust restoration    RME -> TR     k_rme   = 0
  B4 governance redesign  GRE -> AD     k_gre   = 0
Loop contribution = mean RI with the loop - mean RI with the loop cut
(negative for loops that amplify the disturbance, positive for loops that
dampen it), under No-SC and Full-SC.
"""
import csv
import os

import numpy as np

from metrics import g, data_exogenous, HERE

OUT = os.path.join(HERE, "..", "results", "loop_impact")
LOOPS = [("R1", "Trust erosion (R1)", {"tr_ad": 0.0}),
         ("R2", "Friction-buffer spiral (R2)", {"pf_ad": 0.0}),
         ("B1", "Liquidity recovery (B1)", {"cb_pee": 0.0}),
         ("B2", "Friction relief (B2)", {"pf_pee": 0.0}),
         ("B3", "Trust restoration (B3)", {"k_rme": 0.0}),
         ("B4", "Governance redesign (B4)", {"k_gre": 0.0})]


def series(p, pol, exo):
    out = g.run_simulation(p, pol, "data", exogenous_override=exo)[2]
    return np.array([o["RI"] for o in out])


def main():
    os.makedirs(OUT, exist_ok=True)
    exo = data_exogenous()
    base = g.get_default_params()
    rows, traj = [], {}
    for pname, pol in [("No-SC", g.make_no_sc_policy()), ("Full-SC", g.make_full_sc_policy())]:
        full = series(base, pol, exo)
        traj[(pname, "all")] = full
        for code, label, cut in LOOPS:
            s = series({**base, **cut}, pol, exo)
            traj[(pname, code)] = s
            rows.append({"policy": pname, "loop": code, "label": label,
                         "contribution_mean_RI": float(full.mean() - s.mean()),
                         "contribution_terminal_RI": float(full[-1] - s[-1])})
    with open(os.path.join(OUT, "loop_impact.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(f"{r['policy']:8s} {r['label']:28s} mean {r['contribution_mean_RI']:+.4f}  terminal {r['contribution_terminal_RI']:+.4f}")
    np.save(os.path.join(OUT, "traj.npy"), {f"{k[0]}|{k[1]}": v for k, v in traj.items()}, allow_pickle=True)


if __name__ == "__main__":
    main()
