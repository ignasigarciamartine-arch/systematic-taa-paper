# AUDIT.md — Trazabilidad de números del paper
> Fuente única de verdad para todos los valores numéricos del paper.
> Actualizar cada vez que se regeneren outputs.
> Última verificación: 05 May 2026

---

## Convención rf

Todos los Sharpe y Sortino del paper usan **rf = 3M U.S. T-bill mensual**
(serie `aUSTRB3AV` de Refinitiv/Federal Reserve, archivo `data/prices/tbill_3m_monthly_refinitiv.csv`).
El CAGR y el MaxDD se computan sobre retornos brutos (no excess).

**Diferencia con RESULTS.md del TFM**: ese archivo usa rf=0 para Sharpe/Sortino.
Los CAGR y MaxDD del paper y del TFM deben coincidir si el código base es el mismo.
Discrepancias menores en MaxDD (-13.79% paper vs -13.87% TFM) reflejan versiones
distintas del código de backtest.

---

## Tabla 1 — Evolución de la estrategia (in-sample 2008-2019)

| Estrategia            | CAGR     | Sharpe | Max DD   | Fuente              |
|-----------------------|----------|--------|----------|---------------------|
| Base (momentum+cash)  | 8.75%    | 0.823  | -14.02%  | s36_backtest.py     |
| + Enhanced defensive  | 10.75%   | 0.933  | -13.79%  | s36_backtest.py     |
| Full S3.6             | **10.94%** | **0.951** | **-13.79%** | s36_backtest.py + s36_summary_report.txt ✓ |

Verificado: `s36_summary_report.txt` → TRAIN CAGR 10.94%, Sharpe 0.951, MaxDD -13.79%

---

## Tabla 2 — Sensibilidad del crash threshold (in-sample 2008-2019)

Script: `code/s36_threshold_sensitivity.py`
Output: `data/outputs/s36_threshold_report.txt`

| τ     | CAGR   | Sharpe | Max DD   | Triggers |
|-------|--------|--------|----------|----------|
| -2.0% | 10.94% | 0.945  | -13.79%  | 28       |
| -2.5% | 10.36% | 0.901  | -13.79%  | 19       |
| -3.0% | 10.47% | 0.916  | -13.79%  | 16       |
| -3.5% | 10.47% | 0.916  | -13.79%  | 16       |
| **-4.0%** | **10.94%** | **0.951** | **-13.79%** | **12** |
| -4.5% | 10.76% | 0.934  | -13.79%  | 10       |
| -5.0% | 10.81% | 0.938  | -13.79%  | 8        |

⚠ Pendiente re-verificar con `s36_threshold_sensitivity.py` (script creado 05 May 2026).

---

## Tabla 3 — OOS (2020-2025)

Script: `code/s36_backtest.py`
Output: `data/outputs/s36_summary_report.txt`

| Métrica   | S3.6   | Fuente verificada |
|-----------|--------|-------------------|
| CAGR      | 12.54% | s36_summary_report.txt ✓ |
| Vol       | 9.30%  | s36_backtest.py   |
| Sharpe    | 1.029  | s36_summary_report.txt ✓ |
| Sortino   | 1.808  | s36_summary_report.txt ✓ |
| Max DD    | -10.84% | s36_summary_report.txt ✓ |
| Win Rate  | 77.78% | s36_summary_report.txt ✓ |
| Final cap | $20,312 | s36_summary_report.txt ✓ |
| Triggers  | 9      | s36_summary_report.txt ✓ |

---

## Tabla 4 — Full period (2008-2025)

Script: `code/s36_backtest.py`
Benchmarks: calculados con SPY + IEF de `etf_adjclose_2008_2025.csv`

| Estrategia | CAGR   | Vol    | Sharpe | Sortino | Max DD   | Win Rate | Final   |
|------------|--------|--------|--------|---------|----------|----------|---------|
| S3.6       | 11.47% | 10.41% | 0.974  | 1.788   | -13.79%  | 69.63%   | $69,365 |
| 60/40      | 6.16%  | 9.68%  | 0.535  | —       | -29.24%  | 63.6%    | $29,057 |
| B&H EW15   | 2.54%  | 11.99% | 0.163  | —       | -39.71%  | 59.3%    | $15,636 |

Fuente S3.6: `s36_summary_report.txt` ✓
⚠ Fuente benchmarks: calculados inline en paper. Pendiente script explícito de verificación.

---

## Tabla 5 — Crisis periods

Script: `code/s36_crisis_analysis.py`
Output: `data/outputs/s36_crisis_report.txt`

| Crisis   | Período            | S3.6     | S&P 500  | Max DD S3.6 | Triggers |
|----------|--------------------|----------|----------|-------------|----------|
| GFC      | Jan 2008–Jun 2009  | +17.64%  | -33.05%  | -7.88%      | 6        |
| COVID    | Mar 2020–May 2023  | +30.21%  | +41.04%  | -10.84%     | 7        |
| Tariff   | Mar–Apr 2025       | +6.78%   | -6.67%   | 0.00%       | 0        |

Fuente: `s36_crisis_report.txt` ✓ (verificado 05 May 2026)

---

## Tabla 6 — Regime analysis

Script: `code/s36_regime_analysis.py`
Output: `data/outputs/s36_regime_report.txt`

