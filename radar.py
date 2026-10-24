"""Hamzeh DEX Radar: research-only DEX candidate scanner; never signs or trades."""
import json, os, time, math
from correlation import measure
from relative_strength import relative_strength
from btc_replay import replay_reactions
from btc_structure import analyze_btc
from btc_pivots import levels_from_completed_closes
from btc_levels import monitor
from safety import security_evm, liquidity_assessment, indicative_sell_impact
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import quote, urlencode

NETWORKS={"base":"base","arbitrum":"arbitrum","flare":"flare","ethereum":"ethereum","solana":"solana"}
GECKO_NETWORKS={"base":"base","arbitrum":"arbitrum","flare":"flare","ethereum":"eth","solana":"solana"}
DEX="https://api.dexscreener.com"
GECKO="https://api.geckoterminal.com/api/v2"

_last_gecko_call=0.0
def fetch_json(url):
    """Rate-limit GeckoTerminal requests and retry temporary throttling."""
    global _last_gecko_call
    from urllib.error import HTTPError
    gecko=url.startswith(GECKO+"/")
    for attempt in range(3):
        if gecko:
            remaining=8.0-(time.monotonic()-_last_gecko_call)
            if remaining>0:time.sleep(remaining)
            _last_gecko_call=time.monotonic()
        req=Request(url,headers={"User-Agent":"HamzehRadar/0.2","Accept":"application/json"})
        try:
            with urlopen(req,timeout=18) as response:
                return json.load(response)
        except HTTPError as exc:
            if exc.code!=429 or attempt==2:raise
            time.sleep(12*(attempt+1))

def discover():
    tokens={}
    for endpoint in ("/token-profiles/latest/v1","/token-boosts/latest/v1","/token-boosts/top/v1"):
        try: data=fetch_json(DEX+endpoint)
        except Exception as exc:
            print("Discovery source unavailable:",endpoint,str(exc)[:150])
            continue
        for row in data if isinstance(data,list) else []:
            chain=str(row.get("chainId","")).lower()
            if chain=="eth": chain="ethereum"
            address=row.get("tokenAddress")
            if chain in NETWORKS and address:
                tokens[(chain,address if chain=="solana" else address.lower())]={"chain":chain,"address":address}
    return list(tokens.values())

def best_pair(pairs,token):
    eligible=[p for p in pairs if str(p.get("chainId","")).lower() in ({token["chain"],"eth"} if token["chain"]=="ethereum" else {token["chain"]})
        and (str(p.get("baseToken",{}).get("address",""))==token["address"] if token["chain"]=="solana" else str(p.get("baseToken",{}).get("address","")).lower()==token["address"].lower())]
    return max(eligible,key=lambda x:float((x.get("liquidity") or {}).get("usd") or 0),default=None)

def screen(token):
    chain,address=token["chain"],token["address"]
    pairs=fetch_json(f"{DEX}/token-pairs/v1/{'ethereum' if chain=='ethereum' else chain}/{quote(address,safe='')}")
    pair=best_pair(pairs if isinstance(pairs,list) else [],token)
    if not pair: return None
    liquidity=float((pair.get("liquidity") or {}).get("usd") or 0)
    volume=float((pair.get("volume") or {}).get("h24") or 0)
    created=pair.get("pairCreatedAt")
    age=(time.time()*1000-created)/86400000 if isinstance(created,(int,float)) else None
    if liquidity<50000 or volume<20000 or age is None or age<2: return None
    score=40*min(liquidity/250000,1)+35*min(volume/100000,1)+25*min(age/30,1)
    return {"network":chain,"symbol":pair.get("baseToken",{}).get("symbol","?"),
        "contract":address,"pool":pair.get("pairAddress"),"dex":pair.get("dexId"),
        "market_url":pair.get("url"),"liquidity_usd":liquidity,
        "volume_24h_usd":volume,"age_days":round(age,1),
        "research_priority":round(score,1),"contract_security":"NOT_VERIFIED",
        "sellability":"NOT_VERIFIED","timeframes":{},"exit_watch":"INSUFFICIENT_DATA"}

