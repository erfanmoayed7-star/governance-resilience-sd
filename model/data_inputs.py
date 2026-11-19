"""
Data-driven exogenous inputs for the governance SD model.

Builds MCE(t) [Material Cost Exposure] and LTE(t) [Lead Time Exposure] from:
- CBS Office.xlsx: cost breakdown / material composition weights
- Lead Times Material Dec 2025.xlsx: lead time time series per material
- Office_3.pdf: baseline schedule/procurement (optional; fallback to config)

Time unit: WEEKS. Simulation axis t = 0..T with dt=1 (weekly), T=52 (1 year) by default.
All time series are defined on integer week indices; model uses interpolation for t in between.

Usage:
  from data_inputs import build_mce_lte, get_exogenous_from_data
"""

from __future__ import annotations

import os
import re
import logging
import warnings
from typing import Dict, List, Tuple, Optional, Any

import numpy as np

# Optional dependencies (graceful fallback)
try:
    import pandas as pd
except ImportError:
    pd = None
try:
    import openpyxl
except ImportError:
    openpyxl = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION (paths and fallbacks)
# =============================================================================

# Default data directory: same folder as this script, or project root
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Search order: IJPM_DATA_DIR env var, ./data next to this script,
# ../data (repository layout), then this script's folder.
_CANDIDATES = [os.environ.get("IJPM_DATA_DIR", ""),
               os.path.join(_SCRIPT_DIR, "data"),
               os.path.join(_SCRIPT_DIR, "..", "data"),
               _SCRIPT_DIR]
DATA_DIR = next((d for d in _CANDIDATES
                 if d and os.path.isfile(os.path.join(d, "CBS Office.xlsx"))), None)
# Processed inputs (data/processed/mce_lte_weekly.csv) reproduce the paper exactly
# without the source workbooks; they are written by analyses/export_processed_inputs.py.
PROCESSED_PATH = next((os.path.abspath(os.path.join(d, "processed", "mce_lte_weekly.csv"))
                       for d in _CANDIDATES
                       if d and os.path.isfile(os.path.join(d, "processed", "mce_lte_weekly.csv"))), None)
USE_PROCESSED = DATA_DIR is None or os.environ.get("IJPM_USE_PROCESSED") == "1"
if USE_PROCESSED and PROCESSED_PATH is None:
    raise FileNotFoundError(
        "Input data not found. Provide data/processed/mce_lte_weekly.csv, or place "
        "'CBS Office.xlsx' and 'Lead Times Material Dec 2025.xlsx' in data/ "
        "(or set IJPM_DATA_DIR). See data/README.md.")
DATA_DIR = os.path.abspath(DATA_DIR) if DATA_DIR else os.path.dirname(os.path.dirname(PROCESSED_PATH))

CBS_EXCEL_PATH = os.path.join(DATA_DIR, "CBS Office.xlsx")
LEAD_TIMES_EXCEL_PATH = os.path.join(DATA_DIR, "Lead Times Material Dec 2025.xlsx")
OFFICE_PDF_PATH = os.path.join(DATA_DIR, "Office_3.pdf")

# Time axis: weeks. T=52 (1 year), dt=1.
TIME_UNIT = "weeks"
DEFAULT_T_WEEKS = 52
DEFAULT_DT = 1

# TODO: User can fill baseline procurement/schedule durations (weeks) if PDF parsing fails.
# Used only when PDF is not available or parsing fails.
BASELINE_DURATIONS_WEEKS: Dict[str, float] = {
    "concrete": 4.0,
    "rebar_steel": 6.0,
    "glass": 8.0,
    "lumber": 4.0,
    "gypsum": 3.0,
    "asphalt": 2.0,
}

# Material name normalization (map sheet/column names to canonical keys)
MATERIAL_ALIASES = {
    "concrete": ["concrete", "cement", "beton"],
    "rebar_steel": ["rebar", "steel", "reinforcement", "stahl"],
    "glass": ["glass", "glas"],
    "lumber": ["lumber", "wood", "timber", "holz"],
    "gypsum": ["gypsum", "gips", "drywall"],
    "asphalt": ["asphalt", "bitumen"],
}


