"""Read-only BTC market structure evidence; configured historical zones are NOT current validated levels."""
from datetime import datetime, timezone

INITIAL_ZONES={"support":[81000.0,84000.0],"resistance":[87000.0,88000.0]}

def analyze_btc(rows, now=None):
    now=now or datetime.now(timezone.utc).timestamp()
    valid={}
    for stamp,close in rows:
        try:
            t=int(stamp); v=float(close)
            if v>0 and t+86400<=now: valid[t]=v
        except (ValueError,TypeError):continue
    series=sorted(valid.items())
    result={"status":"insufficient_data","basis":"completed BTC-USD daily close UTC",
        "zones_status":"historical_unverified","historical_zones":INITIAL_ZONES,
        "confirmed_breakout":False,"confirmed_breakdown":False,
        "latest_close_usd":None,"latest_close_utc":None,"weekly_closes":[]}
    if not series:return result
    t,c=series[-1]
    result["latest_close_usd"]=c
    result["latest_close_utc"]=datetime.fromtimestamp(t+86400,timezone.utc).isoformat()
    if len(series)<16:return result
    weeks={}
    for stamp,value in series:
        dt=datetime.fromtimestamp(stamp,timezone.utc)
        # daily bars start at midnight UTC; Sunday bar is last day in Monday-Sunday week
        if dt.weekday()==6:
            weeks[dt.strftime("%Y-%m-%d")]=value
    result["weekly_closes"]=[{"week_ending":day,"close_usd":value} for day,value in sorted(weeks.items())[-8:]]
    if len(result["weekly_closes"])<3:return result
    closes=[v for _,v in series]
    last=closes[-1];prev=closes[-2]
    pct=(last/prev-1)*100 if prev else None
    result.update({"status":"observed","daily_change_pct":round(pct,2),
        "weekly_direction":"up" if result["weekly_closes"][-1]["close_usd"]>result["weekly_closes"][-2]["close_usd"] else "down",
        "structure_note":"Weekly support/resistance zone selection and state persistence are not yet validated. Historical preset zones MUST NOT be treated as active signals."})
    return result
