"""Experimental, NON-FEDERATION handoff/0 prototype; simulator tests only.

Ed25519 signatures bind a digest of the exact admitted operation, single-use
approval identity, expiry and domain. Keys are externally provisioned. The
native APS/PIC verifier MUST also succeed; this module is not a substitute.
"""
import base64
import hashlib
import json
import time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from refund_sandbox import validate_admitted_operation

DOMAIN = 'altru-refund-sandbox-handoff-experimental/0'
FIELDS = {'domain', 'approval_ref', 'operation_digest', 'expires_at', 'key_id'}
MAX_SAFE = (1 << 53) - 1


def canonical_bytes(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode('utf-8')


def operation_digest(operation):
    normalized = validate_admitted_operation(operation)
    if normalized != operation:
        raise ValueError('operation-not-canonical')
    return hashlib.sha256(canonical_bytes(normalized)).hexdigest()


def verify_handoff(operation, attestation, trusted_keys, now=None):
    try:
        if not isinstance(attestation, dict) or set(attestation) != {'record', 'signature'}:
            return False
        record = attestation['record']
        if not isinstance(record, dict) or set(record) != FIELDS:
            return False
        if record['domain'] != DOMAIN or record['approval_ref'] != operation['approval_ref']:
            return False
        if type(record['expires_at']) is not int or not 0 < record['expires_at'] <= MAX_SAFE:
            return False
        clock = time.time() if now is None else now
        if not clock < record['expires_at']:
            return False
        if record['operation_digest'] != operation_digest(operation):
            return False
        key_id = record['key_id']
        if not isinstance(key_id, str) or key_id not in trusted_keys:
            return False
        key = trusted_keys[key_id]
        if not isinstance(key, Ed25519PublicKey):
            return False
        signature = base64.b64decode(attestation['signature'], validate=True)
        key.verify(signature, canonical_bytes(record))
        return True
    except (Exception):
        return False


def build_provisional_verifier(native_verifier, trusted_keys, now=None):
    if not callable(native_verifier) or not isinstance(trusted_keys, dict) or not trusted_keys:
        raise ValueError('native-verifier-and-external-trust-required')
    def verify(operation, evidence):
        if not isinstance(evidence, dict) or set(evidence) != {'aps', 'pic', 'handoff'}:
            return False
        if not verify_handoff(operation, evidence['handoff'], trusted_keys, now):
            return False
        return native_verifier(operation, {'aps': evidence['aps'], 'pic': evidence['pic']}) is True
    return verify
