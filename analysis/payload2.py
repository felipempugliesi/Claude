import json
BASE="/tmp/claude-0/-home-user-Claude/acfda38c-f805-5d0e-9f01-51d2c4d57305/scratchpad/"
f=json.load(open(BASE+"full24.json")); D=f["rows"]; order=f["order"]
th={
"SMTC":"Compra de maior qualidade do grupo: +48% no mês rompendo máxima de 52s, 15 analistas (14 compra), fluxo ok. Vol. alta — respeite o sizing.",
"AMD":"Semis em aceleração; RSI 65 saudável, acima das médias 20/50 e forte fluxo institucional. Aguardar leve recuo p/ entrada de menor risco.",
"MU":"Memória em ciclo forte: fluxo comprador pesado e upside +49% ao alvo; EPS_TTM robusto. Correção de 3M digerida — quase-compra.",
"META":"+22% no mês e acima das médias; ruído de saída institucional pontual. Fundamento sólido (P/E 25). Watch p/ rompimento.",
"INTC":"Reviravolta especulativa: +17% no mês com fluxo forte, mas -19% em 3M, prejuízo e 32/49 em 'hold'. Trade tático, não tese.",
"NVDA":"Bellwether consolidando: momentum curto esfriou (RSI 54), mas upside +47% e ratings excepcionais. Comprar em recuo às médias.",
"PLTR":"Momentum de médio prazo (+38% 3M) travado no curto; valuation extremo (P/S 69). Segurar.",
"GOOGL":"O mais barato do grupo (P/E 17,6) e com fluxo comprador, mas curto lateral. Núcleo/segurar.",
"HAFN":"Shipping esticado (RSI 86) e já no alvo. Dividendo ~11% atrai, mas não perseguir — aguardar recuo.",
"TSM":"Tendência intacta, upside +27%, mas momentum curto morno. Núcleo, não gatilho de swing.",
"AAPL":"Perto da máxima mas SEM upside (acima do alvo) e ratings mistos. Evitar entrada nova.",
"TSLA":"Sem tendência (-9% 3M), consenso morno (20 'hold'). Fluxo entrou, setup fraco.",
"ORCL":"Quebrou: -20% em 3M, ~45% da máxima. Analistas veem +61% (valor?), mas p/ swing é faca caindo.",
"TWST":"+91% em 3M e ~34% ACIMA do alvo, prejuízo, P/S 24. Exagero — realizar/não perseguir.",
"AVGO":"Elo fraco dos semis: abaixo da SMA50, RSI 46, sem momentum. Upside de alvo não compensa a fraqueza.",
"TRMD":"Shipping esticado (RSI 80) e acima do alvo. Div. 11,6% e P/E 6 são valor, não swing.",
"CVI":"Refino disparou (+96% 3M) mas RSI 81 e ~38% ACIMA do alvo, com analistas negativos (3 sell/0 buy). Rally esticado — evitar chase.",
"SDGR":"Software de fármacos com IA; +84% em 3M e RSI 77 (esticado). Analistas gostam (5 SB) mas preço passou o alvo. Aguardar recuo.",
"SMMT":"Biotech: +30% 3M, upside ~+52% (alvo em GBP — conferir). 10 SB, mas -39% da máxima. Especulativo/binário (pipeline).",
"ODD":"Consumo/beauty-tech: bounce +39% mas -72% da máxima histórica; analistas negativos (alvo -18%). Repique técnico.",
"FRNM":"Diagnóstico recém-listado na máxima; 5 casas strong buy. Cobertura fina e sem lucro — momentum de IPO, risco alto.",
"SECZ":"ESPECULATIVA: fintech de tokenização (+80% no mês) rompendo com fluxo comprador. Recém-listada, P/E 109, cobertura fina — momentum com stop curto.",
"ASST":"Cripto/gestão parabólica (+102% 3M, RSI 79) e sem fundamento (P/S 290, prejuízo). Exagero — evitar.",
"PURR":"ESPECULATIVA pura: cripto-treasury (Hyperliquid) na máxima; momentum forte, analistas veem +58%. Aposta alavancada em cripto — sizing pequeno e stop rígido.",
"HALO":"Biopharma de royalties/entrega de fármacos, LUCRATIVA (P/E 34) e na máxima de 52s. Mas o preço já passou o alvo médio e o fluxo saiu no dia forte — qualidade com entrada esticada.",
"DBX":"Software lucrativo e barato (P/E 16), porém momentum curto fraco, ratings mornos (4 hold) e acima do alvo. Segurar/observar, não comprar aqui.",
"OSCR":"Health insurance que virou lucrativa (+200% da mínima), P/S 0,65 e upside +10%. Mas o curto prazo travou (1M ~0%) — qualidade aguardando novo gatilho.",
"TXG":"Ferramentas de genômica: +120% em 3M (parabólica) e ~32% ACIMA do alvo, sem lucro. Momentum forte mas esticado — evitar perseguir.",
"IOVA":"Terapia celular: +162% em 3M e já no alvo, sem lucro (biotech binário). Momentum especulativo e esticado — não é entrada de qualidade.",
"PBF":"Refino deep-value (P/E 6,9, P/S 0,27) e +108% em 3M, mas ratings negativos (3 sell/9 hold) e acima do alvo. Valor cíclico esticado, não swing limpo.",
"MG":"SMALL-CAP DE QUALIDADE: testes/inspeção industrial, lucrativa (P/E 25), na máxima de 52s, upside +11%. Cobertura mínima (1 casa) e float pequeno — monitorar recuo p/ entrada.",
"INFU":"⚠ MICRO-CAP: serviços de infusão, lucrativa (P/E 31) e maior upside da lista (+31%). Baixa liquidez e spread largo — só ordem limitada e posição pequena.",
}
orderq=f["orderq"]; rankq={s:i+1 for i,s in enumerate(orderq)}
rows=[]
for i,s in enumerate(order):
    d=D[s]
    rows.append({"rank":i+1,"t":s,"name":d["name"],"sector":d["sec"],"verdict":d["verdict"],
      "score":d["score"],"mom":d["blocks"]["mom"],"tech":d["blocks"]["tech"],"flow":d["blocks"]["flow"],
      "anal":d["blocks"]["anal"],"valq":d["blocks"]["valq"],"r21":d["r21"],"r63":d["r63"],"rsi":d["rsi"],
      "upside":round(d["upside"],1),"bull":round(d["bull"],2),"vol":d["vol"],"risk":d["risk"],"spec":d["spec"],
      "cov":d["cov"],"gbp":d["gbp"],"price":d["price"],"sma20":d["sma20"],"sma50":d["sma50"],
      "disthi":round(d["disthi"],1),"pe":d["pe"],"ps":d["ps"],"eps":d["eps"],"yld":d["yld"],"mcap":d["mcap"],
      "net":round(d["net"],0),"atr":d["atr"],"atrPct":d["atrPct"],"stop":d["stop"],"stopPct":d["stopPct"],
      "t1":d["t1"],"t2":d["t2"],"t1pct":d["t1pct"],"t2pct":d["t2pct"],"ivw":d["ivw"],"target":None,
      "rankq":rankq[s],"scoreq":d["scoreq"],"verdictq":d["verdictq"],
      "qual":d["blocksq"]["qual"],"pull":d["blocksq"]["pull"],"trend":d["blocksq"]["trend"],"ups":d["blocksq"]["ups"],
      "ivwq":d["ivwq"],"thesis":th[s]})