def _normalize_header(s: Any) -> str:
    if pd is not None and isinstance(s, str):
        return s.strip().casefold()
    return str(s).strip().casefold() if s is not None else ""


def _match_material(col_name: str) -> Optional[str]:
    col = _normalize_header(col_name)
    for canonical, aliases in MATERIAL_ALIASES.items():
        if any(a in col for a in aliases):
            return canonical
    return None


# =============================================================================
# LOAD CBS OFFICE.XLSX (cost breakdown / material weights)
# =============================================================================

def load_cbs_material_weights(path: str = CBS_EXCEL_PATH) -> Dict[str, float]:
    """
    Parse cost breakdown and derive material exposure weights.
    Returns dict mapping canonical material name -> weight (sum = 1.0).
    """
    if pd is None or openpyxl is None:
        logger.warning("pandas or openpyxl not available; using equal weights.")
        return {k: 1.0 / 6 for k in MATERIAL_ALIASES}

    if not os.path.isfile(path):
        logger.warning("CBS file not found: %s. Using equal material weights.", path)
        return {k: 1.0 / 6 for k in MATERIAL_ALIASES}

    try:
        xl = pd.ExcelFile(path)
        best_sheet = None
        best_size = 0
        for sheet in xl.sheet_names:
            df = pd.read_excel(xl, sheet_name=sheet, header=None)
            if df.size > best_size:
                # Prefer sheet with "material" or "cost" in header
                first_rows = " ".join(str(x).casefold() for x in df.iloc[:3].values.ravel())
                if "material" in first_rows or "cost" in first_rows or "composition" in first_rows:
                    best_sheet = sheet
                    best_size = df.size
        if best_sheet is None and len(xl.sheet_names) > 0:
            best_sheet = xl.sheet_names[0]

        if best_sheet is None:
            return {k: 1.0 / 6 for k in MATERIAL_ALIASES}

        # FIXED: was pd.read_excel(xl, sheet_name=best_sheet) with default
        # header=0, which takes row 0 (mostly NaN building-metadata text like
        # "Building Type: Office, 2-4 Story") as the column headers. The
        # actual material category columns (Aluminum, Asphalt, Concrete,
        # Glass, Gypsum, Rebar, Lumber & Plywood, etc.) are in row 1. This
        # caused only one column to spuriously match a material name,
        # producing a degenerate {'concrete': 1.0} weighting instead of a
        # genuine cost-weighted composite across all six categories.
        df = pd.read_excel(xl, sheet_name=best_sheet, header=1)
        df.columns = [_normalize_header(c) for c in df.columns]
        weights: Dict[str, float] = {}
        for col in df.columns:
            mat = _match_material(col)
            if mat is None:
                continue
            try:
                vals = pd.to_numeric(df[col], errors="coerce").dropna()
                if len(vals) > 0:
                    weights[mat] = weights.get(mat, 0) + float(vals.abs().sum())
            except Exception:
                pass

        if not weights:
            # Try first row as header and look for numeric columns with material-like names
            for col in df.columns:
                mat = _match_material(col)
                if mat and col not in weights:
                    weights[mat] = 1.0

        if not weights:
            logger.warning("No material columns detected in CBS; using equal weights.")
            return {k: 1.0 / 6 for k in MATERIAL_ALIASES}

        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    except Exception as e:
        logger.warning("CBS parse failed: %s. Using equal weights.", e)
        return {k: 1.0 / 6 for k in MATERIAL_ALIASES}


# =============================================================================
# LOAD LEAD TIMES MATERIAL DEC 2025.XLSX
# =============================================================================

