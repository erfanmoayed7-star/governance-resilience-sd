"""Authoritative headline numbers for the manuscript, each tagged with its scenario.

Scenarios
  data      : data-driven MCE/LTE exposure indices (headline scenario, Section 4.2)
  synthetic : step shock (MCE 0.3, LTE 0.4 at week 10), used by validation tests
Baseline (no exposure) is identical under both.
Stakeholder loops B1-B4 are active in every arm.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import governance_system_dynamics as g  # noqa: E402
import data_inputs as di  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "headline")
os.makedirs(OUT, exist_ok=True)
T = g.DEFAULT_T_WEEKS
MECHS = [("SC_DisputeWF", "sc_dispute_wf"), ("SC_Transparency", "sc_transparency"),
         ("SC_RuleExec", "sc_rule_exec"), ("SC_AutoVerify", "sc_auto_verify")]


def ri(params, pol, scenario, exo=None):
    if scenario == "data":
        out = g.run_simulation(params, pol, "data", exogenous_override=exo)[2]
    else:
        out = g.run_simulation(params, pol, scenario, t_end=float(T))[2]
    return float(out[-1]["RI"])


def main():
    p = g.get_default_params()
    exo, _ = di.get_data_driven_exogenous("data", t_weeks=T, scale_stress=1.0)
    rows = []
    base = ri(p, g.make_no_sc_policy(), "baseline")
    rows.append(("baseline", "RI undisturbed, No-SC", base))
    for scen in ("data", "shocked"):
        tag = "data" if scen == "data" else "synthetic"
        no = ri(p, g.make_no_sc_policy(), scen, exo)
        full = ri(p, g.make_full_sc_policy(), scen, exo)
        loss, gain = base - no, full - no
        rows += [(tag, "RI shocked, No-SC", no), (tag, "RI shocked, Full-SC", full),
                 (tag, "Loss vs baseline (index units)", loss),
                 (tag, "Loss as % of baseline", 100 * loss / base),
                 (tag, "Full-SC gain (index units)", gain),
                 (tag, "Gain as % of shocked value", 100 * gain / no),
                 (tag, "Share of loss recovered (%)", 100 * gain / loss),
                 (tag, "Residual gap to baseline (% of loss)", 100 * (base - full) / loss)]
        eff = []
        for name, kw in MECHS:
            kwargs = {k: 0.0 for _, k in MECHS}
            kwargs[kw] = 1.0
            d = ri(p, g.make_policy(**kwargs), scen, exo) - no
            eff.append((name, d))
            rows.append((tag, f"dRI {name} alone", d))
        eff.sort(key=lambda e: -e[1])
        rows.append((tag, f"Dominance ratio {eff[0][0]} / {eff[1][0]}", eff[0][1] / eff[1][1]))
        rows.append((tag, "Sum of individual effects / joint effect", sum(e for _, e in eff) / gain))

    with open(os.path.join(OUT, "headline_numbers.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["scenario", "quantity", "value"])
        for r in rows:
            w.writerow([r[0], r[1], f"{r[2]:.5f}"])
    for r in rows:
        print(f"{r[0]:10s} {r[1]:45s} {r[2]:.4f}")


if __name__ == "__main__":
    main()
