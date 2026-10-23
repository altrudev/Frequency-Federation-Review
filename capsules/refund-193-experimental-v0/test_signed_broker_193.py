"""Experimental signed handoff -> actual local broker + native APS/PIC verification."""
import base64
import copy
import json
import os
import socket
import threading
import time
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from provisional_handoff_193 import DOMAIN, canonical_bytes, operation_digest
from refund_broker_entrypoint import build_broker, build_runtime_verifier
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from test_cross_native import prepare_cross_fixture, native_aps
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import TEST_KEYRING
from hashlib import sha256

class SignedBroker193Tests(unittest.TestCase):
    def setUp(self):
        prepare_cross_fixture(self)
        self.key = Ed25519PrivateKey.generate()
        self.sock = self.root / 'signed-broker.sock'
        self.broker = build_broker({'socket_path':self.sock,'state_dir':self.root / 'signed-broker-state',
            'authorized_client_uid':os.getuid(),'aps_trusted_key':self.fixture['public_key'],
            'aps_trusted_issuer':self.fixture['boundary_identity'],'pic_keyring_path':TEST_KEYRING,
            'experimental_handoff_keys':{'sandbox-key':base64.b64encode(self.key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()}})
        self.thread = threading.Thread(target=self.broker.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)
        aps = native_aps(self.fixture, self.fixture['public_key'], self.fixture['boundary_identity'])
        pic = verify_pic_refund(self.pic, TEST_KEYRING)
        self.operation = {'schema':'refund-execution/0.1','operation_id':'refund-'+sha256(aps['approval_ref'].encode()).hexdigest(),'tool':'refund','arguments':aps['arguments'],'approval_ref':aps['approval_ref'],'aps_evidence_ref':aps['evidence_ref'],'pic_evidence_ref':pic['evidence_ref']}
        self.record = {'domain':DOMAIN,'approval_ref':aps['approval_ref'],'operation_digest':operation_digest(self.operation),'expires_at':int(time.time())+300,'key_id':'sandbox-key'}
    def close(self):
        self.broker.shutdown()
        self.broker.server_close()
        self.thread.join(timeout=3)
    def submit(self,operation=None,record=None,aps=None,pic=None,key=None,omit_handoff=False):
        rec = copy.deepcopy(self.record if record is None else record)
        signature=base64.b64encode((key or self.key).sign(canonical_bytes(rec))).decode('ascii')
        evidence={'aps':self.fixture if aps is None else aps,'pic':self.pic if pic is None else pic,'handoff':{'record':rec,'signature':signature}}
        if omit_handoff: del evidence['handoff']
        request={'operation':self.operation if operation is None else operation,'admission_evidence':evidence}
        with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as sock:
            sock.connect(str(self.sock))
            sock.sendall((json.dumps(request)+'\n').encode())
            return json.loads(sock.makefile().readline())
    def test_native_and_signed_handoff_single_effect(self):
        self.assertEqual(self.submit()['result']['status'],'observed_success')
        self.assertEqual(self.submit().get('error'),'broker-denied')
        self.assertEqual(self.broker.engine.simulator.effect_count(),1)
    def test_tampering_does_not_admit_or_create_effect(self):
        self.assertEqual(self.submit(omit_handoff=True).get("error"),"broker-denied")
        op=copy.deepcopy(self.operation)
        op['arguments']['amount_minor']=4100
        self.assertEqual(self.submit(operation=op).get('error'),'broker-denied')
        self.assertEqual(self.submit(record={**self.record,'expires_at':100}).get('error'),'broker-denied')
        self.assertEqual(self.submit(key=Ed25519PrivateKey.generate()).get('error'),'broker-denied')
        for change in ({'domain':'foreign'},{'key_id':'unknown'},{'operation_digest':'0'*64}):
            self.assertEqual(self.submit(record={**self.record,**change}).get('error'),'broker-denied')
        badaps=copy.deepcopy(self.fixture)
        badaps['receipt']['result']['verdict']='deny'
        self.assertEqual(self.submit(aps=badaps).get('error'),'broker-denied')
        badpic=copy.deepcopy(self.pic)
        badpic['action']['args']['payment_id']='pay_B'
        self.assertEqual(self.submit(pic=badpic).get('error'),'broker-denied')
        self.assertEqual(self.broker.engine.simulator.effect_count(),0)
        self.assertEqual(self.broker.journal.execute("SELECT count(*) FROM claims").fetchone()[0],0)

class RuntimeNativeVerifierTests(unittest.TestCase):
    def test_native_runtime_gate_without_socket(self):
        prepare_cross_fixture(self)
        key=Ed25519PrivateKey.generate()
        verify=build_runtime_verifier({'aps_trusted_key':self.fixture['public_key'],
            'aps_trusted_issuer':self.fixture['boundary_identity'],'pic_keyring_path':TEST_KEYRING,
            'experimental_handoff_keys':{'sandbox':base64.b64encode(key.public_key().public_bytes(Encoding.Raw,PublicFormat.Raw)).decode()}})
        aps=native_aps(self.fixture,self.fixture['public_key'],self.fixture['boundary_identity'])
        pic=verify_pic_refund(self.pic,TEST_KEYRING)
        op={'schema':'refund-execution/0.1','operation_id':'refund-'+sha256(aps['approval_ref'].encode()).hexdigest(),
            'tool':'refund','arguments':aps['arguments'],'approval_ref':aps['approval_ref'],
            'aps_evidence_ref':aps['evidence_ref'],'pic_evidence_ref':pic['evidence_ref']}
        record={'domain':DOMAIN,'approval_ref':op['approval_ref'],'operation_digest':operation_digest(op),
                'expires_at':int(time.time())+300,'key_id':'sandbox'}
        evidence={'aps':self.fixture,'pic':self.pic,'handoff':{'record':record,
            'signature':base64.b64encode(key.sign(canonical_bytes(record))).decode()}}
        self.assertTrue(verify(op,evidence))
        self.assertFalse(verify(op,{'aps':self.fixture,'pic':self.pic}))
        self.assertFalse(verify(op,{**evidence,'handoff':{}}))
        self.assertFalse(verify({**op,'arguments':{**op['arguments'],'amount_minor':3999}},evidence))
        badaps=copy.deepcopy(self.fixture);badaps['receipt']['result']['verdict']='deny'
        self.assertFalse(verify(op,{**evidence,'aps':badaps}))
        badpic=copy.deepcopy(self.pic);badpic['action']['args']['payment_id']='pay_B'
        self.assertFalse(verify(op,{**evidence,'pic':badpic}))
