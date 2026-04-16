# DATA README
> Instrucciones para poblar la carpeta data/ antes de ejecutar el backtest.

---

## Estructura requerida

```
data/
├── prices/                             ← datos de entrada
│   ├── etf_adjclose_2008_2025.csv      ← REQUERIDO — precios diarios ajustados
│   ├── momentum_train_2008_2019.csv    ← REQUERIDO — momentum 13612U (train)
│   ├── momentum_completo_2008_2025.csv ← REQUERIDO — momentum 13612U (completo)
│   └── monthly_returns_completo.csv    ← OPCIONAL — retornos mensuales precomputados
└── outputs/                            ← generado automáticamente por los scripts
    ├── s36_equity_curve.csv
    ├── s36_monthly_returns.csv
    ├── s36_allocation_log.csv
    ├── s36_summary_report.txt
    ├── s36_crisis_report.txt
    ├── s36_regime_report.txt
    └── s36_regime_detail.csv
```

---

## Cómo obtener los archivos de precios

Los archivos fuente están en `../research/phase_1/01_config/data/`.
Copiar y renombrar:

| Fuente | Destino |
|---|---|
| `../research/phase_1/01_config/data/completo/optimum3_refinitiv_adjclose.csv` | `prices/etf_adjclose_2008_2025.csv` |
| `../research/phase_1/01_config/data/train/momentum_multi_horizon.csv` | `prices/momentum_train_2008_2019.csv` |
| `../research/phase_1/01_config/data/completo/momentum_multi_horizon.csv` | `prices/momentum_completo_2008_2025.csv` |
| `../research/phase_1/01_config/data/completo/monthly_returns.csv` | `prices/monthly_returns_completo.csv` |

---

## Formato de `etf_adjclose_2008_2025.csv`

```
Date,SPY,QQQ,VGK,EWJ,SCZ,EEM,VNQ,REM,GLD,IEF,TLT,TIP,DBC,BWX,RWX,BIL
2007-01-03,142.87,43.45,...
...
2025-12-31,...
```

- Index: `Date` (YYYY-MM-DD)
- 16 columnas: 15 ETFs riesgosos + BIL
- Fuente: Refinitiv Eikon, adjusted close
- Período: desde 2007 (warmup para momentum de enero 2008) hasta 2025-12

---

## Formato de `momentum_train_2008_2019.csv` y `momentum_completo_2008_2025.csv`

```
Date,SPY_13612U,QQQ_13612U,VGK_13612U,...
2008-01-31,0.0523,0.0712,...
```

- Index: `Date` en fin de mes
- Columnas: `{ETF}_13612U` para cada uno de los 15 ETFs riesgosos
- Valores: momentum score = (R1m + R3m + R6m + R12m) / 4

---

## Verificación rápida

Después de poblar `prices/`, ejecutar:

```bash
python code/s36_backtest.py
```

El script imprime un bloque de verificación al final:

```
VERIFICATION CHECK
  ✅  TRAIN CAGR   expected 10.88  got 10.88
  ✅  TEST CAGR    expected 12.05  got 12.05
  ✅  FULL CAGR    expected 11.27  got 11.27
  ✅  TRAIN MaxDD  expected -13.87 got -13.87
  ✅  CRASH TRAIN  expected 12     got 12
  ✅  CRASH TEST   expected 9      got 9
```

Si algún check falla, revisar que los archivos CSV sean los correctos.

---

## Nota sobre Refinitiv

Los datos originales se descargaron con Refinitiv Eikon (requires Desktop abierto).
Si necesitas regenerar los precios desde cero:
- Ejecutar `../research/phase_1/01_config/update_refinitiv_data.py`
- Requiere `refinitiv-data` instalado y Refinitiv Desktop activo

Para uso del paper, los CSVs ya generados son suficientes.
