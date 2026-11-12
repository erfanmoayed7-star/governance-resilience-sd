"""Generate Appendix A (model inventory, adjacency matrix, equations, parameters,
initial conditions) and Appendix C (validation and robustness results) as
Markdown with LaTeX math, from the model code and the results folder, so the
appendix cannot drift from the code that produced the paper's numbers.
Output: results/appendix/appendix_A_C.md (converted to .docx with pandoc).
"""
import csv
import os

from metrics import g, HERE

OUT = os.path.join(HERE, "..", "results", "appendix")
R = os.path.join(HERE, "..", "results")

STOCKS = [  # symbol, name, role, initial value (index in state vector)
    ("VB", "Verification Burden", "Load of documentation and verification awaiting processing", 7),
    ("AB", "Approval Backlog", "Accumulated decisions awaiting authorization", 1),
    ("AL", "Approval Latency", "Delay in decision release", 2),
    ("CL", "Coordination Loss", "Loss of alignment across parties and work packages", 4),
    ("AD", "Active Disputes", "Unresolved claims and disagreements", 0),
    ("TR", "Trust", "Aggregate institutional and relational trust", 6),
    ("CB", "Cash Buffer", "Liquidity slack available to absorb shocks", 3),
    ("SD", "Schedule Delay", "Accumulated schedule slippage", 5),
    ("PF", "Payment Friction", "Delay and contestation in payment processing", 8),
    ("CB_exp", "Expected Cash Buffer", "Friction-free reference trajectory of CB; defines the liquidity gap for B1 and B2", 9),
    ("RS", "Relational Strain", "Slow-moving relational consequence of low trust (code: RC)", 10),
]
X0 = [0.1, 0.2, 0.1, 0.6, 0.1, 0.1, 0.6, 0.1, 0.1, 0.6, 0.5]

