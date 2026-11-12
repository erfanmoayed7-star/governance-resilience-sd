# Appendix A: Model Structure, Equations, and Parameter Set

Appendix A is generated directly from the model source code archived with this article (Data Availability Statement), so that the equations and parameter values reported here are those that produced every result in the paper. Parameter names are given as they appear in the code; the Relational Strain stock RS is named RC in the code.

## A.1 State variables, output indices and auxiliary variables

Table A1. Model inventory. All stocks are bounded to [0, 1]. Initial values are used in every simulation.

| Symbol | Name | Type | Definition | Initial value |
|---|---|---|---|---|
| VB | Verification Burden | Governance stock | Load of documentation and verification awaiting processing | 0.1 |
| AB | Approval Backlog | Governance stock | Accumulated decisions awaiting authorization | 0.2 |
| AL | Approval Latency | Governance stock | Delay in decision release | 0.1 |
| CL | Coordination Loss | Governance stock | Loss of alignment across parties and work packages | 0.1 |
| AD | Active Disputes | Governance stock | Unresolved claims and disagreements | 0.1 |
| TR | Trust | Governance stock | Aggregate institutional and relational trust | 0.6 |
| CB | Cash Buffer | Governance stock | Liquidity slack available to absorb shocks | 0.6 |
| SD | Schedule Delay | Governance stock | Accumulated schedule slippage | 0.1 |
| PF | Payment Friction | Governance stock | Delay and contestation in payment processing | 0.1 |
| CB_exp | Expected Cash Buffer | Auxiliary stock | Friction-free reference trajectory of CB; defines the liquidity gap for B1 and B2 | 0.6 |
| RS | Relational Strain | Auxiliary stock | Slow-moving relational consequence of low trust (code: RC) | 0.5 |
| COI | Cost Overrun Index | Output index (algebraic) | Cost-side performance pressure, Eq. A12 | n/a |
| RI | Resilience Index | Output index (algebraic) | Capacity to absorb and recover from disturbance, Eq. A13 | n/a |
| PEE | Payment Expediting Effort | Auxiliary (B1, B2) | k_pee × max(0, CB_exp − CB) | n/a |
| RME | Relationship Management Effort | Auxiliary (B3) | k_rme × max(0, tr_target − TR) | n/a |
| GRE | Governance Redesign Effort | Auxiliary (B4) | k_gre × max(0, ri_target − RI) | n/a |
| MCE, LTE | Material Cost and Lead-Time Exposure | Exogenous inputs | Data-driven indices on [0, 1] (Appendix B) | n/a |

## A.2 Causal adjacency matrix

Table A2. Direct causal links in the base specification, equivalent to the adjacency matrix. Each row lists every variable with a direct link to the influenced variable and the sign of that link; no other direct links exist.

| Influenced variable | Direct influences (sign) |
|---|---|
| VB | SC_AutoVerify (−) |
| AB | LTE (+); SC_RuleExec (−); VB (+) |
| AL | AB (+) |
| CL | LTE (+); AL (+) |
| AD | MCE (+); SC_DisputeWF (−); TR (−); CB (−); GRE (−) |
| TR | SC_Transparency (+); AD (−); RME (+) |
| CB | MCE (−); PF (−); PEE (+) |
| SD | CL (+) |
| PF | AL (+); AD (+); PEE (−) |
| RS | TR (−) |
| COI | AD (+); SD (+); CB (−) |
| RI | AD (−); CB (+); SD (−); COI (−); RS (−) |
| PEE | CB (−) |
| RME | TR (−) |
| GRE | RI (−) |

Note. CB_exp evolves from its own base inflow and outflow only and enters the model through PEE. Rival specification 1 adds MCE → COI (+) and LTE → SD (+); rival specification 2 adds SC → COI (−). Verification Burden is affected only by SC_AutoVerify; macroeconomic exposure reaches the governance layer through AD, CB, AB and CL.

## A.3 Dynamic equations

Each stock follows inflow minus outflow. Factors of the form (1 − 0.3X) are crowding terms that slow inflows as a stock approaches saturation. All stocks are additionally held inside [0.01, 0.99]: a derivative that would push a stock past either bound is set to zero.

