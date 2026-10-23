import unittest
from datetime import datetime, timezone
from btc_reactions import classify_reaction

START = int(datetime(2026, 1, 5, tzinfo=timezone.utc).timestamp())
ZONE = {"lower":99, "upper":101}

def rows(values):
    return [(START + i*86400, value) for i,value in enumerate(values)]

def check(values, side, previous=None):
    return classify_reaction(rows(values), ZONE, side, previous,
                             now=START + (len(values)+1)*86400)

class TestReactions(unittest.TestCase):
    def test_support_rebound(self):
        self.assertEqual(check([105,100,104],"support")["status"],"support_rebound")
    def test_resistance_rejection(self):
        self.assertEqual(check([95,100,96],"resistance")["status"],"resistance_rejection")
    def test_break_pending(self):
        self.assertEqual(check([106,104,97],"support")["status"],"break_pending")
    def test_confirmed_daily(self):
        self.assertEqual(check([103,97,96],"support")["status"],"confirmed_daily_acceptance")
    def test_retest_in_progress(self):
        self.assertEqual(check([97,96,100],"support",{"status":"confirmed_break"})["status"],"retest_in_progress")
    def test_reclaim_above_lost_support(self):
        self.assertEqual(check([96,97,103],"support",{"status":"confirmed_break"})["status"],"retest_failed")
    def test_missing_candles(self):
        self.assertEqual(check([100,101],"support")["status"],"insufficient_data")

if __name__=="__main__":
    unittest.main()
