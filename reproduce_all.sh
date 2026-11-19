#!/usr/bin/env bash
# Regenerate every table, figure and appendix of the paper from the model code.
# Runtime: about 30 to 60 minutes on a laptop (the Monte Carlo sweeps dominate).
set -euo pipefail
cd "$(dirname "$0")"
( mkdir -p results/round3_midpoint && cd results/round3_midpoint && python ../../model/governance_system_dynamics.py > main_log.txt )
cd analyses
python headline_numbers.py            # Section 4.2 headline values
python a1_adverse_sweep.py            # Table C5, Figure 5
python a2_direct_channel_sweep.py     # Section 4.3 direct-channel sweep, Table C4
python a3_workflow_comparator.py      # Table C6
python a4_weighting_and_sensitivity.py  # Tables C2 and C3
python a5_convergence.py              # Table C4 (convergence)
python a7_methods_claims.py           # 8-parameter Monte Carlo, second rival specification
python loop_impact.py                 # Figure 3, Panel A
python results_section.py             # Tables 4 and 5, Figures 2 to 5
python fig3_two_panel.py              # Figure 3 (two panels)
python build_appendix.py              # Appendices A and C