$$ \frac{dVB}{dt} = vb_{base}(1 - vb_{sc,av}\,SC_{AV})(1 - 0.3\,VB) - vb_{decay}\,VB \qquad (A1) $$

$$ \frac{dAB}{dt} = ab_{base,in}(1 + ab_{vb}VB + ab_{lte}LTE)(1 - ab_{sc,re}SC_{RE})(1 - 0.3\,AB) - ab_{decay}AB \qquad (A2) $$

$$ \frac{dAL}{dt} = (al_{base} + al_{ab}AB)(1 - 0.3\,AL) - al_{decay}AL \qquad (A3) $$

$$ \frac{dCL}{dt} = (cl_{base} + cl_{al}AL + cl_{lte}LTE)(1 - 0.3\,CL) - cl_{decay}CL \qquad (A4) $$

$$ \frac{dAD}{dt} = ad_{base,in}\left[1 + ad_{cb}(1 - CB) + ad_{mce}MCE + ad_{tr}(1 - TR)\right](1 - 0.3\,AD) - ad_{decay}(1 + ad_{sc,dw}SC_{DW} + gre_{ad}GRE)\,AD \qquad (A5) $$

$$ \frac{dTR}{dt} = (tr_{base,in} + tr_{sc,tp}SC_{TP} + RME)(1 - TR) - (tr_{decay} + tr_{ad}AD)\,TR \qquad (A6) $$

$$ \frac{dCB}{dt} = cb_{base,in}(1 - 0.3\,CB) + cb_{pee}PEE - cb_{decay}(1 + cb_{pf}PF + cb_{mce}MCE)(0.3 + 0.7\,CB) \qquad (A7) $$

$$ \frac{dCB_{exp}}{dt} = cb_{base,in}(1 - 0.3\,CB_{exp}) - cb_{decay}(0.3 + 0.7\,CB_{exp}) \qquad (A8) $$

$$ \frac{dSD}{dt} = (sd_{base} + sd_{cl}CL)(1 - 0.3\,SD) - sd_{decay}SD \qquad (A9) $$

$$ \frac{dPF}{dt} = (pf_{base} + pf_{ad}AD + pf_{al}AL)(1 - 0.3\,PF) - pf_{decay}(1 + pf_{pee}PEE)\,PF \qquad (A10) $$

$$ \frac{dRS}{dt} = \alpha_{RS}\left[\min\left(1, \max(0, 1 - k_{RS}TR)\right) - RS\right] \qquad (A11) $$

$$ COI = \max\left(0,\; C_0 + C_{AD}AD + C_{SD}SD + C_{CB}(1 - CB)\right) \qquad (A12) $$

$$ RI = \min\left(1, \max\left(0,\; r_0 - r_{AD}AD + r_{CB}CB - r_{SD}SD - r_{COI}\frac{COI}{COI + k_{coi}} - r_{RS}RS\right)\right) \qquad (A13) $$

Effort variables: PEE = k_pee × max(0, CB_exp − CB); RME = k_rme × max(0, tr_target − TR); GRE = k_gre × max(0, ri_target − RI), with RI evaluated from the current state. SC_AV, SC_RE, SC_DW and SC_TP take the value 1 under Full-SC and 0 under No-SC. Under rival specification 1, LTE × sd_lte_direct is added to the SD inflow and MCE × coi_mce_direct to COI; under rival specification 2, sc_coi_direct × (mean SC activation) is subtracted from COI. The effort costs c_pee, c_rme and c_gre are computed and reported but do not enter COI or RI.

## A.4 Parameter set

Table A3. Complete parameter set (69 parameters). Ranges are those used in the one-at-a-time sensitivity analysis (Table C3) or, for smart contract effects, the Monte Carlo sampling ranges.

