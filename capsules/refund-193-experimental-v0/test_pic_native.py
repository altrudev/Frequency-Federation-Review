import copy,json
from pic_native_adapter import verify_pic_refund
from pic_test_fixture import MOD,TEST_KEYRING

decision=json.loads((MOD.FIXTURES_DIR/"merchant_decision.json").read_text())
proposal=MOD.build_signed_proposal(merchant_decision=decision)
assert verify_pic_refund(proposal,TEST_KEYRING)["decision"]=="permit"
mutated=copy.deepcopy(proposal);mutated["action"]["args"]["amount_minor"]=4100
try: verify_pic_refund(mutated,TEST_KEYRING); raise AssertionError("altered amount admitted")
except ValueError: pass
mutated=copy.deepcopy(proposal);mutated["action"]["args"]["payment_id"]="pay_B"
try: verify_pic_refund(mutated,TEST_KEYRING); raise AssertionError("altered payment admitted")
except ValueError: pass
print("PIC_NATIVE_VERIFIER: signed=PASS altered_amount=DENY altered_payment=DENY")