| Regime   | Meses | % tiempo | S3.6 CAGR | 60/40 CAGR | Def% |
|----------|-------|----------|-----------|------------|------|
| BULL     | 119   | 56.7%    | 16.20%    | 15.21%     | 5.9% |
| SIDEWAYS | 64    | 30.5%    | 8.41%     | 4.96%      | 18.8% |
| BEAR     | 9     | 4.3%     | -23.18%   | 20.59%     | 66.7% |
| CRISIS   | 18    | 8.6%     | 14.74%    | -37.28%    | 66.7% |

Fuente: `s36_regime_report.txt` ✓ (verificado 05 May 2026)

**Nota sobre RESULTS.md**: el TFM usó una clasificación de regímenes distinta
(umbrales y periodos diferentes), produciendo CRISIS=42 meses. El paper usa la
clasificación de `s36_regime_analysis.py` que da CRISIS=18 meses. Son metodologías
distintas; no son inconsistentes, solo incomparables.

---

## Tabla 7 — Monte Carlo return-level

Script: `code/s36_montecarlo.py`
Output: `data/outputs/s36_montecarlo_report.txt`
Método: Circular block bootstrap, block=6m, N=10,000, seed=42, horizonte=214 meses
**Importante**: bootstrap de retornos realizados, NO re-ejecución de la estrategia.

| Percentil | CAGR    | Max DD    |
|-----------|---------|-----------|
| P10       | 8.34%   | -18.61%   |
| P25       | 9.79%   | -15.63%   |
| P50       | 11.51%  | -13.00%   |
| P75       | 13.23%  | -10.95%   |
| P90       | 14.75%  | -9.37%    |

Verificado ejecutando `s36_montecarlo.py` con checkpoints cada 1,000 simulaciones.

Probabilidades:
- P(CAGR >= 7%) = 96.4%
- P(MaxDD > -15%) = 70.2%
- P(ambas restricciones) = 69.4%
- Sensibilidad block length 3/6/9/12/18 guardada en `s36_montecarlo_block_sensitivity.csv`.

## Tabla 8 — Monte Carlo strategy-level

Script: `code/s36_montecarlo_strategy.py`
Output: `data/outputs/s36_montecarlo_strategy_report.txt`
Raw: `data/outputs/s36_montecarlo_strategy_raw.csv` (10,000 filas + header)
Método: paired circular block bootstrap de retornos diarios multi-activo, block=63 trading days, N=10,000, seed=42, horizonte=214 meses.
**Importante**: re-ejecuta momentum, crash filter, defensive switch y triplet selection en cada historia sintética. Incluye 60/40 y SPY en los mismos paths.

| Estrategia | CAGR P10 | CAGR P50 | CAGR P90 | Sharpe P50 | MaxDD P10 | MaxDD P50 |
|---|---:|---:|---:|---:|---:|---:|
| S3.6 | 0.59% | 4.45% | 8.56% | 0.311 | -44.34% | -29.24% |
| 60/40 | 3.11% | 6.14% | 9.05% | 0.522 | -33.10% | -21.90% |
| SPY | 3.89% | 9.24% | 14.57% | 0.543 | -53.37% | -36.69% |

Probabilidades:
- P(CAGR >= 7%) = 20.5%
- P(MaxDD > -15%) = 2.0%
- P(ambas restricciones) = 1.6%
- P(CAGR > 60/40 CAGR) = 25.6%
- P(CAGR > SPY CAGR) = 8.7%
- P(Sharpe > 60/40 Sharpe) = 16.0%

Interpretación crítica: este resultado debilita cualquier claim de superioridad general. La lectura defendible es que S3.6 funcionó en la secuencia histórica/OOS observada, pero no domina bajo historias sintéticas resampleadas donde se rehacen señales y allocations.

---

## Figuras

| Figura | Descripción | Script | Estado |
|--------|-------------|--------|--------|
| G1_equity_curves_full.png | Equity curves 2008-2025 | s36_figures.py | ✓ existe |
| G2_drawdown_full.png | Drawdown comparison | s36_figures.py | pendiente |
| G3_oos_equity.png | OOS equity 2020-2025 | s36_figures.py | pendiente |
| G4_crash_activations.png | Crash timeline | s36_figures.py | pendiente |
| G5_regime_bar.png | Régimen barchart | s36_figures.py | pendiente |
| G6_montecarlo_cagr.png | MC return-level CAGR/MaxDD histogram | s36_figures.py | ✓ existe |
| G8_montecarlo_strategy.png | MC strategy-level comparison | s36_figures.py | ✓ existe |
| G7_threshold_sensitivity.png | Sensitivity τ | s36_figures.py | pendiente |

---

## Errores corregidos en el paper (05 May 2026)

| Archivo | Error | Corrección |
|---------|-------|------------|
| `05_discussion.tex` L40 | "only four months" (BEAR regime) | → "nine months" |
| `05_discussion.tex` L139 | "only four months" (Limitations) | → "nine months" |
| `05_discussion.tex` L28 | "nine times" (COVID triggers) | → "seven times" |

---

## Pendientes de decisión

| # | Pendiente | Quién decide |
|---|-----------|--------------|
| 1 | Framing: S3.6 única estrategia vs framework modular | Francesc |
| 2 | Journal final: JEF / IREF / FRL | Francesc |
| 3 | Orden de autores | Francesc / Marc |
| 4 | Longitud: 8,000-10,000 (JEF) vs 5,000 (FRL) | Según journal |
| 5 | Ejecutar `run_all.py` para verificar todos los números | Ignasi |
| 6 | Añadir figuras G2-G7 al .tex | Ignasi + Marc |