| Parameter | Baseline | Range | Description | Basis |
|---|---|---|---|---|
| **Governance stocks** | | | | |
| vb_base | 0.04 |  | Baseline VB inflow | Theory-informed; selected for stable interior equilibria |
| vb_decay | 0.25 |  | VB processing rate | Theory-informed; selected for stable interior equilibria |
| ab_base_in | 0.08 |  | Baseline AB inflow | Theory-informed; selected for stable interior equilibria |
| ab_decay | 0.18 |  | AB processing rate | Theory-informed; selected for stable interior equilibria |
| ab_vb | 0.4 |  | VB effect on AB inflow | Theory-informed; selected for stable interior equilibria |
| ab_lte | 0.35 | 0.245 to 0.455 | LTE effect on AB inflow | Theory-informed; ±30% in sensitivity analysis |
| al_base | 0.03 |  | Baseline AL inflow | Theory-informed; selected for stable interior equilibria |
| al_ab | 0.25 |  | AB effect on AL | Theory-informed; selected for stable interior equilibria |
| al_decay | 0.35 |  | AL decay rate | Theory-informed; selected for stable interior equilibria |
| cl_base | 0.02 |  | Baseline CL inflow | Theory-informed; selected for stable interior equilibria |
| cl_al | 0.2 |  | AL effect on CL | Theory-informed; selected for stable interior equilibria |
| cl_lte | 0.35 | 0.245 to 0.455 | LTE effect on CL | Theory-informed; ±30% in sensitivity analysis |
| cl_decay | 0.35 |  | CL decay rate | Theory-informed; selected for stable interior equilibria |
| ad_base_in | 0.06 |  | Baseline AD inflow | Theory-informed; selected for stable interior equilibria |
| ad_cb | 0.35 |  | Liquidity shortfall (1 - CB) effect on AD inflow | Theory-informed; selected for stable interior equilibria |
| ad_mce | 0.35 |  | MCE effect on AD inflow | Theory-informed; selected for stable interior equilibria |
| ad_tr | 0.25 |  | Trust shortfall (1 - TR) effect on AD inflow | Theory-informed; selected for stable interior equilibria |
| ad_decay | 0.18 | 0.126 to 0.234 | AD resolution rate | Theory-informed; ±30% in sensitivity analysis |
| tr_base_in | 0.12 |  | Baseline TR inflow | Theory-informed; selected for stable interior equilibria |
| tr_decay | 0.05 |  | TR decay rate | Theory-informed; selected for stable interior equilibria |
| tr_ad | 0.3 |  | AD effect on TR outflow | Theory-informed; selected for stable interior equilibria |
| cb_base_in | 0.12 |  | Baseline CB inflow | Theory-informed; selected for stable interior equilibria |
| cb_decay | 0.08 |  | CB outflow rate | Theory-informed; selected for stable interior equilibria |
| cb_pf | 0.25 |  | PF effect on CB outflow | Theory-informed; selected for stable interior equilibria |
| cb_mce | 0.3 | 0.21 to 0.39 | MCE effect on CB outflow | Theory-informed; ±30% in sensitivity analysis |
| pf_base | 0.02 |  | Baseline PF inflow | Theory-informed; selected for stable interior equilibria |
| pf_ad | 0.2 |  | AD effect on PF | Theory-informed; selected for stable interior equilibria |
| pf_al | 0.25 |  | AL effect on PF | Theory-informed; selected for stable interior equilibria |
| pf_decay | 0.35 |  | PF decay rate | Theory-informed; selected for stable interior equilibria |
| sd_base | 0.02 |  | Baseline SD inflow | Theory-informed; selected for stable interior equilibria |
| sd_cl | 0.25 |  | CL effect on SD | Theory-informed; selected for stable interior equilibria |
| sd_decay | 0.3 |  | SD decay rate | Theory-informed; selected for stable interior equilibria |
| **Smart contract mechanisms** | | | | |
| vb_sc_av | 0.35 | 0.2 to 0.5 (MC) | SC_AutoVerify: proportional reduction of VB inflow | Literature-informed, judgment-based; baseline at range midpoint (Appendix B) |
| ab_sc_re | 0.275 | 0.15 to 0.4 (MC) | SC_RuleExec: proportional reduction of AB inflow | Literature-informed, judgment-based; baseline at range midpoint (Appendix B) |
| ad_sc_dw | 0.4 | 0.2 to 0.6 (MC) | SC_DisputeWF: proportional increase in AD resolution | Literature-informed, judgment-based; baseline at range midpoint (Appendix B) |
| tr_sc_tp | 0.2 | 0.1 to 0.3 (MC) | SC_Transparency: TR inflow increment | Literature-informed, judgment-based; baseline at range midpoint (Appendix B) |
| **Stakeholder-owned loops B1 to B4** | | | | |
| k_pee | 0.3 | 0.15 to 0.5 | B1/B2: PEE gain on the liquidity gap | theory-informed |
| cb_pee | 0.3 | 0.2 to 0.4 | B1: PEE effect on CB inflow | theory-informed |
| pf_pee | 0.3 | 0.2 to 0.4 | B2: PEE effect on PF resolution | theory-informed |
| c_pee | 0.03 | 0.01 to 0.05 | B1/B2: cost per unit PEE (reported, not fed into COI or RI) | empirical (invoice factoring) |
| tr_target | 0.8 |  | B3: target trust level | Theory-informed; selected for stable interior equilibria |
| k_rme | 0.3 | 0.15 to 0.5 | B3: RME gain on the trust gap | theory-informed |
| c_rme | 0.0004 | 0.0001 to 0.0005 | B3: cost per unit RME (reported, not fed into COI or RI) | empirical (CII/CPRADR) |
| ri_target | 0.65 |  | B4: target RI | Theory-informed; selected for stable interior equilibria |
| k_gre | 0.3 | 0.15 to 0.5 | B4: GRE gain on the performance gap | theory-informed |
| gre_ad | 0.3 | 0.2 to 0.4 | B4: GRE effect on AD resolution | theory-informed |
| c_gre | 0.0004 | 0.0001 to 0.0008 | B4: cost per unit GRE (reported, not fed into COI or RI) | theory-informed (order-matched to c_rme) |
| **Relational Strain** | | | | |
| rc_it | 0.5 | 0.3 to 0.7 | k_RS: trust sensitivity of the RS target | theory-informed (+/-40%) |
| rc_adjust | 0.15 | 0.1 to 0.25 | alpha_RS: RS adjustment rate | theory-informed (+/-40%) |
| ri_rc | 0.1 | 0.05 to 0.15 | r_RS: RS weight in RI | theory-informed (+/-40%) |
| **Output indices** | | | | |
| coi_base | 0.02 |  | C_0: COI constant | Theory-informed; selected for stable interior equilibria |
| coi_ad | 0.25 | 0.15 to 0.35 | C_AD: AD weight in COI | theory-informed (+/-40%) |
| coi_sd | 0.3 | 0.18 to 0.42 | C_SD: SD weight in COI | theory-informed (+/-40%) |
| coi_cb | 0.25 | 0.15 to 0.35 | C_CB: weight of (1 - CB) in COI | theory-informed (+/-40%) |
| ri_base | 0.5 |  | r_0: RI constant | Theory-informed; selected for stable interior equilibria |
| ri_ad | 0.2 | 0.12 to 0.28 | r_AD: AD weight in RI | theory-informed (+/-40%) |
| ri_cb | 0.3 | 0.18 to 0.42 | r_CB: CB weight in RI | theory-informed (+/-40%) |
| ri_sd | 0.2 | 0.12 to 0.28 | r_SD: SD weight in RI | theory-informed (+/-40%) |
| ri_coi | 0.15 | 0.09 to 0.21 | r_COI: COI weight in RI | theory-informed (+/-40%) |
| k_coi | 0.4 |  | Saturation constant for COI in RI | Theory-informed; selected for stable interior equilibria |
| **Rival specifications** | | | | |
| alt_spec_active | 0 |  | Rival specification 1 switch (0 = base) | Theory-informed; selected for stable interior equilibria |
| coi_mce_direct | 0.15 | 0 to 0.45 | Rival 1: direct MCE effect on COI | Theory-informed rival-channel strength (swept) |
| sd_lte_direct | 0.15 | 0 to 0.45 | Rival 1: direct LTE effect on SD | Theory-informed rival-channel strength (swept) |
| alt2_spec_active | 0 |  | Rival specification 2 switch (0 = base) | Theory-informed; selected for stable interior equilibria |
| sc_coi_direct | 0.03 | 0.01 to 0.05 | Rival 2: direct SC effect on COI | Theory-informed rival-channel strength (swept) |
| sc_direct_level | 0 |  | Rival 2: mean SC activation (set per run) | Theory-informed; selected for stable interior equilibria |
| **Synthetic step shock** | | | | |
| shock_amplitude_cost | 0.3 | 0.21 to 0.39 | Synthetic step: MCE level (validation tests only) | Theory-informed; ±30% in sensitivity analysis |
| shock_amplitude_lead | 0.4 |  | Synthetic step: LTE level (validation tests only) | Theory-informed; selected for stable interior equilibria |
| shock_time | 10 |  | Synthetic step: onset (weeks, validation tests only) | Theory-informed; selected for stable interior equilibria |

