"""Historical replay diagnostics for BTC reactions; no predictive accuracy claims."""
from btc_reactions import classify_reaction

def replay_reactions(rows, zone, side, now=None):
    """Run successive snapshots using only candles available at each cutoff."""
    import time
    cutoff=time.time() if now is None else now
    clean=sorted((int(t),float(c)) for t,c in rows if int(t)+86400<=cutoff and float(c)>0)
    counts={}
    events=[]
    for i in range(3,len(clean)+1):
        subset=clean[:i]
        result=classify_reaction(subset,zone,side,now=subset[-1][0]+86400)
        status=result["status"]
        counts[status]=counts.get(status,0)+1
        if status in ("support_rebound","resistance_rejection","break_pending","confirmed_daily_acceptance"):
            events.append({"status":status,"utc":result.get("observed_utc"),"close":result.get("last_close")})
    return {"status":"replayed","evaluated_snapshots":max(0,len(clean)-2),
            "status_counts":counts,"events":events[-100:],
            "limitation":"Descriptive in-sample replay with fixed zone; not trade backtest or predictive validation."}
