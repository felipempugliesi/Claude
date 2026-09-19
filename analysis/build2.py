import json
BASE="/tmp/claude-0/-home-user-Claude/acfda38c-f805-5d0e-9f01-51d2c4d57305/scratchpad/"
payload=open(BASE+"payload2.json").read()
HTML = r'''<title>Radar Swing Quant</title>
<meta name="description" content="Análise quantitativa buy/hold/sell de 24 ações americanas com stops, alvos e sizing, via terminal Webull.">
<style>
:root{
  --bg:#eef1f5;--surface:#fff;--surface2:#f5f7fa;--line:#dde3ea;
  --ink:#141a22;--ink2:#3f4a58;--muted:#6b7787;--faint:#9aa5b3;
  --accent:#1f6f8b;--accent-soft:#e2eef2;
  --buy:#0f8f5f;--buy-bg:#e3f4ec;--hold:#b9770c;--hold-bg:#f8efdc;--sell:#c73e3e;--sell-bg:#f8e5e5;
  --pos:#1f7a94;--neg:#c76b4a;--spec:#8e44ad;--spec-bg:#f0e6f6;
  --shadow:0 1px 2px rgba(20,26,34,.05),0 4px 16px rgba(20,26,34,.06);
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --bg:#0d1116;--surface:#161c24;--surface2:#1c242e;--line:#2a333f;
  --ink:#e7ecf2;--ink2:#c2cad4;--muted:#8b96a5;--faint:#5e6a79;
  --accent:#4bb3d1;--accent-soft:#16323c;
  --buy:#3fc088;--buy-bg:#123024;--hold:#e0a838;--hold-bg:#332813;--sell:#e56b6b;--sell-bg:#331b1b;
  --pos:#4bb3d1;--neg:#e08a63;--spec:#c084e0;--spec-bg:#2a1c33;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.35);}}
:root[data-theme="dark"]{
  --bg:#0d1116;--surface:#161c24;--surface2:#1c242e;--line:#2a333f;
  --ink:#e7ecf2;--ink2:#c2cad4;--muted:#8b96a5;--faint:#5e6a79;
  --accent:#4bb3d1;--accent-soft:#16323c;
  --buy:#3fc088;--buy-bg:#123024;--hold:#e0a838;--hold-bg:#332813;--sell:#e56b6b;--sell-bg:#331b1b;
  --pos:#4bb3d1;--neg:#e08a63;--spec:#c084e0;--spec-bg:#2a1c33;
  --shadow:0 1px 2px rgba(0,0,0,.3),0 6px 20px rgba(0,0,0,.35);}
*{box-sizing:border-box}
body{background:var(--bg);color:var(--ink);font-family:"IBM Plex Sans",system-ui,-apple-system,Segoe UI,Roboto,sans-serif;line-height:1.5;-webkit-font-smoothing:antialiased}
.mono{font-family:"IBM Plex Mono",ui-monospace,SFMono-Regular,Menlo,monospace;font-variant-numeric:tabular-nums}
.wrap{max-width:1180px;margin:0 auto;padding-inline:20px;padding-block:0}
h1,h2,h3{margin:0;text-wrap:balance;font-weight:600;letter-spacing:-.01em}
a{color:var(--accent)}
header{position:sticky;top:env(safe-area-inset-top,0px);z-index:20;background:var(--surface);border-bottom:1px solid var(--line)}
.hd{display:flex;align-items:center;gap:14px;flex-wrap:wrap;padding-block:12px}
.brand{display:flex;align-items:center;gap:10px;margin-right:auto}
.logo{width:34px;height:34px;border-radius:8px;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 55%,#000));display:grid;place-items:center;color:#fff;font-weight:700;font-size:15px;flex:none;box-shadow:var(--shadow)}
.brand h1{font-size:17px;line-height:1.15}
.brand .sub{font-size:11.5px;color:var(--muted);letter-spacing:.02em}
.chip{font-size:11px;padding:4px 9px;border-radius:999px;border:1px solid var(--line);color:var(--ink2);background:var(--surface2);white-space:nowrap}
.chip.ro{color:var(--accent);border-color:color-mix(in srgb,var(--accent) 40%,var(--line));background:var(--accent-soft)}
.tbtn{cursor:pointer;font:inherit;font-size:12px;color:var(--ink2);background:var(--surface2);border:1px solid var(--line);border-radius:8px;padding:6px 10px}
.hero{padding-block:22px 6px}
.eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:600}
.hero h2{font-size:clamp(22px,4.4vw,30px);margin:8px 0 8px;line-height:1.12}
.hero p{margin:0;color:var(--ink2);max-width:66ch;font-size:14.5px}
.wl{margin-top:14px;display:flex;gap:10px;align-items:center;background:var(--accent-soft);border:1px solid color-mix(in srgb,var(--accent) 30%,var(--line));border-radius:10px;padding:10px 13px;font-size:13px;color:var(--ink2);flex-wrap:wrap}
.wl b{color:var(--accent)}
.lens{display:flex;align-items:center;gap:8px;margin-top:14px;flex-wrap:wrap}
.lens .lenslab{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;font-weight:600}
.lens .fbtn{font-size:13px;padding:7px 15px}
.mnote{font-size:12px;color:var(--muted);margin-top:8px;max-width:70ch}
.tiles{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:20px 0}
.tile{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:13px 14px;box-shadow:var(--shadow)}
.tile .k{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em}
.tile .v{font-size:26px;font-weight:600;margin-top:3px;line-height:1}
.tile .m{font-size:11.5px;color:var(--muted);margin-top:4px}
.tile.buy{border-top:3px solid var(--buy)}.tile.buy .v{color:var(--buy)}
.tile.hold{border-top:3px solid var(--hold)}.tile.hold .v{color:var(--hold)}
.tile.sell{border-top:3px solid var(--sell)}.tile.sell .v{color:var(--sell)}
section{margin:26px 0}
.sh{display:flex;align-items:baseline;gap:10px;margin-bottom:12px;flex-wrap:wrap}
.sh h3{font-size:15px}.sh .note{font-size:12px;color:var(--muted)}
.filters{display:flex;gap:8px;flex-wrap:wrap}
.fbtn{cursor:pointer;font:inherit;font-size:12.5px;padding:6px 13px;border-radius:999px;border:1px solid var(--line);background:var(--surface);color:var(--ink2)}
.fbtn[aria-pressed="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.fbtn .dot{display:inline-block;width:7px;height:7px;border-radius:50%;margin-right:5px;vertical-align:middle}
.card{background:var(--surface);border:1px solid var(--line);border-radius:14px;box-shadow:var(--shadow)}
.chart{padding:16px 16px 8px}
.crow{display:grid;grid-template-columns:64px 1fr 46px;align-items:center;gap:10px;padding:2px 0}
.crow .tk{font-size:12px;font-weight:600;text-align:right}
.crow .tk small{display:block;font-weight:400;color:var(--faint);font-size:9px}
.track{position:relative;height:17px;background:var(--surface2);border-radius:5px;overflow:hidden}
.bar{position:absolute;left:0;top:0;bottom:0;border-radius:5px;transition:width .5s cubic-bezier(.2,.7,.2,1)}
.bar.BUY{background:linear-gradient(90deg,color-mix(in srgb,var(--buy) 70%,transparent),var(--buy))}
.bar.HOLD{background:linear-gradient(90deg,color-mix(in srgb,var(--hold) 70%,transparent),var(--hold))}
.bar.SELL{background:linear-gradient(90deg,color-mix(in srgb,var(--sell) 70%,transparent),var(--sell))}
.thr{position:absolute;top:-2px;bottom:-2px;width:1px;background:var(--faint);opacity:.5}
.thr b{position:absolute;top:-14px;left:50%;transform:translateX(-50%);font-size:8px;color:var(--muted);font-weight:400}
.crow .sc{font-size:12.5px;font-weight:600;text-align:right}
.axis{grid-column:2;display:flex;justify-content:space-between;font-size:9px;color:var(--faint);padding-top:4px}
.tblwrap{overflow-x:auto;border-radius:14px;border:1px solid var(--line);background:var(--surface);box-shadow:var(--shadow)}
table{border-collapse:collapse;width:100%;min-width:760px}
th,td{padding:9px 11px;text-align:right;border-bottom:1px solid var(--line);white-space:nowrap}
th{font-size:10.5px;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);font-weight:600;position:sticky;top:calc(env(safe-area-inset-top,0px));background:var(--surface2);cursor:pointer;user-select:none}
th:first-child,td:first-child{text-align:center}
th.l,td.l{text-align:left}
tbody tr{cursor:pointer}tbody tr:hover{background:var(--surface2)}
.rk{color:var(--faint);font-size:12px}
.tkr{font-weight:600;font-size:13px}
.tkr small{display:block;color:var(--muted);font-weight:400;font-size:11px}
.sbadge{display:inline-block;font-size:9px;font-weight:700;color:var(--spec);background:var(--spec-bg);border-radius:4px;padding:1px 4px;margin-left:5px;vertical-align:middle;letter-spacing:.03em}
.pill{font-size:11px;font-weight:600;padding:3px 9px;border-radius:999px;display:inline-block;min-width:52px;text-align:center}
.pill.BUY{color:var(--buy);background:var(--buy-bg)}.pill.HOLD{color:var(--hold);background:var(--hold-bg)}.pill.SELL{color:var(--sell);background:var(--sell-bg)}
.scv{font-weight:600}
.fstrip{display:inline-flex;gap:3px}
.fb{position:relative;width:24px;height:15px;background:var(--surface2);border-radius:3px;overflow:hidden}
.fb i{position:absolute;top:0;bottom:0;left:50%;width:1px;background:var(--faint);opacity:.5}
.fb s{position:absolute;top:2px;bottom:2px;border-radius:2px}
.fb s.p{left:50%;background:var(--pos)}.fb s.n{right:50%;background:var(--neg)}
.pos{color:var(--buy)}.neg{color:var(--sell)}
.rsk{font-size:11px;padding:2px 7px;border-radius:5px;background:var(--surface2);color:var(--ink2)}
.rsk.Alto{color:var(--sell);background:var(--sell-bg)}.rsk.Baixo{color:var(--buy);background:var(--buy-bg)}
.detail td{background:var(--surface2);padding:0}
.dbox{padding:14px 16px;display:grid;grid-template-columns:1.4fr 1fr;gap:16px}
.dbox p{margin:0 0 10px;font-size:13.5px;color:var(--ink2);max-width:60ch}
.plan{display:flex;gap:8px;flex-wrap:wrap;margin-top:6px}
.pchip{background:var(--surface);border:1px solid var(--line);border-radius:8px;padding:6px 10px;font-size:11px}
.pchip .k{color:var(--muted);text-transform:uppercase;font-size:9.5px;letter-spacing:.04em}
.pchip .v{font-weight:600;font-size:13px;margin-top:1px}
.pchip.stop .v{color:var(--sell)}.pchip.t1 .v,.pchip.t2 .v{color:var(--buy)}
.kv{display:grid;grid-template-columns:auto auto;gap:4px 14px;font-size:12px;align-content:start}
.kv .k{color:var(--muted)}.kv .v{text-align:right;font-weight:500}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
.pcard{background:var(--surface);border:1px solid var(--line);border-top:3px solid var(--buy);border-radius:12px;padding:15px;box-shadow:var(--shadow)}
.pcard.spec{border-top-color:var(--spec)}
.pcard .top{display:flex;justify-content:space-between;align-items:flex-start;gap:8px}
.pcard .nm{font-weight:600;font-size:15px}.pcard .nm small{display:block;color:var(--muted);font-weight:400;font-size:11.5px}
.pcard .th{font-size:12.5px;color:var(--ink2);margin:10px 0 12px}
.pcard .lv{display:grid;grid-template-columns:repeat(4,1fr);gap:7px}
.lvl{background:var(--surface2);border-radius:8px;padding:7px 9px}
.lvl .k{font-size:9.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em}
.lvl .v{font-size:13.5px;font-weight:600;margin-top:1px}
.lvl.st .v{color:var(--sell)}.lvl.tg .v{color:var(--buy)}
.controls{display:flex;gap:16px;flex-wrap:wrap;align-items:flex-end;padding:16px 16px 6px}
.controls label{font-size:12px;color:var(--muted);display:flex;flex-direction:column;gap:4px}
.controls input{font:inherit;font-size:15px;font-variant-numeric:tabular-nums;width:130px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface2);color:var(--ink)}
.controls .hint{font-size:11.5px;color:var(--faint);max-width:34ch;line-height:1.4}
.ptoggle{display:flex;gap:8px;padding:0 16px 12px}
.risknote{font-size:11px;color:var(--muted);padding:0 16px 14px}
.meth{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:var(--shadow)}
.wgrid{display:grid;grid-template-columns:repeat(5,1fr);gap:10px;margin:14px 0}
.wcell{background:var(--surface2);border-radius:10px;padding:11px}
.wcell .p{font-size:20px;font-weight:600;color:var(--accent)}.wcell .n{font-size:11.5px;color:var(--ink2);margin-top:2px}
.wcell .d{font-size:10.5px;color:var(--muted);margin-top:3px;line-height:1.35}
details{margin-top:12px;border-top:1px solid var(--line);padding-top:10px}
summary{cursor:pointer;font-weight:600;font-size:13.5px;color:var(--ink2)}
details ul{margin:10px 0 0;padding-left:18px;font-size:13px;color:var(--ink2)}details li{margin:5px 0}
.disc{margin-top:14px;font-size:12px;color:var(--muted);background:var(--sell-bg);border:1px solid color-mix(in srgb,var(--sell) 25%,var(--line));border-radius:10px;padding:12px 14px;line-height:1.5}
.disc b{color:var(--sell)}
footer{color:var(--faint);font-size:11.5px;text-align:center;padding:24px 0 8px;border-top:1px solid var(--line);margin-top:8px}
#tt{position:fixed;pointer-events:none;z-index:50;background:var(--ink);color:var(--surface);font-size:11.5px;padding:7px 9px;border-radius:7px;box-shadow:var(--shadow);opacity:0;transition:opacity .12s;max-width:240px;line-height:1.4}
#tt .h{font-weight:600;margin-bottom:2px}
@media (max-width:820px){.tiles{grid-template-columns:repeat(2,1fr)}.tiles .tile:first-child{grid-column:1/-1}.cards{grid-template-columns:1fr}.wgrid{grid-template-columns:repeat(2,1fr)}.dbox{grid-template-columns:1fr}.pcard .lv{grid-template-columns:repeat(2,1fr)}}
@media (prefers-reduced-motion:reduce){*{transition:none!important}}
</style>

<header><div class="wrap hd">
  <div class="brand"><div class="logo">Q</div>
   <div><h1>Radar Swing Quant</h1><div class="sub mono">Terminal Webull · EUA · 32 ativos</div></div></div>
  <span class="chip ro">● Conta somente leitura</span>
  <span class="chip mono" id="asof"></span>
  <button class="tbtn" id="theme">◐ Tema</button>
</div></header>

<div class="wrap">
 <div class="hero">
  <div class="eyebrow">Análise quantitativa · perfil agressivo / curto prazo</div>
  <h2>Buy · Hold · Sell com stops, alvos e sizing</h2>
  <p>32 ações americanas (mega/large-caps + <b>mid-caps</b> e small-caps de momentum, ~14 setores) pontuadas por um modelo de 5 blocos com peso em momentum, técnico e fluxo. Cada nome traz <b>stop (2×ATR), alvos (múltiplos de R) e tamanho por volatilidade</b>. Clique numa linha para o detalhe.</p>
  <div class="wl">📌 <span><b>Watchlist criada na Webull:</b> “Radar Swing Quant” — BUYs + near-buy + novas de qualidade (MG, HALO, OSCR, PBF…).</span></div>
  <div class="lens" id="lens">
   <span class="lenslab">Modelo / lente:</span>
   <button class="fbtn" data-m="mom" aria-pressed="true">⚡ Momentum (agressivo)</button>
   <button class="fbtn" data-m="qual" aria-pressed="false">◈ Qualidade + recuo</button>
  </div>
  <p class="mnote" id="mnote"></p>
 </div>

 <div class="tiles" id="tiles"></div>

 <section>
  <div class="sh"><h3>Ranking por score composto</h3><span class="note">escala 30–72 · linhas = fronteiras (45 / 55) · ⚠ = especulativo</span></div>
  <div class="filters" id="filters" style="margin-bottom:12px">
   <button class="fbtn" data-f="ALL" aria-pressed="true">Todos <span class="mono">(32)</span></button>
   <button class="fbtn" data-f="BUY" aria-pressed="false"><span class="dot" style="background:var(--buy)"></span>Compra</button>
   <button class="fbtn" data-f="HOLD" aria-pressed="false"><span class="dot" style="background:var(--hold)"></span>Manter</button>
   <button class="fbtn" data-f="SELL" aria-pressed="false"><span class="dot" style="background:var(--sell)"></span>Evitar</button>
  </div>
  <div class="card chart" id="chart"></div>
 </section>

 <section id="plan">
  <div class="sh"><h3>Plano de trade &amp; sizing por volatilidade</h3><span class="note">stop 2×ATR · alvos 2R/3R · ações = risco fixo ÷ distância do stop</span></div>
  <div class="card">
   <div class="controls">
    <label>Tamanho da conta (USD)<input id="acct" type="number" value="10000" min="100" step="500"></label>
    <label>Risco por trade (%)<input id="riskpct" type="number" value="1" min="0.1" max="5" step="0.1"></label>
    <div class="hint">Ações = (Conta × Risco%) ÷ (Entrada − Stop). O “Peso vol” distribui a cesta de compra ∝ 1/ATR% (menor volatilidade → maior peso).</div>
   </div>
   <div class="ptoggle filters" id="planfilter">
    <button class="fbtn" data-pf="BUY" aria-pressed="true">Somente compras</button>
    <button class="fbtn" data-pf="ALL" aria-pressed="false">Todos os 32</button>
   </div>
   <div class="tblwrap" style="border:0;box-shadow:none;border-radius:0">
    <table id="plantbl" style="min-width:820px"><thead><tr>
     <th class="l">Ativo</th><th>Entrada</th><th>Stop 2×ATR</th><th>Stop %</th>
     <th>Alvo 1 · 2R</th><th>Alvo 2 · 3R</th><th>Alvo analistas</th><th>Peso vol</th>
     <th>Ações</th><th>Posição</th><th>% conta</th>
    </tr></thead><tbody id="planbody"></tbody></table>
   </div>
   <div class="risknote">Alvo 1 = 2× o risco (R:R 2:1) · Alvo 2 = 3× (R:R 3:1). “Alvo analistas” é o preço-alvo médio (referência, não gatilho). Invalidação estrutural: fechamento abaixo da SMA50.</div>
  </div>
 </section>

 <section>
  <div class="sh"><h3>Tabela de fatores</h3><span class="note">clique no cabeçalho p/ ordenar · na linha p/ detalhes + plano · sub-scores em z</span></div>
  <div class="tblwrap"><table id="tbl"><thead><tr>
   <th data-s="rank">#</th><th class="l" data-s="t">Ativo</th><th class="l" data-s="sector">Setor</th>
   <th data-s="verdict">Veredito</th><th data-s="score">Score</th><th data-s="mom" id="fth">Fatores (M·T·F·A)</th>
   <th data-s="r21">1M %</th><th data-s="r63">3M %</th><th data-s="rsi">RSI</th>
   <th data-s="upside">Upside %</th><th data-s="atrPct">ATR %</th><th data-s="vol">Risco</th>
  </tr></thead><tbody id="tbody"></tbody></table></div>
 </section>

 <section>
  <div class="sh"><h3>Destaques de compra</h3><span class="note" id="cardhd">os setups do topo · níveis de referência (não são ordens)</span></div>
  <div class="cards" id="cards"></div>
 </section>

 <section><div class="meth">
   <div class="sh" style="margin-bottom:4px"><h3>Metodologia &amp; pesos</h3></div>
   <p style="font-size:13px;color:var(--ink2);margin:6px 0 0;max-width:72ch">Cada fator vira <b>z-score</b> (desvio vs. a média do universo) e é combinado nos pesos abaixo (perfil agressivo/curto prazo). O bloco de analistas é <b>escalado pela confiança da cobertura</b> (menos casas → menos peso), e há penalidade para papéis <i>esticados</i> (acima do alvo + RSI alto), <i>parabólicos</i> (+70% em 3M com RSI quente) e <i>sem fundamento</i>. Score reescalado 0–100.</p>
   <div class="wgrid" id="wgrid"></div>
   <details><summary>Stops, alvos e sizing</summary><ul>
    <li><b>Stop:</b> 2 × ATR(14) abaixo da entrada — adapta-se à volatilidade real de cada papel.</li>
    <li><b>Alvos:</b> múltiplos do risco (R = distância até o stop). Alvo 1 = 2R (R:R 2:1), Alvo 2 = 3R (3:1).</li>
    <li><b>Sizing por risco:</b> nº de ações = (conta × risco%) ÷ (entrada − stop). Risco fixo por trade padroniza a perda máxima.</li>
    <li><b>Sizing por volatilidade (cesta):</b> peso ∝ 1/ATR% entre as compras — a de menor volatilidade recebe a maior fatia.</li>
   </ul></details>
   <details><summary>Como interpretar os vereditos</summary><ul>
    <li><b style="color:var(--buy)">Compra (≥55)</b> — melhor combinação de tendência, fluxo e sentimento; entrar com gestão de risco.</li>
    <li><b style="color:var(--hold)">Manter (45–55)</b> — tese válida sem gatilho de curto prazo; aguardar recuo/confirmação.</li>
    <li><b style="color:var(--sell)">Evitar (&lt;45)</b> — momentum fraco ou esticado/parabólico. Não é recomendação de venda a descoberto.</li>
    <li><b style="color:var(--spec)">⚠ Especulativo</b> — cripto/recém-listada/cobertura fina e sem lucro. Risco elevado mesmo quando pontua bem.</li>
   </ul></details>
   <details><summary>Fontes &amp; ressalvas de dados (Webull)</summary><ul>
    <li>Técnico: candles diários (70 barras) — retornos 1M/3M, SMA 20/50, RSI(14), ATR(14), volatilidade.</li>
    <li>Fluxo: entrada/saída líquida de ordens grandes+médias (3 dias) vs. capitalização.</li>
    <li>Analistas: preço-alvo médio e ratings; <b>SMMT</b> tem alvo publicado em GBP (convertido ~1,26 — conferir).</li>
    <li>Recém-listadas (SECZ, PURR, FRNM, ASST) têm histórico curto e cobertura fina — sinais menos robustos.</li>
   </ul></details>
   <div class="disc"><b>Aviso.</b> Conteúdo analítico/educacional a partir de dados do terminal Webull — <b>não é recomendação de investimento</b>. Conta somente leitura; nenhuma ordem foi ou pode ser enviada. Stops/alvos são referências técnicas, não garantias — gaps podem ultrapassar o stop. Ativos de alta volatilidade e especulativos envolvem risco de perda relevante. Faça sua própria diligência.</div>
 </div></section>
 <footer>Radar Swing Quant · dados: terminal Webull (L1) · 24 ativos · valores em USD · watchlist sincronizada na Webull</footer>
</div>
<div id="tt"></div>

<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap">
<script>
const DATA=__PAYLOAD__;
const $=(s,e=document)=>e.querySelector(s),$$=(s,e=document)=>[...e.querySelectorAll(s)];
const fmt=(x,d=1)=>x==null?"–":(x>0&&d>0?"+":"")+Number(x).toFixed(d);
const usd=x=>"$"+Number(x).toLocaleString("en-US",{maximumFractionDigits:x<10?2:0});
const rows=DATA.rows, byT=t=>rows.find(r=>r.t===t);
const vlabel=v=>({BUY:"Compra",HOLD:"Manter",SELL:"Evitar"})[v];
const FMETA={
 mom:{mom:["Momentum","Retornos 1M/3M + preço vs SMA50"],tech:["Técnico","RSI(14) + preço vs SMA20"],flow:["Fluxo","Ordens grandes+médias líq. (3d)"],anal:["Analistas","Upside + ratings × confiança"],valq:["Valuation","P/E · P/S · EPS (sanidade)"]},
 qual:{qual:["Qualidade","Lucro · valuation sã · rating × cobertura"],pull:["Recuo","RSI 40–58 · perto da SMA20 · ~5–18% off-high"],trend:["Tendência","Preço acima da SMA50 (alta intacta)"],ups:["Upside","Preço-alvo médio dos analistas"],flow:["Fluxo","Ordens grandes+médias líq. (3d)"]}
};
const MODELS={
 mom:{label:"⚡ Momentum (agressivo)",note:"Persegue força de curto prazo: momentum, técnico e fluxo. Ideal para swing agressivo, mas evita nomes esticados/parabólicos.",sc:r=>r.score,vd:r=>r.verdict,rk:r=>r.rank,iv:r=>r.ivw,facts:["mom","tech","flow","anal"],flab:"M·T·F·A",weights:DATA.weights,counts:DATA.counts,buys:DATA.buys},
 qual:{label:"◈ Qualidade + recuo",note:"Compra boas empresas na baixa: prioriza qualidade + tendência de fundo intacta + recuo saudável (não sobrecomprado). Um “quality gate” barra junk, tendência quebrada e parabólicas.",sc:r=>r.scoreq,vd:r=>r.verdictq,rk:r=>r.rankq,iv:r=>r.ivwq,facts:["qual","pull","trend","ups"],flab:"Q·P·T·U",weights:DATA.weightsq,counts:DATA.countsq,buys:DATA.buysq}
};
let MODEL="mom"; const AM=()=>MODELS[MODEL];
const FM=()=>FMETA[MODEL];
const val=(r,k)=> k==="score"?AM().sc(r): k==="rank"?AM().rk(r): k==="verdict"?({BUY:0,HOLD:1,SELL:2})[AM().vd(r)]: r[k];

$("#asof").textContent="Dados: "+DATA.asof;
const semis=rows.filter(r=>r.sector==="Semis").length;
function renderTiles(){const C=AM().counts;$("#tiles").innerHTML=[
 {k:"Universo",v:DATA.n,m:"16 large + 14 mid + 2 small/micro",c:""},
 {k:"Compra",v:C.BUY,m:"setups da lente ativa",c:"buy"},
 {k:"Manter",v:C.HOLD,m:"neutros / aguardar",c:"hold"},
 {k:"Evitar",v:C.SELL,m:MODEL==="mom"?"fracos, esticados ou parabólicos":"sem qualidade ou tendência quebrada",c:"sell"},
 {k:"Especulativos",v:rows.filter(r=>r.spec).length,m:"cripto / recém-listadas",c:""},
].map(t=>`<div class="tile ${t.c}"><div class="k">${t.k}</div><div class="v mono">${t.v}</div><div class="m">${t.m}</div></div>`).join("");}

function renderWeights(){$("#wgrid").innerHTML=Object.entries(AM().weights).map(([k,v])=>`<div class="wcell"><div class="p mono">${Math.round(v*100)}%</div><div class="n">${FM()[k][0]}</div><div class="d">${FM()[k][1]}</div></div>`).join("");}

const CMIN=30,CMAX=72,sx=v=>Math.max(0,Math.min(100,(v-CMIN)/(CMAX-CMIN)*100));
function drawChart(list){
 const el=$("#chart");
 el.innerHTML=list.map(r=>`<div class="crow" data-t="${r.t}">
   <div class="tk">${r.t}${r.spec?'<span class="sbadge">⚠</span>':''}<small>${r.name.length>13?r.name.slice(0,12)+'…':r.name}</small></div>
   <div class="track"><div class="thr" style="left:${sx(45)}%"><b>45</b></div><div class="thr" style="left:${sx(55)}%"><b>55</b></div><div class="bar ${AM().vd(r)}" style="width:${sx(AM().sc(r))}%"></div></div>
   <div class="sc mono ${AM().vd(r)==='BUY'?'pos':AM().vd(r)==='SELL'?'neg':''}">${AM().sc(r).toFixed(1)}</div></div>`).join("")
   +`<div class="crow"><div></div><div class="axis"><span>${CMIN}</span><span>evitar ◂ 45</span><span>55 ▸ compra</span><span>${CMAX}</span></div><div></div></div>`;
 $$(".crow[data-t]",el).forEach(row=>{const r=byT(row.dataset.t);
   row.addEventListener("mousemove",e=>tip(e,`<div class="h">${r.t} · ${r.name}${r.spec?' ⚠':''}</div>Score ${AM().sc(r).toFixed(1)} — <b>${vlabel(AM().vd(r))}</b><br>1M ${fmt(r.r21)}% · 3M ${fmt(r.r63)}% · RSI ${r.rsi}<br>Upside ${fmt(r.upside)}% · dist.máx ${fmt(r.disthi)}%`));
   row.addEventListener("mouseleave",untip);});
}

let sortKey="rank",sortDir=1;
function drawTable(list){
 $("#tbody").innerHTML=list.map(r=>{
  const fs=AM().facts.map(k=>{const z=r[k],w=Math.min(50,Math.abs(z)/2.5*50);return `<span class="fb" data-k="${k}" data-z="${z}"><i></i><s class="${z>=0?'p':'n'}" style="width:${w}%"></s></span>`}).join("");
  return `<tr data-t="${r.t}"><td class="rk mono">${AM().rk(r)}</td>
   <td class="l"><span class="tkr">${r.t}${r.spec?'<span class="sbadge">⚠ ESP</span>':''}<small>${r.name}</small></span></td>
   <td class="l" style="color:var(--muted);font-size:12px">${r.sector}</td>
   <td><span class="pill ${AM().vd(r)}">${vlabel(AM().vd(r))}</span></td>
   <td class="scv mono">${AM().sc(r).toFixed(1)}</td>
   <td><span class="fstrip">${fs}</span></td>
   <td class="mono ${r.r21>=0?'pos':'neg'}">${fmt(r.r21)}</td>
   <td class="mono ${r.r63>=0?'pos':'neg'}">${fmt(r.r63)}</td>
   <td class="mono" style="color:${r.rsi>=78?'var(--sell)':r.rsi>=50?'var(--ink)':'var(--muted)'}">${r.rsi}</td>
   <td class="mono ${r.upside>=0?'pos':'neg'}">${fmt(r.upside)}</td>
   <td class="mono" style="color:var(--muted)">${r.atrPct}</td>
   <td><span class="rsk ${r.risk}">${r.risk}</span></td></tr>`;
 }).join("");
 $$("#tbody tr").forEach(tr=>{const r=byT(tr.dataset.t);
   tr.addEventListener("click",()=>toggleDetail(tr,r));
   $$(".fb",tr).forEach(fb=>{fb.addEventListener("mousemove",e=>{e.stopPropagation();tip(e,`<div class="h">${FM()[fb.dataset.k][0]}</div>z = ${fmt(+fb.dataset.z,2)}<br><span style="color:var(--faint)">${FM()[fb.dataset.k][1]}</span>`)});fb.addEventListener("mouseleave",untip)});
 });
}
function toggleDetail(tr,r){
 const nx=tr.nextElementSibling;
 if(nx&&nx.classList.contains("detail")){nx.remove();return}
 $$(".detail").forEach(d=>d.remove());
 const tr2=document.createElement("tr");tr2.className="detail";
 tr2.innerHTML=`<td colspan="12"><div class="dbox">
   <div><p>${r.thesis}</p>
     <div class="plan">
       <div class="pchip"><div class="k">Entrada ref.</div><div class="v mono">$${r.price}</div></div>
       <div class="pchip stop"><div class="k">Stop 2×ATR</div><div class="v mono">$${r.stop} <span style="font-size:10px">(${r.stopPct}%)</span></div></div>
       <div class="pchip t1"><div class="k">Alvo 1 · 2R</div><div class="v mono">$${r.t1} <span style="font-size:10px">(+${r.t1pct}%)</span></div></div>
       <div class="pchip t2"><div class="k">Alvo 2 · 3R</div><div class="v mono">$${r.t2} <span style="font-size:10px">(+${r.t2pct}%)</span></div></div>
       <div class="pchip"><div class="k">Recuo SMA20</div><div class="v mono">$${r.sma20}</div></div>
     </div></div>
   <div class="kv">
     <span class="k">SMA20 / SMA50</span><span class="v mono">${r.sma20} / ${r.sma50}</span>
     <span class="k">Dist. máx 52s</span><span class="v mono">${fmt(r.disthi)}%</span>
     <span class="k">RSI(14) · ATR%</span><span class="v mono">${r.rsi} · ${r.atrPct}%</span>
     <span class="k">Volat. anual.</span><span class="v mono">${r.vol}%</span>
     <span class="k">Upside alvo</span><span class="v mono">${fmt(r.upside)}%${r.gbp?' *GBP':''}</span>
     <span class="k">Analistas (cob.)</span><span class="v mono">${r.cov}</span>
     <span class="k">Fluxo líq. 3d</span><span class="v mono">$${(r.net/1000).toFixed(2)}B</span>
     <span class="k">P/E · P/S</span><span class="v mono">${r.pe==null?'–':r.pe} · ${r.ps==null?'–':r.ps}</span>
     <span class="k">Cap. mercado</span><span class="v mono">$${r.mcap>=1000?(r.mcap/1000).toFixed(2)+'T':r.mcap.toFixed(1)+'B'}</span>
     <span class="k">Momentum / Qualidade</span><span class="v mono">${r.score.toFixed(0)} ${vlabel(r.verdict)[0]} · ${r.scoreq.toFixed(0)} ${vlabel(r.verdictq)[0]}</span>
   </div></div></td>`;
 tr.after(tr2);
}

// cards
function renderCards(){const bs=AM().buys.map(t=>byT(t));
 $("#cardhd").textContent = MODEL==="mom" ? "os setups de momentum mais fortes · níveis de referência" : "boas empresas em recuo (compra na baixa) · níveis de referência";
 $("#cards").innerHTML=bs.map(r=>`
 <div class="pcard ${r.spec?'spec':''}"><div class="top">
   <div class="nm">${r.t}${r.spec?'<span class="sbadge">⚠ ESP</span>':''}<small>${r.name} · ${r.sector}</small></div>
   <span class="pill BUY">Compra</span></div>
   <div class="th">${r.thesis}</div>
   <div class="lv">
     <div class="lvl"><div class="k">Entrada</div><div class="v mono">$${r.price}</div></div>
     <div class="lvl st"><div class="k">Stop</div><div class="v mono">$${r.stop}</div></div>
     <div class="lvl tg"><div class="k">Alvo 1</div><div class="v mono">$${r.t1}</div></div>
     <div class="lvl"><div class="k">Peso vol</div><div class="v mono">${AM().iv(r)}%</div></div>
   </div></div>`).join("")||'<div style="padding:16px;color:var(--muted);font-size:13px">Nenhuma compra nesta lente no momento.</div>';}

// plan table
let planFilter="BUY";
function drawPlan(){
 const acct=Math.max(1,+$("#acct").value||0), rp=Math.max(0,+$("#riskpct").value||0)/100;
 const list=(planFilter==="BUY"?rows.filter(r=>AM().vd(r)==='BUY'):rows.slice().sort((a,b)=>AM().sc(b)-AM().sc(a)));
 $("#planbody").innerHTML=list.map(r=>{
   const rpsh=r.price-r.stop, sh=rpsh>0?Math.floor(acct*rp/rpsh):0, posv=sh*r.price, posp=acct>0?posv/acct*100:0;
   const over=posp>30;
   return `<tr>
     <td class="l"><span class="tkr" style="font-size:12px">${r.t}${r.spec?'<span class="sbadge">⚠</span>':''}</span> <span class="pill ${AM().vd(r)}" style="min-width:0;font-size:9.5px;padding:2px 6px">${vlabel(AM().vd(r))}</span></td>
     <td class="mono">$${r.price}</td>
     <td class="mono neg">$${r.stop}</td>
     <td class="mono neg">-${r.stopPct}%</td>
     <td class="mono pos">$${r.t1}</td>
     <td class="mono pos">$${r.t2}</td>
     <td class="mono" style="color:var(--muted)">$${r.target}</td>
     <td class="mono">${AM().iv(r)>0?AM().iv(r)+'%':'–'}</td>
     <td class="mono" style="font-weight:600">${sh.toLocaleString('en-US')}</td>
     <td class="mono">${usd(posv)}</td>
     <td class="mono" style="color:${over?'var(--sell)':'var(--ink2)'}">${posp.toFixed(1)}%${over?' ⚠':''}</td></tr>`;
 }).join("");
}
$("#acct").addEventListener("input",drawPlan);$("#riskpct").addEventListener("input",drawPlan);
$$("#planfilter .fbtn").forEach(b=>b.addEventListener("click",()=>{planFilter=b.dataset.pf;$$("#planfilter .fbtn").forEach(x=>x.setAttribute("aria-pressed",x===b));drawPlan()}));

// main filters + sort
let filter="ALL";
function apply(){
 renderTiles();renderWeights();renderCards();
 const fth=$("#fth"); if(fth){fth.textContent="Fatores ("+AM().flab+")"; fth.dataset.s=AM().facts[0];}
 const base=filter==="ALL"?rows:rows.filter(r=>AM().vd(r)===filter);
 const list=base.slice().sort((a,b)=>(val(a,sortKey)>val(b,sortKey)?1:-1)*sortDir);
 drawChart(base.slice().sort((a,b)=>AM().sc(b)-AM().sc(a)));
 drawTable(list);drawPlan();
}
$$("#filters .fbtn").forEach(b=>b.addEventListener("click",()=>{filter=b.dataset.f;$$("#filters .fbtn").forEach(x=>x.setAttribute("aria-pressed",x===b));apply()}));
$$("#tbl th").forEach(th=>th.addEventListener("click",()=>{const k=th.dataset.s;if(k===sortKey)sortDir*=-1;else{sortKey=k;sortDir=(k==="t"||k==="sector"||k==="rank")?1:-1}apply()}));

const tt=$("#tt");
function tip(e,html){tt.innerHTML=html;tt.style.opacity=1;let x=e.clientX+14,y=e.clientY+14;if(x>innerWidth-250)x=e.clientX-250;tt.style.left=x+"px";tt.style.top=y+"px"}
function untip(){tt.style.opacity=0}
$("#mnote").textContent=MODELS[MODEL].note;
$$("#lens .fbtn").forEach(b=>b.addEventListener("click",()=>{
 MODEL=b.dataset.m;$$("#lens .fbtn").forEach(x=>x.setAttribute("aria-pressed",x===b));
 $("#mnote").textContent=MODELS[MODEL].note;
 $$(".detail").forEach(d=>d.remove());
 sortKey="rank";sortDir=1;apply();
}));
$("#theme").addEventListener("click",()=>{const cur=document.documentElement.getAttribute("data-theme");const dark=cur?cur==="dark":matchMedia("(prefers-color-scheme:dark)").matches;document.documentElement.setAttribute("data-theme",dark?"light":"dark")});

apply();
</script>'''
HTML=HTML.replace("__PAYLOAD__",payload)
open("/home/user/Claude/dashboard.html","w").write(HTML)
print("written",len(HTML))
