# -*- coding: utf-8 -*-
"""
S3.6 MONTE CARLO - Circular Block Bootstrap
===========================================
Return-level bootstrap of the realised S3.6 monthly return stream.

Purpose
-------
This is a sequencing-risk diagnostic. It asks how CAGR and maximum drawdown
would vary if the realised monthly strategy returns arrived in different
dependent sequences. It does not generate new asset histories, does not
recompute signals, and does not re-optimise parameters.

Method
------
  - Circular block bootstrap on realised S3.6 monthly returns.
  - Primary specification: block length = 6 months, N = 10,000, seed = 42.
  - Sensitivity: block lengths 3, 6, 9, 12, and 18 months.

Inputs
------
  ../data/outputs/s36_monthly_returns.csv

Outputs
-------
  ../data/outputs/s36_montecarlo_report.txt
  ../data/outputs/s36_montecarlo_raw.csv
  ../data/outputs/s36_montecarlo_block_sensitivity.csv

Expected primary results with the current paper return file:
  CAGR  P10 ~=  8.34%  |  P50 ~= 11.51%  |  P90 ~= 14.75%
  MaxDD P10 ~= -18.61% |  P50 ~= -13.00% |  P90 ~=  -9.37%

Authors: Garcia Martin I., Mases Campos M., Prior Sanz F.
         IQS School of Engineering - Universitat Ramon Llull, Barcelona
"""

from pathlib import Path

import numpy as np
import pandas as pd


# =============================================================================
# CONFIG
# =============================================================================

BLOCK_LENGTH = 6
BLOCK_LENGTHS_SENSITIVITY = [3, 6, 9, 12, 18]
N_SIMULATIONS = 10_000
CHECKPOINT_EVERY = 1_000
SEED = 42
INITIAL_CAPITAL = 10_000

CORPORATE_CAGR_TARGET = 0.07
DRAWDOWN_LIMIT = -0.15
SEVERE_DRAWDOWN = -0.20

BASE_DIR = Path(__file__).parent.parent
RESULTS_DIR = BASE_DIR / "data" / "outputs"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

RETURNS_FILE = RESULTS_DIR / "s36_monthly_returns.csv"
REPORT_FILE = RESULTS_DIR / "s36_montecarlo_report.txt"
RAW_FILE = RESULTS_DIR / "s36_montecarlo_raw.csv"
SENSITIVITY_FILE = RESULTS_DIR / "s36_montecarlo_block_sensitivity.csv"
CHECKPOINT_DIR = RESULTS_DIR / "montecarlo_checkpoints"
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# HELPERS
# =============================================================================

def compute_cagr(ret_array: np.ndarray) -> float:
    n = len(ret_array)
    terminal_wealth = np.prod(1.0 + ret_array)
    if n == 0 or terminal_wealth <= 0:
        return np.nan
    return terminal_wealth ** (12.0 / n) - 1.0


def compute_maxdd(ret_array: np.ndarray) -> float:
    cumulative = np.cumprod(1.0 + ret_array)
    peak = np.maximum.accumulate(cumulative)
    drawdown = cumulative / peak - 1.0
    return float(drawdown.min())


def _compute_chunk_stats(
    returns: np.ndarray,
    block_length: int,
    starts: np.ndarray,
    simulation_start: int,
) -> pd.DataFrame:
    """Compute bootstrap statistics for a chunk of block-start indices."""
    t_obs = len(returns)
    offsets = np.arange(block_length)
    indices = (starts[:, :, None] + offsets) % t_obs
    indices = indices.reshape(len(starts), starts.shape[1] * block_length)[:, :t_obs]

    simulated = returns[indices]
    cumulative = np.cumprod(1.0 + simulated, axis=1)
    peaks = np.maximum.accumulate(cumulative, axis=1)
    drawdowns = cumulative / peaks - 1.0

    terminal_wealth = cumulative[:, -1]
    cagr = terminal_wealth ** (12.0 / t_obs) - 1.0
    maxdd = drawdowns.min(axis=1)

    out = pd.DataFrame({
        "simulation": np.arange(simulation_start, simulation_start + len(starts)),
        "block_length": block_length,
        "cagr": cagr,
        "maxdd": maxdd,
        "terminal_wealth_multiple": terminal_wealth,
        "final_capital": INITIAL_CAPITAL * terminal_wealth,
    })
    out["hit_cagr_target"] = out["cagr"] >= CORPORATE_CAGR_TARGET
    out["hit_drawdown_limit"] = out["maxdd"] > DRAWDOWN_LIMIT
    out["hit_both"] = out["hit_cagr_target"] & out["hit_drawdown_limit"]
    out["severe_drawdown"] = out["maxdd"] <= SEVERE_DRAWDOWN
    return out


