# Revision 0.1.2 validation

This document records publication-gate checks for the review capsule. It is not a formal federation pilot result.

## Source-binding correction

The adapter now requires both the owner APS fixture root and the copied APS fixture root used by PriorSeal.

At the pinned commits:

- APS owner commit: `948f99b85343bef2c6fa677c8543965caacfc087`
- PriorSeal commit: `d749d2691c3e6be139de4020e7b27cdafca2c428`
- owner and copied manifest SHA-256: `2bf365bc9124ecfc943d5be86c34e8e0cacd51a5929b8d0c906e633a017231f9`
- manifest-declared files compared: `17`
- byte equality: PASS

## Pre-publication checks

- adapter syntax check: PASS
- adapter self-test: PASS
- `npm audit --audit-level=high`: 0 vulnerabilities
- source-bound public-input development preflight: 14 ESTABLISHED / 3 CONTRADICTED / 5 NOT_ESTABLISHED
- source-binding claim: ESTABLISHED
- one-byte copied-fixture mutation: FAIL CLOSED
- report emitted after tamper: NO
- missing `--aps-owner`: rejected with usage error
- APS trust-key provenance disclosed as pinned fixture test keys: PASS
- APS authenticity claims carry a fixture-test-key claim ceiling: PASS
- existing output destination: rejected before evaluation
- stale sentinel at existing output path: preserved byte-for-byte after rejection
- fresh-attempt wrapper records exact review commit, adapter SHA-256, APS/PriorSeal commits, and exit status
- capsule manifest verification is on the pinned-run execution path
- mutation/corpus adequacy: NOT RUN and excluded from the formal result
- formal pilot run: NOT RUN
- formal result publication: HOLD

The three contradicted preflight outcomes are the intended negative-fixture results. They are not adapter process failures.

Mutation/corpus adequacy remains blocked until discriminating fixtures exist for the listed authenticity and decision-binding mutations and that stage is separately approved.
