import unittest
from datetime import datetime,timezone,timedelta
from correlation import relationship, closed_candles, measure

class CorrelationTests(unittest.TestCase):
 def test_inverse(self):
  base=datetime(2026,1,1)
  a={}; b={}
  x=y=100.
  for i in range(36):
   d=(base+timedelta(days=i)).strftime('%Y-%m-%d')
   change=.03 if i%3==0 else -.017 if i%3==1 else .012
   x*=1+change;y*=1-change
   a[d]=x;b[d]=y
  self.assertLess(relationship(a,b,"daily",12)["coefficient"],-.95)
 def test_missing(self):
  self.assertEqual(relationship({},{},"daily",12)["status"],"insufficient_data")
 def test_unclosed(self):
  stamp=int(datetime(2026,1,10,tzinfo=timezone.utc).timestamp())
  self.assertEqual(closed_candles([(stamp,10)],"day",stamp+100),{})
 def test_stale_gap(self):
  a={"2026-01-01":1,"2026-01-03":2};b={"2026-01-01":3,"2026-01-03":4}
  self.assertEqual(relationship(a,b,"daily",1)["observations"],0)

if __name__=="__main__":unittest.main()
