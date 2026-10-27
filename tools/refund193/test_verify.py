import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from verify import assess, parse_json, InvalidEvidence, digest, exact_args, read_regular_nofollow

IDS = dict(workflow_id="w", admission_issuer="issuer", provider_namespace="sim", operation_id="op")
ARGS = dict(payment_id="pay_A", amount_minor=4000, currency="EUR")
REF = "sha256:" + "a" * 64

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.records = {
            "admission": dict(IDS, arguments=ARGS, admission_ref=REF, state="committed"),
            "attempt": dict(IDS, attempt_id="t1", admission_ref=REF, arguments=ARGS, dispatch_status="sent"),
            "effect": dict(IDS, attempt_id="t1", effect_id="e1", admission_ref=REF, arguments=ARGS, outcome="succeeded"),
            "observation": dict(IDS, attempt_id="t1", effect_id="e1", observed_effect=True, verdict="observed_success", cutoff="2026-10-25T12:00:00Z")
        }

    def verify(self):
        files = {}
        for name, data in self.records.items():
            raw = json.dumps(data, sort_keys=True).encode()
            (self.root / (name + ".json")).write_bytes(raw)
            files[name] = {"path": name + ".json", "sha256": "sha256:" + hashlib.sha256(raw).hexdigest()}
        return assess({"schema": "altru-refund-evidence-review/1", "files": files}, self.root)

    def test_valid_synthetic_still_not_established(self):
        x = self.verify()
        self.assertEqual(x["verdict"], "NOT_ESTABLISHED")
        self.assertFalse(x["execution_authorized"])
        self.assertEqual(x["checks"]["recorded_claim_shape"], "PASS")
        self.assertEqual(x["checks"]["temporal_relationship"], "NOT_ESTABLISHED")
        self.assertEqual(x["checks"]["producer_authenticity"], "NOT_ESTABLISHED")
        self.assertTrue(all(c == "PASS" for k, c in x["checks"].items()
                            if k not in ("temporal_relationship", "producer_authenticity")))

    def test_mismatched_effect_operation(self):
        self.records["effect"]["operation_id"] = "other"
        self.assertEqual(self.verify()["verdict"], "FAIL")

    def test_mismatched_attempt(self):
        self.records["observation"]["attempt_id"] = "other"
        self.assertEqual(self.verify()["verdict"], "FAIL")

    def test_changed_effect_args(self):
        self.records["effect"]["arguments"] = dict(ARGS, amount_minor=3999)
        self.assertEqual(self.verify()["verdict"], "FAIL")

    def test_boolean_amount(self):
        self.records["admission"]["arguments"] = dict(ARGS, amount_minor=True)
        self.assertEqual(self.verify()["verdict"], "FAIL")

    def test_no_effect_claim(self):
        self.records["observation"]["observed_effect"] = False
        self.assertEqual(self.verify()["verdict"], "FAIL")

    def test_duplicate_keys(self):
        with self.assertRaises(InvalidEvidence):
            parse_json(b'{"operation_id":"a","operation_id":"b"}')

    def test_file_tampering(self):
        self.verify()
        path = self.root / "effect.json"
        expected = digest(path.read_bytes())
        path.write_text("tamper")
        self.assertNotEqual(digest(path.read_bytes()), expected)

    def test_symlinked_record_denied(self):
        self.verify()
        source = self.root / "effect.json"
        backup = self.root / "outside.json"
        source.rename(backup)
        source.symlink_to(backup)
        with self.assertRaises(OSError):
            read_regular_nofollow(self.root, "effect.json")

    def test_nonsense_cutoff_rejected(self):
        self.records["observation"]["cutoff"] = "gibberish"
        self.assertEqual(self.verify()["checks"]["recorded_claim_shape"], "FAIL")

    def test_invalid_calendar_cutoff_rejected(self):
        self.records["observation"]["cutoff"] = "2026-02-30T12:00:00Z"
        self.assertEqual(self.verify()["checks"]["recorded_claim_shape"], "FAIL")

    def test_fifo_is_denied_without_blocking(self):
        import os
        os.mkfifo(self.root / "fifo.json")
        with self.assertRaises(InvalidEvidence):
            read_regular_nofollow(self.root, "fifo.json")

    def test_unknown_effect_field_rejected(self):
        self.records["effect"]["approved_by"] = "claim"
        result = self.verify()
        self.assertEqual(result["verdict"], "FAIL")
        self.assertEqual(result["checks"]["file_effect"], "FAIL")

    def test_unknown_observation_field_rejected(self):
        self.records["observation"]["producer_signature"] = "pretend"
        self.assertEqual(self.verify()["checks"]["file_observation"], "FAIL")

    def test_ancient_cutoff_never_proves_chronology(self):
        self.records["observation"]["cutoff"] = "1970-01-01T00:00:00Z"
        result = self.verify()
        self.assertEqual(result["checks"]["temporal_relationship"], "NOT_ESTABLISHED")
        self.assertEqual(result["verdict"], "NOT_ESTABLISHED")

    def test_future_cutoff_never_proves_chronology(self):
        self.records["observation"]["cutoff"] = "9999-12-31T23:59:59Z"
        result = self.verify()
        self.assertEqual(result["checks"]["temporal_relationship"], "NOT_ESTABLISHED")

    def test_forged_self_consistent_bundle_does_not_authenticate(self):
        self.records["admission"]["operation_id"] = "forged"
        for name in ("attempt", "effect", "observation"):
            self.records[name]["operation_id"] = "forged"
        result = self.verify()
        self.assertEqual(result["verdict"], "NOT_ESTABLISHED")
        self.assertFalse(result["execution_authorized"])
        self.assertEqual(result["checks"]["producer_authenticity"], "NOT_ESTABLISHED")

    def test_bool_equals_integer_is_rejected(self):
        self.assertFalse(exact_args(ARGS, dict(ARGS, amount_minor=True)))
        self.assertFalse(exact_args(dict(ARGS, amount_minor=1), dict(ARGS, amount_minor=1.0)))

    def test_unexpected_file_manifest_key(self):
        raw = json.dumps(self.records["admission"]).encode()
        files = {name: {"path": name + ".json", "sha256": digest(raw)}
                 for name in self.records}
        files["extra"] = {"path": "extra.json", "sha256": digest(raw)}
        with self.assertRaises(InvalidEvidence):
            assess({"schema": "altru-refund-evidence-review/1", "files": files}, self.root)

    def test_raises_on_extra_top_level_manifest_field(self):
        with self.assertRaises(InvalidEvidence):
            assess({"schema": "altru-refund-evidence-review/1", "files": {},
                    "authorized": True}, self.root)

if __name__ == "__main__":
    unittest.main()
