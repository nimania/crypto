import unittest
from safety import security_evm,liquidity_assessment

class SafetyTests(unittest.TestCase):
 def test_unsupported_is_not_safe(self):
  self.assertEqual(security_evm("flare","0xabc",lambda url:None)["status"],"not_supported")
 def test_flagged(self):
  def fetch(url):return {"code":1,"result":{"0xabc":{"is_honeypot":"1","is_mintable":"0","is_proxy":"0","is_open_source":"1","is_blacklisted":"0"}}}
  self.assertEqual(security_evm("base","0xABC",fetch)["status"],"risk_detected")
 def test_missing_fields_not_clear(self):
  r=security_evm("base","0xabc",lambda url:{"code":1,"result":{"0xabc":{"is_honeypot":"0"}}})
  self.assertEqual(r["status"],"insufficient_data")
 def test_liquidity_not_verification(self):
  self.assertEqual(liquidity_assessment({"liquidity_usd":100000,"volume_24h_usd":22000})["status"],"reported_not_verified")
if __name__=="__main__":unittest.main()