# Appendix C: Validation and Robustness Results

Validation tests 1 to 9 use the synthetic step shock (MCE = 0.3 and LTE = 0.4 from week 10), under which every stock settles within the 52-week horizon, and report terminal values. The robustness analyses R1 to R7 use the data-driven exposure indices and report the horizon-mean Resilience Index unless stated otherwise. All tests pass.

Table C1. Validation tests.

| Test | Purpose | Criterion | Result |
|---|---|---|---|
| 1 | Baseline stability | All stocks reach interior equilibria with |dX/dt| < 0.01 and no shock | Pass; all terminal derivatives below 10^-5 |
| 2 | Directional response | Full-SC moves AD, AB, VB, SD down and TR, CB, RI up relative to No-SC | Pass; RI 0.483 to 0.523, AD 0.363 to 0.260, TR 0.551 to 0.728 |
| 3 | Shock dampening | Mean deviation of AD from its own baseline is smaller under Full-SC | Pass; AD deviation ratio 0.81 (AB 0.78). Deviations of RI and SD from their own baselines are not reduced (ratios 1.02 and 1.03), because Full-SC also raises those baselines |
| 4 | One-at-a-time sensitivity | Outputs remain bounded across all tested ranges | Pass; see Table C3 for the sensitivity of the smart contract gain |
| 5 | Stakeholder loops B1 to B3 | Effort is zero when gaps close; loops raise RI; loops active under both policies | Pass; terminal RI 0.457 without loops, 0.483 with loops |
| 6 | Rival specification 1 | SC gain retains at least 50% of its base value when MCE and LTE also act directly on COI and SD | Pass; gain 0.040 (base) and 0.039 (rival 1); see R3 for the full sweep |
| 7 | Partial and sequenced adoption | Single, cumulative and all 16 combinations; cumulative gain is monotonic | Pass; SC_DisputeWF ranks first; interaction effect −0.8% (mildly sub-additive) |
| 8 | Alternative RI weightings | SC and stakeholder-loop gains positive under all six schemes | Pass; see Table C2 |
| 9 | Governance redesign loop B4 | Effort is zero at target; B4 raises RI; RI has an outgoing causal path | Pass; terminal RI 0.482 without B4, 0.483 with B4 (small effect, Section 3.2) |

