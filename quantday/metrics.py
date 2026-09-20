"""Metricas de performance a partir da curva de capital e da lista de trades."""
from __future__ import annotations

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    """Drawdown maximo (fracao, ex.: 0.12 = -12%)."""
    if equity.empty:
        return 0.0
    running_max = equity.cummax()
    dd = equity / running_max - 1.0
    return float(dd.min())


def sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
    """Sharpe anualizado a partir de retornos por trade/dia (rf=0)."""
    if returns.std(ddof=1) == 0 or len(returns) < 2:
        return 0.0
    return float(np.sqrt(periods_per_year) * returns.mean() / returns.std(ddof=1))


def summarize(trades: pd.DataFrame, equity: pd.Series, starting_equity: float) -> dict:
    """Resumo de performance da estrategia."""
    if trades.empty:
        return {
            "n_trades": 0, "win_rate": 0.0, "profit_factor": 0.0,
            "expectancy_R": 0.0, "avg_R": 0.0, "total_return": 0.0,
            "max_drawdown": 0.0, "sharpe": 0.0, "final_equity": starting_equity,
        }

    wins = trades[trades["pnl"] > 0]["pnl"]
    losses = trades[trades["pnl"] < 0]["pnl"]
    gross_win = wins.sum()
    gross_loss = -losses.sum()
    profit_factor = float(gross_win / gross_loss) if gross_loss > 0 else float("inf")

    final_equity = float(equity.iloc[-1]) if len(equity) else starting_equity
    # Sharpe por trade (aprox.), anualizado supondo ~ n_trades/ano semelhante a serie
    ret_per_trade = trades["pnl"] / starting_equity

    return {
        "n_trades": int(len(trades)),
        "win_rate": float((trades["pnl"] > 0).mean()),
        "profit_factor": profit_factor,
        "expectancy_R": float(trades["r_multiple"].mean()),
        "avg_R": float(trades["r_multiple"].mean()),
        "total_return": final_equity / starting_equity - 1.0,
        "max_drawdown": max_drawdown(equity),
        "sharpe": sharpe(ret_per_trade, periods_per_year=len(trades) or 1),
        "final_equity": final_equity,
    }


def format_summary(s: dict) -> str:
    """Formata o resumo para impressao no terminal."""
    lines = [
        f"  Trades ............. {s['n_trades']}",
        f"  Win rate ........... {s['win_rate']*100:.1f}%",
        f"  Profit factor ...... {s['profit_factor']:.2f}",
        f"  Expectancy ......... {s['expectancy_R']:+.3f} R / trade",
        f"  Retorno total ...... {s['total_return']*100:+.2f}%",
        f"  Max drawdown ....... {s['max_drawdown']*100:.2f}%",
        f"  Sharpe (aprox) ..... {s['sharpe']:.2f}",
        f"  Capital final ...... {s['final_equity']:,.2f}",
    ]
    return "\n".join(lines)
