import pathlib,tempfile,unittest
from deployment_path_audit import inspect
class DeploymentPathAuditTests(unittest.TestCase):
 def test_existing_ubuntu_writable_sandbox_rejected(self):
  p=pathlib.Path(__file__).parent
  r=inspect(p,"/etc/frequency-refund/trust.env",1001,1002,1003)
  self.assertEqual(r["verdict"],"HOLD")
  self.assertTrue(any(s.startswith("non-root-owned-path") for s in r["problems"]))
  self.assertIn("trust-file-missing",r["problems"])
 def test_same_identity_rejected(self):
  r=inspect("/opt/frequency-refund","/etc/frequency-refund/trust.env",1001,1001,1002)
  self.assertIn("distinct-identities-required",r["problems"])
 def test_missing_group_rejected(self):
  r=inspect("/opt/frequency-refund","/etc/frequency-refund/trust.env",1001,1002,None)
  self.assertIn("client-socket-group-required",r["problems"])
