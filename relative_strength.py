"""Relative performance against BTC from aligned completed daily USD closes."""
from datetime import datetime,timezone
import math

def relative_strength(asset_rows,btc_rows,now=None):
    now=datetime.now(timezone.utc).timestamp() if now is None else now
    def clean(rows):
        result={}
        for t,v in rows:
            try:
                t=int(t);v=float(v)
                if t%86400==0 and t+86400<=now and math.isfinite(v) and v>0:result[t]=v
            except (ValueError,TypeError,OverflowError):continue
        return result
    a,b=clean(asset_rows),clean(btc_rows)
    common=sorted(set(a)&set(b))
    out={"status":"insufficient_data","periods":{},"method":"ratio of token USD return to BTC USD return over aligned completed UTC daily closes"}
    for label,days in (("7d",7),("30d",30),("90d",90)):
        if len(common)<2:out["periods"][label]={"status":"insufficient_data"};continue
        end=common[-1];start=end-days*86400
        if start not in a or start not in b:
            out["periods"][label]={"status":"insufficient_data"};continue
        asset_return=a[end]/a[start]-1
        btc_return=b[end]/b[start]-1
        ratio_change=(a[end]/b[end])/(a[start]/b[start])-1
        out["periods"][label]={"status":"ok","asset_return_pct":round(asset_return*100,2),
            "btc_return_pct":round(btc_return*100,2),"relative_return_pct":round((asset_return-btc_return)*100,2),
            "ratio_change_pct":round(ratio_change*100,2),"end_utc":datetime.fromtimestamp(end+86400,timezone.utc).isoformat()}
    if any(x["status"]=="ok" for x in out["periods"].values()):out["status"]="partial_or_complete"
    return out
