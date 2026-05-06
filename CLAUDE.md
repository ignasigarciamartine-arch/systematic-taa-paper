# CLAUDE.md — Paper: Systematic TAA for Corporate Cash Management
> Leer este archivo primero. Contiene todo el contexto necesario para trabajar en el paper.
> Cualquier AI (Claude, Codex) o colaborador puede replicar el backtest desde este archivo.

---

## ¿Qué es este proyecto?

Paper académico derivado del TFM de Ignasi Garcia Martin (IQS, Universitat Ramon Llull, 2026).
**Co-autores**: Ignasi Garcia Martin · Marc Mases Campos · Francesc Prior Sanz.

La estrategia **S3.6** se presenta como contribución original sin citar Optimum3 (Keller & Butler).
El anclaje académico correcto es: Moskowitz et al. (2012) + Antonacci (2014) + Keller & Keuning (2017) HAA.

**Target journal primario**: Journal of Empirical Finance (Elsevier, Q1)
**Backup**: International Review of Economics and Finance (Elsevier, Q1)
**APC**: cubierto por IQS.

---

## La estrategia S3.6 — descripción completa

### Universo de activos

16 ETFs (15 riesgosos + 1 cash):

| ETF | Clase |
|---|---|
| SPY | US Large Cap Equity |
| QQQ | US Tech Equity |
| VGK | European Equity |
| EWJ | Japanese Equity |
| SCZ | International Small Cap |
| EEM | Emerging Markets Equity |
| VNQ | US REITs |
| REM | Mortgage REITs |
| GLD | Gold |
| IEF | US 7-10Y Treasury |
| TLT | US 20Y+ Treasury |
| TIP | TIPS (inflation-linked) |
| DBC | Commodities |
| BWX | International Bonds |
| RWX | International REITs |
| BIL | Cash proxy (T-Bills, 1-3M) |

### Algoritmo (ejecutar cada fin de mes)

```
Cada fin de mes:

PASO 1 — CRASH FILTER
  r̄(t) = media igual de retornos mensuales de los 15 ETFs riesgosos
  Si r̄(t) < -4%:
    → CRASH DETECTADO → ir a modo defensivo
       Si max(momentum_TLT, momentum_IEF) ≥ 0: portfolio = TLT 50% + IEF 50%
       Si no: portfolio = BIL 100%
    → STOP (no ejecutar pasos 2-4)

PASO 2 — SEÑAL DE MOMENTUM (13612U)
  M_i(t) = (1/4) × (R_1m + R_3m + R_6m + R_12m)
  Calcular para los 15 ETFs riesgosos.
  Rankear descendente → tomar Top-7.

PASO 3 — FILTRO ABSOLUTO
  Mantener solo activos con M_i(t) ≥ 2% → conjunto elegible A_t+

PASO 4 — CONSTRUCCIÓN DEL PORTFOLIO
  Si |A_t+| ≥ 3:
    Si |A_t+| = 3: portfolio = los 3, peso igual 1/3
    Si |A_t+| ≥ 4: seleccionar triplete de mínima correlación media por pares
                   (correlación sobre retornos diarios del mes en curso)
                   portfolio = triplete, peso igual 1/3

  Si |A_t+| < 3: modo defensivo
    Si max(momentum_TLT, momentum_IEF) ≥ 0: portfolio = TLT 50% + IEF 50%
    Si no: portfolio = BIL 100%

REBALANCEO: ejecutar el primer día hábil del mes siguiente.
```

### Parámetros

| Parámetro | Valor | Cómo se fijó |
|---|---|---|
| Momentum windows | 1m, 3m, 6m, 12m (igual peso) | Robustness en literatura |
| Top-N ranking | 7 | In-sample optimización |
| Threshold θ | 2% | In-sample (Tabla 5 TFM) |
| Triplet size | 3 | Fixed by design |
| Crash threshold τ | -4% | In-sample sensitivity (Tabla 9 TFM) |
| Defensive assets | TLT + IEF | In-sample (Tabla 7 TFM) |
| Periodo train | 2008-01 — 2019-12 | Temporal split |
| Periodo test | 2020-01 — 2025-12 | Estrictamente OOS |

---

## Resultados verificados (fuente de verdad)

Fuente: `code/s36_backtest.py` ejecutado con datos Refinitiv Eikon y
`data/prices/tbill_3m_monthly_refinitiv.csv` (`aUSTRB3AV`) para cash/risk-free.
Verificado: 28 Apr 2026.

