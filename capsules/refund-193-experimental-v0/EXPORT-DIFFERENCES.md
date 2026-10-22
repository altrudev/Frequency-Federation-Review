# Export differences

Source revision: `7077f72fa1988f8af889507bd4c2ffae783b1ed7`. This public review capsule omits internal VPS deployment/audit reports, host service unit and runtime configuration example, plus unrelated diagnostics. Test portability adjustment: removed a hardcoded VPS `sys.path` insertion from `test_broker_boundary.py`; the repository-local import remains.

`evidence/manifest.json` hashes **original source checkout paths** at its recorded source commit, not exported capsule paths. Do not misrepresent those hashes as verification of this export. `EXPORT-SHA256.json` independently inventories the public review files.

Fresh-clone QA correction: removed three additional hardcoded VPS `sys.path` insertions in `test_socket_config.py`, `test_gateway.py`, and `test_crash_gate.py`; replaced the original machine-specific path in the isolated OS preflight test with a non-existing synthetic `/home/ubuntu/refund-review-fixture` location.

Runtime gap correction: the simulator entrypoint now composes the existing experimental handoff verifier with native APS/PIC verification and requires externally provisioned sandbox public keys. Configuration and actual runtime-broker negative tests cover absent/invalid trust and denied evidence before claims/effects. No APS trust roots or production authority are supplied. Export hashes reflect these review changes; historical source evidence remains unchanged.
