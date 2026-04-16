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

Fuente: `code/s36_backtest.py` ejecutado con datos Refinitiv Eikon.
Verificado: 10 Mar 2026. Reconfirmado: 14 Apr 2026.

### In-sample (Train 2008–2019, 142 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **10.88%** |
| Volatilidad | 10.97% |
| Sharpe (rf=0%) | 0.991 |
| Sortino (rf=0%) | 1.633 |
| Max Drawdown | **-13.87%** |
| Calmar | 0.784 |
| Win Rate | 61.97% |
| Capital final ($10k) | $33,930 |
| Crash triggers | 12 |

Distribución de modos (train):
- Offensive Triplet: 114 meses (80.3%)
- Crash TLT+IEF: 10 meses (7.0%)
- Defensive TLT+IEF: 6 meses (4.2%)
- Offensive EW3: 6 meses (4.2%)
- BIL Defensive: 4 meses (2.8%)
- BIL Crash: 2 meses (1.4%)

### Out-of-sample (Test 2020–2025, 72 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **12.05%** |
| Volatilidad | 9.34% |
| Sharpe (rf=0%) | 1.291 |
| Sortino (rf=0%) | 2.013 |
| Max Drawdown | **-12.52%** |
| Capital final ($10k) | $19,793 |
| Crash triggers | 9 |

### Período completo (2008–2025, 214 meses)

| Métrica | S3.6 |
|---|---|
| CAGR | **11.27%** |
| Volatilidad | 10.43% |
| Sharpe (rf=0%) | 1.081 |
| Sortino (rf=0%) | 1.745 |
| Max Drawdown | **-13.87%** |
| Total Return | +571.59% |
| Capital final ($10k) | $67,159 |

### Benchmarks (mismo período completo)

| Benchmark | CAGR | Max DD |
|---|---|---|
| 60/40 (SPY+AGG) | 5.89% | -29.24% |
| B&H Equal Weight (15 ETFs) | TBD | TBD |

### Crisis periods

| Crisis | Período | S3.6 return | S&P 500 | Triggers |
|---|---|---|---|---|
| GFC | Jan 2008 – Jun 2009 | **+17.64%** | -33.05% | 6 |
| COVID | Mar 2020 – May 2023 | +27.43% | +41.04% | 7 |
| Tariff Shock | Mar–Apr 2025 | **+6.78%** | -6.67% | 0 |

### Monte Carlo (10,000 simulaciones, circular block bootstrap)

| Percentil | CAGR |
|---|---|
| P10 | 2.59% |
| P50 (mediana) | 7.09% |
| P75 | 9.13% |
| P90 | 12.18% |

**Limitación importante**: la mediana bootstrap (7.09%) es significativamente inferior
al histórico (11.27%). El outperformance histórico depende de la secuencia específica
del crash de 2008 + el bull de bonos. Esto hay que declararlo en el paper.

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
    └── s36_montecarlo.py       ← simulación Monte Carlo
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
TRAIN CAGR:  10.88%
TEST  CAGR:  12.05%
FULL  CAGR:  11.27%
Max DD:     -13.87%
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
2. Los benchmarks del paper son: 60/40, B&H EW15, y Faber (2007) trend-following.
3. El crash filter se ancla en Keller & Keuning (2017) HAA — no en ningún otro trabajo.
4. Todos los números deben coincidir exactamente con los de este CLAUDE.md.
5. rf=0% para Sharpe y Sortino en todos los cálculos del paper.
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
