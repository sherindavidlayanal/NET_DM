"""
NET Service — Statistical Analysis & Chart-Ready Exports
=========================================================
Produces clean aggregated tables that feed directly into Power BI
visuals, plus a summary statistics report printed to console.

Outputs (all to /outputs/):
  - service_overview.csv          → KPI cards and top-level metrics
  - tumour_profile.csv            → site × grade breakdown
  - treatment_by_stage.csv        → treatment modality per stage
  - monthly_registrations.csv     → new patients over time (trend)
  - health_board_referrals.csv    → referring board breakdown
  - followup_distribution.csv     → follow-up gap histogram buckets
  - outcome_by_grade.csv          → outcome × grade crosstab
  - powerbi_master.xlsx           → all tables in one Excel workbook

Author: Sherin David Layanal
Purpose: Interview portfolio project — Cardiff and Vale UHB, NET Service Data Manager
"""

import pandas as pd
import numpy as np
from datetime import date
import os

# ── paths ─────────────────────────────────────────────────────────────────────

data_dir   = os.path.join(os.path.dirname(__file__), "..", "data")
output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(os.path.join(data_dir, "net_patient_data.csv"),
                 parse_dates=["diagnosis_date", "treatment_start_date",
                              "last_followup_date"])

enets = pd.read_csv(os.path.join(output_dir, "enets_readiness.csv"))
queries = pd.read_csv(os.path.join(output_dir, "query_report.csv"))

TODAY = date(2025, 4, 30)

# ── 1. service overview KPIs ──────────────────────────────────────────────────

total_patients      = len(df)
enets_ready         = (enets["enets_submission_status"] == "Ready").sum()
enets_ready_pct     = round(enets_ready / total_patients * 100, 1)
mdt_rate_pct        = round((df["mdt_discussed"] == "Yes").mean() * 100, 1)
overdue_followup    = (df["followup_gap_days"] > 365).sum()
open_high_queries   = (queries["severity"] == "High").sum()
stage_iv_pct        = round((df["stage"] == "IV").mean() * 100, 1)
median_age          = int(df["age_at_diagnosis"].median())
g3_count            = (df["tumour_grade"] == "G3").sum()

overview = pd.DataFrame([{
    "metric": "Total active patients",           "value": total_patients},
    {"metric": "ENETS submission ready (%)",     "value": enets_ready_pct},
    {"metric": "MDT discussion rate (%)",        "value": mdt_rate_pct},
    {"metric": "Overdue follow-up (>365 days)",  "value": int(overdue_followup)},
    {"metric": "Open high-severity queries",     "value": int(open_high_queries)},
    {"metric": "Stage IV patients (%)",          "value": stage_iv_pct},
    {"metric": "Median age at diagnosis",        "value": median_age},
    {"metric": "G3 (high-grade) patients",       "value": int(g3_count)},
])
overview.to_csv(os.path.join(output_dir, "service_overview.csv"), index=False)

# ── 2. tumour profile (site × grade) ──────────────────────────────────────────

tumour_profile = (df.groupby(["tumour_site", "tumour_grade"])
                  .size()
                  .reset_index(name="count"))
tumour_profile["pct_of_total"] = round(
    tumour_profile["count"] / total_patients * 100, 1)
tumour_profile.to_csv(os.path.join(output_dir, "tumour_profile.csv"), index=False)

# ── 3. treatment by stage ──────────────────────────────────────────────────────

treatment_stage = (df.groupby(["stage", "primary_treatment"])
                   .size()
                   .reset_index(name="count"))
treatment_stage.to_csv(os.path.join(output_dir, "treatment_by_stage.csv"), index=False)

# ── 4. monthly registrations ──────────────────────────────────────────────────

df["diagnosis_ym"] = df["diagnosis_date"].dt.to_period("M").astype(str)
monthly = (df.groupby("diagnosis_ym")
           .size()
           .reset_index(name="new_registrations"))
monthly.columns = ["year_month", "new_registrations"]
monthly["cumulative_patients"] = monthly["new_registrations"].cumsum()
monthly.to_csv(os.path.join(output_dir, "monthly_registrations.csv"), index=False)

# ── 5. health board referrals ─────────────────────────────────────────────────

hb = (df.groupby("referring_health_board")
      .size()
      .reset_index(name="patient_count"))
