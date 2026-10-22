"""Native APS verifier adapter for isolated refund integration.

This is runtime code, independent of unittest modules. Trust supplied by caller.
"""
import json
import os
import pathlib
import subprocess

APS_DIR=pathlib.Path(__file__).resolve().parent/"aps-runtime"

def native_aps(artifact, trusted_key, trusted_issuer):
    if not isinstance(trusted_key,str) or not trusted_key or not isinstance(trusted_issuer,str) or not trusted_issuer:
        raise ValueError("trusted-aps-configuration-required")
    proc=subprocess.run(
        ["node","--import","tsx","verify-refund.ts"],
        cwd=APS_DIR,
        input=json.dumps(artifact),
        text=True,capture_output=True,
        env={**os.environ,"APS_TRUSTED_KEY":trusted_key,"APS_TRUSTED_ISSUER":trusted_issuer},
        timeout=10,check=False,
    )
    if proc.returncode:
        raise ValueError("native-aps-verification-failed")
    result=json.loads(proc.stdout)
    if not isinstance(result,dict) or result.get("valid") is not True:
        raise ValueError("native-aps-denied")
    result.pop("valid")
    return result
