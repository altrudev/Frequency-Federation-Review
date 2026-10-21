"""Test-only access to upstream refund example builders and fixture trust."""
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parent/"pic-standard"
SPEC=importlib.util.spec_from_file_location("pic_refund_fixture",ROOT/"examples/refund-approval/sign_and_verify.py")
MOD=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)
TEST_KEYRING=ROOT/"examples/refund-approval/keys/pic_keys.example.json"
