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
# DADOS REAIS do Webull (CSVs já incluídos em data/)
python examples/run_webull.py

# dados sintéticos (cesta completa forex + NASDAQ)
python examples/run_backtest.py --days 250

# um instrumento específico (sintético)
python examples/run_backtest.py --symbol MNQ --days 180

# seus próprios dados (CSV em UTC: timestamp,open,high,low,close,volume)
python examples/run_backtest.py --csv meus_dados.csv --symbol EURUSD
```

## Dados reais via Webull

Os dados em `data/*.csv` foram puxados do **Webull** (endpoint de candles) e
normalizados por [`quantday/webull.py`](quantday/webull.py). Restrições da
assinatura usada e como contorná-las:

| Quero      | Ideal          | Disponível no Webull aqui | Usado           |
|------------|----------------|---------------------------|-----------------|
| NASDAQ     | futuro NQ/MNQ  | futuros exigem assinatura separada ❌ | **QQQ** (ETF) ✓ |
| Forex      | spot / 6E, 6B  | sem spot; futuros ❌       | **FXE**(~EUR/USD), **FXB**(~GBP/USD) — ETFs de moeda |

> ⚠️ ETFs de moeda negociam **só no pregão dos EUA** (não 24h), têm **baixa
> liquidez intradiária** (barras esparsas) e **não são** o mercado forex real.
> São um proxy dado o acesso. Para forex de verdade, use futuros de moeda
> (assinatura de futuros) ou uma fonte 24h (Dukascopy, MetaTrader).

**Resultados em dados reais** (`python examples/run_webull.py`, M5, US$100k, 0.5%/trade):

| Instrumento      | Pregões | Trades | Acerto | Profit factor | Retorno | Max DD |
|------------------|--------:|-------:|-------:|--------------:|--------:|-------:|
| QQQ (NASDAQ)     | 62      | 12     | 58.3%  | 2.83          | +4.6%   | −1.0%  |
| FXE (~EUR/USD)   | 65      | 5      | 20.0%  | 0.50          | −1.0%   | −1.0%  |
| FXB (~GBP/USD)   | 95      | 2      | —      | —             | −1.0%   | −1.0%  |

Leitura honesta: em ativo **líquido** (QQQ) a estratégia se comporta como
esperado (poucos trades, seletivos, com relação risco/retorno favorável). Nos
**ETFs de moeda** ela quase não dispara e o pouco que dispara é ruído — a
lição é que **currency ETFs são veículos ruins para day trade intradiário**
(amostra pequena, métricas não confiáveis). É a evidência a favor de usar
futuros/spot de verdade para forex.

### Atualizar/estender os dados (com suas credenciais)

```python
from quantday.webull import WebullMDataClient
cli = WebullMDataClient()                       # lê WEBULL_APP_KEY / WEBULL_APP_SECRET
df = cli.get_bars("QQQ", "US_ETF", "M5", count=3000)   # pagina automaticamente
WebullMDataClient.to_csv(df, "data/QQQ_M5.csv")
```
Requer `pip install webull-python-sdk-core webull-python-sdk-mdata`. Sem
credenciais, `quantday.webull.normalize_bars(...)` converte qualquer JSON de
candles do Webull no formato do backtest.

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
  webull.py       # adaptador Webull: normaliza candles + cliente OpenAPI SDK
data/
  QQQ_M5.csv      # dados REAIS do Webull (NASDAQ-100 ETF)
  FXE_M5.csv      # dados REAIS do Webull (~EUR/USD)
  FXB_M5.csv      # dados REAIS do Webull (~GBP/USD)
examples/
  run_backtest.py # demonstração em dados sintéticos
  run_webull.py   # demonstração em dados reais do Webull
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
