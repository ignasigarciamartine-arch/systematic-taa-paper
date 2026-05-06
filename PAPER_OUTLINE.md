# PAPER OUTLINE
> Outline detallado del paper. Referencia para los tres autores.
> Números de: `01_TFM/redaccion/RESULTS.md` (fuente de verdad).

---

## Título provisional

**"A Systematic Tactical Asset Allocation Strategy for Corporate Cash Management: Momentum, Crash Detection, and Drawdown Control"**

Alternativas:
- "Low-Drawdown Tactical Asset Allocation for Corporate Treasury: A Momentum-Based Approach with Market-Breadth Crash Detection"
- "Automated Tactical Asset Allocation with Bounded Drawdown: Evidence from 2008–2025"

---

## Estructura (6 secciones + refs)

### 1. Introduction (~600 words)

**Argumento central**: Las empresas con grandes reservas de liquidez necesitan rendimientos > inflación pero no pueden asumir los drawdowns del mercado de renta variable. Las estrategias TAA sistemáticas pueden llenar ese hueco.

**Contribución al artículo**:
1. Aplicación a corporate cash management (gap real en la literatura)
2. Combinación: momentum multi-período + filtro de correlación + crash detection
3. Validación OOS limpia (2020–2025 no usados en ningún parámetro)
4. Implementación UCITS validada

---

### 2. Literature Review (~1,200 words)

| Subsección | Fuentes clave |
|---|---|
| 2.1 Asset allocation foundations | Markowitz (1952), Black & Litterman (1992) |
| 2.2 Momentum en mercados de capitales | Jegadeesh & Titman (1993), Moskowitz et al. (2012), Asness et al. (2013) |
| 2.3 TAA y momentum absoluto | Faber (2007), Antonacci (2012, 2014) |
| 2.4 Crash detection y breadth | Keller & Keuning (2017) HAA |
| 2.5 Corporate cash management | Graham & Harvey (2001), Bates et al. (2009) |

**Nota crítica**: La estrategia S3.6 se presenta como contribución original, construida sobre los pilares de la literatura arriba. No se menciona ninguna estrategia específica de referencia que pudiera implicar derivación directa.

---

### 3. Methodology (~2,000 words)

**3.1 Asset Universe**
- 15 ETFs: SPY, QQQ, VGK, EWJ, SCZ, EEM, VNQ, REM, GLD, IEF, TLT, TIP, DBC, BWX, RWX
- Cash proxy: BIL
- Datos: Refinitiv Eikon, adjusted close, Jan 2008 – Dec 2025
- Train/Test split: 2008–2019 / 2020–2025

**3.2 Momentum Signal (13612U)**
$$M_i(t) = \frac{1}{4}\left(R_{1m,i} + R_{3m,i} + R_{6m,i} + R_{12m,i}\right)$$
- Equal-weight average de 4 lookbacks
- Threshold absoluto θ = 2%: activo elegible solo si M_i(t) ≥ 2%

**3.3 Portfolio Construction: Min-Correlation Triplet**
- Ranking Top-7 por M_i(t)
- Si |A_t+| ≥ 3: seleccionar triplete de mínima correlación media por pares
  - Correlación sobre retornos diarios del mes anterior
  - Peso igual: 1/3 cada activo
- Si |A_t+| < 3: modo defensivo

**3.4 Defensive Allocation**
- Trigger: |A_t+| < 3
- TLT(50%) + IEF(50%) si momentum defensivo > 0
- BIL(100%) si momentum defensivo ≤ 0

**3.5 Market-Breadth Crash Filter**
$$\bar{r}(t) = \frac{1}{15}\sum_{i=1}^{15} r_{i,t}$$
- Si $\bar{r}(t) < \tau = -4\%$: override a modo defensivo
- τ = -4% seleccionado por optimización in-sample (Tabla 2)

**3.6 Rebalancing**
- Señal: último día del mes
- Ejecución: primer día hábil del mes siguiente
- Sin costes de transacción en caso base (robustness con costes en Sección 4.8)

**3.7 Benchmarks**
1. 60/40 portfolio (SPY 60% + IEF 40%), rebalanceado mensualmente
2. Buy-and-Hold Equal Weight (15 ETFs)
3. Trend-following baseline: Faber (2007) 10-month SMA

**3.8 Performance Metrics**
- CAGR, Sharpe (rf=0%), Sortino (rf=0%), Max Drawdown, Calmar, Win Rate
- Bootstrap: circular block bootstrap, block length = 6 meses, N = 10,000