def load_lead_times_series(path: str = LEAD_TIMES_EXCEL_PATH) -> Dict[str, np.ndarray]:
    """
    Parse lead time time series per material.

    FIXED (was previously silently falling back to synthetic data for all
    runs, including whichever run originally generated the manuscript's
    reported 13.7%/9.7% figures -- confirmed via direct inspection that the
    actual file layout is ROW-oriented: materials in column A (24 granular
    categories, e.g. "Rebar", "Steel Beams", "Aluminum"), with quarterly
    "Average" lead-time-in-weeks values across columns (Prior Quarter
    Prediction through Dec 2025). The previous parser assumed the opposite
    layout (materials as column headers), so every column-name match against
    MATERIAL_ALIASES failed silently and the synthetic fallback fired.

    Materials are mapped down into the SAME 6 canonical categories used by
    load_cbs_material_weights (concrete, rebar_steel, glass, lumber, gypsum,
    asphalt), consistent with the manuscript's stated methodology that LTE
    applies "identical CBS-derived weights" to the same material categories
    as MCE. Where multiple granular materials map to one canonical category
    (e.g. Rebar, Steel Beams, Steel Decking, Steel Joist, Steel Piping &
    Tube, and Steel Studs all map to "rebar_steel"), their quarterly values
    are averaged.

    Returns dict: canonical material -> array of lead times in weeks,
    ordered chronologically (Prior Quarter Prediction, then quarterly
    averages June 2024 through Dec 2025 -- the last confirmed actual
    figure; the Jun 2026 column is a forward projection and excluded).
    """
    if pd is None or openpyxl is None:
        logger.warning("pandas/openpyxl not available; using synthetic lead time series.")
        return _synthetic_lead_times()

    if not os.path.isfile(path):
        logger.warning("Lead times file not found: %s. Using synthetic series.", path)
        return _synthetic_lead_times()

    try:
        wb = openpyxl.load_workbook(path, data_only=True)
        ws = wb[wb.sheetnames[0]]

        # Time-ordered "Average"/actual columns identified by direct inspection
        # of the file (1-indexed openpyxl column numbers):
        # 3=Prior Quarter Prediction, 5=June 2024 Avg, 8=Sept 2024 Avg,
        # 12=Dec 2024 Avg, 16=March 2025 Avg, 20=June 2025 Avg, 24=Sep 2025 Avg,
        # 28=Dec 2025 LT WEEKS (last confirmed actual; Jun 2026 excluded as forecast)
        time_cols = [3, 5, 8, 12, 16, 20, 24, 28]

        rows_by_canonical: Dict[str, list] = {}
        for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
            mat_name = row[0].value
            if mat_name is None or not isinstance(mat_name, str):
                continue
            canonical = _match_material(mat_name)
            if canonical is None:
                continue
            vals = []
            for c in time_cols:
                if c - 1 < len(row):
                    v = row[c - 1].value
                    vals.append(v if isinstance(v, (int, float)) else np.nan)
                else:
                    vals.append(np.nan)
            rows_by_canonical.setdefault(canonical, []).append(vals)

        series: Dict[str, np.ndarray] = {}
        for canonical, rows in rows_by_canonical.items():
            arr = np.array(rows, dtype=float)  # shape (n_materials_in_category, n_timepoints)
            with np.errstate(invalid='ignore'):
                avg = np.nanmean(arr, axis=0)
            if np.all(np.isnan(avg)):
                continue
            # Forward-fill any remaining NaN gaps, then drop leading/trailing NaN
            valid = ~np.isnan(avg)
            if not valid.any():
                continue
            avg = avg[valid.argmax():]  # trim leading NaN
            series[canonical] = avg

        if not series:
            logger.warning("No material lead time rows matched after row-oriented parse; using synthetic.")
            return _synthetic_lead_times()

        logger.info("Lead times loaded from %s: %d canonical materials matched (%s)",
                    path, len(series), list(series.keys()))
        return series
    except Exception as e:
        logger.warning("Lead times parse failed: %s. Using synthetic.", e)
        return _synthetic_lead_times()


def _synthetic_lead_times(n_weeks: int = 52) -> Dict[str, np.ndarray]:
    """Synthetic lead time series (weeks) for testing when data missing."""
    np.random.seed(42)
    out = {}
    for mat in MATERIAL_ALIASES:
        base = BASELINE_DURATIONS_WEEKS.get(mat, 5.0)
        # Random walk around base
        x = np.cumsum(np.random.randn(n_weeks) * 0.3) + base
        x = np.clip(x, 0.5, 20.0)
        out[mat] = x
    return out


