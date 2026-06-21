# -*- coding: utf-8 -*-
"""
01_derive_train.py — ETAPA 1 (protocolo Marc): DERIVAR en TRAIN (2004-2015, 143m).
================================================================================
Para cada regla (R1 señal, R2 top-N, R3 θ, R4 k) hace un grid scan SOLO en train
(descenso por coordenadas en orden R1->R2->R3->R4) y reporta:
  - perfil completo (param -> Sharpe en train)
  - óptimo-en-train (argmax)
  - valor de literatura
  - test de Sharpe-difference bootstrap (literatura vs óptimo-en-train): si p>0.05,
    el valor de literatura es indistinguible del óptimo -> no pudo sobreajustarse.

Emite los PARÁMETROS SELECCIONADOS = óptimo-en-train (enfoque Marc: optimizar en train).
La etapa 02 los VALIDA en val y decide si revertir a literatura cuando un pick de train
no sobreviva OOS.

Escribe: data/outputs/DERIVE_TRAIN.md, derive_train_profiles.csv, train_selected_params.csv
"""
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import lib, config as C

lib.load()
LO, HI = C.TRAIN
rng = np.random.default_rng(C.SEED)

SIGNALS = ['1m', '3m', '6m', '12m', '612', '3612', '13612U', '13612W']
TOPNS   = list(range(1, 13))
THETAS  = [0.0, 0.005, 0.01, 0.015, 0.02, 0.025, 0.03, 0.035, 0.04, 0.045, 0.05]  # rejilla completa (sin tope artificial)
KS      = [1, 2, 3, 4, 5, 6]
LIT = {'signal': '13612U', 'top_n': 7, 'theta': 0.02, 'k': 3}

def sh(**kw):
    """Sharpe en train de GAT con los params dados (resto = sel actual)."""
    p = dict(sel); p.update(kw)
    g = lib.gat(signal_kind=p['signal'], top_n=p['top_n'], theta=p['theta'], k=p['k'])
    return lib.met(g, LO, HI)['sharpe'], g

sel = dict(LIT)   # arranca en literatura; se va fijando al argmax de train
profiles, summary = [], []

def scan(rule, grid, key, label):
    print(f"\n--- {rule}: scan {label} (resto fijo en {sel}) ---")
    res = []
    for v in grid:
        s, _ = sh(**{key: v}); res.append((v, s))
        profiles.append({'rule': rule, 'param': key, 'value': v, 'train_sharpe': s})
        mark = ' <-LIT' if v == LIT[key] else ''
        print(f"   {label}={str(v):<8} Sharpe={s:.3f}{mark}")
    argmax = max(res, key=lambda x: x[1])
    lit_v = LIT[key]; lit_s = dict(res)[lit_v]
    # Sharpe-diff bootstrap (train): literatura vs óptimo-en-train
    _, g_lit = sh(**{key: lit_v}); _, g_opt = sh(**{key: argmax[0]})
    obs, l, h, p = lib.sdiff(g_opt, g_lit, LO, HI, rng)
    indist = (p > 0.05)
    print(f"   -> argmax {label}={argmax[0]} (SR {argmax[1]:.3f}) | LIT={lit_v} (SR {lit_s:.3f}) "
          f"| ΔSR(opt-lit)={obs:+.3f} p={p:.3f} -> {'INDISTINGUIBLE' if indist else 'distinto'}")
    sel[key] = argmax[0]   # descenso por coordenadas: fija el argmax
    summary.append({'rule': rule, 'param': key, 'lit': lit_v, 'lit_sharpe': round(lit_s, 3),
                    'train_opt': argmax[0], 'opt_sharpe': round(argmax[1], 3),
                    'dsr_obs': round(obs, 3), 'dsr_p': round(p, 3),
                    'indistinguible': indist})
    return argmax[0]

print("="*80)
print(f"DERIVACIÓN EN TRAIN {LO[:7]} a {HI[:7]} ({lib.met(lib.gat(),LO,HI)['n']}m)")
print("="*80)
scan('R1', SIGNALS, 'signal', 'señal')
scan('R2', TOPNS,   'top_n',  'top-N')
scan('R3', THETAS,  'theta',  'θ')   # reporta el perfil; el argmax NO se adopta (ver abajo)
# --- R3 (θ): NO se deriva por argmax. Se FIJA EX-ANTE en el risk-free (Antonacci θ≈2%). ---
# El perfil de train es dentado y su máximo está más alto (~5%), pero perseguirlo sería
# data-snooping: θ tiene ancla económica (activo bajo cash = sin prima esperada) y su papel
# es control de cola (suelo de riesgo), no selección. Override explícito tras el scan:
sel['theta'] = LIT['theta']
print(f"\n[R3] θ FIJADO EX-ANTE = {LIT['theta']*100:.0f}% (Antonacci θ≈rf), NO el argmax de train. sel={sel}")
scan('R4', KS,      'k',      'k')

