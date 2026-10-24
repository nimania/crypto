"""Bounded GDELT web-news sampling. Research metadata, not social engagement."""
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json
import re

GDELT = "https://api.gdeltproject.org/api/v2/doc/doc"

def news_query(symbol, network):
    token = str(symbol or "").strip()
    # Common/short symbols cause unrelated web hits; skip until identity verified.
    if not re.fullmatch(r"[A-Za-z0-9]{4,15}", token):
        return None
    return f'"{token}" cryptocurrency "{network}"'

def collect(item, fetcher=None):
    query=news_query(item.get("symbol"),item.get("network"))
    result={"status":"ambiguous_identity" if query is None else "unavailable",
            "source":"GDELT DOC 2.0","sample_count_24h":None,"articles":[],
            "trend_status":"not_established","note":"Sampled relevant news is not proof of organic trends or total web coverage."}
    if query is None:
        return result
    params=urlencode({"query":query,"mode":"artlist","format":"json",
                      "maxrecords":20,"timespan":"1d","sort":"datedesc"})
    url=GDELT+"?"+params
    try:
        if fetcher is None:
            def fetcher(target):
                with urlopen(Request(target,headers={"User-Agent":"HamzehCryptoRadar/0.3"}),timeout=12) as r:
                    return json.load(r)
        payload=fetcher(url)
        articles=[]
        seen=set()
        for row in payload.get("articles",[]) if isinstance(payload,dict) else []:
            title=str(row.get("title") or "").strip()
            link=str(row.get("url") or "")
            if not link.startswith("https://") or not title or link in seen:continue
            # Simple relevance guard against homonymous tickers.
            check=(title+" "+str(row.get("domain") or "")).lower()
            if not any(w in check for w in (str(item.get("symbol","")).lower(),"crypto","token","blockchain",str(item.get("network","")).lower())):
                continue
            seen.add(link)
            articles.append({"title":title[:240],"url":link,
                 "source":str(row.get("domain") or "")[:120],
                 "published_at":str(row.get("seendate") or "")[:32]})
        result.update(status="sampled",sample_count_24h=len(articles),articles=articles[:10],
                      checked_at_utc=datetime.now(timezone.utc).isoformat())
    except Exception as exc:
        result["error"]=str(exc)[:160]
    return result

def enrich_news(items, limit=5):
    ranked=sorted(items,key=lambda x:x.get("research_priority",0),reverse=True)
    for item in items:
        item["web_attention"]={"status":"not_sampled_this_run","sample_count_24h":None,
                               "articles":[],"trend_status":"not_established"}
    attempted=0
    for item in ranked:
        if attempted>=limit:break
        if news_query(item.get("symbol"),item.get("network")) is None:
            item["web_attention"]=collect(item)
            continue
        item["web_attention"]=collect(item)
        attempted+=1
    return attempted
