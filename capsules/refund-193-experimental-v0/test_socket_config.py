import os,pathlib,stat,tempfile,unittest,sys
sys.path[:0]=["/home/ubuntu/frequency-refund-integration-radial"]
from refund_broker import Broker
class SocketConfigTests(unittest.TestCase):
 def test_explicit_client_gid_socket_mode(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   b=Broker(root/"broker.sock",root/"state",os.getuid(),socket_gid=os.getgid())
   try:
    s=(root/"broker.sock").stat()
    self.assertEqual(stat.S_IMODE(s.st_mode),0o660)
    self.assertEqual(s.st_gid,os.getgid())
   finally:b.server_close()
 def test_default_mode_remains_private(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   b=Broker(root/"broker.sock",root/"state",os.getuid())
   try:self.assertEqual(stat.S_IMODE((root/"broker.sock").stat().st_mode),0o600)
   finally:b.server_close()
 def test_no_client_identity_denied(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d)
   with self.assertRaises(ValueError):Broker(root/"broker.sock",root/"state",None)
