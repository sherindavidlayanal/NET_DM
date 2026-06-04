"""
NET Service — Synthetic Patient Data Generator
===============================================
Generates 150 fictional NET patient records with clinically realistic
fields mapped to ENETS Centre of Excellence data requirements.

Author: Sherin David Layanal
Purpose: Interview portfolio project — Cardiff and Vale UHB, NET Service Data Manager
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

N = 150

# ── helpers ──────────────────────────────────────────────────────────────────

def random_date(start_year=2019, end_year=2024):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    return start + timedelta(days=random.randint(0, (end - start).days))

def add_days(d, days):
    return d + timedelta(days=days)

# ── core fields ───────────────────────────────────────────────────────────────

patient_ids = [f"NET-{str(i).zfill(3)}" for i in range(1, N + 1)]

ages = np.random.randint(30, 82, N)
sexes = np.random.choice(["Male", "Female"], N, p=[0.52, 0.48])

tumour_sites = np.random.choice(
    ["GI (small intestine)", "Pancreatic", "GI (colorectal)", "Lung", "Other"],
    N, p=[0.30, 0.25, 0.12, 0.15, 0.18]
)

grades = []
for site in tumour_sites:
    if site == "Pancreatic":
        grades.append(np.random.choice(["G1", "G2", "G3"], p=[0.35, 0.45, 0.20]))
    elif site == "Lung":
        grades.append(np.random.choice(["G1", "G2", "G3"], p=[0.40, 0.40, 0.20]))
    else:
        grades.append(np.random.choice(["G1", "G2", "G3"], p=[0.55, 0.35, 0.10]))

ki67_values = []
for g in grades:
    if g == "G1":
        ki67_values.append(round(random.uniform(0.5, 2.9), 1))
    elif g == "G2":
        ki67_values.append(round(random.uniform(3.0, 19.9), 1))
    else:
        ki67_values.append(round(random.uniform(20.0, 65.0), 1))

stages = np.random.choice(["I", "II", "III", "IV"], N, p=[0.12, 0.20, 0.23, 0.45])

treatments = []
for i in range(N):
    stage = stages[i]
    grade = grades[i]
    if stage == "IV" and grade in ["G1", "G2"]:
        treatments.append(np.random.choice(
            ["SSA (Octreotide)", "SSA (Lanreotide)", "PRRT", "Everolimus", "Sunitinib"],
            p=[0.30, 0.25, 0.25, 0.10, 0.10]
        ))
    elif stage in ["I", "II"]:
        treatments.append(np.random.choice(
            ["Surgery", "Watch & Wait", "SSA (Octreotide)"],
            p=[0.55, 0.30, 0.15]
        ))
    elif grade == "G3":
        treatments.append(np.random.choice(
            ["Chemotherapy (EP)", "Chemotherapy (FOLFOX)", "Immunotherapy"],
            p=[0.50, 0.30, 0.20]
        ))
    else:
        treatments.append(np.random.choice(
            ["SSA (Octreotide)", "SSA (Lanreotide)", "PRRT", "Surgery"],
            p=[0.35, 0.25, 0.25, 0.15]
        ))

health_boards = np.random.choice(
    ["Cardiff and Vale UHB", "Swansea Bay UHB", "Cwm Taf Morgannwg UHB",
     "Aneurin Bevan UHB", "Hywel Dda UHB", "Betsi Cadwaladr UHB", "NHS England"],
    N, p=[0.30, 0.18, 0.15, 0.15, 0.10, 0.07, 0.05]
)

diagnosis_dates = [random_date(2019, 2024) for _ in range(N)]

treatment_start_dates = []
for i, dx in enumerate(diagnosis_dates):
    # intentionally introduce 4 date errors (treatment before diagnosis)
    if i in [12, 47, 83, 119]:
        treatment_start_dates.append(dx - timedelta(days=random.randint(5, 30)))
    else:
        treatment_start_dates.append(dx + timedelta(days=random.randint(14, 120)))

last_followup_dates = []
for dx in diagnosis_dates:
    gap = random.randint(30, 900)
    fu = dx + timedelta(days=gap)
    if fu > date(2025, 4, 30):
        fu = date(2025, 4, 30)
    last_followup_dates.append(fu)

followup_gap_days = [
    (date(2025, 4, 30) - fu).days for fu in last_followup_dates
]

mdt_discussed = np.random.choice(["Yes", "No"], N, p=[0.88, 0.12])

# ENETS completeness — intentionally 22% incomplete for dashboard interest
enets_complete = np.random.choice(["Yes", "No"], N, p=[0.78, 0.22])

# Functional status (secretory vs non-secretory)
functional_status = np.random.choice(
    ["Functional", "Non-functional"], N, p=[0.35, 0.65]
)

# Chromogranin A (CgA) measured — ENETS requirement
cga_measured = np.random.choice(["Yes", "No"], N, p=[0.82, 0.18])

# Imaging at diagnosis
imaging = np.random.choice(
    ["CT", "MRI", "Octreoscan", "DOTATATE PET-CT", "CT + DOTATATE"],
    N, p=[0.25, 0.15, 0.10, 0.30, 0.20]
)

outcomes = []
for i in range(N):
    stage = stages[i]
    grade = grades[i]
    gap   = followup_gap_days[i]
    if stage == "IV" and grade == "G3":
        outcomes.append(np.random.choice(
            ["Progressive disease", "Deceased", "Stable disease"],
            p=[0.40, 0.35, 0.25]
        ))
    elif gap > 500:
        outcomes.append(np.random.choice(
            ["Lost to follow-up", "Stable disease"],
            p=[0.40, 0.60]
        ))
    elif stage in ["I", "II"]:
        outcomes.append(np.random.choice(
            ["Complete remission", "Stable disease", "Progressive disease"],
            p=[0.45, 0.45, 0.10]
        ))
    else:
        outcomes.append(np.random.choice(
            ["Stable disease", "Progressive disease", "Deceased", "Lost to follow-up"],
            p=[0.50, 0.25, 0.15, 0.10]
        ))

# ── assemble dataframe ────────────────────────────────────────────────────────

df = pd.DataFrame({
    "patient_id":            patient_ids,
    "age_at_diagnosis":      ages,
    "sex":                   sexes,
    "referring_health_board": health_boards,
    "diagnosis_date":        diagnosis_dates,
    "tumour_site":           tumour_sites,
    "tumour_grade":          grades,
    "ki67_percent":          ki67_values,
    "stage":                 stages,
    "functional_status":     functional_status,
    "imaging_at_diagnosis":  imaging,
    "chromogranin_a_measured": cga_measured,
    "primary_treatment":     treatments,
    "treatment_start_date":  treatment_start_dates,
    "last_followup_date":    last_followup_dates,
    "followup_gap_days":     followup_gap_days,
    "mdt_discussed":         mdt_discussed,
    "enets_fields_complete": enets_complete,
    "outcome":               outcomes,
})

# ── save ──────────────────────────────────────────────────────────────────────

out_dir = os.path.join(os.path.dirname(__file__), "..", "data")
os.makedirs(out_dir, exist_ok=True)
out_path = os.path.join(out_dir, "net_patient_data.csv")
df.to_csv(out_path, index=False)

print(f"Generated {N} synthetic NET patient records → {out_path}")
print(f"\nSummary:")
print(f"  Tumour sites:      {df['tumour_site'].value_counts().to_dict()}")
print(f"  Grade breakdown:   {df['tumour_grade'].value_counts().to_dict()}")
print(f"  ENETS complete:    {df['enets_complete'].value_counts().to_dict()}" if 'enets_complete' in df else f"  ENETS complete:    {df['enets_fields_complete'].value_counts().to_dict()}")
print(f"  MDT discussed:     {df['mdt_discussed'].value_counts().to_dict()}")
print(f"  Stage IV patients: {(df['stage']=='IV').sum()}")
