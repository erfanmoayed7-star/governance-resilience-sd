"""Shared resilience measures.

Primary: horizon-mean RI, the average of RI over the 52-week simulation.
Secondary: terminal RI at week 52.
The horizon mean is primary because the data-driven exposure series do not
settle by week 52 (MCE returns to zero, LTE ends at its maximum), so a
terminal value depends on where the series happens to end.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import governance_system_dynamics as g  # noqa: E402
import data_inputs as di  # noqa: E402


def data_exogenous():
    exo, _ = di.get_data_driven_exogenous("data", t_weeks=g.DEFAULT_T_WEEKS, scale_stress=1.0)
    return exo


def zero_exogenous(exo):
    """Same time axis as the data scenario, with no exposure (undisturbed baseline)."""
    return {**exo, "MCE": lambda t: 0.0, "LTE": lambda t: 0.0}


def ri_measures(params, policy, exo):
    """Return {'mean': horizon-mean RI, 'terminal': RI at week 52}."""
    out = g.run_simulation(params, policy, "data", exogenous_override=exo)[2]
    return {"mean": float(sum(o["RI"] for o in out) / len(out)), "terminal": float(out[-1]["RI"])}
