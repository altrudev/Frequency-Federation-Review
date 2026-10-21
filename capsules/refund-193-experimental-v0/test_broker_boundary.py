import json,os,pathlib,socket,threading,tempfile,unittest,sys

from refund_broker import Broker

class BrokerTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
    root=pathlib.Path(self.tmp.name)
    self.broker=Broker(root/"broker.sock",root/"state",os.getuid())
    self.thread=threading.Thread(target=self.broker.serve_forever,daemon=True);self.thread.start()
    self.addCleanup(self.stop)
    self.sock=root/"broker.sock"
 def stop(self):
    self.broker.shutdown();self.broker.server_close();self.thread.join(timeout=3)
 def send(self,obj):
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
      s.connect(str(self.sock))
      s.sendall((json.dumps(obj)+"\n").encode())
      return json.loads(s.makefile().readline())
 def events(self):
    with self.broker.journal_lock:
      return [r[0] for r in self.broker.journal.execute("SELECT event FROM audit_events ORDER BY id").fetchall()]
 def test_peer_uid_mismatch_denied_before_verification(self):
    self.broker.allowed_uid=os.getuid()+10000
    op={"schema":"refund-execution/0.1","operation_id":"peer-test","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"approval_ref":"fake","pic_evidence_ref":"fake","aps_evidence_ref":"fake"}
    self.assertEqual(self.send({"operation":op,"admission_evidence":{}})["error"],"peer-denied")
    self.assertEqual(self.broker.engine.simulator.effect_count(),0)
    self.assertIn("peer-denied",self.events())
 def test_unsupported_command_denied(self):
    self.assertEqual(self.send({"action":"shell"})["error"],"broker-denied")
    self.assertIn("unsupported-command",self.events())
 def test_unverified_execution_denied_to_same_uid(self):
    op={"schema":"refund-execution/0.1","operation_id":"unadmitted","tool":"refund","arguments":{"payment_id":"pay_A","amount_minor":4000,"currency":"EUR"},"approval_ref":"fake","pic_evidence_ref":"fake","aps_evidence_ref":"fake"}
    r=self.send({"operation":op,"admission_evidence":{"claimed":"true"}})
    self.assertEqual(r["error"],"broker-denied")
    self.assertEqual(self.broker.engine.simulator.effect_count(),0)
    self.assertIn("admission-verifier-unconfigured",self.events())
if __name__=="__main__":unittest.main()
