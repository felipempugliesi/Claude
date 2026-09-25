#!/usr/bin/env python3
"""Radar Swing Quant — scoring pipeline (data-driven).
Reads data/radar_data.json (fetched layer) + data/meta.json (static config);
computes technicals, both models (Momentum / Qualidade+Recuo) and the trade plan;
writes data/radar_scored.json. No hardcoded market data, no absolute paths.
"""
import json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
def load(name): return json.load(open(os.path.join(DATA, name), encoding="utf-8"))

RD = load("radar_data.json")
META = load("meta.json")
snapD, tgt, rat, cf, BARS = RD["snap"], RD["tgt"], RD["rat"], RD["cf"], RD["bars"]
gbp_flag = set(META.get("gbp", []))
names = {t: META["meta"][t]["name"] for t in META["tickers"]}
sectors = {t: META["meta"][t]["sector"] for t in META["tickers"]}
syms = [t for t in META["tickers"] if t in snapD and t in BARS]

# ---------- technicals ----------
def sma(x, n): return sum(x[:n]) / n if len(x) >= n else (sum(x) / len(x) if x else None)
def rsi(co, n=14):
    if len(co) < n + 1: return None
    g = []; l = []
    for i in range(1, len(co)):
        c = co[i] - co[i - 1]; g.append(max(c, 0)); l.append(max(-c, 0))
    ag = sum(g[:n]) / n; al = sum(l[:n]) / n
    for i in range(n, len(g)):
        ag = (ag * (n - 1) + g[i]) / n; al = (al * (n - 1) + l[i]) / n
    if al == 0: return 100.0
    return 100 - 100 / (1 + ag / al)
def stdev(x):
    if len(x) < 2: return 0
    m = sum(x) / len(x); return (sum((v - m) ** 2 for v in x) / len(x)) ** .5
def atr(bars, n=14):
    b = bars[:n + 1]
    if len(b) < 2: return None
    trs = []
    for i in range(len(b) - 1):
        h = float(b[i]["high"]); lo = float(b[i]["low"]); pc = float(b[i + 1]["close"])
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    return sum(trs) / len(trs)

tech = {}
for s in syms:
    bars = BARS[s]                       # newest-first
    cn = [float(b["close"]) for b in bars]
    n = len(cn); price = cn[0]
    def ret(k): return (price / cn[k] - 1) * 100 if n > k else None
    r21 = ret(21); r63 = ret(63) if n > 63 else ret(n - 1)
    s20 = sma(cn, 20); s50 = sma(cn, 50)
    dr = [cn[i] / cn[i + 1] - 1 for i in range(min(20, n - 1))]
    a = atr(bars, 14)
    tech[s] = dict(price=round(price, 2),
        r21=round(r21, 1) if r21 is not None else 0, r63=round(r63, 1) if r63 is not None else 0,
        sma20=round(s20, 2) if s20 else price, sma50=round(s50, 2) if s50 else price,
        px20=round((price / s20 - 1) * 100, 1) if s20 else 0, px50=round((price / s50 - 1) * 100, 1) if s50 else 0,
        rsi=round(rsi(cn[::-1], 14), 1) if rsi(cn[::-1], 14) is not None else 50,
        vol=round(stdev(dr) * (252 ** .5) * 100, 1), atr=round(a, 3) if a else round(price * 0.03, 3), bars=n)

# ---------- assemble rows ----------
rows = {}
for s in syms:
    t = tech[s]; sp = snapD[s]; price = t["price"]
    up = (tgt[s] / price - 1) * 100
    sb, b, h, sell, un, num = rat[s]
    bull = (sb + 0.5 * b - 0.5 * sell - un) / num if num else 0
    net = sum((d[0] - d[1]) + (d[2] - d[3]) for d in cf[s]) if cf.get(s) else 0
    netr = net / (sp["mcap"] * 1000) if sp["mcap"] else 0
    rows[s] = dict(price=price, r21=t["r21"], r63=t["r63"], px20=t["px20"], px50=t["px50"], rsi=t["rsi"],
        vol=t["vol"], atr=t["atr"], upside=up, bull=bull, net=net, netr=netr,
        disthi=(price / sp["hi"] - 1) * 100, pe=sp["pe"], ps=sp["ps"], eps=sp["eps"], yld=sp["yld"],
        mcap=sp["mcap"], sec=sectors[s], name=names[s], sma20=t["sma20"], sma50=t["sma50"], bars=t["bars"])

def z(vals):
    m = sum(vals) / len(vals); sd = stdev(vals) or 1
    return [(v - m) / sd for v in vals]
def zmap(key):
    zz = z([rows[s][key] for s in syms]); return {s: zz[i] for i, s in enumerate(syms)}
