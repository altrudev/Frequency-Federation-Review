"""Issue #193: simulator-only contract boundary checks; not signed-handoff conformance."""
import copy
import tempfile
import unittest
from pathlib import Path
from test_native_broker import NativeBrokerTests
from refund_sandbox import LocalRefundSimulator, SimulatedResponseLost, BindingMismatch


class Contract193BoundaryTests(NativeBrokerTests):
    def test_exact_argument_mutations_refused_without_effect(self):
        original = self.operation()
        for field, value in [('payment_id','pay_B'),('amount_minor',3999),('currency','USD'),('amount_minor',4001),('amount_minor',True),('amount_minor',4000.5)]:
            with self.subTest(field=field,value=value):
                mutated=copy.deepcopy(original)
                mutated['arguments'][field]=value
                self.assertEqual(self.send(mutated).get('error'),'broker-denied')
                self.assertEqual(self.broker.engine.simulator.effect_count(),0)

    def test_extra_fields_and_unsafe_integer_refused(self):
        base=self.operation()
        for change in ({'unexpected': 'new-claim'}, {'amount_minor': 2**53}, {'amount_minor': 0}, {'payment_id': ''}):
            with self.subTest(change=change):
                op=copy.deepcopy(base)
                op['arguments'].update(change)
                self.assertEqual(self.send(op).get('error'), 'broker-denied')
                self.assertEqual(self.broker.engine.simulator.effect_count(),0)

    def test_missing_and_invalid_evidence_refused(self):
        op=self.operation()
        bad_aps=copy.deepcopy(self.fixture)
        bad_aps['receipt']['result']['verdict']='deny'
        self.assertEqual(self.send(op,aps=bad_aps).get('error'),'broker-denied')
        self.assertEqual(self.broker.engine.simulator.effect_count(),0)

    def test_duplicate_approval_never_dispatches_twice(self):
        op=self.operation()
        self.assertEqual(self.send(op)['result']['status'],'observed_success')
        self.assertEqual(self.send(op).get('error'),'broker-denied')
        self.assertEqual(self.broker.engine.simulator.effect_count(),1)

    def test_simulator_response_lost_retry_same_effect(self):
        with tempfile.TemporaryDirectory() as d:
            simulator=LocalRefundSimulator(Path(d))
            args={'payment_id':'pay_A','amount_minor':4000,'currency':'EUR'}
            with self.assertRaises(SimulatedResponseLost):
                simulator.dispatch(idempotency_key='op-193',operation_id='refund-193',arguments=args,lose_response_after_commit=True)
            result=simulator.dispatch(idempotency_key='op-193',operation_id='refund-193',arguments=args)
            self.assertEqual(simulator.effect_count(),1)
            self.assertEqual(result['operation_id'],'refund-193')
            with self.assertRaises(BindingMismatch):
                simulator.dispatch(idempotency_key='op-193',operation_id='refund-193',arguments={**args,'amount_minor':4100})
            self.assertEqual(simulator.effect_count(),1)