# analyst mean target for reference line
tgt={"NVDA":327.7,"AMD":616.5,"INTC":116.37,"MU":1513.1,"TSM":552.26,"AVGO":531.85,"META":755.28,"GOOGL":428.16,"AAPL":328.22,"ORCL":237.97,"PLTR":196.84,"TSLA":396.94,"SMTC":209.29,"TWST":109.58,"HAFN":10.25,"TRMD":36.5,"CVI":33.4,"SDGR":21.43,"SMMT":27.2,"ODD":14.93,"FRNM":18.0,"SECZ":11.8,"ASST":29.4,"PURR":22.3,"HALO":99.56,"DBX":32.6,"OSCR":35.4,"TXG":52.13,"IOVA":10.22,"PBF":72.54,"MG":23.0,"INFU":16.83}
for r in rows: r["target"]=tgt[r["t"]]
counts={v:sum(1 for r in rows if r["verdict"]==v) for v in ["BUY","HOLD","SELL"]}
countsq={v:sum(1 for r in rows if r["verdictq"]==v) for v in ["BUY","HOLD","SELL"]}
buys=[r["t"] for r in rows if r["verdict"]=="BUY"]
buysq=[r["t"] for r in sorted(rows,key=lambda x:x["scoreq"],reverse=True) if r["verdictq"]=="BUY"]
payload={"rows":rows,"counts":counts,"countsq":countsq,"weights":f["weights"],"weightsq":f["weightsq"],
  "asof":"18 set 2026 (fechamento)","n":len(rows),"buys":buys,"buysq":buysq}
open(BASE+"payload2.json","w").write(json.dumps(payload,ensure_ascii=False))
print("n",len(rows),"counts",counts,"buys",buys,"bytes",len(json.dumps(payload,ensure_ascii=False)))