hb["pct"] = round(hb["patient_count"] / total_patients * 100, 1)
hb = hb.sort_values("patient_count", ascending=False)
hb.to_csv(os.path.join(output_dir, "health_board_referrals.csv"), index=False)

# ── 6. follow-up gap distribution ─────────────────────────────────────────────

bins   = [0, 90, 180, 365, 540, 730, 9999]
labels = ["0–3 months", "3–6 months", "6–12 months",
          "12–18 months", "18–24 months", ">24 months"]
df["followup_bucket"] = pd.cut(df["followup_gap_days"], bins=bins, labels=labels)
fu_dist = (df.groupby("followup_bucket", observed=True)
           .size()
           .reset_index(name="patient_count"))
fu_dist.to_csv(os.path.join(output_dir, "followup_distribution.csv"), index=False)

# ── 7. outcome by grade ───────────────────────────────────────────────────────

outcome_grade = (df.groupby(["tumour_grade", "outcome"])
                 .size()
                 .reset_index(name="count"))
outcome_grade.to_csv(os.path.join(output_dir, "outcome_by_grade.csv"), index=False)

# ── 8. ENETS field-level completeness (simulated) ─────────────────────────────

enets_fields = [
    "Tumour site", "Tumour grade (Ki-67)", "Stage at diagnosis",
    "Functional status", "Imaging modality", "Chromogranin A",
    "Primary treatment", "MDT discussion", "Date of diagnosis",
    "Last follow-up date", "Outcome", "Referring health board"
]
# Simulate varying completeness per field
np.random.seed(99)
completeness_pcts = np.random.uniform(72, 99, len(enets_fields)).round(1)
field_completeness = pd.DataFrame({
    "enets_field":       enets_fields,
    "completeness_pct":  completeness_pcts,
    "missing_count":     [int((1 - p/100) * total_patients) for p in completeness_pcts]
})
field_completeness = field_completeness.sort_values("completeness_pct")
field_completeness.to_csv(
    os.path.join(output_dir, "enets_field_completeness.csv"), index=False)

# ── 9. master Excel workbook (all sheets) ────────────────────────────────────

xl_path = os.path.join(output_dir, "powerbi_master.xlsx")
with pd.ExcelWriter(xl_path, engine="openpyxl") as writer:
    df.to_excel(writer,                  sheet_name="Patient Data",          index=False)
    overview.to_excel(writer,            sheet_name="Service Overview KPIs", index=False)
    tumour_profile.to_excel(writer,      sheet_name="Tumour Profile",        index=False)
    treatment_stage.to_excel(writer,     sheet_name="Treatment by Stage",    index=False)
    monthly.to_excel(writer,             sheet_name="Monthly Registrations", index=False)
    hb.to_excel(writer,                  sheet_name="Health Board Referrals",index=False)
    fu_dist.to_excel(writer,             sheet_name="Follow-up Distribution",index=False)
    outcome_grade.to_excel(writer,       sheet_name="Outcome by Grade",      index=False)
    field_completeness.to_excel(writer,  sheet_name="ENETS Field Completeness", index=False)
    queries.to_excel(writer,             sheet_name="Query Report",          index=False)
    enets.to_excel(writer,               sheet_name="ENETS Readiness",       index=False)

# ── print summary ─────────────────────────────────────────────────────────────

print(f"\n{'='*55}")
print(f"  STATISTICAL ANALYSIS COMPLETE")
print(f"{'='*55}")
print(f"\n  SERVICE KPIs:")
for _, row in overview.iterrows():
    print(f"    {row['metric']:40s} {row['value']}")

print(f"\n  TOP 3 TUMOUR SITES:")
top_sites = df["tumour_site"].value_counts().head(3)
for site, count in top_sites.items():
    print(f"    {site:35s} n={count}")

print(f"\n  TREATMENT DISTRIBUTION:")
for tx, count in df["primary_treatment"].value_counts().items():
    print(f"    {tx:35s} n={count}")

print(f"\n  OUTPUTS SAVED:")
files = ["service_overview.csv", "tumour_profile.csv", "treatment_by_stage.csv",
         "monthly_registrations.csv", "health_board_referrals.csv",
         "followup_distribution.csv", "outcome_by_grade.csv",
         "enets_field_completeness.csv", "powerbi_master.xlsx"]
for f in files:
    print(f"    → {f}")
