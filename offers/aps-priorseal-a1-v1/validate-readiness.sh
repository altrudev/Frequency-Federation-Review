#!/usr/bin/env bash
set -euo pipefail

FREQUENCY_REPO=${FREQUENCY_REPO:-/home/ubuntu/src/Frequency-a1-offer}
A1_BASE=${A1_BASE:-/home/ubuntu/a1-ready-20261004}
HERE=$(cd "$(dirname "$0")" && pwd)
CLI=(cargo run -q -p frequency --bin frequency --manifest-path "$FREQUENCY_REPO/Cargo.toml" --)

"${CLI[@]}" verification-offer check "$HERE/verification-offer.json" >/tmp/a1-offer-check.json

test "$(git -C "$A1_BASE/execution" rev-parse HEAD)" = "cf7389097fe3a404b3557da2e72fdd8cbe962b81"
test "$(git -C "$A1_BASE/aps" rev-parse HEAD)" = "948f99b85343bef2c6fa677c8543965caacfc087"
test "$(git -C "$A1_BASE/priorseal" rev-parse HEAD)" = "d749d2691c3e6be139de4020e7b27cdafca2c428"
test -z "$(git -C "$A1_BASE/execution" status --porcelain)"
test -z "$(git -C "$A1_BASE/aps" status --porcelain)"
test -z "$(git -C "$A1_BASE/priorseal" status --porcelain)"
( cd "$A1_BASE/execution" && sha256sum -c capsules/aps-priorseal-v0.1/MANIFEST.sha256 >/dev/null )

grep -q '^PRIORSEAL_PRECONFIRMED=yes$' "$A1_BASE/PRE-RUN-GATE.env"
grep -q '^APS_PRECONFIRMED=yes$' "$A1_BASE/PRE-RUN-GATE.env"
test -f "$A1_BASE/priorseal-current-authorization.json"
test -f "$A1_BASE/aps-current-gate.json"
test ! -e "$A1_BASE/captures"

set +e
"${CLI[@]}" verification-offer reproduction-check "$HERE/verification-offer.json" "$HERE/reproduction-record.template.json" 1791170000000 >/tmp/a1-repro-check.out 2>/tmp/a1-repro-check.err
rc=$?
set -e
test "$rc" -ne 0
grep -q 'MissingExplicitConsent' /tmp/a1-repro-check.err

printf '%s\n' 'A1_VERIFICATION_OFFER=VALID'
printf '%s\n' 'FROZEN_INPUTS=VALID'
printf '%s\n' 'PRIORSEAL_PRE_RUN_AUTHORITY=PRESENT'
printf '%s\n' 'APS_PRE_RUN_AUTHORITY=PRESENT'
printf '%s\n' 'FORMAL_EXECUTION=NOT_RUN'
printf '%s\n' 'STATUS=READY_FOR_ONE_BOUNDED_A1_RUN'
