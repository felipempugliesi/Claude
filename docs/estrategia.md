# Estratégia quantitativa de day trade — Forex e NASDAQ

**Modelo:** Tendência + Pullback com risco ajustado por volatilidade
**Timeframe:** intradiário (5 min por padrão)
**Instrumentos:** EUR/USD, GBP/USD (forex) · NQ/MNQ, QQQ (NASDAQ)

> ⚠️ **Aviso.** Este é um material técnico/educacional. Os números de
> backtest neste repositório vêm de **dados sintéticos** e servem apenas para
> validar o funcionamento do código — **não são previsão de desempenho nem
> recomendação de investimento**. Antes de operar capital real, valide em
> dados históricos reais, com walk-forward e custos realistas. Day trade
> alavancado tem risco elevado de perda.

---

## 1. Tese quantitativa

A estratégia combina dois fenômenos estatísticos bem documentados em séries
intradiárias:

1. **Persistência de tendência (momentum)** — dentro de uma sessão, o preço
   tende a manter a direção do fluxo dominante por algum tempo.
2. **Reversão de curto prazo (pullback)** — sobre essa tendência, o preço
   oscila; recuos temporários contra a tendência tendem a ser recomprados.

A ideia é **operar a favor da tendência, entrando no pullback** — comprar a
correção numa tendência de alta (e vender o repique numa de baixa). Isso
oferece um ponto de entrada com **stop curto** (perto do ponto de exaustão do
recuo) e **alvo largo** (a continuação da tendência), gerando uma relação
risco/retorno assimétrica favorável (~2:1).

Três filtros aumentam a razão sinal/ruído:

- **Regime**: só operar quando há tendência de fato (não em mercado lateral).
- **Volatilidade**: só operar quando o ATR está numa faixa "saudável".
- **Sessão**: só operar nas janelas de maior liquidez do instrumento.

---

## 2. Definição formal dos sinais

Todos os indicadores são **causais** (usam apenas dados até a barra corrente).
O sinal é avaliado no **fechamento** da barra `t`; a ordem é executada na
**abertura** da barra `t+1`. Não há look-ahead.

### 2.1 Regime de tendência

Desacoplamos a **tendência** (estrutura de médio/longo prazo) do **gatilho**
(o pullback de curto prazo). Isso é essencial: se exigíssemos `EMA_rápida >
EMA_lenta` no regime, perderíamos o sinal exatamente quando o pullback empurra
a EMA rápida para baixo.

```
tendência de ALTA  ⇔  EMA_slow > EMA_trend  E  close > EMA_trend  E  ADX > adx_min
tendência de BAIXA ⇔  EMA_slow < EMA_trend  E  close < EMA_trend  E  ADX > adx_min
```

- `EMA_slow` (21) vs `EMA_trend` (50): direção estrutural.
- `ADX > adx_min` (18–20): confirma que há **força** de tendência — filtra
  mercado lateral, onde pullback-trading tem expectativa negativa.

### 2.2 Gatilho de entrada (pullback de momentum)

Dentro da tendência, esperamos o momentum enfraquecer e voltar:

```
LONG:  regime = ALTA
       E  o RSI recuou abaixo de rsi_pullback (≈42) nas últimas N barras
       E  o RSI cruza ACIMA de rsi_trigger (50) nesta barra   (retomada)
       E  close > VWAP da sessão                              (viés intradiário)
       E  filtro de volatilidade e de sessão OK

SHORT: espelhado (RSI acima de 100−rsi_pullback, cruza abaixo de 100−rsi_trigger,
       close < VWAP)
```

O `EMA_fast` (9) e o RSI capturam a oscilação de curto prazo; o VWAP da sessão
ancora o viés intradiário (compramos só acima do preço médio ponderado por
volume do dia, vendemos só abaixo).

### 2.3 Filtro de volatilidade

```
vol_ok  ⇔  atr_min_pct ≤ 100·ATR/preço ≤ atr_max_pct
```

Evita mercado parado (ATR baixo → ruído, custos dominam) e pânico (ATR
altíssimo → stops estourados). Os limiares são calibrados por classe, porque o
ATR% intradiário de forex (~0.05–0.15%) é bem menor que o de índices
(~0.1–1%):

