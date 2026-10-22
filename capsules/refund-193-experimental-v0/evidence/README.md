# Refund #193 — bounded review evidence

This bundle records the locally tested experimental Frequency refund broker integration. No Federation contract freeze, independent reproduction, merchant consent, external provider credentials or production isolation is established.

## Reproduce

Checkout the `source_commit` in manifest.json with its pinned dependencies (RUNTIME-PINS.json), provision an isolated Python environment with requirements-runtime.txt and install the pinned APS runtime dependencies (`npm ci` in aps-runtime). Run the exact `test_command` from the repository root. Test keys are generated for synthetic cases only.

## Results and limits

The captured VPS run reports 55 tests OK. Relevant tests: `test_signed_broker_193.py`, `test_provisional_handoff_193.py` and `test_contract_193.py`. Tests demonstrate one synthetic effect after a verified admission and fail-closed tamper/duplicate checks. The Ed25519 experimental canonical form is **not** a published PIC/APS/Federation handoff standard. The signature verifier is a test-only addition via a broker callback; no production entrypoint/deployment is enabled.

The manifest includes SHA-256 hashes of tracked source files. The hash listing is a reproducibility inventory, not an externally signed attestation.
