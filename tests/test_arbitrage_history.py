import unittest
from arbitrage_history import merge
class HistoryTests(unittest.TestCase):
    def test_observations_not_interpolated(self):
        old={"generated_at_utc":"2026-10-28T01:00:00Z","opportunities":[{"symbol":"BTC","buy_exchange":"a","sell_exchange":"b","gross_spread_pct":2}]}
        now={"generated_at_utc":"2026-10-28T02:00:00Z","opportunities":[{"symbol":"BTC","buy_exchange":"a","sell_exchange":"b","gross_spread_pct":3}]}
        result=merge(old,now)
        self.assertEqual(len(result[0]["observations"]),2)
        self.assertEqual(result[0]["observations"][-1]["spread_pct"],3)
    def test_deduplicates_current_timestamp(self):
        current={"generated_at_utc":"2026-10-28T02:00:00Z","opportunities":[{"symbol":"BTC","buy_exchange":"a","sell_exchange":"b","gross_spread_pct":3}]}
        self.assertEqual(len(merge(current,current)[0]["observations"]),1)
if __name__=="__main__": unittest.main()
