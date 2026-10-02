# Exact scope-review run

This command is provided so maintainers can review and reproduce the proposed bounded adapter. Do not treat a locally reproduced result as the formal federation run.

## Reviewed adapter pin

Frequency Federation Review adapter commit:

`cf7389097fe3a404b3557da2e72fdd8cbe962b81`

The pinned runner requires the review checkout to be exactly this commit and clean, verifies the capsule manifest, records the adapter SHA-256 and both producer commits, and requires a fresh attempt directory.

## Fresh clone

```bash
git clone https://github.com/altrudev/Frequency-Federation-Review.git
git -C Frequency-Federation-Review checkout cf7389097fe3a404b3557da2e72fdd8cbe962b81

git clone https://github.com/aeoess/agent-passport-system.git /tmp/frequency-aps
git -C /tmp/frequency-aps checkout 948f99b85343bef2c6fa677c8543965caacfc087

git clone https://github.com/imokokok/PriorSeal.git /tmp/frequency-priorseal
git -C /tmp/frequency-priorseal checkout d749d2691c3e6be139de4020e7b27cdafca2c428
```

Run one fresh attempt:

```bash
Frequency-Federation-Review/capsules/aps-priorseal-v0.1/run-pinned.sh \
  --repo "$PWD/Frequency-Federation-Review" \
  --adapter-commit cf7389097fe3a404b3557da2e72fdd8cbe962b81 \
  --aps-repo /tmp/frequency-aps \
  --priorseal-repo /tmp/frequency-priorseal \
  --attempt-dir /tmp/frequency-aps-priorseal-attempt-001
```

The attempt directory must not already exist. The adapter also refuses an existing report destination. `exit-status.txt` is written for every attempted run; a successful attempt additionally contains `frequency-run-report.json` and `run-metadata.txt` with the exact review commit and adapter digest.

Before any APS claim is evaluated, the adapter verifies that the owner-repository APS manifest at the pinned APS commit and the copied APS manifest inside PriorSeal are byte-for-byte identical. It then compares every one of the 17 manifest-declared fixture files byte-for-byte. Any missing or changed copied file causes a fail-closed exit and no new report.

The resulting source-binding claim is:

`composition.aps_owner_fixture_copy.byte_identical`

The APS authenticity claims are explicitly limited to verification under the fixture test keys published in the pinned APS fixture. They do not establish production identity or production key control.

The formal Frequency run will not be published until scope is explicitly confirmed. Mutation/corpus adequacy remains outside the formal result until discriminating authenticity/binding fixtures exist and that stage is separately agreed. Publication of any formal result is a separate decision.
