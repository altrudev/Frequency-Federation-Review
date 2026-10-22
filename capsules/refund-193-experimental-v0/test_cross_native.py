import copy,json,os,pathlib,subprocess,tempfile,unittest
ROOT=pathlib.Path(__file__).resolve().parent
APS=ROOT/"aps-runtime"
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import MOD,TEST_KEYRING
from test_support.admission_gateway import RefundAdmissionGateway,AdmissionDenied
from refund_sandbox import RefundExecutionEngine

def native_aps(artifact,key,issuer):
    p=subprocess.run(["node","--import","tsx","verify-refund.ts"],cwd=APS,input=json.dumps(artifact),text=True,capture_output=True,env={**os.environ,"APS_TRUSTED_KEY":key,"APS_TRUSTED_ISSUER":issuer},timeout=10)
    if p.returncode:raise ValueError(p.stdout or p.stderr)
    x=json.loads(p.stdout)
    if x.get("valid") is not True:raise ValueError("native APS denied")
    x.pop("valid")
    return x

def prepare_cross_fixture(case):
    t=tempfile.TemporaryDirectory();case.addCleanup(t.cleanup)
    case.root=pathlib.Path(t.name)
    args={"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"}
    p=subprocess.run(["node","--import","tsx","make-test-fixture.ts"],cwd=APS,input=json.dumps({"arguments":args}),text=True,capture_output=True,check=True,timeout=10)
    case.fixture=json.loads(p.stdout)
    md=json.loads((MOD.FIXTURES_DIR/"merchant_decision.json").read_text())
    md["approval_ref"]=case.fixture["approval_ref"]
    case.pic=MOD.build_signed_proposal(merchant_decision=md)
    case.engine=RefundExecutionEngine(case.root/"executor")
    case.gate=RefundAdmissionGateway(case.root/"gate.sqlite",lambda a:native_aps(a,case.fixture["public_key"],case.fixture["boundary_identity"]),lambda p:verify_pic_refund(p,TEST_KEYRING),case.engine)

class CrossNativeTests(unittest.TestCase):
 def setUp(self): prepare_cross_fixture(self)
 def perform(self,a=None,p=None):
    return self.gate.execute(approval=native_aps(self.fixture,self.fixture["public_key"],self.fixture["boundary_identity"]),aps_artifact=a or self.fixture,pic_artifact=p or self.pic)
 def test_native_aps_pic_and_execution(self):
    self.assertEqual(self.perform()["status"],"observed_success");self.assertEqual(self.engine.simulator.effect_count(),1)
    with self.assertRaises(AdmissionDenied):self.perform()
 def test_tampered_aps_receipt_rejected(self):
    a=copy.deepcopy(self.fixture);a["receipt"]["result"]["verdict"]="deny"
    with self.assertRaises(AdmissionDenied):self.perform(a=a)
    self.assertEqual(self.engine.simulator.effect_count(),0)
 def test_tampered_pic_payment_rejected(self):
    p=copy.deepcopy(self.pic);p["action"]["args"]["payment_id"]="pay_B"
    with self.assertRaises(AdmissionDenied):self.perform(p=p)
    self.assertEqual(self.engine.simulator.effect_count(),0)
if __name__=="__main__":unittest.main()
