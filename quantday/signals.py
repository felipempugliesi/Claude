"""
Logica de sinais da estrategia "Tendencia + Pullback".

Racional quantitativo
---------------------
1. REGIME (filtro de tendencia): so operamos a favor de uma tendencia
   estabelecida. Definimos tendencia de alta quando
   ema_fast > ema_slow > ema_trend E ADX > adx_min. (Simetrico para baixa.)
   Isso evita operar em mercado lateral, onde pullback-trading tem baixa
   expectativa.

2. GATILHO (pullback de momentum): dentro da tendencia, esperamos o preco
   perder forca (RSI recua abaixo de `rsi_pullback`) e entao retomar
   (RSI cruza acima de `rsi_trigger`). Compramos a retomada — "buy the dip"
   em tendencia de alta. Adicionamos confirmacao de que o preco esta do lado
   correto do VWAP da sessao (vies intradiario).

3. FILTRO DE VOLATILIDADE: exigimos ATR% dentro de uma faixa saudavel
   (nem parado demais, nem em panico). Isso melhora a razao sinal/ruido e
   estabiliza o dimensionamento por ATR.

4. FILTRO DE SESSAO: so entramos nas janelas de maior liquidez do instrumento.

Os sinais sao calculados no FECHAMENTO de cada barra; a execucao ocorre na
ABERTURA da barra seguinte (ver backtest.py) — sem look-ahead.
"""
from __future__ import annotations

import pandas as pd

from . import indicators as ind


def _in_sessions(index: pd.DatetimeIndex, sessions) -> pd.Series:
    """Mascara booleana: True quando o horario UTC cai em alguma sessao."""
    if not sessions:
        return pd.Series(True, index=index)
    minutes = index.hour * 60 + index.minute
    mask = pd.Series(False, index=index)
    for s in sessions:
        sh, sm = map(int, s.start.split(":"))
        eh, em = map(int, s.end.split(":"))
        start = sh * 60 + sm
        end = eh * 60 + em
        mask |= (minutes >= start) & (minutes < end)
    return mask


def generate(df: pd.DataFrame, params, sessions=()) -> pd.DataFrame:
    """Recebe OHLCV, devolve o mesmo DataFrame com indicadores + colunas de sinal.

    Colunas adicionadas:
        long_signal, short_signal : bool (entrada na proxima abertura)
        regime : +1 alta, -1 baixa, 0 sem tendencia
        session_ok, vol_ok : filtros
    """
    data = ind.compute_all(df, params)

    ema_f, ema_s, ema_t = data["ema_fast"], data["ema_slow"], data["ema_trend"]
    rsi = data["rsi"]
    adx = data["adx"]
    vwap = data["vwap"]
    close = data["close"]

    # --- Regime ---
    # A tendencia e definida pela estrutura de MEDIO/LONGO prazo (ema_slow vs
    # ema_trend + preco do lado certo do ema_trend), com ADX confirmando forca.
    # A ema_fast NAO entra no regime de proposito: e ela quem recua no pullback
    # que a estrategia procura para entrar. Desacoplar regime (tendencia) de
    # gatilho (pullback) evita perder o sinal justamente quando ele acontece.
    trending = adx > params.adx_min
    up = (ema_s > ema_t) & (close > ema_t) & trending
    down = (ema_s < ema_t) & (close < ema_t) & trending
    regime = pd.Series(0, index=data.index)
    regime = regime.mask(up, 1).mask(down, -1)
    data["regime"] = regime

    # --- Filtro de volatilidade ---
    vol_ok = (data["atr_pct"] >= params.atr_min_pct) & (
        data["atr_pct"] <= params.atr_max_pct
    )
    data["vol_ok"] = vol_ok

    # --- Filtro de sessao ---
    session_ok = _in_sessions(data.index, sessions)
    data["session_ok"] = session_ok

    # --- Gatilho de pullback (momentum) ---
    # Houve recuo recente do RSI abaixo de `rsi_pullback` dentro do lookback?
    recent_pullback_dn = (
        (rsi < params.rsi_pullback)
        .rolling(params.pullback_lookback, min_periods=1)
        .max()
        .astype(bool)
    )
    recent_pullback_up = (
        (rsi > (100.0 - params.rsi_pullback))
        .rolling(params.pullback_lookback, min_periods=1)
        .max()
        .astype(bool)
    )

    trig_long = ind.cross_above(rsi, params.rsi_trigger)
    trig_short = ind.cross_below(rsi, 100.0 - params.rsi_trigger)

    long_signal = (
        (regime == 1)
        & recent_pullback_dn
        & trig_long
        & (close > vwap)
        & vol_ok
        & session_ok
    )

    short_signal = (
        (regime == -1)
        & recent_pullback_up
        & trig_short
        & (close < vwap)
        & vol_ok
        & session_ok
    )
    if not params.allow_shorts:
        short_signal = short_signal & False

    data["long_signal"] = long_signal.fillna(False)
    data["short_signal"] = short_signal.fillna(False)
    return data
