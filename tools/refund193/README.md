# #193 read-only evidence-boundary verifier (experimental)

Copyright 2026 Val Rukhaylo / Altru.dev. **Review only**; existing repository licensing and proprietary implementation boundaries remain in force.

This deliberately small standalone Python 3 verifier checks SHA-256 integrity of an allowlisted four-file synthetic bundle and compares retained operation, attempt, effect, observation, argument and reference identities. It refuses inconsistent identities, altered arguments, malformed or duplicated JSON keys, and unproven positive statuses.

Run: `python3 tools/refund193/verify.py path/to/manifest.json`. Exit 1 means FAIL; exit 2 means NOT_ESTABLISHED; there is **no PASS authorization state**. Unit tests: `cd tools/refund193 && python3 -m unittest -v test_verify.py`.

Manifest schema `altru-refund-evidence-review/1` contains a `files` object with entries `admission`, `attempt`, `effect`, `observation`. Each entry has exactly `path` (respectively `admission.json`, etc.) and `sha256` (`sha256:` + lowercase hex digest of raw file bytes). Files are read only from the manifest's own directory.

This is **not** the Federation #193 signed-admission contract, a PIC/APS verifier, a production dispatch gate, or a claim that records are authentic. Even all matching synthetic records return `NOT_ESTABLISHED`, because trusted signing evidence, key roles, revocation-at-dispatch, exact producer time, durable effects, report-cutoff semantics and independent custody are not proven. No new dispatch, remote command or payment API is used. The verifier neither imports nor exposes private Frequency Core.

Before treating an independent reader result as established, frozen #193 producer contracts must separately verify signature/trust/time, native PIC/APS bindings, idempotency derivation, historical dispatch times and observation provenance. No equivalence between this review schema and `refund-sandbox-contract/review-2026-10-23` is claimed.

Strict typed equality and closed manifest keys are enforced; connected producer evidence remains unverified.
