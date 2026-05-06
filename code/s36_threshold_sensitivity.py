# -*- coding: utf-8 -*-
"""
S3.6 THRESHOLD SENSITIVITY — Crash Filter τ
============================================
Re-runs the core S3.6 strategy loop for a range of crash threshold values
to produce Table 2 (threshold sensitivity) in the paper.

This script replicates the full backtest logic from s36_backtest.py
but varies the crash threshold τ ∈ {-2.0%, -2.5%, -3.0%, -3.5%, -4.0%, -4.5%, -5.0%}.
All other parameters are fixed at their selected values.

Required data: same as s36_backtest.py (in ../data/prices/)

Output:
  ../data/outputs/s36_threshold_report.txt
  ../data/outputs/s36_threshold_sensitivity.csv

Expected results (in-sample, 2008-2019, rf=3M T-bill):
  τ = -4.0%  →  CAGR 10.94%, Sharpe 0.951, MaxDD -13.79%, triggers 12

Authors: Garcia Martin I., Mases Campos M., Prior Sanz F.
         IQS School of Engineering — Universitat Ramon Llull, Barcelona
"""

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations

# =============================================================================
# CONFIG
# =============================================================================

RISKY_ASSETS = ['SPY', 'QQQ', 'VGK', 'EWJ', 'SCZ', 'EEM',
                'VNQ', 'REM', 'GLD', 'IEF', 'TLT', 'TIP',
                'DBC', 'BWX', 'RWX']
CASH         = 'BIL'
ALL_ASSETS   = RISKY_ASSETS + [CASH]

MOM_THRESHOLD = 0.02
TOP_N         = 7
TRIPLET_N     = 3

START_DATE   = '2008-01-01'
TRAIN_END    = '2019-12-31'
TEST_START   = '2020-01-01'
TEST_END     = '2025-12-31'
INITIAL_CAP  = 10_000

THRESHOLDS = [-0.020, -0.025, -0.030, -0.035, -0.040, -0.045, -0.050]

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / 'data' / 'prices'
RESULTS_DIR = BASE_DIR / 'data' / 'outputs'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("S3.6 THRESHOLD SENSITIVITY")
print(f"  Thresholds: {[f'{t*100:.1f}%' for t in THRESHOLDS]}")
print("=" * 70)

# =============================================================================
# 1. LOAD DATA (same as main backtest)
# =============================================================================

print("\n[1] Loading data...")

daily_prices = pd.read_csv(DATA_DIR / 'etf_adjclose_2008_2025.csv',
                           index_col='Date', parse_dates=True)
daily_prices = daily_prices.sort_index()
daily_prices = daily_prices[
    (daily_prices.index >= START_DATE) & (daily_prices.index <= '2026-01-31')
]
daily_prices = daily_prices.reindex(columns=ALL_ASSETS).ffill()

try:
    monthly_prices = daily_prices.resample('ME').last()
except Exception:
    monthly_prices = daily_prices.resample('M').last()

monthly_prices.index = monthly_prices.index.to_period('M').to_timestamp('M')
monthly_returns = monthly_prices.pct_change()

backtest_months = [m for m in monthly_prices.index
                   if pd.Timestamp(START_DATE) <= m <= pd.Timestamp(TEST_END)]

rf_monthly = pd.read_csv(DATA_DIR / 'tbill_3m_monthly_refinitiv.csv',
                         index_col='date', parse_dates=True)['rf_monthly']
rf_monthly.index = pd.to_datetime(rf_monthly.index).to_period('M').to_timestamp('M')
rf_monthly = rf_monthly.sort_index()

def load_momentum_file(path, assets):
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index).to_period('M').to_timestamp('M')
    cols = {a: f'{a}_13612U' for a in assets if f'{a}_13612U' in df.columns}
    sub = df[[cols[a] for a in assets if a in cols]].copy()
    sub.columns = [a for a in assets if a in cols]
    return sub

