"""BTC relationship measured on aligned, completed UTC candle returns."""
import math
from datetime import datetime, timezone

def closed_candles(rows, period, now=None):
    now=now or datetime.now(timezone.utc).timestamp()
    step=86400 if period=="day" else 604800
    out={}
    for stamp,close in rows:
        try:
            stamp=int(stamp); close=float(close)
            if stamp+step>now or not math.isfinite(close) or close<=0: continue
            key=datetime.fromtimestamp(stamp,timezone.utc).strftime("%Y-%m-%d")
            out[key]=close
        except (ValueError,TypeError,OverflowError): continue
    return out

def pearson(a,b):
    n=len(a)
    if n<3: return None
    ma=sum(a)/n;mb=sum(b)/n
    aa=sum((x-ma)**2 for x in a)
    bb=sum((y-mb)**2 for y in b)
    if aa<=1e-18 or bb<=1e-18:return None
    return sum((x-ma)*(y-mb) for x,y in zip(a,b))/math.sqrt(aa*bb)

def relationship(asset,btc,window,min_pairs):
    dates=sorted(set(asset)&set(btc))
    returns=[]
    # A return is valid only when consecutive aligned periods have both observations.
    for prev,cur in zip(dates,dates[1:]):
        gap=(datetime.fromisoformat(cur)-datetime.fromisoformat(prev)).days
        if gap != (7 if window=="weekly" else 1):continue
        returns.append((math.log(asset[cur]/asset[prev]),math.log(btc[cur]/btc[prev])))
    returns=returns[-(26 if window=="weekly" else 30):]
    if len(returns)<min_pairs:return {"status":"insufficient_data","observations":len(returns)}
    rho=pearson([v[0] for v in returns],[v[1] for v in returns])
    if rho is None:return {"status":"insufficient_variance","observations":len(returns)}
    label="same_direction" if rho>=0.3 else "inverse" if rho<=-0.3 else "weak_or_mixed"
    return {"status":"ok","coefficient":round(rho,3),"observations":len(returns),"relationship":label}

def measure(asset_rows,btc_rows,now=None):
    daily=relationship(closed_candles(asset_rows,"day",now),closed_candles(btc_rows,"day",now),"daily",12)
    # Weekly series constructed from completed daily closes on Sunday UTC.
    def weekly(rows):
        from datetime import timedelta
        complete=closed_candles(rows,"day",now)
        result={}
        for date,close in complete.items():
            dt=datetime.fromisoformat(date)
            if dt.weekday()!=6:continue
            monday=(dt-timedelta(days=6)).strftime("%Y-%m-%d")
            result[monday]=close
        return result
    weekly_result=relationship(weekly(asset_rows),weekly(btc_rows),"weekly",8)
    return {"daily_30":daily,"weekly_26":weekly_result,"method":"Pearson correlation of aligned UTC log returns (completed daily closes; Sunday-derived weekly closes)","benchmark":"BTC-USD","decision_rule":"No assumption that any ticker always tracks or opposes Bitcoin"}
