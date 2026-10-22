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
from broker_native_verifier import build_native_verifier
from provisional_handoff_193 import DOMAIN, canonical_bytes, operation_digest, build_provisional_verifier
from refund_broker import Broker
from test_cross_native import prepare_cross_fixture, native_aps
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import TEST_KEYRING
from hashlib import sha256

class SignedBroker193Tests(unittest.TestCase):
    def setUp(self):
        prepare_cross_fixture(self)
        self.key = Ed25519PrivateKey.generate()
        native = build_native_verifier(self.fixture['public_key'], self.fixture['boundary_identity'], TEST_KEYRING)
        self.sock = self.root / 'signed-broker.sock'
        self.broker = Broker(self.sock, self.root / 'signed-broker-state', os.getuid(), build_provisional_verifier(native, {'sandbox-key':self.key.public_key()}))
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
    def submit(self,operation=None,record=None,aps=None,pic=None,key=None):
        rec = copy.deepcopy(self.record if record is None else record)
        signature=base64.b64encode((key or self.key).sign(canonical_bytes(rec))).decode('ascii')
        evidence={'aps':self.fixture if aps is None else aps,'pic':self.pic if pic is None else pic,'handoff':{'record':rec,'signature':signature}}
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
        op=copy.deepcopy(self.operation)
        op['arguments']['amount_minor']=4100
        self.assertEqual(self.submit(operation=op).get('error'),'broker-denied')
        self.assertEqual(self.submit(record={**self.record,'expires_at':100}).get('error'),'broker-denied')
        self.assertEqual(self.submit(key=Ed25519PrivateKey.generate()).get('error'),'broker-denied')
        badaps=copy.deepcopy(self.fixture)
        badaps['receipt']['result']['verdict']='deny'
        self.assertEqual(self.submit(aps=badaps).get('error'),'broker-denied')
        badpic=copy.deepcopy(self.pic)
        badpic['action']['args']['payment_id']='pay_B'
        self.assertEqual(self.submit(pic=badpic).get('error'),'broker-denied')
        self.assertEqual(self.broker.engine.simulator.effect_count(),0)
