# Radar Swing Quant — Runbook do check-in diário (pipeline data-driven)

Reprocessa o radar quantitativo de ações americanas (dados do **terminal Webull**, via MCP)
e atualiza o dashboard publicado e a watchlist. **Conta Webull é somente leitura — nunca enviar ordens.**
Isto é análise/educacional, **não recomendação de investimento**.

> **Hardening:** o pipeline é 100% orientado a dados. Você **não edita código** — só derruba as
> saídas cruas do Webull em `data/raw/` e roda a cadeia. O que faltar cai no *fallback* do último run.

## Artefatos fixos
- **Artifact (dashboard):** `https://claude.ai/artifact/3v1eBAMC3MCYvBWTEScSAK` (publicar com `url=` este link).
- **Watchlist Webull:** `Radar Swing Quant` — id `72042905c55b45448b0198b2ccab4e3b`.
- **Branch:** `claude/webull-stock-analysis-quantitative-jzk92h` (repo `felipempugliesi/Claude`).
- **Config estática:** `data/meta.json` (universo de 32 tickers, nomes, setores, teses, flag GBP). Só muda se o universo mudar.

## Fluxo
### 1. Buscar dados (Webull MCP) e salvar CRU em `data/raw/`
Para os 32 tickers de `data/meta.json`:
- `get_stock_snapshot` (lote, todos) → salvar a **lista retornada** em `data/raw/snapshot.json`.
- `get_stock_bars` (timespan `D`, count `70`, RTH; lotes ≤20) → cada saída (auto-salva em arquivo quando grande)
  vai para `data/raw/bars/bars1.json`, `bars2.json`, … (o objeto `{"result":[{symbol,result:[...]}]}` como veio).
- `get_analyst_target_price` (por ticker) → juntar as saídas numa **lista** em `data/raw/analyst_target.json`.
- `get_analyst_rating` (por ticker) → **lista** em `data/raw/analyst_rating.json`.
- `get_stock_capital_flow` (count 3, por ticker) → objeto **`{TICKER: <saída de 3 dias>}`** em `data/raw/capital_flow.json`.
- (opcional) `data/raw/asof.txt` com o rótulo da data, ex.: `19 set 2026 (fechamento)`.

*Não precisa converter nada:* `assemble.py` extrai os campos, converte fluxo $→$M, mcap→$bn e alvo GBP→USD.

### 2. Montar + pontuar + publicar (sem editar código)
```
python3 analysis/assemble.py        # data/raw/* + fallback -> data/radar_data.json (+ relatório de faltantes)
python3 analysis/pipeline.py        # -> data/radar_scored.json (2 modelos + stops/alvos/sizing)
python3 analysis/build_payload.py   # -> data/payload.json
python3 analysis/build.py           # -> dashboard.html
```
3. **Publicar** `dashboard.html` atualizando o artifact existente (passar `url=` o link acima).
4. **Watchlist**: manter BUYs dos dois modelos + near-buy + qualidade; remover o que saiu, adicionar novos.
5. **Commit + push** (`dashboard.html`, `data/`) na branch.
6. **Resumo** (curto): mudanças de veredito por modelo, novos BUY/SELL e alertas (rompeu stop, encostou no alvo, RSI extremo).

## Degradação graciosa
`assemble.py` usa o `data/radar_data.json` anterior como *fallback* por campo. Se faltar tempo, atualize ao menos
**snapshot + bars** (preço/técnico) e deixe analistas/fluxo do run anterior — o relatório do assemble lista o que faltou.

## Modelos (resumo)
- Fator → **z-score** vs. média do universo; combinação ponderada; score 0–100; BUY ≥55, HOLD 45–55, SELL <45.
- **A · Momentum (agressivo):** momentum 35 · técnico 25 · fluxo 15 · analistas 20 (× confiança da cobertura) · valuation 5. Penaliza esticado/parabólico.
- **B · Qualidade + Recuo:** qualidade 30 · recuo 30 (RSI 40–58, perto SMA20, ~5–18% off-high) · tendência 15 (acima SMA50) · upside 20 · fluxo 5. *Quality gate* barra junk/tendência quebrada/parabólica no BUY.

## Mudar o universo
Editar `data/meta.json` (tickers, meta.name/sector, thesis, gbp). Nenhum outro arquivo precisa mudar.
