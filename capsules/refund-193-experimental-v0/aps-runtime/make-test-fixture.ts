import { createHash, randomBytes } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { buildDecisionRefV1, computeActionRefV2, computePayloadRefV1, createActionReferenceInputV2, createReceiptV1, generateKeyPair, verifyReceiptV1 } from 'agent-passport-system'
const digest=(s:string)=>createHash('sha256').update(s).digest('hex')
const refundTarget=(paymentId:string)=>`https://payments.operator.example/v1/payments/${paymentId}/refunds`
const message=JSON.parse(readFileSync(0,'utf8')); const args=message.arguments
if(!args || Object.keys(args).sort().join(',')!=='amount_minor,currency,payment_id' || !Number.isSafeInteger(args.amount_minor) || args.amount_minor<=0 || typeof args.payment_id!=='string' || typeof args.currency!=='string') throw Error('invalid-refund-payload')
const keys=generateKeyPair(); const actor='did:example:synthetic-worker'; const boundary='did:example:synthetic-refund-operator'; const issued=new Date().toISOString()
const input=createActionReferenceInputV2({agent_id:actor,action_type:'refund',target:refundTarget(args.payment_id),payload_ref:computePayloadRefV1(args),scope_required:['payments:refund'],issued_at:issued,nonce:randomBytes(16).toString('hex')})
const action_ref=computeActionRefV2(input)
const result={profile:'aps-core-decision-output-v1',verdict:'permit',effective_authority_ref:digest('synthetic'),constraints:[],valid_until:new Date(Date.now()+60000).toISOString()}
const decision_ref=buildDecisionRefV1({action_ref,authority_state:{synthetic:true},policy_input:{operator_approved:args},decision_context:{test:'radial'},decision_output:result}).decision_ref
const receipt=createReceiptV1({profile:'aps-receipt-v1',receipt_type:'aps:policy-decision:v1',issuer:boundary,subject_agent:actor,action_ref,delegation_ref:'sha256:'+digest('synthetic-delegation'),decision_ref,issued_at:issued,evidence_refs:[],result,prev:digest('synthetic-intent')},[{signer:boundary,key_id:'test',private_key:keys.privateKey}])
const check=verifyReceiptV1(receipt,(signer:string)=>signer===boundary?keys.publicKey:undefined,{boundaryIdentity:boundary,expectedReceiptType:'aps:policy-decision:v1'})
if(check.status!=='valid') throw Error('native-aps-receipt-invalid:'+check.status)
console.log(JSON.stringify({receipt,public_key:keys.publicKey,boundary_identity:boundary,input,arguments:args,approval_ref:receipt.receipt_id}))
