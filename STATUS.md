# STATUS — Paper
> Actualizar siempre al cerrar sesión.

## Estado actual (15 Apr 2026 — sesión 1)

**Fase activa**: Estructura creada. Todos los archivos son stubs con comentarios de contenido.

### Archivos creados
- `main.tex` — documento principal, template elsarticle (Elsevier)
- `sections/01_introduction.tex` — stub con argumentos clave
- `sections/02_literature.tex` — stub con cadena de citas (sin Optimum3)
- `sections/03_methodology.tex` — stub con algoritmo completo S3.6
- `sections/04_results.tex` — stub con todos los números verificados
- `sections/05_discussion.tex` — stub con líneas argumentales
- `sections/06_conclusion.tex` — stub con puntos clave
- `paper.bib` — bibliografía base (15 refs, expandible)
- `figures/` — carpeta vacía (copiar desde `redaccion/figures/`)
- `tables/` — carpeta vacía (tablas .tex pendientes)
- `output/` — carpeta vacía (PDFs compilados)
- `PAPER_OUTLINE.md` — outline detallado del paper
- `STATUS.md` — este archivo

### Próxima acción
1. Copiar figuras clave de `redaccion/figures/` a `paper/figures/`
2. Empezar a redactar `sections/03_methodology.tex` (la más técnica y autónoma)
3. Crear tablas .tex de resultados clave (Tablas 4.1, 4.3, 4.4)
4. Decidir orden de redacción: Metodología → Resultados → Discusión → Intro → Conclusión

---

## Journals target

| Priority | Journal | Q | APC |
|---|---|---|---|
| 1 | Journal of Empirical Finance | Q1 Elsevier | ~2,500€ (cubierto IQS) |
| 2 | International Review of Economics and Finance | Q1 Elsevier | cubierto IQS |
| 3 | Financial Analysts Journal | Q2 T&F | TBD |
| 4 | Finance Research Letters | Q2 Elsevier | cubierto IQS |

Decisión final: Francesc Prior. Cerrar antes de empezar a formatear para journal específico.

---

## Decisiones tomadas

| Decisión | Valor |
|---|---|
| Template | `elsarticle` (Elsevier standard) — cambiar a T&F si el target es FAJ |
| Optimum3 | NO se menciona en ningún momento. Anclaje en literatura académica primaria |
| Cadena de citas breadth filter | Keller & Keuning 2017 HAA (SSRN, citable) — no Keller & Butler |
| Benchmarks | 60/40, B&H EW15, Faber 2007 trend-following — sin Optimum3 |
| rf para Sharpe | rf=0% (consistente con backtest verificado) |

## Decisiones pendientes

| Decisión | Opciones | Quién decide |
|---|---|---|
| Journal final | JEF / IREF / FRL / FAJ | Francesc |
| Orden de autores | Garcia M. / Mases C. / Prior S. — TBC | Francesc / Marc |
| Transaction costs model | Modelar explícitamente o solo en robustness | Marc / Francesc |
| Longitud target | 8,000–10,000 (JEF) vs 5,000 (FRL) | Según journal final |

---

## Co-autores y roles (provisional)

- **Ignasi Garcia Martin** — diseño y backtesting de la estrategia, redacción principal
- **Marc Mases Campos** — co-tutor, LaTeX, revisión metodológica
- **Francesc Prior Sanz** — tutor, dirección académica, decisión journal

---

## Protocolo de sesión

### Al INICIAR:
1. Leer este STATUS.md
2. Confirmar qué sección trabajamos
3. Leer el stub .tex correspondiente

### Al CERRAR:
1. Marcar progreso en la tabla de secciones
2. Actualizar "Próxima acción"
3. Escribir **"SESIÓN CERRADA — STATUS actualizado"**
