import hashlib
import json
import unittest
from pic_contract_probe import probe

ARGS = {"payment_id": "pay_A", "amount_minor": 4000, "currency": "EUR"}
def digest(args):
    return hashlib.sha256(json.dumps(args, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

class PICContractProbeTests(unittest.TestCase):
    def test_closed_synthetic_pair_never_authorizes(self):
        x = probe({"arguments": ARGS}, {"args_digest": digest(ARGS), "result": "allow"})
        self.assertEqual(x["verdict"], "NOT_ESTABLISHED")
        self.assertEqual(x["syntax_and_digest"], "PASS")
        self.assertFalse(x["execution_authorized"])
    def test_missing_or_extra_result_arguments_rejected(self):
        for result in (
            {"args_digest": digest(ARGS), "result": "allow", "arguments": ARGS},
            {"args_digest": digest(ARGS)},
        ):
            with self.subTest(result=result):
                self.assertEqual(probe({"arguments": ARGS}, result)["verdict"], "FAIL")
    def test_mismatch_and_denial_rejected(self):
        for result in ({"args_digest": "0"*64, "result": "allow"},
                       {"args_digest": digest(ARGS), "result": "deny"}):
            self.assertEqual(probe({"arguments": ARGS}, result)["verdict"], "FAIL")
    def test_coercion_and_unknown_proposal_rejected(self):
        for proposal in ({"arguments": dict(ARGS, amount_minor=True)}, {"arguments": ARGS, "extra": 1}):
            self.assertEqual(probe(proposal, {"args_digest": digest(ARGS), "result": "allow"})["verdict"], "FAIL")
    def test_result_never_proves_signature(self):
        x = probe({"arguments": ARGS}, {"args_digest": digest(ARGS), "result": "allow"})
        self.assertEqual(x["native_pic_verification"], "NOT_ESTABLISHED")

if __name__ == "__main__":
    unittest.main()
