#!/usr/bin/env python3
"""Build data/payload.json for the dashboard from data/radar_scored.json (+ thesis).
No hardcoded data."""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
S = json.load(open(os.path.join(DATA, "radar_scored.json"), encoding="utf-8"))
D, order, orderq, th = S["rows"], S["order"], S["orderq"], S.get("thesis", {})
rankq = {s: i + 1 for i, s in enumerate(orderq)}

rows = []
for i, s in enumerate(order):
    d = D[s]
    rows.append({"rank": i + 1, "t": s, "name": d["name"], "sector": d["sec"], "verdict": d["verdict"],
        "score": d["score"], "mom": d["blocks"]["mom"], "tech": d["blocks"]["tech"], "flow": d["blocks"]["flow"],
        "anal": d["blocks"]["anal"], "valq": d["blocks"]["valq"], "r21": d["r21"], "r63": d["r63"], "rsi": d["rsi"],
        "upside": d["upside"], "bull": d["bull"], "vol": d["vol"], "risk": d["risk"], "spec": d["spec"],
        "cov": d["cov"], "gbp": d["gbp"], "price": d["price"], "sma20": d["sma20"], "sma50": d["sma50"],
        "disthi": d["disthi"], "pe": d["pe"], "ps": d["ps"], "eps": d["eps"], "yld": d["yld"], "mcap": d["mcap"],
        "net": d["net"], "atr": d["atr"], "atrPct": d["atrPct"], "stop": d["stop"], "stopPct": d["stopPct"],
        "t1": d["t1"], "t2": d["t2"], "t1pct": d["t1pct"], "t2pct": d["t2pct"], "ivw": d["ivw"], "target": d["target"],
        "rankq": rankq[s], "scoreq": d["scoreq"], "verdictq": d["verdictq"],
        "qual": d["blocksq"]["qual"], "pull": d["blocksq"]["pull"], "trend": d["blocksq"]["trend"], "ups": d["blocksq"]["ups"],
        "ivwq": d["ivwq"], "thesis": th.get(s, "")})
counts = {v: sum(1 for r in rows if r["verdict"] == v) for v in ["BUY", "HOLD", "SELL"]}
countsq = {v: sum(1 for r in rows if r["verdictq"] == v) for v in ["BUY", "HOLD", "SELL"]}
buys = [r["t"] for r in rows if r["verdict"] == "BUY"]
buysq = [r["t"] for r in sorted(rows, key=lambda x: x["scoreq"], reverse=True) if r["verdictq"] == "BUY"]
payload = {"rows": rows, "counts": counts, "countsq": countsq, "weights": S["weights"], "weightsq": S["weightsq"],
    "asof": S.get("asof", ""), "n": len(rows), "buys": buys, "buysq": buysq}
open(os.path.join(DATA, "payload.json"), "w", encoding="utf-8").write(json.dumps(payload, ensure_ascii=False))
print("payload:", len(rows), "rows |", counts, "| A-buys", buys, "| B-buys", buysq)
