#!/usr/bin/env python3
"""Offline, read-only refund evidence bindings check. Not an authorization gate."""
import argparse
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
import re
import sys
from pathlib import Path

HEX = re.compile(r"sha256:[0-9a-f]{64}\Z")
ID = re.compile(r"[A-Za-z0-9_-]+\Z")
FIELDS = ("workflow_id", "admission_issuer", "provider_namespace", "operation_id")
ARG_FIELDS = {"payment_id", "amount_minor", "currency"}
RECORD_FIELDS = {
    "admission": set(FIELDS) | {"arguments", "admission_ref", "state"},
    "attempt": set(FIELDS) | {"attempt_id", "admission_ref", "arguments", "dispatch_status"},
    "effect": set(FIELDS) | {"attempt_id", "effect_id", "admission_ref", "arguments", "outcome"},
    "observation": set(FIELDS) | {"attempt_id", "effect_id", "observed_effect", "verdict", "cutoff"},
}

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

def exact_args(left, right):
    """Avoid Python's bool == int and int == float coercion during binding."""
    return (type(left) is dict and type(right) is dict
            and set(left) == ARG_FIELDS and set(right) == ARG_FIELDS
            and all(type(left[k]) is type(right[k]) and left[k] == right[k]
                    for k in ARG_FIELDS))

def read_regular_nofollow(directory, filename):
    """Read only a bounded regular file, refusing symlinks even on the last component."""
    base = Path(directory)
    require(not base.is_symlink() and base.is_dir(), "bundle_directory_invalid")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    dirfd = os.open(base, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        fd = os.open(filename, flags, dir_fd=dirfd)
        try:
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "not_single_regular_file")
            require(info.st_size <= 1024 * 1024, "file_too_large")
            with os.fdopen(os.dup(fd), "rb") as reader:
                raw = reader.read(1024 * 1024 + 1)
            require(len(raw) <= 1024 * 1024, "file_too_large")
            return raw
        finally:
            os.close(fd)
    finally:
        os.close(dirfd)

def parse_cutoff(value):
    require(type(value) is str and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), "cutoff_format_invalid")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise InvalidEvidence("cutoff_calendar_invalid") from exc
    return parsed

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
    require(type(manifest) is dict and set(manifest) == {"schema", "files"} and manifest["schema"] == "altru-refund-evidence-review/1", "manifest_schema_invalid")
    files = manifest.get("files")
    require(type(files) is dict and set(files) == {"admission", "attempt", "effect", "observation"}, "files_shape_invalid")
    records = {}
    for name in ("admission", "attempt", "effect", "observation"):
        def load(name=name):
            entry = files.get(name)
            require(type(entry) is dict and set(entry) == {"path", "sha256"}, "file_entry_invalid")
            path = entry["path"]
            require(type(path) is str and path in (name + ".json",), "file_path_not_allowlisted")
            require(type(entry["sha256"]) is str and HEX.fullmatch(entry["sha256"]), "hash_format_invalid")
            raw = read_regular_nofollow(bundle_dir, path)
            require(digest(raw) == entry["sha256"], "file_digest_mismatch")
            records[name] = parse_json(raw)
            require(type(records[name]) is dict and set(records[name]) == RECORD_FIELDS[name], "record_schema_invalid")
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
        require(exact_args(t.get("arguments"), a["arguments"]), "attempt_arguments_mismatch")
        require(exact_args(e.get("arguments"), a["arguments"]), "effect_arguments_mismatch")
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
        parse_cutoff(o.get("cutoff"))
    check("recorded_claim_shape", status)
    # A timestamp string alone cannot prove its order relative to a producer event.
    # Neither the manifest nor these synthetic records authenticate timing.
    checks["temporal_relationship"] = "NOT_ESTABLISHED"
    checks["producer_authenticity"] = "NOT_ESTABLISHED"
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
