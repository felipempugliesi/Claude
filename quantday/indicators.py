"""
Indicadores tecnicos vetorizados (pandas/numpy).

Convencao: todas as funcoes recebem Series/DataFrame de OHLCV com index
datetime (UTC) e retornam Series alinhadas ao mesmo index. Nenhuma funcao
olha para o futuro (sao causais: usam apenas dados ate a barra corrente).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Media movel exponencial."""
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Media movel simples."""
    return series.rolling(period, min_periods=period).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    """True Range de Wilder."""
    high, low, close = df["high"], df["low"], df["close"]
    prev_close = close.shift(1)
    tr = pd.concat(
        [(high - low), (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)
    return tr


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range (suavizacao de Wilder via EMA de alpha=1/period)."""
    tr = true_range(df)
    return tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index (suavizacao de Wilder)."""
    delta = series.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    out = 100.0 - (100.0 / (1.0 + rs))
    # quando nao ha perdas, RSI = 100; quando nao ha ganhos, RSI = 0
    out = out.where(avg_loss != 0.0, 100.0)
    out = out.where(avg_gain != 0.0, out.where(avg_loss == 0.0, 0.0))
    return out


def adx(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average Directional Index (forca da tendencia, 0-100)."""
    high, low = df["high"], df["low"]
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    plus_dm = pd.Series(plus_dm, index=df.index)
    minus_dm = pd.Series(minus_dm, index=df.index)

    tr = true_range(df)
    atr_ = tr.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()

    plus_di = 100.0 * (
        plus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / atr_
    )
    minus_di = 100.0 * (
        minus_dm.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean() / atr_
    )
    dx = 100.0 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0.0, np.nan)
    return dx.ewm(alpha=1.0 / period, adjust=False, min_periods=period).mean()


def session_vwap(df: pd.DataFrame) -> pd.Series:
    """VWAP reiniciado a cada dia (data UTC).

    Usa o preco tipico ((H+L+C)/3) ponderado por volume, acumulado por dia.
    """
    typical = (df["high"] + df["low"] + df["close"]) / 3.0
    vol = df["volume"].astype(float)
    day = df.index.normalize()  # reinicia por data UTC
    cum_pv = (typical * vol).groupby(day).cumsum()
    cum_v = vol.groupby(day).cumsum().replace(0.0, np.nan)
    return cum_pv / cum_v


def rolling_min(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=1).min()


def rolling_max(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window, min_periods=1).max()


def cross_above(series: pd.Series, level: float | pd.Series) -> pd.Series:
    """True na barra em que `series` cruza ACIMA de `level`."""
    prev = series.shift(1)
    lvl = level if np.isscalar(level) else level
    lvl_prev = lvl if np.isscalar(lvl) else lvl.shift(1)
    return (prev <= lvl_prev) & (series > lvl)


def cross_below(series: pd.Series, level: float | pd.Series) -> pd.Series:
    """True na barra em que `series` cruza ABAIXO de `level`."""
    prev = series.shift(1)
    lvl = level if np.isscalar(level) else level
    lvl_prev = lvl if np.isscalar(lvl) else lvl.shift(1)
    return (prev >= lvl_prev) & (series < lvl)


def compute_all(df: pd.DataFrame, params) -> pd.DataFrame:
    """Anexa todos os indicadores usados pela estrategia ao DataFrame OHLCV."""
    out = df.copy()
    close = out["close"]
    out["ema_fast"] = ema(close, params.ema_fast)
    out["ema_slow"] = ema(close, params.ema_slow)
    out["ema_trend"] = ema(close, params.ema_trend)
    out["rsi"] = rsi(close, params.rsi_period)
    out["atr"] = atr(out, params.atr_period)
    out["adx"] = adx(out, params.adx_period)
    out["vwap"] = session_vwap(out)
    out["atr_pct"] = 100.0 * out["atr"] / close
    return out
