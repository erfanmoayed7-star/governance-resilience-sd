# Smart Contracts and Project Governance Resilience: System Dynamics Model

Replication materials for the manuscript JPMA-D-26-00601 (International Journal of Project Management), Moayyed, Castelblanco and Anumba.

## Contents
- `model/governance_system_dynamics.py`: stock-and-flow model (11 stocks), validation tests 1 to 9, Monte Carlo (beneficial and adverse implementation).
- `model/data_inputs.py`: construction of the Material Cost Exposure (MCE) and Lead Time Exposure (LTE) indices.
- `data/`: input workbooks (CBS weights; material lead times).
- `results/`: logged outputs for each run, by revision round.
- `analyses/`: additional analyses for the second revision.

## Reproducing
```
pip install -r requirements.txt
cd results/<run> && python ../../model/governance_system_dynamics.py
```
Solver: SciPy `solve_ivp`, RK45, rtol 1e-6, atol 1e-8, max_step 0.5. Time unit: weeks. Monte Carlo: N = 300, seed 42.

## Status
Work in progress for the second revision round. A versioned release with a DOI will be archived on Zenodo before resubmission.
