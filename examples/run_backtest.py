#!/usr/bin/env python3
"""
Demonstracao: roda o backtest da estrategia Tendencia+Pullback em dados
sinteticos para um instrumento de forex (EURUSD) e um de NASDAQ (NQ/QQQ).

Uso:
    python examples/run_backtest.py
    python examples/run_backtest.py --symbol NQ --days 180
    python examples/run_backtest.py --csv caminho/para/dados.csv --symbol EURUSD

Para dados reais, passe um CSV com colunas: timestamp,open,high,low,close,volume
(timestamps em UTC).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# permite rodar sem instalar o pacote
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quantday import config, data as datamod, backtest, metrics  # noqa: E402


def build_data(symbol: str, args) -> "pd.DataFrame":  # type: ignore # noqa
    inst = config.INSTRUMENTS[symbol]
    if args.csv:
        return datamod.load_csv(args.csv)

    # seed distinto e DETERMINISTICO por simbolo (nao usa hash() do Python,
    # que e randomizado entre execucoes) -> series diferentes e reproduziveis.
    seed = args.seed + sum(ord(c) for c in symbol)

    # parametros do gerador conforme a classe do ativo
    if inst.asset_class == "forex":
        # sessao overlap Londres/NY; preco ~1.08 (EURUSD) / ~1.27 (GBPUSD)
        base = 1.08 if symbol == "EURUSD" else 1.27
        return datamod.synthetic_intraday(
            days=args.days, freq_min=5, base_price=base,
            ann_vol=0.08, session_start="12:00", session_end="16:00",
            seed=seed,
        )
    else:
        # NASDAQ RTH; preco ~18000 (NQ/MNQ) ou ~450 (QQQ)
        base = 18000.0 if symbol in ("NQ", "MNQ") else 450.0
        return datamod.synthetic_intraday(
            days=args.days, freq_min=5, base_price=base,
            ann_vol=0.22, session_start="13:30", session_end="20:00",
            seed=seed,
        )


def run_symbol(symbol: str, args) -> dict:
    inst = config.INSTRUMENTS[symbol]
    params = config.params_for(inst)
    df = build_data(symbol, args)
    trades, equity, summary = backtest.run(
        df, inst, params, starting_equity=args.equity
    )

    print(f"\n=== {symbol}  ({inst.asset_class}) ===")
    print(f"  Periodo ............ {df.index[0]}  ->  {df.index[-1]}")
    print(f"  Barras ............. {len(df)}")
    print(metrics.format_summary(summary))
    if not trades.empty:
        by_reason = trades["reason"].value_counts().to_dict()
        print(f"  Saidas por motivo .. {by_reason}")
    return summary


def main():
    ap = argparse.ArgumentParser(description="Backtest day trade forex/NASDAQ")
    ap.add_argument("--symbol", default=None,
                    help="EURUSD | GBPUSD | NQ | QQQ (default: roda uma cesta)")
    ap.add_argument("--csv", default=None, help="CSV OHLCV em UTC")
    ap.add_argument("--days", type=int, default=150)
    ap.add_argument("--equity", type=float, default=100_000.0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    symbols = [args.symbol] if args.symbol else ["EURUSD", "GBPUSD", "MNQ", "QQQ"]
    print("Backtest — estrategia Tendencia+Pullback (day trade)")
    print(f"Capital inicial: {args.equity:,.2f}  |  dias: {args.days}")
    for sym in symbols:
        if sym not in config.INSTRUMENTS:
            print(f"  [ignorado] simbolo desconhecido: {sym}")
            continue
        run_symbol(sym, args)


if __name__ == "__main__":
    main()