def momentum(closes):
    if len(closes)<16 or any(v<=0 for v in closes): return {"status":"insufficient_data"}
    def avglog(xs): return sum(math.log(xs[i]/xs[i-1]) for i in range(1,len(xs)))/(len(xs)-1)
    recent=avglog(closes[-6:])
    previous=avglog(closes[-11:-5])
    trend=avglog(closes[-16:])
    return {"status":"ok","recent":round(recent,6),"previous":round(previous,6),
            "trend":round(trend,6),"decelerating":recent<previous,"uptrend":trend>0}

def candles(payload):
    rows=(((payload or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    return [float(r[4]) for r in sorted(rows,key=lambda x:x[0]) if len(r)>=5]

def discover_gecko():
    """Independent pool discovery: new, trending and top pools per chain."""
    candidates={}
    errors=[]
    health={chain:{"successful_endpoints":0,"raw_pools":0,"eligible_pools":0,"errors":[]} for chain in GECKO_NETWORKS}
    for chain,network in GECKO_NETWORKS.items():
        for endpoint in ("trending_pools","new_pools","pools"):
            try:
                payload=fetch_json(f"{GECKO}/networks/{network}/{endpoint}?include=base_token&page=1")
                health[chain]["successful_endpoints"]+=1
                health[chain]["raw_pools"]+=len(payload.get("data",[]))
                included={x.get("id"):x for x in payload.get("included",[])}
                for record in payload.get("data",[]):
                    a=record.get("attributes") or {}
                    address=a.get("address")
                    rel=(record.get("relationships") or {}).get("base_token",{}).get("data") or {}
                    token=included.get(rel.get("id"),{})
                    ta=token.get("attributes") or {}
                    token_addr=ta.get("address")
                    if not address or not token_addr:continue
                    liquidity=float(a.get("reserve_in_usd") or 0)
                    vols=a.get("volume_usd") or {}
                    volume=float(vols.get("h24") or 0)
                    created=a.get("pool_created_at") or ""
                    try:
                        dt=datetime.fromisoformat(created.replace("Z","+00:00"))
                        age=max(0,(datetime.now(timezone.utc)-dt).total_seconds()/86400)
                    except (ValueError,TypeError): age=None
                    if liquidity<20000 or volume<10000 or age is None or age<1:continue
                    health[chain]["eligible_pools"]+=1
                    score=40*min(liquidity/250000,1)+35*min(volume/100000,1)+25*min(age/30,1)
                    entry={"network":chain,"symbol":ta.get("symbol") or a.get("name") or "?",
                        "contract":token_addr,"pool":address,"dex":"GeckoTerminal",
                        "market_url":f"https://www.geckoterminal.com/{network}/pools/{address}",
                        "liquidity_usd":liquidity,"volume_24h_usd":volume,"age_days":round(age,1),
                        "research_priority":round(score,1),"contract_security":"NOT_VERIFIED",
                        "sellability":"NOT_VERIFIED","timeframes":{},"exit_watch":"INSUFFICIENT_DATA",
                        "discovery_source":endpoint}
                    key=(chain,address if chain=="solana" else address.lower())
                    if key not in candidates or candidates[key]["research_priority"]<entry["research_priority"]:
                        candidates[key]=entry
            except Exception as exc:
                errors.append(f"{chain}/{endpoint}: {str(exc)[:110]}")
                health[chain]["errors"].append(f"{endpoint}: {str(exc)[:100]}")
    return list(candidates.values()),errors,health

def btc_daily_rows():
    """Public Coinbase BTC-USD completed daily candles for a comparable benchmark."""
    from datetime import timedelta
    end=datetime.now(timezone.utc).replace(hour=0,minute=0,second=0,microsecond=0)
    start=end-timedelta(days=230)
    url="https://api.exchange.coinbase.com/products/BTC-USD/candles?"+urlencode({
        "granularity":86400,"start":start.isoformat(),"end":end.isoformat()})
    rows=fetch_json(url)
    return [(int(row[0]),float(row[4])) for row in rows if isinstance(row,list) and len(row)>=5]

def token_daily_rows(item):
    network=GECKO_NETWORKS[item["network"]]
    pool=item.get("pool")
    url=f"{GECKO}/networks/{network}/pools/{quote(pool,safe='')}/ohlcv/day?aggregate=1&limit=240&currency=usd"
    data=fetch_json(url)
    rows=(((data or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    return [(int(row[0]),float(row[4])) for row in rows if len(row)>=5]

def inspect(item,btc_rows=None):
    pool=item.get("pool")
    item["btc_relationship"]={"status":"unavailable"}
    item["relative_strength"]={"status":"insufficient_data"}
    if not pool: return
    if btc_rows:
        try:
            token_rows=token_daily_rows(item)
            item["btc_relationship"]=measure(token_rows,btc_rows)
            item["relative_strength"]=relative_strength(token_rows,btc_rows)
        except Exception as exc: item["btc_relationship"]={"status":"unavailable","reason":str(exc)[:100]}
    network=GECKO_NETWORKS[item["network"]]
    for period in ("day","week"):
        url=f"{GECKO}/networks/{network}/pools/{quote(pool,safe='')}/ohlcv/{period}?aggregate=1&limit=40&currency=usd"
        try: item["timeframes"][period]=momentum(candles(fetch_json(url)))
        except Exception as exc: item["timeframes"][period]={"status":"unavailable","reason":str(exc)[:100]}
    d=item["timeframes"].get("day",{})
    w=item["timeframes"].get("week",{})
    if d.get("status")!="ok" or w.get("status")!="ok": return
    if d["decelerating"] and w["decelerating"]:
        item["exit_watch"]="JOINT_MOMENTUM_DECELERATION_REVIEW_ONLY"
    elif d["decelerating"] or w["decelerating"]:
        item["exit_watch"]="MIXED_TIMEFRAMES_MONITOR"
    else: item["exit_watch"]="NO_JOINT_DECELERATION"

def report(items,scanned):
    lines=[f"# Hamzeh DEX Radar — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "Research watchlist only. Not a buy/sell recommendation.",
        "Contract security, honeypot risk and ability to exit have NOT been verified.",
        f"Discovered tokens: {scanned}; candidates shown: {len(items)}",""]
    if not items: lines.append("No candidates passed screening, or public sources were unavailable.")
    for i,x in enumerate(items,1):
        lines.extend([f"## {i}. {x['symbol']} — {x['network']}",
            f"Research priority: {x['research_priority']}/100 (not a trading signal)",
            f"Liquidity (reported): USD {x['liquidity_usd']:,.0f}",
            f"24h volume (reported): USD {x['volume_24h_usd']:,.0f}",
            f"Day/week momentum status: {x['exit_watch']}",
            f"BTC correlation: {x.get('btc_relationship',{})}",
            f"Contract: {x['contract']}",f"Market: {x.get('market_url') or 'unknown'}",""])
    lines.append("A momentum slowdown does not establish a market top. Missing weekly data blocks exit conclusions.")
    return "\n".join(lines)

def notify(message):
    token,chat=os.getenv("TELEGRAM_BOT_TOKEN"),os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat: return False
    data=urlencode({"chat_id":chat,"text":message[:3800]}).encode()
    req=Request(f"https://api.telegram.org/bot{token}/sendMessage",data=data)
    with urlopen(req,timeout=20) as response: return response.status==200

def enrich_metadata(items):
    """Metadata is not evidence of organic social popularity or creator ownership."""
    try:
        profiles=fetch_json(DEX+"/token-profiles/latest/v1")
    except Exception:
        profiles=[]
    lookup={}
    for row in profiles if isinstance(profiles,list) else []:
        chain=str(row.get("chainId","")).lower().replace("eth","ethereum") if row.get("chainId")=="eth" else str(row.get("chainId","")).lower()
        address=str(row.get("tokenAddress") or "")
        if address: lookup[(chain,address if chain=="solana" else address.lower())]=row
    # Query actual watched contracts in batches rather than the small global latest-profile feed.
    # DexScreener allows up to 30 addresses per token batch request.
    pair_links={}
    for chain in NETWORKS:
        addresses=list(dict.fromkeys(x["contract"] for x in items if x["network"]==chain))
        for start in range(0,len(addresses),30):
            batch=addresses[start:start+30]
            try:
                payload=fetch_json(DEX+"/tokens/v1/"+("ethereum" if chain=="ethereum" else chain)+"/"+",".join(quote(a,safe="") for a in batch))
                for pair in payload if isinstance(payload,list) else []:
                    addr=str((pair.get("baseToken") or {}).get("address") or "")
                    if not addr:continue
                    key=(chain,addr if chain=="solana" else addr.lower())
                    info=pair.get("info") or {}
                    links=[]
                    for entry in (info.get("socials") or [])+(info.get("websites") or []):
                        if isinstance(entry,dict) and str(entry.get("url") or "").startswith("https://"):
                            links.append({"platform":str(entry.get("platform") or entry.get("label") or "web"),
                                          "url":entry["url"]})
                    if len(links)>len(pair_links.get(key,[])):pair_links[key]=links
            except Exception as exc:
                print("Bulk token social metadata unavailable:",chain,str(exc)[:100])
    for index,item in enumerate(items):
        chain=item["network"]
        address=item["contract"]
        profile=lookup.get((chain,address if chain=="solana" else address.lower()),{})
        links=list(pair_links.get((chain,address if chain=="solana" else address.lower()),[]))
        for link in profile.get("links") or []:
            if isinstance(link,dict) and str(link.get("url","")).startswith("https://"):
                links.append({"platform":str(link.get("type") or link.get("label") or "web"),"url":link["url"]})
        links=list({link["url"]:link for link in links}.values())
        item["social_monitor"]={"links":links[:15],"organic_mentions_24h":None,
            "engagement_24h":None,"trending":"unverified",
            "status":"links_only" if links else "unavailable"}
        supply={"total_supply":None,"circulating_supply":None,"unreleased_supply":None,
                "creator_held":None,"creator_held_pct":None,"status":"unavailable"}
        try:
            if index>=12:
                supply["status"]="not_queried_this_run"
                item["token_supply"]=supply
                continue
            url=GECKO+"/networks/"+GECKO_NETWORKS[chain]+"/tokens/"+quote(address,safe="")+"/info"
            attrs=((fetch_json(url).get("data") or {}).get("attributes") or {})
            for key in ("total_supply","circulating_supply"):
                try:
                    value=float(attrs[key])
                    if math.isfinite(value) and value>=0:supply[key]=value
                except (KeyError,TypeError,ValueError):pass
            total,circ=supply["total_supply"],supply["circulating_supply"]
            if total is not None and circ is not None and circ<=total:
                supply["unreleased_supply"]=total-circ
                supply["status"]="provider_reported"
            elif total is not None or circ is not None:
                supply["status"]="partial"
        except Exception as exc:
            supply["error"]=str(exc)[:100]
        item["token_supply"]=supply

def main():
    output=Path("output"); output.mkdir(exist_ok=True)
    found=discover()
    candidates,source_errors,source_health=discover_gecko()
    for token in found[:100]:
        try:
            item=screen(token)
            if item: candidates.append(item)
        except Exception as exc: print("Token unavailable:",token["chain"],str(exc)[:100])
        time.sleep(0.2)
    # Avoid filling the entire shortlist from one network when other chains have data.
    by_network={name:[] for name in NETWORKS}
    for item in sorted(candidates,key=lambda x:x["research_priority"],reverse=True):
        by_network[item["network"]].append(item)
    # Network-specific watchlists must not be hidden by the global eight-item analysis budget.
    per_network={network:items[:30] for network,items in by_network.items()}
    selected=[]
    while len(selected)<8 and any(by_network.values()):
        for network in NETWORKS:
            if by_network[network] and len(selected)<8:
                selected.append(by_network[network].pop(0))
    selected_ids={(x["network"],x["pool"]) for x in selected}
    watchlist=[]
    for network,items in per_network.items():
        for item in items:
            if (item["network"],item["pool"]) not in selected_ids:
                item["detail_status"]="pending_deep_analysis"
                item["btc_relationship"]={"status":"not_evaluated"}
                item["relative_strength"]={"status":"not_evaluated"}
                item["security_review"]={"status":"not_evaluated"}
                item["liquidity_review"]=liquidity_assessment(item)
                item["sell_impact_scenarios"]=[]
                item["sellability"]="NOT_SIMULATED"
            else:
                item["detail_status"]="deep_analysis_selected"
            watchlist.append(item)
    try: btc_rows=btc_daily_rows()
    except Exception as exc:
        btc_rows=[]
        print("BTC reference market data unavailable:",str(exc)[:160])
    btc_market_structure=analyze_btc(btc_rows)
    btc_market_structure['derived_pivots']=levels_from_completed_closes(btc_rows)
    previous_levels=None
    state_path=Path("state/btc_levels.json")
    if state_path.exists():
        try:
            previous_levels=json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError,ValueError) as exc:
            print("Persisted BTC state invalid:",str(exc)[:150])
    if previous_levels is None:
        try:
            previous_report=fetch_json("https://nimania.github.io/crypto/radar.json")
            previous_levels=previous_report.get("btc_levels")
        except Exception as exc:
            print("Previous BTC state unavailable:",str(exc)[:150])
    btc_levels=monitor(btc_rows,btc_market_structure['derived_pivots'],previous_levels)
    btc_levels["history_source"]="persisted_state_or_last_published_json" if previous_levels else "bootstrap_no_previous_state"
    btc_levels["historical_replay"]={}
    for side in ("support","resistance"):
        zone=btc_levels.get(side)
        btc_levels["historical_replay"][side]=replay_reactions(btc_rows,zone,side) if zone else {"status":"unavailable","reason":"no_zone"}
    state_path.parent.mkdir(parents=True,exist_ok=True)
    state_path.write_text(json.dumps(btc_levels,ensure_ascii=False,indent=2),encoding="utf-8")
    for item in selected:
        inspect(item,btc_rows)
        item['security_review']=security_evm(item['network'],item['contract'],fetch_json)
        item['liquidity_review']=liquidity_assessment(item)
        item['sell_impact_scenarios']=[indicative_sell_impact(item,trade_usd=n) for n in (500,1000,5000)]
        item['sellability']='NOT_SIMULATED'
        time.sleep(0.3)
    enrich_metadata(watchlist)
    for item in candidates:
        source_health[item["network"]].setdefault("screened_candidates",0)
        source_health[item["network"]]["screened_candidates"]+=1
    for item in watchlist:
        source_health[item["network"]].setdefault("displayed_candidates",0)
        source_health[item["network"]]["displayed_candidates"]+=1
    for network,h in source_health.items():
        if h["successful_endpoints"]==0:
            h["status"]="source_unavailable"
        elif h.get("screened_candidates",0)==0:
            h["status"]="no_eligible_pools_or_incomplete_coverage"
        elif h.get("displayed_candidates",0)==0:
            h["status"]="not_selected"
        elif h["errors"]:
            h["status"]="partial_data"
        else:
            h["status"]="data_available"
        h["checked_at_utc"]=datetime.now(timezone.utc).isoformat()
    data={"generated_at":datetime.now(timezone.utc).isoformat(),
        "networks":list(NETWORKS),"discovered_count":len(found)+len(candidates),"screened_count":len(candidates),
        "data_source_errors":source_errors,"network_health":source_health,
        "btc_market_structure":btc_market_structure,"btc_levels":btc_levels,
        "deep_analyzed_count":len(selected),
        "candidates":watchlist}
    (output/"radar.json").write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding="utf-8")
    result=report(selected,len(found))
    (output/"report.md").write_text(result,encoding="utf-8")
    print(result)
    for err in source_errors: print("Source warning:",err)
    # Web dashboard is the only reporting channel; no Telegram notifications.

if __name__=="__main__": main()
