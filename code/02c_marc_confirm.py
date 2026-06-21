# -*- coding: utf-8 -*-
"""
02c_marc_confirm.py — Método EXACTO de Marc, transparente:
  óptimo en TRAIN (coordenadas) -> se confirma en VAL y en TRAIN+VAL (pooled) -> siguiente.
NO selecciona por val; toma el óptimo-train y muestra si "da bien" en val y train+val.
El único caso donde óptimo-train y val/train+val discrepan se marca para decisión humana.
Test queda intacto (04_test). Solo informa; no sobreescribe el lock.
"""
import sys
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
import numpy as np, pandas as pd
import lib, config as C

lib.load()
TR = C.TRAIN; VA = C.VAL; TV = ('2004-02-01', '2020-12-31')  # train+val pooled
SIGNALS = ['1m','3m','6m','12m','612','3612','13612U','13612W']
TOPNS = list(range(1,13)); THETAS=[0.0,0.005,0.01,0.015,0.02,0.025,0.03,0.035,0.04,0.045,0.05]; KS=[1,2,3,4,5,6]
LIT = {'signal':'13612U','top_n':7,'theta':0.02,'k':3}
sel = dict(LIT)

def sh3(**kw):
    p=dict(sel); p.update(kw)
    g=lib.gat(signal_kind=p['signal'],top_n=p['top_n'],theta=p['theta'],k=p['k'])
    return (lib.met(g,*TR)['sharpe'], lib.met(g,*VA)['sharpe'], lib.met(g,*TV)['sharpe'])

def scan(rule,grid,key,label):
    print(f"\n--- {rule} ({label}): óptimo en train, luego confirmar en val y train+val ---")
    print(f"   {label:<8}{'train':>8}{'val':>8}{'tr+val':>8}")
    res={}
    for v in grid:
        t,va,tv=sh3(**{key:v}); res[v]=(t,va,tv)
        mark=' <-LIT' if v==LIT[key] else ''
        print(f"   {str(v):<8}{t:>8.3f}{va:>8.3f}{tv:>8.3f}{mark}")
    opt_tr   = max(res, key=lambda v:res[v][0])
    opt_val  = max(res, key=lambda v:res[v][1])
    opt_tv   = max(res, key=lambda v:res[v][2])
    print(f"   óptimo TRAIN={opt_tr} (SR {res[opt_tr][0]:.3f}) | mejor VAL={opt_val} | mejor TR+VAL={opt_tv}")
    agree = (opt_tr==opt_val==opt_tv)
    print(f"   -> óptimo-train {'CONFIRMA en val y train+val (da bien)' if agree else 'DISCREPA: val/train+val prefieren '+str(opt_val)+'/'+str(opt_tv)}")
    sel[key]=opt_tr   # método Marc: se queda el óptimo-train
    return opt_tr, opt_val, opt_tv, agree

print("="*60); print("MÉTODO MARC — óptimo train confirmado en val y train+val"); print("="*60)
r1=scan('R1',SIGNALS,'signal','señal')
r2=scan('R2',TOPNS,'top_n','top-N')
r3=scan('R3',THETAS,'theta','θ')
# θ NO se deriva por argmax: se FIJA EX-ANTE en rf (Antonacci θ≈2%). El óptimo-train real
# (~5%) NO se persigue (anti-snooping); θ es suelo de riesgo, no selección. Override:
sel['theta']=LIT['theta']
print(f"   >> θ FIJADO EX-ANTE = {LIT['theta']*100:.0f}% (Antonacci θ≈rf), NO el argmax de train (suelo de riesgo, no optimizado).")
r4=scan('R4',KS,'k','k')
print("\n"+"="*60)
print(f"SET por óptimo-train (método Marc literal): {sel}")
print("Reglas donde val/train+val discrepan del óptimo-train:")
for nm,(ot,ov,otv,ag) in [('R1',r1),('R2',r2),('R3',r3),('R4',r4)]:
    if not ag: print(f"   {nm}: train={ot}  val-best={ov}  trainval-best={otv}")
print("="*60)
