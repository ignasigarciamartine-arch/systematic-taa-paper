# STATUS -- Paper
> Actualizar siempre al cerrar sesion.

## Estado actual (05 May 2026 -- sesion 5)

### Cambios sesion 05 May 2026
- Auditoría completa de coherencia numérica entre .tex, outputs y RESULTS.md.
- Errores corregidos en `05_discussion.tex`:
  - "only four months" (BEAR regime, ×2) → "nine months" (según s36_regime_report.txt).
  - "triggered nine times" (COVID) → "seven times" (según s36_crisis_report.txt).
- Creados scripts nuevos en `code/`:
  - `s36_montecarlo.py` — bootstrap circular, bloque 6m, N=10,000, seed=42.
  - `s36_threshold_sensitivity.py` — sensibilidad τ, re-ejecuta backtest completo.
  - `s36_figures.py` — genera G1–G7 (todas las figuras del paper).
  - `run_all.py` — script maestro para reproducibilidad completa.
- Creado `AUDIT.md` — trazabilidad de todos los números con fuentes verificadas.
- Verificado: todas las citas \cite en los .tex tienen entrada en paper.bib. ✓
- Verificado: números del paper consistentes con `data/outputs/` (script s36_backtest.py). ✓
- Discrepancias identificadas vs RESULTS.md del TFM: MaxDD (-13.79 paper vs -13.87 TFM)
  y retorno COVID (+30.21% paper vs +27.43% TFM) — ambas debidas a versiones distintas
  del código. El paper usa la versión de `paper/code/s36_backtest.py` como fuente oficial.
- Ejecutados y verificados dos Monte Carlo de periodo completo:
  - `code/s36_montecarlo.py`: return-level circular block bootstrap, 10,000 sims,
    horizonte 214 meses, checkpoints cada 1,000, sensibilidad block 3/6/9/12/18.
  - `code/s36_montecarlo_strategy.py`: strategy-level paired daily block bootstrap,
    10,000 sims, block=63 trading days, horizonte 214 meses, checkpoints cada 1,000,
    con benchmarks 60/40 y SPY en los mismos paths.
- Resultado crítico strategy-level: S3.6 CAGR P50 4.45%, MaxDD P50 -29.24%;
  P(CAGR > 60/40) 25.6%, P(CAGR > SPY) 8.7%, P(CAGR>=7% and MaxDD>-15%) 1.6%.
  Conclusión: no vender superioridad general; limitar claim a histórico/OOS/crisis observadas.
- Actualizados `main.tex`, `sections/03_methodology.tex`, `sections/04_results.tex`,
  `sections/05_discussion.tex`, `sections/06_conclusion.tex`, `CLAUDE.md` y `AUDIT.md`
  para distinguir Monte Carlo return-level vs strategy-level.
- Regeneradas figuras G1-G8; `G8_montecarlo_strategy.png` enlazada en resultados.
- Preparada sensibilidad strategy-level por bloques de 3/6/9/12 meses sin ejecutarla:
  - `code/s36_montecarlo_strategy.py` acepta `--block-months 3|6|9|12`
    y escribe en carpetas separadas bajo `data/outputs/montecarlo/strategy_level/`.
  - `code/run_montecarlo_strategy_blocks.py` imprime los cuatro comandos por defecto
    y solo ejecuta si se pasa `--execute`.
  - `code/s36_montecarlo_strategy_collect.py` agregará resultados una vez estén los cuatro `raw.csv`.
  - Validado dry-run; no se han creado nuevos raw/reports en las carpetas block_03m/block_06m/block_09m/block_12m.

### Proxima accion
1. Ejecutar, cuando se autorice, `python3 code/run_montecarlo_strategy_blocks.py --execute`
   para strategy-level MC con bloques 3/6/9/12 meses.
2. Ejecutar después `python3 code/s36_montecarlo_strategy_collect.py`.
3. Decidir si el strategy-level Monte Carlo queda en cuerpo principal, appendix o robustness supplement.
4. Revisar si G2-G7 deben enlazarse ahora o mantenerse como outputs auxiliares.
5. Decidir framing final (S3.6 vs framework modular) — Francesc.
6. Decidir journal target — Francesc.
7. Compilar PDF (LaTeX en el equipo).

