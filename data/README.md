# Input data

## Included: `processed/`
These files are the exact inputs used for every result in the paper. The model reads them
automatically when the source workbooks are absent, and reproduces all reported values
identically (checked against the outputs in `results/`).

| File | Contents |
|---|---|
| `mce_lte_weekly.csv` | Material Cost Exposure (MCE) and Lead-Time Exposure (LTE) for weeks 0 to 51, raw and min-max normalized. The normalized columns are the model's exogenous inputs. |
| `cbs_material_weights.csv` | Material weights derived from the cost breakdown structure of a 2 to 4 story commercial office building. |
| `ppi_yoy_annual.csv` | Year-over-year change (%) in the U.S. Bureau of Labor Statistics Producer Price Index for each material, 2020 to 2025 (partial), with BLS series identifiers. |
| `lead_times_weekly.csv` | Per-material procurement lead times (weeks) interpolated onto the weekly axis. |

## Sources
- **Producer Price Index (public domain).** U.S. Bureau of Labor Statistics, retrieved via the Federal
  Reserve Economic Data database (https://fred.stlouisfed.org): WPU1333 (ready-mixed concrete),
  WPU1074051 (fabricated structural metal bar joists and rebar), WPU1311 (flat glass),
  WPUSI004011 (lumber and plywood), WPU13710102 (gypsum building materials) and WPU1394
  (paving mixtures and blocks). Annual year-over-year values as compiled by the Associated General
  Contractors of America (PPI tables, updated 14 August 2025).
- **Cost breakdown structure.** Material composition of a 2 to 4 story office building by MasterFormat 2018
  line item, from a licensed construction cost database. The workbook is not redistributed; the derived
  material weights are provided in `cbs_material_weights.csv`.
- **Material lead times.** Quarterly material lead-time report (low and high lead times in weeks,
  through December 2025). The workbook is not redistributed; the derived per-material series are provided in
  `lead_times_weekly.csv`.

## Rebuilding the processed files from the source workbooks
Researchers with access to the source workbooks can place `CBS Office.xlsx` and
`Lead Times Material Dec 2025.xlsx` in this folder (or set `IJPM_DATA_DIR`), and run
`python analyses/export_processed_inputs.py`. With the workbooks present the model builds the indices
from them directly; set `IJPM_USE_PROCESSED=1` to force the processed files.
