# PIC contract compatibility probe — pre-freeze, synthetic only

The command below checks a **deliberately restricted local test shape**, not the complete Federation section 4 signature/provenance protocol:

    python3 tools/refund193/pic_contract_probe.py proposal.json result.json

The proposal must contain only `arguments` (payment_id ASCII ID, positive integer amount_minor, currency EUR). The result must contain only `args_digest` (64 lowercase hex characters) and `result` equal to `allow`. The digest is SHA-256 of canonical JSON for the constrained ASCII test tuple. For the constrained arguments, this agrees with JSON Canonicalization Scheme serialization; this tool does not implement general RFC 8785 JCS.

A matching local test reports overall NOT_ESTABLISHED (exit 2), never authorization. Mismatches are FAIL (exit 1). Source provenance, native PIC SDK cryptographic verification, signed result schema, retained proposal bytes and file reference, approval authority, issuer trust, admission and connected executor are NOT_ESTABLISHED. Do not feed its output into an execution gateway.

This subset is **not** a declaration that the shared contract is frozen or that its real result contains only these two fields. It is a precise negative compatibility fixture against the current Probity stand-in containing result.arguments, pending the producer-controlled native PIC adapter and final closed schema. The original bounded verifier v1 remains unchanged.

Independent test: `python3 -m unittest discover -s tools/refund193 -v`.