---

## Estado actual (28 Apr 2026 -- sesion 4)

**Fase activa**: borrador LaTeX completo creado. El foco inmediato es cerrar la parte de Ignasi: abstract, keywords, introduction, literature review y references. La metodologia queda principalmente para Marc; resultados, discussion y conclusion son trabajo compartido Ignasi/Marc.

### Reparto segun email a Francesc

| Bloque | Responsable inicial | Revision |
|---|---|---|
| Abstract, keywords, introduction, literature review | Ignasi | Francesc |
| Methodology | Marc | Ignasi/Francesc |
| Results, discussion, conclusions | Ignasi + Marc | Francesc |
| References | Ignasi | Francesc/Marc |

### Estado de archivos
- `main.tex` -- documento principal, template elsarticle (Elsevier)
- `sections/01_introduction.tex` -- reescrito como introduccion de paper academico
- `sections/02_literature.tex` -- reescrito con estructura argumental y citas conectadas al metodo
- `sections/03_methodology.tex` -- borrador redactado con algoritmo S3.6
- `sections/04_results.tex` -- borrador redactado con tablas principales
- `sections/05_discussion.tex` -- borrador redactado
- `sections/06_conclusion.tex` -- borrador redactado
- `paper.bib` -- bibliografia base ampliada y limpia de problemas obvios de encoding
- `CITATION_STRATEGY.md` -- matriz de papers para citar y funcion de cada referencia
- `SIMILAR_PAPERS.md` -- papers parecidos para posicionamiento editorial
- `REFORMULATION_OPTIONS.md` -- propuesta para reformular el paper como framework modular, no como una unica estrategia
- `figures/` -- contiene `G1_equity_curves_full.png`; faltan figuras restantes
- `tables/` -- pendiente si se decide externalizar tablas
- `output/` -- pendiente de PDF compilado

### Cambios sesion 28 Apr 2026
- Descargada serie Refinitiv/Federal Reserve 3M T-bill (`aUSTRB3AV`) a `data/prices/tbill_3m_monthly_refinitiv.csv`.
- Actualizado `code/s36_backtest.py`: cash acreditado con 3M T-bill mensual y Sharpe/Sortino calculados sobre exceso mensual vs T-bill.
- Regenerados `data/outputs/s36_monthly_returns.csv`, `s36_equity_curve.csv`, `s36_allocation_log.csv` y `s36_summary_report.txt`.
- Nuevos resultados verificados: train CAGR 10.94%, Sharpe 0.951, MaxDD -13.79%; OOS CAGR 12.54%, Sharpe 1.029, MaxDD -10.84%; full CAGR 11.47%, Sharpe 0.974, MaxDD -13.79%.
- Actualizados `main.tex` y `sections/01/03/04/05/06` para eliminar `rf=0%`, incorporar metodologia T-bill y sustituir resultados antiguos.
- Confirmado: ningun `.tex` menciona Optimum3.
- Corregido `main.tex`: anadido tipo de columna `R{}` para evitar error de compilacion.
- Corregido `sections/03_methodology.tex`: referencia rota `Algorithm~\ref{alg:s36}` sustituida por `Figure~\ref{fig:flowchart}`.
- Corregido `sections/04_results.tex`, `05_discussion.tex` y `06_conclusion.tex`: drag UCITS actualizado al valor oficial de 0.72 pp/year, con distincion 83 meses brutos vs 82 transiciones de costes.
- Corregida cita inexistente `harvey2016` -> `harvey2018`.
- Copiada figura `G1_equity_curves_full.png` a `paper/figures/` y enlazada en resultados.
- Reescrito el abstract para enfatizar problema, restriccion de drawdown, resultados OOS y contribucion.
- Reescrita la introduction para que funcione sin depender del TFM: gap, contribucion, datos, resultados y estructura.
- Reescrita la literature review con cinco bloques: portfolio theory, momentum, ETF TAA, crash detection y corporate cash management.
- Limpiado `paper.bib` de caracteres problemáticos en comentarios y en `Stulz, Rene M.`.
- Buscados papers adicionales para citar y basar el paper: corporate cash, TAA/momentum, crash protection, data snooping y backtest overfitting.
- Anandidos a `paper.bib`: `opler1999`, `cardella2021`, `barroso2015`, `antonacci2015`, `guilleminot2014`, `blitz2008`, `sullivan1999`, `harvey2016`, `bailey2017`.
- Creado `CITATION_STRATEGY.md` con uso recomendado por seccion.
- Buscada literatura reciente 2023-2025 para repensar framing: corporate cash composition, marketable securities, momentum reviews, volatility/VIX-managed portfolios y downside risk.
- Anandidos a `paper.bib`: `jegadeesh2023`, `blanco2023`, `ysmailov2025`, `moreira2017`, `bozovic2024`, `wang2024vmp`, `ergun2023`.
- Creado `REFORMULATION_OPTIONS.md`: recomendacion de reposicionar el paper como drawdown-constrained tactical allocation framework para strategic corporate cash.

