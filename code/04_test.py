# -*- coding: utf-8 -*-
"""
04_test.py — ETAPA 4 (protocolo Marc): CIERRE ÚNICO EN TEST (2021-2025, 60m).
================================================================================
Evalúa la estrategia CONGELADA (params post-val) una sola vez en TEST. Este es el
CLAIM PRIMARIO del paper. VAL y FULL/VALTEST se reportan como contexto/soporte.

Reporta en TEST:
  - métricas (CAGR, Sharpe, Sortino, MaxDD, Calmar)
  - Sharpe ≠ 0 (Lo 2002)
  - Sharpe-difference vs 1/N, 60/40, Faber, SPY (bootstrap de bloque)
  - alfa de spanning Newey-West: vs 1/N, CAPM(SPY), 2-factor(SPY+IEF)
Y la misma batería de alfa en VALTEST(120m) y FULL(263m) para mostrar la potencia.

Escribe: data/outputs/TEST_RESULTS.md, test_results.csv
"""
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd, statsmodels.api as sm
import lib, config as C

lib.load()
p = pd.read_csv(C.OUT/'val_selected_params.csv').iloc[0].to_dict()
P = {'signal': str(p['signal']), 'top_n': int(p['top_n']), 'theta': float(p['theta']), 'k': int(p['k'])}
print(f"Estrategia congelada: {P}\n")

g = lib.gat(signal_kind=P['signal'], top_n=P['top_n'], theta=P['theta'], k=P['k'])
B = lib.benchmarks()

def multi_alpha(r, factors, lo, hi):
    """Alfa Newey-West de r sobre varios factores (series de retorno bruto)."""
    r = r.loc[lo:hi].dropna(); rfc = lib.rf_mon.reindex(r.index, method='ffill').fillna(0)
    y = (r - rfc).rename('y')
    cols = {nm: (f.loc[lo:hi].reindex(y.index) - rfc) for nm, f in factors.items()}
    df = pd.concat([y, pd.DataFrame(cols)], axis=1).dropna()
    X = sm.add_constant(df[list(cols)].values)
    m = sm.OLS(df['y'].values, X).fit(cov_type='HAC', cov_kwds={'maxlags': C.HAC})
    return float(m.params[0])*12, float(m.pvalues[0])

# --- métricas por período ---
print("="*92)
print("MÉTRICAS por período (estrategia congelada)")
print("="*92)
print(f"{'Período':<10}{'n':>5}{'CAGR':>9}{'Vol':>8}{'Sharpe':>8}{'Sortino':>9}{'MaxDD':>9}{'Calmar':>8}")
met_rows = []
for pn in ['TRAIN', 'VAL', 'TEST', 'VALTEST', 'FULL']:
    lo, hi = C.PERIODS[pn]; m = lib.met(g, lo, hi)
    print(f"{pn:<10}{m['n']:>5}{m['cagr']*100:>8.2f}%{m['vol']*100:>7.2f}%{m['sharpe']:>8.3f}"
          f"{m['sortino']:>9.3f}{m['maxdd']*100:>8.2f}%{m['calmar']:>8.2f}")
    met_rows.append({'period': pn, **m})

