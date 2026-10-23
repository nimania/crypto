import unittest
from datetime import datetime,timezone
from relative_strength import relative_strength

START=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp())
class RelativeStrengthTests(unittest.TestCase):
 def test_outperformance(self):
  btc=[(START+i*86400,100+i) for i in range(40)]
  asset=[(START+i*86400,100+2*i) for i in range(40)]
  result=relative_strength(asset,btc,now=START+41*86400)
  self.assertEqual(result["periods"]["30d"]["status"],"ok")
  self.assertGreater(result["periods"]["30d"]["relative_return_pct"],0)
 def test_sparse(self):
  self.assertEqual(relative_strength([],[])["status"],"insufficient_data")
 def test_unclosed_candle_excluded(self):
  result=relative_strength([(START,100),(START+86400,110)],[(START,100),(START+86400,100)],now=START+86400+10)
  self.assertEqual(result["periods"]["7d"]["status"],"insufficient_data")
