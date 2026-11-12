"""Numbers, tables and figures for Section 4 (data-driven exposure, horizon-mean RI).

Outputs in results/section4/:
  table4_abc.csv          relative area between curves, Full-SC vs No-SC, per variable
  table5_mc8.csv          8-parameter Monte Carlo summary for dRI, dCOI, dSD, dAD (horizon means)
  mc8_draws.csv           all draws
  src_attribution.csv     standardized regression coefficients of the sampled parameters on dRI
  fig2.png ... fig5.png   manuscript figures
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from metrics import g, data_exogenous, zero_exogenous, HERE

OUT = os.path.join(HERE, "..", "results", "section4")
R = os.path.join(HERE, "..", "results")
LOOP_PARAMS = {"cb_pee": g.STAKEHOLDER_LOOP_PARAM_RANGES["cb_pee"][1:3],
               "pf_pee": g.STAKEHOLDER_LOOP_PARAM_RANGES["pf_pee"][1:3],
               "k_rme": g.STAKEHOLDER_LOOP_PARAM_RANGES["k_rme"][1:3],
               "k_gre": g.B4_PARAM_RANGES["k_gre"][1:3]}
LABEL = {"ad_sc_dw": "SC_DisputeWF effect", "tr_sc_tp": "SC_Transparency effect", "ab_sc_re": "SC_RuleExec effect",
         "vb_sc_av": "SC_AutoVerify effect", "cb_pee": "B1 gain (PEE → CB)", "pf_pee": "B2 gain (PEE → PF)",
         "k_rme": "B3 gain (RME)", "k_gre": "B4 gain (GRE)"}
IDX = {"AD": 0, "AB": 1, "AL": 2, "CB": 3, "CL": 4, "SD": 5, "TR": 6, "VB": 7, "PF": 8}
plt.rcParams.update({"font.family": "serif", "font.serif": ["DejaVu Serif"], "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
C_NO, C_SC, C_BASE = "#b2182b", "#1a7a4c", "#333333"


def run(p, pol, exo):
    t, x, out = g.run_simulation(p, pol, "data", exogenous_override=exo)
    return t, x, out


def series(t, x, out, var):
    return x[IDX[var]] if var in IDX else np.array([o[var] for o in out])


def hmean(t, s):
    return float(np.mean(s))


def table4(exo):
    p = g.get_default_params()
    t0, x0, o0 = run(p, g.make_no_sc_policy(), exo)
    t1, x1, o1 = run(p, g.make_full_sc_policy(), exo)
    rows = []
    direct = {"VB": "Direct SC_AutoVerify effect", "AB": "Direct SC_RuleExec effect", "AD": "Direct SC_DisputeWF effect",
              "TR": "Direct SC_Transparency effect"}
    for v in ["VB", "AB", "AL", "CL", "AD", "TR", "CB", "SD", "PF", "COI", "RI"]:
        a, b = series(t0, x0, o0, v), series(t1, x1, o1, v)
        abc = np.trapezoid(np.abs(b - a), t0)
        rel = 100 * abc / np.trapezoid(a, t0)
        improve = (np.mean(b) > np.mean(a)) if v in ("TR", "CB", "RI") else (np.mean(b) < np.mean(a))
        rows.append({"variable": v, "type": "Increase" if v in ("TR", "CB", "RI") else "Reduction",
                     "relative_improvement_pct": rel if improve else -rel,
                     "note": direct.get(v, "Performance output" if v in ("COI", "SD") else
                                        "System-level aggregate" if v == "RI" else "Downstream")})
    rows.sort(key=lambda r: -r["relative_improvement_pct"])
    return rows, (t0, o0, o1)


def mc8(exo):
    base = g.get_default_params()
    rng = np.random.default_rng(g.MC_SEED)
    keys = list({**g.SC_EFFECT_RANGES, **LOOP_PARAMS})
    rows = []
    for _ in range(g.MC_N_RUNS):
        p = dict(base)
        for k, (lo, hi) in {**g.SC_EFFECT_RANGES, **LOOP_PARAMS}.items():
            p[k] = float(rng.uniform(lo, hi))
        t0, x0, o0 = run(p, g.make_no_sc_policy(), exo)
        t1, x1, o1 = run(p, g.make_full_sc_policy(), exo)
        r = {k: p[k] for k in keys}
        for v in ("RI", "COI", "SD", "AD"):
            r[f"d{v}"] = hmean(t1, series(t1, x1, o1, v)) - hmean(t0, series(t0, x0, o0, v))
        rows.append(r)
    X = np.array([[r[k] for k in keys] for r in rows])
    y = np.array([r["dRI"] for r in rows])
    Xs = (X - X.mean(0)) / X.std(0)
    ys = (y - y.mean()) / y.std()
    coef, *_ = np.linalg.lstsq(np.c_[np.ones(len(ys)), Xs], ys, rcond=None)
    r2 = 1 - np.sum((ys - np.c_[np.ones(len(ys)), Xs] @ coef) ** 2) / np.sum(ys ** 2)
    src = sorted(zip(keys, coef[1:]), key=lambda kv: -kv[1])
    return rows, src, r2


def write(rows, name):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{v:.5f}" if isinstance(v, float) else v) for k, v in r.items()})


def fig2(exo, traj):
    t0, o0, o1 = traj
    p = g.get_default_params()
    tb, xb, ob = run(p, g.make_no_sc_policy(), zero_exogenous(exo))
    ri_b, ri_n, ri_s = (np.array([o["RI"] for o in o]) for o in (ob, o0, o1))
    m = {k: float(np.mean(v)) for k, v in (("b", ri_b), ("n", ri_n), ("s", ri_s))}
    fig, (a, b) = plt.subplots(2, 1, figsize=(7.2, 5.6), height_ratios=[1, 2], sharex=True)
    a.plot(t0, [exo["MCE"](t) for t in t0], color="#e08214", lw=1.6, label="MCE (material cost exposure)")
    a.plot(t0, [exo["LTE"](t) for t in t0], color="#5e3c99", lw=1.6, ls="--", label="LTE (lead-time exposure)")
    a.set_ylabel("Exposure index [0, 1]"); a.legend(frameon=False, loc="upper right", fontsize=8)
    a.set_title("A. Data-driven exposure indices", loc="left", fontsize=9, fontweight="bold")
    b.plot(tb, ri_b, color=C_BASE, ls=":", lw=1.6, label=f"Undisturbed baseline (mean {m['b']:.3f})")
    b.plot(t0, ri_n, color=C_NO, ls="--", lw=1.8, label=f"Shocked, No-SC (mean {m['n']:.3f})")
    b.plot(t0, ri_s, color=C_SC, lw=1.8, label=f"Shocked, Full-SC (mean {m['s']:.3f})")
    b.fill_between(t0, ri_n, np.interp(t0, tb, ri_b), color=C_NO, alpha=0.08, lw=0)
    b.fill_between(t0, ri_n, ri_s, color=C_SC, alpha=0.15, lw=0)
    b.set_xlabel("Week"); b.set_ylabel("Resilience Index (RI)")
    b.set_title(f"B. Resilience Index: Full-SC recovers {100*(m['s']-m['n'])/(m['b']-m['n']):.0f}% of the "
                f"shock-induced loss in mean RI", loc="left", fontsize=9, fontweight="bold")
    b.set_ylim(0.40, 0.60)
    b.legend(frameon=False, loc="upper left", fontsize=8, ncol=1, bbox_to_anchor=(0.0, 1.0))
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig2.png")); plt.close(fig)
    return m


def fig3(src, r2):
    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    names = [LABEL[k] for k, _ in src][::-1]
    vals = [v for _, v in src][::-1]
    cols = ["#b2182b" if k in g.SC_EFFECT_RANGES else "#2166ac" for k, _ in src][::-1]
    ax.barh(names, vals, color=cols)
    for i, v in enumerate(vals):
        ax.text(v + (0.02 if v >= 0 else -0.02), i, f"{v:+.3f}", va="center", ha="left" if v >= 0 else "right", fontsize=8)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel(f"Standardized regression coefficient on ΔRI (horizon mean); R² = {r2:.3f}")
    ax.set_xlim(min(vals) - 0.25, max(vals) + 0.25)
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig3.png")); plt.close(fig)


def fig4(exo, rows):
    p = g.get_default_params()
    d = np.array([r["dRI"] for r in rows])
    fig = plt.figure(figsize=(7.2, 6.0))
    a = fig.add_subplot(2, 2, 1); b = fig.add_subplot(2, 2, 2); c = fig.add_subplot(2, 1, 2)
    a.hist(d, bins=30, color="#4d7ea8", edgecolor="white")
    a.axvline(d.mean(), color="black", lw=1, label=f"mean {d.mean():+.4f}")
    a.axvline(np.percentile(d, 5), color="black", lw=1, ls=":", label=f"5th pct {np.percentile(d, 5):+.4f}")
    a.set_xlabel("ΔRI, Full-SC minus No-SC (horizon mean)"); a.set_ylabel("Draws")
    a.set_title("A. Monte Carlo, 8 parameters, N = 300", loc="left", fontsize=9, fontweight="bold")
    a.legend(frameon=False, fontsize=7.5)
    lv = np.linspace(0, 1, 11)
    no = np.mean([o["RI"] for o in run(p, g.make_no_sc_policy(), exo)[2]])
    for name, kw, ls in [("SC_DisputeWF", "sc_dispute_wf", "-"), ("SC_Transparency", "sc_transparency", "-."),
                         ("SC_RuleExec", "sc_rule_exec", "--"), ("SC_AutoVerify", "sc_auto_verify", ":")]:
        ys = []
        for l in lv:
            kws = {"sc_dispute_wf": 0, "sc_transparency": 0, "sc_rule_exec": 0, "sc_auto_verify": 0}
            kws[kw] = l
            ys.append(np.mean([o["RI"] for o in run(p, g.make_policy(**kws), exo)[2]]) - no)
        b.plot(lv, ys, ls=ls, lw=1.6, label=name)
    b.set_xlabel("Mechanism activation level"); b.set_ylabel("ΔRI vs No-SC (horizon mean)")
    b.set_title("B. Single-mechanism activation", loc="left", fontsize=9, fontweight="bold")
    b.legend(frameon=False, fontsize=7.5)
    oat = list(csv.DictReader(open(os.path.join(R, "a4_weighting_and_sensitivity", "oat_sensitivity_sc_gain.csv"))))[:10][::-1]
    base = 0.0352
    for i, r in enumerate(oat):
        lo, hi = sorted([float(r["SC_gain_low"]), float(r["SC_gain_high"])])
        c.barh(i, hi - lo, left=lo, color="#4d7ea8")
    c.axvline(base, color="black", lw=0.8, ls="--")
    c.set_yticks(range(len(oat))); c.set_yticklabels([f"{r['parameter']} ({r['group'].split(' (')[0].replace('Relational Climate', 'Relational Strain')})" for r in oat], fontsize=7.5)
    c.set_xlabel("Smart contract gain in RI (horizon mean) across each parameter's tested range")
    c.set_title("C. One-at-a-time sensitivity of the smart contract gain\n(10 most influential of 28 parameters)",
                loc="left", fontsize=9, fontweight="bold")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig4.png")); plt.close(fig)


def fig5():
    a1 = list(csv.DictReader(open(os.path.join(R, "a1_adverse_sweep", "a1_results.csv"))))
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.3), width_ratios=[1.1, 1])
    for exp, lab, mk, col in [("E1", "Independent failures", "o", "#2166ac"), ("E4", "Symmetric adverse magnitudes", "s", "#b2182b")]:
        rr = [r for r in a1 if r["experiment"] == exp]
        x = [float(r["p_adverse"]) for r in rr]; y = [100 * float(r["reversal_rate"]) for r in rr]
        lo = [100 * float(r["ci_lo"]) for r in rr]; hi = [100 * float(r["ci_hi"]) for r in rr]
        a.errorbar(x, y, yerr=[np.subtract(y, lo), np.subtract(hi, y)], marker=mk, ms=4, lw=1.2, capsize=2, color=col, label=lab)
    rr = [r for r in a1 if r["experiment"] == "E2" and float(r["rho"]) == 1.0]
    a.plot([float(r["p_adverse"]) for r in rr], [100 * float(r["reversal_rate"]) for r in rr], "^", color="#1a7a4c", ms=5,
           label="Fully correlated failures")
    a.axvline(0.25, color="grey", lw=0.8, ls=":")
    a.set_xlabel("Probability that each mechanism fails"); a.set_ylabel("Draws with reversed benefit (%)")
    a.set_title("A. Reversal rate (95% CI)", loc="left", fontsize=9, fontweight="bold")
    a.legend(frameon=False, fontsize=7.5, loc="upper left")
    a.set_ylim(-2, 62)
    rr = [r for r in a1 if r["experiment"] == "E3" and r["failed"]]
    rr.sort(key=lambda r: float(r["reversal_rate"]))
    labs = [r["failed"].replace("SC_", "").replace("+", " + ") for r in rr]
    vals = [100 * float(r["reversal_rate"]) for r in rr]
    b.barh(labs, vals, color=["#b2182b" if "DisputeWF" in l else "#9ecae1" for l in labs])
    for i, v in enumerate(vals):
        b.text(v + 1, i, f"{v:.0f}%", va="center", fontsize=7.5)
    b.set_xlim(0, 112); b.tick_params(axis="y", labelsize=7.5)
    b.set_xlabel("Draws with reversed benefit (%)")
    b.set_title("B. Which mechanisms fail", loc="left", fontsize=9, fontweight="bold")
    fig.tight_layout(); fig.savefig(os.path.join(OUT, "fig5.png")); plt.close(fig)


def main():
    os.makedirs(OUT, exist_ok=True)
    exo = data_exogenous()
    t4, traj = table4(exo)
    write(t4, "table4_abc.csv")
    for r in t4:
        print(f"T4 {r['variable']:4s} {r['type']:9s} {r['relative_improvement_pct']:6.1f}%  {r['note']}")
    rows, src, r2 = mc8(exo)
    write(rows, "mc8_draws.csv")
    t5 = []
    for v in ("RI", "COI", "SD", "AD"):
        d = np.array([r[f"d{v}"] for r in rows])
        t5.append({"outcome": f"d{v}", "mean": d.mean(), "median": float(np.median(d)), "p5": float(np.percentile(d, 5)),
                   "p95": float(np.percentile(d, 95)), "sign_reversals": int(np.sum(d < 0) if v == "RI" else np.sum(d > 0))})
        print(f"T5 d{v}: mean {d.mean():+.4f} median {np.median(d):+.4f} p5 {np.percentile(d,5):+.4f} p95 {np.percentile(d,95):+.4f}")
    write(t5, "table5_mc8.csv")
    write([{"parameter": k, "label": LABEL[k], "src": v} for k, v in src], "src_attribution.csv")
    print("SRC:", ", ".join(f"{LABEL[k]} {v:+.3f}" for k, v in src), f"R2={r2:.3f}")
    m = fig2(exo, traj)
    print("Fig2 means", m)
    fig3(src, r2); fig4(exo, rows); fig5()
    print("figures written")


if __name__ == "__main__":
    main()
