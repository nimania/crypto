"""Classify completed-close reactions around an existing BTC price zone.

This is research evidence only. With close-only data, wick tests and true
intraday touches are NOT observable.
"""
from datetime import datetime, timezone

def classify_reaction(rows, zone, side, previous=None, now=None):
    now = datetime.now(timezone.utc).timestamp() if now is None else now
    if side not in ("support", "resistance") or not isinstance(zone, dict):
        return {"status": "unavailable", "reason": "missing_zone"}
    try:
        lower, upper = float(zone["lower"]), float(zone["upper"])
        if not (0 < lower <= upper):
            raise ValueError("invalid zone")
    except (KeyError, TypeError, ValueError):
        return {"status": "unavailable", "reason": "invalid_zone"}
    observed = {}
    for stamp, close in rows:
        try:
            stamp, close = int(stamp), float(close)
            if stamp % 86400 == 0 and stamp + 86400 <= now and close > 0:
                observed[stamp] = close
        except (ValueError, TypeError, OverflowError):
            continue
    points = sorted(observed.items())
    if len(points) < 3 or any(points[-i][0]-points[-i-1][0] != 86400 for i in (1,2)):
        return {"status": "insufficient_data", "reason": "three_consecutive_closes_required"}
    (t0, a), (t1, b), (t2, c) = points[-3:]
    prior_status = previous.get("status") if isinstance(previous,dict) else None
    prior_break = prior_status in ("confirmed_break", "retest_holding", "retest_failed")
    if side == "support":
        outside = lambda p: p < lower
        restored = lambda p: p > upper
        # After confirmed support loss: old support may act as resistance.
        retest_holding = prior_break and b <= lower and lower <= c <= upper
        retest_failed = prior_break and b <= lower and c > upper
        bounce = a > upper and lower <= b <= upper and c > upper
        close_rejection = a >= lower and b <= upper and c > upper
    else:
        outside = lambda p: p > upper
        restored = lambda p: p < lower
        # After confirmed resistance breakout: old resistance may act as support.
        retest_holding = prior_break and b >= upper and lower <= c <= upper
        retest_failed = prior_break and b >= upper and c < lower
        bounce = a < lower and lower <= b <= upper and c < lower
        close_rejection = a <= upper and b >= lower and c < lower
    if retest_failed:
        status = "retest_failed"
    elif retest_holding:
        status = "retest_in_progress"
    elif outside(b) and outside(c):
        status = "confirmed_daily_acceptance"
    elif outside(c):
        status = "break_pending"
    elif bounce or close_rejection:
        status = "support_rebound" if side == "support" else "resistance_rejection"
    else:
        status = "no_decisive_reaction"
    return {"status":status,"basis":"three consecutive completed UTC daily closes",
            "last_close":c,
            "observed_utc":datetime.fromtimestamp(t2+86400, timezone.utc).isoformat(),
            "limitations":"No intraday highs/lows or wick-based touching; retests are provisional"}
