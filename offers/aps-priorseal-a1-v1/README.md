# APS × PriorSeal A1 — Frequency Verification Offer

This directory is the first concrete instance of Frequency's Verification Offer / Reproduction Contract.

It does **not** authorize a new A1 execution by itself. The existing A1 agreement still requires an affirmative APS pre-run confirmation. PriorSeal's bounded authorization is already retained; APS has explicitly withheld its pre-run confirmation until the #185 checkpoint.

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
- `validate-readiness.sh` — pre-execution Frequency check. The expected current terminal state is `READY_EXCEPT_APS_PRE_RUN_CONSENT`.

## Current authority state

PriorSeal authorization:
`https://github.com/aeoess/agent-governance-vocabulary/issues/177#issuecomment-5974102214`

Current APS gate:
`https://github.com/aeoess/agent-governance-vocabulary/issues/177#issuecomment-5975814456`

The APS gate currently says no pre-run confirmation. Therefore the formal A1 runner must not be executed yet.

## Promotion sequence

When APS posts affirmative pre-run confirmation for these exact frozen inputs:

1. save the immutable APS confirmation source;
2. update the external pre-run gate to `APS_PRECONFIRMED=yes` with that exact reference;
3. run the already-prepared outer capture gate once;
4. build the final reproduction record with `build-reproduction-record.py --aps-consent-ref <immutable-ref>`;
5. validate the generated record with Frequency;
6. separately seek shared-record admission;
7. separately seek publication approval if publication is desired.

A valid reproduction record does not itself mean APS or PriorSeal endorsed the result, the federation admitted it, or publication was approved.
