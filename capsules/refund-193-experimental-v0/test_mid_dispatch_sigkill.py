import json,os,pathlib,signal,socket,sqlite3,subprocess,sys,time,unittest
from hashlib import sha256
ROOT=pathlib.Path(__file__).parent
from test_cross_native import prepare_cross_fixture,native_aps
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import TEST_KEYRING

class MidDispatch(unittest.TestCase):
 def setUp(self): prepare_cross_fixture(self)
 def operation(self):
  aps=native_aps(self.fixture,self.fixture["public_key"],self.fixture["boundary_identity"])
  pic=verify_pic_refund(self.pic,TEST_KEYRING)
  return {"schema":"refund-execution/0.1","operation_id":"refund-"+sha256(aps["approval_ref"].encode()).hexdigest(),
          "tool":"refund","arguments":aps["arguments"],"approval_ref":aps["approval_ref"],
          "aps_evidence_ref":aps["evidence_ref"],"pic_evidence_ref":pic["evidence_ref"]}
 def test_sigkill_between_provider_commit_and_reply(self):
   state=self.root/"process-state";state.mkdir();sock=self.root/"broker.sock";marker=self.root/"commit.marker"
   slow=self.root/"slow.py";simple=self.root/"simple.py"
   common="""import os,sys
sys.path.insert(0,%r)
from refund_broker import Broker
from broker_native_verifier import build_native_verifier
verifier=build_native_verifier(sys.argv[4],sys.argv[5],sys.argv[6])
"""%str(ROOT)
   slow.write_text(common+"""import time,pathlib
with Broker(sys.argv[1],sys.argv[2],os.getuid(),verifier) as b:
 original=b.engine.simulator.dispatch
 def dispatch(**kwargs):
  outcome=original(**kwargs);pathlib.Path(sys.argv[3]).write_text('provider-effect-persisted');time.sleep(30);return outcome
 b.engine.simulator.dispatch=dispatch;b.serve_forever()
""")
   simple.write_text(common+"""with Broker(sys.argv[1],sys.argv[2],os.getuid(),verifier) as b:b.serve_forever()
""")
   env={**os.environ,"PYTHONPATH":str(ROOT)}
   def start(slow_mode):
    if sock.exists():sock.unlink()
    p=subprocess.Popen([sys.executable,str(slow if slow_mode else simple),str(sock),str(state),str(marker),self.fixture["public_key"],self.fixture["boundary_identity"],str(TEST_KEYRING)],env=env)
    for _ in range(300):
     if sock.exists():break
     time.sleep(.01)
    self.assertTrue(sock.exists());return p
   op=self.operation();request=(json.dumps({"operation":op,"admission_evidence":{"aps":self.fixture,"pic":self.pic}})+"\n").encode()
   p=start(True)
   try:
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
     s.settimeout(3);s.connect(str(sock));s.sendall(request)
     for _ in range(300):
      if marker.exists():break
      time.sleep(.01)
     self.assertTrue(marker.exists(),"provider-commit-marker-not-seen");os.kill(p.pid,signal.SIGKILL);p.wait(timeout=3)
    with sqlite3.connect(state/"broker-admissions.sqlite") as c:status=c.execute("SELECT status FROM claims WHERE approval=?",(op["approval_ref"],)).fetchone()[0]
    self.assertEqual(status,"in_flight")
    p=start(False)
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
     s.settimeout(3);s.connect(str(sock));s.sendall(request);answer=json.loads(s.makefile().readline())
    self.assertEqual(answer["error"],"broker-denied");self.assertEqual(len(json.loads((state/"simulator"/"effects.json").read_text())),1)
   finally:
    if p.poll() is None:p.kill();p.wait(timeout=3)
if __name__=="__main__":unittest.main()
