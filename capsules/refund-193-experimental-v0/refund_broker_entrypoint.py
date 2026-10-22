#!/usr/bin/env python3
"""Fail-closed Frequency refund broker entrypoint.

Current release profile is simulator-only. Real provider execution is unsupported.
"""
import argparse,base64,json,os
from pathlib import Path
from broker_native_verifier import build_native_verifier
from refund_broker import Broker
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from provisional_handoff_193 import build_provisional_verifier

_REQUIRED={"socket_path","state_dir","authorized_client_uid","aps_trusted_key",
          "aps_trusted_issuer","pic_keyring_path","simulator_only","experimental_handoff_keys"}

def handoff_keys(config):
    """Decode externally provisioned sandbox trust, never request-supplied keys."""
    values=config.get("experimental_handoff_keys")
    if not isinstance(values,dict) or not values:
        raise ValueError("experimental-handoff-trust-required")
    keys={}
    for key_id,value in values.items():
        if not isinstance(key_id,str) or not key_id.strip() or not isinstance(value,str):
            raise ValueError("experimental-handoff-key-invalid")
        try:
            keys[key_id]=Ed25519PublicKey.from_public_bytes(base64.b64decode(value,validate=True))
        except Exception as exc:
            raise ValueError("experimental-handoff-key-invalid") from exc
    return keys

def load_config(path):
    p=Path(path)
    data=json.loads(p.read_text())
    if not isinstance(data,dict) or set(data)!=_REQUIRED|({"socket_gid"} if "socket_gid" in data else set()):
        raise ValueError("runtime-config-fields-invalid")
    if data["simulator_only"] is not True:
        raise ValueError("real-provider-execution-not-supported")
    if type(data["authorized_client_uid"]) is not int or data["authorized_client_uid"]<0:
        raise ValueError("authorized-client-uid-invalid")
    if "socket_gid" in data and (type(data["socket_gid"]) is not int or data["socket_gid"]<0):
        raise ValueError("socket-gid-invalid")
    if not isinstance(data["aps_trusted_key"],str) or not data["aps_trusted_key"]:
        raise ValueError("aps-trusted-key-required")
    if not isinstance(data["aps_trusted_issuer"],str) or not data["aps_trusted_issuer"]:
        raise ValueError("aps-trusted-issuer-required")
    if not Path(data["pic_keyring_path"]).is_file():
        raise ValueError("pic-keyring-missing")
    socket_path=Path(data["socket_path"])
    state_dir=Path(data["state_dir"])
    if not socket_path.is_absolute() or not state_dir.is_absolute():
        raise ValueError("absolute-runtime-paths-required")
    if not socket_path.parent.is_dir():
        raise ValueError("socket-parent-missing")
    handoff_keys(data)
    state_dir.mkdir(parents=True,exist_ok=True)
    return data

def build_runtime_verifier(config):
    keys=handoff_keys(config)
    native=build_native_verifier(config["aps_trusted_key"],config["aps_trusted_issuer"],config["pic_keyring_path"])
    return build_provisional_verifier(native,keys)

def build_broker(config):
    verifier=build_runtime_verifier(config)
    return Broker(config["socket_path"],config["state_dir"],config["authorized_client_uid"],
                  verifier,socket_gid=config.get("socket_gid"))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--config",required=True)
    ap.add_argument("--check",action="store_true")
    args=ap.parse_args()
    config=load_config(args.config)
    build_runtime_verifier(config)
    if args.check:
        print("CONFIG_OK_SIMULATOR_ONLY")
        return
    with build_broker(config) as server:
        server.serve_forever()

if __name__=="__main__":
    main()
