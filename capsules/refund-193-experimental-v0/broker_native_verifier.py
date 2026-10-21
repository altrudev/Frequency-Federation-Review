"""Sandbox native APS/PIC broker verifier. Trust root is configured out of band."""
import hashlib
import json
from pic_native_adapter import verify_pic_refund
from aps_native_adapter import native_aps
from refund_sandbox import validate_admitted_operation

def build_native_verifier(trusted_aps_key, trusted_aps_issuer, trusted_pic_keyring_path):
    if not trusted_aps_key or not trusted_aps_issuer:
        raise ValueError("trusted-aps-configuration-required")
    if not trusted_pic_keyring_path:
        raise ValueError("trusted-pic-keyring-required")
    def verify(operation, evidence):
        if not isinstance(evidence, dict) or set(evidence)!={"aps","pic"}:
            return False
        try:
            aps=native_aps(evidence["aps"],trusted_aps_key,trusted_aps_issuer)
            pic=verify_pic_refund(evidence["pic"],trusted_pic_keyring_path)
            op=validate_admitted_operation(operation)
            if aps["decision"]!="permit" or pic["decision"]!="permit":
                return False
            if any(aps[k]!=pic[k] for k in ("approval_ref","tool","arguments")):
                return False
            expected={
                "schema":"refund-execution/0.1",
                "operation_id":"refund-"+hashlib.sha256(aps["approval_ref"].encode()).hexdigest(),
                "tool":"refund","arguments":aps["arguments"],
                "approval_ref":aps["approval_ref"],
                "aps_evidence_ref":aps["evidence_ref"],
                "pic_evidence_ref":pic["evidence_ref"],
            }
            return op==expected
        except Exception:
            return False
    return verify