Table C2. Alternative Resilience Index weighting schemes (data-driven exposure, horizon-mean RI).

| Scheme | r_AD | r_CB | r_SD | r_COI | r_RS | RI No-SC | RI Full-SC | SC gain | % of baseline gain | Loss recovered | B1 to B4 gain | Top mechanism (ratio to second) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Baseline (disclosed) | 0.20 | 0.30 | 0.20 | 0.15 | 0.10 | 0.484 | 0.519 | +0.0352 | 100% | 54% | +0.0288 | SC_DisputeWF (3.01)|
| Equal weights | 0.19 | 0.19 | 0.19 | 0.19 | 0.19 | 0.321 | 0.361 | +0.0406 | 115% | 68% | +0.0282 | SC_DisputeWF (1.83)|
| Dispute-dominant | 0.40 | 0.20 | 0.15 | 0.10 | 0.10 | 0.364 | 0.415 | +0.0508 | 144% | 86% | +0.0265 | SC_DisputeWF (4.28)|
| Liquidity-dominant | 0.15 | 0.50 | 0.15 | 0.10 | 0.05 | 0.742 | 0.769 | +0.0263 | 75% | 41% | +0.0358 | SC_DisputeWF (4.09)|
| Relational-dominant | 0.15 | 0.20 | 0.15 | 0.15 | 0.30 | 0.297 | 0.340 | +0.0429 | 122% | 83% | +0.0329 | SC_DisputeWF (1.09)|
| Performance-dominant | 0.15 | 0.20 | 0.30 | 0.25 | 0.05 | 0.378 | 0.409 | +0.0305 | 87% | 40% | +0.0218 | SC_DisputeWF (3.39)|

