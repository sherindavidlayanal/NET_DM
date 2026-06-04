"""
NET Service — Automated Data Quality Checks
=============================================
Runs clinically meaningful validation rules against the synthetic NET
patient dataset and produces:
  - query_report.csv       → all flagged records with severity and rule
  - quality_summary.csv    → aggregate counts per rule for dashboard
  - enets_readiness.csv    → per-patient ENETS submission status

Rules mirror the kind of edit checks used in regulated clinical trials
(Medidata Rave / Viedoc) adapted for an NHS NET service context.

Author: Sherin David Layanal
Purpose: Interview portfolio project — Cardiff and Vale UHB, NET Service Data Manager
"""

import pandas as pd
import numpy as np
from datetime import date
import os

# ── load data ────────────────────────────────────────────────────────────────

data_dir   = os.path.join(os.path.dirname(__file__), "..", "data")
output_dir = os.path.join(os.path.dirname(__file__), "..", "outputs")
os.makedirs(output_dir, exist_ok=True)

df = pd.read_csv(os.path.join(data_dir, "net_patient_data.csv"),
                 parse_dates=["diagnosis_date", "treatment_start_date",
                              "last_followup_date"])

TODAY = date(2025, 4, 30)

# ── validation rules ─────────────────────────────────────────────────────────

queries = []

def flag(patient_id, rule_id, rule_name, field, observed_value, severity, recommendation):
    queries.append({
        "patient_id":       patient_id,
        "rule_id":          rule_id,
        "rule_name":        rule_name,
        "field":            field,
        "observed_value":   str(observed_value),
        "severity":         severity,        # High / Medium / Low
        "status":           "Open",
        "recommendation":   recommendation,
    })

for _, row in df.iterrows():
    pid = row["patient_id"]

    # ── RULE 1: Missing ENETS fields ─────────────────────────────────────────
    # ENETS CoE requires all mandatory fields completed for annual submission
    if row["enets_fields_complete"] == "No":
        flag(pid, "R01", "Incomplete ENETS fields",
             "enets_fields_complete", "No", "High",
             "Review patient record and complete all mandatory ENETS fields before next submission window.")

    # ── RULE 2: Overdue follow-up (>365 days since last contact) ─────────────
    if row["followup_gap_days"] > 365:
        flag(pid, "R02", "Overdue follow-up",
             "followup_gap_days", f"{row['followup_gap_days']} days", "Medium",
             "Contact clinical team to schedule follow-up appointment or confirm patient status.")

    # ── RULE 3: Treatment start date before diagnosis date ───────────────────
    if pd.notna(row["treatment_start_date"]) and pd.notna(row["diagnosis_date"]):
        if row["treatment_start_date"].date() < row["diagnosis_date"].date():
            flag(pid, "R03", "Treatment precedes diagnosis",
                 "treatment_start_date",
                 f"{row['treatment_start_date'].date()} < {row['diagnosis_date'].date()}",
                 "High",
                 "Date error — verify both dates with clinical records and correct.")

    # ── RULE 4: G3 tumour on Watch & Wait ────────────────────────────────────
    # G3 NETs are aggressive; watchful waiting is clinically implausible
    if row["tumour_grade"] == "G3" and row["primary_treatment"] == "Watch & Wait":
        flag(pid, "R04", "G3 grade with Watch & Wait",
             "primary_treatment", "Watch & Wait (G3 tumour)", "High",
             "Clinical review required — G3 NETs typically require active treatment. "
             "Verify treatment record with Lead NET Consultant.")

    # ── RULE 5: MDT not discussed within 30 days of diagnosis ────────────────
    if row["mdt_discussed"] == "No":
        days_since_dx = (TODAY - row["diagnosis_date"].date()).days
        if days_since_dx > 30:
            flag(pid, "R05", "MDT discussion not recorded",
                 "mdt_discussed", f"No (diagnosed {days_since_dx} days ago)", "Medium",
                 "Confirm whether patient was discussed at MDT. If yes, update record. "
                 "If no, escalate to MDT coordinator.")

    # ── RULE 6: Stage IV with no treatment recorded ───────────────────────────
    if row["stage"] == "IV" and pd.isna(row["primary_treatment"]):
        flag(pid, "R06", "Stage IV — no treatment recorded",
             "primary_treatment", "Missing", "High",
             "Stage IV patient with no treatment on record. Verify with clinical team.")

    # ── RULE 7: CgA not measured ──────────────────────────────────────────────
    # Chromogranin A is a standard ENETS biomarker requirement
    if row["chromogranin_a_measured"] == "No":
        flag(pid, "R07", "Chromogranin A not measured",
             "chromogranin_a_measured", "No", "Medium",
             "CgA is an ENETS mandatory biomarker. Confirm whether assay was performed "
             "and result not entered, or whether test needs to be ordered.")

    # ── RULE 8: Ki-67 / grade mismatch ───────────────────────────────────────
    ki67 = row["ki67_percent"]
    grade = row["tumour_grade"]
    mismatch = False
    if grade == "G1" and ki67 >= 3.0:
        mismatch = True
    elif grade == "G2" and (ki67 < 3.0 or ki67 >= 20.0):
        mismatch = True
    elif grade == "G3" and ki67 < 20.0:
        mismatch = True
    if mismatch:
        flag(pid, "R08", "Ki-67 / grade mismatch",
             "ki67_percent",
             f"Ki-67={ki67}% but grade recorded as {grade}", "High",
             "WHO 2022 grading: G1 <3%, G2 3–19%, G3 ≥20%. "
             "Verify Ki-67 result and correct grade or Ki-67 value.")

    # ── RULE 9: Lost to follow-up + active treatment ──────────────────────────
    if row["outcome"] == "Lost to follow-up" and row["primary_treatment"] not in [
            "Watch & Wait", None]:
        flag(pid, "R09", "Lost to follow-up on active treatment",
             "outcome", "Lost to follow-up", "Medium",
             "Patient on active treatment marked as lost to follow-up. "
             "Escalate to clinical team — patient may need re-engagement.")

    # ── RULE 10: Missing imaging at diagnosis ─────────────────────────────────
    if pd.isna(row["imaging_at_diagnosis"]) or str(row["imaging_at_diagnosis"]).strip() == "":
        flag(pid, "R10", "No imaging recorded at diagnosis",
             "imaging_at_diagnosis", "Missing", "Low",
             "Record imaging modality used at diagnosis for ENETS submission completeness.")