mom_train    = load_momentum_file(DATA_DIR / 'momentum_train_2008_2019.csv', RISKY_ASSETS)
mom_completo = load_momentum_file(DATA_DIR / 'momentum_completo_2008_2025.csv', RISKY_ASSETS)
mom_test     = mom_completo.loc[mom_completo.index >= pd.Timestamp(TEST_START)]
momentum_u   = mom_train.combine_first(mom_test).reindex(columns=RISKY_ASSETS)

print(f"  Data loaded. Backtest months: {len(backtest_months)}")

# =============================================================================
# 2. CORE FUNCTIONS
# =============================================================================

def select_and_filter(mom_row):
    valid  = mom_row[RISKY_ASSETS].dropna()
    if len(valid) == 0:
        return []
    ranked = valid.sort_values(ascending=False)
    top    = ranked.head(TOP_N).index.tolist()
    return [a for a in top if ranked[a] >= MOM_THRESHOLD]

def compute_corr_matrix(assets, prev_t, curr_t):
    mask  = (daily_prices.index > prev_t) & (daily_prices.index <= curr_t)
    daily = daily_prices.loc[mask, assets].pct_change().dropna()
    if len(daily) < 2:
        return None
    return daily.corr()

def select_best_triplet(assets, corr):
    if len(assets) < TRIPLET_N:
        return assets
    if corr is None:
        return assets[:TRIPLET_N]
    best, best_score = assets[:TRIPLET_N], float('inf')
    for tri in combinations(assets, TRIPLET_N):
        i, j, k = tri
        if not all(x in corr.index for x in [i, j, k]):
            continue
        avg = (corr.loc[i,j] + corr.loc[i,k] + corr.loc[j,k]) / 3
        if avg < best_score:
            best_score, best = avg, list(tri)
    return best

def get_defensive_weights(mom_row, crash=False):
    weights = {a: 0.0 for a in ALL_ASSETS}
    tlt_m = mom_row.get('TLT', np.nan)
    ief_m = mom_row.get('IEF', np.nan)
    if pd.notna(tlt_m) and pd.notna(ief_m) and max(tlt_m, ief_m) >= 0:
        weights['TLT'] = 0.5
        weights['IEF'] = 0.5
    else:
        weights['BIL'] = 1.0
    return weights

def compute_metrics(ret):
    ret = ret.dropna()
    n   = len(ret)
    if n == 0:
        return {}
    rf      = rf_monthly.reindex(ret.index)
    cum     = (1 + ret).cumprod()
    cagr    = cum.iloc[-1] ** (12 / n) - 1
    excess  = ret - rf
    ex_std  = excess.std()
    sharpe  = np.sqrt(12) * excess.mean() / ex_std if ex_std > 0 else np.nan
    max_dd  = ((cum - cum.cummax()) / cum.cummax()).min()
    return dict(CAGR=cagr, Sharpe=sharpe, Max_DD=max_dd)

# =============================================================================
# 3. RUN FOR EACH THRESHOLD
# =============================================================================

rows = []