def _load_checkpoint(path: Path, block_length: int, n_simulations: int) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()

    existing = pd.read_csv(path)
    if existing.empty:
        return existing

    existing = existing[existing["block_length"] == block_length].copy()
    existing = existing.sort_values("simulation").drop_duplicates("simulation", keep="last")
    existing = existing[existing["simulation"] <= n_simulations]
    return existing


def bootstrap_paths(
    returns: np.ndarray,
    block_length: int,
    n_simulations: int,
    seed: int,
    checkpoint_path: Path,
    label: str,
) -> pd.DataFrame:
    """Run a circular block bootstrap with checkpoint saves every 1,000 sims."""
    if block_length <= 0:
        raise ValueError("block_length must be positive")

    t_obs = len(returns)
    n_blocks = int(np.ceil(t_obs / block_length))
    rng = np.random.default_rng(seed)

    existing = _load_checkpoint(checkpoint_path, block_length, n_simulations)
    completed = len(existing)

    if completed >= n_simulations:
        print(f"    {label}: checkpoint already complete ({completed:,}/{n_simulations:,})")
        return existing.iloc[:n_simulations].copy()

    if completed > 0:
        # Advance RNG so resumed runs match an uninterrupted run with the same seed.
        rng.integers(0, t_obs, size=(completed, n_blocks))
        print(f"    {label}: resuming from {completed:,}/{n_simulations:,}")

    chunks = [existing] if not existing.empty else []
    write_header = not checkpoint_path.exists() or completed == 0

    for start in range(completed, n_simulations, CHECKPOINT_EVERY):
        chunk_size = min(CHECKPOINT_EVERY, n_simulations - start)
        starts = rng.integers(0, t_obs, size=(chunk_size, n_blocks))
        chunk = _compute_chunk_stats(
            returns=returns,
            block_length=block_length,
            starts=starts,
            simulation_start=start + 1,
        )
        chunk.to_csv(
            checkpoint_path,
            mode="a",
            header=write_header,
            index=False,
        )
        write_header = False
        chunks.append(chunk)
        print(f"    {label}: checkpoint saved {start + chunk_size:,}/{n_simulations:,}")

    return pd.concat(chunks, ignore_index=True)


def percentile_map(series: pd.Series, percentiles: list[int]) -> dict[int, float]:
    return {p: float(np.percentile(series.dropna(), p)) for p in percentiles}


def summarise_simulations(sim: pd.DataFrame) -> dict[str, float]:
    cagr = sim["cagr"]
    maxdd = sim["maxdd"]
    p10_cagr = np.percentile(cagr, 10)
    p10_maxdd = np.percentile(maxdd, 10)

    return {
        "n": len(sim),
        "p_cagr_ge_7": float((cagr >= CORPORATE_CAGR_TARGET).mean()),
        "p_maxdd_gt_15": float((maxdd > DRAWDOWN_LIMIT).mean()),
        "p_both": float(((cagr >= CORPORATE_CAGR_TARGET) & (maxdd > DRAWDOWN_LIMIT)).mean()),
        "p_maxdd_le_20": float((maxdd <= SEVERE_DRAWDOWN).mean()),
        "cagr_expected_shortfall_p10": float(cagr[cagr <= p10_cagr].mean()),
        "maxdd_expected_shortfall_p10": float(maxdd[maxdd <= p10_maxdd].mean()),
    }


def format_pct(value: float) -> str:
    return f"{value * 100:,.2f}%"


def format_prob(value: float) -> str:
    return f"{value * 100:,.1f}%"


# =============================================================================
# LOAD RETURNS
# =============================================================================

print("=" * 70)
print("S3.6 MONTE CARLO - Circular Block Bootstrap")
print("=" * 70)
print(f"Primary block length: {BLOCK_LENGTH} months | N: {N_SIMULATIONS:,} | Seed: {SEED}")

if not RETURNS_FILE.exists():
    raise FileNotFoundError(f"{RETURNS_FILE} not found. Run s36_backtest.py first.")

monthly = pd.read_csv(RETURNS_FILE, index_col="date", parse_dates=True)
returns = monthly["return"].dropna().astype(float).values
t_obs = len(returns)

if t_obs == 0:
    raise ValueError("No monthly returns available for Monte Carlo.")
