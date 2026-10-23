import unittest
from datetime import datetime,timezone,timedelta
from btc_structure import analyze_btc
class StructureTests(unittest.TestCase):
 def test_empty(self):
  self.assertEqual(analyze_btc([])["status"],"insufficient_data")
 def test_never_confirm_historical(self):
  start=datetime(2026,1,5,tzinfo=timezone.utc)
  rows=[(int((start+timedelta(days=i)).timestamp()),100000+i*100) for i in range(40)]
  r=analyze_btc(rows,int((start+timedelta(days=43)).timestamp()))
  self.assertEqual(r["status"],"observed")
  self.assertFalse(r["confirmed_breakout"])
  self.assertEqual(r["zones_status"],"historical_unverified")
if __name__=="__main__":unittest.main()
