"""Negative proofs for an explicitly nonstandard experimental handoff."""
import base64
import copy
import time
import unittest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from provisional_handoff_193 import DOMAIN, canonical_bytes, operation_digest, verify_handoff, build_provisional_verifier

class ExperimentalHandoffTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.trust = {'sandbox-issuer': self.key.public_key()}
        self.op = {'schema':'refund-execution/0.1','operation_id':'refund-1','tool':'refund','arguments':{'payment_id':'pay_A','amount_minor':4000,'currency':'EUR'},'approval_ref':'approval-1','aps_evidence_ref':'aps-evidence','pic_evidence_ref':'pic-evidence'}
        self.record={'domain':DOMAIN,'approval_ref':'approval-1','operation_digest':operation_digest(self.op),'expires_at':int(time.time())+300,'key_id':'sandbox-issuer'}
    def signed(self, record=None, key=None):
        record = copy.deepcopy(self.record if record is None else record)
        return {'record':record, 'signature':base64.b64encode((key or self.key).sign(canonical_bytes(record))).decode('ascii')}
    def test_valid_signed_handoff_and_native_verifier(self):
        envelope=self.signed()
        self.assertTrue(verify_handoff(self.op,envelope,self.trust))
        evidence={'aps':'native-aps','pic':'native-pic','handoff':envelope}
        gate=build_provisional_verifier(lambda op,ev: ev=={'aps':'native-aps','pic':'native-pic'},self.trust)
        self.assertTrue(gate(self.op,evidence))
        self.assertFalse(build_provisional_verifier(lambda op,ev: False,self.trust)(self.op,evidence))
    def test_fail_closed_mutation_matrix(self):
        for field, value in [('payment_id','pay_B'),('amount_minor',3999),('currency','USD')]:
            with self.subTest(field=field):
                op=copy.deepcopy(self.op);op['arguments'][field]=value
                self.assertFalse(verify_handoff(op,self.signed(),self.trust))
        for key,value in [('approval_ref','other'),('operation_digest','0'*64),('key_id','unknown'),('domain','foreign')]:
            with self.subTest(key=key):
                record={**self.record,key:value}
                self.assertFalse(verify_handoff(self.op,self.signed(record),self.trust))
        self.assertFalse(verify_handoff(self.op,self.signed(self.record,Ed25519PrivateKey.generate()),self.trust))
        self.assertFalse(verify_handoff(self.op,{'record':self.record,'signature':'bad'},self.trust))
        self.assertFalse(verify_handoff(self.op,self.signed({**self.record,'expires_at':100}),self.trust))
        self.assertFalse(verify_handoff(self.op,self.signed(),{}))
        self.assertFalse(verify_handoff(self.op,{'record':{**self.record,'unknown':1},'signature':self.signed()['signature']},self.trust))
        self.assertFalse(verify_handoff(self.op,{'record':self.record},self.trust))
        self.assertFalse(verify_handoff({**self.op,'arguments':{**self.op['arguments'],'extra':3}},self.signed(),self.trust))
    def test_reject_untrusted_native_or_missing_trust(self):
        with self.assertRaises(ValueError):build_provisional_verifier(lambda o,e: True,{})
        v=build_provisional_verifier(lambda o,e: True,self.trust)
        self.assertFalse(v(self.op,{'handoff':self.signed()}))
        self.assertFalse(v(self.op,{'aps':{},'pic':{},'handoff':self.signed(),'extra':'yes'}))

class StrictTrustTests(unittest.TestCase):
    def test_signature_not_valid_for_other_operation_or_domain(self):
        t=ExperimentalHandoffTests()
        t.setUp()
        signed=t.signed()
        for key, replacement in [('operation_id','refund-other'),('approval_ref','approval-other'),('pic_evidence_ref','pic-other')]:
            with self.subTest(key=key):
                op=copy.deepcopy(t.op)
                op[key]=replacement
                self.assertFalse(verify_handoff(op,signed,t.trust))
        self.assertFalse(verify_handoff(t.op,signed,t.trust,now=t.record['expires_at']))
