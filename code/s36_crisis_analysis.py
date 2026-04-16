# -*- coding: utf-8 -*-
"""
S3.6 CRISIS PERIOD ANALYSIS
=============================
Computes performance metrics for specific crisis/stress periods.

Input:  ../data/outputs/s36_monthly_returns.csv   (from s36_backtest.py)
        ../data/prices/etf_adjclose_2008_2025.csv  (for SPY benchmark)
Output: ../data/outputs/s36_crisis_report.txt

Crisis periods:
  1. Global Financial Crisis  : 2008-01 – 2009-06
  2. COVID & Aftermath        : 2020-03 – 2023-05
  3. Tariff Shock             : 2025-03 – 2025-04
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / 'data' / 'prices'
RESULTS_DIR = BASE_DIR / 'data' / 'outputs'

# ── Load S3.6 backtest output ───────────────────────────────────────────────

df = pd.read_csv(RESULTS_DIR / 's36_monthly_returns.csv', parse_dates=['date'])
df = df.set_index('date').sort_index()

# ── Load SPY and compute 60/40 benchmark ────────────────────────────────────

daily = pd.read_csv(
    DATA_DIR / 'etf_adjclose_2008_2025.csv',
    index_col='Date', parse_dates=True
).sort_index()

try:
    monthly_px = daily.resample('ME').last()
except Exception:
    monthly_px = daily.resample('M').last()
monthly_px.index = monthly_px.index.to_period('M').to_timestamp('M')

spy_ret   = monthly_px['SPY'].pct_change()
ief_ret   = monthly_px['IEF'].pct_change()
ret_6040  = 0.6 * spy_ret + 0.4 * ief_ret

# ── Performance metrics function ─────────────────────────────────────────────

def metrics(returns):
    r = returns.dropna()
    if len(r) == 0:
        return {}
    total  = (1 + r).prod() - 1
    years  = len(r) / 12
    cagr   = (1 + total) ** (1 / years) - 1 if years > 0 else np.nan
    vol    = r.std() * np.sqrt(12)
    sharpe = cagr / vol if vol > 0 else np.nan
    equity = (1 + r).cumprod()
    dd     = (equity / equity.cummax() - 1).min()
    return {
        'N_months'    : len(r),
        'Total_Return': round(total * 100, 2),
        'CAGR_%'      : round(cagr * 100, 2),
        'Volatility_%': round(vol * 100, 2),
        'Sharpe_rf0'  : round(sharpe, 3),
        'Max_DD_%'    : round(dd * 100, 2),
        'Final_$10k'  : round(10_000 * (1 + total), 0),
    }

# ── Crisis periods ───────────────────────────────────────────────────────────

PERIODS = {
    'Global Financial Crisis (2008-01 – 2009-06)': ('2008-01-31', '2009-06-30'),
    'COVID & Aftermath (2020-03 – 2023-05)'       : ('2020-03-31', '2023-05-31'),
    'Tariff Shock (2025-03 – 2025-04)'            : ('2025-03-31', '2025-04-30'),
}

lines = []
def p(s=''): lines.append(s)

p("=" * 70)
p("S3.6 — CRISIS PERIOD ANALYSIS")
p("Benchmarks: SPY (S&P 500), 60/40 (SPY 60% + IEF 40%)")
p("=" * 70)

for period_name, (start, end) in PERIODS.items():
    s36_slice   = df.loc[start:end, 'return'] if 'return' in df.columns else pd.Series(dtype=float)
    spy_slice   = spy_ret.loc[start:end]
    f6040_slice = ret_6040.loc[start:end]

    # Count crash triggers
    crashes = int(df.loc[start:end, 'crash_detected'].sum()) if 'crash_detected' in df.columns else 0

    p(f"\n{'─'*70}")
    p(f"  {period_name}")
    p(f"{'─'*70}")

    header = f"  {'Metric':<22} {'S3.6':>10} {'SPY':>10} {'60/40':>10}"
    p(header)
    p(f"  {'─'*54}")

    m_s36  = metrics(s36_slice)
    m_spy  = metrics(spy_slice)
    m_6040 = metrics(f6040_slice)

    rows = [
        ('N months',      'N_months',     False),
        ('Total Return %', 'Total_Return', True),
        ('CAGR %',         'CAGR_%',       True),
        ('Volatility %',   'Volatility_%', True),
        ('Sharpe (rf=0)',   'Sharpe_rf0',  False),
        ('Max DD %',        'Max_DD_%',    True),
        ('Final ($10k)',    'Final_$10k',  False),
    ]

    for name, key, is_pct in rows:
        v1 = m_s36.get(key, 'N/A')
        v2 = m_spy.get(key, 'N/A')
        v3 = m_6040.get(key, 'N/A')
        if key == 'N_months':
            p(f"  {name:<22} {str(v1):>10} {str(v2):>10} {str(v3):>10}")
        elif key == 'Final_$10k':
            p(f"  {name:<22} {f'${v1:>8,.0f}':>10} {f'${v2:>8,.0f}':>10} {f'${v3:>8,.0f}':>10}")
        else:
            p(f"  {name:<22} {v1:>9}% {v2:>9}% {v3:>9}%")

    p(f"  {'Crash triggers':<22} {crashes:>10}")

p("\n" + "=" * 70)

# Print and save
report = "\n".join(lines)
print(report)

out_file = RESULTS_DIR / 's36_crisis_report.txt'
with open(out_file, 'w') as f:
    f.write(report)
print(f"\nSaved: {out_file}")
