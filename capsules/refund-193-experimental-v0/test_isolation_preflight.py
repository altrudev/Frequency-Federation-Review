import unittest
from os_isolation_preflight import check
class IsolationPreflightTests(unittest.TestCase):
 def test_absent_install_is_hold(self):
  result=check("/opt/frequency-refund")
  self.assertEqual(result["verdict"],"HOLD")
  self.assertFalse(next(f for f in result["findings"] if f["id"]=="OS-IDENTITY")["pass"])
  self.assertFalse(next(f for f in result["findings"] if f["id"]=="BROKER-ENTRYPOINT")["pass"])
 def test_unprotected_user_home_target_denied(self):
  result=check("/home/ubuntu/frequency-refund-integration-radial")
  self.assertEqual(result["verdict"],"HOLD")
  self.assertFalse(next(f for f in result["findings"] if f["id"]=="STATE-LOCATION")["pass"])
