#!/usr/bin/env python3
"""
Backtest da estrategia em DADOS REAIS do Webull (salvos em data/*.csv).

Os CSVs foram gerados a partir das barras do Webull (endpoint get_stock_bars)
e normalizados por quantday.webull. Como a conta so tem market data de
acoes/ETFs (futuros exigem assinatura separada), usamos:
    - NASDAQ  -> QQQ  (ETF Nasdaq-100)
    - "forex" -> FXE (~EUR/USD) e FXB (~GBP/USD), ETFs de moeda (proxy, RTH-only)

Uso:
    python examples/run_webull.py
    python examples/run_webull.py --symbol QQQ

Para atualizar/estender os dados com suas credenciais, use quantday.webull:
    from quantday.webull import WebullMDataClient
    cli = WebullMDataClient()                      # WEBULL_APP_KEY / _SECRET
    df = cli.get_bars("QQQ", "US_ETF", "M5", 3000)
    WebullMDataClient.to_csv(df, "data/QQQ_M5.csv")
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from quantday import config, data as datamod, backtest, metrics  # noqa: E402

DATA_DIR = ROOT / "data"
DEFAULT_SYMBOLS = ["QQQ", "FXE", "FXB"]


def run_symbol(symbol: str, equity: float) -> None:
    inst = config.INSTRUMENTS[symbol]
    params = config.params_for(inst)
    csv_path = DATA_DIR / f"{symbol}_M5.csv"
    if not csv_path.exists():
        print(f"  [pulado] {symbol}: {csv_path} nao encontrado")
        return
    df = datamod.load_csv(str(csv_path))
    trades, eq, summary = backtest.run(df, inst, params, starting_equity=equity)

    label = {"QQQ": "NASDAQ-100 ETF", "FXE": "~EUR/USD (ETF)",
             "FXB": "~GBP/USD (ETF)"}.get(symbol, inst.asset_class)
    days = df.index.normalize().nunique()
    print(f"\n=== {symbol}  ({label}) — DADOS REAIS WEBULL ===")
    print(f"  Periodo ............ {df.index[0]} -> {df.index[-1]}  ({days} pregoes)")
    print(f"  Barras ............. {len(df)}")
    print(metrics.format_summary(summary))
    if not trades.empty:
        print(f"  Saidas por motivo .. {trades['reason'].value_counts().to_dict()}")


def main():
    ap = argparse.ArgumentParser(description="Backtest em dados reais do Webull")
    ap.add_argument("--symbol", default=None, help="QQQ | FXE | FXB")
    ap.add_argument("--equity", type=float, default=100_000.0)
    args = ap.parse_args()

    print("Backtest — Tendencia+Pullback em DADOS REAIS do Webull (M5, RTH)")
    print(f"Capital inicial: {args.equity:,.2f}")
    symbols = [args.symbol] if args.symbol else DEFAULT_SYMBOLS
    for sym in symbols:
        if sym not in config.INSTRUMENTS:
            print(f"  [ignorado] simbolo desconhecido: {sym}")
            continue
        run_symbol(sym, args.equity)


if __name__ == "__main__":
    main()
