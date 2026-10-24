import unittest
from web_attention import news_query, collect, enrich_news

class WebAttentionTests(unittest.TestCase):
    def test_short_ambiguous_ticker_skipped(self):
        self.assertIsNone(news_query("UP","base"))
        self.assertEqual(collect({"symbol":"UP","network":"base"})["status"],"ambiguous_identity")
    def test_news_is_sample_not_trend(self):
        def fake(_url):
            return {"articles":[{"title":"VELVET crypto expands on Base","url":"https://example.org/news","domain":"example.org","seendate":"20261024T110000Z"},
                                {"title":"VELVET crypto expands on Base","url":"https://example.org/news","domain":"example.org"}]}
        r=collect({"symbol":"VELVET","network":"base"},fake)
        self.assertEqual(r["sample_count_24h"],1)
        self.assertEqual(r["trend_status"],"not_established")
    def test_unqueried_candidates_visible_as_unqueried(self):
        xs=[{"symbol":"UP","network":"base","research_priority":1}]
        self.assertEqual(enrich_news(xs,limit=0),0)
        self.assertEqual(xs[0]["web_attention"]["status"],"not_sampled_this_run")
if __name__=="__main__":
    unittest.main()
