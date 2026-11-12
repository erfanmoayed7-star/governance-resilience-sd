"""A2 (R2.1, R4.7): how conclusions shift as shocks bypass governance more strongly.

The rival specification adds direct exposure channels that bypass the
governance layer: MCE -> COI and LTE -> SD. Their strength s (applied to both
coefficients, baseline rival value 0.15) is swept from 0 (governance-mediated
only) upward. For each s, under the data-driven exposure scenario:
  loss            = RI(baseline) - RI(shocked, No-SC)
  direct share    = part of the loss that disappears when s is set to 0,
                    i.e. (loss_s - loss_0) / loss_s
  SC gain         = RI(shocked, Full-SC) - RI(shocked, No-SC)
  recovered share = SC gain / loss
Each channel is also swept alone. B1-B4 active throughout.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import governance_system_dynamics as g  # noqa: E402
import data_inputs as di  # noqa: E402

OUT = os.path.join(HERE, "..", "results", "a2_direct_channel_sweep")
LEVELS = [0.0, 0.075, 0.15, 0.225, 0.30, 0.45]  # SD reaches its 0.99 ceiling above ~0.4


def ri(p, pol, exo):
    """Return (terminal RI at week 52, mean RI over the 52-week horizon)."""
    out = g.run_simulation(p, pol, "data", exogenous_override=exo)[2]
    return float(out[-1]["RI"]), float(sum(o["RI"] for o in out) / len(out))


def main():
    os.makedirs(OUT, exist_ok=True)
    base_p = g.get_default_params()
    exo, _ = di.get_data_driven_exogenous("data", t_weeks=g.DEFAULT_T_WEEKS, scale_stress=1.0)
    bo = g.run_simulation(base_p, g.make_no_sc_policy(), "data",
                          exogenous_override={**exo, "MCE": lambda t: 0.0, "LTE": lambda t: 0.0})[2]
    base = {"terminal": float(bo[-1]["RI"]), "mean": float(sum(o["RI"] for o in bo) / len(bo))}
    rows = []
    for variant, keys in [("both", ("coi_mce_direct", "sd_lte_direct")),
                          ("MCE->COI only", ("coi_mce_direct",)),
                          ("LTE->SD only", ("sd_lte_direct",))]:
        loss0 = {}
        print(f"\nDirect channel(s): {variant}")
        for s in LEVELS:
            p = dict(base_p)
            p["alt_spec_active"] = 1.0
            p["coi_mce_direct"] = s if "coi_mce_direct" in keys else 0.0
            p["sd_lte_direct"] = s if "sd_lte_direct" in keys else 0.0
            no, full = ri(p, g.make_no_sc_policy(), exo), ri(p, g.make_full_sc_policy(), exo)
            line = f"  s={s:5.3f}"
            for j, metric in enumerate(("terminal", "mean")):
                loss, gain = base[metric] - no[j], full[j] - no[j]
                loss0.setdefault(metric, loss)
                direct = (loss - loss0[metric]) / loss if loss > 0 else 0.0
                rows.append({"variant": variant, "metric": metric, "strength": s,
                             "RI_noSC": no[j], "RI_fullSC": full[j], "loss": loss,
                             "direct_share_of_loss": direct, "governance_share_of_loss": 1 - direct,
                             "SC_gain": gain, "recovered_share": gain / loss})
                line += f" | {metric:8s} loss={loss:.4f} direct={direct:6.1%} gain={gain:+.4f} rec={gain/loss:6.1%}"
            print(line)
    with open(os.path.join(OUT, "a2_results.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.5f}" if isinstance(v, float) else v) for k, v in r.items()})


if __name__ == "__main__":
    main()