### Proxima accion
1. Copiar y enlazar el resto de figuras clave: drawdown, OOS, crash activations, regimes, heatmap y Monte Carlo.
2. Decidir framing final: estrategia S3.6 vs framework modular drawdown-constrained para corporate cash.
3. Resolver benchmark Faber trend-following o eliminarlo del claim si no se calcula; B&H EW15 ya esta calculado.
4. Revisar `sections/04_results.tex` para no usar valores de 60/40 fuera de su periodo correcto.
5. Compilar cuando haya LaTeX disponible en el equipo.

---

## Journals target

| Priority | Journal | Q | APC |
|---|---|---|---|
| 1 | Journal of Empirical Finance | Q1 Elsevier | ~2,500 EUR (cubierto IQS) |
| 2 | International Review of Economics and Finance | Q1 Elsevier | cubierto IQS |
| 3 | Financial Analysts Journal | Q2 T&F | TBD |
| 4 | Finance Research Letters | Q2 Elsevier | cubierto IQS |

Decision final: Francesc Prior. Cerrar antes de empezar a formatear para journal especifico.

---

## Decisiones tomadas

| Decision | Valor |
|---|---|
| Template | `elsarticle` (Elsevier standard); cambiar a T&F si el target es FAJ |
| Optimum3 | NO se menciona en ninguna seccion, tabla, figura o referencia |
| Cadena de citas breadth filter | Keller & Keuning 2017 HAA (SSRN, citable); no Keller & Butler |
| Benchmarks | 60/40, B&H EW15, Faber 2007 trend-following; pendientes de cierre reproducible |
| Cash/rf | 3M U.S. T-bill mensual de Refinitiv/Federal Reserve (`aUSTRB3AV`); Sharpe/Sortino sobre exceso mensual |

## Decisiones pendientes

| Decision | Opciones | Quien decide |
|---|---|---|
| Journal final | JEF / IREF / FRL / FAJ | Francesc |
| Orden de autores | Garcia M. / Mases C. / Prior S. -- TBC | Francesc / Marc |
| Transaction costs model | Modelar explicitamente o solo en robustness | Marc / Francesc |
| Longitud target | 8,000-10,000 (JEF) vs 5,000 (FRL) | Segun journal final |

---

## Co-autores y roles (provisional)

- **Ignasi Garcia Martin** -- diseno y backtesting de la estrategia, redaccion principal
- **Marc Mases Campos** -- co-tutor, LaTeX, revision metodologica
- **Francesc Prior Sanz** -- tutor, direccion academica, decision journal

---

## Protocolo de sesion

### Al INICIAR:
1. Leer este STATUS.md
2. Confirmar que seccion trabajamos
3. Leer la seccion `.tex` correspondiente

### Al CERRAR:
1. Marcar progreso en la tabla de secciones
2. Actualizar "Proxima accion"
3. Escribir **"SESION CERRADA -- STATUS actualizado"**
