#!/usr/bin/env python3
import argparse, hashlib, json
from pathlib import Path

EXPECTED = {
"aps.manifest.pinned":"ESTABLISHED",
"composition.aps_owner_fixture_copy.byte_identical":"ESTABLISHED",
"aps.permit.receipts.authentic":"ESTABLISHED",
"aps.permit.delegation.authentic":"ESTABLISHED",
"aps.permit.decision_ref.bound":"ESTABLISHED",
"aps.permit.temporal_validity_at_reference":"ESTABLISHED",
"aps.expired.temporal_validity_at_reference":"CONTRADICTED",
"aps.deny.decision_verdict":"ESTABLISHED",
"priorseal.principal_eip712_authorization.authentic":"ESTABLISHED",
"priorseal.issuer_acceptance.authentic":"ESTABLISHED",
"priorseal.execution_receipt.positive.authentic":"ESTABLISHED",
"priorseal.execution_receipt.over_limit.authentic":"ESTABLISHED",
"composition.aps_decision_to_priorseal_authorization.bound":"ESTABLISHED",
"positive.observation.exact_call_agreement":"ESTABLISHED",
"positive.observation.aps_cap_compliance":"ESTABLISHED",
"over_limit.observation.exact_call_agreement":"CONTRADICTED",
"over_limit.observation.aps_cap_compliance":"CONTRADICTED",
"live_chain.execution_occurred":"NOT_ESTABLISHED",
"aps.decision.single_use":"NOT_ESTABLISHED",
"aps.live_currency_enforcement":"NOT_ESTABLISHED",
"observation.independent_external_witness":"NOT_ESTABLISHED",
"production.adoption":"NOT_ESTABLISHED",
}
NEGATIVES = {
"expired-temporal-negative":"aps.expired.temporal_validity_at_reference",
"over-limit-exact-call-negative":"over_limit.observation.exact_call_agreement",
"over-limit-cap-negative":"over_limit.observation.aps_cap_compliance",
}
def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):
    p=Path(p)
    return f"sha256:{sha(p)}:{p.name}"
ap=argparse.ArgumentParser()
ap.add_argument("--offer", required=True)
ap.add_argument("--capture-dir", required=True)
ap.add_argument("--execution-repo", required=True)
ap.add_argument("--aps-repo", required=True)
ap.add_argument("--priorseal-repo", required=True)
ap.add_argument("--aps-consent-ref", required=True)
ap.add_argument("--priorseal-consent-ref", required=True)
ap.add_argument("--out", required=True)
args=ap.parse_args()

offer=json.loads(Path(args.offer).read_text())
cap=Path(args.capture_dir)
attempt=cap/"formal-attempt"
report_path=attempt/"frequency-run-report.json"
report=json.loads(report_path.read_text())
claims={c["id"]:c for c in report["claims"]}
if set(claims) != set(EXPECTED):
    raise SystemExit("claim set mismatch")
for cid,expected in EXPECTED.items():
    if claims[cid]["result"] != expected:
        raise SystemExit(f"{cid}: expected {expected}, got {claims[cid]['result']}")
if report.get("summary") != {"established":14,"contradicted":3,"not_established":5}:
    raise SystemExit(f"unexpected summary: {report.get('summary')}")
if (attempt/"exit-status.txt").read_text().strip() != "0":
    raise SystemExit("formal runner exit status is not zero")

execution=Path(args.execution_repo)
aps=Path(args.aps_repo)
ps=Path(args.priorseal_repo)
paths={
"runner":execution/"capsules/aps-priorseal-v0.1/run-pinned.sh",
"adapter":execution/"capsules/aps-priorseal-v0.1/adapter/verify.mjs",
"capsule-manifest":execution/"capsules/aps-priorseal-v0.1/MANIFEST.sha256",
"trust-pins":execution/"capsules/aps-priorseal-v0.1/TRUST-PINS.json",
"aps-owner-manifest":aps/"fixtures/priorseal-decision-binding/MANIFEST.sha256",
"aps-copy-manifest":ps/"examples/aps-priorseal-decision-binding-v1/aps-inputs/MANIFEST.sha256",
"priorseal-positive":ps/"examples/aps-priorseal-decision-binding-v1/priorseal-inputs/payment-within-limit.json",
"priorseal-over-limit":ps/"examples/aps-priorseal-decision-binding-v1/priorseal-inputs/payment-over-limit.json",
"priorseal-producer-report":ps/"examples/aps-priorseal-decision-binding-v1/PAYMENT-LIMIT-REPORT.json",
}
observed={k:sha(v) for k,v in paths.items()}
expected_artifacts={a["artifact_id"]:a["sha256"] for a in offer["artifacts"]}
if observed != expected_artifacts:
    raise SystemExit("artifact digest set mismatch")

ceiling={c["claim_id"]:c["ceiling"] for c in offer["claims"]}
record={
"schema_version":1,
"offer_id":offer["offer_id"],
"operator":"Val Rukhaylo / Altru.dev",
"observed_artifact_sha256":observed,
"capture":{
"argv_ref":ref(cap/"argv.nul"),
"working_directory":next(x.split("=",1)[1] for x in (cap/"pre-exec.txt").read_text().splitlines() if x.startswith("cwd=")),
"process_start_time_ref":ref(cap/"pre-exec.txt"),
"stdout_ref":ref(cap/"stdout.txt"),
"stderr_ref":ref(cap/"stderr.txt"),
"exit_status_ref":ref(cap/"wrapper-exit-status.txt"),
"file_hash_manifest_ref":ref(cap/"CAPTURE.sha256")},
"claim_results":[{"claim_id":cid,"disposition":EXPECTED[cid],"evidence_refs":[ref(report_path),*[str(x) for x in claims[cid].get("evidence",[])]],"claimed_ceiling":ceiling[cid]} for cid in EXPECTED],
"negative_control_results":[{"control_id":nid,"observation_refs":[f"{cid}=CONTRADICTED",ref(report_path)],"passed":claims[cid]["result"]=="CONTRADICTED"} for nid,cid in NEGATIVES.items()],
"producer_consent_refs":[args.aps_consent_ref,args.priorseal_consent_ref],
"operator_statement":"I executed the exact pinned A1 procedure under the recorded pre-run authority and captured the resulting bounded fixture-assurance record.",
"producer_approved":False,"producer_approval_refs":[],
"shared_record_admitted":False,"shared_record_admission_refs":[],
"published":False,"publication_approval_refs":[]}
Path(args.out).write_text(json.dumps(record,indent=2)+"\n")
print(args.out)
