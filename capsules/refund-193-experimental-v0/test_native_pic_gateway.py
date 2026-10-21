import pathlib,sys,tempfile,unittest,json
BASE=pathlib.Path(__file__).resolve().parent
sys.path[:0]=[str(BASE)]
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import MOD,TEST_KEYRING
from test_support.admission_gateway import RefundAdmissionGateway,AdmissionDenied
from refund_sandbox import RefundExecutionEngine
class NativePICBoundary(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=pathlib.Path(self.tmp.name)
  d=json.loads((MOD.FIXTURES_DIR/"merchant_decision.json").read_text())
  self.pic=MOD.build_signed_proposal(merchant_decision=d)
  self.aps=verify_pic_refund(self.pic,TEST_KEYRING)
  self.aps["evidence_ref"]="aps-test-stub"
  self.engine=RefundExecutionEngine(self.root/"executor")
  self.gate=RefundAdmissionGateway(self.root/"gate.db",lambda v:v,lambda p:verify_pic_refund(p,TEST_KEYRING),self.engine)
 def call(self,p=None):
  return self.gate.execute(approval=self.aps,aps_artifact=self.aps,pic_artifact=p or self.pic)
 def test_native_pic_then_synthetic_aps_allows_once(self):
  self.assertEqual(self.call()["status"],"observed_success")
  self.assertEqual(self.engine.simulator.effect_count(),1)
 def test_native_pic_rejects_untrusted_fixture_signer(self):
  keyring=self.root/"empty-keyring.json";keyring.write_text('{"trusted_keys":{},"revoked_keys":[]}')
  with self.assertRaises(ValueError):verify_pic_refund(self.pic,keyring)
 def test_native_pic_rejects_mutated_payment(self):
  import copy
  p=copy.deepcopy(self.pic);p["action"]["args"]["payment_id"]="pay_changed"
  with self.assertRaises(AdmissionDenied):self.call(p)
  self.assertEqual(self.engine.simulator.effect_count(),0)
if __name__=="__main__":unittest.main()