# =============================================================================
# OFFICE_3.PDF (baseline durations fallback)
# =============================================================================

def load_baseline_durations_from_pdf(path: str = OFFICE_PDF_PATH) -> Optional[Dict[str, float]]:
    """Extract baseline schedule/procurement durations from PDF if possible."""
    if not os.path.isfile(path):
        return None
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        # Heuristic: look for numbers followed by "week" or "day"
        durations = {}
        for mat in MATERIAL_ALIASES:
            durations[mat] = BASELINE_DURATIONS_WEEKS.get(mat, 5.0)
        # Simple pattern: "X weeks" or "X week"
        for m in re.finditer(r"(\d+(?:\.\d+)?)\s*weeks?", text.casefold()):
            pass  # Could map to materials if table structure known
        return durations
    except ImportError:
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                text = ""
                for p in pdf.pages:
                    if p.extract_text():
                        text += p.extract_text()
            return BASELINE_DURATIONS_WEEKS.copy()
        except ImportError:
            pass
    except Exception as e:
        logger.warning("PDF parsing failed: %s. Use BASELINE_DURATIONS_WEEKS.", e)
    return None


def _load_processed(T, scale_stress=1.0):
    """Read the processed weekly indices and CBS weights (exact values used in the paper)."""
    import csv
    rows = list(csv.DictReader(open(PROCESSED_PATH)))
    if len(rows) != T:
        raise ValueError(f"Processed inputs have {len(rows)} weeks; {T} requested.")
    col = lambda k: np.array([float(r[k]) for r in rows])
    mce_raw, lte_raw = col("mce_raw") * scale_stress, col("lte_raw") * scale_stress
    norm = lambda x: np.zeros_like(x) if x.max() - x.min() < 1e-10 else (x - x.min()) / (x.max() - x.min())
    wpath = os.path.join(os.path.dirname(PROCESSED_PATH), "cbs_material_weights.csv")
    weights = {r["material"]: float(r["weight"]) for r in csv.DictReader(open(wpath))} if os.path.isfile(wpath) else {}
    logger.info("Using processed inputs: %s", PROCESSED_PATH)
    return col("week"), mce_raw, norm(mce_raw), lte_raw, norm(lte_raw), weights


# =============================================================================
# BUILD MCE(t) AND LTE(t)
# =============================================================================