| Classe          | atr_min_pct | atr_max_pct |
|-----------------|-------------|-------------|
| forex           | 0.03%       | 0.50%       |
| índice / equity | 0.05%       | 2.50%       |

### 2.4 Filtro de sessão (janelas de maior liquidez, UTC)

| Mercado | Janela (UTC)         | Motivo                                  |
|---------|----------------------|-----------------------------------------|
| Forex   | 12:00–16:00          | Overlap Londres/NY: maior volume/spread |
| NASDAQ  | 13:30–15:30          | Drive de abertura do pregão (RTH)       |
| NASDAQ  | 19:00–20:00          | "Power hour" (última hora)              |

> Ajuste ao horário de verão (DST) do mercado se for operar ao vivo — as
> janelas em UTC deslocam-se 1h conforme US/EU DST.

---

## 3. Gestão de risco

O coração da estratégia. Sem gestão de risco, nenhum sinal sobrevive.

### 3.1 Stop e alvo por ATR

```
stop   = entrada ∓ stop_atr_mult   · ATR      (1.5–1.8 · ATR)
alvo   = entrada ± target_atr_mult · ATR      (3.0–3.6 · ATR)
```

Relação risco/retorno alvo ≈ **2R** (o alvo é o dobro do stop). Isso permite
ser lucrativo com taxa de acerto **abaixo de 50%** (ver §4).

### 3.2 Dimensionamento (risco fixo-fracionário)

Cada operação arrisca uma fração fixa do capital:

```
risco_$        = capital · risk_per_trade            (0.5% por operação)
dist_stop_$    = |entrada − stop| · valor_do_ponto
tamanho        = floor( risco_$ / dist_stop_$ )      (em contratos/lotes mínimos)
```

O `valor_do_ponto` traduz variação de preço em dinheiro:

| Instrumento | valor/ponto | Observação                          |
|-------------|-------------|-------------------------------------|
| EUR/USD     | US$ 100.000 | 1 lote padrão; 1 pip (0.0001)=US$10 |
| GBP/USD     | US$ 100.000 | idem                                |
| NQ          | US$ 20      | E-mini Nasdaq-100                   |
| MNQ         | US$ 2       | Micro E-mini (varejo)               |
| QQQ         | US$ 1       | ETF, por ação                       |

> Consequência prática: com US$ 100k e 0.5% de risco (US$ 500/trade), 1
> contrato **NQ** (stop ~60 pts = US$ 1.200 de risco) é **rejeitado** pelo
> sizing — use **MNQ** ou aumente o capital/risco. O código faz isso
> automaticamente (tamanho 0 → sem trade).

### 3.3 Circuit breakers

- **Máx. de trades/dia** (3–4): evita overtrading.
- **Limite de perda diária** (−2%): se o dia atinge −2%, encerra as operações
  do dia (trava o "revenge trading").
- **Time-stop**: toda posição é encerrada no fim da sessão — **nunca carrega
  overnight** (é day trade).

### 3.4 Trailing stop (opcional, desligado por padrão)

Existe um trailing por ATR, mas nos testes a **saída por R-múltiplo fixo**
(stop/alvo) mostrou-se mais robusta — o trailing apertado corta vencedores
antes do alvo. Ligue via `use_trailing=True` e recalibre `trail_atr_mult` se
preferir gestão dinâmica.

---

## 4. Matemática da expectativa

A expectativa por operação, em múltiplos de R:

```
E[R] = p · G − (1 − p) · 1
```

onde `p` = taxa de acerto e `G` = ganho médio dos vencedores (em R). Com alvo
2R e stop 1R (G≈2):

| Taxa de acerto p | E[R] por trade |
|------------------|----------------|
| 30%              | −0.10 R        |
| **34%**          | **+0.02 R** (break-even) |
| 40%              | +0.20 R        |
| 45%              | +0.35 R        |
| 50%              | +0.50 R        |

Ou seja: **com relação 2:1, basta acertar ~34%** para ficar no zero a zero.
Todo o jogo é manter o acerto acima disso e o alvo/stop na proporção certa —
por isso os filtros de regime/volatilidade/sessão existem: eles elevam `p`
recusando as entradas de baixa qualidade.

