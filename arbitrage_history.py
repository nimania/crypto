"""Bounded snapshot history; does not infer continuous opportunity lifetime from sparse samples."""
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen

URL="https://nimania.github.io/crypto/arbitrage.json"
def key(x):
    return "|".join(str(x.get(k,"")) for k in ("symbol","buy_exchange","sell_exchange"))
def merge(previous,current,limit=168):
    records={}
    if isinstance(previous,dict):
        for x in previous.get("history",[]):
            if isinstance(x,dict) and isinstance(x.get("observations"),list):
                records[x.get("key","")]=[v for v in x["observations"] if isinstance(v,dict)]
        if not records and previous.get("generated_at_utc"):
            for x in previous.get("opportunities",[]):
                records.setdefault(key(x),[]).append({"time":previous["generated_at_utc"],"spread_pct":x.get("gross_spread_pct")})
    timestamp=current.get("generated_at_utc")
    for x in current.get("opportunities",[]):
        k=key(x)
        points=records.setdefault(k,[])
        if not any(p.get("time")==timestamp for p in points):
            points.append({"time":timestamp,"spread_pct":x.get("gross_spread_pct")})
    history=[]
    for k,points in records.items():
        points=sorted((p for p in points if isinstance(p.get("time"),str)),key=lambda p:p["time"])[-limit:]
        if points: history.append({"key":k,"observations":points})
    history.sort(key=lambda e:e["observations"][-1]["time"],reverse=True)
    return history[:500]
def read_previous():
    try:
        with urlopen(Request(URL,headers={"User-Agent":"HamzehRadar/2.0"}),timeout=8) as response:
            return json.load(response)
    except Exception:
        return {}
