import json,os,pathlib,tempfile,unittest
from refund_broker import Broker
from broker_reconcile import inspect_claim
from refund_sandbox import RefundExecutionEngine
class ReconcileTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup)
  self.root=pathlib.Path(self.t.name)
  self.b=Broker(self.root/"broker.sock",self.root/"state",os.getuid(),lambda op,e:True)
  self.addCleanup(self.b.server_close)
 def claim(self, approval, status="in_flight"):
  with self.b.journal_lock:
   self.b.journal.execute("INSERT INTO claims VALUES (?,?,?)",(approval,"sha256-test-binding",status))
 def test_pre_dispatch_claim_only_no_effect(self):
  self.claim("pre")
  r=inspect_claim(self.b,"pre")
  self.assertEqual(r["claim_status"],"in_flight")
  self.assertEqual(r["matching_operations"],[])
  self.assertFalse(r["dispatch_attempted"])
  self.assertEqual(self.b.engine.simulator.effect_count(),0)
 def test_post_provider_effect_is_observed_not_replayed(self):
  op={"schema":"refund-execution/0.1","operation_id":"op1","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"approval_ref":"post","aps_evidence_ref":"aps","pic_evidence_ref":"pic"}
  self.claim("post")
  self.b.engine.execute(op,lose_response_after_commit=True)
  r=inspect_claim(self.b,"post")
  self.assertEqual(r["matching_operations"][0]["executor_status"],"unresolved")
  self.assertEqual(r["matching_operations"][0]["local_effect_integrity"],"local_effect_binding_verified")
  self.assertEqual(self.b.engine.simulator.effect_count(),1)
  self.assertFalse(r["dispatch_attempted"])
 def test_mismatched_effect_is_flagged_without_dispatch(self):
  op={"schema":"refund-execution/0.1","operation_id":"op2","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"approval_ref":"tampered","aps_evidence_ref":"aps","pic_evidence_ref":"pic"}
  self.claim("tampered")
  self.b.engine.execute(op)
  record=self.b.engine._load_record("op2")
  effects_path=self.b.engine.simulator.effects_path
  effects=json.loads(effects_path.read_text())
  effects[record["idempotency_key"]]["arguments_digest"]="wrong"
  effects_path.write_text(json.dumps(effects))
  r=inspect_claim(self.b,"tampered")
  self.assertEqual(r["matching_operations"][0]["local_effect_integrity"],"local_effect_binding_mismatch")
  self.assertFalse(r["dispatch_attempted"])
 def test_read_only_does_not_recover_or_release(self):
  self.claim("unknown")
  before=self.b.journal.execute("SELECT status FROM claims WHERE approval='unknown'").fetchone()
  inspect_claim(self.b,"unknown")
  after=self.b.journal.execute("SELECT status FROM claims WHERE approval='unknown'").fetchone()
  self.assertEqual(before,after)
if __name__=="__main__":unittest.main()
