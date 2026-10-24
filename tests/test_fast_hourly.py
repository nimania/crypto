import unittest
from fast_hourly import evaluate,key

class FastHourlyTests(unittest.TestCase):
    def test_identity_is_network_and_contract(self):
        self.assertNotEqual(key({"network":"base","contract":"0xABC"}),
                            key({"network":"arbitrum","contract":"0xABC"}))
    def test_no_duplicate_event_for_same_closed_candle(self):
        calls=[]
        def fetch(url):
            rows=[[i*3600,0,0,0,100 if i<19 else 110,0] for i in range(20)]
            return {"data":{"attributes":{"ohlcv_list":rows}}}
        item={"network":"base","contract":"0xABC","pool":"0xpool","symbol":"VELVET"}
        import unittest.mock as mock
        with mock.patch("fast_hourly.closed_prices",side_effect=lambda payload:[(i*3600,100 if i<19 else 110) for i in range(20)]):
            result=evaluate([item],requester=fetch,news_fetcher=lambda url:{"articles":[]},sleep=lambda n:None)
            previous=result["tokens"][key(item)]
            second=evaluate([item],previous={"tokens":{key(item):previous}},
                            requester=fetch,news_fetcher=lambda url:{"articles":[]},sleep=lambda n:None)
        self.assertTrue(previous["new_event"])
        self.assertFalse(second["tokens"][key(item)]["new_event"])
    def test_api_failure_is_not_no_signal(self):
        item={"network":"base","contract":"0xABC","pool":"0xpool"}
        def broken(url):raise RuntimeError("source down")
        result=evaluate([item],requester=broken,sleep=lambda n:None)
        self.assertEqual(result["tokens"][key(item)]["status"],"unavailable")
if __name__=="__main__":unittest.main()