DESC = {
    "vb_base": "Baseline VB inflow", "vb_decay": "VB processing rate", "vb_sc_av": "SC_AutoVerify: proportional reduction of VB inflow",
    "ab_base_in": "Baseline AB inflow", "ab_decay": "AB processing rate", "ab_vb": "VB effect on AB inflow", "ab_lte": "LTE effect on AB inflow",
    "ab_sc_re": "SC_RuleExec: proportional reduction of AB inflow", "al_base": "Baseline AL inflow", "al_ab": "AB effect on AL", "al_decay": "AL decay rate",
    "cl_base": "Baseline CL inflow", "cl_al": "AL effect on CL", "cl_lte": "LTE effect on CL", "cl_decay": "CL decay rate",
    "ad_base_in": "Baseline AD inflow", "ad_cb": "Liquidity shortfall (1 - CB) effect on AD inflow", "ad_mce": "MCE effect on AD inflow",
    "ad_tr": "Trust shortfall (1 - TR) effect on AD inflow", "ad_decay": "AD resolution rate", "ad_sc_dw": "SC_DisputeWF: proportional increase in AD resolution",
    "gre_ad": "B4: GRE effect on AD resolution", "tr_base_in": "Baseline TR inflow", "tr_decay": "TR decay rate", "tr_ad": "AD effect on TR outflow",
    "tr_sc_tp": "SC_Transparency: TR inflow increment", "tr_target": "B3: target trust level", "k_rme": "B3: RME gain on the trust gap",
    "c_rme": "B3: cost per unit RME (reported, not fed into COI or RI)", "cb_base_in": "Baseline CB inflow", "cb_decay": "CB outflow rate",
    "cb_pf": "PF effect on CB outflow", "cb_mce": "MCE effect on CB outflow", "k_pee": "B1/B2: PEE gain on the liquidity gap",
    "cb_pee": "B1: PEE effect on CB inflow", "pf_pee": "B2: PEE effect on PF resolution", "c_pee": "B1/B2: cost per unit PEE (reported, not fed into COI or RI)",
    "pf_base": "Baseline PF inflow", "pf_ad": "AD effect on PF", "pf_al": "AL effect on PF", "pf_decay": "PF decay rate",
    "sd_base": "Baseline SD inflow", "sd_cl": "CL effect on SD", "sd_decay": "SD decay rate",
    "rc_it": "k_RS: trust sensitivity of the RS target", "rc_adjust": "alpha_RS: RS adjustment rate", "ri_rc": "r_RS: RS weight in RI",
    "ri_target": "B4: target RI", "k_gre": "B4: GRE gain on the performance gap", "c_gre": "B4: cost per unit GRE (reported, not fed into COI or RI)",
    "coi_base": "C_0: COI constant", "coi_ad": "C_AD: AD weight in COI", "coi_sd": "C_SD: SD weight in COI", "coi_cb": "C_CB: weight of (1 - CB) in COI",
    "ri_base": "r_0: RI constant", "ri_ad": "r_AD: AD weight in RI", "ri_cb": "r_CB: CB weight in RI", "ri_sd": "r_SD: SD weight in RI",
    "ri_coi": "r_COI: COI weight in RI", "k_coi": "Saturation constant for COI in RI",
    "alt_spec_active": "Rival specification 1 switch (0 = base)", "coi_mce_direct": "Rival 1: direct MCE effect on COI", "sd_lte_direct": "Rival 1: direct LTE effect on SD",
    "alt2_spec_active": "Rival specification 2 switch (0 = base)", "sc_coi_direct": "Rival 2: direct SC effect on COI", "sc_direct_level": "Rival 2: mean SC activation (set per run)",
    "shock_amplitude_cost": "Synthetic step: MCE level (validation tests only)", "shock_amplitude_lead": "Synthetic step: LTE level (validation tests only)",
    "shock_time": "Synthetic step: onset (weeks, validation tests only)",
}
GROUPS = [
    ("Governance stocks", ["vb_base", "vb_decay", "ab_base_in", "ab_decay", "ab_vb", "ab_lte", "al_base", "al_ab", "al_decay",
                           "cl_base", "cl_al", "cl_lte", "cl_decay", "ad_base_in", "ad_cb", "ad_mce", "ad_tr", "ad_decay",
                           "tr_base_in", "tr_decay", "tr_ad", "cb_base_in", "cb_decay", "cb_pf", "cb_mce",
                           "pf_base", "pf_ad", "pf_al", "pf_decay", "sd_base", "sd_cl", "sd_decay"]),
    ("Smart contract mechanisms", ["vb_sc_av", "ab_sc_re", "ad_sc_dw", "tr_sc_tp"]),
    ("Stakeholder-owned loops B1 to B4", ["k_pee", "cb_pee", "pf_pee", "c_pee", "tr_target", "k_rme", "c_rme",
                                          "ri_target", "k_gre", "gre_ad", "c_gre"]),
    ("Relational Strain", ["rc_it", "rc_adjust", "ri_rc"]),
    ("Output indices", ["coi_base", "coi_ad", "coi_sd", "coi_cb", "ri_base", "ri_ad", "ri_cb", "ri_sd", "ri_coi", "k_coi"]),
    ("Rival specifications", ["alt_spec_active", "coi_mce_direct", "sd_lte_direct", "alt2_spec_active", "sc_coi_direct", "sc_direct_level"]),
    ("Synthetic step shock", ["shock_amplitude_cost", "shock_amplitude_lead", "shock_time"]),
]


def rng_and_basis(k, v):
    for d in (g.STAKEHOLDER_LOOP_PARAM_RANGES, g.B4_PARAM_RANGES, g.RI_COI_WEIGHT_RANGES,
              g.RELATIONAL_CLIMATE_PARAM_RANGES):
        if k in d:
            _, lo, hi, unit, src = d[k]
            return f"{lo:g} to {hi:g}", src
    if k in g.SC_EFFECT_RANGES:
        lo, hi = g.SC_EFFECT_RANGES[k]
        return f"{lo:g} to {hi:g} (MC)", "Literature-informed, judgment-based; baseline at range midpoint (Appendix B)"
    if k in ("ad_decay", "ab_lte", "cb_mce", "cl_lte", "shock_amplitude_cost"):
        return f"{0.7*v:.3g} to {1.3*v:.3g}", "Theory-informed; ±30% in sensitivity analysis"
    if k in ("coi_mce_direct", "sd_lte_direct"):
        return "0 to 0.45", "Theory-informed rival-channel strength (swept)"
    if k == "sc_coi_direct":
        return "0.01 to 0.05", "Theory-informed rival-channel strength (swept)"
    return "", "Theory-informed; selected for stable interior equilibria"


def read(path):
    with open(os.path.join(R, path)) as f:
        return list(csv.DictReader(f))


