# Federation #193 — DDC Radial integration gate (2026-10-27)

Review-only document. This does not change the frozen bounded verifier contract in ACCEPTANCE-v1.md, accept an executor role, or grant use of private Frequency implementation.

## Pinned independent audit inputs

- Federation issue: aeoess/agent-governance-vocabulary#193, latest coordinator comment from madeinplutofabio describing four pre-freeze questions.
- Probity main inspected: f756419417f21bbd953d5dcdd64e0b880fb61a2b; merged executor PR probityai/probity#146.
- Frequency read-only verifier: 624e811e54992c0a74b5c73d0a753fb6afc63e6d (PR #13).
- Shared draft: refund-sandbox-contract/review-2026-10-23 (not frozen).

## Acceptance cases, ownership and evidence

| ID | Required producer evidence | Current decision |
|---|---|---|
| I01 | Frozen closed PIC result schema with signed native verification and source proposal carrying exact typed refund args; no undeclared result.arguments | HOLD — Probity executor currently reads pic.get('arguments') at check_evidence, conflicting with draft section 4 |
| I02 | Door-authenticated committed admission plus signed mapping tied to exact JCS bytes, role-bound under independently selected trust; signer verifies both | HOLD — proposed, not connected and mandatory verification not demonstrated |
| I03 | Admission controlled requests/responses proving changed-content rejection, single-use decision-to-operation binding, replay and reissue recovery | HOLD — hosted door sequences and reproducible signed traces not provided |
| I04 | Manifest names and hashes exact dispatch-time producer source per attempt_id; independent reader recomputes temporal relation | HOLD — Probity writes raw/dispatch-times.jsonl but manifest-level authenticated binding not demonstrated |
| I05 | Native APS approval/decision/intent; real PIC verification; genuine admission record; Probity signer/runner; separate Default Settlement reader operate on one pinned fixture | NOT ESTABLISHED — synthetic and stand-in inputs do not constitute a connected run |
| I06 | Reader reproduces positive and negative J cases, without trusting the producer's own outcome claims; report source commit pins, immutable hashes and external signer roles | NOT ESTABLISHED |

## Decision and scope controls

No connected-run PASS until all six conditions have independently inspected receipts. Local synthetic success is not proof of producer provenance or independent observation. Preserve all negative outcomes and fail-closed judgments; a future reader adapter should be separate from tools/refund193/verify.py. Verify source authenticity before matching claims; do not infer it from self-supplied hashes. Treat Probity's current source/schema disagreement as a contract mismatch, not permission to silently extend the Federation schema. Frequency is review-only, not executor or owner of PIC/APS/admission/reader obligations.

## Next producer handoff

Request one immutable fixture index with (1) contract commit; (2) exact file list and raw SHA-256; (3) invocation and dependency pins; (4) trust roots and independently held signer-role mapping; (5) each J-case expected output and signed negative evidence; (6) raw dispatch timestamps explicitly bound into the manifest; (7) independent reader invocation. Re-run the complete matrix from a clean checkout and publish per-case PASS, FAIL or NOT_ESTABLISHED. No mock fixture is an acceptable substitute for these producer-owned bytes.
