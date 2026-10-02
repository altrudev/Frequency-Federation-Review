#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "usage: $0 --repo <Frequency-Federation-Review> --adapter-commit <40hex> --aps-repo <path> --priorseal-repo <path> --attempt-dir <new-dir>" >&2
  exit 2
}

repo=
adapter_commit=
aps_repo=
priorseal_repo=
attempt_dir=
while [ "$#" -gt 0 ]; do
  case "$1" in
    --repo) repo=$2; shift 2 ;;
    --adapter-commit) adapter_commit=$2; shift 2 ;;
    --aps-repo) aps_repo=$2; shift 2 ;;
    --priorseal-repo) priorseal_repo=$2; shift 2 ;;
    --attempt-dir) attempt_dir=$2; shift 2 ;;
    *) usage ;;
  esac
done
[ -n "$repo" ] && [ -n "$adapter_commit" ] && [ -n "$aps_repo" ] && [ -n "$priorseal_repo" ] && [ -n "$attempt_dir" ] || usage
[[ "$adapter_commit" =~ ^[0-9a-f]{40}$ ]] || { echo "BLOCKED: adapter commit must be 40 hex" >&2; exit 2; }
[ ! -e "$attempt_dir" ] || { echo "BLOCKED: attempt directory already exists: $attempt_dir" >&2; exit 2; }

mkdir -m 700 "$attempt_dir" || exit 2
status_file="$attempt_dir/exit-status.txt"
report_file="$attempt_dir/frequency-run-report.json"
meta_file="$attempt_dir/run-metadata.txt"

record_status() {
  rc=$?
  printf '%s\n' "$rc" > "$status_file"
  exit "$rc"
}
trap record_status EXIT

actual=$(git -C "$repo" rev-parse HEAD) || exit 2
[ "$actual" = "$adapter_commit" ] || { echo "BLOCKED: review checkout mismatch: $actual" >&2; exit 2; }
[ -z "$(git -C "$repo" status --porcelain)" ] || { echo "BLOCKED: review checkout has uncommitted or untracked changes" >&2; exit 2; }
aps_actual=$(git -C "$aps_repo" rev-parse HEAD) || exit 2
[ "$aps_actual" = "948f99b85343bef2c6fa677c8543965caacfc087" ] || { echo "BLOCKED: APS checkout mismatch: $aps_actual" >&2; exit 2; }
priorseal_actual=$(git -C "$priorseal_repo" rev-parse HEAD) || exit 2
[ "$priorseal_actual" = "d749d2691c3e6be139de4020e7b27cdafca2c428" ] || { echo "BLOCKED: PriorSeal checkout mismatch: $priorseal_actual" >&2; exit 2; }

capsule="$repo/capsules/aps-priorseal-v0.1"
adapter="$capsule/adapter/verify.mjs"
( cd "$repo" && sha256sum -c capsules/aps-priorseal-v0.1/MANIFEST.sha256 ) || exit 2
adapter_sha=$(sha256sum "$adapter" | awk '{print $1}') || exit 2
printf 'review_commit=%s\nadapter_sha256=%s\naps_commit=%s\npriorseal_commit=%s\n' \
  "$actual" "$adapter_sha" "$aps_actual" "$priorseal_actual" > "$meta_file"

cd "$capsule/adapter" || exit 2
npm ci --ignore-scripts --no-audit --no-fund
npm run selftest
node verify.mjs \
  --aps-owner "$aps_repo/fixtures/priorseal-decision-binding" \
  --aps "$priorseal_repo/examples/aps-priorseal-decision-binding-v1/aps-inputs" \
  --priorseal "$priorseal_repo/examples/aps-priorseal-decision-binding-v1" \
  --out "$report_file"

trap - EXIT
printf '0\n' > "$status_file"
printf 'PASS: %s\n' "$report_file"
