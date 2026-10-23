from datetime import datetime, timezone

def levels_from_completed_closes(rows, now=None):
    now = now if now is not None else datetime.now(timezone.utc).timestamp()
    valid = sorted((int(t), float(p)) for t,p in rows if float(p)>0 and int(t)+86400<=now)
    weekly = [(t,p) for t,p in valid if datetime.fromtimestamp(t,timezone.utc).weekday()==6]
    if len(weekly)<7:
        return {"status":"insufficient_data"}
    pivots={"support":[],"resistance":[]}
    for i in range(2,len(weekly)-2):
        value=weekly[i][1]
        peers=[x[1] for x in weekly[i-2:i+3]]
        if value==min(peers) and peers.count(value)==1:pivots["support"].append(value)
        if value==max(peers) and peers.count(value)==1:pivots["resistance"].append(value)
    latest=valid[-1][1]
    out={"status":"observed","latest_close":latest}
    for name in pivots:
        possible=[v for v in pivots[name] if (v<latest if name=="support" else v>latest)]
        out[name]=min(possible,key=lambda v:abs(v-latest)) if possible else None
    return out
