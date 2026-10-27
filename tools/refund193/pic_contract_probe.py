#!/usr/bin/env python3
"""Non-authoritative, read-only PIC result/proposal compatibility probe."""
import argparse
import hashlib
import json
from pathlib import Path

from verify import InvalidEvidence, parse_json, validate_args, require, HEX

RESULT_FIELDS = {"args_digest", "result"}
PROPOSAL_FIELDS = {"arguments"}

def probe(proposal, result):
    """Closed synthetic subset; never asserts native PIC signature or refund authority."""
    errors = []
    try:
        require(type(proposal) is dict and set(proposal) == PROPOSAL_FIELDS, "proposal_shape")
        args = proposal["arguments"]
        validate_args(args)
    except (InvalidEvidence, KeyError, TypeError) as exc:
        errors.append("proposal:" + str(exc))
        args = None
    try:
        require(type(result) is dict and set(result) == RESULT_FIELDS, "result_shape")
        require(type(result["args_digest"]) is str and HEX.fullmatch("sha256:" + result["args_digest"]) is not None, "result_digest")
        require(result["result"] == "allow", "result_not_allow")
        if args is not None:
            # This intentionally supports only the three constrained ASCII synthetic fields.
            raw = json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
            require(hashlib.sha256(raw).hexdigest() == result["args_digest"], "arguments_digest_mismatch")
    except (InvalidEvidence, KeyError, TypeError) as exc:
        errors.append("result:" + str(exc))
    return {
        "schema": "altru-pic-contract-probe/1",
        "verdict": "FAIL" if errors else "NOT_ESTABLISHED",
        "syntax_and_digest": "FAIL" if errors else "PASS",
        "producer_authenticity": "NOT_ESTABLISHED",
        "native_pic_verification": "NOT_ESTABLISHED",
        "execution_authorized": False,
        "reasons": errors if errors else ["synthetic_unverified_pic_result_and_proposal"],
    }

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("proposal", type=Path)
    p.add_argument("result", type=Path)
    a = p.parse_args()
    try:
        data = probe(parse_json(a.proposal.read_bytes()), parse_json(a.result.read_bytes()))
    except (OSError, InvalidEvidence, ValueError, TypeError) as exc:
        data = {"schema": "altru-pic-contract-probe/1", "verdict": "FAIL", "syntax_and_digest": "FAIL",
                "producer_authenticity": "NOT_ESTABLISHED", "native_pic_verification": "NOT_ESTABLISHED",
                "execution_authorized": False, "reasons": [str(exc)]}
    print(json.dumps(data, sort_keys=True, indent=2))
    return 1 if data["verdict"] == "FAIL" else 2

if __name__ == "__main__":
    raise SystemExit(main())
