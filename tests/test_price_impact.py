import unittest
from safety import indicative_sell_impact

class PriceImpactTests(unittest.TestCase):
    def test_unavailable_on_zero_liquidity(self):
        self.assertEqual(indicative_sell_impact({"liquidity_usd":0})["status"],"insufficient_data")

    def test_larger_order_has_more_impact(self):
        p={"liquidity_usd":100000}
        small=indicative_sell_impact(p,500)
        large=indicative_sell_impact(p,5000)
        self.assertGreater(large["estimated_price_impact_pct"],small["estimated_price_impact_pct"])
        self.assertFalse(large["execution_verified"])

    def test_disclosure(self):
        r=indicative_sell_impact({"liquidity_usd":80000},1000)
        self.assertEqual(r["status"],"hypothetical_model_only")
        self.assertIn("Not an executable sell quote",r["warning"])

if __name__=="__main__":
    unittest.main()
