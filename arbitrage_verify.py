"""Conservative, read-only verification of order-book and fee evidence."""
import asyncio
import json

def parse_result(result):
    if getattr(result,"isError",getattr(result,"is_error",False)):
        raise RuntimeError("MCP tool error: "+" ".join(getattr(c,"text","") for c in result.content)[:250])
    value=getattr(result,"structuredContent",None) or getattr(result,"structured_content",None)
    if value is not None: return value
    texts=[c.text for c in getattr(result,"content",[]) if getattr(c,"type",None)=="text"]
    if not texts: raise ValueError("missing MCP content")
    return json.loads("\n".join(texts))

def book_fill(levels, qty, descending=False):
    filled=proceeds=0.0
    for value in levels:
        try: price,volume=float(value[0]),float(value[1])
        except (ValueError,TypeError,IndexError): continue
        if price<=0 or volume<=0: continue
        take=min(volume,qty-filled)
        proceeds+=take*price; filled+=take
        if filled>=qty-1e-10: break
    return filled,proceeds

async def verify(session, item, *, budget_toman=10_000_000):
    """A fixed-notional scenario; missing withdrawal/deposit evidence is never assumed valid."""
    proof={"status":"unverified","budget_toman":budget_toman,
           "estimated_net_toman":None,"fee_status":"unknown",
           "transfer_status":"unverified","book_status":"unknown"}
    buy,sell,coin=item["buy_exchange"],item["sell_exchange"],item["symbol"]
    async def call(tool,args):
        return parse_result(await asyncio.wait_for(session.call_tool(tool,arguments=args),timeout=22))
    try:
        bought_book,sold_book=await asyncio.gather(
            call("ic_get_orderbook",{"exchange":buy,"coin":coin,"quote":"IRT","depth":20}),
            call("ic_get_orderbook",{"exchange":sell,"coin":coin,"quote":"IRT","depth":20}))
        asks=sorted(bought_book.get("asks",[]),key=lambda a:float(a[0]))
        bids=sorted(sold_book.get("bids",[]),key=lambda a:-float(a[0]))
        if not asks or not bids: raise ValueError("order book empty")
        left=float(budget_toman); acquired=cost=0.0
        for p,q in asks:
            p,q=float(p),float(q)
            if p<=0 or q<=0: continue
            portion=min(q,left/p)
            acquired+=portion; cost+=portion*p; left-=portion*p
            if left<0.01: break
        sold,revenue=book_fill(bids,acquired)
        proof.update(buy_filled_pct=round((budget_toman-left)/budget_toman*100,2),
                     sell_filled_pct=round(sold/acquired*100,2) if acquired else 0,
                     purchase_cost_toman=round(cost,2),sale_proceeds_toman=round(revenue,2),
                     book_status="sufficient" if left<0.01 and sold>=acquired-1e-9 else "insufficient",
                     book_gross_toman=round(revenue-cost,2))
    except Exception as exc:
        proof["book_status"]="unavailable"
        proof["book_error"]=str(exc)[:180]
        return proof
    try:
        fees=await call("ic_fees",{"coin":coin})
        rates=fees.get("trade_fees_pct",{})
        b,s=rates.get(buy),rates.get(sell)
        def fee_pct(value):
            if isinstance(value,(int,float)): return float(value)
            if isinstance(value,dict):
                for key in ("taker","taker_pct","taker_fee_pct","trade_fee_pct"):
                    if isinstance(value.get(key),(int,float)): return float(value[key])
            return None
        bp,sp=fee_pct(b),fee_pct(s)
        if bp is not None and sp is not None:
            proof["fee_status"]="reported"
            proof["trade_buy_pct"]=bp; proof["trade_sell_pct"]=sp
            if proof["book_status"]=="sufficient":
                proof["estimated_net_before_transfer_toman"]=round(proof["sale_proceeds_toman"]*(1-sp/100)-proof["purchase_cost_toman"]*(1+bp/100),2)
        else: proof["fee_status"]="missing"
        network_rows=fees.get("networks",[])
        source=[n for n in network_rows if n.get("exchange")==buy and n.get("withdraw") is True]
        target=[n for n in network_rows if n.get("exchange")==sell and n.get("deposit") is True]
        shared={n.get("network") for n in source}&{n.get("network") for n in target}
        proof["candidate_networks"]=sorted(x for x in shared if x)
        # Public fee listings are not proof of operational transfer support.
        proof["transfer_status"]="requires_live_confirmation"
        proof["status"]="estimated_before_transfer" if proof["book_status"]=="sufficient" and proof["fee_status"]=="reported" else "unverified"
    except Exception as exc:
        proof["fee_error"]=str(exc)[:180]
    return proof
