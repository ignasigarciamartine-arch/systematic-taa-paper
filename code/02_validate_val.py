# -*- coding: utf-8 -*-
"""
02_validate_val.py — ETAPA 2 (protocolo Marc): VALIDAR/SELECCIONAR en VAL (2016-2020, 60m).
================================================================================
Toma el set óptimo-en-train (etapa 01) y lo valida en VAL. Donde un parámetro de
train difiera de la literatura (aquí solo k: 5 vs 3), evalúa AMBOS candidatos en VAL
y selecciona el que mejor se comporta OUT-OF-SAMPLE-en-val (Sharpe + control de DD +
alfa vs 1/N). Regla de decisión: si el pick de train NO mejora en val, se revierte a
literatura y se documenta (anti-overfit).

VAL es selección, NO el claim final. El cierre es TEST (etapa 04), que no se mira aquí.

Escribe: data/outputs/VALIDATE_VAL.md, validate_val.csv, val_selected_params.csv
"""
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import lib, config as C

lib.load()
LO, HI = C.VAL
rng = np.random.default_rng(C.SEED)
b1n = lib.bench_1n()

train_opt = pd.read_csv(C.OUT/'train_selected_params.csv').iloc[0].to_dict()
train_opt = {'signal': str(train_opt['signal']), 'top_n': int(train_opt['top_n']),
             'theta': float(train_opt['theta']), 'k': int(train_opt['k'])}
LIT = {'signal': '13612U', 'top_n': 7, 'theta': 0.02, 'k': 3}

# candidatos = train_opt + literatura (se distinguen donde difieran)
candidates = {'TRAIN_OPT': train_opt, 'LITERATURA': LIT}
# dedup si coinciden
if train_opt == LIT:
    candidates = {'TRAIN_OPT=LIT': train_opt}

print("="*84)
print(f"VALIDACIÓN EN VAL {LO[:7]} a {HI[:7]}")
print("="*84)
rows = []
evals = {}
for name, p in candidates.items():
    g = lib.gat(signal_kind=p['signal'], top_n=p['top_n'], theta=p['theta'], k=p['k'])
    m = lib.met(g, LO, HI)
    o, l, h, pv = lib.sdiff(g, b1n, LO, HI, rng)
    a, ap, beta = lib.spanning_alpha(g, b1n, LO, HI)
    evals[name] = {'params': p, 'm': m, 'sdiff': (o, pv, l), 'alpha': (a, ap)}
    print(f"\n[{name}] {p}")
    print(f"   CAGR {m['cagr']*100:.2f}%  Sharpe {m['sharpe']:.3f}  Vol {m['vol']*100:.2f}%  MaxDD {m['maxdd']*100:.2f}%")
    print(f"   ΔSharpe vs 1/N {o:+.3f} [{l:+.3f},{h:+.3f}] p={pv:.3f}")
    print(f"   Alfa spanning vs 1/N {a*100:+.2f}%/año p={ap:.4f}{' ✅' if ap<0.05 else ''}  (β={beta:+.2f})")
    rows.append({'candidate': name, **p, 'val_cagr': m['cagr'], 'val_sharpe': m['sharpe'],
                 'val_maxdd': m['maxdd'], 'val_sdiff_1n': o, 'val_sdiff_p': pv,
                 'val_alpha_1n': a, 'val_alpha_p': ap})

# --- selección ---
if len(candidates) == 1:
    selected = list(candidates.values())[0]; reason = "train_opt = literatura; nada que decidir"
else:
    # criterio: Sharpe en val como primario; si empate técnico (<0.05), preferir mejor MaxDD (riesgo)
    by_sharpe = sorted(evals.items(), key=lambda kv: kv[1]['m']['sharpe'], reverse=True)
    top, second = by_sharpe[0], by_sharpe[1]
    if top[1]['m']['sharpe'] - second[1]['m']['sharpe'] < 0.05:
        # empate -> mejor drawdown
        best = max(evals.items(), key=lambda kv: kv[1]['m']['maxdd'])  # maxdd negativo: mayor = menos profundo
        selected = best[1]['params']
        reason = (f"Sharpe en val empatado ({top[0]} {top[1]['m']['sharpe']:.3f} vs "
                  f"{second[0]} {second[1]['m']['sharpe']:.3f}); se elige por menor drawdown -> "
                  f"{best[0]} (MaxDD {best[1]['m']['maxdd']*100:.2f}%)")
    else:
        selected = top[1]['params']
        reason = f"{top[0]} domina en Sharpe-val ({top[1]['m']['sharpe']:.3f})"

print("\n" + "="*84)
print(f"PARÁMETROS SELECCIONADOS (post-val, a congelar): {selected}")
print(f"Motivo: {reason}")
print("="*84)

pd.DataFrame(rows).to_csv(C.OUT/'validate_val.csv', index=False)
pd.DataFrame([selected]).to_csv(C.OUT/'val_selected_params.csv', index=False)
md = ["# VALIDACIÓN EN VAL — etapa 2 (protocolo Marc)\n",
      f"> VAL = **{LO[:7]} a {HI[:7]}** ({list(evals.values())[0]['m']['n']}m). Selección OOS-en-val "
      "del set óptimo-en-train vs literatura. VAL es selección, NO el claim final (ese es TEST).",
      "> `code/02_validate_val.py`.\n",
      "## Candidatos en VAL\n",
      "| Candidato | señal | N | θ | k | CAGR | Sharpe | MaxDD | ΔSR vs 1/N (p) | α vs 1/N (p) |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for name, e in evals.items():
    p, m = e['params'], e['m']; o, pv, _ = e['sdiff']; a, ap = e['alpha']
    md.append(f"| {name} | {p['signal']} | {p['top_n']} | {p['theta']} | {p['k']} | {m['cagr']*100:.2f}% | "
              f"{m['sharpe']:.3f} | {m['maxdd']*100:.2f}% | {o:+.3f} ({pv:.3f}) | {a*100:+.2f}% ({ap:.3f}) |")
md += [f"\n## Selección\n", f"**{selected}**\n", f"Motivo: {reason}"]
(C.OUT/'VALIDATE_VAL.md').write_text("\n".join(md), encoding='utf-8')
print(f"\nSaved: VALIDATE_VAL.md, validate_val.csv, val_selected_params.csv")
