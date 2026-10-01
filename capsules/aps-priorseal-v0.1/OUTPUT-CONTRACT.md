# Output contract

The adapter writes one JSON document with profile:

`frequency.external-assurance.aps-priorseal.v1`

The report contains exact public input pins and fixture hashes; adapter-local trust-key identifiers and digests; individual claims with `ESTABLISHED`, `CONTRADICTED`, or `NOT_ESTABLISHED`; evidence references; explicit claim ceilings; a summary count; a separately gated mutation/corpus-adequacy plan; and the public/private disclosure boundary.

A contradiction is a claim-level result, not a process crash. The pinned negative fixtures are expected to contradict the relevant temporal, exact-call, and cap-compliance claims.

The following claims cannot be promoted by this fixture-only run:

- `live_chain.execution_occurred`
- `aps.decision.single_use`
- `aps.live_currency_enforcement`
- `observation.independent_external_witness`
- `production.adoption`

The adapter deliberately does not emit an overall endorsement, production-readiness verdict, or claim that external execution occurred.

Expected machine-readable output path:

`artifacts/aps-priorseal-v0.1/frequency-run-report.json`