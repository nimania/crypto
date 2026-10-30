"""Read-only multi-notional liquidity and fee scenarios for Iranian exchange arbitrage.

Unknown fees/transfer availability never become a validated net profit.
"""
from math import isfinite

TIERS_TOMAN=(1_000_000,5_000_000,10_000_000,50_000_000,100_000_000)

def _levels(rows, descending=False):
    cleaned=[]
    for row in rows or []:
        try:
            price,qty=float(row[0]),float(row[1])
            if isfinite(price) and isfinite(qty) and price>0 and qty>0:
                cleaned.append((price,qty))
        except (TypeError,ValueError,IndexError):
            continue
    return sorted(cleaned,key=lambda x:x[0],reverse=descending)

def _buy(asks, budget):
    remaining=float(budget); qty=cost=0.0
    for price,available in _levels(asks):
        count=min(available,remaining/price)
        qty+=count;cost+=count*price;remaining-=count*price
        if remaining<=max(0.01,budget*1e-10): break
    return qty,cost,max(remaining,0.0)

def _sell(bids, quantity):
    remaining=float(quantity);received=0.0
    for price,available in _levels(bids,descending=True):
        count=min(available,remaining)
        received+=count*price;remaining-=count
        if remaining<=max(quantity*1e-10,1e-10):break
    return received,max(remaining,0.0)

def calculate_tiers(asks,bids,buy_fee_pct=None,sell_fee_pct=None,tiers=TIERS_TOMAN):
    """All fee inputs are percentage values, not fractions.
    Buy fee is conservatively charged on capital; sell fee on gross proceeds.
    Transfer costs and network latency are excluded, never silently treated as zero.
    """
    valid_fees=all(isinstance(x,(int,float)) and isfinite(x) and 0<=x<100
                   for x in (buy_fee_pct,sell_fee_pct))
    result=[]
    for amount in tiers:
        if amount<=0:continue
        # Fee is reserved inside the initial capital (not additional to it).
        spend=amount/(1+buy_fee_pct/100) if valid_fees else amount
        qty,cost,unspent=_buy(asks,spend)
        revenue,unsold=_sell(bids,qty)
        bought_ok=qty>0 and unspent<=max(.01,spend*1e-8)
        sold_ok=qty>0 and unsold<=max(qty*1e-8,1e-9)
        status="book_sufficient" if bought_ok and sold_ok else "book_insufficient"
        row={"capital_toman":amount,"status":status,
             "buy_filled_pct":round(100*(spend-unspent)/spend,3),
             "sell_filled_pct":round(100*(qty-unsold)/qty,3) if qty else 0,
             "gross_proceeds_toman":round(revenue,2) if sold_ok else None,
             "estimated_net_before_transfer_toman":None,
             "estimated_return_before_transfer_pct":None,
             "fee_status":"reported" if valid_fees else "missing",
             "transfer_status":"unverified"}
        if status=="book_sufficient" and valid_fees:
            # Includes unspent fee reserve through full capital subtraction.
            net=revenue*(1-sell_fee_pct/100)-amount
            row["status"]="estimated_before_transfer"
            row["estimated_net_before_transfer_toman"]=round(net,2)
            row["estimated_return_before_transfer_pct"]=round(net/amount*100,4)
        result.append(row)
    return result
