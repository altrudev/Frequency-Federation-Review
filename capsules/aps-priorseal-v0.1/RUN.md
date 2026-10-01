# Exact scope-review run

This command is provided so maintainers can review and reproduce the proposed bounded adapter. Do not treat a locally reproduced result as the formal federation run.

## Fresh clone

```bash
git clone https://github.com/altrudev/Frequency-Federation-Review.git
cd Frequency-Federation-Review

mkdir -p inputs artifacts/aps-priorseal-v0.1

git clone https://github.com/aeoess/agent-passport-system.git inputs/agent-passport-system
git -C inputs/agent-passport-system checkout 948f99b85343bef2c6fa677c8543965caacfc087

git clone https://github.com/imokokok/PriorSeal.git inputs/PriorSeal
git -C inputs/PriorSeal checkout d749d2691c3e6be139de4020e7b27cdafca2c428

cd capsules/aps-priorseal-v0.1/adapter
npm ci --ignore-scripts --no-audit --no-fund
npm run selftest

node verify.mjs \
  --aps ../../../inputs/PriorSeal/examples/aps-priorseal-decision-binding-v1/aps-inputs \
  --priorseal ../../../inputs/PriorSeal/examples/aps-priorseal-decision-binding-v1 \
  --out ../../../artifacts/aps-priorseal-v0.1/frequency-run-report.json
```

The `agent-passport-system` checkout makes the owner-designated APS commit explicit and independently inspectable. The frozen PriorSeal interoperability directory contains the copied APS input fixture bytes used by this bounded composition.

## Expected output location

`artifacts/aps-priorseal-v0.1/frequency-run-report.json`

The formal Frequency run will not be published until scope is explicitly confirmed. Publication of any formal result is a separate decision.