Table C3. One-at-a-time sensitivity of the smart contract gain (horizon-mean RI; baseline gain +0.0352). Parameters ordered by swing; the sign of the gain is preserved for all 28 parameters.

| Parameter | Group | Range tested | Gain at low | Gain at high | Swing (% of gain) |
|---|---|---|---|---|---|
| ad_sc_dw | SC effect size (MC range) | 0.2 to 0.6 | +0.0252 | +0.0431 | 50.9 |
| ri_ad | RI/COI weights | 0.12 to 0.28 | +0.0277 | +0.0427 | 42.6 |
| ad_decay | core structural (+/-30%) | 0.126 to 0.234 | +0.0401 | +0.0314 | 24.5 |
| ri_rc | Relational Strain | 0.05 to 0.15 | +0.0318 | +0.0387 | 19.6 |
| rc_it | Relational Strain | 0.3 to 0.7 | +0.0323 | +0.0381 | 16.3 |
| tr_sc_tp | SC effect size (MC range) | 0.1 to 0.3 | +0.0321 | +0.0376 | 15.5 |
| ab_sc_re | SC effect size (MC range) | 0.15 to 0.4 | +0.0332 | +0.0374 | 11.8 |
| k_rme | stakeholder loops B1-B3 | 0.15 to 0.5 | +0.0371 | +0.0336 | 10.1 |
| ri_coi | RI/COI weights | 0.09 to 0.21 | +0.0335 | +0.0369 | 9.5 |
| ri_sd | RI/COI weights | 0.12 to 0.28 | +0.0341 | +0.0363 | 6.3 |
| ri_cb | RI/COI weights | 0.18 to 0.42 | +0.0343 | +0.0362 | 5.5 |
| coi_ad | RI/COI weights | 0.15 to 0.35 | +0.0342 | +0.0360 | 5.3 |
| rc_adjust | Relational Strain | 0.1 to 0.25 | +0.0347 | +0.0357 | 2.9 |
| k_pee | stakeholder loops B1-B3 | 0.15 to 0.5 | +0.0356 | +0.0348 | 2.2 |
| k_gre | B4 governance redesign | 0.15 to 0.5 | +0.0355 | +0.0348 | 2.1 |
| cl_lte | core structural (+/-30%) | 0.245 to 0.455 | +0.0356 | +0.0349 | 2.0 |
| coi_sd | RI/COI weights | 0.18 to 0.42 | +0.0356 | +0.0349 | 1.9 |
| cb_pee | stakeholder loops B1-B3 | 0.2 to 0.4 | +0.0355 | +0.0350 | 1.3 |
| gre_ad | B4 governance redesign | 0.2 to 0.4 | +0.0354 | +0.0350 | 1.2 |
| vb_sc_av | SC effect size (MC range) | 0.2 to 0.5 | +0.0351 | +0.0353 | 0.5 |
| coi_cb | RI/COI weights | 0.15 to 0.35 | +0.0353 | +0.0351 | 0.5 |
| cb_mce | core structural (+/-30%) | 0.21 to 0.39 | +0.0353 | +0.0352 | 0.4 |
| ab_lte | core structural (+/-30%) | 0.245 to 0.455 | +0.0352 | +0.0353 | 0.3 |
| pf_pee | stakeholder loops B1-B3 | 0.2 to 0.4 | +0.0352 | +0.0352 | 0.0 |
| shock_amplitude_cost | core structural (+/-30%) | 0.21 to 0.39 | +0.0352 | +0.0352 | 0.0 |
| c_rme | stakeholder loops B1-B3 | 0.0001 to 0.0005 | +0.0352 | +0.0352 | 0.0 |
| c_pee | stakeholder loops B1-B3 | 0.01 to 0.05 | +0.0352 | +0.0352 | 0.0 |
| c_gre | B4 governance redesign | 0.0001 to 0.0008 | +0.0352 | +0.0352 | 0.0 |

Note. shock_amplitude_cost applies only to the synthetic step scenario and therefore has no effect under data-driven exposure.

