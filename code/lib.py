# -*- coding: utf-8 -*-
"""
lib.py — MOTOR ÚNICO del rebuild. Extraído del motor canónico verificado
(look-ahead defensivo corregido) y PARAMETRIZADO para grid scans en derivación.

Importan de aquí TODOS los scripts (01_derive_train, 02_validate_val, 03_lock,
04_test, 05_robustness, 06_figures). Un solo motor = no se repite el bug de los
16 motores duplicados.

API principal:
  load()                         -> carga px, mr, months, rf_mon, MOM (global, una vez)
  gat(signal_kind='13612U', top_n=7, theta=0.02, k=3)  -> serie mensual de retornos GAT
  bench_1n/6040/spy/faber()      -> series de benchmarks
  met(r, lo, hi)                 -> dict de métricas (CAGR, Sharpe, Sortino, MaxDD, Calmar)
  sdiff(a, b, lo, hi, rng)       -> Sharpe-difference bootstrap de bloque (obs, ci_lo, ci_hi, p)
  lo_sharpe(r, lo, hi)           -> Sharpe + p de Lo (2002) (≠0)
  spanning_alpha(r, bench, lo, hi) -> alfa Newey-West (alpha_anual, p, beta)
  momentum(kind)                 -> DataFrame de señal de momentum (para R1 scan)
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from itertools import combinations
import requests, statsmodels.api as sm
from scipy import stats
import config as C

# --- estado global (se rellena en load) ---
px = mr = MOM = rf_mon = None
months = None

def load():
    """Carga dataset + rf + momentum 13612U por defecto. Idempotente."""
    global px, mr, MOM, rf_mon, months
    if px is not None:
        return
    px = pd.read_csv(C.D / 'dataset_extended.csv', index_col='Date', parse_dates=True)
    px.index = pd.to_datetime(px.index).tz_localize(None)
    mr = px.pct_change(fill_method=None)
    months = mr.index.tolist()
    # rf desde FRED TB3MS; si falla, 0
    try:
        url = ("https://api.stlouisfed.org/fred/series/observations?series_id=TB3MS"
               "&observation_start=2003-01-01&observation_end=2025-12-31&frequency=m"
               f"&file_type=json&api_key={C.FRED}")
        o = requests.get(url, timeout=30).json()['observations']
        rf = pd.DataFrame(o)[['date', 'value']]
        rf['value'] = pd.to_numeric(rf['value'], errors='coerce')
        rf = rf.set_index('date')['value']; rf.index = pd.to_datetime(rf.index)
        rf_mon = (rf / 100 / 12).resample('ME').last().dropna()
    except Exception:
        rf_mon = pd.Series(0.0, index=mr.index)
    MOM = momentum('13612U')

def momentum(kind='13612U'):
    """Señal de momentum por activo riesgoso. Soporta variantes para el scan de R1."""
    p = px
    def r(n): return p.pct_change(n)
    if kind == '13612U':
        sig = {c: (r(1)[c] + r(3)[c] + r(6)[c] + r(12)[c]) / 4 for c in C.RISKY}
    elif kind == '13612W':  # ponderado (Keller): pesos 12,4,2,1 sobre 1,3,6,12m
        sig = {c: (12*r(1)[c] + 4*r(3)[c] + 2*r(6)[c] + 1*r(12)[c]) / 19 for c in C.RISKY}
    elif kind == '1m':   sig = {c: r(1)[c]  for c in C.RISKY}
    elif kind == '3m':   sig = {c: r(3)[c]  for c in C.RISKY}
    elif kind == '6m':   sig = {c: r(6)[c]  for c in C.RISKY}
    elif kind == '12m':  sig = {c: r(12)[c] for c in C.RISKY}
    elif kind == '612':  sig = {c: (r(6)[c] + r(12)[c]) / 2 for c in C.RISKY}
    elif kind == '3612': sig = {c: (r(3)[c] + r(6)[c] + r(12)[c]) / 3 for c in C.RISKY}
    else:
        raise ValueError(f"señal desconocida: {kind}")
    return pd.DataFrame(sig)

def _get_corr(a, t, w=12):
    av = [x for x in a if x in mr.columns]
    if len(av) < 2: return pd.DataFrame(np.eye(len(a)), index=a, columns=a)
    ip = months.index(t) if t in months else -1
    if ip < 0: return pd.DataFrame(np.eye(len(a)), index=a, columns=a)
    wr = mr.iloc[max(0, ip-w):ip+1][av].dropna(how='all')
    if len(wr) < 4: return pd.DataFrame(np.eye(len(a)), index=a, columns=a)
    c = wr.corr()
    for x in a:
        if x not in c.index: c.loc[x, :] = 0; c.loc[:, x] = 0; c.loc[x, x] = 1
    return c.reindex(index=a, columns=a)

def _min_corr_triplet(a, c, k=3):
    if len(a) <= k: return a
    best, br = a[:k], np.inf
    for s in combinations(a, k):
        rbar = np.nanmean([c.loc[i, j] for i, j in combinations(s, 2)])
        if rbar < br: br, best = rbar, list(s)
    return best

def _defensive(t1, mom):
    """Rama defensiva. La composición se decide con el momentum de la SEÑAL (t=t1-1),
    NO del mes de tenencia t1 (look-ahead corregido)."""
    if t1 not in mr.index: return 0.0
    j = months.index(t1); td = months[j-1] if j > 0 else t1
    if td in mom.index:
        mt, mi = mom.loc[td, 'TLT'], mom.loc[td, 'IEF']
        if pd.notna(mt) and pd.notna(mi) and max(mt, mi) >= 0:
            v = [mr.loc[t1, a] for a in ['TLT', 'IEF'] if not np.isnan(mr.loc[t1, a])]
            return float(np.mean(v)) if v else 0.0
    return mr.loc[t1, C.CASH] if t1 in mr.index else 0.0

def gat(signal_kind='13612U', top_n=C.TOP_N, theta=C.THETA, k=C.K, min_corr=True):
    """Serie mensual de retornos GAT (4 reglas, sin crash filter). Parametrizada
    para grid scans. min_corr=False -> top-k por rank (para atribución de R4)."""
    mom = MOM if signal_kind == '13612U' else momentum(signal_kind)
    pr, dt = [], []
    for i, t in enumerate(months):
        if i + 1 >= len(months): continue
        t1 = months[i+1]
        if t not in mom.index: continue
        sig = mom.loc[t, C.RISKY].dropna()
        ranked = sig.sort_values(ascending=False).head(top_n)
        elig = ranked[ranked >= theta].index.tolist()
        if len(elig) < 3:
            pr.append(_defensive(t1, mom)); dt.append(t1); continue
        sel = _min_corr_triplet(elig, _get_corr(elig, t), k) if min_corr else elig[:k]
        rr = mr.loc[t1, sel].dropna() if t1 in mr.index else pd.Series(dtype=float)
        pr.append(rr.mean() if len(rr) > 0 else 0.0); dt.append(t1)
    return pd.Series(pr, index=dt).dropna()

# --- benchmarks ---
def bench_1n():   return mr[C.RISKY].mean(axis=1).dropna()
def bench_6040(): return (0.6*mr['SPY'] + 0.4*mr['IEF']).dropna()
def bench_spy():  return mr['SPY'].dropna()
def bench_faber():
    sma = px[C.RISKY].rolling(10).mean(); pr, dt = [], []
    for i, t in enumerate(months):
        if i + 1 >= len(months): continue
        t1 = months[i+1]
        if t not in sma.index: continue
        rs = 0.0; nin = 0
        for a in C.RISKY:
            if a in px.columns and pd.notna(px.loc[t, a]) and pd.notna(sma.loc[t, a]):
                if px.loc[t, a] > sma.loc[t, a] and t1 in mr.index and pd.notna(mr.loc[t1, a]):
                    rs += mr.loc[t1, a] / 15.0; nin += 1
        cw = (15 - nin) / 15.0
        rc = mr.loc[t1, C.CASH] if (t1 in mr.index and pd.notna(mr.loc[t1, C.CASH])) else 0.0
        pr.append(rs + cw*rc); dt.append(t1)
    return pd.Series(pr, index=dt).dropna()

def benchmarks():
    return {'1/N': bench_1n(), '60/40': bench_6040(), 'Faber 2007': bench_faber(), 'SPY B&H': bench_spy()}

# --- métricas y tests ---
def met(r, lo, hi):
    r = r.loc[lo:hi].dropna()
    rfc = rf_mon.reindex(r.index, method='ffill').fillna(0); e = r - rfc; n = len(r)
    eq = (1+r).cumprod(); dd = ((eq/eq.cummax()) - 1).min(); cagr = (1+r).prod()**(12/n) - 1
    return {'n': n, 'cagr': cagr, 'vol': r.std()*np.sqrt(12),
            'sharpe': e.mean()/e.std()*np.sqrt(12) if e.std() > 0 else np.nan,
            'sortino': (e.mean()*12/(e[e < 0].std()*np.sqrt(12))) if e[e < 0].std() > 0 else np.nan,
            'maxdd': dd, 'calmar': cagr/abs(dd) if dd < 0 else np.nan}

def _block_idx(rng, T, b):
    idx = []
    while len(idx) < T:
        s = rng.integers(0, T); idx.extend([(s+kk) % T for kk in range(b)])
    return np.array(idx[:T])

def sdiff(a, b, lo, hi, rng):
    a = a.loc[lo:hi]; b = b.loc[lo:hi]; c = a.index.intersection(b.index)
    if len(c) < 12: return np.nan, np.nan, np.nan, np.nan
    rfc = rf_mon.reindex(c, method='ffill').fillna(0).values
    ea = a.loc[c].values - rfc; eb = b.loc[c].values - rfc; T = len(c)
    obs = (ea.mean()/ea.std() - eb.mean()/eb.std()) * np.sqrt(12)
    df = np.empty(C.Bn)
    for j in range(C.Bn):
        ix = _block_idx(rng, T, C.BLOCK); sa, sb = ea[ix], eb[ix]
        df[j] = (sa.mean()/sa.std() - sb.mean()/sb.std())*np.sqrt(12) if sa.std() > 0 and sb.std() > 0 else 0
    l, h = np.percentile(df, [2.5, 97.5])
    return obs, l, h, 2*min((df <= 0).mean(), (df >= 0).mean())

def lo_sharpe(r, lo, hi):
    r = r.loc[lo:hi].dropna(); rfc = rf_mon.reindex(r.index, method='ffill').fillna(0)
    e = (r - rfc).values; n = len(e)
    sr = e.mean()/e.std(ddof=1)*np.sqrt(12); se = np.sqrt((1 + 0.5*sr**2)/n)
    p = 2*(1 - stats.norm.cdf(abs(sr/se)))
    return sr, p

def spanning_alpha(r, bench, lo, hi):
    r = r.loc[lo:hi].dropna(); rfc = rf_mon.reindex(r.index, method='ffill').fillna(0)
    y = r - rfc; f = (bench.loc[lo:hi].reindex(y.index) - rfc)
    df = pd.concat([y.rename('y'), f.rename('x')], axis=1).dropna()
    m = sm.OLS(df['y'].values, sm.add_constant(df['x'].values)).fit(cov_type='HAC', cov_kwds={'maxlags': C.HAC})
    return float(m.params[0])*12, float(m.pvalues[0]), float(m.params[1])
