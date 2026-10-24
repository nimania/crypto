import unittest
from hourly_technical import closed_prices, assess

class HourlyTests(unittest.TestCase):
    def test_excludes_open_candle(self):
        rows=[[i*3600,1,1,1,100+i,1] for i in range(22)]
        data={"data":{"attributes":{"ohlcv_list":rows}}}
        out=closed_prices(data,now=21*3600+120)
        self.assertEqual(out[-1][0],20*3600)
    def test_breakout_requests_news_only_after_closed_boundary(self):
        rows=[(i*3600,100.0) for i in range(19)]+[(19*3600,110.0)]
        value=assess(rows)
        self.assertTrue(value["news_trigger"])
        self.assertEqual(value["signal"],"PROVISIONAL_HOURLY_BREAKOUT")
    def test_no_news_for_insufficient_data(self):
        self.assertFalse(assess([(0,100.0)])["news_trigger"])
    def test_no_news_for_flat(self):
        self.assertFalse(assess([(i*3600,100.0) for i in range(20)])["news_trigger"])
if __name__=="__main__":unittest.main()
