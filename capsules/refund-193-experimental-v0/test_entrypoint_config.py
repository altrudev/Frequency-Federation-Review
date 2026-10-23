import base64,json,pathlib,subprocess,sys,tempfile,unittest
from refund_broker_entrypoint import load_config
from pic_test_fixture import TEST_KEYRING
class EntrypointConfigTests(unittest.TestCase):
 def make(self,root,**overrides):
  data={"socket_path":str(root/"run"/"broker.sock"),"state_dir":str(root/"state"),
        "authorized_client_uid":1234,"aps_trusted_key":"public-test-key",
        "aps_trusted_issuer":"test-issuer","pic_keyring_path":str(TEST_KEYRING),
        "simulator_only":True,"experimental_handoff_keys":{"test":base64.b64encode(bytes(range(32))).decode()}}
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

 def test_missing_or_malformed_handoff_trust_refused(self):
  for value in (None,{},[],{"test":"bad"},{"test":"AA=="},{"":"AA=="}):
   with self.subTest(value=value),tempfile.TemporaryDirectory() as td:
    root=pathlib.Path(td)
    with self.assertRaises(ValueError):load_config(self.make(root,experimental_handoff_keys=value))
    self.assertFalse((root/"state").exists())
 def test_legacy_config_refused(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);p=self.make(root)
   data=json.loads(p.read_text());del data["experimental_handoff_keys"];p.write_text(json.dumps(data))
   with self.assertRaises(ValueError):load_config(p)
   self.assertFalse((root/"state").exists())

 def test_check_rejects_missing_handoff_trust_without_socket(self):
  with tempfile.TemporaryDirectory() as td:
   root=pathlib.Path(td);p=self.make(root,experimental_handoff_keys={})
   result=subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name("refund_broker_entrypoint.py")),"--config",str(p),"--check"],capture_output=True,text=True)
   self.assertNotEqual(result.returncode,0)
   self.assertNotIn("CONFIG_OK",result.stdout)
   self.assertFalse((root/"run"/"broker.sock").exists())
   self.assertFalse((root/"state").exists())

 def test_runtime_composition_requires_handoff_and_native_success(self):
  from unittest.mock import patch
  from test_provisional_handoff_193 import ExperimentalHandoffTests
  from cryptography.hazmat.primitives.serialization import Encoding,PublicFormat
  from refund_broker_entrypoint import build_runtime_verifier
  fixture=ExperimentalHandoffTests();fixture.setUp()
  config={"aps_trusted_key":"test-only","aps_trusted_issuer":"test-only","pic_keyring_path":str(TEST_KEYRING),
          "experimental_handoff_keys":{"sandbox-issuer":base64.b64encode(fixture.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()}}
  with patch("refund_broker_entrypoint.build_native_verifier") as factory:
   native=factory.return_value;native.return_value=True
   verify=build_runtime_verifier(config)
   for evidence in ({"aps":{},"pic":{}},{"aps":{},"pic":{},"handoff":{}},
                    {"aps":{},"pic":{},"handoff":fixture.signed({**fixture.record,"expires_at":1})}):
    self.assertFalse(verify(fixture.op,evidence))
   native.assert_not_called()
   evidence={"aps":"aps-evidence","pic":"pic-evidence","handoff":fixture.signed()}
   self.assertTrue(verify(fixture.op,evidence))
   native.assert_called_once_with(fixture.op,{"aps":"aps-evidence","pic":"pic-evidence"})
   native.return_value=False
   self.assertFalse(verify(fixture.op,evidence))
