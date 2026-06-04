"""
NET Service — Run All Scripts in Sequence
==========================================
Execute this single file to regenerate the full project from scratch.

Usage:
    python3 scripts/run_all.py

Author: Sherin David Layanal
"""

import subprocess
import sys
import os
import time

scripts = [
    ("01_generate_data.py",      "Generating synthetic NET patient dataset..."),
    ("02_data_quality_checks.py","Running automated data quality checks..."),
    ("03_statistical_analysis.py","Producing statistical analysis and exports..."),
]

base = os.path.dirname(__file__)

print("\n" + "="*55)
print("  NET SERVICE DATA PIPELINE — FULL RUN")
print("="*55)

for script, message in scripts:
    print(f"\n  ▶  {message}")
    t0 = time.time()
    result = subprocess.run(
        [sys.executable, os.path.join(base, script)],
        capture_output=False
    )
    elapsed = round(time.time() - t0, 1)
    if result.returncode == 0:
        print(f"     ✓  Done in {elapsed}s")
    else:
        print(f"     ✗  Failed — check error above")
        sys.exit(1)

print("\n" + "="*55)
print("  ALL STEPS COMPLETE")
print("  Outputs are in /outputs/")
print("  Master workbook: outputs/powerbi_master.xlsx")
print("="*55 + "\n")
