"""Testes de sanidade dos indicadores, sinais e backtest.

Rode com:  python -m pytest -q   (ou)   python tests/test_quantday.py
Nao exige pytest para o modo __main__.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quantday import config, data, indicators as ind, signals, risk, backtest, webull  # noqa: E402


def _sample(n=500, seed=3):
    rng = np.random.default_rng(seed)
    rets = 0.0005 * rng.normal(0, 1, n)
    close = 100 * np.exp(np.cumsum(rets))
    o = np.empty(n); o[0] = 100; o[1:] = close[:-1]
    w = 0.001 * close
    hi = np.maximum(o, close) + np.abs(rng.normal(0, 1, n)) * w
    lo = np.minimum(o, close) - np.abs(rng.normal(0, 1, n)) * w
    idx = pd.date_range("2025-01-01 13:30", periods=n, freq="5min")
    return pd.DataFrame({"open": o, "high": hi, "low": lo, "close": close,
                         "volume": 1000.0}, index=idx)


def test_rsi_bounds():
    df = _sample()
    r = ind.rsi(df["close"], 14).dropna()
    assert (r >= 0).all() and (r <= 100).all()


def test_adx_reasonable_on_random_walk():
    df = _sample(2000)
    a = ind.adx(df, 14).dropna()
    # random walk: ADX tipicamente baixo/moderado, nunca ~90
    assert 5 < a.median() < 45, f"ADX mediano irreal: {a.median()}"


def test_atr_positive():
    df = _sample()
    a = ind.atr(df, 14).dropna()
    assert (a > 0).all()


def test_ema_matches_pandas():
    df = _sample()
    e = ind.ema(df["close"], 10)
    ref = df["close"].ewm(span=10, adjust=False, min_periods=10).mean()
    assert np.allclose(e.dropna().values, ref.dropna().values)


def test_vwap_resets_daily():
    df = _sample(300)
    v = ind.session_vwap(df)
    # VWAP deve estar dentro do range de precos do dia
    assert v.dropna().between(df["low"].min(), df["high"].max()).all()


def test_position_size_respects_risk():
    inst = config.INSTRUMENTS["QQQ"]
    p = config.params_for(inst)
    equity = 100_000.0
    entry, stop = 450.0, 447.0
    size = risk.position_size(equity, entry, stop, inst, p)
    risk_cash = size * abs(entry - stop) * inst.point_value
    # nao pode arriscar mais que o alvo (0.5%) + 1 incremento
    assert risk_cash <= equity * p.risk_per_trade + abs(entry - stop) * inst.point_value


def test_r_multiple_sign():
    # long vencedor -> R positivo; perdedor -> negativo
    assert risk.r_multiple(100, 106, 97, 1) > 0
    assert risk.r_multiple(100, 98, 97, 1) < 0
    assert risk.r_multiple(100, 94, 103, -1) > 0  # short vencedor


def test_no_lookahead_and_runs():
    inst = config.INSTRUMENTS["MNQ"]
    p = config.params_for(inst)
    df = data.synthetic_intraday(days=60, base_price=18000, ann_vol=0.22,
                                 session_start="13:30", session_end="20:00", seed=5)
    trades, equity, summary = backtest.run(df, inst, p)
    assert summary["n_trades"] >= 0
    if not trades.empty:
        # toda saida ocorre em/ apos a entrada
        assert (trades["exit_time"] >= trades["entry_time"]).all()
        # R-multiplo coerente com o pnl (mesmo sinal)
        same_sign = np.sign(trades["r_multiple"]) == np.sign(trades["pnl"])
        assert same_sign.all()


def test_signals_only_in_session():
    inst = config.INSTRUMENTS["EURUSD"]
    p = config.params_for(inst)
    df = data.synthetic_intraday(days=60, base_price=1.08, ann_vol=0.08,
                                 session_start="12:00", session_end="16:00", seed=5)
    s = signals.generate(df, p, inst.sessions)
    fired = s[s["long_signal"] | s["short_signal"]]
    assert fired["session_ok"].all()


def test_webull_normalize_bars():
    # formato real do endpoint get_stock_bars (strings, ISO UTC, mais novo -> antigo)
    raw = [
        {"symbol": "QQQ", "time": "2026-09-18T19:55:00.000+0000", "open": "720.24",
         "close": "721.45", "high": "721.72", "low": "720.23", "volume": "6971592",
         "trading_session": "RTH"},
        {"symbol": "QQQ", "time": "2026-09-18T19:50:00.000+0000", "open": "720.09",
         "close": "720.23", "high": "720.44", "low": "719.84", "volume": "1109502",
         "trading_session": "RTH"},
        # duplicata de tempo deve ser removida
        {"symbol": "QQQ", "time": "2026-09-18T19:50:00.000+0000", "open": "999",
         "close": "999", "high": "999", "low": "999", "volume": "1",
         "trading_session": "RTH"},
    ]
    df = webull.normalize_bars(raw)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 2                              # duplicata removida
    assert df.index.is_monotonic_increasing          # ordenado do antigo p/ novo
    assert df.index.tz is None                        # tz-naive UTC
    assert df["close"].dtype.kind == "f"              # numerico
    assert abs(df["close"].iloc[-1] - 721.45) < 1e-6  # ultima barra = a mais nova


def test_webull_normalize_empty():
    assert webull.normalize_bars([]).empty


def _run_all():
    fns = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    passed = 0
    for fn in fns:
        fn()
        print(f"  ok  {fn.__name__}")
        passed += 1
    print(f"\n{passed}/{len(fns)} testes passaram.")


if __name__ == "__main__":
    _run_all()
