import unittest
from btc_levels import monitor

class BTCLevelTests(unittest.TestCase):
    def test_missing_candles(self):
        self.assertEqual(monitor([],{}).get("status"),"insufficient_data")
    def test_zone_from_pivot(self):
        rows=[(1704067200+i*86400,100.0+i) for i in range(4)]
        output=monitor(rows,{"support":90.0,"resistance":120.0},now=1704067200+5*86400)
        self.assertEqual(output["status"],"observed")
        self.assertEqual(output["support_status"],"inside_or_safe_side")
    def test_break_requires_two_closes(self):
        start=1704067200
        rows=[(start+i*86400,v) for i,v in enumerate([100,101,103,106])]
        prev={"resistance":{"anchor":100,"lower":99.2,"upper":100.8,"source":"weekly_close_fractal"},"resistance_status":"inside_or_safe_side"}
        result=monitor(rows,{},prev,now=start+5*86400)
        self.assertEqual(result["resistance_status"],"confirmed_daily_acceptance")
        self.assertEqual(len(result["events"]),1)

    def test_weekly_close_is_separate_from_daily_signal(self):
        start=1704067200
        rows=[(start+i*86400,100+i) for i in range(4)]
        result=monitor(rows,{"resistance":102},now=start+5*86400)
        self.assertIn("weekly_confirmation",result)
        self.assertEqual(result["weekly_confirmation"]["resistance"]["status"],"unavailable")
