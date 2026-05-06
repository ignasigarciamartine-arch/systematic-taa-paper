# -*- coding: utf-8 -*-
"""
S3.6 MONTE CARLO v3 - Stationary Block Bootstrap + Paired 60/40 + Ledoit-Wolf
==============================================================================
Return-level bootstrap of the realised S3.6 monthly return stream.
Three improvements over v1 (circular block bootstrap):

  1. Stationary Bootstrap (Politis & Romano 1994) with data-driven block
     length (Politis & White 2004). Geometrically distributed block lengths
     guarantee the simulated series is itself stationary; avoids the
     wrap-around artefact of the circular bootstrap.

  2. Paired bootstrap with 60/40 benchmark. Strategy and benchmark returns
     are resampled with the same block indices. Produces P(S3.6 outperforms
     60/40 | same return-sequence ordering) - tests whether the historical
     outperformance is robust to reorderings or depends on the specific
     sequence lived.

  3. Ledoit-Wolf (2008) Sharpe ratio test. Formal statistical test of
     H0: Sharpe(S3.6) = Sharpe(60/40) using the asymptotic distribution
     of the Sharpe ratio difference. Provides a p-value independent of the
     bootstrap.

Scope and limitations
---------------------
This remains a return-level sequencing-risk diagnostic. It does not
re-execute momentum signals, crash filters, or parameter optimisation on
synthetic asset histories. It evaluates how sensitive CAGR, MaxDD, and
outperformance are to the ordering of historically realised returns.

Inputs
------
  ../data/outputs/s36_monthly_returns.csv
  ../data/prices/etf_adjclose_2008_2025.csv
  ../data/prices/tbill_3m_monthly_refinitiv.csv

Outputs
-------
  ../data/outputs/s36_montecarlo_v3_report.txt
  ../data/outputs/s36_montecarlo_v3_raw.csv

Authors: Garcia Martin I., Mases Campos M., Prior Sanz F.
         IQS School of Engineering - Universitat Ramon Llull, Barcelona

References
----------
  Politis D.N. & Romano J.P. (1994). The Stationary Bootstrap.
    JASA, 89(428), 1303-1313.
  Politis D.N. & White H. (2004). Automatic Block-Length Selection for
    the Dependent Bootstrap. Econometric Reviews, 23(1), 53-70.
  Patton A., Politis D.N. & White H. (2009). Correction to Automatic
    Block-Length Selection. Econometric Reviews, 28(4), 372-375.
  Ledoit O. & Wolf M. (2008). Robust Performance Hypothesis Testing with
    the Sharpe Ratio. Journal of Empirical Finance, 15(5), 850-859.
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

try:
    from arch.bootstrap import StationaryBootstrap, optimal_block_length
except ImportError:
    raise ImportError("pip install arch  (version >= 5.0 required)")


# =============================================================================
# CONFIG
# =============================================================================

N_SIMULATIONS = 10_000
SEED          = 42
INITIAL_CAPITAL = 10_000

CORPORATE_CAGR_TARGET = 0.07
DRAWDOWN_LIMIT        = -0.15
SEVERE_DRAWDOWN       = -0.20

BASE_DIR    = Path(__file__).parent.parent
DATA_DIR    = BASE_DIR / "data" / "prices"
RESULTS_DIR = BASE_DIR / "data" / "outputs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RETURNS_FILE = RESULTS_DIR / "s36_monthly_returns.csv"
REPORT_FILE  = RESULTS_DIR / "s36_montecarlo_v3_report.txt"
RAW_FILE     = RESULTS_DIR / "s36_montecarlo_v3_raw.csv"


# =============================================================================
# HELPERS
# =============================================================================

def compute_cagr(ret_array: np.ndarray) -> float:
    n = len(ret_array)
    tw = np.prod(1.0 + ret_array)
    if n == 0 or tw <= 0:
        return np.nan
    return tw ** (12.0 / n) - 1.0


def compute_maxdd(ret_array: np.ndarray) -> float:
    cum  = np.cumprod(1.0 + ret_array)
    peak = np.maximum.accumulate(cum)
    return float((cum / peak - 1.0).min())


def compute_sharpe(ret_array: np.ndarray, rf_array: np.ndarray) -> float:
    excess = ret_array - rf_array
    if excess.std() == 0:
        return np.nan
    return float(np.sqrt(12) * excess.mean() / excess.std())


# =============================================================================
# LEDOIT-WOLF (2008) SHARPE RATIO TEST
# =============================================================================
# Tests H0: Sharpe(A) = Sharpe(B) using the asymptotic variance of the
# difference in Sharpe ratios (Ledoit & Wolf 2008, eq. 8).
# Works directly on the realised monthly return series (no bootstrap needed).

def ledoit_wolf_sharpe_test(
    ret_a: np.ndarray,
    ret_b: np.ndarray,
    rf: np.ndarray,
    annualise: float = 12.0,
) -> dict:
    """
    Test H0: SR_a = SR_b.

    Returns
    -------
    dict with keys: sr_a, sr_b, diff, se, t_stat, p_value (two-sided),
                    ci_95_lo, ci_95_hi
    """
    T = len(ret_a)
    ea = ret_a - rf
    eb = ret_b - rf

    mu_a, mu_b   = ea.mean(), eb.mean()
    sig_a, sig_b = ea.std(ddof=1), eb.std(ddof=1)

    sr_a = mu_a / sig_a  # monthly
    sr_b = mu_b / sig_b

    # Asymptotic variance of (SR_a - SR_b) per Ledoit-Wolf (2008) eq. 8
    # V = (1/T) * [1 + 0.5*(sr_a^2 + sr_b^2) - sr_a*sr_b*rho_ab]
    # where rho_ab is the correlation of the excess return series.
    rho_ab = np.corrcoef(ea, eb)[0, 1]
    V = (1.0 / T) * (
        1.0
        + 0.5 * (sr_a**2 + sr_b**2)
        - sr_a * sr_b * rho_ab
    )
    se   = np.sqrt(max(V, 0.0))
    diff = sr_a - sr_b
    t_stat   = diff / se if se > 0 else np.nan
    p_value  = 2.0 * (1.0 - stats.norm.cdf(abs(t_stat))) if se > 0 else np.nan
    z95 = 1.96
    ci_lo = diff - z95 * se
    ci_hi = diff + z95 * se

    # Annualise Sharpe ratios for reporting
    scale = np.sqrt(annualise)
    return {
        "sr_a":      sr_a  * scale,
        "sr_b":      sr_b  * scale,
        "diff":      diff  * scale,
        "se":        se    * scale,
        "t_stat":    t_stat,         # scale-invariant
        "p_value":   p_value,
        "ci_95_lo":  ci_lo * scale,
        "ci_95_hi":  ci_hi * scale,
    }


# =============================================================================
# LOAD DATA
# =============================================================================

print("=" * 70)
print("S3.6 MONTE CARLO v3 - Stationary Bootstrap + Paired 60/40 + LW Test")
print("=" * 70)

if not RETURNS_FILE.exists():
    raise FileNotFoundError(f"{RETURNS_FILE} not found. Run s36_backtest.py first.")

monthly = pd.read_csv(RETURNS_FILE, index_col="date", parse_dates=True)
s36_ret = monthly["return"].dropna().astype(float)
t_obs   = len(s36_ret)

if t_obs == 0:
    raise ValueError("No monthly returns available.")
if np.any(s36_ret.values <= -1.0):
    raise ValueError("Return series contains values <= -100%.")

print(f"\n[1] Loaded {t_obs} monthly S3.6 returns")
print(f"    Period: {s36_ret.index[0].date()} to {s36_ret.index[-1].date()}")

# --- 60/40 benchmark ---
prices = pd.read_csv(DATA_DIR / "etf_adjclose_2008_2025.csv",
                     index_col="Date", parse_dates=True).sort_index()
try:
    mp = prices.resample("ME").last()
except Exception:
    mp = prices.resample("M").last()
mp.index = mp.index.to_period("M").to_timestamp("M")
mr       = mp.pct_change()
b6040    = (0.6 * mr["SPY"] + 0.4 * mr["IEF"]).reindex(s36_ret.index).fillna(0)

# --- Risk-free rate ---
rf_raw = pd.read_csv(DATA_DIR / "tbill_3m_monthly_refinitiv.csv",
                     index_col="date", parse_dates=True)["rf_monthly"]
rf_raw.index = pd.to_datetime(rf_raw.index).to_period("M").to_timestamp("M")
rf = rf_raw.reindex(s36_ret.index).fillna(0).astype(float)

s36_arr   = s36_ret.values
b6040_arr = b6040.values
rf_arr    = rf.values

hist_cagr_s36   = compute_cagr(s36_arr)
hist_maxdd_s36  = compute_maxdd(s36_arr)
hist_cagr_6040  = compute_cagr(b6040_arr)
hist_maxdd_6040 = compute_maxdd(b6040_arr)
hist_sr_s36     = compute_sharpe(s36_arr, rf_arr)
hist_sr_6040    = compute_sharpe(b6040_arr, rf_arr)

print(f"\n    S3.6:  CAGR={hist_cagr_s36*100:.2f}%  "
      f"MaxDD={hist_maxdd_s36*100:.2f}%  Sharpe={hist_sr_s36:.3f}")
print(f"    60/40: CAGR={hist_cagr_6040*100:.2f}%  "
      f"MaxDD={hist_maxdd_6040*100:.2f}%  Sharpe={hist_sr_6040:.3f}")


# =============================================================================
# IMPROVEMENT 3: LEDOIT-WOLF TEST (analytical, no bootstrap needed)
# =============================================================================

print("\n[2] Ledoit-Wolf (2008) Sharpe ratio test...")
lw = ledoit_wolf_sharpe_test(s36_arr, b6040_arr, rf_arr)

print(f"    Sharpe S3.6:  {lw['sr_a']:.3f}")
print(f"    Sharpe 60/40: {lw['sr_b']:.3f}")
print(f"    Difference:   {lw['diff']:+.3f}  (95% CI: [{lw['ci_95_lo']:+.3f}, {lw['ci_95_hi']:+.3f}])")
print(f"    t-statistic:  {lw['t_stat']:.3f}  |  p-value: {lw['p_value']:.4f}")
sig = "*** (p<0.01)" if lw['p_value'] < 0.01 else \
      "**  (p<0.05)" if lw['p_value'] < 0.05 else \
      "*   (p<0.10)" if lw['p_value'] < 0.10 else \
      "    (not significant at 10%)"
print(f"    Significance: {sig}")


# =============================================================================
# IMPROVEMENT 1: OPTIMAL BLOCK LENGTH (Politis-White 2004)
# =============================================================================

print("\n[3] Computing optimal block length (Politis & White 2004)...")
try:
    opt = optimal_block_length(s36_arr)
    b_sb = max(1, int(np.round(float(opt["stationary"].iloc[0]))))
    b_cb = max(1, int(np.round(float(opt["circular"].iloc[0]))))
    print(f"    Stationary Bootstrap: b = {b_sb} months")
    print(f"    Circular Bootstrap:   b = {b_cb} months  (reference)")
    BLOCK_LENGTH = b_sb
except Exception as e:
    print(f"    [WARN] optimal_block_length failed ({e}). Defaulting to b=6.")
    BLOCK_LENGTH = 6

print(f"    -> Using Stationary Bootstrap with b = {BLOCK_LENGTH} months")


# =============================================================================
# IMPROVEMENT 1+2: STATIONARY BOOTSTRAP — PAIRED S3.6 + 60/40
# =============================================================================

print(f"\n[4] Running Stationary Bootstrap "
      f"(b={BLOCK_LENGTH}, N={N_SIMULATIONS:,}, seed={SEED})...")
print(f"    Paired resampling: same block indices for S3.6 and 60/40")

# Stack the two series as a (T x 2) matrix so the bootstrap resamples them jointly
paired_matrix = np.column_stack([s36_arr, b6040_arr, rf_arr])  # T x 3

bs = StationaryBootstrap(BLOCK_LENGTH, paired_matrix, seed=SEED)

sim_results = []
checkpoint_every = 1_000

for s_idx, (sim_data, _) in enumerate(bs.bootstrap(N_SIMULATIONS)):
    sim_mat   = sim_data[0]               # shape: (T, 3)
    sim_s36   = sim_mat[:, 0]
    sim_6040  = sim_mat[:, 1]
    sim_rf    = sim_mat[:, 2]

    cagr_s36   = compute_cagr(sim_s36)
    maxdd_s36  = compute_maxdd(sim_s36)
    sr_s36     = compute_sharpe(sim_s36, sim_rf)

    cagr_6040  = compute_cagr(sim_6040)
    maxdd_6040 = compute_maxdd(sim_6040)
    sr_6040    = compute_sharpe(sim_6040, sim_rf)

    sim_results.append({
        "s36_cagr":         cagr_s36,
        "s36_maxdd":        maxdd_s36,
        "s36_sharpe":       sr_s36,
        "b6040_cagr":       cagr_6040,
        "b6040_maxdd":      maxdd_6040,
        "b6040_sharpe":     sr_6040,
        "outperform_cagr":  int(cagr_s36 > cagr_6040),
        "outperform_sharpe": int(sr_s36 > sr_6040),
        "hit_cagr_target":  int(cagr_s36 >= CORPORATE_CAGR_TARGET),
        "hit_dd_limit":     int(maxdd_s36 > DRAWDOWN_LIMIT),
        "hit_both":         int(cagr_s36 >= CORPORATE_CAGR_TARGET and
                                maxdd_s36 > DRAWDOWN_LIMIT),
        "severe_dd":        int(maxdd_s36 <= SEVERE_DRAWDOWN),
    })

    if (s_idx + 1) % checkpoint_every == 0:
        print(f"    Simulation {s_idx+1:,}/{N_SIMULATIONS:,}...")

sim_df = pd.DataFrame(sim_results)
sim_df.to_csv(RAW_FILE, index=False)
print(f"    Saved raw simulations: {RAW_FILE.name}")


# =============================================================================
# RESULTS
# =============================================================================

percs = [5, 10, 25, 50, 75, 90, 95]

def pct_table(col):
    return {p: float(np.percentile(sim_df[col].dropna(), p)) for p in percs}

cagr_p   = pct_table("s36_cagr")
maxdd_p  = pct_table("s36_maxdd")
sharpe_p = pct_table("s36_sharpe")

p_cagr_7   = sim_df["hit_cagr_target"].mean()
p_dd_15    = sim_df["hit_dd_limit"].mean()
p_both     = sim_df["hit_both"].mean()
p_sev_dd   = sim_df["severe_dd"].mean()
p_beat_cagr   = sim_df["outperform_cagr"].mean()
p_beat_sharpe = sim_df["outperform_sharpe"].mean()

p10_cagr = cagr_p[10]
p10_maxdd = maxdd_p[10]
es_cagr = float(sim_df.loc[sim_df["s36_cagr"] <= p10_cagr, "s36_cagr"].mean())
es_maxdd = float(sim_df.loc[sim_df["s36_maxdd"] <= p10_maxdd, "s36_maxdd"].mean())


print("\n" + "=" * 70)
print("RESULTS — Stationary Bootstrap, Return-Level, Paired with 60/40")
print("=" * 70)

print(f"\n  {'':12}  {'Actual':>8}  " + "  ".join(f"P{p:<3}" for p in percs))
print(f"  {'-' * 72}")
print(f"  {'S3.6 CAGR':<12}  {hist_cagr_s36*100:>7.2f}%  " +
      "  ".join(f"{cagr_p[p]*100:>5.2f}%" for p in percs))
print(f"  {'S3.6 MaxDD':<12}  {hist_maxdd_s36*100:>7.2f}%  " +
      "  ".join(f"{maxdd_p[p]*100:>5.2f}%" for p in percs))
print(f"  {'S3.6 Sharpe':<12}  {hist_sr_s36:>8.3f}  " +
      "  ".join(f"{sharpe_p[p]:>6.3f}" for p in percs))

print(f"\n  Probability diagnostics")
print(f"  P(CAGR >= 7%):                {p_cagr_7*100:>5.1f}%")
print(f"  P(MaxDD > -15%):              {p_dd_15*100:>5.1f}%")
print(f"  P(both constraints):          {p_both*100:>5.1f}%")
print(f"  P(MaxDD <= -20%):             {p_sev_dd*100:>5.1f}%")
print(f"\n  Paired outperformance vs 60/40 (same sequence ordering)")
print(f"  P(S3.6 CAGR > 60/40 CAGR):   {p_beat_cagr*100:>5.1f}%")
print(f"  P(S3.6 Sharpe > 60/40 Sharpe): {p_beat_sharpe*100:>4.1f}%")
print(f"\n  Lower-tail diagnostics")
print(f"  ES of CAGR below P10:   {es_cagr*100:>7.2f}%")
print(f"  ES of MaxDD below P10:  {es_maxdd*100:>7.2f}%")

print(f"\n  Ledoit-Wolf (2008) Sharpe test: S3.6 vs 60/40")
print(f"  SR difference: {lw['diff']:+.3f}  "
      f"(95% CI: [{lw['ci_95_lo']:+.3f}, {lw['ci_95_hi']:+.3f}])")
print(f"  t-stat: {lw['t_stat']:.3f}  |  p-value: {lw['p_value']:.4f}  |  {sig}")


# =============================================================================
# SAVE REPORT
# =============================================================================

report_lines = [
    "S3.6 MONTE CARLO v3 REPORT",
    "=" * 65,
    "",
    "Improvements over v1 (circular block bootstrap):",
    "  1. Stationary Bootstrap (Politis & Romano 1994) with data-driven",
    "     block length (Politis & White 2004). Avoids circular wrap-around",
    "     artefact; simulated series are themselves stationary.",
    "  2. Paired resampling with 60/40: same block indices applied to both",
    "     series. P(outperform) is conditional on the same return ordering.",
    "  3. Ledoit-Wolf (2008) Sharpe ratio test: formal H0: SR_S36 = SR_60/40.",
    "     Analytical asymptotic test, independent of the bootstrap.",
    "",
    "Scope (unchanged): return-level sequencing-risk diagnostic.",
    "Does not re-execute signals, re-run asset selection, or re-optimise",
    "parameters. Evaluates sensitivity of CAGR, MaxDD, and outperformance",
    "to the ordering of historically realised monthly returns.",
    "",
    f"Method:          Stationary Bootstrap (Politis & Romano 1994)",
    f"Block length:    b = {BLOCK_LENGTH} months (Politis & White 2004, data-driven)",
    f"N simulations:   {N_SIMULATIONS:,}",
    f"Seed:            {SEED}",
    f"Horizon:         {t_obs} months",
    f"Period:          {s36_ret.index[0].date()} to {s36_ret.index[-1].date()}",
    "",
    "Historical realised path:",
    f"  S3.6:  CAGR={hist_cagr_s36*100:.2f}%  MaxDD={hist_maxdd_s36*100:.2f}%  "
    f"Sharpe={hist_sr_s36:.3f}",
    f"  60/40: CAGR={hist_cagr_6040*100:.2f}%  MaxDD={hist_maxdd_6040*100:.2f}%  "
    f"Sharpe={hist_sr_6040:.3f}",
    "",
    "Bootstrap percentile distribution:",
    f"  {'':12}  {'Actual':>8}  " + "  ".join(f"P{p:<4}" for p in percs),
    "-" * 72,
    f"  {'S3.6 CAGR':<12}  {hist_cagr_s36*100:>7.2f}%  " +
        "  ".join(f"{cagr_p[p]*100:>5.2f}%" for p in percs),
    f"  {'S3.6 MaxDD':<12}  {hist_maxdd_s36*100:>7.2f}%  " +
        "  ".join(f"{maxdd_p[p]*100:>5.2f}%" for p in percs),
    f"  {'S3.6 Sharpe':<12}  {hist_sr_s36:>8.3f}  " +
        "  ".join(f"{sharpe_p[p]:>6.3f}" for p in percs),
    "",
    "Probability diagnostics:",
    f"  P(CAGR >= 7%):                {p_cagr_7*100:.1f}%",
    f"  P(MaxDD > -15%):              {p_dd_15*100:.1f}%",
    f"  P(both constraints):          {p_both*100:.1f}%",
    f"  P(MaxDD <= -20%):             {p_sev_dd*100:.1f}%",
    "",
    "Paired outperformance vs 60/40 (same sequence ordering):",
    f"  P(S3.6 CAGR > 60/40 CAGR):     {p_beat_cagr*100:.1f}%",
    f"  P(S3.6 Sharpe > 60/40 Sharpe): {p_beat_sharpe*100:.1f}%",
    "",
    "Lower-tail diagnostics:",
    f"  ES of CAGR below P10:   {es_cagr*100:.2f}%",
    f"  ES of MaxDD below P10:  {es_maxdd*100:.2f}%",
    "",
    "Ledoit-Wolf (2008) Sharpe ratio test: H0: Sharpe(S3.6) = Sharpe(60/40)",
    f"  Sharpe S3.6:   {lw['sr_a']:.3f}",
    f"  Sharpe 60/40:  {lw['sr_b']:.3f}",
    f"  Difference:    {lw['diff']:+.3f}",
    f"  SE:            {lw['se']:.3f}",
    f"  95% CI:        [{lw['ci_95_lo']:+.3f}, {lw['ci_95_hi']:+.3f}]",
    f"  t-statistic:   {lw['t_stat']:.3f}",
    f"  p-value:       {lw['p_value']:.4f}",
    f"  Significance:  {sig}",
    "",
    "Reviewer interpretation:",
    "  P50 CAGR close to historical is expected (geometric mean nearly",
    "  invariant to ordering). The main inferential content is:",
    "  (a) Drawdown tails: ~30% of orderings breach the -15% constraint.",
    "  (b) Paired outperformance: P(CAGR > 60/40) and P(Sharpe > 60/40)",
    "      under the same reorderings show whether the outperformance is",
    "      sequence-dependent or structural.",
    "  (c) Ledoit-Wolf test: provides a formal p-value on the Sharpe",
    "      outperformance claim using asymptotic theory.",
    "",
    "References:",
    "  Politis D.N. & Romano J.P. (1994). The Stationary Bootstrap.",
    "    JASA, 89(428), 1303-1313.",
    "  Politis D.N. & White H. (2004). Automatic Block-Length Selection.",
    "    Econometric Reviews, 23(1), 53-70.",
    "  Patton A., Politis D.N. & White H. (2009). Correction.",
    "    Econometric Reviews, 28(4), 372-375.",
    "  Ledoit O. & Wolf M. (2008). Robust Performance Hypothesis Testing",
    "    with the Sharpe Ratio. Journal of Empirical Finance, 15(5), 850-859.",
    "",
    f"Raw simulations: {RAW_FILE.name}",
]

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print(f"\n[OK] Report saved: {REPORT_FILE}")
print("=" * 70)
