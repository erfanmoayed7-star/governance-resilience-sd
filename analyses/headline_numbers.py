"""Authoritative headline numbers for the manuscript.

Scenario: data-driven MCE/LTE exposure; baseline = same horizon with no exposure.
Measures: horizon-mean RI (primary) and terminal RI at week 52 (secondary).
Stakeholder loops B1-B4 are active in every arm, so every SC effect is
measured with those loops already operating.
"""
import csv
import os

from metrics import g, data_exogenous, zero_exogenous, ri_measures, HERE

OUT = os.path.join(HERE, "..", "results", "headline")
MECHS = [("SC_DisputeWF", "sc_dispute_wf"), ("SC_Transparency", "sc_transparency"),
         ("SC_RuleExec", "sc_rule_exec"), ("SC_AutoVerify", "sc_auto_verify")]


def main():
    os.makedirs(OUT, exist_ok=True)
    p = g.get_default_params()
    exo = data_exogenous()
    base = ri_measures(p, g.make_no_sc_policy(), zero_exogenous(exo))
    no = ri_measures(p, g.make_no_sc_policy(), exo)
    full = ri_measures(p, g.make_full_sc_policy(), exo)
    singles = {}
    for name, kw in MECHS:
        kwargs = {k: 0.0 for _, k in MECHS}
        kwargs[kw] = 1.0
        singles[name] = ri_measures(p, g.make_policy(**kwargs), exo)

    rows = []
    for m in ("mean", "terminal"):
        loss, gain = base[m] - no[m], full[m] - no[m]
        rows += [(m, "RI undisturbed, No-SC", base[m]), (m, "RI shocked, No-SC", no[m]),
                 (m, "RI shocked, Full-SC", full[m]),
                 (m, "Loss vs baseline (index units)", loss),
                 (m, "Loss as % of baseline", 100 * loss / base[m]),
                 (m, "Full-SC gain (index units)", gain),
                 (m, "Gain as % of shocked value", 100 * gain / no[m]),
                 (m, "Share of loss recovered (%)", 100 * gain / loss),
                 (m, "Residual gap to baseline (% of loss)", 100 * (base[m] - full[m]) / loss)]
        eff = sorted(((n, singles[n][m] - no[m]) for n, _ in MECHS), key=lambda e: -e[1])
        rows += [(m, f"dRI {n} alone", d) for n, d in eff]
        rows.append((m, f"Dominance ratio {eff[0][0]} / {eff[1][0]}", eff[0][1] / eff[1][1]))
        rows.append((m, "Sum of individual effects / joint effect", sum(d for _, d in eff) / gain))

    with open(os.path.join(OUT, "headline_numbers.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["measure", "quantity", "value"])
        for r in rows:
            w.writerow([r[0], r[1], f"{r[2]:.5f}"])
    for r in rows:
        print(f"{r[0]:9s} {r[1]:48s} {r[2]:.4f}")


if __name__ == "__main__":
    main()
