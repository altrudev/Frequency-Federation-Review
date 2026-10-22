import copy,json,os,socket,threading,unittest
from test_cross_native import prepare_cross_fixture,native_aps
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import TEST_KEYRING
from broker_native_verifier import build_native_verifier
from refund_broker import Broker
from hashlib import sha256

class NativeBrokerTests(unittest.TestCase):
 def setUp(self):
  prepare_cross_fixture(self)
  self.sock=self.root/"broker.sock"
  self.broker=Broker(self.sock,self.root/"broker-state",os.getuid(),build_native_verifier(self.fixture["public_key"],self.fixture["boundary_identity"],TEST_KEYRING))
  self.thread=threading.Thread(target=self.broker.serve_forever,daemon=True);self.thread.start();self.addCleanup(self.stop)
 def stop(self): self.broker.shutdown();self.broker.server_close();self.thread.join(timeout=3)
 def send(self,operation,aps=None,pic=None):
  with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
   s.connect(str(self.sock));s.sendall((json.dumps({"operation":operation,"admission_evidence":{"aps":aps or self.fixture,"pic":pic or self.pic}})+"\n").encode());return json.loads(s.makefile().readline())
 def operation(self):
  aps=native_aps(self.fixture,self.fixture["public_key"],self.fixture["boundary_identity"]);pic=verify_pic_refund(self.pic,TEST_KEYRING)
  return {"schema":"refund-execution/0.1","operation_id":"refund-"+sha256(aps["approval_ref"].encode()).hexdigest(),"tool":"refund","arguments":aps["arguments"],"approval_ref":aps["approval_ref"],"aps_evidence_ref":aps["evidence_ref"],"pic_evidence_ref":pic["evidence_ref"]}
 def test_broker_allows_native_verified_fixture(self):
  out=self.send(self.operation());self.assertEqual(out["result"]["status"],"observed_success");self.assertEqual(self.broker.engine.simulator.effect_count(),1)
  with self.broker.journal_lock: events=[r[0] for r in self.broker.journal.execute("SELECT event FROM audit_events ORDER BY id").fetchall()]
  self.assertIn("dispatch-result",events)
 def test_broker_consumes_approval_durably(self):
  op=self.operation();self.assertEqual(self.send(op)["result"]["status"],"observed_success");self.assertEqual(self.send(op)["error"],"broker-denied");self.assertEqual(self.broker.engine.simulator.effect_count(),1)
  with self.broker.journal_lock: row=self.broker.journal.execute("SELECT status FROM claims WHERE approval=?",(op["approval_ref"],)).fetchone()
  self.assertEqual(row[0],"observed_success")
  with self.broker.journal_lock: events=[r[0] for r in self.broker.journal.execute("SELECT event FROM audit_events ORDER BY id").fetchall()]
  self.assertIn("approval-claimed-or-uncertain",events)
 def test_broker_refuses_argument_substitution(self):
  op=self.operation();op["arguments"]={**op["arguments"],"amount_minor":4100};self.assertEqual(self.send(op)["error"],"broker-denied");self.assertEqual(self.broker.engine.simulator.effect_count(),0)
 def test_broker_refuses_pic_tamper(self):
  op=self.operation();pic=copy.deepcopy(self.pic);pic["action"]["args"]["payment_id"]="pay_B";self.assertEqual(self.send(op,pic=pic)["error"],"broker-denied");self.assertEqual(self.broker.engine.simulator.effect_count(),0)
if __name__=="__main__":unittest.main()