zr21 = zmap("r21"); zr63 = zmap("r63"); zpx50 = zmap("px50"); zpx20 = zmap("px20")
zup = zmap("upside"); zbull = zmap("bull"); znf = zmap("netr")

# ============ MODEL A: MOMENTUM (aggressive) ============
def rsi_score(r):
    if r >= 78: return -1.5 - (r - 78) * 0.05
    if r >= 50: return 1.0 - abs(r - 61) / 15.0
    return (r - 50) / 12.0
zr = z([rsi_score(rows[s]["rsi"]) for s in syms]); zrsi = {s: zr[i] for i, s in enumerate(syms)}
def valq(s):
    r = rows[s]; sc = 0
    sc += -1.0 if (r["eps"] is None or r["eps"] < 0) else 0.3
    if r["ps"] is not None:
        sc += -1.2 if r["ps"] > 30 else (-0.5 if r["ps"] > 15 else 0)
    if r["pe"] is not None and 0 < r["pe"] < 30: sc += 0.5
    return sc
zv = z([valq(s) for s in syms]); zvq = {s: zv[i] for i, s in enumerate(syms)}
W = {"mom": 0.35, "tech": 0.25, "flow": 0.15, "anal": 0.20, "valq": 0.05}
comp = {}; blocks = {}
for s in syms:
    mom = 0.45 * zr21[s] + 0.35 * zr63[s] + 0.20 * zpx50[s]
    tb = 0.55 * zrsi[s] + 0.45 * zpx20[s]
    conf = min(1.0, rat[s][5] / 10.0)
    an = conf * (0.6 * zup[s] + 0.4 * zbull[s]); vq = zvq[s]
    c = W["mom"] * mom + W["tech"] * tb + W["flow"] * znf[s] + W["anal"] * an + W["valq"] * vq
    r = rows[s]; pen = 0
    if r["upside"] < 0 and r["rsi"] > 72: pen -= 0.45
    if r["rsi"] > 82: pen -= 0.25
    if r["r63"] > 70 and r["rsi"] > 72: pen -= 0.30
    if (r["eps"] is None or r["eps"] < 0) and r["mcap"] < 4 and (r["ps"] is None or r["ps"] > 25): pen -= 0.20
    comp[s] = c + pen
    blocks[s] = dict(mom=round(mom, 2), tech=round(tb, 2), flow=round(znf[s], 2), anal=round(an, 2), valq=round(vq, 2), pen=round(pen, 2))
def to100(c): return round(max(0, min(100, 50 + c * 22)), 1)
score = {s: to100(comp[s]) for s in syms}
def verdict(x): return "BUY" if x >= 55 else ("HOLD" if x >= 45 else "SELL")

# ============ MODEL B: QUALIDADE + RECUO ============
def clamp(x, a, b): return max(a, min(b, x))
def quality_raw(s):
    r = rows[s]; q = 0.0; conf = min(1.0, rat[s][5] / 10.0)
    q += 1.2 if (r["eps"] is not None and r["eps"] > 0) else -1.2
    pe = r["pe"]
    if pe is None or pe < 0: q -= 0.6
    elif 8 <= pe <= 35: q += 0.8
    elif 0 < pe < 8: q += 0.3
    elif pe > 80: q -= 0.8
    ps = r["ps"]
    if ps is not None:
        q += 0.5 if ps < 6 else (-0.8 if ps > 20 else (-0.3 if ps > 10 else 0))
    if r["yld"] > 0: q += 0.3
    m = r["mcap"]; q += 0.5 if m >= 50 else (0.2 if m >= 5 else (-0.5 if m < 1 else 0))
    q += r["bull"] * conf * 0.8
    return q
def pullback_raw(s):
    r = rows[s]; p = 0.0; rsi = r["rsi"]
    if 40 <= rsi <= 58: p += 1.0 - abs(rsi - 48) / 18.0
    elif rsi < 40: p -= (40 - rsi) / 15.0
    else: p -= (rsi - 58) / 12.0
    x = r["px20"]
    if -7 <= x <= 2: p += 0.8
    elif x > 2: p -= clamp((x - 2) / 8.0, 0, 1.2)
    else: p -= clamp((-7 - x) / 8.0, 0, 1.0)
    d = r["disthi"]
    if -20 <= d <= -3: p += 0.9
    elif d > -3: p -= 0.8
    else: p -= clamp((-20 - d) / 20.0, 0, 1.2)
    mm = r["r21"]
    if -8 <= mm <= 10: p += 0.5
    elif mm > 10: p -= clamp((mm - 10) / 20.0, 0, 1.0)
    else: p -= clamp((-8 - mm) / 15.0, 0, 0.8)
    return p
