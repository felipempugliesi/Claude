# Universo de instrumentos para day trade quantitativo

Lista curada de tickers que se encaixam na análise MNQ/forex (mesma estratégia
Tendência+Pullback intradiária). Todas as specs foram confirmadas na listagem
de contratos do Webull (endpoint de instrumentos, não bloqueado). Foco em
**micro futuros** — o veículo de varejo compatível com o sizing de 0,5%/trade.

## Critérios de seleção

Para uma estratégia de tendência+pullback intradiária, o instrumento precisa de:
1. **Liquidez alta** — spread apertado, execução limpa.
2. **Volatilidade intradiária suficiente** — ATR% numa faixa operável (nem
   parado, nem em pânico).
3. **Comportamento de tendência intradiário** — não pura lateralização.
4. **Estrutura de sessão clara** — concentração de volume em janelas.
5. **Contrato micro disponível** — dimensionamento em conta de varejo.

> ⚠️ **Correlação importa.** MNQ, MES, MYM e M2K são todos índices de ações
> dos EUA e andam quase juntos (correlação intradiária ~0,8–0,95). Ter os
> quatro é redundância, não diversificação. A carteira ideal mistura
> **1–2 índices + ouro + petróleo + 2–3 FX** — fontes de risco diferentes.

## Lista (micro futuros CME/CBOT/COMEX/NYMEX)

### Tier 1 — núcleo recomendado (baixa correlação entre si)

| Símbolo | Instrumento          | USD/ponto | Tick (USD)   | Classe            | Por que entra |
|---------|----------------------|----------:|--------------|-------------------|---------------|
| **MNQ** | Micro Nasdaq-100     | 2         | 0,25 (1,25)  | index_future      | Já no projeto; alta vol, tendências fortes |
| **MES** | Micro S&P 500        | 5         | 0,25 (1,25)  | index_future      | Índice mais líquido do mundo; tendências mais suaves, menos ruído que NQ |
| **MGC** | Micro Gold (10 oz)   | 10        | 0,10 (1,00)  | commodity_future  | "Ouro"; tendências limpas, macro/juros/dólar; ativo fora do RTH de ações |
| **MCL** | Micro WTI Crude      | 100       | 0,01 (1,00)  | commodity_future  | Muito volátil, tendências fortes (usar filtro de evento: EIA qua 10:30 ET) |
| **M6E** | Micro EUR/USD        | 12.500    | 0,0001 (1,25)| fx_future         | Perna forex principal (já no config) |
| **M6B** | Micro GBP/USD        | 6.250     | 0,0001 (0,625)| fx_future        | Forex (já no config) |

### Tier 2 — bons complementos (diversificam ou reforçam)

| Símbolo | Instrumento          | USD/ponto | Tick (USD)   | Classe           | Nota |
|---------|----------------------|----------:|--------------|------------------|------|
| **M2K** | Micro Russell 2000   | 5         | 0,10 (0,50)  | index_future     | Small caps: mais beta/volátil que S&P; regime próprio |
| **MYM** | Micro Dow            | 0,50      | 1,0 (0,50)   | index_future     | Líquido; parecido com ES (alta correlação) |
| **M6A** | Micro AUD/USD        | 10.000    | 0,0001 (1,00)| fx_future        | Proxy "risk-on"; correlaciona com ações/commodities |
| **MCD** | Micro CAD/USD        | 10.000    | 0,0001 (1,00)| fx_future        | Ligado ao petróleo |

### Tier 3 — avançado / experimental (não adicionados por padrão)

| Símbolo | Instrumento         | USD/ponto | Tick (USD)   | Nota |
|---------|---------------------|----------:|--------------|------|
| SIL     | Micro Silver (1000 oz)| 1.000   | 0,005 (5,00) | Muito volátil/errático; notional alto p/ um "micro" |
| MHG     | Micro Copper (2500 lb)| 2.500   | 0,0005 (1,25)| Sensível a China/macro |
| MBT     | Micro Bitcoin (0,1)  | 0,10      | 5,0 (0,50)   | 24/7, vol extrema, regime muito diferente |

> Não há micro USD/JPY no Webull (M6J vazio); o full-size 6J tem cotação
> invertida (complica o valor do ponto) — fica de fora por ora.

Tier 1 e Tier 2 já estão em `quantday/config.py` com specs e sessões — quando
os dados chegarem, é `run_walkforward.py --symbol <TICKER>`.

## O que trazer (série histórica) — especificação

Para cada símbolo que você quiser incluir, o ideal é:

| Campo        | Requisito |
|--------------|-----------|
| **Timeframe**| **5 minutos (M5)** — resolução de trabalho da estratégia. (1-min opcional) |
| **Histórico**| **≥ 2 anos** (ideal 3–5) — quanto mais, mais folds no walk-forward |
| **Colunas**  | `timestamp, open, high, low, close, volume` |
| **Fuso**     | **UTC** de preferência (ou me diga o fuso e eu converto) |
| **Sessão**   | **Sessão eletrônica completa (Globex/ETH)** onde existir (ouro, petróleo, FX são ~24h); eu aplico o filtro de sessão certo. Para índices, RTH basta. |
| **Contrato** | Futuros: **série contínua** (contínuo back-adjusted) ou front-month rolado; me diga qual |
| **Formato**  | Um **CSV por símbolo**, igual aos de `data/` (ex.: `data/MGC_M5.csv`) |

Nomes equivalentes por fonte (caso baixe de terceiros):

| Símbolo | TradingView | Yahoo | Barchart/contínuo |
|---------|-------------|-------|-------------------|
| MNQ     | MNQ1!       | NQ=F  | MNQ / NQ          |
| MES     | MES1!       | ES=F  | MES / ES          |
| MGC     | MGC1!       | GC=F  | MGC / GC          |
| MCL     | MCL1!       | CL=F  | MCL / CL          |
| M6E     | M6E1! (ou 6E1!) | EURUSD=X / 6E=F | M6E / 6E |
| M6B     | M6B1!       | GBPUSD=X / 6B=F | M6B / 6B   |

> Se preferir, dá para usar os **ETFs proxy** (dados que já sei puxar do
> Webull): SPY→MES, GLD→MGC, USO→MCL, IWM→M2K, DIA→MYM, FXA→M6A, FXC→MCD.
> Menos fiel que o futuro (RTH-only, sem alavancagem), mas serve para um
> screen inicial de volatilidade/correlação sem você baixar nada.
