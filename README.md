# Smart Contracts and Project Governance Resilience: System Dynamics Model

Replication materials for Moayyed, Castelblanco and Anumba, "When Does Code Make Project Governance
Resilient? A Sociotechnical System Dynamics Study of Smart Contracts under Macroeconomic Volatility",
*International Journal of Project Management* (manuscript JPMA-D-26-00601).

## Contents
| Path | Contents |
|---|---|
| `model/governance_system_dynamics.py` | Stock-and-flow model (eleven stocks), validation tests, beneficial and adverse Monte Carlo |
| `model/data_inputs.py` | Construction of the Material Cost Exposure (MCE) and Lead-Time Exposure (LTE) indices |
| `data/processed/` | Exact model inputs (see `data/README.md` for sources) |
| `analyses/` | One script per analysis reported in the paper |
| `results/` | Logged outputs of every script, as used in the paper |
| `figures/` | Vensim source of Figure 1 (causal loop diagram) |

## Installation
Python 3.13 with the pinned packages:
```
pip install -r requirements.txt
```

## Reproducing the paper
Run everything with `./reproduce_all.sh` (about 30 to 60 minutes), or individual scripts from `analyses/`:

| Paper element | Script | Output in `results/` |
|---|---|---|
| Section 4.2 headline values (loss, gain, share recovered) | `headline_numbers.py` | `headline/` |
| Table 4 (area between curves), Table 5 (8-parameter Monte Carlo), Figures 2, 4 and 5 | `results_section.py` | `section4/` |
| Figure 3 (loop impact and parameter attribution) | `loop_impact.py`, then `fig3_two_panel.py` | `loop_impact/`, `section4/fig3.png` |
| Adverse-implementation sweep (Table C5, Figure 5) | `a1_adverse_sweep.py` | `a1_adverse_sweep/` |
| Direct-channel sweep (Section 4.3) | `a2_direct_channel_sweep.py` | `a2_direct_channel_sweep/` |
| Comparison with workflow automation (Table C6) | `a3_workflow_comparator.py` | `a3_workflow_comparator/` |
| Weighting schemes and one-at-a-time sensitivity (Tables C2, C3) | `a4_weighting_and_sensitivity.py` | `a4_weighting_and_sensitivity/` |
| Convergence check (Table C4) | `a5_convergence.py` | `a5_convergence/` |
| Joint 8-parameter Monte Carlo and second rival specification | `a7_methods_claims.py` | `a7_methods_claims/` |
| Validation tests (Table C1) | `model/governance_system_dynamics.py` | `round3_midpoint/` |
| Appendices A and C (generated from the code) | `build_appendix.py` | `appendix/` |

## Settings
SciPy `solve_ivp`, RK45, relative tolerance 1e-6, absolute tolerance 1e-8, maximum step 0.5 weeks.
Time unit: weeks; horizon 52 weeks. Monte Carlo: N = 300, seed 42 (per-condition seeds are set in each script).
Principal resilience measure: mean Resilience Index over the 52-week horizon; terminal (week 52) values are reported alongside.

`results/round2_baseline/` holds the outputs of the model as submitted in the previous revision round, for reference.

## License
Code: MIT (see `LICENSE`). Processed data: CC BY 4.0.

## Citation
See `CITATION.cff`.