qz = z([quality_raw(s) for s in syms]); pz = z([pullback_raw(s) for s in syms])
tz = z([clamp(rows[s]["px50"], -25, 25) for s in syms])
uz = z([rows[s]["upside"] * min(1.0, rat[s][5] / 10.0) for s in syms])
zQ = {s: qz[i] for i, s in enumerate(syms)}; zP = {s: pz[i] for i, s in enumerate(syms)}
zT = {s: tz[i] for i, s in enumerate(syms)}; zU = {s: uz[i] for i, s in enumerate(syms)}
WQ = {"qual": 0.30, "pull": 0.30, "trend": 0.15, "ups": 0.20, "flow": 0.05}
compq = {}; blocksq = {}
for s in syms:
    c = WQ["qual"] * zQ[s] + WQ["pull"] * zP[s] + WQ["trend"] * zT[s] + WQ["ups"] * zU[s] + WQ["flow"] * znf[s]
    compq[s] = c
    blocksq[s] = dict(qual=round(zQ[s], 2), pull=round(zP[s], 2), trend=round(zT[s], 2), ups=round(zU[s], 2), flow=round(znf[s], 2))
scoreq = {s: to100(compq[s]) for s in syms}
def verdictq(s):
    v = "BUY" if scoreq[s] >= 55 else ("HOLD" if scoreq[s] >= 45 else "SELL")
    r = rows[s]; isspec = r["sec"] in ("Cripto", "Gestão/Cripto") or r["mcap"] < 0.4
    if v == "BUY" and ((r["eps"] is None or r["eps"] <= 0) or isspec or r["px50"] < -3 or r["disthi"] < -30 or r["rsi"] > 68):
        v = "HOLD"
    return v

# ---------- trade plan + flags ----------
for s in syms:
    r = rows[s]; a = r["atr"]; price = r["price"]; R = 2 * a
    r["stop"] = round(price - R, 2); r["stopPct"] = round(R / price * 100, 1)
    r["t1"] = round(price + 2 * R, 2); r["t2"] = round(price + 3 * R, 2)
    r["t1pct"] = round(2 * R / price * 100, 1); r["t2pct"] = round(3 * R / price * 100, 1)
    r["atrPct"] = round(a / price * 100, 1); r["target"] = round(tgt[s], 2)
    r["score"] = score[s]; r["verdict"] = verdict(score[s]); r["blocks"] = blocks[s]
    r["scoreq"] = scoreq[s]; r["verdictq"] = verdictq(s); r["blocksq"] = blocksq[s]
    r["disthi"] = round(r["disthi"], 1); r["upside"] = round(r["upside"], 1); r["bull"] = round(r["bull"], 2); r["net"] = round(r["net"], 0)
    r["gbp"] = s in gbp_flag
    r["risk"] = "Alto" if r["atrPct"] >= 6 else ("Médio" if r["atrPct"] >= 3.5 else "Baixo")
    r["cov"] = rat[s][5]
    _un = (r["eps"] is None or r["eps"] < 0); _pe = r["pe"]
    r["spec"] = (r["sec"] in ("Cripto", "Gestão/Cripto") or r["mcap"] < 0.4
                 or (r["mcap"] < 3 and _un) or (rat[s][5] < 6 and (_un or _pe is None or _pe > 60)))

def ivw(buyset):
    inv = sum(1 / rows[s]["atrPct"] for s in buyset) if buyset else 1
    return {s: round((1 / rows[s]["atrPct"]) / inv * 100, 1) if s in buyset else 0 for s in syms}
buys = [s for s in syms if rows[s]["verdict"] == "BUY"]; iw = ivw(buys)
buysq = [s for s in syms if rows[s]["verdictq"] == "BUY"]; iwq = ivw(buysq)
for s in syms: rows[s]["ivw"] = iw[s]; rows[s]["ivwq"] = iwq[s]

order = sorted(syms, key=lambda s: comp[s], reverse=True)
orderq = sorted(syms, key=lambda s: compq[s], reverse=True)
out = {"asof": RD.get("asof", ""), "order": order, "orderq": orderq,
       "rows": {s: rows[s] for s in syms}, "weights": W, "weightsq": WQ,
       "thesis": META.get("thesis", {})}
json.dump(out, open(os.path.join(DATA, "radar_scored.json"), "w"), ensure_ascii=False)
print(f"scored {len(syms)} tickers  |  A-BUY:", [s for s in order if rows[s]['verdict'] == 'BUY'],
      " |  B-BUY:", [s for s in orderq if rows[s]['verdictq'] == 'BUY'])