if np.any(returns <= -1.0):
    raise ValueError("Return series contains values <= -100%; CAGR is undefined.")

hist_cagr = compute_cagr(returns)
hist_maxdd = compute_maxdd(returns)

print(f"\n[1] Loaded {t_obs} monthly returns from {RETURNS_FILE.name}")
print(f"    Historical CAGR:  {hist_cagr * 100:.2f}%")
print(f"    Historical MaxDD: {hist_maxdd * 100:.2f}%")


# =============================================================================
# PRIMARY BOOTSTRAP
# =============================================================================

print("\n[2] Running primary bootstrap...")
primary = bootstrap_paths(
    returns=returns,
    block_length=BLOCK_LENGTH,
    n_simulations=N_SIMULATIONS,
    seed=SEED,
    checkpoint_path=RAW_FILE,
    label=f"primary b={BLOCK_LENGTH}",
)
primary.to_csv(RAW_FILE, index=False)
print(f"    Saved raw simulations: {RAW_FILE}")

percentiles = [5, 10, 25, 50, 75, 90, 95]
cagr_p = percentile_map(primary["cagr"], percentiles)
maxdd_p = percentile_map(primary["maxdd"], percentiles)
summary = summarise_simulations(primary)


# =============================================================================
# BLOCK-LENGTH SENSITIVITY
# =============================================================================

print("\n[3] Running block-length sensitivity...")
sensitivity_rows = []

for block_length in BLOCK_LENGTHS_SENSITIVITY:
    checkpoint_path = CHECKPOINT_DIR / f"s36_montecarlo_b{block_length:02d}_raw.csv"
    sim = bootstrap_paths(
        returns=returns,
        block_length=block_length,
        n_simulations=N_SIMULATIONS,
        seed=SEED,
        checkpoint_path=checkpoint_path,
        label=f"sensitivity b={block_length}",
    )
    sim_summary = summarise_simulations(sim)
    row = {
        "block_length": block_length,
        "n_simulations": N_SIMULATIONS,
        "cagr_p10": np.percentile(sim["cagr"], 10),
        "cagr_p50": np.percentile(sim["cagr"], 50),
        "cagr_p90": np.percentile(sim["cagr"], 90),
        "maxdd_p10": np.percentile(sim["maxdd"], 10),
        "maxdd_p50": np.percentile(sim["maxdd"], 50),
        "maxdd_p90": np.percentile(sim["maxdd"], 90),
        **{k: v for k, v in sim_summary.items() if k != "n"},
    }
    sensitivity_rows.append(row)
    print(
        f"    b={block_length:>2}: "
        f"P10 CAGR {row['cagr_p10'] * 100:>6.2f}% | "
        f"P10 MaxDD {row['maxdd_p10'] * 100:>7.2f}% | "
        f"P(both) {row['p_both'] * 100:>5.1f}%"
    )

sensitivity = pd.DataFrame(sensitivity_rows)
sensitivity.to_csv(SENSITIVITY_FILE, index=False)
print(f"    Saved block sensitivity: {SENSITIVITY_FILE}")


# =============================================================================
# CONSOLE OUTPUT
# =============================================================================

print("\n" + "=" * 70)
print("MONTE CARLO RESULTS - PRIMARY SPECIFICATION")
print("=" * 70)
print(f"\n  {'Percentile':<12}  {'CAGR':>8}  {'Max DD':>10}")
print(f"  {'-' * 35}")
for p in percentiles:
    print(f"  P{p:<10}  {cagr_p[p] * 100:>8.2f}%  {maxdd_p[p] * 100:>10.2f}%")

print("\n  Probability diagnostics")
print(f"  P(CAGR >= 7%):       {summary['p_cagr_ge_7'] * 100:>5.1f}%")
print(f"  P(MaxDD > -15%):     {summary['p_maxdd_gt_15'] * 100:>5.1f}%")
print(f"  P(both constraints): {summary['p_both'] * 100:>5.1f}%")
print(f"  P(MaxDD <= -20%):    {summary['p_maxdd_le_20'] * 100:>5.1f}%")


# =============================================================================
# VERIFICATION
# =============================================================================

print("\n" + "=" * 70)
print("VERIFICATION")
print("=" * 70)

checks = [
    ("P10 CAGR", cagr_p[10] * 100, 8.34, 0.30),
    ("P50 CAGR", cagr_p[50] * 100, 11.51, 0.30),
    ("P90 CAGR", cagr_p[90] * 100, 14.75, 0.30),
    ("P10 MaxDD", maxdd_p[10] * 100, -18.61, 0.50),
    ("P50 MaxDD", maxdd_p[50] * 100, -13.00, 0.50),
]