# --- batería inferencial: TEST (primario) + VALTEST + FULL (soporte) ---
test_rows = []
for pn in ['TEST', 'VALTEST', 'FULL']:
    lo, hi = C.PERIODS[pn]; rng = np.random.default_rng(C.SEED)
    print("\n" + "="*92)
    print(f"{pn}  ({lib.met(g,lo,hi)['n']}m)" + ("   <-- CLAIM PRIMARIO" if pn == 'TEST' else "   (soporte)"))
    print("="*92)
    sr, p_lo = lib.lo_sharpe(g, lo, hi)
    print(f"  Sharpe = {sr:.3f}  (≠0 Lo 2002: p={p_lo:.4f}{' ✅' if p_lo<0.05 else ''})")
    print("  Sharpe-difference vs benchmarks:")
    for nm, bs in B.items():
        o, l, h, pv = lib.sdiff(g, bs, lo, hi, rng)
        sig = '✅' if l > 0 else ('⚠️peor' if h < 0 else 'n.s.')
        print(f"    vs {nm:<11} Δ={o:+.3f} [{l:+.3f},{h:+.3f}] p={pv:.3f} {sig}")
        test_rows.append({'period': pn, 'test': f'sdiff_{nm}', 'value': o, 'pval': pv, 'ci_lo': l})
    a1, p1, b1 = lib.spanning_alpha(g, B['1/N'], lo, hi)
    ac, pc, bc = lib.spanning_alpha(g, B['SPY B&H'], lo, hi)
    a2, p2 = multi_alpha(g, {'SPY': B['SPY B&H'], 'IEF': lib.mr['IEF']}, lo, hi)
    print("  Alfa de spanning (Newey-West):")
    print(f"    vs 1/N            α={a1*100:+.2f}%/año p={p1:.4f}{' ✅' if p1<0.05 else ''} (β={b1:+.2f})")
    print(f"    CAPM (SPY)        α={ac*100:+.2f}%/año p={pc:.4f}{' ✅' if pc<0.05 else ''} (β={bc:+.2f})")
    print(f"    2-factor SPY+IEF  α={a2*100:+.2f}%/año p={p2:.4f}{' ✅' if p2<0.05 else ''}")
    for nm, (a, pv) in [('alpha_1n', (a1, p1)), ('alpha_capm', (ac, pc)), ('alpha_2f', (a2, p2))]:
        test_rows.append({'period': pn, 'test': nm, 'value': a, 'pval': pv})
    test_rows.append({'period': pn, 'test': 'lo_sharpe', 'value': sr, 'pval': p_lo})

pd.DataFrame(met_rows).to_csv(C.OUT/'test_results.csv', index=False)
pd.DataFrame(test_rows).to_csv(C.OUT/'test_inference.csv', index=False)

# --- markdown ---
mt = {r['period']: r for r in met_rows}
ti = {}
for r in test_rows: ti.setdefault(r['period'], {})[r['test']] = (r['value'], r['pval'])
md = ["# CIERRE EN TEST — etapa 4 (protocolo Marc, claim primario)\n",
      f"> Estrategia congelada `{P}`. TEST = **{C.TEST[0][:7]} a {C.TEST[1][:7]}** "
      f"({mt['TEST']['n']}m), evaluado una sola vez. VALTEST/FULL = soporte. `code/04_test.py`.\n",
      "## Métricas por período\n",
      "| Período | n | CAGR | Vol | Sharpe | Sortino | MaxDD | Calmar |",
      "|---|---|---|---|---|---|---|---|"]
for pn in ['TRAIN', 'VAL', 'TEST', 'VALTEST', 'FULL']:
    m = mt[pn]
    md.append(f"| {pn} | {m['n']} | {m['cagr']*100:.2f}% | {m['vol']*100:.2f}% | {m['sharpe']:.3f} | "
              f"{m['sortino']:.3f} | {m['maxdd']*100:.2f}% | {m['calmar']:.2f} |")
md += ["\n## Inferencia: TEST (primario) vs soporte\n",
       "| Test | TEST (60m) | VALTEST (120m) | FULL (263m) |", "|---|---|---|---|"]
def cell(pn, key):
    v, pv = ti[pn][key]
    pct = key.startswith('alpha')
    s = f"{v*100:+.2f}% (p={pv:.4f})" if pct else f"{v:+.3f} (p={pv:.3f})" if key.startswith('sdiff') else f"{v:.3f} (p={pv:.4f})"
    return s + (' ✅' if pv < 0.05 else '')
for key, lab in [('lo_sharpe', 'Sharpe (≠0)'), ('sdiff_1/N', 'ΔSharpe vs 1/N'),
                 ('alpha_1n', 'α spanning vs 1/N'), ('alpha_capm', 'α CAPM (SPY)'),
                 ('alpha_2f', 'α 2-factor (SPY+IEF)')]:
    md.append(f"| {lab} | {cell('TEST',key)} | {cell('VALTEST',key)} | {cell('FULL',key)} |")
md += ["\n## Lectura honesta\n",
       f"- TEST (60m) es el claim primario. α vs 1/N = {ti['TEST']['alpha_1n'][0]*100:+.2f}%/año "
       f"(p={ti['TEST']['alpha_1n'][1]:.4f}).",
       "- La potencia cae con n: comparar TEST(60m) vs VALTEST(120m) vs FULL(263m) muestra el efecto. "
       "Effect size estable, significancia depende de la ventana — declararlo."]
(C.OUT/'TEST_RESULTS.md').write_text("\n".join(md), encoding='utf-8')
print(f"\nSaved: TEST_RESULTS.md, test_results.csv, test_inference.csv")
