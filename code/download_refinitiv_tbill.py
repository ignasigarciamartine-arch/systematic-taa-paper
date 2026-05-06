# -*- coding: utf-8 -*-
"""
Download a monthly 3-month US Treasury Bill risk-free series from Refinitiv.

Output:
  paper/data/prices/tbill_3m_monthly_refinitiv.csv

The CSV stores the annual yield in percent and the converted monthly
risk-free return used for Sharpe/Sortino calculations:
  rf_monthly = (1 + annual_yield_pct / 100) ** (1/12) - 1
"""

from pathlib import Path

import pandas as pd


def patch_httpx_proxy_if_needed() -> None:
    """Refinitiv Data 1.6.x can pass an httpx proxy dict to httpx >= 0.26."""
    try:
        import httpx
        import refinitiv.data._core.session.http_service as http_service
    except Exception:
        return

    def normalize_proxy(proxies):
        if not proxies:
            return None
        if isinstance(proxies, dict):
            values = [value for value in proxies.values() if value]
            return values[0] if values else None
        return proxies

    def get_httpx_client(proxies, **kwargs):
        proxy = normalize_proxy(proxies)
        if proxy is None:
            return httpx.Client(**kwargs)
        return httpx.Client(proxy=proxy, **kwargs)

    def get_httpx_client_async(proxies, **kwargs):
        proxy = normalize_proxy(proxies)
        if proxy is None:
            return httpx.AsyncClient(**kwargs)
        return httpx.AsyncClient(proxy=proxy, **kwargs)

    http_service.get_httpx_client = get_httpx_client
    http_service.get_httpx_client_async = get_httpx_client_async


def main() -> int:
    import refinitiv.data as rd

    patch_httpx_proxy_if_needed()

    paper_dir = Path(__file__).resolve().parents[1]
    out_path = paper_dir / "data" / "prices" / "tbill_3m_monthly_refinitiv.csv"

    candidates = [
        ("US3MFRB=RR", ["TRDPRC_1", "VALUE", "CLOSE", "CF_LAST", "TR.PriceClose"]),
        ("aUSTRB3AV", ["VALUE", "TRDPRC_1", "CLOSE", "CF_LAST", "TR.PriceClose"]),
        ("US3MT=RR", ["VALUE", "CLOSE", "TR.PriceClose", "CF_LAST"]),
        ("US3MT=RRPS", ["VALUE", "CLOSE", "TR.PriceClose", "CF_LAST"]),
        ("USBMK3M=", ["VALUE", "CLOSE", "TRDPRC_1", "TR.PriceClose", "CF_LAST"]),
        ("USTREASURY3M=", ["VALUE", "CLOSE", "TR.PriceClose", "CF_LAST"]),
        ("FDFD=", ["VALUE", "CLOSE", "TR.PriceClose", "CF_LAST"]),
    ]

    print("Opening Refinitiv session...")
    rd.open_session()
    try:
        for ric, fields in candidates:
            for field in fields:
                try:
                    print(f"Trying {ric} / {field}...")
                    df = rd.get_history(
                        universe=ric,
                        fields=[field],
                        start="2007-01-01",
                        end="2025-12-31",
                        interval="1M",
                    )
                    if df is None or df.empty:
                        print("  empty")
                        continue

                    series = df[field].dropna() if field in df.columns else df.iloc[:, 0].dropna()
                    series.index = pd.to_datetime(series.index).to_period("M").to_timestamp("M")
                    series = pd.to_numeric(series, errors="coerce").dropna()

                    print(
                        f"  rows={len(series)}, "
                        f"range={series.index.min().date()} to {series.index.max().date()}"
                    )
                    if len(series) < 120:
                        continue

                    monthly_rf = (1 + series / 100.0) ** (1 / 12.0) - 1
                    out = pd.DataFrame(
                        {
                            "date": monthly_rf.index,
                            "annual_yield_pct": series.values,
                            "rf_monthly": monthly_rf.values,
                            "source_ric": ric,
                            "source_field": field,
                        }
                    )
                    out.to_csv(out_path, index=False)
                    print(f"Saved {len(out)} rows to {out_path}")
                    print(out.head(3).to_string(index=False))
                    print(out.tail(3).to_string(index=False))
                    return 0
                except Exception as exc:
                    print(f"  failed: {str(exc)[:220]}")

        print("No Refinitiv candidate produced a valid monthly T-bill series.")
        return 1
    finally:
        try:
            rd.close_session()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
