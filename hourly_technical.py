"""Technical-first hourly close evaluation; never treat forming candles as confirmed."""
from datetime import datetime, timezone
import math

HOUR=3600

def closed_prices(payload, now=None, granularity=HOUR):
    now=now or int(datetime.now(timezone.utc).timestamp())
    rows=(((payload or {}).get("data") or {}).get("attributes") or {}).get("ohlcv_list") or []
    result={}
    for row in rows:
        if not isinstance(row,list) or len(row)<5:continue
        try:
            stamp=int(row[0]); close=float(row[4])
        except (ValueError,TypeError):continue
        if stamp+granularity<=now and close>0 and math.isfinite(close):
            result[stamp]=close
    return sorted(result.items())

def assess(rows):
    result={"status":"insufficient_data","last_closed_at":None,"reason":"at_least_20_closed_hourly_candles_required",
            "news_trigger":False,"signal":"NO_CONFIRMED_TECHNICAL_EVENT"}
    if rows:result["last_closed_at"]=rows[-1][0]
    if len(rows)<20:return result
    prices=[x[1] for x in rows]
    latest=prices[-1]; prior=prices[-2]
    prior_high=max(prices[-20:-1]); prior_low=min(prices[-20:-1])
    result.update(status="sufficient",reason="closed_candles_available",last_close=latest,
                  previous_close=prior,resistance_prior_19=prior_high,support_prior_19=prior_low)
    if latest>prior_high and prior<=prior_high:
        result.update(signal="PROVISIONAL_HOURLY_BREAKOUT",news_trigger=True)
    elif latest<prior_low and prior>=prior_low:
        result.update(signal="PROVISIONAL_HOURLY_BREAKDOWN",news_trigger=True)
    else:
        result["signal"]="NO_NEW_BOUNDARY_CROSSING"
    return result
