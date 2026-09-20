"""
Configuracao de instrumentos e parametros da estrategia.

Todos os horarios de sessao sao em UTC. Ajuste conforme o horario de verao
do mercado (DST) se for operar ao vivo.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Session:
    """Janela de negociacao em UTC (inclusiva no inicio, exclusiva no fim)."""
    start: str  # "HH:MM"
    end: str    # "HH:MM"
    label: str = ""


@dataclass(frozen=True)
class Instrument:
    """Especificacao de um instrumento negociavel.

    point_value : valor monetario de 1.0 de variacao de PRECO por 1 unidade/contrato.
                  - Forex (conta em USD, quote USD): para EUR/USD, 1 lote padrao (100k)
                    equivale a point_value = 100_000 (1 pip = 0.0001 -> USD 10).
                  - NASDAQ NQ (mini): 1 ponto de indice = USD 20 por contrato.
                  - QQQ (acao/ETF): point_value = 1.0 (USD por acao por ponto).
    min_size    : menor incremento de posicao (0.01 lote em forex, 1 contrato em futuros).
    spread      : spread/custo por operacao em unidades de PRECO (round-trip aproximado).
    """
    symbol: str
    asset_class: str          # "forex" | "index_future" | "equity"
    point_value: float
    min_size: float
    spread: float             # em unidades de preco (round-trip)
    tick_size: float
    sessions: tuple[Session, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class StrategyParams:
    """Parametros da estrategia Tendencia+Pullback.

    A estrategia entra a favor da tendencia intradiaria apos um pullback de
    momentum, com stop e alvo dimensionados por ATR (volatilidade).
    """
    # --- Regime de tendencia ---
    ema_fast: int = 9
    ema_slow: int = 21
    ema_trend: int = 50        # filtro de tendencia mais longo
    adx_period: int = 14
    adx_min: float = 18.0      # regime so e "tendencia" acima disso

    # --- Gatilho de momentum (pullback) ---
    rsi_period: int = 14
    rsi_pullback: float = 42.0  # o RSI precisa ter recuado abaixo disso...
    rsi_trigger: float = 50.0   # ...e cruzar acima disso para disparar a compra
    pullback_lookback: int = 6  # janela (em barras) para procurar o recuo

    # --- Volatilidade ---
    atr_period: int = 14
    atr_min_pct: float = 0.15   # ignora se ATR < 0.15% do preco (mercado parado)
    atr_max_pct: float = 2.50   # ignora se ATR > 2.5% do preco (volatilidade extrema)

    # --- Risco / saidas ---
    stop_atr_mult: float = 1.5   # stop = entrada -/+ 1.5 * ATR
    target_atr_mult: float = 3.0 # alvo = entrada +/- 3.0 * ATR  (R-multiplo alvo = 2.0R)
    trail_atr_mult: float = 2.0  # trailing stop opcional (0 = desligado)
    # Trailing desligado por padrao: a saida por R-multiplo fixo (stop/alvo por
    # ATR) mostrou-se mais robusta nos testes — o trailing apertado corta
    # vencedores antes do alvo. Ligue e recalibre trail_atr_mult se preferir.
    use_trailing: bool = False

    # --- Gestao de conta ---
    risk_per_trade: float = 0.005   # 0.5% do capital por operacao
    max_trades_per_day: int = 4
    daily_loss_limit: float = 0.02  # circuit breaker: -2% no dia encerra o dia
    allow_shorts: bool = True


# ---------------------------------------------------------------------------
# Sessoes de maior liquidez (UTC)
# ---------------------------------------------------------------------------
# Forex: overlap Londres/Nova York — maior volume e melhores spreads.
FX_SESSIONS = (
    Session("12:00", "16:00", "London/NY overlap"),
)

# NASDAQ (indice/futuro NQ e QQQ): abertura do RTH e "power hour".
# RTH cash: 13:30-20:00 UTC. Foco no drive de abertura e na ultima hora.
NASDAQ_SESSIONS = (
    Session("13:30", "15:30", "RTH open drive"),
    Session("19:00", "20:00", "Power hour"),
)


# ---------------------------------------------------------------------------
# Instrumentos
# ---------------------------------------------------------------------------
INSTRUMENTS: dict[str, Instrument] = {
    "EURUSD": Instrument(
        symbol="EURUSD", asset_class="forex",
        point_value=100_000.0, min_size=0.01, spread=0.00008,
        tick_size=0.00001, sessions=FX_SESSIONS,
    ),
    "GBPUSD": Instrument(
        symbol="GBPUSD", asset_class="forex",
        point_value=100_000.0, min_size=0.01, spread=0.00012,
        tick_size=0.00001, sessions=FX_SESSIONS,
    ),
    "NQ": Instrument(  # E-mini Nasdaq-100 future (USD 20/ponto)
        symbol="NQ", asset_class="index_future",
        point_value=20.0, min_size=1.0, spread=0.50,
        tick_size=0.25, sessions=NASDAQ_SESSIONS,
    ),
    "MNQ": Instrument(  # Micro E-mini Nasdaq-100 (USD 2/ponto) — varejo
        symbol="MNQ", asset_class="index_future",
        point_value=2.0, min_size=1.0, spread=0.50,
        tick_size=0.25, sessions=NASDAQ_SESSIONS,
    ),
    "QQQ": Instrument(  # ETF Nasdaq-100
        symbol="QQQ", asset_class="equity",
        point_value=1.0, min_size=1.0, spread=0.02,
        tick_size=0.01, sessions=NASDAQ_SESSIONS,
    ),
}


# Overrides de parametros por classe de ativo (opcional).
# Forex tende a ter tendencias mais suaves; NASDAQ, movimentos mais rapidos.
PARAMS_BY_CLASS: dict[str, StrategyParams] = {
    "forex": StrategyParams(
        ema_fast=9, ema_slow=21, ema_trend=50, adx_min=18.0,
        # ATR% intradiario de forex e pequeno (~0.05-0.15%): thresholds baixos.
        atr_min_pct=0.03, atr_max_pct=0.50,
        stop_atr_mult=1.5, target_atr_mult=3.0, risk_per_trade=0.005,
    ),
    "index_future": StrategyParams(
        ema_fast=8, ema_slow=20, ema_trend=50, adx_min=20.0,
        atr_min_pct=0.05, atr_max_pct=2.50,
        stop_atr_mult=1.8, target_atr_mult=3.6, risk_per_trade=0.005,
        max_trades_per_day=3,
    ),
    "equity": StrategyParams(
        ema_fast=8, ema_slow=20, ema_trend=50, adx_min=20.0,
        atr_min_pct=0.05, atr_max_pct=2.50,
        stop_atr_mult=1.8, target_atr_mult=3.6, risk_per_trade=0.005,
        max_trades_per_day=3,
    ),
}


def params_for(instrument: Instrument, **overrides) -> StrategyParams:
    """Retorna os parametros da estrategia para um instrumento, com overrides."""
    base = PARAMS_BY_CLASS.get(instrument.asset_class, StrategyParams())
    return replace(base, **overrides) if overrides else base
