# -*- coding: utf-8 -*-
"""
S3.6 FIGURES — All paper figures
=================================
Generates all figures used in the paper from backtest outputs.
Run AFTER s36_backtest.py, s36_crisis_analysis.py, s36_regime_analysis.py,
s36_threshold_sensitivity.py, and s36_montecarlo.py.

Figures produced (saved to ../figures/):
  G1_equity_curves_full.png          — equity curves 2008-2025 (strategy vs 60/40)
  G2_drawdown_full.png               — drawdown comparison 2008-2025
  G3_oos_equity.png                  — OOS equity curve 2020-2025
  G4_crash_activations.png           — crash filter trigger timeline
  G5_regime_bar.png                  — performance by regime (bar chart)
  G6_montecarlo_cagr.png             — MC CAGR and MaxDD distributions
  G7_threshold_sensitivity.png       — sensitivity of CAGR and Sharpe to τ
  G8_montecarlo_strategy.png         — strategy-level MC vs 60/40 and SPY

Authors: Garcia Martin I., Mases Campos M., Prior Sanz F.
         IQS School of Engineering — Universitat Ramon Llull, Barcelona
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')   # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from pathlib import Path

# =============================================================================
# PATHS & STYLE
# =============================================================================

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / 'data' / 'prices'
RESULTS_DIR = BASE_DIR / 'data' / 'outputs'
FIG_DIR     = BASE_DIR / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)

# IQS-inspired palette
C_STRATEGY = '#1f4e79'   # dark blue
C_BENCH    = '#808080'   # grey
C_60_40    = '#c55a11'   # orange
C_CRASH    = '#c00000'   # red

plt.rcParams.update({
    'font.family'     : 'serif',
    'font.size'       : 11,
    'axes.spines.top' : False,
    'axes.spines.right': False,
    'figure.dpi'      : 150,
})

print("=" * 70)
print("S3.6 FIGURE GENERATOR")
print("=" * 70)

# =============================================================================
# LOAD DATA
# =============================================================================

print("\n[1] Loading data...")

monthly = pd.read_csv(RESULTS_DIR / 's36_monthly_returns.csv',
                      index_col='date', parse_dates=True)
monthly.index = pd.to_datetime(monthly.index)

# 60/40 benchmark from price data
prices = pd.read_csv(DATA_DIR / 'etf_adjclose_2008_2025.csv',
                     index_col='Date', parse_dates=True)
prices.index = pd.to_datetime(prices.index)
try:
    mp = prices.resample('ME').last()
except Exception:
    mp = prices.resample('M').last()
mp.index = mp.index.to_period('M').to_timestamp('M')
mr = mp.pct_change()

s36_ret  = monthly['return']
b6040_ret = 0.6 * mr['SPY'] + 0.4 * mr['IEF']
b6040_ret = b6040_ret.reindex(s36_ret.index)

# Align
s36_ret   = s36_ret.dropna()
b6040_ret = b6040_ret.reindex(s36_ret.index).fillna(0)

INITIAL = 10_000
s36_eq   = INITIAL * (1 + s36_ret).cumprod()
b6040_eq = INITIAL * (1 + b6040_ret).cumprod()

def drawdown_series(eq):
    return (eq - eq.cummax()) / eq.cummax() * 100

# =============================================================================
# G1 — EQUITY CURVES FULL (2008-2025)
# =============================================================================

print("\n[G1] Equity curves full period...")
fig, ax = plt.subplots(figsize=(9, 4.5))

ax.plot(s36_eq.index,   s36_eq.values,   color=C_STRATEGY, lw=2,   label='S3.6 strategy')
ax.plot(b6040_eq.index, b6040_eq.values, color=C_60_40,    lw=1.5, linestyle='--', label='60/40 benchmark')

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.set_xlabel('')
ax.set_ylabel('Portfolio value ($)')
ax.set_title('Equity curves, 2008–2025 ($10,000 initial capital)', fontsize=12)
ax.legend(frameon=False)
ax.axvline(pd.Timestamp('2020-01-01'), color='#444', lw=0.8, linestyle=':', label='Train/test split')
ax.text(pd.Timestamp('2020-03-01'), ax.get_ylim()[0] * 1.05, 'OOS →',
        fontsize=9, color='#444')

plt.tight_layout()
fig.savefig(FIG_DIR / 'G1_equity_curves_full.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print("  [OK] G1_equity_curves_full.png")

# =============================================================================
# G2 — DRAWDOWN COMPARISON
# =============================================================================

print("\n[G2] Drawdown comparison...")
dd_s36   = drawdown_series(s36_eq)
dd_6040  = drawdown_series(b6040_eq)

fig, ax = plt.subplots(figsize=(9, 3.5))
ax.fill_between(dd_s36.index,   dd_s36.values,   0, alpha=0.4, color=C_STRATEGY, label='S3.6 strategy')
ax.fill_between(dd_6040.index,  dd_6040.values,  0, alpha=0.3, color=C_60_40,    label='60/40 benchmark')
ax.axhline(-15, color=C_CRASH, lw=1, linestyle='--', label='Hard constraint: −15%')

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.0f}%'))
ax.set_ylabel('Drawdown (%)')
ax.set_title('Drawdown comparison, 2008–2025', fontsize=12)
ax.legend(frameon=False, loc='lower left', fontsize=9)
ax.axvline(pd.Timestamp('2020-01-01'), color='#444', lw=0.8, linestyle=':')

plt.tight_layout()
fig.savefig(FIG_DIR / 'G2_drawdown_full.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print("  [OK] G2_drawdown_full.png")

# =============================================================================
# G3 — OOS EQUITY CURVE
# =============================================================================

print("\n[G3] OOS equity curve...")
oos_mask  = s36_eq.index >= pd.Timestamp('2020-01-01')
s36_oos   = s36_eq[oos_mask] / s36_eq[oos_mask].iloc[0] * INITIAL
b6040_oos = b6040_eq[oos_mask] / b6040_eq[oos_mask].iloc[0] * INITIAL

fig, ax = plt.subplots(figsize=(8, 4))
ax.plot(s36_oos.index,   s36_oos.values,   color=C_STRATEGY, lw=2,   label='S3.6 strategy')
ax.plot(b6040_oos.index, b6040_oos.values, color=C_60_40,    lw=1.5, linestyle='--', label='60/40 benchmark')

ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax.set_ylabel('Portfolio value ($)')
ax.set_title('Out-of-sample equity curves, 2020–2025 ($10,000 initial)', fontsize=12)
ax.legend(frameon=False)

plt.tight_layout()
fig.savefig(FIG_DIR / 'G3_oos_equity.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print("  [OK] G3_oos_equity.png")

# =============================================================================
# G4 — CRASH ACTIVATIONS TIMELINE
# =============================================================================

print("\n[G4] Crash activations...")
crash_mask = monthly['crash_detected'].astype(bool)
crash_dates = monthly.index[crash_mask]

fig, axes = plt.subplots(2, 1, figsize=(9, 5), sharex=True,
                         gridspec_kw={'height_ratios': [3, 1]})

ax1, ax2 = axes
ax1.plot(s36_eq.index, s36_eq.values, color=C_STRATEGY, lw=1.8, label='S3.6 equity')
for d in crash_dates:
    ax1.axvline(d, color=C_CRASH, lw=0.8, alpha=0.5)
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'${x:,.0f}'))
ax1.set_ylabel('Portfolio value ($)')
ax1.legend(frameon=False, fontsize=9)

ax2.vlines(crash_dates, 0, 1, color=C_CRASH, lw=1.5, label='Crash trigger')
ax2.set_yticks([])
ax2.set_ylabel('Triggers', fontsize=9)
ax2.legend(frameon=False, fontsize=9)

fig.suptitle('S3.6 crash filter activations, 2008–2025', fontsize=12)
plt.tight_layout()
fig.savefig(FIG_DIR / 'G4_crash_activations.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print("  [OK] G4_crash_activations.png")

# =============================================================================
# G5 — REGIME BAR CHART
# =============================================================================

print("\n[G5] Regime bar chart...")
regimes   = ['BULL', 'SIDEWAYS', 'BEAR', 'CRISIS']
s36_cagr  = [16.20, 8.41, -23.18, 14.74]
b6040_cag = [15.21, 4.96,  20.59, -37.28]

x = np.arange(len(regimes))
w = 0.35

fig, ax = plt.subplots(figsize=(8, 4))
bars1 = ax.bar(x - w/2, s36_cagr,  w, label='S3.6',         color=C_STRATEGY, alpha=0.9)
bars2 = ax.bar(x + w/2, b6040_cag, w, label='60/40',        color=C_60_40,    alpha=0.9)

ax.axhline(0, color='black', lw=0.8)
ax.set_xticks(x)
ax.set_xticklabels(regimes)
ax.set_ylabel('Annualised CAGR (%)')
ax.set_title('Performance by market regime, 2008–2025', fontsize=12)
ax.legend(frameon=False)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda y, _: f'{y:.0f}%'))

plt.tight_layout()
fig.savefig(FIG_DIR / 'G5_regime_bar.png', dpi=200, bbox_inches='tight')
plt.close(fig)
print("  [OK] G5_regime_bar.png")

# =============================================================================
# G6 — MONTE CARLO CAGR AND MAXDD DISTRIBUTIONS
# =============================================================================

print("\n[G6] Monte Carlo distribution...")
mc_raw = RESULTS_DIR / 's36_montecarlo_raw.csv'
if not mc_raw.exists():
    print("  [SKIP] s36_montecarlo_raw.csv not found. Run s36_montecarlo.py first.")
else:
    mc = pd.read_csv(mc_raw)
    sim_cagr = mc['cagr'].to_numpy() * 100
    sim_maxdd = mc['maxdd'].to_numpy() * 100
    block = int(mc['block_length'].mode().iloc[0])
    n_sim = len(mc)

    hist_cagr = ((1 + s36_ret).prod() ** (12 / len(s36_ret)) - 1) * 100
    hist_maxdd = drawdown_series(s36_eq).min()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    ax = axes[0]
    ax.hist(sim_cagr, bins=70, color=C_STRATEGY, alpha=0.72,
            edgecolor='white', linewidth=0.3)
    ax.axvline(np.percentile(sim_cagr, 10), color=C_CRASH, lw=1.4,
               linestyle='--', label=f'P10: {np.percentile(sim_cagr, 10):.1f}%')
    ax.axvline(np.percentile(sim_cagr, 50), color='green', lw=1.4,
               linestyle='--', label=f'P50: {np.percentile(sim_cagr, 50):.1f}%')
    ax.axvline(hist_cagr, color='black', lw=1.4, linestyle='-',
               label=f'Historical: {hist_cagr:.1f}%')
    ax.axvline(7, color=C_60_40, lw=1.1, linestyle=':',
               label='Corporate threshold: 7%')
    ax.set_xlabel('Simulated CAGR (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('CAGR distribution', fontsize=12)
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    ax.hist(sim_maxdd, bins=70, color=C_BENCH, alpha=0.72,
            edgecolor='white', linewidth=0.3)
    ax.axvline(np.percentile(sim_maxdd, 10), color=C_CRASH, lw=1.4,
               linestyle='--', label=f'P10: {np.percentile(sim_maxdd, 10):.1f}%')
    ax.axvline(np.percentile(sim_maxdd, 50), color='green', lw=1.4,
               linestyle='--', label=f'P50: {np.percentile(sim_maxdd, 50):.1f}%')
    ax.axvline(hist_maxdd, color='black', lw=1.4, linestyle='-',
               label=f'Historical: {hist_maxdd:.1f}%')
    ax.axvline(-15, color=C_60_40, lw=1.1, linestyle=':',
               label='Drawdown limit: -15%')
    ax.set_xlabel('Simulated maximum drawdown (%)')
    ax.set_ylabel('Frequency')
    ax.set_title('Maximum drawdown distribution', fontsize=12)
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle(f'Monte Carlo bootstrap distributions (N={n_sim:,}, block={block}m)',
                 fontsize=13)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / 'G6_montecarlo_cagr.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("  [OK] G6_montecarlo_cagr.png")

# =============================================================================
# G8 — STRATEGY-LEVEL MONTE CARLO COMPARISON
# =============================================================================

print("\n[G8] Strategy-level Monte Carlo comparison...")
mc_strategy_raw = RESULTS_DIR / 's36_montecarlo_strategy_raw.csv'
if not mc_strategy_raw.exists():
    print("  [SKIP] s36_montecarlo_strategy_raw.csv not found. Run s36_montecarlo_strategy.py first.")
else:
    mc_s = pd.read_csv(mc_strategy_raw)

    data_cagr = [
        mc_s['s36_cagr'].to_numpy() * 100,
        mc_s['b6040_cagr'].to_numpy() * 100,
        mc_s['spy_cagr'].to_numpy() * 100,
    ]
    data_dd = [
        mc_s['s36_maxdd'].to_numpy() * 100,
        mc_s['b6040_maxdd'].to_numpy() * 100,
        mc_s['spy_maxdd'].to_numpy() * 100,
    ]
    labels = ['S3.6', '60/40', 'SPY']
    colors = [C_STRATEGY, C_60_40, C_BENCH]

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))

    ax = axes[0]
    bp = ax.boxplot(data_cagr, labels=labels, patch_artist=True, showfliers=False)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    ax.axhline(7, color=C_CRASH, linestyle=':', linewidth=1.2, label='CAGR target: 7%')
    ax.set_ylabel('CAGR (%)')
    ax.set_title('CAGR by strategy-level bootstrap path', fontsize=12)
    ax.legend(frameon=False, fontsize=8)

    ax = axes[1]
    bp = ax.boxplot(data_dd, labels=labels, patch_artist=True, showfliers=False)
    for patch, color in zip(bp['boxes'], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.65)
    ax.axhline(-15, color=C_CRASH, linestyle=':', linewidth=1.2, label='Drawdown limit: -15%')
    ax.set_ylabel('Maximum drawdown (%)')
    ax.set_title('Drawdown by strategy-level bootstrap path', fontsize=12)
    ax.legend(frameon=False, fontsize=8)

    fig.suptitle('Strategy-level Monte Carlo: S3.6 versus benchmarks (N=10,000)',
                 fontsize=13)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(FIG_DIR / 'G8_montecarlo_strategy.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("  [OK] G8_montecarlo_strategy.png")

# =============================================================================
# G7 — THRESHOLD SENSITIVITY
# =============================================================================

print("\n[G7] Threshold sensitivity...")
thresh_file = RESULTS_DIR / 's36_threshold_sensitivity.csv'
if not thresh_file.exists():
    print("  [SKIP] s36_threshold_sensitivity.csv not found. Run s36_threshold_sensitivity.py first.")
else:
    ts = pd.read_csv(thresh_file)
    taus = ts['tau_pct'].values

    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()

    ax1.plot(taus, ts['CAGR']*100, color=C_STRATEGY, lw=2, marker='o', label='CAGR (left)')
    ax2.plot(taus, ts['Sharpe'],    color=C_60_40,    lw=2, marker='s', linestyle='--', label='Sharpe (right)')

    ax1.axvline(-4.0, color='black', lw=0.8, linestyle=':', label='Selected τ = -4%')
    ax1.set_xlabel('Crash threshold τ (%)')
    ax1.set_ylabel('In-sample CAGR (%)', color=C_STRATEGY)
    ax2.set_ylabel('Sharpe ratio', color=C_60_40)
    ax1.set_title('Crash filter threshold sensitivity — in-sample (2008–2019)', fontsize=12)

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, frameon=False, fontsize=9)

    ax1.invert_xaxis()   # from -2% to -5% left to right

    plt.tight_layout()
    fig.savefig(FIG_DIR / 'G7_threshold_sensitivity.png', dpi=200, bbox_inches='tight')
    plt.close(fig)
    print("  [OK] G7_threshold_sensitivity.png")

# =============================================================================
# SUMMARY
# =============================================================================

print("\n" + "=" * 70)
generated = list(FIG_DIR.glob('G*.png'))
print(f"Figures in {FIG_DIR}:")
for f in sorted(generated):
    print(f"  {f.name}")
print("=" * 70)