def build_mce_lte(
    t_weeks: Optional[int] = None,
    cbs_path: str = CBS_EXCEL_PATH,
    lead_times_path: str = LEAD_TIMES_EXCEL_PATH,
    scale_stress: float = 1.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, float]]:
    """
    Build MCE and LTE time series (raw and normalized) on weekly time axis.

    Time unit: weeks. t = 0, 1, ..., T-1 with T = t_weeks (default 52).

    MCE(t) = sum_i w_i * price_index_i(t).
    If no cost/price columns in CBS, price proxy = f(lead_time_deviation) (scarcity proxy).
    LTE(t) = sum_i w_i * lead_time_deviation_i(t) (deviation from baseline, e.g. first 12 weeks avg).

    Returns:
        t_axis: 1D array of week indices (0..T-1)
        mce_raw: MCE in engineering units
        mce_norm: MCE normalized to [0, 1] (min-max or logistic)
        lte_raw: LTE in engineering units
        lte_norm: LTE normalized to [0, 1]
        weights: material weights used (for logging)
    """
    T = t_weeks or DEFAULT_T_WEEKS
    t_axis = np.arange(T, dtype=float)

    if USE_PROCESSED:
        return _load_processed(T, scale_stress)

    weights = load_cbs_material_weights(cbs_path)
    lt_series = load_lead_times_series(lead_times_path)

    # Align to T weeks: if lead time series longer, trim; if shorter, pad with last value
    materials = list(weights.keys())
    if not materials:
        materials = list(MATERIAL_ALIASES.keys())
        weights = {m: 1.0 / len(materials) for m in materials}

    lead_times_aligned: Dict[str, np.ndarray] = {}
    baselines: Dict[str, float] = {}
    for m in materials:
        if m in lt_series:
            arr = lt_series[m]
        else:
            arr = _synthetic_lead_times(T).get(m, np.full(T, 5.0))
        arr = np.asarray(arr, dtype=float)
        if len(arr) > T:
            arr = arr[:T]
        elif len(arr) < T and len(arr) > 1:
            # FIXED: was np.resize(arr, T), which cyclically TILES a short
            # array (e.g. 8 real quarterly lead-time observations) to fill
            # T=52 weekly slots, producing a repeating sawtooth artifact with
            # no relationship to actual elapsed time. Correct approach:
            # linearly interpolate the N real observations, assumed evenly
            # spaced across the observation window, onto the T-week axis.
            src_x = np.linspace(0, T - 1, num=len(arr))
            dst_x = np.arange(T, dtype=float)
            arr = np.interp(dst_x, src_x, arr)
        elif len(arr) == 1:
            arr = np.full(T, arr[0])
        lead_times_aligned[m] = arr
        # Baseline = first 12 weeks (or first 3 months) average
        n_baseline = min(12, len(arr))
        baselines[m] = float(np.mean(arr[:n_baseline]))

    # LTE(t) = weighted sum of (lead_time_i(t) - baseline_i) normalized per material then weighted
    lte_raw = np.zeros(T)
    for m in materials:
        w = weights.get(m, 0.0)
        if w <= 0:
            continue
        dev = lead_times_aligned[m] - baselines[m]
        # Relative deviation (avoid div by zero)
        scale = baselines[m] if baselines[m] > 0.1 else 1.0
        lte_raw += w * (dev / scale)
    lte_raw *= scale_stress

    # MCE(t): FIXED. Was previously a proxy derived from the same lead-time
    # deviation data used for LTE (price_index_proxy_i(t) = 1 + lead_time
    # deviation), meaning MCE and LTE were mathematically dependent rather
    # than independently varying pressures as the manuscript claims (r=1.0
    # confirmed empirically). Replaced with genuine Producer Price Index
    # data from the U.S. Bureau of Labor Statistics (via the Associated
    # General Contractors of America's published PPI compilation,
    # https://www.agc.org/sites/default/files/users/user21902/PPI%20Tables%202025_07.pdf,
    # updated 8/14/2025, sourced from www.bls.gov/ppi), covering annual
    # year-over-year percentage change 2020-2025 (partial) for the six CBS
    # material categories:
    #   concrete    -> WPU1333  Ready-mixed concrete
    #   rebar_steel -> WPU1074051 Fabricated structural metal bar joists & rebar
    #   glass       -> WPU1311  Flat glass
    #   lumber      -> WPUSI004011 Lumber and plywood
    #   gypsum      -> WPU13710102 Gypsum building materials
    #   asphalt     -> WPU1394  Paving mixtures and blocks (asphalt)
    # Six annual observations per material (2020, 2021, 2022, 2023, 2024,
    # partial-2025) are linearly interpolated onto the 52-week axis (same
    # method as the corrected Lead Times interpolation) and CBS-weighted.
    REAL_PPI_YOY_PCT = {
        'concrete':    [2.6, 3.8, 10.3, 11.1, 5.8, -0.5],
        'rebar_steel': [0.2, 34.2, 24.7, 0.5, -17.3, -0.5],
        'glass':       [1.5, 5.3, 10.3, 5.8, 1.2, 3.1],
        'lumber':      [17.0, 41.1, -0.8, -23.1, -1.7, -0.8],
        'gypsum':      [0.1, 18.1, 19.9, 4.0, 3.0, 0.0],
        'asphalt':     [-3.0, 3.6, 16.7, 4.5, 2.5, 0.2],
    }
    mce_raw = np.zeros(T)
    src_x_annual = np.linspace(0, T - 1, num=6)  # 6 annual points spread across the observation window
    dst_x = np.arange(T, dtype=float)
    for m in materials:
        w = weights.get(m, 0.0)
        if w <= 0 or m not in REAL_PPI_YOY_PCT:
            continue
        series_annual = np.array(REAL_PPI_YOY_PCT[m], dtype=float)
        series_weekly = np.interp(dst_x, src_x_annual, series_annual)
        mce_raw += w * series_weekly
    mce_raw *= scale_stress

    # Normalize to [0, 1]: min-max
    def min_max_norm(x: np.ndarray) -> np.ndarray:
        mn = np.min(x)
        mx = np.max(x)
        if mx - mn < 1e-10:
            return np.zeros_like(x)
        return (x - mn) / (mx - mn)

    mce_norm = min_max_norm(mce_raw)
    lte_norm = min_max_norm(lte_raw)

    return t_axis, mce_raw, mce_norm, lte_raw, lte_norm, weights


