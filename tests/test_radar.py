import unittest
from radar import momentum, best_pair

class RadarTests(unittest.TestCase):
    def test_insufficient(self):
        self.assertEqual(momentum([1,2,3])["status"],"insufficient_data")
    def test_uptrend(self):
        self.assertTrue(momentum([100+2*i for i in range(30)])["uptrend"])
    def test_correct_chain(self):
        token={"chain":"base","address":"0xABC"}
        pairs=[{"chainId":"base","baseToken":{"address":"0xabc"},"liquidity":{"usd":20}},
               {"chainId":"arbitrum","baseToken":{"address":"0xabc"},"liquidity":{"usd":999}}]
        self.assertEqual(best_pair(pairs,token)["chainId"],"base")

if __name__=="__main__": unittest.main()
