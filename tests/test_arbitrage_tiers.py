import unittest
from arbitrage_tiers import calculate_tiers

class TierTests(unittest.TestCase):
    def test_full_fill_and_fees(self):
        r=calculate_tiers([[100,10000000]],[[110,10000000]],.3,.3,tiers=[1000000])
        self.assertEqual(r[0]["status"],"estimated_before_transfer")
        self.assertGreater(r[0]["estimated_net_before_transfer_toman"],0)
        self.assertEqual(r[0]["transfer_status"],"unverified")

    def test_limited_buy_depth_no_profit(self):
        r=calculate_tiers([[100,1]],[[110,100000]],.3,.3,tiers=[1000000])
        self.assertEqual(r[0]["status"],"book_insufficient")
        self.assertIsNone(r[0]["estimated_net_before_transfer_toman"])

    def test_limited_sell_depth_no_profit(self):
        r=calculate_tiers([[100,1000000]],[[110,1]],.3,.3,tiers=[1000000])
        self.assertEqual(r[0]["status"],"book_insufficient")

    def test_unknown_fees_not_zero(self):
        r=calculate_tiers([[100,1000000]],[[110,1000000]],None,.3,tiers=[1000000])
        self.assertEqual(r[0]["fee_status"],"missing")
        self.assertIsNone(r[0]["estimated_net_before_transfer_toman"])

    def test_fee_budget_is_not_overspent(self):
        r=calculate_tiers([[100,1000000]],[[100,1000000]],1,0,tiers=[10000])
        self.assertLess(r[0]["estimated_net_before_transfer_toman"],0)

if __name__=="__main__":unittest.main()
