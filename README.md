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
# WALK-FORWARD em dados reais (~2,3 anos) — o teste honesto (out-of-sample)
python examples/run_walkforward.py --symbol QQQ

# backtest simples em DADOS REAIS do Webull (CSVs incluídos em data/)
python examples/run_webull.py

# dados sintéticos (cesta completa forex + NASDAQ)
python examples/run_backtest.py --days 250

# um instrumento específico (sintético)
python examples/run_backtest.py --symbol MNQ --days 180

# seus próprios dados (CSV em UTC: timestamp,open,high,low,close,volume)
python examples/run_backtest.py --csv meus_dados.csv --symbol EURUSD
```

## Dados reais via Webull

Os dados em `data/*.csv` (~2,3 anos de barras M5) foram puxados do **Webull**
(endpoint de candles) e normalizados por [`quantday/webull.py`](quantday/webull.py).

**Futuros continuam bloqueados nesta conta.** Re-testei MNQ, M6E e M6B em M5 e
diário — todos retornam `MARKET_DATA_NOT_SUBSCRIBED: subscribe to US_FUTURES`.
Sem essa assinatura, o walk-forward roda nos instrumentos acessíveis (ETFs):

| Quero  | Alvo ideal      | Webull nesta conta          | Usado no walk-forward |
|--------|-----------------|-----------------------------|-----------------------|
| NASDAQ | futuro MNQ      | futuros ❌ (assinatura)      | **QQQ** (ETF)         |
| Forex  | futuro M6E/M6B  | futuros ❌; sem spot         | **FXE**, **FXB** (ETFs de moeda) |

Os instrumentos **MNQ, M6E, M6B já estão prontos no `config.py`** (specs reais
da CME). Com a assinatura de US_FUTURES, é um swap de símbolo: puxe as barras
(`get_futures_bars` / `WebullMDataClient`) e rode `run_walkforward.py --symbol MNQ`.

> ⚠️ Os ETFs de moeda negociam **só no pregão dos EUA** (não 24h), têm baixa
> liquidez intradiária e **não são** forex real — proxy dado o acesso.

**Fuso/DST:** o filtro de sessão é aplicado em **horário da bolsa**
(`America/New_York`), então acompanha o horário de verão automaticamente
(09:30 ET = abertura, seja 13:30 UTC no EDT ou 14:30 no EST). Essencial num
histórico multi-ano.

### Walk-forward (o teste honesto)

`python examples/run_walkforward.py` otimiza parâmetros numa janela de treino
(180 pregões, in-sample) e testa na seguinte (45 pregões, out-of-sample),
deslizando por todo o histórico. **A curva OOS concatenada é o resultado que
importa.** Resultado (US$100k, 0.5%/trade):

| Instrumento    | Pregões | Folds | Trades OOS | PF OOS | Retorno OOS | WF eff. |
|----------------|--------:|------:|-----------:|-------:|------------:|--------:|
| QQQ (NASDAQ)   | 584     | 8     | 41         | 0.98   | −0.3%       | −0.17   |
| FXE (~EUR/USD) | 612     | 9     | 40         | 0.88   | −1.7%       | −0.41   |

**Leitura honesta — e o ponto central de todo o projeto:** os períodos
*in-sample* parecem ótimos (retornos positivos em quase todos os folds), mas
**esse lucro NÃO sobrevive out-of-sample** (PF ≈ 0.9, retorno levemente
negativo, eficiência WF < 0). Ou seja: a lucratividade in-sample era em boa
parte **overfitting/sorte**, não edge real. Um backtest único e otimizado teria
mostrado números bonitos e enganosos; **o walk-forward expõe a verdade**. Como
está, a estratégia **não tem edge robusto** nesses instrumentos/período — não
opere capital real com ela sem antes encontrar e validar (walk-forward) uma
fonte de edge genuína. Isso é o sucesso do método, não uma falha do exercício.

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
  walkforward.py  # walk-forward: otimização IS rolante + teste OOS + eficiência WF
data/
  QQQ_M5.csv      # dados REAIS do Webull (~2,3 anos, NASDAQ-100 ETF)
  FXE_M5.csv      # dados REAIS do Webull (~EUR/USD)
  FXB_M5.csv      # dados REAIS do Webull (~GBP/USD)
examples/
  run_backtest.py     # demonstração em dados sintéticos
  run_webull.py       # backtest simples em dados reais do Webull
  run_walkforward.py  # walk-forward em dados reais (out-of-sample)
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
