"""Radial staging audit. Reject executable deployment from user-writable home.
Read-only: no privilege escalation, no service changes.
"""
import os, pathlib, stat
def inspect(target, trusted_key_file, service_uid, client_uid, socket_group):
    problems=[]
    target=pathlib.Path(target)
    if not target.is_absolute() or not target.exists():problems.append("package-missing")
    else:
        for path in (target,*target.parents):
            mode=path.stat().st_mode
            if path.stat().st_uid!=0:problems.append("non-root-owned-path:"+str(path))
            if mode & (stat.S_IWGRP|stat.S_IWOTH):problems.append("writable-path:"+str(path))
    if service_uid is None or client_uid is None or service_uid==client_uid:
        problems.append("distinct-identities-required")
    if socket_group is None:problems.append("client-socket-group-required")
    trust=pathlib.Path(trusted_key_file)
    if not trust.is_file():problems.append("trust-file-missing")
    elif trust.stat().st_uid!=0 or trust.stat().st_mode & (stat.S_IWGRP|stat.S_IWOTH|stat.S_IROTH):
        problems.append("trust-file-permissions-invalid")
    return {"verdict":"HOLD" if problems else "PREFLIGHT_ONLY_PASS","problems":problems}
