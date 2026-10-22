"""DDC Radial read-only preflight: never creates accounts or starts services."""
import json, os, pathlib, pwd, stat, sys
def check(root):
    findings=[]
    def add(code,ok,detail): findings.append({"id":code,"pass":bool(ok),"detail":detail})
    try:
        account=pwd.getpwnam("refundexec")
    except KeyError:
        account=None
    add("OS-IDENTITY",account is not None,"dedicated refundexec account required")
    base=pathlib.Path(root)
    add("BINARY-ROOT",base.exists() and base.stat().st_uid==0 if base.exists() else False,"broker deployment owned by root")
    add("STATE-LOCATION",not str(base).startswith("/home/ubuntu/"),"no protected executor code/state under ubuntu home")
    secret=pathlib.Path("/etc/frequency-refund/trust.env")
    add("TRUST-ANCHOR",secret.exists() and secret.stat().st_uid==0 and stat.S_IMODE(secret.stat().st_mode)==0o600 if secret.exists() else False,"externally provisioned root-owned 0600 trust configuration")
    add("BROKER-ENTRYPOINT",pathlib.Path("/usr/local/libexec/frequency-refund-broker").exists(),"audited production entrypoint, not test fixture")
    return {"verdict":"PASS" if all(f["pass"] for f in findings) else "HOLD","findings":findings}
if __name__=="__main__":
    print(json.dumps(check(sys.argv[1] if len(sys.argv)>1 else "/opt/frequency-refund"),indent=2))