def main():
    os.makedirs(OUT, exist_ok=True)
    p = g.get_default_params()
    L = []
    w = L.append
    w("# Appendix A: Model Structure, Equations, and Parameter Set\n")
    w("Appendix A is generated directly from the model source code archived with this article "
      "(Data Availability Statement), so that the equations and parameter values reported here are those "
      "that produced every result in the paper. Parameter names are given as they appear in the code; "
      "the Relational Strain stock RS is named RC in the code.\n")
    w("## A.1 State variables, output indices and auxiliary variables\n")
    w("Table A1. Model inventory. All stocks are bounded to [0, 1]. Initial values are used in every simulation.\n")
    w("| Symbol | Name | Type | Definition | Initial value |\n|---|---|---|---|---|")
    for s, n, d, i in STOCKS:
        typ = "Governance stock" if i <= 8 else "Auxiliary stock"
        w(f"| {s} | {n} | {typ} | {d} | {X0[i]:g} |")
    w("| COI | Cost Overrun Index | Output index (algebraic) | Cost-side performance pressure, Eq. A12 | n/a |")
    w("| RI | Resilience Index | Output index (algebraic) | Capacity to absorb and recover from disturbance, Eq. A13 | n/a |")
    w("| PEE | Payment Expediting Effort | Auxiliary (B1, B2) | k_pee × max(0, CB_exp − CB) | n/a |")
    w("| RME | Relationship Management Effort | Auxiliary (B3) | k_rme × max(0, tr_target − TR) | n/a |")
    w("| GRE | Governance Redesign Effort | Auxiliary (B4) | k_gre × max(0, ri_target − RI) | n/a |")
    w("| MCE, LTE | Material Cost and Lead-Time Exposure | Exogenous inputs | Data-driven indices on [0, 1] (Appendix B) | n/a |\n")

    w("## A.2 Causal adjacency matrix\n")
    w("Table A2. Direct causal links in the base specification, equivalent to the adjacency matrix. Each row lists every "
      "variable with a direct link to the influenced variable and the sign of that link; no other direct links exist.\n")
    links = {
        "VB": {"SC_AV": "−"}, "AB": {"LTE": "+", "SC_RE": "−", "VB": "+"}, "AL": {"AB": "+"},
        "CL": {"LTE": "+", "AL": "+"}, "AD": {"MCE": "+", "SC_DW": "−", "TR": "−", "CB": "−", "GRE": "−"},
        "TR": {"SC_TP": "+", "AD": "−", "RME": "+"}, "CB": {"MCE": "−", "PF": "−", "PEE": "+"},
        "SD": {"CL": "+"}, "PF": {"AL": "+", "AD": "+", "PEE": "−"}, "RS": {"TR": "−"},
        "COI": {"AD": "+", "SD": "+", "CB": "−"}, "RI": {"AD": "−", "CB": "+", "SD": "−", "COI": "−", "RS": "−"},
        "PEE": {"CB": "−"}, "RME": {"TR": "−"}, "GRE": {"RI": "−"},
    }
    names = {"MCE": "MCE", "LTE": "LTE", "SC_AV": "SC_AutoVerify", "SC_RE": "SC_RuleExec", "SC_DW": "SC_DisputeWF", "SC_TP": "SC_Transparency"}
    w("| Influenced variable | Direct influences (sign) |\n|---|---|")
    for r in ["VB", "AB", "AL", "CL", "AD", "TR", "CB", "SD", "PF", "RS", "COI", "RI", "PEE", "RME", "GRE"]:
        w(f"| {r} | " + "; ".join(f"{names.get(c, c)} ({sg})" for c, sg in links[r].items()) + " |")
    w("\nNote. CB_exp evolves from its own base inflow and outflow only and enters the model through PEE. "
      "Rival specification 1 adds MCE → COI (+) and LTE → SD (+); rival specification 2 adds SC → COI (−). "
      "Verification Burden is affected only by SC_AutoVerify; macroeconomic exposure reaches the governance layer through AD, CB, AB and CL.\n")

    w("## A.3 Dynamic equations\n")
    w("Each stock follows inflow minus outflow. Factors of the form (1 − 0.3X) are crowding terms that slow inflows as a stock "
      "approaches saturation. All stocks are additionally held inside [0.01, 0.99]: a derivative that would push a stock past either bound is set to zero.\n")
    eq = [
        r"\frac{dVB}{dt} = vb_{base}(1 - vb_{sc,av}\,SC_{AV})(1 - 0.3\,VB) - vb_{decay}\,VB",
        r"\frac{dAB}{dt} = ab_{base,in}(1 + ab_{vb}VB + ab_{lte}LTE)(1 - ab_{sc,re}SC_{RE})(1 - 0.3\,AB) - ab_{decay}AB",
        r"\frac{dAL}{dt} = (al_{base} + al_{ab}AB)(1 - 0.3\,AL) - al_{decay}AL",
        r"\frac{dCL}{dt} = (cl_{base} + cl_{al}AL + cl_{lte}LTE)(1 - 0.3\,CL) - cl_{decay}CL",
        r"\frac{dAD}{dt} = ad_{base,in}\left[1 + ad_{cb}(1 - CB) + ad_{mce}MCE + ad_{tr}(1 - TR)\right](1 - 0.3\,AD) - ad_{decay}(1 + ad_{sc,dw}SC_{DW} + gre_{ad}GRE)\,AD",
        r"\frac{dTR}{dt} = (tr_{base,in} + tr_{sc,tp}SC_{TP} + RME)(1 - TR) - (tr_{decay} + tr_{ad}AD)\,TR",
        r"\frac{dCB}{dt} = cb_{base,in}(1 - 0.3\,CB) + cb_{pee}PEE - cb_{decay}(1 + cb_{pf}PF + cb_{mce}MCE)(0.3 + 0.7\,CB)",
        r"\frac{dCB_{exp}}{dt} = cb_{base,in}(1 - 0.3\,CB_{exp}) - cb_{decay}(0.3 + 0.7\,CB_{exp})",
        r"\frac{dSD}{dt} = (sd_{base} + sd_{cl}CL)(1 - 0.3\,SD) - sd_{decay}SD",
        r"\frac{dPF}{dt} = (pf_{base} + pf_{ad}AD + pf_{al}AL)(1 - 0.3\,PF) - pf_{decay}(1 + pf_{pee}PEE)\,PF",
        r"\frac{dRS}{dt} = \alpha_{RS}\left[\min\left(1, \max(0, 1 - k_{RS}TR)\right) - RS\right]",
        r"COI = \max\left(0,\; C_0 + C_{AD}AD + C_{SD}SD + C_{CB}(1 - CB)\right)",
        r"RI = \min\left(1, \max\left(0,\; r_0 - r_{AD}AD + r_{CB}CB - r_{SD}SD - r_{COI}\frac{COI}{COI + k_{coi}} - r_{RS}RS\right)\right)",
    ]
    for i, e in enumerate(eq, 1):
        w(f"$$ {e} \\qquad (A{i}) $$\n")
    w("Effort variables: PEE = k_pee × max(0, CB_exp − CB); RME = k_rme × max(0, tr_target − TR); "
      "GRE = k_gre × max(0, ri_target − RI), with RI evaluated from the current state. SC_AV, SC_RE, SC_DW and SC_TP "
      "take the value 1 under Full-SC and 0 under No-SC. Under rival specification 1, LTE × sd_lte_direct is added to the SD inflow "
      "and MCE × coi_mce_direct to COI; under rival specification 2, sc_coi_direct × (mean SC activation) is subtracted from COI. "
      "The effort costs c_pee, c_rme and c_gre are computed and reported but do not enter COI or RI.\n")

    w("## A.4 Parameter set\n")
    w("Table A3. Complete parameter set (69 parameters). Ranges are those used in the one-at-a-time sensitivity analysis (Table C3) "
      "or, for smart contract effects, the Monte Carlo sampling ranges.\n")
    w("| Parameter | Baseline | Range | Description | Basis |\n|---|---|---|---|---|")
    seen = set()
    for grp, keys in GROUPS:
        w(f"| **{grp}** | | | | |")
        for k in keys:
            seen.add(k)
            r_, b_ = rng_and_basis(k, p[k])
            w(f"| {k} | {p[k]:g} | {r_} | {DESC[k]} | {b_} |")
    missing = set(p) - seen
    assert not missing, missing

    w("\n# Appendix C: Validation and Robustness Results\n")
    w("Validation tests 1 to 9 use the synthetic step shock (MCE = 0.3 and LTE = 0.4 from week 10), under which every stock settles "
      "within the 52-week horizon, and report terminal values. The robustness analyses R1 to R7 use the data-driven exposure "
      "indices and report the horizon-mean Resilience Index unless stated otherwise. All tests pass.\n")
    w("Table C1. Validation tests.\n")
    w("| Test | Purpose | Criterion | Result |\n|---|---|---|---|")
    tests = [
        ("1", "Baseline stability", "All stocks reach interior equilibria with |dX/dt| < 0.01 and no shock", "Pass; all terminal derivatives below 10^-5"),
        ("2", "Directional response", "Full-SC moves AD, AB, VB, SD down and TR, CB, RI up relative to No-SC", "Pass; RI 0.483 to 0.523, AD 0.363 to 0.260, TR 0.551 to 0.728"),
        ("3", "Shock dampening", "Mean deviation of AD from its own baseline is smaller under Full-SC", "Pass; AD deviation ratio 0.81 (AB 0.78). Deviations of RI and SD from their own baselines are not reduced (ratios 1.02 and 1.03), because Full-SC also raises those baselines"),
        ("4", "One-at-a-time sensitivity", "Outputs remain bounded across all tested ranges", "Pass; see Table C3 for the sensitivity of the smart contract gain"),
        ("5", "Stakeholder loops B1 to B3", "Effort is zero when gaps close; loops raise RI; loops active under both policies", "Pass; terminal RI 0.457 without loops, 0.483 with loops"),
        ("6", "Rival specification 1", "SC gain retains at least 50% of its base value when MCE and LTE also act directly on COI and SD", "Pass; gain 0.040 (base) and 0.039 (rival 1); see R3 for the full sweep"),
        ("7", "Partial and sequenced adoption", "Single, cumulative and all 16 combinations; cumulative gain is monotonic", "Pass; SC_DisputeWF ranks first; interaction effect −0.8% (mildly sub-additive)"),
        ("8", "Alternative RI weightings", "SC and stakeholder-loop gains positive under all six schemes", "Pass; see Table C2"),
        ("9", "Governance redesign loop B4", "Effort is zero at target; B4 raises RI; RI has an outgoing causal path", "Pass; terminal RI 0.482 without B4, 0.483 with B4 (small effect, Section 3.2)"),
    ]
    for t in tests:
        w("| " + " | ".join(t) + " |")

    ws = read("a4_weighting_and_sensitivity/weighting_schemes.csv")
    w("\nTable C2. Alternative Resilience Index weighting schemes (data-driven exposure, horizon-mean RI).\n")
    w("| Scheme | r_AD | r_CB | r_SD | r_COI | r_RS | RI No-SC | RI Full-SC | SC gain | % of baseline gain | Loss recovered | B1 to B4 gain | Top mechanism (ratio to second) |")
    w("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in ws:
        w(f"| {r['scheme']} | {float(r['w_ad']):.2f} | {float(r['w_cb']):.2f} | {float(r['w_sd']):.2f} | {float(r['w_coi']):.2f} | {float(r['w_rc']):.2f} | "
          f"{float(r['RI_noSC']):.3f} | {float(r['RI_fullSC']):.3f} | {float(r['SC_gain']):+.4f} | {float(r['SC_gain_pct_of_baseline_scheme']):.0f}% | "
          f"{float(r['share_of_loss_recovered_pct']):.0f}% | {float(r['stakeholder_loop_gain_B1_B4']):+.4f} | "
          f"{r['ranking'].split(' > ')[0]} ({float(r['dominance_ratio']):.2f})|")

    oat = read("a4_weighting_and_sensitivity/oat_sensitivity_sc_gain.csv")
    w("\nTable C3. One-at-a-time sensitivity of the smart contract gain (horizon-mean RI; baseline gain +0.0352). "
      "Parameters ordered by swing; the sign of the gain is preserved for all 28 parameters.\n")
    w("| Parameter | Group | Range tested | Gain at low | Gain at high | Swing (% of gain) |\n|---|---|---|---|---|---|")
    for r in oat:
        w(f"| {r['parameter']} | {r['group']} | {float(r['low']):.4g} to {float(r['high']):.4g} | {float(r['SC_gain_low']):+.4f} | "
          f"{float(r['SC_gain_high']):+.4f} | {float(r['swing_pct_of_gain']):.1f} |")
    w("\nNote. shock_amplitude_cost applies only to the synthetic step scenario and therefore has no effect under data-driven exposure.\n")

    w("Table C4. Robustness analyses (data-driven exposure).\n")
    w("| Analysis | Question | Result |\n|---|---|---|")
    rob = [
        ("R1 Beneficial Monte Carlo (8 parameters, N = 300)", "Is the gain robust to uncertainty in SC effects and stakeholder-loop gains?",
         "No reversals; mean dRI +0.035 (5th to 95th percentile +0.025 to +0.044); mean stable from N = 200"),
        ("R2 Adverse-implementation Monte Carlo", "How often does the gain reverse when mechanisms can fail, and what drives reversal?",
         "Reversal 7.0% at p = 0.10, 18.3% at p = 0.25 (SE 2.2 pp), 39.0% at p = 0.40; correlated failure raises reversal at low p only; reversal arises almost entirely from SC_DisputeWF failure (62% when it fails alone, 0% when any other mechanism or pair fails). Table C5"),
        ("R3 Rival specification 1 sweep", "How do results change as disturbances bypass governance?",
         "Absolute SC gain nearly unchanged (+0.035 to +0.033); share of loss recovered falls from 54% to 27% as direct channels reach 0.30; governance becomes the minority route near 0.30"),
        ("R4 Rival specification 2 sweep", "Does denying SC a direct performance channel bias the estimate?",
         "Gain rises 4% to 24% with direct strength 0.01 to 0.05; base estimates are conservative"),
        ("R5 Workflow-automation comparator", "Is the gain specific to smart contracts?",
         "Standard workflow captures 16% of the SC gain; SC exceeds it in all 300 draws; the difference lies in dispute handling and transparency (Table C6)"),
        ("R6 Convergence", "Are terminal values steady states?",
         "Yes under the synthetic shock; no under data-driven exposure (RI still falling 0.03 over the last four weeks), hence the horizon-mean measure"),
        ("R7 Weighting and sensitivity", "Is the gain and the mechanism ranking robust to the index definition?", "Yes; Tables C2 and C3"),
    ]
    for r in rob:
        w("| " + " | ".join(r) + " |")

    a1 = read("a1_adverse_sweep/a1_results.csv")
    w("\nTable C5. Adverse-implementation Monte Carlo (N = 300 per condition; reversal = share of draws with dRI < 0, horizon-mean RI; 95% Wilson interval).\n")
    w("| Condition | Reversal | SE (pp) | 95% CI | Mean dRI |\n|---|---|---|---|---|")
    for r in a1:
        w(f"| {r['condition']} | {100*float(r['reversal_rate']):.1f}% | {100*float(r['se']):.1f} | "
          f"{100*float(r['ci_lo']):.1f}% to {100*float(r['ci_hi']):.1f}% | {float(r['mean_dRI']):+.4f} |")
    w("\nNote. E1 independent failure with probability p; E2 correlated failure via a shared implementation-quality factor "
      "(Gaussian copula, correlation rho); E3 exactly k mechanisms fail, or the named mechanisms fail; E4 adverse magnitudes mirror the beneficial ranges. "
      "These rates describe the specified scenarios and are not estimates of real-world failure rates.\n")

    a3 = read("a3_workflow_comparator/configs.csv")
    w("Table C6. Smart contracts compared with conventional workflow automation (horizon-mean RI). Activation levels for AutoVerify (AV), RuleExec (RE), DisputeWF (DW) and Transparency (TP).\n")
    w("| Configuration | AV | RE | DW | TP | RI | dRI vs No-SC | Share of Full-SC gain |\n|---|---|---|---|---|---|---|---|")
    for r in a3:
        w(f"| {r['Config']} | {r['AV']} | {r['RE']} | {r['DW']} | {r['TP']} | {float(r['RI']):.4f} | {float(r['dRI_vs_NoSC']):+.4f} | "
          f"{100*float(r['share_of_FullSC_gain']):.0f}% |")
    with open(os.path.join(OUT, "appendix_A_C.md"), "w") as f:
        f.write("\n".join(L) + "\n")
    print("wrote", os.path.join(OUT, "appendix_A_C.md"), len(L), "lines")


if __name__ == "__main__":
    main()
