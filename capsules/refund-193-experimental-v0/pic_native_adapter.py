"""PIC refund verifier with caller-supplied trust.

Runtime code never loads the example keyring or any private key.
"""
import hashlib, json
from pathlib import Path

PIC_ROOT=Path(__file__).resolve().parent

from pic_standard.canonical import canonicalize
from pic_standard.keyring import StaticKeyRingResolver, TrustedKeyRing
from pic_standard.pipeline import PipelineOptions, verify_proposal
from pic_standard.policy import PICPolicy

def verify_pic_refund(proposal, trusted_keyring_path):
    path=Path(trusted_keyring_path)
    if not path.is_file():
        raise ValueError("trusted-pic-keyring-required")
    keyring=TrustedKeyRing.from_json_file(path)
    result=verify_proposal(
        proposal,
        options=PipelineOptions(
            verify_evidence=True,
            strict_trust=True,
            policy=PICPolicy(),
            key_resolver=StaticKeyRingResolver(keyring),
            proposal_base_dir=PIC_ROOT,
        ),
    )
    if not result.ok:
        raise ValueError("pic-native-verification-denied")
    if proposal.get("impact")!="money" or not isinstance(proposal.get("action"),dict):
        raise ValueError("pic-invalid-refund-impact")
    action=proposal["action"]; claims=proposal.get("claims")
    if action.get("tool")!="refund" or not isinstance(claims,list) or len(claims)!=1:
        raise ValueError("pic-refund-contract-mismatch")
    try:
        claim=json.loads(claims[0]["text"])
    except Exception as exc:
        raise ValueError("pic-claim-invalid") from exc
    approval=claim.get("approval_ref")
    if not isinstance(approval,str) or not approval:
        raise ValueError("pic-approval-identity-missing")
    return {"approval_ref":approval,"tool":"refund","arguments":action["args"],
            "decision":"permit","evidence_ref":hashlib.sha256(canonicalize(proposal)).hexdigest()}
