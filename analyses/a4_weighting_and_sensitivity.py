"""A4 (R4.4): Resilience Index weighting schemes and full one-at-a-time sensitivity.

Part 1. All six RI weighting schemes with full weight vectors, RI under No-SC
and Full-SC, the smart-contract gain, the stakeholder-loop gain, and the
mechanism ranking under each scheme (is SC_DisputeWF first in every scheme?).

Part 2. One-at-a-time sensitivity of the smart-contract gain (the paper's
central quantity) to every disclosed parameter, each moved to its disclosed
minimum and maximum:
  core structural parameters      +/-30% of baseline
  stakeholder loops B1-B3, B4     disclosed theory-informed ranges (about +/-40%)
  RI/COI weights                  disclosed ranges (+/-40%)
  Relational Climate (rc_*)       disclosed ranges (about +/-40%)
  SC effect sizes                 Monte Carlo ranges

Scenario: data-driven exposure. Measure: horizon-mean RI (primary); terminal
RI at week 52 reported alongside.
"""
import csv
import os

from metrics import g, data_exogenous, zero_exogenous, ri_measures, HERE

OUT = os.path.join(HERE, "..", "results", "a4_weighting_and_sensitivity")
MECHS = [("SC_DisputeWF", "sc_dispute_wf"), ("SC_Transparency", "sc_transparency"),
         ("SC_RuleExec", "sc_rule_exec"), ("SC_AutoVerify", "sc_auto_verify")]
CORE = ["ad_decay", "ab_lte", "cb_mce", "cl_lte", "shock_amplitude_cost"]


def single(name_kw):
    kwargs = {k: 0.0 for _, k in MECHS}
    kwargs[name_kw] = 1.0
    return g.make_policy(**kwargs)


def loops_off(p):
    q = dict(p)
    q.update({"k_rme": 0.0, "k_pee": 0.0, "k_gre": 0.0})
    return q


def part1(exo):
    base_p = g.get_default_params()
    rows, base_gain = [], None
    for scheme, w in g.RI_WEIGHTING_SCHEMES.items():
        p = {**base_p, **w}
        no = ri_measures(p, g.make_no_sc_policy(), exo)
        full = ri_measures(p, g.make_full_sc_policy(), exo)
        undist = ri_measures(p, g.make_no_sc_policy(), zero_exogenous(exo))
        off = ri_measures(loops_off(p), g.make_no_sc_policy(), exo)
        eff = {n: ri_measures(p, single(kw), exo)["mean"] - no["mean"] for n, kw in MECHS}
        rank = sorted(eff, key=lambda n: -eff[n])
        gain = full["mean"] - no["mean"]
        base_gain = base_gain if base_gain is not None else gain
        r = {"scheme": scheme, **{f"w_{k[3:]}": v for k, v in w.items()},
             "RI_noSC": no["mean"], "RI_fullSC": full["mean"], "SC_gain": gain,
             "SC_gain_pct_of_baseline_scheme": 100 * gain / base_gain,
             "share_of_loss_recovered_pct": 100 * gain / (undist["mean"] - no["mean"]),
             "stakeholder_loop_gain_B1_B4": no["mean"] - off["mean"],
             "SC_gain_terminal": full["terminal"] - no["terminal"],
             **{f"dRI_{n}": eff[n] for n, _ in MECHS},
             "ranking": " > ".join(rank),
             "dominance_ratio": eff[rank[0]] / eff[rank[1]]}
        rows.append(r)
        print(f"{scheme:22s} w(AD,CB,SD,COI,RC)=({w['ri_ad']:.2f},{w['ri_cb']:.2f},{w['ri_sd']:.2f},"
              f"{w['ri_coi']:.2f},{w['ri_rc']:.2f})  gain={gain:+.4f} ({100*gain/base_gain:5.1f}% of base)  "
              f"recovered={r['share_of_loss_recovered_pct']:4.1f}%  loops={r['stakeholder_loop_gain_B1_B4']:+.4f}  "
              f"top={rank[0]} x{r['dominance_ratio']:.2f}")
    gains = [r["SC_gain"] for r in rows]
    print(f"SC gain across schemes: {min(gains):+.4f} to {max(gains):+.4f}; "
          f"{100*min(gains)/base_gain:.0f}% to {100*max(gains)/base_gain:.0f}% of the baseline-scheme gain")
    return rows


def ranges():
    p = g.get_default_params()
    out = [(k, "core structural (+/-30%)", p[k], 0.7 * p[k], 1.3 * p[k]) for k in CORE]
    for label, d in [("stakeholder loops B1-B3", g.STAKEHOLDER_LOOP_PARAM_RANGES),
                     ("B4 governance redesign", g.B4_PARAM_RANGES),
                     ("RI/COI weights", g.RI_COI_WEIGHT_RANGES),
                     ("Relational Climate", g.RELATIONAL_CLIMATE_PARAM_RANGES)]:
        out += [(k, label, p[k], v[1], v[2]) for k, v in d.items()]
    out += [(k, "SC effect size (MC range)", p[k], lo, hi) for k, (lo, hi) in g.SC_EFFECT_RANGES.items()]
    return out


def part2(exo):
    base_p = g.get_default_params()
    b_no = ri_measures(base_p, g.make_no_sc_policy(), exo)["mean"]
    b_gain = ri_measures(base_p, g.make_full_sc_policy(), exo)["mean"] - b_no
    rows = []
    for k, group, base, lo, hi in ranges():
        res = {}
        for tag, v in (("low", lo), ("high", hi)):
            p = {**base_p, k: v}
            no = ri_measures(p, g.make_no_sc_policy(), exo)["mean"]
            res[tag] = ri_measures(p, g.make_full_sc_policy(), exo)["mean"] - no
        swing = abs(res["high"] - res["low"])
        rows.append({"parameter": k, "group": group, "baseline": base, "low": lo, "high": hi,
                     "SC_gain_low": res["low"], "SC_gain_high": res["high"], "swing": swing,
                     "swing_pct_of_gain": 100 * swing / b_gain,
                     "sign_preserved": min(res.values()) > 0})
    rows.sort(key=lambda r: -r["swing"])
    print(f"\nOne-at-a-time sensitivity of the SC gain (baseline {b_gain:+.4f}), largest swings first:")
    for r in rows:
        print(f"  {r['parameter']:22s} {r['group']:28s} [{r['low']:.4g}, {r['high']:.4g}]  "
              f"gain {r['SC_gain_low']:+.4f} .. {r['SC_gain_high']:+.4f}  swing {r['swing_pct_of_gain']:5.1f}%  "
              f"{'sign kept' if r['sign_preserved'] else 'SIGN LOST'}")
    print(f"Sign of the SC gain preserved for all {len(rows)} parameters: "
          f"{all(r['sign_preserved'] for r in rows)}")
    return rows


def write(rows, name):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.5f}" if isinstance(v, float) else v) for k, v in r.items()})


def main():
    os.makedirs(OUT, exist_ok=True)
    exo = data_exogenous()
    write(part1(exo), "weighting_schemes.csv")
    write(part2(exo), "oat_sensitivity_sc_gain.csv")


if __name__ == "__main__":
    main()
