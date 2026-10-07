# APS × PriorSeal A1 — Frequency Verification Offer

This directory is the first concrete instance of Frequency's Verification Offer / Reproduction Contract.

The offer does **not** authorize execution by itself. The current A1 authority is supplied by the public producer records: APS states that no separate per-run confirmation is needed for these unchanged public pinned inputs and permits its October 7 comment to serve as the execution record if required; PriorSeal states that its one bounded formal A1 authorization remains in effect and is exercisable.

## Frozen execution

- Frequency Federation Review execution commit: `cf7389097fe3a404b3557da2e72fdd8cbe962b81`
- execution tag: `aps-priorseal-a1-exec-2026-10-02`
- APS commit: `948f99b85343bef2c6fa677c8543965caacfc087`
- PriorSeal commit: `d749d2691c3e6be139de4020e7b27cdafca2c428`
- reference time: `2026-09-19T10:05:00.000Z`
- pinned runner SHA-256: `4b289714de31174a917b9c0f856e1d8900828e1bcbf637cdc8e97bc2deec2e34`

The offer binds all 22 public claim IDs emitted by the adapter, including the expected 14 ESTABLISHED / 3 CONTRADICTED / 5 NOT_ESTABLISHED shape. The three contradictions are explicit negative controls. The five NOT_ESTABLISHED claims are capped at a declarative extent and cannot be promoted into live-execution, single-use, live-currency, independent-witness, or production-adoption claims by this offer.

## Files

- `verification-offer.json` — authoritative A1 offer instance.
- `reproduction-record.template.json` — non-authoritative structural template. `pending:` references are placeholders and must never be submitted as a final record.
- `build-reproduction-record.py` — post-run builder. It refuses the wrong claim set, wrong dispositions, wrong summary, non-zero runner status, or changed artifact digests.
- `validate-readiness.sh` — pre-execution Frequency check. The expected current terminal state is `READY_FOR_ONE_BOUNDED_A1_RUN` when the retained producer authority files and frozen checkouts match the offer.

## Current authority state

PriorSeal authorization:
`https://github.com/aeoess/agent-governance-vocabulary/issues/177#issuecomment-6041926615`

APS authority record:
`https://github.com/aeoess/agent-governance-vocabulary/issues/177#issuecomment-6041543648`

For the unchanged frozen inputs above, APS requires no separate per-run confirmation and PriorSeal's one bounded formal A1 authorization is exercisable. A2, real-chain execution, shared-record admission and publication remain separate decisions.

## Promotion sequence

For the one bounded formal A1 run on these exact frozen inputs:

1. retain the immutable APS and PriorSeal authority sources;
2. set the external pre-run gate to `APS_PRECONFIRMED=yes` and `PRIORSEAL_PRECONFIRMED=yes` with those exact references;
3. run the already-prepared outer capture gate once;
4. build the final reproduction record with `build-reproduction-record.py --aps-consent-ref <immutable-ref>`;
5. validate the generated record with Frequency;
6. deliver the complete result to the three maintainers first;
7. separately seek shared-record admission;
8. separately seek publication approval if publication is desired.

A valid reproduction record does not itself mean APS or PriorSeal endorsed the result, the federation admitted it, or publication was approved.