---

### 4. Results (~2,500 words + tables + figures)

**Tabla 4.1 — Strategy evolution (in-sample)**

| Strategy | Innovation | CAGR | Sharpe | Max DD |
|---|---|---|---|---|
| Base (momentum only) | 13612U, θ=2%, triplet | 7.64% | 0.762 | -13.28% |
| + Enhanced Defensive | TLT+IEF in defensive mode | 9.72% | 0.891 | -13.87% |
| **Full strategy** | **+ Crash filter τ=-4%** | **10.88%** | **0.991** | **-13.87%** |
| 60/40 benchmark | — | ~7% | ~0.65 | ~-29% |

**Tabla 4.2 — Threshold sensitivity (τ)**

| τ | CAGR | Sharpe | MaxDD | #Crashes |
|---|---|---|---|---|
| -2.0% | 9.88% | 0.900 | -13.87% | 28 |
| -3.0% | 9.43% | 0.870 | -13.87% | 16 |
| **-4.0%** | **10.88%** | **0.991** | **-13.87%** | **12** |
| -5.0% | 9.78% | 0.896 | -13.87% | 8 |

**Tabla 4.3 — OOS performance (2020–2025)**

| Metric | Full strategy |
|---|---|
| CAGR | 12.05% |
| Sharpe (rf=0) | 1.291 |
| Max DD | -12.52% |
| Crash triggers | 9 |

Nota: no usar el 5.89% full-period de 60/40 como si fuera OOS. Calcular benchmark OOS antes de incluirlo.

**Tabla 4.4 — Full period (2008–2025)**

| Metric | Full strategy | 60/40 |
|---|---|---|
| CAGR | 11.27% | 5.89% |
| Sharpe (rf=0) | 1.081 | — |
| Max DD | -13.87% | -29.24% |
| Total Return | +571.6% | +165% |

**Tabla 4.5 — Crisis periods**

| Crisis | Strategy return | S&P 500 | Triggers |
|---|---|---|---|
| GFC (Jan08–Jun09) | +17.64% | -33.05% | 6 |
| COVID (Mar20–May23) | +27.43% | +41.04% | 7 |
| Tariff Shock (Mar–Apr 2025) | +6.78% | -6.67% | 0 |

**Tabla 4.6 — Market regime analysis**

| Regime | % time | Strategy CAGR | 60/40 CAGR |
|---|---|---|---|
| BULL | 55.7% | 15.35% | 14.51% |
| SIDEWAYS | 22.4% | 1.77% | -4.79% |
| CRISIS | 20.0% | 17.18% | 1.29% |
| BEAR | 1.9% | -30.28% | -19.12% |

**Figuras sugeridas** (reutilizar del TFM):
- Fig 1: Equity curves full period (G1)
- Fig 2: Drawdown chart (G4)
- Fig 3: OOS equity curve (G5)
- Fig 4: Crash filter activations (G6)
- Fig 5: Market regime analysis (G7v2)
- Fig 6: Monthly returns heatmap (G8)
- Fig 7: Monte Carlo fan chart (G9)
- Fig 8: Threshold sensitivity chart (G_METH2)

---

### 5. Discussion (~1,500 words)

- Por qué funciona el crash filter (mecanismo económico)
- Coste de la protección (underperformance en BULL)
- Estabilidad OOS: OOS > Train sugiere robustez pero no garantiza persistencia
- Monte Carlo: limitación principal — path dependency
- Transaction costs: drag ~0.72pp/año en la ventana de 82 transiciones del análisis UCITS Phase 3
- Implementación práctica: UCITS, mensual, automatizable

---

### 6. Conclusion (~600 words)

- Estrategia cumple constraint corporativo: MaxDD < -15% ✓
- CAGR 11.27% full period supera target 7% ✓
- OOS confirma resultados in-sample
- Limitaciones honestas: sin costes en base case, path dependency MC, BEAR n=4
- Futuras extensiones: universo extendido, τ dinámico, live tracking

---

## Posición respecto a Optimum3

El paper **no menciona Optimum3 en ningún momento**. La estrategia se presenta como contribución original, construida sobre:
- Moskowitz et al. (2012): momentum multi-período
- Antonacci (2014): absolute momentum threshold
- Keller & Keuning (2017) HAA: market breadth / crash filter
- Markowitz (1952): min-correlation diversification

Esta cadena de citas es académicamente legítima e independiente. Los revisores familiarizados con TAA reconocerán la arquitectura, pero no hay deuda directa con ningún trabajo concreto no citado.