Table C4. Robustness analyses (data-driven exposure).

| Analysis | Question | Result |
|---|---|---|
| R1 Beneficial Monte Carlo (8 parameters, N = 300) | Is the gain robust to uncertainty in SC effects and stakeholder-loop gains? | No reversals; mean dRI +0.035 (5th to 95th percentile +0.025 to +0.044); mean stable from N = 200 |
| R2 Adverse-implementation Monte Carlo | How often does the gain reverse when mechanisms can fail, and what drives reversal? | Reversal 7.0% at p = 0.10, 18.3% at p = 0.25 (SE 2.2 pp), 39.0% at p = 0.40; correlated failure raises reversal at low p only; reversal arises almost entirely from SC_DisputeWF failure (62% when it fails alone, 0% when any other mechanism or pair fails). Table C5 |
| R3 Rival specification 1 sweep | How do results change as disturbances bypass governance? | Absolute SC gain nearly unchanged (+0.035 to +0.033); share of loss recovered falls from 54% to 27% as direct channels reach 0.30; governance becomes the minority route near 0.30 |
| R4 Rival specification 2 sweep | Does denying SC a direct performance channel bias the estimate? | Gain rises 4% to 24% with direct strength 0.01 to 0.05; base estimates are conservative |
| R5 Workflow-automation comparator | Is the gain specific to smart contracts? | Standard workflow captures 16% of the SC gain; SC exceeds it in all 300 draws; the difference lies in dispute handling and transparency (Table C6) |
| R6 Convergence | Are terminal values steady states? | Yes under the synthetic shock; no under data-driven exposure (RI still falling 0.03 over the last four weeks), hence the horizon-mean measure |
| R7 Weighting and sensitivity | Is the gain and the mechanism ranking robust to the index definition? | Yes; Tables C2 and C3 |

Table C5. Adverse-implementation Monte Carlo (N = 300 per condition; reversal = share of draws with dRI < 0, horizon-mean RI; 95% Wilson interval).