### In-sample (Train 2008–2019, 142 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **10.94%** |
| Volatilidad | 10.97% |
| Sharpe (rf=3M T-bill) | 0.951 |
| Sortino (rf=3M T-bill) | 1.776 |
| Max Drawdown | **-13.79%** |
| Win Rate | 65.49% |
| Capital final ($10k) | $34,149 |
| Crash triggers | 12 |

Distribución de modos (train):
- Offensive Triplet: 114 meses (80.3%)
- Crash TLT+IEF: 10 meses (7.0%)
- Defensive TLT+IEF: 6 meses (4.2%)
- Offensive EW3: 6 meses (4.2%)
- Cash Defensive: 4 meses (2.8%)
- Cash Crash: 2 meses (1.4%)

### Out-of-sample (Test 2020–2025, 72 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **12.54%** |
| Volatilidad | 9.30% |
| Sharpe (rf=3M T-bill) | 1.029 |
| Sortino (rf=3M T-bill) | 1.808 |
| Max Drawdown | **-10.84%** |
| Capital final ($10k) | $20,312 |
| Crash triggers | 9 |

### Período completo (2008–2025, 214 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **11.47%** |
| Volatilidad | 10.41% |
| Sharpe (rf=3M T-bill) | 0.974 |
| Sortino (rf=3M T-bill) | 1.788 |
| Max Drawdown | **-13.79%** |
| Total Return | +593.65% |
| Capital final ($10k) | $69,365 |

### Benchmarks (mismo período completo)

| Benchmark | CAGR | Max DD |
|---|---|---|
| 60/40 (SPY+IEF) | 6.16% | -29.24% |
| B&H Equal Weight (15 ETFs) | 2.54% | -39.71% |

### Crisis periods

| Crisis | Período | S3.6 return | S&P 500 | Triggers |
|---|---|---|---|---|
| GFC | Jan 2008 – Jun 2009 | **+17.64%** | -33.05% | 6 |
| COVID | Mar 2020 – May 2023 | +30.21% | +41.04% | 7 |
| Tariff Shock | Mar–Apr 2025 | **+6.78%** | -6.67% | 0 |

### Monte Carlo 1 — return-level (10,000 simulaciones, circular block bootstrap)

| Percentil | CAGR |
|---|---|
| P10 | 8.34% |
| P50 (mediana) | 11.51% |
| P75 | 13.23% |
| P90 | 14.75% |

**Limitación importante**: el bootstrap de retornos muestra CAGR robusto, pero
el P10 de MaxDD es -18.61%. El control de drawdown observado no debe venderse
como garantía estadística.

### Monte Carlo 2 — strategy-level (10,000 simulaciones, daily paired block bootstrap)

Fuente: `code/s36_montecarlo_strategy.py`, verificado 05 May 2026.
Periodo efectivo completo: 214 meses (Mar 2008--Dic 2025).
Método: resampleo circular de retornos diarios multi-activo, block=63 trading days;
re-ejecuta momentum, crash filter, defensive switch y triplet selection en cada path.
Incluye 60/40 y SPY sobre los mismos paths.

| Estrategia | CAGR P10 | CAGR P50 | CAGR P90 | Sharpe P50 | MaxDD P10 | MaxDD P50 |
|---|---:|---:|---:|---:|---:|---:|
| S3.6 | 0.59% | 4.45% | 8.56% | 0.311 | -44.34% | -29.24% |
| 60/40 | 3.11% | 6.14% | 9.05% | 0.522 | -33.10% | -21.90% |
| SPY | 3.89% | 9.24% | 14.57% | 0.543 | -53.37% | -36.69% |

Probabilidades clave:
- P(CAGR > 60/40) = 25.6%
- P(CAGR > SPY) = 8.7%
- P(CAGR >= 7% and MaxDD > -15%) = 1.6%

**Lectura crítica**: el strategy-level MC no sostiene superioridad general.
El claim defendible debe limitarse a performance histórica/OOS y crisis observadas,
no robustez estadística fuerte frente a historias sintéticas.

---

## Estructura de archivos del paper

