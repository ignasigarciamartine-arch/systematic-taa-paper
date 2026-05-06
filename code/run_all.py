# -*- coding: utf-8 -*-
"""
RUN ALL — Master reproducibility script
========================================
Runs all S3.6 analyses in order.
Start here to fully reproduce all paper results from scratch.

Order:
  1. s36_backtest.py             — main backtest, generates equity curve + summary
  2. s36_crisis_analysis.py      — crisis period performance
  3. s36_regime_analysis.py      — regime breakdown
  4. s36_threshold_sensitivity.py — crash filter sensitivity (Table 2)
  5. s36_montecarlo_v3.py        — stationary bootstrap + paired 60/40 + Ledoit-Wolf
  6. s36_figures.py              — all paper figures

Expected total runtime: ~5-15 min (montecarlo dominates).

Usage:
  python code/run_all.py               # run everything
  python code/run_all.py --skip-mc     # skip montecarlo (faster)

Authors: Garcia Martin I., Mases Campos M., Prior Sanz F.
         IQS School of Engineering — Universitat Ramon Llull, Barcelona
"""

import subprocess
import sys
import time
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

STEPS = [
    ('s36_backtest.py',              'Main backtest (equity curve, summary)'),
    ('s36_crisis_analysis.py',       'Crisis period analysis'),
    ('s36_regime_analysis.py',       'Market regime analysis'),
    ('s36_threshold_sensitivity.py', 'Crash threshold sensitivity'),
    ('s36_montecarlo_v3.py',         'Monte Carlo bootstrap (stationary + paired + LW)'),
    ('s36_figures.py',               'Figure generation'),
]

skip_mc = '--skip-mc' in sys.argv

print("=" * 70)
print("S3.6 — FULL REPRODUCIBILITY RUN")
print("=" * 70)

total_start = time.time()
ok_all = True

for script, description in STEPS:
    if skip_mc and 'montecarlo' in script:
        print(f"\n  [SKIP] {script}  (--skip-mc)")
        continue

    path = SCRIPT_DIR / script
    if not path.exists():
        print(f"\n  [MISSING] {script} — file not found, skipping")
        ok_all = False
        continue

    print(f"\n{'='*70}")
    print(f"  STEP: {description}")
    print(f"  Script: {script}")
    print(f"{'='*70}")

    t0     = time.time()
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(SCRIPT_DIR),
        capture_output=False,
    )
    elapsed = time.time() - t0

    if result.returncode == 0:
        print(f"\n  [OK] {script} — completed in {elapsed:.1f}s")
    else:
        print(f"\n  [FAIL] {script} — exit code {result.returncode}")
        ok_all = False

total_elapsed = time.time() - total_start
print(f"\n{'='*70}")
if ok_all:
    print(f"  ALL STEPS COMPLETED — total time: {total_elapsed:.1f}s")
else:
    print(f"  COMPLETED WITH ERRORS — check output above")
print(f"{'='*70}")