for tau in THRESHOLDS:
    print(f"\n  tau = {tau*100:.1f}% ...", end='', flush=True)
    results  = []
    triggers = 0

    for i, t in enumerate(backtest_months):
        if i == 0:
            continue
        if t not in momentum_u.index or momentum_u.loc[t].isna().all():
            continue
        mom_row = momentum_u.loc[t]
        prev_t  = backtest_months[i - 1]
        ni = i + 1
        if ni >= len(backtest_months):
            break
        t1 = backtest_months[ni]
        if t1 not in monthly_returns.index:
            continue

        next_ret = monthly_returns.loc[t1]

        # Crash filter with current tau
        crash = False
        if t in monthly_returns.index:
            avail = [a for a in RISKY_ASSETS
                     if a in monthly_returns.columns and pd.notna(monthly_returns.loc[t, a])]
            if avail:
                avg_ret = monthly_returns.loc[t, avail].mean()
                crash   = avg_ret < tau

        if crash:
            weights = get_defensive_weights(mom_row, crash=True)
            triggers += 1
        else:
            eligible = select_and_filter(mom_row)
            weights  = {a: 0.0 for a in ALL_ASSETS}
            if len(eligible) >= TRIPLET_N:
                if len(eligible) == TRIPLET_N:
                    selected = eligible
                else:
                    corr     = compute_corr_matrix(eligible, prev_t, t)
                    selected = select_best_triplet(eligible, corr)
                for a in selected:
                    weights[a] = 1.0 / TRIPLET_N
            else:
                weights = get_defensive_weights(mom_row, crash=False)

        port_ret = 0.0
        for a in ALL_ASSETS:
            w = weights.get(a, 0.0)
            if w == 0:
                continue
            if a == CASH:
                r = rf_monthly.loc[t1] if t1 in rf_monthly.index else 0.0
            else:
                r = next_ret[a] if a in next_ret.index and pd.notna(next_ret[a]) else 0.0
            port_ret += w * r

        results.append({'date': t1, 'return': port_ret})

    df     = pd.DataFrame(results).set_index('date')
    train  = df.loc[:'2019-12-31', 'return']
    m      = compute_metrics(train)
    train_triggers = sum(
        1 for i, t in enumerate(backtest_months)
        if i > 0 and t <= pd.Timestamp(TRAIN_END) and t in monthly_returns.index
        and [a for a in RISKY_ASSETS if a in monthly_returns.columns and pd.notna(monthly_returns.loc[t, a])]
        and monthly_returns.loc[t, [a for a in RISKY_ASSETS if a in monthly_returns.columns and pd.notna(monthly_returns.loc[t, a])]].mean() < tau
    )

    rows.append({
        'tau':      tau,
        'CAGR':     m.get('CAGR', np.nan),
        'Sharpe':   m.get('Sharpe', np.nan),
        'Max_DD':   m.get('Max_DD', np.nan),
        'triggers': train_triggers,
    })
    print(f" CAGR={m.get('CAGR',0)*100:.2f}%  Sharpe={m.get('Sharpe',0):.3f}  MaxDD={m.get('Max_DD',0)*100:.2f}%  triggers={train_triggers}")

# =============================================================================
# 4. PRINT TABLE
# =============================================================================

print("\n" + "=" * 70)
print("THRESHOLD SENSITIVITY — IN-SAMPLE (2008-2019, rf=3M T-bill)")
print("=" * 70)
print(f"\n  {'tau':>8}  {'CAGR':>8}  {'Sharpe':>8}  {'Max DD':>8}  {'Triggers':>9}")
print(f"  {'-'*50}")
for r in rows:
    flag = " ←" if abs(r['tau'] + 0.04) < 0.001 else ""
    print(f"  {r['tau']*100:>7.1f}%  {r['CAGR']*100:>7.2f}%  {r['Sharpe']:>8.3f}  {r['Max_DD']*100:>7.2f}%  {r['triggers']:>8}{flag}")

# =============================================================================
# 5. SAVE OUTPUT
# =============================================================================

out_df = pd.DataFrame(rows)
out_df['tau_pct'] = out_df['tau'] * 100
out_df.to_csv(RESULTS_DIR / 's36_threshold_sensitivity.csv', index=False)

with open(RESULTS_DIR / 's36_threshold_report.txt', 'w', encoding='utf-8') as f:
    f.write("S3.6 THRESHOLD SENSITIVITY REPORT\n")
    f.write("=" * 60 + "\n\n")
    f.write("In-sample period: 2008-2019 (142 months)\n")
    f.write("rf: 3M U.S. T-bill monthly\n")
    f.write("All other parameters fixed: θ=2%, N=7, triplet=3\n\n")
    f.write(f"{'tau':>8}  {'CAGR':>8}  {'Sharpe':>8}  {'Max DD':>8}  {'Triggers':>9}\n")
    f.write("-" * 50 + "\n")
    for r in rows:
        f.write(f"  {r['tau']*100:>5.1f}%  {r['CAGR']*100:>7.2f}%  {r['Sharpe']:>8.3f}  {r['Max_DD']*100:>7.2f}%  {r['triggers']:>8}\n")

print(f"\n[OK] Saved: s36_threshold_sensitivity.csv + s36_threshold_report.txt")
print("=" * 70)
