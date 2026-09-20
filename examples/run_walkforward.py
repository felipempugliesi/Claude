#!/usr/bin/env python3
"""
Walk-forward analysis em dados reais do Webull.

Otimiza parametros numa janela de treino (in-sample) e testa na janela
seguinte (out-of-sample), deslizando por todo o historico. O resultado
reportado e a curva OOS concatenada — a estimativa honesta de desempenho.

Uso:
    python examples/run_walkforward.py                 # QQQ (default)
    python examples/run_walkforward.py --symbol FXE
    python examples/run_walkforward.py --symbol QQQ --is-days 180 --oos-days 45

Quando houver assinatura de US_FUTURES, troque o simbolo por MNQ / M6E / M6B
(mesmo comando) apos puxar as barras com quantday.webull.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from quantday import config, data as datamod, walkforward, metrics  # noqa: E402

DATA_DIR = ROOT / "data"


def main():
    ap = argparse.ArgumentParser(description="Walk-forward em dados reais Webull")
    ap.add_argument("--symbol", default="QQQ", help="QQQ | FXE | FXB (com dados em data/)")
    ap.add_argument("--is-days", type=int, default=180, help="pregoes in-sample (treino)")
    ap.add_argument("--oos-days", type=int, default=45, help="pregoes out-of-sample (teste)")
    ap.add_argument("--equity", type=float, default=100_000.0)
    args = ap.parse_args()

    inst = config.INSTRUMENTS[args.symbol]
    base = config.params_for(inst)
    csv = DATA_DIR / f"{args.symbol}_M5.csv"
    if not csv.exists():
        print(f"Sem dados: {csv}")
        return
    df = datamod.load_csv(str(csv))

    print(f"Walk-forward — {args.symbol} ({inst.asset_class})")
    print(f"Historico: {df.index[0].date()} -> {df.index[-1].date()} "
          f"({df.index.normalize().nunique()} pregoes)")
    print(f"Janela: {args.is_days}d treino (IS) / {args.oos_days}d teste (OOS), rolante\n")

    res = walkforward.run(df, inst, base, is_days=args.is_days,
                          oos_days=args.oos_days, starting_equity=args.equity)

    print(f"{'fold':>4} {'OOS periodo':>25} {'params (adx/stop/tgt)':>24} "
          f"{'IS ret':>8} {'OOS ret':>8} {'OOS PF':>7} {'trades':>7}")
    for f in res["folds"]:
        p = f["params"]
        pstr = f"{p['adx_min']:.0f}/{p['stop_atr_mult']:.1f}/{p['target_atr_mult']:.1f}"
        oos = f["oos_period"]
        print(f"{f['fold']:>4} {str(oos[0])+'..'+str(oos[1]):>25} {pstr:>24} "
              f"{f['is_return']*100:>7.1f}% {f['oos_return']*100:>7.1f}% "
              f"{f['oos_pf']:>7.2f} {f['oos_trades']:>7}")

    s = res["oos_summary"]
    print("\n=== RESULTADO OUT-OF-SAMPLE CONCATENADO (honesto) ===")
    print(metrics.format_summary(s))
    print(f"  Folds .............. {res['n_folds']}")
    print(f"  WF efficiency ...... {res['wf_efficiency']:.2f}  "
          f"(mediana OOS/IS; >~0.5 e saudavel)")


if __name__ == "__main__":
    main()
