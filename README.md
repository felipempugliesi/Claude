# quantday — base quantitativa para day trade (Forex e NASDAQ)

Framework em Python, backtestável e sem look-ahead, para uma estratégia de day
trade baseada em análise quantitativa, aplicada a **forex** (EUR/USD, GBP/USD)
e **NASDAQ** (futuros NQ/MNQ e ETF QQQ).

Estratégia: **Tendência + Pullback com risco ajustado por volatilidade** —
opera a favor da tendência intradiária, entrando em pullbacks de momentum, com
stops/alvos dimensionados por ATR e gestão de risco fixo-fracionário.

> ⚠️ Material técnico/educacional. Os backtests aqui usam **dados sintéticos**
> só para validar o código — **não** são previsão de desempenho nem
> recomendação de investimento. Valide em dados reais antes de operar.
> Documentação completa da lógica: [`docs/estrategia.md`](docs/estrategia.md).

## Instalação

```bash
pip install -r requirements.txt   # pandas, numpy
```

## Uso rápido

```bash
# roda a cesta completa (forex + NASDAQ) em dados sintéticos
python examples/run_backtest.py --days 250

# um instrumento específico
python examples/run_backtest.py --symbol MNQ --days 180

# seus próprios dados (CSV em UTC: timestamp,open,high,low,close,volume)
python examples/run_backtest.py --csv meus_dados.csv --symbol EURUSD
```

Testes:

```bash
python tests/test_quantday.py        # ou: python -m pytest -q
```

## Estrutura

```
quantday/
  config.py       # instrumentos (valor do ponto, spread, sessões) e parâmetros
  data.py         # carregar CSV + gerador de dados sintéticos realistas
  indicators.py   # EMA, RSI, ATR, ADX, VWAP de sessão (vetorizados, causais)
  signals.py      # regime de tendência + gatilho de pullback
  risk.py         # stop/alvo por ATR, sizing fixo-fracionário, R-múltiplo
  backtest.py     # motor bar-a-bar (execução na próxima abertura, sem look-ahead)
  metrics.py      # win rate, profit factor, expectancy, Sharpe, drawdown
examples/
  run_backtest.py # demonstração executável
tests/
  test_quantday.py
docs/
  estrategia.md   # tese, definição formal dos sinais, matemática, calibração
```

## Componentes da estratégia (resumo)

| Camada         | Regra                                                        |
|----------------|--------------------------------------------------------------|
| **Regime**     | `EMA_slow` vs `EMA_trend` + preço vs `EMA_trend` + `ADX > mín`|
| **Gatilho**    | RSI recua (pullback) e cruza de volta + `close` vs VWAP       |
| **Volatilidade** | ATR% dentro de faixa saudável (calibrada por classe)       |
| **Sessão**     | Só nas janelas de maior liquidez (overlap Londres/NY; open + power hour do RTH) |
| **Risco**      | Stop/alvo por ATR (≈2:1), 0.5%/trade, máx. trades/dia, stop de perda diária, sem overnight |

## Resultados ilustrativos (dados sintéticos, 250 pregões)

| Instrumento | Trades | Acerto | Profit factor | Retorno | Max DD |
|-------------|-------:|-------:|--------------:|--------:|-------:|
| EUR/USD     | 61     | 39%    | 1.29          | +5.5%   | −3.5%  |
| GBP/USD     | 45     | 44%    | 1.59          | +7.6%   | −2.5%  |
| MNQ         | 37     | 43%    | 1.39          | +3.3%   | −2.5%  |
| QQQ         | 42     | 43%    | 1.11          | +1.3%   | −4.7%  |

Perfil típico de estratégia de tendência: **acerto < 50%** compensado por
**profit factor > 1** via relação risco/retorno ~2:1. Números variam com a
semente dos dados sintéticos — a lição é validar em dados **reais** com
walk-forward (ver `docs/estrategia.md`, §6).
