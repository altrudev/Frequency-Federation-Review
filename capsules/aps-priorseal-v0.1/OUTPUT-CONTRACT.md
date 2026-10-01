# Output contract

The adapter writes one JSON document with profile:

`frequency.external-assurance.aps-priorseal.v1`

The report contains exact public input pins and fixture hashes; adapter-local trust-key identifiers and digests; individual claims with `ESTABLISHED`, `CONTRADICTED`, or `NOT_ESTABLISHED`; evidence references; explicit claim ceilings; a summary count; a separately gated mutation/corpus-adequacy plan; and the public/private disclosure boundary.

## Owner-source binding

Before evaluating the copied APS inputs, the adapter requires the pinned owner APS fixture root via `--aps-owner`. It verifies both manifest digests, requires the two manifest files to be byte-for-byte identical, and compares every manifest-declared owner fixture with the corresponding PriorSeal copy.

On success it emits:

`composition.aps_owner_fixture_copy.byte_identical = ESTABLISHED`

A mismatch is not converted into a weak or unknown claim. The verifier fails closed and does not emit a report.

## Trust-key scope

The three APS public keys used by this capsule are the test keys published in the pinned APS fixture `keys.json`. An APS authenticity result therefore establishes signature verification under those fixture test keys only. It does not establish production identity, production key control, or production deployment.

## Run-output freshness

The adapter refuses an existing `--out` destination. The pinned runner also requires a previously nonexistent attempt directory, records the exact review commit and adapter SHA-256, and always records the process exit status. A failed attempt cannot promote a pre-existing report into a new result.

A contradiction is a claim-level result, not a process crash. The pinned negative fixtures are expected to contradict the relevant temporal, exact-call, and cap-compliance claims.

The following claims cannot be promoted by this fixture-only run:

- `live_chain.execution_occurred`
- `aps.decision.single_use`
- `aps.live_currency_enforcement`
- `observation.independent_external_witness`
- `production.adoption`

Mutation/corpus adequacy is excluded from the formal result until the listed signature, wrong-key, altered-authorization, and decision-ref-binding mutations have discriminating fixtures and maintainers separately agree to that stage.

The adapter deliberately does not emit an overall endorsement, production-readiness verdict, or claim that external execution occurred.

Expected machine-readable output path:

`artifacts/aps-priorseal-v0.1/frequency-run-report.json`
