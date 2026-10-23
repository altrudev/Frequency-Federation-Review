# Refund #193 — experimental local review capsule

Copyright 2026 Valentyn Rukhaylo / Altru.dev. Review-only; implementation rights reserved under repository `REVIEW-ONLY-NOTICE.md`. This code is **not** an approved Federation standard, a signed APS admission implementation, or a production payment executor. `provisional_handoff_193.py` defines an Altru sandbox-only Ed25519 envelope.

Source/tested revision: `7077f72fa1988f8af889507bd4c2ffae783b1ed7`; evidence revision: `9d96ec9e85dee7d0ed54f1aa462b56dbc3f4c81f`. Review export differs only by removal of the VPS-specific absolute `sys.path` in `test_broker_boundary.py` and packaging (listed in `EXPORT-DIFFERENCES.md`). The historical 55-test captured outcome is from the source checkout, **not** a fresh public-clone run. The later published review head `0843b68` was independently reproduced from a fresh checkout on 2026-10-23: Python 3.14.4, Node 24.21.0, pinned PIC commit `ccb1dbb`, `npm ci` and `pip install -r requirements-runtime.txt`; `python -m unittest discover -q`: **61 tests, 0 failures**. These are synthetic local tests, not independent Federation certification.

## Reproduce (synthetic only)

From this directory, clone PIC Standard to `pic-standard` and checkout `ccb1dbb20c2283d9e20c7ade18374dc700c48097`; create a Python 3.14 virtual environment, `pip install -r requirements-runtime.txt`; run `npm ci` under `aps-runtime` with Node 24; run `python -m unittest discover -q`. The test suite uses pinned public PIC examples and locally generated synthetic APS keys. Do not attach live payments or private signing material.

## Boundaries

The broker verifies native APS/PIC fixtures with test trust, and the runtime entrypoint now requires the experimental additional signed-handoff gate as well as native APS/PIC verification. Only a local simulator produces effects. No real merchant authorization, live provider integration, cross-user OS deployment, APS signed-admission contract freeze, or independent Federation conformance has been established. Results: HOLD for production and Federation sign-off.

## Rights & dependencies

See repository `LICENSE`, `REVIEW-ONLY-NOTICE.md`, and `THIRD_PARTY_NOTICES.md`. Project-specific software here has no open-source grant. APS and PIC source references belong to their authors and are fetched separately.

The simulator runtime configuration requires `experimental_handoff_keys`, a nonempty object mapping sandbox key IDs to strict base64 encodings of raw 32-byte Ed25519 public keys. Provision these keys independently of request evidence; no keys are bundled or inferred from APS/PIC artifacts. Legacy configurations without this field, empty trust, and malformed keys fail startup and `--check`. The runtime accepts only evidence containing `aps`, `pic`, and the existing experimental `handoff` envelope. Missing, expired, untrusted, or mismatched handoffs are denied before an approval claim or simulator effect. `--check` validates configuration and constructs the verifier; it does not demonstrate admission or production readiness.

This is the existing Altru sandbox envelope, not an APS signed-admission contract or Federation conformance claim. APS/PIC trust still requires independent out-of-band configuration. Production and Federation sign-off remain HOLD.
