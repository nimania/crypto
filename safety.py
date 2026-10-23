"""Conservative third-party contract risk checks. No API result is a safety guarantee."""
from urllib.parse import urlencode

CHAIN_IDS={"ethereum":"1","base":"8453","arbitrum":"42161"}

RED_FLAGS={
 "is_honeypot":"Honeypot risk",
 "is_blacklisted":"Blacklist capability or use",
 "is_mintable":"Mint capability",
 "transfer_pausable":"Transfer pause capability",
 "can_take_back_ownership":"Ownership recovery capability",
 "slippage_modifiable":"Trading tax/slippage modifiable",
 "is_proxy":"Upgradeable proxy contract",
}

def security_evm(chain,address,fetch):
    cid=CHAIN_IDS.get(chain)
    if not cid:
        return {"status":"not_supported","provider":"GoPlus","red_flags":[],"checked_fields":[]}
    url="https://api.gopluslabs.io/api/v1/token_security/"+cid+"?"+urlencode({"contract_addresses":address.lower()})
    try:
        payload=fetch(url)
        if str(payload.get("code"))!="1":raise ValueError("Provider response not successful")
        raw=payload.get("result") or {}
        item=raw.get(address.lower()) or raw.get(address) or {}
        if not isinstance(item,dict) or not item:raise ValueError("Missing token security result")
        red=[]; checked=[]
        for field,label in RED_FLAGS.items():
            if item.get(field) in ("0","1",0,1):
                checked.append(field)
                if str(item[field])=="1":red.append(label)
        if item.get("is_open_source") in ("0",0):red.append("Unverified contract source")
        if item.get("is_open_source") in ("0","1",0,1):checked.append("is_open_source")
        tax=item.get("sell_tax")
        try:
            if tax is not None and float(tax)>0.10:red.append("High reported sell tax")
        except (ValueError,TypeError):pass
        status="risk_detected" if red else ("no_flags_in_checked_fields" if len(checked)>=4 else "insufficient_data")
        return {"status":status,"provider":"GoPlus","red_flags":red,"checked_fields":checked,
                "sell_tax_reported":tax,"simulation_performed":False}
    except Exception as exc:
        return {"status":"unavailable","provider":"GoPlus","red_flags":[],"checked_fields":[],"error":str(exc)[:110]}

def liquidity_assessment(item):
    liquidity=item.get("liquidity_usd")
    volume=item.get("volume_24h_usd")
    if liquidity is None or volume is None:return {"status":"insufficient_data"}
    try:
        liquidity=float(liquidity);volume=float(volume)
        if liquidity<=0 or volume<0:return {"status":"invalid_data"}
        return {"status":"reported_not_verified","usd_liquidity":liquidity,
                "usd_volume_24h":volume,"execution_slippage":"NOT_MEASURED"}
    except (ValueError,TypeError):return {"status":"invalid_data"}

def indicative_sell_impact(item, trade_usd=1000):
    """Scenario only: 50/50 constant-product AMM with 0.30% hypothetical LP fee.
    Reported pool liquidity is NOT a route quote, and V3/CLMMs are not modeled."""
    import math
    try:
        pool=float(item.get("liquidity_usd") or 0)
        amount=float(trade_usd)
        if not math.isfinite(pool) or not math.isfinite(amount) or pool<=0 or amount<=0:
            return {"status":"insufficient_data","execution_verified":False}
        # A 50/50 pool has estimated quote-side inventory L/2.
        quote_reserve=pool/2
        effective=amount*(1-0.003)
        estimated_out=quote_reserve*effective/(quote_reserve+effective)
        impact_pct=100*(1-estimated_out/amount)
        return {"status":"hypothetical_model_only","execution_verified":False,
            "model":"unverified_50_50_constant_product","hypothetical_fee_pct":0.3,
            "trade_usd":amount,"estimated_price_impact_pct":round(impact_pct,2),
            "estimated_output_usd":round(estimated_out,2),
            "warning":"Not an executable sell quote. Does not check token taxes, actual reserves, concentrated liquidity, route or gas."}
    except (ValueError,TypeError,OverflowError):
        return {"status":"insufficient_data","execution_verified":False}
