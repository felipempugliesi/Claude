"""
quantday — base quantitativa para estrategias de day trade (forex e NASDAQ).

Modulos:
    config      -> especificacao dos instrumentos e parametros da estrategia
    data        -> carregamento de OHLCV e gerador de dados sinteticos
    indicators  -> indicadores tecnicos vetorizados (EMA, RSI, ATR, ADX, VWAP...)
    signals     -> logica de sinais (entrada/saida) da estrategia
    risk        -> dimensionamento de posicao e gestao de risco
    backtest    -> motor de backtest bar-a-bar sem look-ahead
    metrics     -> metricas de performance (Sharpe, drawdown, profit factor...)
"""

__version__ = "0.1.0"

from . import (  # noqa: F401
    config, data, indicators, signals, risk, backtest, metrics,
    webull, walkforward,
)
