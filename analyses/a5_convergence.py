"""A5 (R4.2): do the stocks settle by week 52, i.e. are terminal values steady states?

Reports |dx/dt| for every stock at the final time, and the change in RI over
the last 4 weeks, for No-SC and Full-SC under the undisturbed baseline, the
synthetic step shock, and the data-driven exposure.
"""
import csv
import os

import numpy as np

from metrics import g, data_exogenous, zero_exogenous, HERE

OUT = os.path.join(HERE, "..", "results", "a5_convergence")
NAMES = ["AD", "AB", "AL", "CB", "CL", "SD", "TR", "VB", "PF", "CB_exp", "RC"]
TOL = 1e-3  # per week


def main():
    os.makedirs(OUT, exist_ok=True)
    p = g.get_default_params()
    exo = data_exogenous()
    rows = []
    for scen, kw in [("baseline", {"scenario": "data", "exogenous_override": zero_exogenous(exo)}),
                     ("synthetic step", {"scenario": "shocked", "t_end": 51.0}),
                     ("data-driven", {"scenario": "data", "exogenous_override": exo})]:
        for pname, pol in [("No-SC", g.make_no_sc_policy()), ("Full-SC", g.make_full_sc_policy())]:
            t, x, out = g.run_simulation(p, pol, **kw)
            ex = kw.get("exogenous_override") or g.make_exogenous("shocked", p)
            dx = g.governance_ode(t[-1], x[:, -1], p, pol, ex)
            ri = np.array([o["RI"] for o in out])
            i4 = np.searchsorted(t, t[-1] - 4)
            worst = int(np.argmax(np.abs(dx)))
            r = {"scenario": scen, "policy": pname, "max_abs_dxdt": float(np.max(np.abs(dx))),
                 "worst_stock": NAMES[worst], "RI_change_last_4wk": float(ri[-1] - ri[i4]),
                 "converged": bool(np.max(np.abs(dx)) < TOL)}
            rows.append(r)
            print(f"{scen:15s} {pname:8s} max|dx/dt|={r['max_abs_dxdt']:.5f} ({r['worst_stock']})  "
                  f"dRI last 4 wk={r['RI_change_last_4wk']:+.4f}  converged={r['converged']}")
    with open(os.path.join(OUT, "a5_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
