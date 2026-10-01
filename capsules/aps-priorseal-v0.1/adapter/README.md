# Frequency APS × PriorSeal assurance adapter

This is a **thin external-evidence adapter** for the bounded APS × PriorSeal pilot discussed in `aeoess/agent-governance-vocabulary#177`.

It intentionally does **not** import `agent-passport-system`, `priorseal-sdk`, their verifier functions, or their generated reports as an oracle. The adapter reads pinned public bytes and applies the public signing/binding contracts with adapter-local trust pins. It also requires the owner APS fixture checkout and proves that every manifest-declared APS byte consumed from the PriorSeal copy is identical to the owner-repository fixture at the pinned APS commit. Generic cryptography is supplied by Node.js and `ethers` for EIP-712 recovery.

The output is per-claim. It separates `ESTABLISHED`, `CONTRADICTED`, and `NOT_ESTABLISHED` rather than collapsing the run into one pass/fail result. It also emits explicit claim ceilings and a mutation-adequacy plan. The mutation run is deliberately **not executed** and is excluded from the formal result until discriminating authenticity/binding fixtures exist and the separately agreed adequacy gate is opened.

## Pinned pilot

- APS: `948f99b85343bef2c6fa677c8543965caacfc087`
- PriorSeal: `d749d2691c3e6be139de4020e7b27cdafca2c428`
- Reference time: `2026-09-19T10:05:00.000Z`
- APS manifest SHA-256: `2bf365bc9124ecfc943d5be86c34e8e0cacd51a5929b8d0c906e633a017231f9`
- Within-limit fixture SHA-256: `c8dd05f412b3d1dd957f66deaf231a8becb9656e8bd1960ba88638cf9ad4c6da`
- Over-limit fixture SHA-256: `cb45a8378a5c9f1f7f2695c4d1fb5cbe344d9c840b799cf0ecb786e5ddf3c226`

## Run

```bash
cd tools/aps-priorseal-showcase
npm ci
node verify.mjs \
  --aps-owner /path/to/agent-passport-system/fixtures/priorseal-decision-binding \
  --aps /path/to/PriorSeal/examples/aps-priorseal-decision-binding-v1/aps-inputs \
  --priorseal /path/to/PriorSeal/examples/aps-priorseal-decision-binding-v1 \
  --out frequency-run-report.json
```

The output contract is intentionally narrow. It exposes public evidence pins, claim identifiers, evidence references, results, claim ceilings and the future adequacy plan. Frequency internal reasoning graphs, heuristics, repair ranking, orchestration and private assurance controls are not part of the adapter contract.