# =============================================================================
# EXOGENOUS CALLABLES FOR THE SD MODEL
# =============================================================================

def get_exogenous_from_data(
    t_axis: np.ndarray,
    mce_norm: np.ndarray,
    lte_norm: np.ndarray,
    scenario: str = "data",
    scale: float = 1.0,
) -> Dict[str, Any]:
    """
    Return exogenous dict for the governance model: MCE(t) and LTE(t) as callables.
    Model time t is in weeks; we interpolate from t_axis, mce_norm, lte_norm.
    """
    if scenario == "baseline":
        return {
            "MCE": lambda t: 0.0,
            "LTE": lambda t: 0.0,
            "t_axis": t_axis,
            "mce_raw": np.zeros_like(t_axis),
            "mce_norm": np.zeros_like(t_axis),
            "lte_raw": np.zeros_like(t_axis),
            "lte_norm": np.zeros_like(t_axis),
        }

    def interp(t: float, axis: np.ndarray, vals: np.ndarray) -> float:
        if axis.size == 0:
            return 0.0
        if t <= axis[0]:
            return float(vals[0])
        if t >= axis[-1]:
            return float(vals[-1])
        return float(np.interp(t, axis, vals))

    mce_norm_scaled = np.clip(mce_norm * scale, 0.0, 1.0)
    lte_norm_scaled = np.clip(lte_norm * scale, 0.0, 1.0)

    return {
        "MCE": lambda t: interp(t, t_axis, mce_norm_scaled),
        "LTE": lambda t: interp(t, t_axis, lte_norm_scaled),
        "t_axis": t_axis,
        "mce_raw": mce_norm * 0,  # placeholder; pass from build if needed
        "mce_norm": mce_norm_scaled,
        "lte_raw": lte_norm * 0,
        "lte_norm": lte_norm_scaled,
    }


def get_data_driven_exogenous(
    scenario: str = "data",
    t_weeks: int = 52,
    scale_stress: float = 1.0,
) -> Tuple[Dict[str, Any], Dict[str, np.ndarray]]:
    """
    Build data-driven MCE/LTE and return exogenous dict + series for plotting.
    scenario: "baseline" (zeros), "data" (from files or synthetic), "data_stressed" (scale 1.3).
    """
    if scenario == "baseline":
        t_axis = np.arange(t_weeks)
        exo = get_exogenous_from_data(t_axis, np.zeros(t_weeks), np.zeros(t_weeks), "baseline")
        series = {"t": t_axis, "mce_raw": np.zeros(t_weeks), "mce_norm": np.zeros(t_weeks),
                  "lte_raw": np.zeros(t_weeks), "lte_norm": np.zeros(t_weeks)}
        return exo, series

    t_axis, mce_raw, mce_norm, lte_raw, lte_norm, _ = build_mce_lte(
        t_weeks=t_weeks, scale_stress=scale_stress
    )
    scale = 1.3 if scenario == "data_stressed" else 1.0
    exo = get_exogenous_from_data(t_axis, mce_norm, lte_norm, "data", scale)
    series = {
        "t": t_axis,
        "mce_raw": mce_raw,
        "mce_norm": exo["mce_norm"],
        "lte_raw": lte_raw,
        "lte_norm": exo["lte_norm"],
    }
    return exo, series
