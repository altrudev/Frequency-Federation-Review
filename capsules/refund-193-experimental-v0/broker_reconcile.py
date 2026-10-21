"""Read-only local simulator reconciliation. No dispatch, no state promotion."""
import json
from refund_sandbox import stable_sha256

def inspect_claim(broker, approval_ref):
    with broker.journal_lock:
        row=broker.journal.execute("SELECT binding,status FROM claims WHERE approval=?",(approval_ref,)).fetchone()
    if row is None:
        return {"status":"not_found","dispatch_attempted":False}
    binding,status=row
    matches=[]
    try:
        for path in broker.engine.operations_dir.glob("*.json"):
            record=json.loads(path.read_text())
            if record.get("approval_ref")!=approval_ref:
                continue
            key=record.get("idempotency_key")
            observed=broker.engine.simulator.observe(key) if isinstance(key,str) else None
            integrity="no_local_effect"
            if observed is not None:
                good=(observed.get("operation_id")==record.get("operation_id")
                    and observed.get("arguments_digest")==record.get("arguments_digest")
                    and record.get("arguments_digest")==stable_sha256(record.get("arguments")))
                integrity="local_effect_binding_verified" if good else "local_effect_binding_mismatch"
            matches.append({"operation_id":record.get("operation_id"),"executor_status":record.get("status"),
                "effect_ref":record.get("effect_ref"),"local_effect_integrity":integrity})
    except (OSError,ValueError,TypeError):
        return {"status":"inspection_error","claim_status":status,"dispatch_attempted":False}
    return {"status":"inspection_only","claim_status":status,"binding":binding,
        "matching_operations":matches,"dispatch_attempted":False,"provider_authority":"local-simulator-only"}
