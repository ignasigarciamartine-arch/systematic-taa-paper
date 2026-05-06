# -*- coding: utf-8 -*-
"""
S3.6 BACKTEST — Full Period 2008-01 to 2025-12
================================================
Self-contained backtest for the paper.
Reads data from ../data/prices/ relative to this file's location.

Strategy: 13612U momentum + absolute threshold 2% + min-correlation triplet
          + enhanced defensive (TLT+IEF) + market-breadth crash filter (τ=-4%)

Algorithm:
  Each month-end:
  1. Crash filter: if avg return of 15 risky ETFs < -4% → defensive
  2. 13612U momentum = (R1m + R3m + R6m + R12m) / 4 → Top-7 → filter ≥ 2%
  3. If |eligible| ≥ 3: select min-correlation triplet (equal weight 1/3 each)
     If |eligible| < 3: defensive
  Defensive: TLT 50% + IEF 50% if max(mom_TLT, mom_IEF) ≥ 0, else cash 100%

Data required (place in ../data/prices/):
  - etf_adjclose_2008_2025.csv          daily adjusted close, 16 ETFs, 2007-2025
  - momentum_train_2008_2019.csv        13612U momentum, train period
  - momentum_completo_2008_2025.csv     13612U momentum, full period
  - tbill_3m_monthly_refinitiv.csv      monthly 3M T-bill rf/cash return

Outputs saved to ../data/outputs/:
  - s36_equity_curve.csv
  - s36_monthly_returns.csv
  - s36_allocation_log.csv
  - s36_summary_report.txt

To verify correct replication, expected results:
  TRAIN CAGR:  10.94%  |  Max DD: -13.79%  |  Crash triggers: 12
  TEST  CAGR:  12.54%  |  Max DD: -10.84%  |  Crash triggers:  9
  FULL  CAGR:  11.47%  |  Max DD: -13.79%

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
                'DBC', 'BWX', 'RWX']   # 15 risky ETFs
CASH         = 'BIL'
ALL_ASSETS   = RISKY_ASSETS + [CASH]

CRASH_THRESHOLD = -0.04   # τ = -4%  (market breadth crash filter)
MOM_THRESHOLD   =  0.02   # θ = 2%   (absolute momentum filter)
TOP_N           =  7      # top-N assets by momentum score
TRIPLET_N       =  3      # portfolio size

START_DATE      = '2008-01-01'
TRAIN_END       = '2019-12-31'
TEST_START      = '2020-01-01'
TEST_END        = '2025-12-31'
INITIAL_CAPITAL = 10_000

# Paths relative to this script's location (paper/code/)
BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / 'data' / 'prices'
RESULTS_DIR = BASE_DIR / 'data' / 'outputs'
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 80)
print("S3.6 BACKTEST — 2008-2025")
print("=" * 80)

# =============================================================================
# 1. LOAD DAILY PRICES
# =============================================================================

print("\n[1] Loading price data...")

price_file = DATA_DIR / 'etf_adjclose_2008_2025.csv'
if not price_file.exists():
    raise FileNotFoundError(
        f"\nPrice file not found: {price_file}\n"
        f"Copy from: ../research/phase_1/01_config/data/completo/optimum3_refinitiv_adjclose.csv\n"
        f"Rename to: etf_adjclose_2008_2025.csv"
    )

daily_prices = pd.read_csv(price_file, index_col='Date', parse_dates=True)
daily_prices.index = pd.to_datetime(daily_prices.index)
daily_prices = daily_prices.sort_index()
daily_prices = daily_prices[
    (daily_prices.index >= START_DATE) & (daily_prices.index <= '2026-01-31')
]
daily_prices = daily_prices.reindex(columns=ALL_ASSETS)
daily_prices = daily_prices.ffill()

print(f"  Daily prices: {daily_prices.index[0].date()} to {daily_prices.index[-1].date()}  ({len(daily_prices)} days)")

# Monthly prices (month-end, last trading day)
try:
    monthly_prices = daily_prices.resample('ME').last()
except Exception:
    monthly_prices = daily_prices.resample('M').last()

monthly_prices.index = monthly_prices.index.to_period('M').to_timestamp('M')
monthly_returns = monthly_prices.pct_change()

backtest_months = [m for m in monthly_prices.index
                   if pd.Timestamp(START_DATE) <= m <= pd.Timestamp(TEST_END)]

print(f"  Backtest range: {backtest_months[0].date()} to {backtest_months[-1].date()}  ({len(backtest_months)} months)")

print("\n[1b] Loading 3M T-bill risk-free/cash series...")

rf_file = DATA_DIR / 'tbill_3m_monthly_refinitiv.csv'
if not rf_file.exists():
    raise FileNotFoundError(
        f"\nRisk-free file not found: {rf_file}\n"
        f"Run: python code/download_refinitiv_tbill.py\n"
    )

rf_monthly = pd.read_csv(rf_file, index_col='date', parse_dates=True)['rf_monthly']
rf_monthly.index = pd.to_datetime(rf_monthly.index).to_period('M').to_timestamp('M')
rf_monthly = rf_monthly.sort_index()

missing_rf = [m for m in backtest_months if m not in rf_monthly.index]
if missing_rf:
    raise ValueError(f"Missing T-bill risk-free returns for {len(missing_rf)} backtest months.")

print(f"  3M T-bill rf: {rf_monthly.index[0].date()} to {rf_monthly.index[-1].date()}  ({len(rf_monthly)} months)")

# =============================================================================
# 2. LOAD MOMENTUM DATA (13612U)
# =============================================================================

print("\n[2] Loading 13612U momentum...")

def load_momentum_file(path, assets):
    """Load pre-computed 13612U momentum scores."""
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.to_period('M').to_timestamp('M')
    cols = {a: f'{a}_13612U' for a in assets if f'{a}_13612U' in df.columns}
    sub = df[[cols[a] for a in assets if a in cols]].copy()
    sub.columns = [a for a in assets if a in cols]
    return sub

train_mom_file    = DATA_DIR / 'momentum_train_2008_2019.csv'
completo_mom_file = DATA_DIR / 'momentum_completo_2008_2025.csv'

if not train_mom_file.exists() or not completo_mom_file.exists():
    raise FileNotFoundError(
        f"\nMomentum files not found in {DATA_DIR}\n"
        f"Copy from: ../research/phase_1/01_config/data/\n"
        f"  train/momentum_multi_horizon.csv    → momentum_train_2008_2019.csv\n"
        f"  completo/momentum_multi_horizon.csv → momentum_completo_2008_2025.csv"
    )

mom_train    = load_momentum_file(train_mom_file, RISKY_ASSETS)
mom_completo = load_momentum_file(completo_mom_file, RISKY_ASSETS)
mom_test     = mom_completo.loc[mom_completo.index >= pd.Timestamp(TEST_START)]

# Merge: train takes priority; extend with test period
momentum_u = mom_train.combine_first(mom_test)
momentum_u = momentum_u.reindex(columns=RISKY_ASSETS)

first_valid = momentum_u.dropna(how='all').index[0]
print(f"  13612U momentum valid from: {first_valid.date()}")

# =============================================================================
# 3. STRATEGY FUNCTIONS
# =============================================================================

def select_and_filter(mom_row, threshold=MOM_THRESHOLD, top_n=TOP_N):
    """Top-N by 13612U momentum, then filter by absolute threshold."""
    valid  = mom_row[RISKY_ASSETS].dropna()
    if len(valid) == 0:
        return []
    ranked = valid.sort_values(ascending=False)
    top    = ranked.head(top_n).index.tolist()
    return [a for a in top if ranked[a] >= threshold]


def compute_corr_matrix(assets, prev_month_end, current_month_end):
    """
    Pairwise correlation from daily returns of the current month only.
    Excludes cross-month return (first day pct_change is NaN → dropped).
    """
    mask   = (daily_prices.index > prev_month_end) & (daily_prices.index <= current_month_end)
    period = daily_prices.loc[mask, assets]
    daily_ret = period.pct_change().dropna()
    if len(daily_ret) < 2:
        return None
    return daily_ret.corr()


def select_best_triplet(assets, corr_matrix):
    """Select triplet of 3 assets with minimum average pairwise correlation."""
    if len(assets) < TRIPLET_N:
        return assets
    if corr_matrix is None:
        return assets[:TRIPLET_N]

    best, best_score = assets[:TRIPLET_N], float('inf')
    for triplet in combinations(assets, TRIPLET_N):
        i, j, k = triplet
        if not all(x in corr_matrix.index for x in [i, j, k]):
            continue
        avg = (corr_matrix.loc[i, j] + corr_matrix.loc[i, k] + corr_matrix.loc[j, k]) / 3
        if avg < best_score:
            best_score = avg
            best       = list(triplet)
    return best


def get_defensive_weights(mom_row, crash=False):
    """
    Enhanced defensive allocation:
    - TLT 50% + IEF 50% if max(momentum_TLT, momentum_IEF) >= 0
    - BIL 100% otherwise
    """
    weights = {a: 0.0 for a in ALL_ASSETS}
    tlt_m   = mom_row.get('TLT', np.nan)
    ief_m   = mom_row.get('IEF', np.nan)

    if pd.notna(tlt_m) and pd.notna(ief_m) and max(tlt_m, ief_m) >= 0:
        weights['TLT'] = 0.5
        weights['IEF'] = 0.5
        mode = 'TLT+IEF_Crash' if crash else 'TLT+IEF_Def'
    else:
        weights['BIL'] = 1.0
        mode = 'Cash_Crash' if crash else 'Cash_Def'
    return weights, mode

# =============================================================================
# 4. BACKTEST LOOP
# =============================================================================

print("\n[3] Running S3.6 backtest...")

results   = []
alloc_log = []

for i, t in enumerate(backtest_months):
    if i == 0:
        continue

    if t not in momentum_u.index or momentum_u.loc[t].isna().all():
        continue

    mom_row = momentum_u.loc[t]
    prev_t  = backtest_months[i - 1]

    next_idx = i + 1
    if next_idx >= len(backtest_months):
        break
    t1 = backtest_months[next_idx]
    if t1 not in monthly_returns.index:
        continue

    next_ret = monthly_returns.loc[t1]

    # ------------------------------------------------------------------
    # STEP 1: CRASH FILTER
    # Average monthly return of all 15 risky assets in current month
    # ------------------------------------------------------------------
    crash_detected = False
    avg_mkt_return = np.nan

    if t in monthly_returns.index:
        avail = [a for a in RISKY_ASSETS
                 if a in monthly_returns.columns and pd.notna(monthly_returns.loc[t, a])]
        if avail:
            avg_mkt_return = monthly_returns.loc[t, avail].mean()
            crash_detected = avg_mkt_return < CRASH_THRESHOLD

    if crash_detected:
        weights, mode = get_defensive_weights(mom_row, crash=True)
        selected = [a for a in ALL_ASSETS if weights.get(a, 0) > 0]

    else:
        # ------------------------------------------------------------------
        # STEPS 2-3: Momentum → Top-7 → threshold filter
        # ------------------------------------------------------------------
        eligible = select_and_filter(mom_row)

        # ------------------------------------------------------------------
        # STEP 4: Offensive or defensive
        # ------------------------------------------------------------------
        if len(eligible) >= TRIPLET_N:
            weights = {a: 0.0 for a in ALL_ASSETS}

            if len(eligible) == TRIPLET_N:
                selected = eligible
                mode     = 'Offensive_EW3'
            else:
                corr     = compute_corr_matrix(eligible, prev_t, t)
                selected = select_best_triplet(eligible, corr)
                mode     = 'Offensive_Triplet'

            for a in selected:
                weights[a] = 1.0 / TRIPLET_N

        else:
            weights, mode = get_defensive_weights(mom_row, crash=False)
            selected = [a for a in ALL_ASSETS if weights.get(a, 0) > 0]

    # ------------------------------------------------------------------
    # STEP 5: Apply allocation to next month returns
    # ------------------------------------------------------------------
    port_return = 0.0
    for a in ALL_ASSETS:
        weight = weights.get(a, 0.0)
        if weight == 0:
            continue
        if a == CASH:
            asset_return = rf_monthly.loc[t1]
        else:
            asset_return = next_ret[a] if a in next_ret.index and pd.notna(next_ret[a]) else 0.0
        port_return += weight * asset_return

    results.append({
        'date'           : t1,
        'return'         : port_return,
        'mode'           : mode,
        'crash_detected' : crash_detected,
        'avg_mkt_return' : avg_mkt_return,
        'selected'       : ', '.join(selected),
    })

    alloc_log.append({
        'decision_date'  : t,
        'apply_date'     : t1,
        'mode'           : mode,
        'crash_detected' : crash_detected,
        'avg_mkt_ret_%'  : round(avg_mkt_return * 100, 2) if not np.isnan(avg_mkt_return) else np.nan,
        **{a: round(weights.get(a, 0.0), 4) for a in ALL_ASSETS},
        'selected'       : ', '.join(selected),
    })

results_df = pd.DataFrame(results).set_index('date')
alloc_df   = pd.DataFrame(alloc_log)

print(f"  Months processed: {len(results_df)}  |  {results_df.index[0].date()} to {results_df.index[-1].date()}")

# =============================================================================
# 5. PERFORMANCE METRICS
# =============================================================================

def compute_metrics(ret, initial=INITIAL_CAPITAL):
    """Compute standard performance metrics using 3M T-bill excess returns."""
    ret   = ret.dropna()
    n     = len(ret)
    if n == 0:
        return {}
    rf        = rf_monthly.reindex(ret.index)
    if rf.isna().any():
        raise ValueError("Missing risk-free observations for metric calculation.")
    years     = n / 12
    cum       = (1 + ret).cumprod()
    final_val = cum.iloc[-1]
    cagr      = final_val ** (1 / years) - 1
    vol       = ret.std() * np.sqrt(12)
    excess    = ret - rf
    ex_std    = excess.std()
    sharpe    = np.sqrt(12) * excess.mean() / ex_std if ex_std > 0 else np.nan

    downside = np.minimum(excess, 0.0)
    dv       = np.sqrt((downside ** 2).sum() / (n - 1)) if n > 1 else np.nan
    sortino  = np.sqrt(12) * excess.mean() / dv if (dv and dv > 0) else np.nan

    max_dd  = ((cum - cum.cummax()) / cum.cummax()).min()
    calmar  = cagr / abs(max_dd) if max_dd != 0 else np.nan
    win     = (ret > 0).mean()

    return dict(
        n=n, years=round(years, 2),
        CAGR=cagr, Vol=vol,
        Sharpe_TBill=sharpe, Sortino_TBill=sortino,
        Max_DD=max_dd, Calmar=calmar,
        Win=win, Total_Ret=final_val - 1,
        Final_Cap=initial * final_val
    )

print("\n[4] Computing metrics...")

s36_train = results_df.loc[:'2019-12-31', 'return']
s36_test  = results_df.loc['2020-01-01':, 'return']
s36_full  = results_df['return']

m_train = compute_metrics(s36_train)
m_test  = compute_metrics(s36_test)
m_full  = compute_metrics(s36_full)

# Mode distributions
train_modes = results_df.loc[:'2019-12-31', 'mode'].value_counts()
test_modes  = results_df.loc['2020-01-01':, 'mode'].value_counts()
crash_train = int(results_df.loc[:'2019-12-31', 'crash_detected'].sum())
crash_test  = int(results_df.loc['2020-01-01':, 'crash_detected'].sum())

# Asset frequency (train)
alloc_df['apply_date'] = pd.to_datetime(alloc_df['apply_date'])
atr        = alloc_df[alloc_df['apply_date'] <= pd.Timestamp('2019-12-31')]
asset_freq = {a: (atr[a] > 0).mean() for a in ALL_ASSETS
              if a in atr.columns and (atr[a] > 0).any()}
asset_freq = dict(sorted(asset_freq.items(), key=lambda x: x[1], reverse=True))

# =============================================================================
# 6. PRINT RESULTS
# =============================================================================

print("\n" + "=" * 80)
print("RESULTS SUMMARY - S3.6")
print("=" * 80)

for lbl, m in [('TRAIN (2008-2019)', m_train), ('TEST (2020-2025)', m_test), ('FULL (2008-2025)', m_full)]:
    print(f"\n  {lbl}")
    print(f"  {'-'*50}")
    print(f"  CAGR:       {m['CAGR']*100:7.2f}%")
    print(f"  Volatility: {m['Vol']*100:7.2f}%")
    print(f"  Sharpe:     {m['Sharpe_TBill']:7.3f}  (rf=3M T-bill)")
    print(f"  Sortino:    {m['Sortino_TBill']:7.3f}  (rf=3M T-bill)")
    print(f"  Max DD:     {m['Max_DD']*100:7.2f}%")
    print(f"  Win Rate:   {m['Win']*100:7.2f}%")
    print(f"  Final cap:  ${m['Final_Cap']:>10,.0f}  (from $10,000)")

print(f"\n  Crash triggers - TRAIN: {crash_train}  |  TEST: {crash_test}")

# Verification check
print("\n" + "=" * 80)
print("VERIFICATION CHECK")
print("=" * 80)
ok = True
checks = [
    ('TRAIN CAGR',  m_train['CAGR']*100, 10.94, 0.05),
    ('TEST CAGR',   m_test['CAGR']*100,  12.54, 0.05),
    ('FULL CAGR',   m_full['CAGR']*100,  11.47, 0.05),
    ('TRAIN MaxDD', m_train['Max_DD']*100, -13.79, 0.05),
    ('CRASH TRAIN', crash_train, 12, 0),
    ('CRASH TEST',  crash_test,  9, 0),
]
for name, got, expected, tol in checks:
    if isinstance(expected, int):
        passed = (got == expected)
    else:
        passed = abs(got - expected) <= tol
    status = 'OK' if passed else 'FAIL'
    print(f"  [{status}]  {name:<20}  expected {expected}  got {got:.2f}")
    if not passed:
        ok = False

if ok:
    print("\n  [OK] All checks passed - results match verified numbers.")
else:
    print("\n  [FAIL] Some checks failed - review data or code.")

# =============================================================================
# 7. SAVE OUTPUTS
# =============================================================================

print("\n[5] Saving outputs...")

out = results_df[['return', 'mode', 'crash_detected', 'avg_mkt_return', 'selected']].copy()
out['equity'] = INITIAL_CAPITAL * (1 + results_df['return']).cumprod()
out.to_csv(RESULTS_DIR / 's36_monthly_returns.csv')
print("  [OK] s36_monthly_returns.csv")

equity_df = pd.DataFrame({'S3.6': INITIAL_CAPITAL * (1 + results_df['return']).cumprod()})
equity_df.to_csv(RESULTS_DIR / 's36_equity_curve.csv')
print("  [OK] s36_equity_curve.csv")

alloc_df.to_csv(RESULTS_DIR / 's36_allocation_log.csv', index=False)
print("  [OK] s36_allocation_log.csv")

with open(RESULTS_DIR / 's36_summary_report.txt', 'w', encoding='utf-8') as f:
    f.write("S3.6 BACKTEST REPORT\n")
    f.write("=" * 60 + "\n\n")
    for lbl, m in [('TRAIN (2008-2019)', m_train), ('TEST (2020-2025)', m_test), ('FULL (2008-2025)', m_full)]:
        f.write(f"{lbl}\n{'-'*40}\n")
        f.write(f"  CAGR:       {m['CAGR']*100:.2f}%\n")
        f.write(f"  Sharpe:     {m['Sharpe_TBill']:.3f}  (rf=3M T-bill)\n")
        f.write(f"  Sortino:    {m['Sortino_TBill']:.3f}  (rf=3M T-bill)\n")
        f.write(f"  Max DD:     {m['Max_DD']*100:.2f}%\n")
        f.write(f"  Win Rate:   {m['Win']*100:.2f}%\n")
        f.write(f"  Final Cap:  ${m['Final_Cap']:,.0f}\n\n")
    f.write(f"Crash triggers - TRAIN: {crash_train}  |  TEST: {crash_test}\n")
print("  [OK] s36_summary_report.txt")

print("\n" + "=" * 80)
print(f"DONE — outputs in {RESULTS_DIR}")
print("=" * 80)