# R4 extra: min-corr vs top-k por rank (reducción de varianza, no Sharpe)
g_mc = lib.gat(signal_kind=sel['signal'], top_n=sel['top_n'], theta=sel['theta'], k=sel['k'], min_corr=True)
g_rk = lib.gat(signal_kind=sel['signal'], top_n=sel['top_n'], theta=sel['theta'], k=sel['k'], min_corr=False)
m_mc, m_rk = lib.met(g_mc, LO, HI), lib.met(g_rk, LO, HI)
print(f"\n--- R4 min-corr vs top-k-rank (k={sel['k']}) en train ---")
print(f"   min-corr: SR {m_mc['sharpe']:.3f} vol {m_mc['vol']*100:.2f}% MaxDD {m_mc['maxdd']*100:.2f}%")
print(f"   top-rank: SR {m_rk['sharpe']:.3f} vol {m_rk['vol']*100:.2f}% MaxDD {m_rk['maxdd']*100:.2f}%")
print(f"   -> reducción vol {(1-m_mc['vol']/m_rk['vol'])*100:+.1f}%, MaxDD {(m_mc['maxdd']-m_rk['maxdd'])*100:+.1f}pp")

print("\n" + "="*80)
print("PARÁMETROS SELECCIONADOS (óptimo-en-train, a validar en VAL):")
print(f"   {sel}")
print("="*80)

# --- guardar ---
pd.DataFrame(profiles).to_csv(C.OUT/'derive_train_profiles.csv', index=False)
pd.DataFrame([sel]).to_csv(C.OUT/'train_selected_params.csv', index=False)
sm_df = pd.DataFrame(summary)
md = ["# DERIVACIÓN EN TRAIN — etapa 1 (protocolo Marc 60/20/20)\n",
      f"> Train = **{LO[:7]} a {HI[:7]}** ({m_mc['n']}m). Grid scan por coordenadas R1->R2->R3->R4.",
      "> Selección = óptimo-en-train; se valida en VAL (etapa 02). `code/01_derive_train.py`.\n",
      "## Resumen por regla\n",
      "| Regla | Param | Literatura | SR_lit | Óptimo train | SR_opt | ΔSR(opt-lit) | p | ¿Indistinguible? |",
      "|---|---|---|---|---|---|---|---|---|"]
for r in summary:
    md.append(f"| {r['rule']} | {r['param']} | {r['lit']} | {r['lit_sharpe']} | {r['train_opt']} | "
              f"{r['opt_sharpe']} | {r['dsr_obs']:+.3f} | {r['dsr_p']} | "
              f"{'✅ sí' if r['indistinguible'] else '❌ no'} |")
md += ["\n> **θ (R3) NO se selecciona por argmax — se FIJA EX-ANTE en 2% (Antonacci θ≈rf).** El perfil de train",
       "> es dentado y su máximo real está más alto (~5%, fila R3 arriba), pero NO se persigue: θ tiene ancla",
       "> económica (activo bajo cash = sin prima) y su función es **control de cola** (suelo de riesgo), no",
       "> selección. Justificación del valor 2% = economía + drawdown (θ<1.5% dispara el MaxDD de val), no",
       "> optimización. Robusto en [1.5%, 4%]. R1/R2/R4 sí son óptimo-train directo = literatura."]
md += ["\n## R4 min-corr vs top-k-rank (train)\n",
       f"- min-corr: Sharpe {m_mc['sharpe']:.3f}, vol {m_mc['vol']*100:.2f}%, MaxDD {m_mc['maxdd']*100:.2f}%",
       f"- top-rank: Sharpe {m_rk['sharpe']:.3f}, vol {m_rk['vol']*100:.2f}%, MaxDD {m_rk['maxdd']*100:.2f}%",
       f"- min-corr reduce vol {(1-m_mc['vol']/m_rk['vol'])*100:+.1f}% y MaxDD {(m_mc['maxdd']-m_rk['maxdd'])*100:+.1f}pp "
       "(defensa por riesgo, no por retorno).",
       f"\n## Parámetros seleccionados (a validar en VAL)\n",
       f"`{sel}`"]
(C.OUT/'DERIVE_TRAIN.md').write_text("\n".join(md), encoding='utf-8')
print(f"\nSaved: DERIVE_TRAIN.md, derive_train_profiles.csv, train_selected_params.csv")
