# Radar Swing Quant — Runbook do check-in diário

Reprocessa o radar quantitativo de ações americanas (dados do **terminal Webull**, via MCP)
e atualiza o dashboard publicado e a watchlist. **Conta Webull é somente leitura — nunca enviar ordens.**
Isto é análise/educacional, **não recomendação de investimento**.

## Artefatos fixos
- **Artifact (dashboard):** `https://claude.ai/artifact/3v1eBAMC3MCYvBWTEScSAK` (publicar com `url=` este link para manter a mesma URL).
- **Watchlist Webull:** `Radar Swing Quant` — id `72042905c55b45448b0198b2ccab4e3b`.
- **Branch:** `claude/webull-stock-analysis-quantitative-jzk92h` do repo `felipempugliesi/Claude`.
- **Scripts (template de referência):** `analysis/pipeline.py`, `analysis/payload2.py`, `analysis/build2.py`.

## Universo (32 tickers)
Semis/Tech: `NVDA AMD INTC MU TSM AVGO META GOOGL AAPL ORCL PLTR TSLA`
Mid/small wave 2: `SMTC TWST HAFN TRMD CVI SDGR SMMT ODD FRNM SECZ ASST PURR`
Mid/small wave 3: `HALO DBX OSCR TXG IOVA PBF MG INFU`

## Passos
1. **Re-puxar dados atuais** (Webull MCP) para os 32 tickers:
   - `get_stock_snapshot` (P/E, P/S, EPS_TTM, máx/mín 52s, market cap, yield) — em lotes.
   - `get_stock_bars` (timespan `D`, count `70`, RTH) — em lotes de ≤20; o resultado grande é salvo em arquivo (processar com Python).
   - `get_analyst_target_price` e `get_analyst_rating` (por ticker).
   - `get_stock_capital_flow` (count 3, por ticker) → fluxo líquido de ordens grandes+médias.
2. **Atualizar os dicionários** em `pipeline.py` (`snap`, `tgt`, `rat`, `cf`) com os valores novos e ajustar
   `files=[...]` para os caminhos dos arquivos de candles salvos, e `BASE` para o scratchpad da sessão.
   *(Observação: SMMT publica alvo em GBP — converter ~×1,26 e manter a flag `gbp_flag`.)*
3. **Rodar** `python3 pipeline.py && python3 payload2.py && python3 build2.py` → gera `dashboard.html`.
   - Modelo A = **Momentum (agressivo)**; Modelo B = **Qualidade + Recuo**; ambos com stop 2×ATR, alvos 2R/3R e sizing por volatilidade.
4. **Publicar** o `dashboard.html` atualizando o artifact existente (passar `url=` o link acima).
5. **Atualizar a watchlist** Webull `Radar Swing Quant`: manter BUYs dos dois modelos + near-buy + nomes de qualidade;
   remover o que saiu (`remove_watchlist_instruments`), adicionar novos (`add_watchlist_instruments`).
6. **Commit + push** do `dashboard.html` (e dos scripts, se alterados) na branch.
7. **Resumo** (para push/email): mudanças de veredito vs. execução anterior em cada modelo, novos BUY/SELL,
   e alertas (papéis que romperam stop, encostaram no alvo, ou RSI em extremo).

## Metodologia (resumo)
- Cada fator → **z-score** vs. a média do universo; combinação ponderada; score reescalado 0–100; BUY ≥55, HOLD 45–55, SELL <45.
- **Modelo A (Momentum):** momentum 35% · técnico 25% · fluxo 15% · analistas 20% (× confiança da cobertura) · valuation 5%. Penaliza esticado/parabólico.
- **Modelo B (Qualidade+Recuo):** qualidade 30% · recuo 30% (RSI 40–58, perto SMA20, ~5–18% off-high) · tendência 15% (acima SMA50) · upside 20% · fluxo 5%. *Quality gate* barra junk/tendência quebrada/parabólica no BUY.

## Degradação graciosa
Se o re-fetch completo dos 32 for inviável no tempo disponível, priorizar os nomes da **watchlist**,
recomputar seus sinais e reportar mudanças/alertas — sem falhar silenciosamente.

## Hardening futuro (opcional)
Refatorar o `pipeline.py` para ler os dados de arquivos JSON gerados no passo 1 (em vez de dicionários hardcoded),
tornando o job 100% automático sem edição manual de código.