---

## 5. Resultados em dados sintéticos (ilustrativos)

`python examples/run_backtest.py --days 250` — capital inicial US$ 100k, risco
0.5%/trade, ~250 pregões de dados sintéticos (semente fixa por símbolo).

| Instrumento | Trades | Acerto | Profit factor | Expectancy | Retorno | Max DD |
|-------------|-------:|-------:|--------------:|-----------:|--------:|-------:|
| EUR/USD     | 61     | 39.3%  | 1.29          | +0.18 R    | +5.5%   | −3.5%  |
| GBP/USD     | 45     | 44.4%  | 1.59          | +0.33 R    | +7.6%   | −2.5%  |
| MNQ         | 37     | 43.2%  | 1.39          | +0.23 R    | +3.3%   | −2.5%  |
| QQQ         | 42     | 42.9%  | 1.11          | +0.06 R    | +1.3%   | −4.7%  |

**Leitura honesta destes números:**

- O perfil é o esperado de uma estratégia de tendência: **acerto < 50%**,
  compensado por **profit factor > 1** graças à relação 2:1.
- Os resultados **variam com a semente** dos dados sintéticos (sem estrutura
  real, não há edge estatístico verdadeiro). Isso é a lição central: **um
  backtest só vale sobre dados reais**, com validação fora da amostra.
- Servem para provar que o *pipeline* (indicadores → sinais → risco →
  execução → métricas) está correto e sem look-ahead, **não** para prometer
  retorno.

---

## 6. Como levar para dados reais

1. **Dados**: obtenha OHLCV intradiário (5 min) do seu broker/fonte
   (Dukascopy, Polygon, Webull, MetaTrader…) e salve como CSV
   `timestamp,open,high,low,close,volume` em UTC. Rode:
   ```
   python examples/run_backtest.py --csv seus_dados.csv --symbol EURUSD
   ```
2. **Custos reais**: ajuste `spread` (e adicione comissão/slippage) em
   `config.py` para o seu broker. Forex/CFD embutem spread; futuros têm
   comissão por contrato.
3. **Validação fora da amostra (walk-forward)**: calibre parâmetros numa
   janela (ex.: 2022–2023) e teste "cego" na seguinte (2024). Nunca reporte o
   resultado in-sample.
4. **Robustez**: varie os parâmetros ±20% e confirme que o resultado não
   colapsa (evita overfitting). Teste em vários pares/anos.
5. **Execução ao vivo**: comece em **conta demo**, depois tamanho mínimo.
   Respeite os circuit breakers.

---

## 7. Parâmetros (resumo)

Ver `quantday/config.py`. Principais:

| Grupo          | Parâmetro           | Forex   | Índice/Equity |
|----------------|---------------------|---------|---------------|
| Tendência      | ema_fast/slow/trend | 9/21/50 | 8/20/50       |
|                | adx_min             | 18      | 20            |
| Gatilho        | rsi_pullback/trigger| 42 / 50 | 42 / 50       |
|                | pullback_lookback   | 6       | 6             |
| Volatilidade   | atr_min/max_pct     | 0.03/0.50 | 0.05/2.50   |
| Risco          | stop/target_atr_mult| 1.5/3.0 | 1.8/3.6       |
|                | risk_per_trade      | 0.5%    | 0.5%          |
|                | max_trades_per_day  | 4       | 3             |
|                | daily_loss_limit    | 2%      | 2%            |

---

## 8. Limitações e próximos passos

- **Sem dados reais** aqui — a validação real é do usuário.
- **Um instrumento por vez** no backtest; não há correlação de carteira nem
  limite de risco agregado entre posições simultâneas.
- **Sem modelagem de gap/lacuna** de abertura, notícias, ou microestrutura.
- Próximos passos sugeridos: (a) walk-forward automatizado; (b) filtro de
  notícias/macro (NFP, CPI, FOMC) para pausar forex; (c) breakout de abertura
  como estratégia complementar ao pullback; (d) sizing por volatilidade-alvo
  (vol targeting) no nível de carteira.
