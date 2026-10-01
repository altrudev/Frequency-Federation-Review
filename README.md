# Frequency Federation Review

Public, bounded review capsules for proposed Frequency federation pilots.

This repository is **not Frequency**, **not Frequency-Dev**, and not a public release of Frequency's internal assurance architecture. It exists so external maintainers can review the exact interoperability surface needed to approve a bounded pilot without receiving access to private Frequency repositories.

## Current capsule

`capsules/aps-priorseal-v0.1/`

Purpose: scope review for the proposed APS × PriorSeal independent assurance pilot discussed in `aeoess/agent-governance-vocabulary#177`.

The capsule contains:

- the exact thin adapter source offered for review;
- public producer commit and fixture pins;
- adapter-local public trust-key pins;
- the exact fresh-clone command;
- the machine-readable output contract and expected output location;
- claim identifiers and explicit claim ceilings;
- a hold on formal execution until maintainer scope confirmation;
- a separate hold on publication until publication terms are agreed.

No Frequency internal evidence graph, private heuristics, repair logic, orchestration, model/provider configuration, private controls, credentials, or customer data are included.

## Review status

Formal run status: `NOT_RUN_PENDING_SCOPE_CONFIRMATION`

Publication status: `HOLD_PENDING_SEPARATE_AGREEMENT`

See the versioned capsule manifest for the authoritative review contract.

## Rights

The adapter source is exposed only so federation participants and reviewers can inspect and reproduce this bounded pilot interface. See `REVIEW-ONLY-NOTICE.md`.