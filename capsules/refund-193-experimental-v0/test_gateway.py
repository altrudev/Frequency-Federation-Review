import sys,tempfile,pathlib,unittest
from test_support.admission_gateway import RefundAdmissionGateway,AdmissionDenied
from refund_sandbox import RefundExecutionEngine
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  root=pathlib.Path(self.t.name)
  self.engine=RefundExecutionEngine(root/"exec")
  self.gate=RefundAdmissionGateway(root/"gate.db",lambda x:x if x.get("verified") else (_ for _ in ()).throw(ValueError("bad APS")),lambda x:x if x.get("verified") else (_ for _ in ()).throw(ValueError("bad PIC")),self.engine)
  self.a={"approval_ref":"a1","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"decision":"permit","evidence_ref":"aps1","verified":True}
  self.p={**self.a,"evidence_ref":"pic1"}
 def call(self):
  return self.gate.execute(approval=self.a,aps_artifact=self.a,pic_artifact=self.p)
 def test_allowed_then_replay_denied(self):
  self.assertEqual(self.call()["status"],"observed_success")
  with self.assertRaises(AdmissionDenied):self.call()
  self.assertEqual(self.engine.simulator.effect_count(),1)
 def test_unverified_no_effect(self):
  self.a["verified"]=False
  with self.assertRaises(AdmissionDenied):self.call()
  self.assertEqual(self.engine.simulator.effect_count(),0)
 def test_changed_amount_no_effect(self):
  self.p["arguments"]={**self.p["arguments"],"amount_minor":4100}
  with self.assertRaises(AdmissionDenied):self.call()
  self.assertEqual(self.engine.simulator.effect_count(),0)
 def test_refusal_no_effect(self):
  self.a["decision"]="deny"
  with self.assertRaises(AdmissionDenied):self.call()
  self.assertEqual(self.engine.simulator.effect_count(),0)
if __name__=="__main__":unittest.main()
