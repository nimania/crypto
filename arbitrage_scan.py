#!/usr/bin/env python3
"""Read-only MCP arbitrage collection. Never implies executable profitability."""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path

OUTPUT = Path("output/arbitrage.json")
def number(obj, *keys):
    for key in keys:
        if isinstance(obj, dict) and obj.get(key) is not None:
            try: return float(obj[key])
            except (ValueError, TypeError): pass
    return None
def rows_from(obj):
    if isinstance(obj, list): return obj
    if not isinstance(obj, dict): return []
    for key in ("opportunities","results","arbitrages","gaps","items"):
        if isinstance(obj.get(key), list): return obj[key]
    if isinstance(obj.get("data"), (dict,list)): return rows_from(obj["data"])
    return []
def normalize(item):
    if not isinstance(item, dict): return None
    buy=item.get("buy_exchange") or item.get("cheapest_exchange") or item.get("buy_from")
    sell=item.get("sell_exchange") or item.get("most_expensive_exchange") or item.get("sell_at")
    if isinstance(buy,dict): buy=buy.get("name_fa") or buy.get("exchange") or buy.get("name")
    if isinstance(sell,dict): sell=sell.get("name_fa") or sell.get("exchange") or sell.get("name")
    ask=number(item,"buy_ask_toman","ask_toman","buy_price_toman","lowest_ask")
    bid=number(item,"sell_bid_toman","bid_toman","sell_price_toman","highest_bid")
    pct=number(item,"spread_pct","gross_spread_pct","gap_pct","profit_pct")
    if ask and bid and ask>0: pct=(bid-ask)/ask*100
    if not buy or not sell or pct is None or pct<=0: return None
    return {"symbol":str(item.get("symbol") or item.get("coin") or item.get("base") or "نامشخص"),
            "buy_exchange":str(buy),"sell_exchange":str(sell),"ask_toman":ask,
            "bid_toman":bid,"gross_spread_pct":round(pct,4),
            "note":"اختلاف خام؛ هزینه‌ها، نقدینگی و انتقال تأیید نشده"}
async def main():
    result={"generated_at_utc":datetime.now(timezone.utc).isoformat(),"status":"unavailable",
            "message":"اسکن انجام نشده","opportunities":[]}
    try:
        from mcp import ClientSession, StdioServerParameters
        from mcp.client.stdio import stdio_client
        params=StdioServerParameters(command="iran-crypto-mcp",args=[])
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                tools=await session.list_tools()
                match=next((t for t in tools.tools if t.name=="ic_arbitrage"),None)
                if match is None: raise RuntimeError("ic_arbitrage tool absent")
                props=match.inputSchema.get("properties",{})
                args={}
                if "quote" in props: args["quote"]="IRT"
                if "limit" in props: args["limit"]=30
                output=await session.call_tool("ic_arbitrage",arguments=args)
                if output.isError: raise RuntimeError("ic_arbitrage returned error")
                payload=getattr(output,"structuredContent",None)
                if not payload:
                    texts=[x.text for x in output.content if getattr(x,"type",None)=="text"]
                    payload=json.loads("\n".join(texts))
                raw=rows_from(payload)
                parsed=[x for x in (normalize(i) for i in raw) if x]
                parsed.sort(key=lambda x:x["gross_spread_pct"],reverse=True)
                result.update(status="ok" if parsed else "partial",opportunities=parsed,
                              message=f"{len(raw)} raw records; {len(parsed)} recognized positive spreads. Fees and execution unverified.")
                if raw and not parsed: result["message"]+=" Provider schema needs review; no negative market conclusion."
    except Exception as exc:
        result["message"]=f"Source unavailable or incompatible: {type(exc).__name__}: {str(exc)[:250]}"
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    OUTPUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding="utf-8")
    print(result["status"],result["message"])
if __name__=="__main__": asyncio.run(main())
