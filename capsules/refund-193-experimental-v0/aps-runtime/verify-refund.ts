import { readFileSync } from 'node:fs'
import { computeActionRefV2, computePayloadRefV1, verifyReceiptV1 } from 'agent-passport-system'
const input=JSON.parse(readFileSync(0,'utf8'))
const trustedKey=process.env.APS_TRUSTED_KEY
const trustedIssuer=process.env.APS_TRUSTED_ISSUER
const refundTarget=(paymentId:string)=>`https://payments.operator.example/v1/payments/${paymentId}/refunds`
const r=input.receipt, action=input.input, args=input.arguments
const refuse=(reason:string)=>{ console.log(JSON.stringify({valid:false,reason}));process.exitCode=2 }
if(!trustedKey || !trustedIssuer) refuse('trusted-key-unconfigured')
else if(!r || !action || !args || typeof args.payment_id!=='string' || !Number.isSafeInteger(args.amount_minor) || args.amount_minor<=0 || typeof args.currency!=='string') refuse('invalid-input')
else {
 const v=verifyReceiptV1(r,(signer:string)=>signer===trustedIssuer?trustedKey:undefined,{expectedReceiptType:'aps:policy-decision:v1',boundaryIdentity:trustedIssuer})
 if(v.status!=='valid') refuse('signature-or-schema-invalid')
 else if(r.result?.verdict!=='permit' || r.result?.constraints?.length!==0) refuse('not-unconstrained-permit')
 else if(Date.parse(r.result.valid_until)<Date.now()) refuse('expired')
 else if(action.action_type!=='refund' || action.target!==refundTarget(args.payment_id)) refuse('wrong-refund-target')
 else if(computePayloadRefV1(args)!==action.payload_ref || computeActionRefV2(action)!==r.action_ref) refuse('payload-or-action-mismatch')
 else console.log(JSON.stringify({valid:true,approval_ref:r.receipt_id,tool:'refund',arguments:args,decision:'permit',evidence_ref:r.receipt_id}))
}
