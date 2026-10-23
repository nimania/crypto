"""Evidence-only BTC level monitor. Uses completed UTC daily closes, no price predictions."""
from datetime import datetime, timezone

def monitor(rows, pivots, previous=None, now=None):
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    daily = {}
    for ts, close in rows:
        try:
            ts, close = int(ts), float(close)
            if close > 0 and ts % 86400 == 0 and ts + 86400 <= now:
                daily[ts] = close
        except (ValueError, TypeError, OverflowError):
            pass
    points = sorted(daily.items())
    output = {"status":"insufficient_data","method":"two consecutive completed UTC daily closes outside a previously observed 0.8% weekly pivot zone",
              "support":None,"resistance":None,"events":[],"history":[]}
    if len(points) < 3:
        return output
    last_ts = points[-1][0]
    last = points[-1][1]
    earlier = points[-2][1] if points[-1][0]-points[-2][0] == 86400 else None
    prev = previous if isinstance(previous,dict) else {}
    old_history = prev.get("history",[])
    output["history"] = old_history[-30:] if isinstance(old_history,list) else []
    output["status"]="observed"
    for side in ("support","resistance"):
        prior = prev.get(side)
        candidate = pivots.get(side) if isinstance(pivots,dict) else None
        # Persist the prior zone so a breach is evaluated against the prior level, not a shifted goalpost.
        if isinstance(prior,dict) and prior.get("anchor") and prior.get("source")=="weekly_close_fractal":
            zone = prior
        elif isinstance(candidate,(int,float)) and candidate>0:
            zone = {"anchor":round(candidate,2),"lower":round(candidate*.992,2),
                    "upper":round(candidate*1.008,2),"source":"weekly_close_fractal",
                    "established_utc":datetime.fromtimestamp(last_ts+86400,timezone.utc).isoformat()}
        else:
            zone = None
        output[side]=zone
        if zone is None: continue
        boundary = zone["lower"] if side=="support" else zone["upper"]
        beyond = last<boundary if side=="support" else last>boundary
        confirmed = beyond and earlier is not None and (earlier<boundary if side=="support" else earlier>boundary)
        label = "confirmed_daily_acceptance" if confirmed else "tested_not_confirmed" if beyond else "inside_or_safe_side"
        output[side+"_status"]=label
        old_label=prev.get(side+"_status")
        if confirmed and old_label!="confirmed_daily_acceptance":
            event={"side":side,"event":"two_daily_closes_outside_zone","close":last,
                   "utc":datetime.fromtimestamp(last_ts+86400,timezone.utc).isoformat(),
                   "zone_anchor":zone["anchor"]}
            output["events"].append(event)
            output["history"].append(event)
    output["history"]=output["history"][-30:]
    output["latest_close_utc"]=datetime.fromtimestamp(last_ts+86400,timezone.utc).isoformat()
    return output
