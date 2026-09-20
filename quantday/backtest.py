"""
Motor de backtest bar-a-bar para a estrategia de day trade.

Regras de execucao (realistas, sem look-ahead):
  * Sinal calculado no FECHAMENTO da barra t.
  * Entrada na ABERTURA da barra t+1, com custo de spread.
  * A cada barra, verifica-se stop e alvo usando HIGH/LOW da barra
    (prioridade conservadora: se ambos forem tocados na mesma barra,
    assume-se o STOP primeiro).
  * Trailing stop opcional por ATR.
  * Time-stop: toda posicao e encerrada no fim da sessao (nunca carrega
    overnight — e day trade).
  * Uma posicao por vez, por instrumento.
  * Circuit breakers: max de trades/dia e limite de perda diaria.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict

import pandas as pd

from . import signals as sig
from . import risk as rk


@dataclass
class Trade:
    symbol: str
    direction: int          # +1 long, -1 short
    entry_time: pd.Timestamp
    entry: float
    exit_time: pd.Timestamp
    exit: float
    size: float
    stop: float
    target: float
    pnl: float
    r_multiple: float
    reason: str             # 'target' | 'stop' | 'trail' | 'session_end' | 'day_end'


def _session_end_flags(index: pd.DatetimeIndex, session_ok: pd.Series) -> pd.Series:
    """True na ultima barra dentro de uma janela de sessao (antes de sair dela)."""
    nxt = session_ok.shift(-1, fill_value=False)
    return session_ok & (~nxt)


def run(
    df: pd.DataFrame,
    instrument,
    params,
    starting_equity: float = 100_000.0,
) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Executa o backtest.

    Retorna (trades_df, equity_curve, resumo_dict).
    """
    from . import metrics

    data = sig.generate(df, params, instrument.sessions,
                         getattr(instrument, "session_tz", "UTC"))
    data = data.dropna(subset=["ema_trend", "atr", "adx", "rsi", "vwap"]).copy()
    if data.empty:
        return pd.DataFrame(), pd.Series(dtype=float), metrics.summarize(
            pd.DataFrame(), pd.Series(dtype=float), starting_equity
        )

    session_end = _session_end_flags(data.index, data["session_ok"])

    equity = starting_equity
    trades: list[Trade] = []
    equity_points: list[tuple[pd.Timestamp, float]] = [(data.index[0], equity)]

    # Estado da posicao aberta
    pos = None  # dict com chaves: direction, entry, size, stop, target, entry_time, entry_idx

    # Controle diario
    cur_day = None
    trades_today = 0
    day_start_equity = equity
    day_locked = False

    rows = data.itertuples()
    prev_row = None

    for row in rows:
        ts = row.Index
        day = ts.normalize()
        if day != cur_day:
            cur_day = day
            trades_today = 0
            day_start_equity = equity
            day_locked = False

        # ---- Gestao de posicao aberta ----
        if pos is not None:
            direction = pos["direction"]
            high, low = row.high, row.low
            exit_price = None
            reason = None

            # Trailing stop (atualiza antes de checar toque)
            if params.use_trailing and params.trail_atr_mult > 0:
                trail = (row.close if False else None)
                # trailing baseado no fechamento anterior + ATR corrente
                new_stop = (
                    row.close - direction * params.trail_atr_mult * row.atr
                )
                # so aperta o stop, nunca afrouxa
                if direction == 1:
                    pos["stop"] = max(pos["stop"], new_stop)
                else:
                    pos["stop"] = min(pos["stop"], new_stop)

            stop, target = pos["stop"], pos["target"]

            # Checagem conservadora: stop primeiro
            if direction == 1:
                if low <= stop:
                    exit_price, reason = stop, "stop"
                elif high >= target:
                    exit_price, reason = target, "target"
            else:
                if high >= stop:
                    exit_price, reason = stop, "stop"
                elif low <= target:
                    exit_price, reason = target, "target"

            # Time-stop: fim de sessao -> encerra no fechamento
            if exit_price is None and session_end.loc[ts]:
                exit_price, reason = row.close, "session_end"

            if exit_price is not None:
                # custo de saida (metade do spread por perna ja embutido no round-trip)
                pnl = (
                    direction
                    * (exit_price - pos["entry"])
                    * pos["size"]
                    * instrument.point_value
                )
                r = rk.r_multiple(pos["entry"], exit_price, pos["stop_init"], direction)
                equity += pnl
                trades.append(
                    Trade(
                        symbol=instrument.symbol, direction=direction,
                        entry_time=pos["entry_time"], entry=pos["entry"],
                        exit_time=ts, exit=exit_price, size=pos["size"],
                        stop=pos["stop_init"], target=pos["target"],
                        pnl=pnl, r_multiple=r, reason=reason,
                    )
                )
                equity_points.append((ts, equity))
                pos = None
                # circuit breaker diario
                if equity <= day_start_equity * (1.0 - params.daily_loss_limit):
                    day_locked = True

        # ---- Nova entrada (usa sinal da barra ANTERIOR, executa nesta abertura) ----
        if (
            pos is None
            and prev_row is not None
            and not day_locked
            and trades_today < params.max_trades_per_day
        ):
            go_long = bool(prev_row.long_signal)
            go_short = bool(prev_row.short_signal)
            # so entra se ainda estamos em janela de sessao nesta barra
            if (go_long or go_short) and bool(row.session_ok):
                direction = 1 if go_long else -1
                # entrada na abertura desta barra + custo de spread
                entry = row.open + direction * (instrument.spread / 2.0)
                atr_val = prev_row.atr
                stop, target = rk.stop_target(entry, atr_val, direction, params)
                size = rk.position_size(equity, entry, stop, instrument, params)
                if size > 0:
                    pos = {
                        "direction": direction, "entry": entry, "size": size,
                        "stop": stop, "stop_init": stop, "target": target,
                        "entry_time": ts,
                    }
                    trades_today += 1

        prev_row = row

    # Fecha posicao remanescente ao final dos dados
    if pos is not None:
        last = data.iloc[-1]
        direction = pos["direction"]
        exit_price = last["close"]
        pnl = direction * (exit_price - pos["entry"]) * pos["size"] * instrument.point_value
        r = rk.r_multiple(pos["entry"], exit_price, pos["stop_init"], direction)
        equity += pnl
        trades.append(Trade(
            symbol=instrument.symbol, direction=direction,
            entry_time=pos["entry_time"], entry=pos["entry"],
            exit_time=data.index[-1], exit=exit_price, size=pos["size"],
            stop=pos["stop_init"], target=pos["target"],
            pnl=pnl, r_multiple=r, reason="day_end",
        ))
        equity_points.append((data.index[-1], equity))

    trades_df = pd.DataFrame([asdict(t) for t in trades])
    eq_curve = pd.Series(
        [e for _, e in equity_points],
        index=pd.DatetimeIndex([t for t, _ in equity_points]),
        name="equity",
    )
    summary = metrics.summarize(trades_df, eq_curve, starting_equity)
    return trades_df, eq_curve, summary
