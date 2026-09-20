"""
Gestao de risco e dimensionamento de posicao.

Regra central: risco fixo-fracionario. Cada operacao arrisca uma fracao
constante do capital (`risk_per_trade`), definida pela distancia ao stop em
unidades de PRECO e pelo valor do ponto do instrumento.
"""
from __future__ import annotations

import math


def stop_target(entry: float, atr: float, direction: int, params):
    """Calcula stop e alvo iniciais a partir do ATR.

    direction: +1 (long) ou -1 (short).
    Retorna (stop, target).
    """
    stop_dist = params.stop_atr_mult * atr
    target_dist = params.target_atr_mult * atr
    stop = entry - direction * stop_dist
    target = entry + direction * target_dist
    return stop, target


def position_size(equity: float, entry: float, stop: float, instrument, params) -> float:
    """Tamanho de posicao (em unidades/contratos) para arriscar `risk_per_trade`.

    size = (equity * risk_per_trade) / (dist_stop_em_preco * point_value)

    Arredonda para baixo no incremento minimo do instrumento.
    """
    risk_cash = equity * params.risk_per_trade
    stop_dist = abs(entry - stop)
    if stop_dist <= 0:
        return 0.0
    raw = risk_cash / (stop_dist * instrument.point_value)
    steps = math.floor(raw / instrument.min_size)
    return max(0.0, steps * instrument.min_size)


def r_multiple(entry: float, exit_price: float, stop: float, direction: int) -> float:
    """Resultado da operacao em multiplos de R (risco inicial)."""
    risk = abs(entry - stop)
    if risk <= 0:
        return 0.0
    return direction * (exit_price - entry) / risk