```
paper/
├── CLAUDE.md                   ← ESTE ARCHIVO — leer primero
├── main.tex                    ← documento LaTeX principal (elsarticle)
├── paper.bib                   ← bibliografía
├── PAPER_OUTLINE.md            ← outline detallado
├── STATUS.md                   ← tracking de sesiones
├── sections/
│   ├── 01_introduction.tex
│   ├── 02_literature.tex
│   ├── 03_methodology.tex
│   ├── 04_results.tex
│   ├── 05_discussion.tex
│   └── 06_conclusion.tex
├── figures/                    ← PNGs para el paper (copiar de redaccion/figures/)
├── tables/                     ← tablas .tex independientes
├── output/                     ← PDFs compilados
├── data/
│   ├── prices/                 ← datos de entrada (ver DATA_README.md)
│   │   ├── etf_adjclose_2008_2025.csv          ← precios diarios ajustados (16 ETFs)
│   │   ├── momentum_train_2008_2019.csv        ← momentum 13612U periodo train
│   │   ├── momentum_completo_2008_2025.csv     ← momentum 13612U periodo completo
│   │   └── monthly_returns_completo.csv        ← retornos mensuales
│   └── outputs/                ← resultados del backtest
│       ├── s36_equity_curve.csv
│       ├── s36_monthly_returns.csv
│       ├── s36_allocation_log.csv
│       └── s36_summary_report.txt
└── code/
    ├── s36_backtest.py         ← backtest principal (autosuficiente con data/ local)
    ├── s36_crisis_analysis.py  ← análisis por periodos de crisis
    ├── s36_regime_analysis.py  ← análisis por régimen de mercado
    ├── s36_montecarlo.py       ← Monte Carlo return-level
    └── s36_montecarlo_strategy.py ← Monte Carlo strategy-level con 60/40 y SPY
```

---

## Cómo reproducir el backtest

### Prerequisitos

```bash
pip install pandas numpy
```

No se necesita Refinitiv ni APIs externas si los CSVs ya están en `data/prices/`.

### Paso 1 — Verificar datos

Los archivos en `data/prices/` deben existir. Si no están:
- Copiar desde `../research/phase_1/01_config/data/`
  - `completo/optimum3_refinitiv_adjclose.csv` → renombrar a `etf_adjclose_2008_2025.csv`
  - `train/momentum_multi_horizon.csv` → renombrar a `momentum_train_2008_2019.csv`
  - `completo/momentum_multi_horizon.csv` → renombrar a `momentum_completo_2008_2025.csv`
  - `completo/monthly_returns.csv` → `monthly_returns_completo.csv`

### Paso 2 — Ejecutar backtest

```bash
# Desde la carpeta paper/
python code/s36_backtest.py
```

Outputs en `data/outputs/`:
- `s36_equity_curve.csv` — equity curves mensuales
- `s36_monthly_returns.csv` — retornos + modo + activos seleccionados
- `s36_allocation_log.csv` — log completo de allocations
- `s36_summary_report.txt` — métricas completas

### Resultados esperados (verificación)

Si el backtest reproduce correctamente:
```
TRAIN CAGR:  10.94%
TEST  CAGR:  12.54%
FULL  CAGR:  11.47%
Max DD:     -13.79%
Crash triggers (train): 12
Crash triggers (test):   9
```

Cualquier desviación indica un problema en los datos o en el código.

---

## Formato del CSV de precios (`etf_adjclose_2008_2025.csv`)

```
Date,SPY,QQQ,VGK,EWJ,SCZ,EEM,VNQ,REM,GLD,IEF,TLT,TIP,DBC,BWX,RWX,BIL
2007-01-03,142.87,43.45,...
2007-01-04,...
...
2025-12-31,...
```

- Index: `Date` en formato `YYYY-MM-DD`
- Valores: precios ajustados de cierre (adjusted close)
- Fuente original: Refinitiv Eikon
- Cubre 2007-01 a 2025-12 (el año 2007 sirve de warmup para el momentum de enero 2008)

---

## Reglas del paper (importante)

1. **No mencionar Optimum3** en ninguna sección, tabla, figura o referencia.
2. Los benchmarks del paper son: 60/40 (SPY+IEF), B&H EW15, y Faber (2007) trend-following.
3. El crash filter se ancla en Keller & Keuning (2017) HAA — no en ningún otro trabajo.
4. Todos los números deben coincidir exactamente con los de este CLAUDE.md.
5. Cash y rf para Sharpe/Sortino usan 3M T-bill mensual de Refinitiv/Federal Reserve.
6. Declarar siempre: sin costes de transacción en el caso base.
7. El Monte Carlo es la limitación principal — tratar con honestidad.

---

## Co-autores

| Autor | Rol | Email |
|---|---|---|
| Ignasi Garcia Martin | Diseño estrategia, backtesting, redacción principal | ignasi.garcia.martin.e@gmail.com |
| Marc Mases Campos | Co-tutor, LaTeX, revisión metodológica | — |
| Francesc Prior Sanz | Tutor, dirección académica, decisión journal | — |

---

## Contexto adicional (solo si necesario)

- Resultados detallados: `data/outputs/s36_summary_report.txt`
- Figures del TFM reutilizables: `../redaccion/figures/`
- Números auditados del TFM: `../redaccion/RESULTS.md`
