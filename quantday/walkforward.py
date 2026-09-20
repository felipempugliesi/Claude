"""
Walk-forward analysis (analise fora-da-amostra rolante).

Por que walk-forward? Um backtest unico, otimizado sobre todo o historico,
quase sempre parece otimo — e mente (overfitting). O walk-forward mede o que
importa: como parametros escolhidos NO PASSADO se saem em dados que o
otimizador NUNCA viu.

Procedimento (rolling / anchored):
  1. Divide o historico em janelas: [treino IS | teste OOS], deslizando adiante.
  2. Em cada janela, otimiza os parametros no periodo IS (in-sample).
  3. Aplica ESSES parametros no periodo OOS (out-of-sample) — sem reotimizar.
  4. Concatena todos os trechos OOS: essa curva concatenada e a estimativa
     honesta de desempenho. Reporta tambem a eficiencia WF (OOS / IS).

A otimizacao aqui e uma busca em grade (grid search) sobre poucos parametros
de alto impacto, escolhendo pela metrica-objetivo (default: profit factor com
minimo de trades). E deliberadamente simples e robusta — o objetivo do
walk-forward nao e achar o "melhor" parametro, e sim medir a degradacao
IS->OOS.
"""
from __future__ import annotations

import itertools
from dataclasses import replace

import numpy as np
import pandas as pd

from . import backtest, metrics


# Grade padrao: parametros de alto impacto, faixas conservadoras.
DEFAULT_GRID = {
    "adx_min": [15.0, 20.0, 25.0],
    "stop_atr_mult": [1.2, 1.5, 1.8],
    "target_atr_mult": [2.4, 3.0, 3.6],
}


def _objective(summary: dict, min_trades: int) -> float:
    """Metrica a maximizar no IS. Penaliza amostras pequenas."""
    if summary["n_trades"] < min_trades:
        return -np.inf
    pf = summary["profit_factor"]
    if not np.isfinite(pf):
        pf = 5.0  # cap para PF infinito (sem perdas na amostra)
    # expectancy pondera a qualidade media por trade
    return pf * (1.0 + summary["expectancy_R"])


def optimize(df, instrument, base_params, grid=None, min_trades=8,
             starting_equity=100_000.0):
    """Grid search no periodo `df`. Retorna (melhores_params, melhor_resumo)."""
    grid = grid or DEFAULT_GRID
    keys = list(grid)
    best_params, best_summary, best_score = base_params, None, -np.inf
    for combo in itertools.product(*(grid[k] for k in keys)):
        overrides = dict(zip(keys, combo))
        params = replace(base_params, **overrides)
        _, _, summary = backtest.run(df, instrument, params, starting_equity)
        score = _objective(summary, min_trades)
        if score > best_score:
            best_score, best_params, best_summary = score, params, summary
    return best_params, best_summary


def run(df, instrument, base_params, is_days=180, oos_days=45,
        grid=None, min_trades=8, starting_equity=100_000.0):
    """Executa o walk-forward rolante.

    is_days  : tamanho da janela de treino (in-sample), em pregoes.
    oos_days : tamanho da janela de teste (out-of-sample), em pregoes.

    Retorna dict com:
      folds        : lista por janela (datas, params escolhidos, IS e OOS)
      oos_trades   : DataFrame de todos os trades OOS concatenados
      oos_summary  : metricas da curva OOS concatenada (o resultado honesto)
      wf_efficiency: mediana de (retorno OOS / retorno IS) — quanto do edge IS
                     sobrevive fora da amostra (>~0.5 e considerado saudavel)
    """
    days = df.index.normalize().unique()
    days = pd.DatetimeIndex(sorted(days))
    n = len(days)
    folds = []
    all_oos_trades = []
    equity = starting_equity

    start = 0
    while start + is_days + oos_days <= n:
        is_start = days[start]
        is_end = days[start + is_days - 1]
        oos_start = days[start + is_days]
        oos_end = days[start + is_days + oos_days - 1]

        is_df = df[(df.index.normalize() >= is_start) & (df.index.normalize() <= is_end)]
        oos_df = df[(df.index.normalize() >= oos_start) & (df.index.normalize() <= oos_end)]

        best_params, is_summary = optimize(
            is_df, instrument, base_params, grid, min_trades, starting_equity
        )
        oos_trades, _, oos_summary = backtest.run(
            oos_df, instrument, best_params, starting_equity
        )
        if not oos_trades.empty:
            oos_trades = oos_trades.copy()
            oos_trades["fold"] = len(folds)
            all_oos_trades.append(oos_trades)

        folds.append({
            "fold": len(folds),
            "is_period": (is_start.date(), is_end.date()),
            "oos_period": (oos_start.date(), oos_end.date()),
            "params": {k: getattr(best_params, k) for k in (grid or DEFAULT_GRID)},
            "is_return": is_summary["total_return"] if is_summary else 0.0,
            "is_pf": is_summary["profit_factor"] if is_summary else 0.0,
            "oos_return": oos_summary["total_return"],
            "oos_pf": oos_summary["profit_factor"],
            "oos_trades": oos_summary["n_trades"],
        })
        start += oos_days  # desliza pela janela OOS (nao sobrepoe OOS)

    # Curva OOS concatenada: aplica os PnL OOS em sequencia sobre o capital
    if all_oos_trades:
        oos_all = pd.concat(all_oos_trades, ignore_index=True).sort_values("exit_time")
        eq_points, eq = [], starting_equity
        for pnl in oos_all["pnl"]:
            eq += pnl
            eq_points.append(eq)
        oos_curve = pd.Series(eq_points, index=oos_all["exit_time"].values, name="equity")
        oos_summary = metrics.summarize(oos_all, oos_curve, starting_equity)
    else:
        oos_all = pd.DataFrame()
        oos_summary = metrics.summarize(pd.DataFrame(), pd.Series(dtype=float), starting_equity)

    # eficiencia WF: mediana de (retorno OOS / retorno IS) nas janelas com IS>0
    ratios = [
        f["oos_return"] / f["is_return"]
        for f in folds if f["is_return"] > 1e-9
    ]
    wf_eff = float(np.median(ratios)) if ratios else 0.0

    return {
        "folds": folds,
        "oos_trades": oos_all,
        "oos_summary": oos_summary,
        "wf_efficiency": wf_eff,
        "n_folds": len(folds),
    }
