"""Fail-closed sandbox admission boundary. No production/provider authorization.

Verifier functions MUST implement the pinned APS/PIC native verification; test doubles
are permitted only in unit tests. This module does not itself verify signatures.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Callable, Mapping, Any

class AdmissionDenied(Exception):
    pass

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

class RefundAdmissionGateway:
    def __init__(self, state_path: Path, aps_verify: Callable, pic_verify: Callable, executor):
        if not callable(aps_verify) or not callable(pic_verify):
            raise ValueError("native-verifiers-required")
        self.aps_verify, self.pic_verify, self.executor = aps_verify, pic_verify, executor
        self.db = sqlite3.connect(str(state_path), isolation_level=None)
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("CREATE TABLE IF NOT EXISTS admissions (approval TEXT PRIMARY KEY, digest TEXT NOT NULL, operation TEXT UNIQUE NOT NULL)")

    def execute(self, *, approval: Mapping[str, Any], aps_artifact: Any, pic_artifact: Any):
        # Callbacks return independently verified, normalized bindings or raise.
        try:
            a = self.aps_verify(aps_artifact)
            p = self.pic_verify(pic_artifact)
        except Exception as e:
            raise AdmissionDenied("native-verification-failed") from e
        fields = ("approval_ref", "tool", "arguments")
        if not isinstance(a, dict) or not isinstance(p, dict):
            raise AdmissionDenied("missing-verified-claims")
        if any(a.get(k) != p.get(k) or a.get(k) != approval.get(k) for k in fields):
            raise AdmissionDenied("cross-evidence-mismatch")
        if a.get("decision") != "permit" or p.get("decision") != "permit":
            raise AdmissionDenied("non-permit")
        if a.get("tool") != "refund" or not isinstance(a.get("approval_ref"), str) or not a["approval_ref"]:
            raise AdmissionDenied("invalid-action")
        args = a["arguments"]
        if not isinstance(args, dict) or set(args) != {"payment_id", "amount_minor", "currency"}:
            raise AdmissionDenied("invalid-arguments")
        if type(args["amount_minor"]) is not int or args["amount_minor"] <= 0:
            raise AdmissionDenied("invalid-amount")
        if not isinstance(args["payment_id"], str) or not args["payment_id"]:
            raise AdmissionDenied("invalid-payment")
        if not isinstance(args["currency"], str) or len(args["currency"]) != 3 or not args["currency"].isupper():
            raise AdmissionDenied("invalid-currency")
        if not all(isinstance(v.get("evidence_ref"), str) and v["evidence_ref"] for v in (a, p)):
            raise AdmissionDenied("missing-evidence-identity")
        digest = hashlib.sha256(canonical({"approval_ref": a["approval_ref"], "tool": a["tool"], "arguments": args, "aps": a["evidence_ref"], "pic": p["evidence_ref"]}).encode()).hexdigest()
        operation_id = "refund-" + hashlib.sha256(a["approval_ref"].encode()).hexdigest()
        operation = {"schema": "refund-execution/0.1", "operation_id": operation_id,
                     "tool": "refund", "arguments": args, "approval_ref": a["approval_ref"],
                     "aps_evidence_ref": a["evidence_ref"], "pic_evidence_ref": p["evidence_ref"]}
        # Fail closed on repeated admission; reconciliations belong to executor.
        try:
            self.db.execute("BEGIN IMMEDIATE")
            row = self.db.execute("SELECT digest FROM admissions WHERE approval=?", (a["approval_ref"],)).fetchone()
            if row is not None:
                raise AdmissionDenied("approval-consumed")
            self.db.execute("INSERT INTO admissions VALUES (?, ?, ?)", (a["approval_ref"], digest, operation_id))
            self.db.execute("COMMIT")
        except Exception:
            if self.db.in_transaction:
                self.db.execute("ROLLBACK")
            raise
        return self.executor.execute(operation)