all_ok = True
for name, got, expected, tolerance in checks:
    ok = abs(got - expected) <= tolerance
    status = "OK" if ok else "FAIL"
    print(f"  [{status}] {name:<12} expected {expected:+.2f}, got {got:+.2f}")
    all_ok = all_ok and ok

if all_ok:
    print("\n  [OK] All primary checks passed.")
else:
    print("\n  [WARN] Some checks differ. Review seed, block length, or return file.")


# =============================================================================
# REPORT
# =============================================================================

report_lines = [
    "S3.6 MONTE CARLO REPORT",
    "=" * 60,
    "",
    "Method: Circular block bootstrap of realised monthly strategy returns",
    f"Primary block length: {BLOCK_LENGTH} months",
    f"Block sensitivity: {', '.join(str(b) for b in BLOCK_LENGTHS_SENSITIVITY)} months",
    f"Simulations: {N_SIMULATIONS:,} per block length",
    f"Checkpoint frequency: every {CHECKPOINT_EVERY:,} simulations",
    f"Seed: {SEED}",
    f"Horizon: {t_obs} months (same as full backtest)",
    "",
    "Scope and limitation:",
    "  This is a return-level sequencing-risk diagnostic.",
    "  It does not re-estimate signals, re-run the asset-selection algorithm,",
    "  simulate unseen market states, or account for parameter uncertainty.",
    "",
    "Historical realised path:",
    f"  CAGR:  {format_pct(hist_cagr)}",
    f"  MaxDD: {format_pct(hist_maxdd)}",
    "",
    "Primary bootstrap percentiles:",
    f"{'Percentile':<12}  {'CAGR':>8}  {'Max DD':>10}",
    "-" * 35,
]

for p in percentiles:
    report_lines.append(f"P{p:<10}  {format_pct(cagr_p[p]):>8}  {format_pct(maxdd_p[p]):>10}")

report_lines.extend([
    "",
    "Probability diagnostics:",
    f"  P(CAGR >= 7%):       {format_prob(summary['p_cagr_ge_7'])}",
    f"  P(MaxDD > -15%):     {format_prob(summary['p_maxdd_gt_15'])}",
    f"  P(both constraints): {format_prob(summary['p_both'])}",
    f"  P(MaxDD <= -20%):    {format_prob(summary['p_maxdd_le_20'])}",
    "",
    "Lower-tail diagnostics:",
    f"  Expected shortfall of CAGR below P10:  {format_pct(summary['cagr_expected_shortfall_p10'])}",
    f"  Expected shortfall of MaxDD below P10: {format_pct(summary['maxdd_expected_shortfall_p10'])}",
    "",
    "Block-length sensitivity:",
    f"{'b':>4}  {'P10 CAGR':>10}  {'P50 CAGR':>10}  {'P90 CAGR':>10}  "
    f"{'P10 MaxDD':>10}  {'P(MaxDD>-15%)':>14}  {'P(both)':>8}",
    "-" * 82,
])

for _, row in sensitivity.iterrows():
    report_lines.append(
        f"{int(row['block_length']):>4}  "
        f"{format_pct(row['cagr_p10']):>10}  "
        f"{format_pct(row['cagr_p50']):>10}  "
        f"{format_pct(row['cagr_p90']):>10}  "
        f"{format_pct(row['maxdd_p10']):>10}  "
        f"{format_prob(row['p_maxdd_gt_15']):>14}  "
        f"{format_prob(row['p_both']):>8}"
    )

report_lines.extend([
    "",
    "Reviewer interpretation:",
    "  Median CAGR close to historical CAGR is expected because the return set is",
    "  resampled from the realised strategy path. It is an implementation check,",
    "  not independent evidence of alpha or signal robustness.",
    "  The main inferential content is in drawdown tails and block-length",
    "  sensitivity. These show residual path dependence: the historical -15%",
    "  drawdown constraint is satisfied in the realised path, but not guaranteed",
    "  across all bootstrap orderings.",
    "",
    f"Raw simulations: {RAW_FILE.name}",
    f"Block sensitivity CSV: {SENSITIVITY_FILE.name}",
    f"Sensitivity checkpoints: {CHECKPOINT_DIR.name}/",
])

with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines) + "\n")

print(f"\n[OK] Report saved: {REPORT_FILE}")
print("=" * 70)
