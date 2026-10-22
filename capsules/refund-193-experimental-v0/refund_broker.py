"""Unix-socket refund broker for the simulator-only Frequency integration.

External responses remain deliberately non-sensitive. Internal audit events retain
stable failure classes for operator diagnosis.
"""
import hashlib,json,os,socketserver,sqlite3,struct,threading,time
from pathlib import Path
from refund_sandbox import RefundExecutionEngine

class BrokerDenied(Exception):
    def __init__(self,code):
        super().__init__(code);self.code=code

class Broker(socketserver.UnixStreamServer):
    allow_reuse_address=False
    def __init__(self,socket_path,state_dir,allowed_uid,verify_admission=None,socket_gid=None):
        if type(allowed_uid) is not int or allowed_uid<0:raise ValueError("authorized-client-uid-required")
        self.allowed_uid=allowed_uid;self.socket_gid=socket_gid;self.verify_admission=verify_admission
        self.engine=RefundExecutionEngine(Path(state_dir))
        self.journal=sqlite3.connect(str(Path(state_dir)/"broker-admissions.sqlite"),check_same_thread=False,isolation_level=None)
        self.journal.execute("PRAGMA journal_mode=WAL");self.journal.execute("PRAGMA synchronous=FULL")
        self.journal.execute("CREATE TABLE IF NOT EXISTS claims (approval TEXT PRIMARY KEY,binding TEXT NOT NULL,status TEXT NOT NULL)")
        self.journal.execute("CREATE TABLE IF NOT EXISTS audit_events (id INTEGER PRIMARY KEY AUTOINCREMENT,ts REAL NOT NULL,event TEXT NOT NULL,approval TEXT,detail TEXT)")
        self.journal_lock=threading.Lock()
        super().__init__(str(socket_path),Handler)
        if socket_gid is not None:
            if type(socket_gid) is not int or socket_gid<0:raise ValueError("socket-gid-invalid")
            os.chown(socket_path,-1,socket_gid);os.chmod(socket_path,0o660)
        else:os.chmod(socket_path,0o600)
    def audit(self,event,approval=None,detail=None):
        safe_detail=(detail or "")[:120]
        try:
            with self.journal_lock:
                self.journal.execute("INSERT INTO audit_events(ts,event,approval,detail) VALUES(?,?,?,?)",(time.time(),event,approval,safe_detail))
        except Exception:
            pass

class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        approval=None
        try:
            _pid,uid,_gid=struct.unpack("3i",self.request.getsockopt(1,17,12))
            if uid!=self.server.allowed_uid:
                self.server.audit("peer-denied",detail="uid-mismatch");self.wfile.write(b'{"error":"peer-denied"}\n');return
            raw=self.rfile.readline(65537)
            if not raw or len(raw)>65536:raise BrokerDenied("invalid-frame")
            try:req=json.loads(raw)
            except (json.JSONDecodeError,UnicodeDecodeError) as exc:raise BrokerDenied("invalid-json") from exc
            if not isinstance(req,dict) or set(req)!={"operation","admission_evidence"}:raise BrokerDenied("unsupported-command")
            if not callable(self.server.verify_admission):raise BrokerDenied("admission-verifier-unconfigured")
            op=req.get("operation")
            if isinstance(op,dict) and isinstance(op.get("approval_ref"),str):approval=op["approval_ref"]
            if self.server.verify_admission(op,req["admission_evidence"]) is not True:raise BrokerDenied("admission-not-verified")
            binding=hashlib.sha256(json.dumps(op,sort_keys=True,separators=(",",":")).encode()).hexdigest()
            with self.server.journal_lock:
                db=self.server.journal;db.execute("BEGIN IMMEDIATE")
                try:
                    db.execute("INSERT INTO claims VALUES (?,?,?)",(approval,binding,"in_flight"));db.execute("COMMIT")
                except sqlite3.IntegrityError as exc:
                    db.execute("ROLLBACK");raise BrokerDenied("approval-claimed-or-uncertain") from exc
                except Exception:
                    db.execute("ROLLBACK");raise
            try:result=self.server.engine.execute(op)
            except Exception as exc:
                self.server.audit("executor-error",approval,type(exc).__name__);raise
            with self.server.journal_lock:
                self.server.journal.execute("UPDATE claims SET status=? WHERE approval=?",(result["status"],approval))
            self.server.audit("dispatch-result",approval,result["status"])
            self.wfile.write((json.dumps({"result":result})+"\n").encode())
        except BrokerDenied as exc:
            self.server.audit(exc.code,approval);self.wfile.write(b'{"error":"broker-denied"}\n')
        except Exception as exc:
            self.server.audit("internal-error",approval,type(exc).__name__);self.wfile.write(b'{"error":"broker-denied"}\n')

def serve(socket_path,state_dir,allowed_uid,verify_admission,socket_gid=None):
    if not callable(verify_admission):raise ValueError("admission-verifier-required")
    with Broker(socket_path,state_dir,allowed_uid,verify_admission,socket_gid=socket_gid) as server:server.serve_forever()
