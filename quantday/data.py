"""
Carregamento de dados OHLCV e gerador de dados sinteticos.

- load_csv: le um CSV com colunas [timestamp, open, high, low, close, volume].
- synthetic_intraday: gera barras intradiarias realistas (tendencia + ruido +
  clusterizacao de volatilidade / GARCH-like) para o backtest rodar sem
  depender de fonte externa.

Para dados reais, use a fonte que preferir (broker, Webull, Dukascopy,
Polygon, etc.) e salve como CSV no formato acima, ou adapte load_csv.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_COLS = ["open", "high", "low", "close", "volume"]


def load_csv(path: str, tz: str = "UTC") -> pd.DataFrame:
    """Le OHLCV de CSV. Precisa de uma coluna de tempo (timestamp/datetime/date)."""
    df = pd.read_csv(path)
    time_col = next(
        (c for c in df.columns if c.lower() in ("timestamp", "datetime", "date", "time")),
        None,
    )
    if time_col is None:
        raise ValueError("CSV precisa de uma coluna de tempo (timestamp/datetime/date).")
    idx = pd.to_datetime(df[time_col], utc=True)
    df = df.drop(columns=[time_col])
    df.columns = [c.lower() for c in df.columns]
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas ausentes no CSV: {missing}")
    df.index = idx.dt.tz_convert(tz).dt.tz_localize(None)
    df.index.name = "timestamp"
    return df[REQUIRED_COLS].sort_index()


def synthetic_intraday(
    days: int = 120,
    freq_min: int = 5,
    start: str = "2025-01-01",
    base_price: float = 100.0,
    ann_drift: float = 0.05,
    ann_vol: float = 0.20,
    seed: int = 7,
    session_start: str = "13:30",
    session_end: str = "20:00",
    vol_clustering: float = 0.85,
    momentum: float = 0.18,
    wick: float = 0.25,
) -> pd.DataFrame:
    """Gera OHLCV intradiario sintetico realista.

    Modelo dos log-retornos:
        r[t] = mu + momentum * r[t-1] + trend_do_dia + sigma[t] * eps[t]
    - `momentum` (AR(1) nos retornos) cria tendencias intradiarias persistentes,
      que e o que a estrategia busca; valores tipicos 0.1-0.25.
    - `sigma[t]` segue um AR(1) em log (proxy de GARCH) -> clusterizacao de vol.
    - `wick` controla o tamanho das sombras intrabarra (fracao do range do corpo);
      valores pequenos mantem ADX/RSI em faixas realistas.
    """
    rng = np.random.default_rng(seed)

    # constroi o index de barras dentro da sessao, em dias uteis
    sh, sm = map(int, session_start.split(":"))
    eh, em = map(int, session_end.split(":"))
    session_minutes = (eh * 60 + em) - (sh * 60 + sm)
    bars_per_day = session_minutes // freq_min

    all_index = []
    day = pd.Timestamp(start)
    collected = 0
    while collected < days:
        if day.weekday() < 5:  # seg-sex
            t0 = day + pd.Timedelta(hours=sh, minutes=sm)
            idx = pd.date_range(t0, periods=bars_per_day, freq=f"{freq_min}min")
            all_index.append(idx)
            collected += 1
        day += pd.Timedelta(days=1)
    index = pd.DatetimeIndex(np.concatenate([i.values for i in all_index]))

    n = len(index)
    bars_per_year = 252 * bars_per_day
    mu = ann_drift / bars_per_year
    base_sigma = ann_vol / np.sqrt(bars_per_year)

    # volatilidade com clusterizacao (AR(1) em log-vol)
    log_sig = np.zeros(n)
    log_sig[0] = np.log(base_sigma)
    shocks = rng.normal(0, 0.20, n)
    mean_log = np.log(base_sigma)
    for i in range(1, n):
        log_sig[i] = mean_log + vol_clustering * (log_sig[i - 1] - mean_log) + shocks[i]
    sigma = np.exp(log_sig)

    # leve vies direcional por dia (regime), pequeno o bastante para nao
    # gerar tendencias monotonicas; as tendencias intradiarias reais vem do
    # termo de momentum AR(1) abaixo.
    day_ids = pd.Series(index).dt.normalize().factorize()[0]
    day_trend = rng.normal(0, base_sigma * 0.15, day_ids.max() + 1)
    trend_component = day_trend[day_ids]

    # log-retornos com momentum AR(1) -> tendencias intradiarias
    eps = sigma * rng.normal(0, 1, n)
    rets = np.zeros(n)
    rets[0] = mu + trend_component[0] + eps[0]
    for i in range(1, n):
        rets[i] = mu + momentum * rets[i - 1] + trend_component[i] + eps[i]
    close = base_price * np.exp(np.cumsum(rets))

    # OHLC a partir do close; sombras pequenas e proporcionais a sigma (realistas)
    open_ = np.empty(n)
    open_[0] = base_price
    open_[1:] = close[:-1]
    intrabar = sigma * close * wick
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 1, n)) * intrabar
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 1, n)) * intrabar
    volume = rng.integers(500, 5000, n) * (1.0 + 5.0 * (sigma / base_sigma - 1.0).clip(0))

    df = pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=index,
    )
    df.index.name = "timestamp"
    return df
