#!/usr/bin/env python3
"""Assemble data/radar_data.json from raw Webull tool outputs in data/raw/.
Each field falls back to the PREVIOUS radar_data.json when its raw file is
missing/incomplete (graceful degradation). Prints a validation report.

Expected raw files (drop the tool outputs verbatim):
  data/raw/snapshot.json        -> list returned by get_stock_snapshot (all tickers)
  data/raw/bars/*.json          -> each get_stock_bars result object {"result":[{symbol,result:[...]}]}
  data/raw/analyst_target.json  -> list of get_analyst_target_price objects
  data/raw/analyst_rating.json  -> list of get_analyst_rating objects
  data/raw/capital_flow.json    -> {TICKER: <3-element list from get_stock_capital_flow>}
  data/raw/asof.txt             -> optional label, e.g. "19 set 2026 (fechamento)"
"""
import json, os, glob
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data"); RAW = os.path.join(DATA, "raw")
def jload(path, default=None):
    try: return json.load(open(path, encoding="utf-8"))
    except Exception: return default
def f(x):
    try: return float(x)
    except Exception: return None

META = jload(os.path.join(DATA, "meta.json"), {})
TICK = META.get("tickers", []); GBP = set(META.get("gbp", []))
GBP_USD = 1.26  # SMMT & co. publish targets in GBP
PREV = jload(os.path.join(DATA, "radar_data.json"), {}) or {}
prev = lambda k: PREV.get(k, {}) or {}

# ---- snapshot ----
snap = dict(prev("snap"))
for it in (jload(os.path.join(RAW, "snapshot.json"), []) or []):
    s = it.get("symbol")
    if not s: continue
    mv = f(it.get("market_value"))
    snap[s] = {"pe": f(it.get("pe_ratio")), "ps": f(it.get("ps_ratio")), "eps": f(it.get("eps_ttm")),
               "yld": round((f(it.get("yield")) or 0) * 100, 4), "hi": f(it.get("fifty_two_wk_high")),
               "lo": f(it.get("fifty_two_wk_low")), "mcap": round(mv / 1e9, 4) if mv else None}

# ---- bars ----
bars = dict(prev("bars"))
for path in sorted(glob.glob(os.path.join(RAW, "bars", "*.json"))):
    obj = jload(path)
    if not obj: continue
    for entry in obj.get("result", obj if isinstance(obj, list) else []):
        if entry.get("symbol") and entry.get("result"): bars[entry["symbol"]] = entry["result"]

# ---- analyst target (GBP -> USD where flagged) ----
tgt = dict(prev("tgt"))
for it in (jload(os.path.join(RAW, "analyst_target.json"), []) or []):
    s = it.get("symbol"); m = f(it.get("mean"))
    if s and m is not None: tgt[s] = round(m * (GBP_USD if s in GBP else 1), 4)

# ---- analyst rating ----
rat = dict(prev("rat"))
for it in (jload(os.path.join(RAW, "analyst_rating.json"), []) or []):
    s = it.get("symbol")
    if s: rat[s] = [int(it.get(k, 0)) for k in ("strong_buy", "buy", "hold", "sell", "under_perform", "number")]

# ---- capital flow ($ -> $M) ----
cf = dict(prev("cf"))
for s, days in (jload(os.path.join(RAW, "capital_flow.json"), {}) or {}).items():
    try:
        cf[s] = [[round(f(d["large_in"]) / 1e6, 4), round(f(d["large_out"]) / 1e6, 4),
                  round(f(d["medium_in"]) / 1e6, 4), round(f(d["medium_out"]) / 1e6, 4)] for d in days]
    except Exception: pass

asof = (jload(os.path.join(RAW, "asof.txt")) if False else None)
try: asof = open(os.path.join(RAW, "asof.txt"), encoding="utf-8").read().strip()
except Exception: asof = PREV.get("asof", "")

order = [t for t in TICK] or sorted(snap.keys())
RD = {"asof": asof, "tickers": order, "snap": {t: snap[t] for t in order if t in snap},
      "tgt": {t: tgt[t] for t in order if t in tgt}, "rat": {t: rat[t] for t in order if t in rat},
      "cf": {t: cf[t] for t in order if t in cf}, "bars": {t: bars[t] for t in order if t in bars}}
json.dump(RD, open(os.path.join(DATA, "radar_data.json"), "w"), ensure_ascii=False)

# ---- validation ----
def miss(d): return [t for t in order if t not in d]
report = {"snap": miss(RD["snap"]), "bars": miss(RD["bars"]), "tgt": miss(RD["tgt"]),
          "rat": miss(RD["rat"]), "cf": miss(RD["cf"])}
print(f"radar_data.json: {len(order)} tickers | asof={asof!r}")
ok = True
for k, v in report.items():
    if v: ok = False; print(f"  ! {k}: faltando {len(v)} -> {v} (usando fallback do run anterior onde havia)")
print("  todos os campos presentes." if ok else "  (campos faltantes acima usaram fallback quando disponível)")
