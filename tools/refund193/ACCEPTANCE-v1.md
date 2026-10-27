# Bounded evidence reader: acceptance contract v1

Scope: offline synthetic evidence consistency only; NOT merchant authorization, PIC/APS integration, or Federation #193 acceptance.

A01: Allowlist and hash four regular evidence files; reject symlinks and special files.
A02: Reject duplicated JSON members and unknown manifest or record fields.
A03: Typed argument and admission-reference consistency.
A04: Consistent operation, attempt, effect, observation identity.
A05: Validate claimed status and UTC cutoff format without asserting temporal correctness.
A06: Every internally consistent synthetic bundle returns NOT_ESTABLISHED, and execution_authorized is always false. Temporal and producer-authenticity checks explicitly remain NOT_ESTABLISHED.
A07: Clean checkout passes all tests and source diff checks.

Acceptance: all gates verified on a pinned revision, with no reproducible contradiction. This qualifies only the bounded reader. External signed evidence, revocation, recovery, real effects, hostile parent directories, and Federation #193 are excluded and must not become retroactive blockers for this defined artifact.