# ── build query report ────────────────────────────────────────────────────────

query_df = pd.DataFrame(queries)

if not query_df.empty:
    query_df.to_csv(os.path.join(output_dir, "query_report.csv"), index=False)
    print(f"\n{'='*55}")
    print(f"  QUERY REPORT SUMMARY")
    print(f"{'='*55}")
    print(f"  Total queries raised:  {len(query_df)}")
    print(f"  Patients affected:     {query_df['patient_id'].nunique()} / 150")
    print(f"\n  By severity:")
    for sev, count in query_df["severity"].value_counts().items():
        print(f"    {sev:8s}: {count}")
    print(f"\n  By rule:")
    for rule, count in query_df["rule_name"].value_counts().items():
        print(f"    {count:3d}  {rule}")

# ── quality summary (for Power BI) ───────────────────────────────────────────

summary = (query_df.groupby(["rule_id", "rule_name", "severity"])
           .size()
           .reset_index(name="query_count"))
summary.to_csv(os.path.join(output_dir, "quality_summary.csv"), index=False)

# ── ENETS readiness per patient ───────────────────────────────────────────────

high_rules = {"R01", "R03", "R04", "R06", "R08"}
high_queries = query_df[query_df["rule_id"].isin(high_rules)]["patient_id"].unique() \
    if not query_df.empty else []

enets = df[["patient_id", "tumour_site", "tumour_grade", "stage",
            "enets_fields_complete", "mdt_discussed",
            "chromogranin_a_measured", "outcome"]].copy()

enets["has_high_severity_query"] = enets["patient_id"].isin(high_queries)

def readiness_status(row):
    if row["enets_fields_complete"] == "Yes" and not row["has_high_severity_query"]:
        return "Ready"
    elif row["enets_fields_complete"] == "No" or row["has_high_severity_query"]:
        return "Not Ready"
    else:
        return "Review Required"

enets["enets_submission_status"] = enets.apply(readiness_status, axis=1)

ready_pct = (enets["enets_submission_status"] == "Ready").mean() * 100
print(f"\n{'='*55}")
print(f"  ENETS SUBMISSION READINESS")
print(f"{'='*55}")
print(f"  Ready:           {(enets['enets_submission_status']=='Ready').sum()}")
print(f"  Not Ready:       {(enets['enets_submission_status']=='Not Ready').sum()}")
print(f"  Review Required: {(enets['enets_submission_status']=='Review Required').sum()}")
print(f"  Readiness %:     {ready_pct:.1f}%")

enets.to_csv(os.path.join(output_dir, "enets_readiness.csv"), index=False)
print(f"\n  Outputs saved to /outputs/")
print(f"    → query_report.csv")
print(f"    → quality_summary.csv")
print(f"    → enets_readiness.csv")