| Condition | Reversal | SE (pp) | 95% CI | Mean dRI |
|---|---|---|---|---|
| E1 p=0.00 | 0.0% | 0.0 | 0.0% to 1.3% | +0.0347 |
| E1 p=0.05 | 3.7% | 1.1 | 2.1% to 6.4% | +0.0319 |
| E1 p=0.10 | 7.0% | 1.5 | 4.6% to 10.5% | +0.0285 |
| E1 p=0.15 | 11.3% | 1.8 | 8.2% to 15.4% | +0.0257 |
| E1 p=0.20 | 12.7% | 1.9 | 9.4% to 16.9% | +0.0243 |
| E1 p=0.25 | 18.3% | 2.2 | 14.4% to 23.1% | +0.0210 |
| E1 p=0.30 | 22.3% | 2.4 | 18.0% to 27.4% | +0.0188 |
| E1 p=0.35 | 30.0% | 2.6 | 25.1% to 35.4% | +0.0147 |
| E1 p=0.40 | 39.0% | 2.8 | 33.7% to 44.6% | +0.0095 |
| E1 p=0.45 | 41.3% | 2.8 | 35.9% to 47.0% | +0.0085 |
| E1 p=0.50 | 43.3% | 2.9 | 37.8% to 49.0% | +0.0075 |
| E2 p=0.10 rho=0.25 | 7.7% | 1.5 | 5.2% to 11.2% | +0.0285 |
| E2 p=0.10 rho=0.50 | 8.0% | 1.6 | 5.4% to 11.6% | +0.0298 |
| E2 p=0.10 rho=0.75 | 8.7% | 1.6 | 6.0% to 12.4% | +0.0289 |
| E2 p=0.10 rho=1.00 | 12.0% | 1.9 | 8.8% to 16.2% | +0.0277 |
| E2 p=0.25 rho=0.25 | 22.7% | 2.4 | 18.3% to 27.7% | +0.0199 |
| E2 p=0.25 rho=0.50 | 25.7% | 2.5 | 21.1% to 30.9% | +0.0179 |
| E2 p=0.25 rho=0.75 | 25.7% | 2.5 | 21.1% to 30.9% | +0.0184 |
| E2 p=0.25 rho=1.00 | 22.7% | 2.4 | 18.3% to 27.7% | +0.0216 |
| E2 p=0.40 rho=0.25 | 38.3% | 2.8 | 33.0% to 43.9% | +0.0099 |
| E2 p=0.40 rho=0.50 | 40.7% | 2.8 | 35.3% to 46.3% | +0.0094 |
| E2 p=0.40 rho=0.75 | 40.7% | 2.8 | 35.3% to 46.3% | +0.0109 |
| E2 p=0.40 rho=1.00 | 40.3% | 2.8 | 34.9% to 46.0% | +0.0104 |
| E3 exactly 0 of 4 fail | 0.0% | 0.0 | 0.0% to 1.3% | +0.0346 |
| E3 exactly 1 of 4 fail | 16.7% | 2.2 | 12.9% to 21.3% | +0.0200 |
| E3 exactly 2 of 4 fail | 43.3% | 2.9 | 37.8% to 49.0% | +0.0057 |
| E3 exactly 3 of 4 fail | 70.0% | 2.6 | 64.6% to 74.9% | -0.0075 |
| E3 exactly 4 of 4 fail | 100.0% | 0.0 | 98.7% to 100.0% | -0.0232 |
| E3 only SC_AutoVerify fails | 0.0% | 0.0 | 0.0% to 1.3% | +0.0352 |
| E3 only SC_RuleExec fails | 0.0% | 0.0 | 0.0% to 1.3% | +0.0287 |
| E3 only SC_DisputeWF fails | 62.3% | 2.8 | 56.7% to 67.6% | -0.0033 |
| E3 only SC_Transparency fails | 0.0% | 0.0 | 0.0% to 1.3% | +0.0217 |
| E3 only SC_AutoVerify+SC_RuleExec fail | 0.0% | 0.0 | 0.0% to 1.3% | +0.0282 |
| E3 only SC_AutoVerify+SC_DisputeWF fail | 64.7% | 2.8 | 59.1% to 69.9% | -0.0036 |
| E3 only SC_AutoVerify+SC_Transparency fail | 0.0% | 0.0 | 0.0% to 1.3% | +0.0216 |
| E3 only SC_RuleExec+SC_DisputeWF fail | 87.3% | 1.9 | 83.1% to 90.6% | -0.0089 |
| E3 only SC_RuleExec+SC_Transparency fail | 0.0% | 0.0 | 0.0% to 1.3% | +0.0161 |
| E3 only SC_DisputeWF+SC_Transparency fail | 100.0% | 0.0 | 98.7% to 100.0% | -0.0174 |
| E4 symmetric p=0.10 | 10.3% | 1.8 | 7.4% to 14.3% | +0.0252 |
| E4 symmetric p=0.25 | 26.7% | 2.6 | 22.0% to 31.9% | +0.0111 |
| E4 symmetric p=0.40 | 45.3% | 2.9 | 39.8% to 51.0% | -0.0060 |

Note. E1 independent failure with probability p; E2 correlated failure via a shared implementation-quality factor (Gaussian copula, correlation rho); E3 exactly k mechanisms fail, or the named mechanisms fail; E4 adverse magnitudes mirror the beneficial ranges. These rates describe the specified scenarios and are not estimates of real-world failure rates.

Table C6. Smart contracts compared with conventional workflow automation (horizon-mean RI). Activation levels for AutoVerify (AV), RuleExec (RE), DisputeWF (DW) and Transparency (TP).

| Configuration | AV | RE | DW | TP | RI | dRI vs No-SC | Share of Full-SC gain |
|---|---|---|---|---|---|---|---|
| No-SC (traditional) | 0.0 | 0.0 | 0.0 | 0.0 | 0.4836 | +0.0000 | 0% |
| Workflow, conservative | 0.5 | 0.5 | 0.0 | 0.0 | 0.4857 | +0.0022 | 6% |
| Workflow, standard | 0.75 | 0.75 | 0.0 | 0.25 | 0.4892 | +0.0056 | 16% |
| Workflow, generous | 1.0 | 1.0 | 0.25 | 0.5 | 0.4994 | +0.0158 | 45% |
| Full-SC | 1.0 | 1.0 | 1.0 | 1.0 | 0.5188 | +0.0352 | 100% |
