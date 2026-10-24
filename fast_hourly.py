"""Standalone read-only 15-minute hourly-close monitor; writes a branch JSON snapshot."""
import json, os, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from hourly_technical import closed_prices, assess
from web_attention import collect

BASE="https://api.geckoterminal.com/api/v2"
NETWORK={"ethereum":"eth","base":"base","arbitrum":"arbitrum","flare":"flare","solana":"solana"}

def get(url,timeout=12):
    with urlopen(Request(url,headers={"User-Agent":"HamzehRadar-Hourly/1.0","Accept":"application/json"}),timeout=timeout) as resp:
        return json.load(resp)

def key(item):
    network=str(item.get("network") or "")
    contract=str(item.get("contract") or "")
    return network+":"+ (contract if network=="solana" else contract.lower())

def evaluate(items, previous=None, requester=get, news_fetcher=None, sleep=time.sleep):
    previous=previous or {}
    old=previous.get("tokens") or {}
    records={}
    news_budget=4
    for item in items:
        k=key(item)
        network=NETWORK.get(item.get("network"))
        pool=item.get("pool")
        if not network or not pool or not item.get("contract"):continue
        last=(old.get(k) or {})
        result={"status":"unavailable","news_trigger":False,"signal":"NO_CONFIRMED_TECHNICAL_EVENT"}
        try:
            url=f"{BASE}/networks/{network}/pools/{quote(str(pool),safe='')}/ohlcv/hour?aggregate=1&limit=50&currency=usd"
            result=assess(closed_prices(requester(url)))
        except Exception as exc:
            result["reason"]=str(exc)[:110]
        stamp=result.get("last_closed_at")
        fresh=bool(result.get("news_trigger") and stamp and
                  (not last.get("last_closed_at") or stamp>last["last_closed_at"]))
        result["new_event"]=fresh
        result["last_event_key"]=last.get("last_event_key")
        result["last_news"]=last.get("last_news")
        if fresh:
            result["last_event_key"]=k+":"+str(stamp)+":"+result["signal"]
            if news_budget:
                result["last_news"]=collect(item,news_fetcher)
                news_budget-=1
            else:
                result["last_news"]={"status":"deferred_capacity","articles":[]}
        # Preserve previous checked candle when upstream data is temporarily stale.
        if stamp is None and last.get("last_closed_at"):
            result["last_closed_at"]=last["last_closed_at"]
        records[k]=result
        sleep(3.1)  # approximately 19 requests/min, allowing for public provider caps
    return {"generated_at":datetime.now(timezone.utc).isoformat(),
            "source":"GeckoTerminal hour OHLCV","coverage":{"requested":len(items),"processed":len(records),
            "available":sum(v.get("status")=="sufficient" for v in records.values())},
            "tokens":records}

def main():
    previous={}
    try:previous=get("https://raw.githubusercontent.com/nimania/crypto/hourly-data/hourly.json")
    except Exception as exc: print("No previous hourly state:",str(exc)[:100])
    report=get("https://nimania.github.io/crypto/radar.json?ts="+str(int(time.time())))
    items=list({key(x):x for x in report.get("candidates",[]) if x.get("pool")}.values())
    result=evaluate(items,previous)
    Path("hourly.json").write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print("Hourly covered",result["coverage"])

if __name__=="__main__":main()
