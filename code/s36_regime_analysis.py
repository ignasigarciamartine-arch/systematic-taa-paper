# -*- coding: utf-8 -*-
"""
S3.6 MARKET REGIME ANALYSIS
=============================
Classifies each month into BULL / SIDEWAYS / BEAR / CRISIS based on SPY,
then reports S3.6 performance by regime.

Regime classification (hierarchical, based on SPY):
  CRISIS  : 6-month drawdown of SPY < -10%
  BEAR    : 6-month momentum of SPY < -5%  (not CRISIS)
  BULL    : 6-month momentum of SPY ≥ +5%
  SIDEWAYS: everything else

Input:  ../data/outputs/s36_monthly_returns.csv   (from s36_backtest.py)
        ../data/prices/etf_adjclose_2008_2025.csv
Output: ../data/outputs/s36_regime_report.txt
        ../data/outputs/s36_regime_detail.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / 'data' / 'prices'
RESULTS_DIR = BASE_DIR / 'data' / 'outputs'

# =============================================================================
# 1. LOAD DATA
# =============================================================================

df = pd.read_csv(RESULTS_DIR / 's36_monthly_returns.csv', parse_dates=['date'])
df = df.set_index('date').sort_index()

daily = pd.read_csv(
    DATA_DIR / 'etf_adjclose_2008_2025.csv',
    index_col='Date', parse_dates=True
).sort_index()

try:
    mpx = daily.resample('ME').last()
except Exception:
    mpx = daily.resample('M').last()
mpx.index = mpx.index.to_period('M').to_timestamp('M')

spy_px  = mpx['SPY']
spy_ret = spy_px.pct_change()
ief_ret = mpx['IEF'].pct_change()
ret_6040 = (0.6 * spy_ret + 0.4 * ief_ret)
ret_6040.name = '60/40'

# =============================================================================
# 2. COMPUTE REGIME INDICATORS (based on SPY)
# =============================================================================

spy_px_clean = spy_px.dropna()

mom_6m  = spy_px_clean.pct_change(6)
dd_6m   = (spy_px_clean / spy_px_clean.rolling(6).max() - 1)

def classify_regime(idx):
    """Hierarchical regime classification."""
    dd  = dd_6m.get(idx, np.nan)
    mom = mom_6m.get(idx, np.nan)
    if pd.isna(dd) or pd.isna(mom):
        return 'UNKNOWN'
    if dd < -0.10:
        return 'CRISIS'
    if mom < -0.05:
        return 'BEAR'
    if mom >= 0.05:
        return 'BULL'
    return 'SIDEWAYS'

# =============================================================================
# 3. ASSIGN REGIMES AND MERGE
# =============================================================================

# Align to backtest period
s36_ret = df['return']
common  = s36_ret.index.intersection(spy_ret.index)
s36_ret = s36_ret.reindex(common)

regime_series = pd.Series(
    {idx: classify_regime(idx) for idx in common},
    name='regime'
)

analysis = pd.DataFrame({
    'S3.6'   : s36_ret,
    '60/40'  : ret_6040.reindex(common),
    'SPY'    : spy_ret.reindex(common),
    'regime' : regime_series,
})

analysis = analysis[analysis['regime'] != 'UNKNOWN']
analysis['defensive'] = df.reindex(common)['mode'].str.contains('Def|Crash', na=False).astype(int)

# =============================================================================
# 4. REGIME PERFORMANCE SUMMARY
# =============================================================================

def annualize(r):
    r = r.dropna()
    if len(r) == 0:
        return np.nan
    years = len(r) / 12
    total = (1 + r).prod()
    return total ** (1 / years) - 1

lines = []
def p(s=''): lines.append(s)

REGIME_ORDER = ['BULL', 'SIDEWAYS', 'BEAR', 'CRISIS']
total_months = len(analysis)

p("=" * 75)
p("S3.6 — MARKET REGIME ANALYSIS (2008–2025)")
p("SPY regime classification: BULL / SIDEWAYS / BEAR / CRISIS")
p("=" * 75)

p(f"\n  {'Regime':<12} {'N':>5} {'%time':>7} {'S3.6 CAGR':>12} {'60/40 CAGR':>12} {'Def%':>8}")
p(f"  {'─'*60}")

regime_data = {}
for regime in REGIME_ORDER:
    sub = analysis[analysis['regime'] == regime]
    n   = len(sub)
    if n == 0:
        continue
    pct    = n / total_months * 100
    s36_c  = annualize(sub['S3.6'])
    f40_c  = annualize(sub['60/40'])
    def_pct= sub['defensive'].mean() * 100
    p(f"  {regime:<12} {n:>5}  {pct:>5.1f}%  {s36_c*100:>10.2f}%  {f40_c*100:>10.2f}%  {def_pct:>6.1f}%")
    regime_data[regime] = {'n': n, 'pct': pct, 's36_cagr': s36_c, '6040_cagr': f40_c, 'def_pct': def_pct}

p(f"\n  Total months classified: {total_months}")

p("\n\nKEY FINDINGS:")
p("  S3.6 vs 60/40 outperformance by regime:")
for regime in REGIME_ORDER:
    if regime in regime_data:
        d   = regime_data[regime]
        diff = (d['s36_cagr'] - d['6040_cagr']) * 100
        p(f"  {regime:<12}  {diff:>+6.2f}pp  (S3.6: {d['s36_cagr']*100:.2f}%  60/40: {d['6040_cagr']*100:.2f}%)")

p("\n" + "=" * 75)

report = "\n".join(lines)
print(report)

# Save outputs
out_report = RESULTS_DIR / 's36_regime_report.txt'
with open(out_report, 'w', encoding='utf-8') as f:
    f.write(report)
print(f"\nSaved: {out_report}")

analysis.to_csv(RESULTS_DIR / 's36_regime_detail.csv')
print(f"Saved: {RESULTS_DIR / 's36_regime_detail.csv'}")
