# -*- coding: utf-8 -*-
"""
config.py — FUENTE ÚNICA del split y parámetros del rebuild (metodología Marc).
================================================================================
Protocolo anidado 60/20/20:
  TRAIN  -> se derivan/optimizan TODAS las reglas (grid scans).
  VAL    -> se valida/selecciona; confirma que la elección de train sobrevive OOS.
  TEST   -> se evalúa UNA sola vez al final (cierre confirmatorio). NO se mira antes.

Todo script del rebuild importa de aquí. NO hardcodear fechas en ningún otro sitio.
Ventana viva = 2004-02 a 2025-12 (263 meses; 2003 es warmup de momentum 12m).
"""
import os
from pathlib import Path

# --- Universo ---
RISKY = ['SPY','QQQ','VGK','EWJ','SCZ','EEM','VNQ','REM','GLD','IEF','TLT','TIP','DBC','BWX','RWX']
CASH  = 'BIL'

# --- Parámetros GAT (los que el protocolo re-deriva en TRAIN; valores iniciales = referencia) ---
TOP_N = 7        # R2  (a re-derivar/validar)
THETA = 0.02     # R3  (a re-derivar/validar)
K     = 3        # R4  (a re-derivar/validar)
# R1 = señal 13612U. Crash filter (R5) ELIMINADO en v2.

# --- SPLIT ~54/23/23 (calendario limpio; test largo para recuperar potencia) ---
TRAIN = ('2004-02-01', '2015-12-31')   # 143 meses (54.4%)
VAL   = ('2016-01-01', '2020-12-31')   #  60 meses (22.8%)
TEST  = ('2021-01-01', '2025-12-31')   #  60 meses (22.8%)

# Ventanas SECUNDARIAS (solo robustez/soporte; NO son el claim inferencial primario).
# El claim primario del paper de Marc cierra en TEST. FULL/VALTEST se reportan como
# corroboración rica en potencia, declarando que incluyen datos vistos en desarrollo.
VALTEST = ('2016-01-01', '2025-12-31')  # 120 meses — soporte OOS-amplio
FULL    = ('2004-02-01', '2025-12-31')  # 263 meses — incluye train (in-sample)

PERIODS = {'TRAIN': TRAIN, 'VAL': VAL, 'TEST': TEST, 'VALTEST': VALTEST, 'FULL': FULL}

# --- Constantes estadísticas (idénticas al motor canónico verificado) ---
FRED  = os.environ.get("FRED_API_KEY", "")   # TB3MS (rf); set FRED_API_KEY (free key from fredaccount.stlouisfed.org). If empty, rf falls back to 0.
BLOCK = 6        # bootstrap de bloque circular
Bn    = 10000
SEED  = 42
HAC   = 6        # Newey-West maxlags

# --- Rutas ---
BASE = Path(__file__).resolve().parent.parent
D    = BASE / 'data' / 'prices'
OUT  = BASE / 'data' / 'outputs'
