import json,os,pathlib,signal,socket,sqlite3,subprocess,sys,time,unittest
from hashlib import sha256
ROOT=pathlib.Path(__file__).parent
from test_cross_native import prepare_cross_fixture,native_aps
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import TEST_KEYRING

class RestartTest(unittest.TestCase):
 def setUp(self): prepare_cross_fixture(self)
 def operation(self):
  aps=native_aps(self.fixture,self.fixture["public_key"],self.fixture["boundary_identity"])
  pic=verify_pic_refund(self.pic,TEST_KEYRING)
  return {"schema":"refund-execution/0.1","operation_id":"refund-"+sha256(aps["approval_ref"].encode()).hexdigest(),
          "tool":"refund","arguments":aps["arguments"],"approval_ref":aps["approval_ref"],
          "aps_evidence_ref":aps["evidence_ref"],"pic_evidence_ref":pic["evidence_ref"]}
 def test_killed_broker_retains_claim_and_prevents_redispatch(self):
   state=self.root/"process-state";state.mkdir();sock=self.root/"broker.sock";runner=self.root/"runner.py"
   runner.write_text("""import os,sys
sys.path.insert(0,%r)
from refund_broker import Broker
from broker_native_verifier import build_native_verifier
verifier=build_native_verifier(sys.argv[3],sys.argv[4],sys.argv[5])
with Broker(sys.argv[1],sys.argv[2],os.getuid(),verifier) as b:b.serve_forever()
"""%str(ROOT))
   env={**os.environ,"PYTHONPATH":str(ROOT)}
   def start():
    if sock.exists():sock.unlink()
    p=subprocess.Popen([sys.executable,str(runner),str(sock),str(state),self.fixture["public_key"],self.fixture["boundary_identity"],str(TEST_KEYRING)],env=env)
    for _ in range(200):
     if sock.exists():break
     time.sleep(.01)
    self.assertTrue(sock.exists());return p
   op=self.operation();request=(json.dumps({"operation":op,"admission_evidence":{"aps":self.fixture,"pic":self.pic}})+"\n").encode()
   def submit():
    with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as s:
     s.connect(str(sock));s.sendall(request);return json.loads(s.makefile().readline())
   p=start()
   try:
    first=submit();self.assertEqual(first["result"]["status"],"observed_success")
    os.kill(p.pid,signal.SIGKILL);p.wait(timeout=3)
    p=start();second=submit();self.assertEqual(second["error"],"broker-denied")
    self.assertEqual(len(json.loads((state/"simulator"/"effects.json").read_text())),1)
    with sqlite3.connect(state/"broker-admissions.sqlite") as c:self.assertEqual(c.execute("SELECT count(*) FROM claims").fetchone()[0],1)
   finally:
    if p.poll() is None:p.kill();p.wait(timeout=3)
if __name__=="__main__":unittest.main()
