"""
Configuracao de instrumentos e parametros da estrategia.

Os horarios de sessao sao interpretados no fuso da bolsa do instrumento
(`Instrument.session_tz`). Assim o filtro de sessao acompanha o horario de
verao (DST) automaticamente: 09:30-16:00 em "America/New_York" e sempre a
abertura do pregao dos EUA, seja o UTC 13:30 (EDT) ou 14:30 (EST).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace


@dataclass(frozen=True)
class Session:
    """Janela de negociacao no fuso do instrumento (inicio inclusivo, fim exclusivo)."""
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
    asset_class: str          # "forex" | "index_future" | "equity" | "fx_etf"
    point_value: float
    min_size: float
    spread: float             # em unidades de preco (round-trip)
    tick_size: float
    sessions: tuple[Session, ...] = field(default_factory=tuple)
    session_tz: str = "UTC"   # fuso em que `sessions` sao definidas


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
# Em horario de NY (session_tz="America/New_York"): pregao 09:30-16:00 ET.
# Foco no drive de abertura e na ultima hora ("power hour").
NASDAQ_SESSIONS = (
    Session("09:30", "11:30", "RTH open drive"),
    Session("15:00", "16:00", "Power hour"),
)

# ETFs de moeda (FXE/FXB) so negociam no RTH dos EUA (nao 24h). Como tem baixa
# liquidez intradiaria, usamos o pregao inteiro (09:30-16:00 ET) como sessao.
US_RTH_FULL = (
    Session("09:30", "16:00", "US RTH"),
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
        tick_size=0.25, sessions=NASDAQ_SESSIONS, session_tz="America/New_York",
    ),
    "MNQ": Instrument(  # Micro E-mini Nasdaq-100 (USD 2/ponto) — varejo
        symbol="MNQ", asset_class="index_future",
        point_value=2.0, min_size=1.0, spread=0.50,
        tick_size=0.25, sessions=NASDAQ_SESSIONS, session_tz="America/New_York",
    ),
    "QQQ": Instrument(  # ETF Nasdaq-100
        symbol="QQQ", asset_class="equity",
        point_value=1.0, min_size=1.0, spread=0.02,
        tick_size=0.01, sessions=NASDAQ_SESSIONS, session_tz="America/New_York",
    ),
    # --- Proxies de forex via ETF de moeda (US_ETF no Webull) ---
    # FXE ~ EUR/USD, FXB ~ GBP/USD. Negociam so no RTH dos EUA; baixa liquidez
    # intradiaria. Sao PROXY de forex dado o acesso, nao o mercado 24h.
    "FXE": Instrument(  # Invesco CurrencyShares Euro Trust (~EUR/USD)
        symbol="FXE", asset_class="fx_etf",
        point_value=1.0, min_size=1.0, spread=0.03,
        tick_size=0.01, sessions=US_RTH_FULL, session_tz="America/New_York",
    ),
    "FXB": Instrument(  # Invesco CurrencyShares British Pound (~GBP/USD)
        symbol="FXB", asset_class="fx_etf",
        point_value=1.0, min_size=1.0, spread=0.04,
        tick_size=0.01, sessions=US_RTH_FULL, session_tz="America/New_York",
    ),
    # --- Futuros de moeda CME (FOREX real, liquido) ---
    # Alvo preferido para forex, mas exigem assinatura de US_FUTURES no Webull
    # (indisponivel nesta conta). Deixados prontos: com a assinatura, basta
    # puxar as barras (WebullMDataClient/get_futures_bars) e rodar.
    # point_value = notional do contrato: 1.0 de variacao no quote = size USD.
    "M6E": Instrument(  # Micro EUR/USD (notional 12.500 EUR); 1 pip=USD 1,25
        symbol="M6E", asset_class="fx_future",
        point_value=12_500.0, min_size=1.0, spread=0.00005,
        tick_size=0.00001, sessions=FX_SESSIONS, session_tz="UTC",
    ),
    "M6B": Instrument(  # Micro GBP/USD (notional 6.250 GBP); 1 pip=USD 0,625
        symbol="M6B", asset_class="fx_future",
        point_value=6_250.0, min_size=1.0, spread=0.00010,
        tick_size=0.00001, sessions=FX_SESSIONS, session_tz="UTC",
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
    # ETF de moeda: comportamento parecido com forex (ATR% intradiario baixo).
    "fx_etf": StrategyParams(
        ema_fast=9, ema_slow=21, ema_trend=50, adx_min=18.0,
        atr_min_pct=0.02, atr_max_pct=0.60,
        stop_atr_mult=1.5, target_atr_mult=3.0, risk_per_trade=0.005,
        max_trades_per_day=4,
    ),
    # Futuro de moeda CME: mesmo perfil do forex spot.
    "fx_future": StrategyParams(
        ema_fast=9, ema_slow=21, ema_trend=50, adx_min=18.0,
        atr_min_pct=0.02, atr_max_pct=0.60,
        stop_atr_mult=1.5, target_atr_mult=3.0, risk_per_trade=0.005,
        max_trades_per_day=4,
    ),
}


def params_for(instrument: Instrument, **overrides) -> StrategyParams:
    """Retorna os parametros da estrategia para um instrumento, com overrides."""
    base = PARAMS_BY_CLASS.get(instrument.asset_class, StrategyParams())
    return replace(base, **overrides) if overrides else base
