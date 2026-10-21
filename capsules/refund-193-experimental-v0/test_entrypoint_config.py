import json,pathlib,tempfile,unittest
from refund_broker_entrypoint import load_config
from pic_test_fixture import TEST_KEYRING
class EntrypointConfigTests(unittest.TestCase):
 def make(self,root,**overrides):
  data={"socket_path":str(root/"run"/"broker.sock"),"state_dir":str(root/"state"),
        "authorized_client_uid":1234,"aps_trusted_key":"public-test-key",
        "aps_trusted_issuer":"test-issuer","pic_keyring_path":str(TEST_KEYRING),
        "simulator_only":True}
  data.update(overrides);(root/"run").mkdir()
  p=root/"config.json";p.write_text(json.dumps(data));return p
 def test_explicit_simulator_config_loads(self):
  with tempfile.TemporaryDirectory() as td:
   c=load_config(self.make(pathlib.Path(td)));self.assertTrue(c["simulator_only"])
 def test_real_provider_mode_refused(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):load_config(self.make(pathlib.Path(td),simulator_only=False))
 def test_missing_pic_trust_refused(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(ValueError):load_config(self.make(pathlib.Path(td),pic_keyring_path="/missing/keyring.json"))
