import unittest
from arbitrage_scan import normalize, rows_from

class ArbitrageSchemaTests(unittest.TestCase):
    def test_actual_provider_schema(self):
        row={"coin":"BTC","buy_on":"nobitex","sell_on":"wallex",
             "buy_price_toman":10000000,"sell_price_toman":10150000,"gap_pct":1.5}
        result=normalize(row)
        self.assertEqual(result["symbol"],"BTC")
        self.assertEqual(result["buy_exchange"],"nobitex")
        self.assertEqual(result["sell_exchange"],"wallex")
        self.assertEqual(result["gross_spread_pct"],1.5)
    def test_missing_legs_not_a_confirmed_opportunity(self):
        self.assertIsNone(normalize({"coin":"ETH","gap_pct":2}))
    def test_nested_provider_rows(self):
        self.assertEqual(len(rows_from({"opportunities":[{"coin":"USDT"}]})),1)

if __name__=="__main__": unittest.main()
