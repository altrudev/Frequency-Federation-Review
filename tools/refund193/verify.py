#!/usr/bin/env python3
"""Offline, read-only refund evidence bindings check. Not an authorization gate."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HEX = re.compile(r"sha256:[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_-]+\Z")
FIELDS = ("workflow_id", "admission_issuer", "provider_namespace", "operation_id")
ARG_FIELDS = {"payment_id", "amount_minor", "currency"}

class InvalidEvidence(ValueError):
    pass

def pairs_no_duplicates(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise InvalidEvidence("duplicate_json_member")
        obj[key] = value
    return obj

def parse_json(data):
    return json.loads(data, object_pairs_hook=pairs_no_duplicates,
                      parse_constant=lambda _: (_ for _ in ()).throw(InvalidEvidence("non_json_constant")))

def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()

def require(cond, code):
    if not cond:
        raise InvalidEvidence(code)

def validate_args(args):
    require(type(args) is dict and set(args) == ARG_FIELDS, "arguments_shape_invalid")
    require(type(args["payment_id"]) is str and bool(ID.fullmatch(args["payment_id"])), "payment_id_invalid")
    require(type(args["amount_minor"]) is int and 0 < args["amount_minor"] <= 2**53-1, "amount_invalid")
    require(args["currency"] == "EUR", "currency_invalid")

def assess(manifest, bundle_dir):
    """Never grants permission to dispatch; each verdict is only about retained evidence."""
    reasons = []
    checks = {}
    def check(name, fn):
        try:
            fn()
            checks[name] = "PASS"
        except (InvalidEvidence, OSError, ValueError, TypeError, KeyError) as exc:
            checks[name] = "FAIL"
            reasons.append(name + ":" + str(exc))
    require(type(manifest) is dict and manifest.get("schema") == "altru-refund-evidence-review/1", "manifest_schema_invalid")
    files = manifest.get("files")
    require(type(files) is dict and files, "files_missing")
    records = {}
    for name in ("admission", "attempt", "effect", "observation"):
        def load(name=name):
            entry = files.get(name)
            require(type(entry) is dict and set(entry) == {"path", "sha256"}, "file_entry_invalid")
            path = entry["path"]
            require(type(path) is str and path in (name + ".json",), "file_path_not_allowlisted")
            require(type(entry["sha256"]) is str and HEX.fullmatch(entry["sha256"]), "hash_format_invalid")
            raw = (bundle_dir / path).read_bytes()
            require(digest(raw) == entry["sha256"], "file_digest_mismatch")
            records[name] = parse_json(raw)
            require(type(records[name]) is dict, "record_not_object")
        check("file_" + name, load)
    if len(records) != 4:
        return {"schema": "altru-refund-evidence-review-result/1", "verdict": "FAIL", "checks": checks, "reasons": reasons, "execution_authorized": False}
    a, t, e, o = (records[k] for k in ("admission", "attempt", "effect", "observation"))
    def identities():
        for n, r in (("admission", a), ("attempt", t), ("effect", e), ("observation", o)):
            for key in FIELDS:
                require(type(r.get(key)) is str and r[key] != "", n + "_missing_" + key)
        for key in FIELDS:
            require(t[key] == a[key] and e[key] == a[key] and o[key] == a[key], key + "_mismatch")
        for key in ("attempt_id",):
            require(type(t.get(key)) is str and t[key], "attempt_id_missing")
            require(e.get(key) == t[key] and o.get(key) == t[key], "attempt_id_mismatch")
        require(type(e.get("effect_id")) is str and e["effect_id"], "effect_id_missing")
        require(o.get("effect_id") == e["effect_id"], "effect_id_mismatch")
    check("identity_bindings", identities)
    def arguments():
        validate_args(a.get("arguments"))
        require(t.get("arguments") == a["arguments"], "attempt_arguments_mismatch")
        require(e.get("arguments") == a["arguments"], "effect_arguments_mismatch")
        require(type(a.get("admission_ref")) is str and bool(HEX.fullmatch(a["admission_ref"])), "admission_ref_invalid")
        require(t.get("admission_ref") == a["admission_ref"], "attempt_admission_ref_mismatch")
        require(e.get("admission_ref") == a["admission_ref"], "effect_admission_ref_mismatch")
    check("argument_bindings", arguments)
    def status():
        require(a.get("state") == "committed", "admission_not_committed")
        require(t.get("dispatch_status") == "sent", "dispatch_not_recorded")
        require(e.get("outcome") == "succeeded", "effect_not_successful")
        require(o.get("observed_effect") is True, "effect_not_observed")
        require(o.get("verdict") == "observed_success", "observation_not_success")
        require(type(o.get("cutoff")) is str and o["cutoff"], "cutoff_missing")
    check("recorded_status", status)
    # No trusted PIC/APS verification, signing-key custody, temporal authority, or
    # independent producer attestation is established by this synthetic manifest.
    if reasons:
        verdict = "FAIL"
    else:
        verdict = "NOT_ESTABLISHED"
        reasons.append("no_independent_cryptographic_or_authorization_proof")
    return {"schema": "altru-refund-evidence-review-result/1", "verdict": verdict, "checks": checks, "reasons": reasons, "execution_authorized": False}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    try:
        raw = args.manifest.read_bytes()
        result = assess(parse_json(raw), args.manifest.resolve().parent)
    except (InvalidEvidence, OSError, ValueError, TypeError) as exc:
        result = {"schema": "altru-refund-evidence-review-result/1", "verdict": "FAIL", "checks": {}, "reasons": [str(exc)], "execution_authorized": False}
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(output)
    else:
        sys.stdout.write(output)
    return 1 if result["verdict"] == "FAIL" else 2

if __name__ == "__main__":
    raise SystemExit(main())
