"""Write the processed model inputs to data/processed/ from the source workbooks.

  mce_lte_weekly.csv        weekly Material Cost Exposure and Lead-Time Exposure (raw and normalized)
  cbs_material_weights.csv  material weights from the office-building cost breakdown structure
  ppi_yoy_annual.csv        BLS Producer Price Index year-over-year changes used for MCE, with series IDs
  lead_times_weekly.csv     per-material lead times (weeks) interpolated to the weekly axis

With these files the model reproduces every result without the source workbooks
(data_inputs.py uses them automatically when the workbooks are absent).
Values are written with full float precision (repr) so results are identical.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "model"))
import data_inputs as d  # noqa: E402

OUT = os.path.join(HERE, "..", "data", "processed")
SERIES = {"concrete": ("WPU1333", "Ready-mixed concrete"),
          "rebar_steel": ("WPU1074051", "Fabricated structural metal bar joists and rebar"),
          "glass": ("WPU1311", "Flat glass"),
          "lumber": ("WPUSI004011", "Lumber and plywood"),
          "gypsum": ("WPU13710102", "Gypsum building materials"),
          "asphalt": ("WPU1394", "Paving mixtures and blocks")}


def main():
    if d.USE_PROCESSED:
        sys.exit("Source workbooks not found; processed inputs can only be exported from them.")
    os.makedirs(OUT, exist_ok=True)
    t, mce_raw, mce_norm, lte_raw, lte_norm, w = d.build_mce_lte(t_weeks=52)
    with open(os.path.join(OUT, "mce_lte_weekly.csv"), "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["week", "mce_raw", "mce_norm", "lte_raw", "lte_norm"])
        for row in zip(t, mce_raw, mce_norm, lte_raw, lte_norm):
            wr.writerow([repr(float(x)) for x in row])
    with open(os.path.join(OUT, "cbs_material_weights.csv"), "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["material", "weight"])
        for m, v in w.items():
            wr.writerow([m, repr(float(v))])
    import inspect, re, ast
    src = inspect.getsource(d.build_mce_lte)
    ppi = ast.literal_eval(re.search(r"REAL_PPI_YOY_PCT = (\{.*?\})", src, re.S).group(1))
    with open(os.path.join(OUT, "ppi_yoy_annual.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["material", "bls_series_id", "series_title", "2020", "2021", "2022", "2023", "2024", "2025_partial"])
        for m, vals in ppi.items():
            wr.writerow([m, *SERIES[m], *vals])
    lt = d.load_lead_times_series(d.LEAD_TIMES_EXCEL_PATH)
    mats = list(lt)
    n = max(len(v) for v in lt.values())
    with open(os.path.join(OUT, "lead_times_weekly.csv"), "w", newline="") as f:
        wr = csv.writer(f); wr.writerow(["week"] + mats)
        for k in range(n):
            wr.writerow([k] + [repr(float(lt[m][min(k, len(lt[m]) - 1)])) for m in mats])
    print("wrote", sorted(os.listdir(OUT)))


if __name__ == "__main__":
    main()
