import pathlib,sys,tempfile,unittest
sys.path[:0]=["/home/ubuntu/frequency-refund-integration-radial"]
from test_support.admission_gateway import RefundAdmissionGateway,AdmissionDenied
from refund_sandbox import RefundExecutionEngine

class CrashAndBoundaryTests(unittest.TestCase):
 def setUp(self):
  t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
  self.base=pathlib.Path(t.name)
  self.a={"approval_ref":"a1","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"decision":"permit","evidence_ref":"aps1"}
  self.p={**self.a,"evidence_ref":"pic1"}
 def gateway(self,executor):
  return RefundAdmissionGateway(self.base/"admission.db",lambda v:v,lambda v:v,executor)
 def test_dispatch_crash_consumes_approval_no_second_effect(self):
  class Crash:
   def execute(self,op):raise RuntimeError("crash-before-provider")
  gate=self.gateway(Crash())
  with self.assertRaises(RuntimeError):gate.execute(approval=self.a,aps_artifact=self.a,pic_artifact=self.p)
  engine=RefundExecutionEngine(self.base/"exec")
  second=self.gateway(engine)
  with self.assertRaisesRegex(AdmissionDenied,"consumed"):
   second.execute(approval=self.a,aps_artifact=self.a,pic_artifact=self.p)
  self.assertEqual(engine.simulator.effect_count(),0)
 def test_no_verifier_functions_refused(self):
  with self.assertRaises(ValueError):RefundAdmissionGateway(self.base/"bad.db",None,None,None)
if __name__=="__main__":unittest.main()
