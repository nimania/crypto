import asyncio
import json
import unittest
from types import SimpleNamespace
from arbitrage_verify import verify

def response(data):
    return SimpleNamespace(is_error=False, content=[SimpleNamespace(type="text", text=json.dumps(data))])

class FakeSession:
    def __init__(self, full=True): self.full=full
    async def call_tool(self,name,arguments):
        if name=="ic_get_orderbook":
            if arguments["exchange"]=="wallex":
                return response({"asks":[[100,100000]] if self.full else [[100,10]],"bids":[[99,100000]]})
            return response({"asks":[[110,100000]],"bids":[[110,100000]]})
        if name=="ic_fees":
            return response({"trade_fees_pct":{"wallex":0.3,"nobitex":0.3},"networks":[]})
        raise ValueError(name)

class VerifyTests(unittest.TestCase):
    def test_full_order_book_returns_pre_transfer_estimate(self):
        item={"buy_exchange":"wallex","sell_exchange":"nobitex","symbol":"ALGO"}
        p=asyncio.run(verify(FakeSession(),item,budget_toman=10000))
        self.assertEqual(p["book_status"],"sufficient")
        self.assertEqual(p["status"],"estimated_before_transfer")
        self.assertIsNotNone(p["estimated_net_before_transfer_toman"])
        self.assertIsNone(p["estimated_net_toman"])
    def test_partial_fill_does_not_report_net_estimate(self):
        item={"buy_exchange":"wallex","sell_exchange":"nobitex","symbol":"ALGO"}
        p=asyncio.run(verify(FakeSession(full=False),item,budget_toman=10000))
        self.assertEqual(p["book_status"],"insufficient")
        self.assertIsNone(p.get("estimated_net_before_transfer_toman"))
        self.assertIsNone(p["estimated_net_toman"])

if __name__=="__main__": unittest.main()
