import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { verifyTypedData } from 'ethers';

const PROFILE = 'frequency.external-assurance.aps-priorseal.v1';
const APS_COMMIT = '948f99b85343bef2c6fa677c8543965caacfc087';
const PRIORSEAL_COMMIT = 'd749d2691c3e6be139de4020e7b27cdafca2c428';
const REFERENCE_TIME = '2026-09-19T10:05:00.000Z';
const REFERENCE_MS = Date.parse(REFERENCE_TIME);
const APS_MANIFEST_SHA256 = '2bf365bc9124ecfc943d5be86c34e8e0cacd51a5929b8d0c906e633a017231f9';
const POSITIVE_SHA256 = 'c8dd05f412b3d1dd957f66deaf231a8becb9656e8bd1960ba88638cf9ad4c6da';
const OVER_LIMIT_SHA256 = 'cb45a8378a5c9f1f7f2695c4d1fb5cbe344d9c840b799cf0ecb786e5ddf3c226';
const REPORT_SHA256 = 'd2c1bea5f0acf0afe06c944376c5a471402ab5d48bf85ca267ed9b5876336ae4';
const APS_KEYS = Object.freeze({
  'did:example:agent#key-1': 'f80727401f51c1b7e41eeda7004b29aca9c9d7a017144c31f7370725514d6260',
  'did:example:boundary#key-1': '6468a72acb50bf67fc180d0a092e22d1aa44a43268c8e2dc7b6302dc9199126c',
  'did:example:principal#key-1': 'd69859e9701161194f0f583a2369d287ce895bf0e96b70db753b9e1e27b2bc94'
});
const PRIORSEAL_ISSUER = 'priorseal.aps-163-fixture';
const PRIORSEAL_KEY_ID = 'aps-163-priorseal-test-key-1';
const PRIORSEAL_PUBLIC_KEY_PEM = `-----BEGIN PUBLIC KEY-----\nMCowBQYDK2VwAyEA4v4qObcyZkKCfW2C1JdiLNbCl/54Jw6qQ2sB8Ia288s=\n-----END PUBLIC KEY-----\n`;

const CLAIM = Object.freeze({ ESTABLISHED:'ESTABLISHED', CONTRADICTED:'CONTRADICTED', NOT_ESTABLISHED:'NOT_ESTABLISHED' });

function fail(message) { throw new Error(message); }
function bytes(p) { return fs.readFileSync(p); }
function json(p) { return JSON.parse(fs.readFileSync(p, 'utf8')); }
function sha256Bytes(b) { return crypto.createHash('sha256').update(b).digest('hex'); }
function sha256Text(s) { return sha256Bytes(Buffer.from(s, 'utf8')); }
function hashJson(v) { return sha256Text(priorsealCanonical(v)); }
function strip(obj, ...keys) { const out = structuredClone(obj); for (const key of keys) delete out[key]; return out; }
function eq(a,b,msg){ if(a!==b) fail(`${msg}: expected ${b}, got ${a}`); }
function requireTrue(v,msg){ if(!v) fail(msg); }
function hex64(v){ return typeof v==='string' && /^[0-9a-f]{64}$/.test(v); }
function claim(id, result, evidence=[], ceiling=null, detail=null) { return { id, result, evidence, ...(detail?{detail}:{}), ...(ceiling?{claim_ceiling:ceiling}:{}) }; }

// Pinned fixtures contain no object keys whose JS UTF-16 order diverges from RFC 8785.
// This serializer is deliberately local to this bounded adapter; it is not exported as
// a general-purpose canonicalizer.
function canonicalValue(v) {
  if (v === null || typeof v === 'boolean' || typeof v === 'string') return v;
  if (typeof v === 'number') {
    if (!Number.isFinite(v) || (Number.isInteger(v) && !Number.isSafeInteger(v))) fail('non-interoperable JSON number');
    return v;
  }
  if (Array.isArray(v)) return v.map(canonicalValue);
  if (typeof v !== 'object') fail('unsupported JSON value');
  const out = {};
  for (const k of Object.keys(v).sort()) {
    if (['__proto__','prototype','constructor'].includes(k)) fail('unsafe JSON key');
    out[k] = canonicalValue(v[k]);
  }
  return out;
}
function priorsealCanonical(v) { return JSON.stringify(canonicalValue(v)); }
function apsJcs(v) { return JSON.stringify(canonicalValue(v)); }

function ed25519RawKey(hex) {
  const raw = Buffer.from(hex, 'hex');
  if (raw.length !== 32) fail('bad Ed25519 public key length');
  return crypto.createPublicKey({ key: Buffer.concat([Buffer.from('302a300506032b6570032100','hex'), raw]), format:'der', type:'spki' });
}
function verifyEdRaw(publicHex, message, signatureHex) {
  return crypto.verify(null, Buffer.from(message,'utf8'), ed25519RawKey(publicHex), Buffer.from(signatureHex,'hex'));
}
function verifyEdPem(pem, message, sigB64Url) {
  const sig = Buffer.from(sigB64Url.replace(/-/g,'+').replace(/_/g,'/') + '='.repeat((4 - sigB64Url.length % 4) % 4), 'base64');
  return crypto.verify(null, Buffer.from(message,'utf8'), pem, sig);
}

function apsReceiptId(receipt) {
  return sha256Text(`APS-RECEIPT-ID-V1\0${apsJcs(strip(receipt,'receipt_id','signatures'))}`);
}
function apsReceiptSigPayload(receipt, sig) {
  const descriptor = { signer:sig.signer, key_id:sig.key_id, alg:sig.alg };
  return `APS-RECEIPT-SIG-V1\0${apsJcs({receipt:strip(receipt,'signatures'), signer:descriptor})}`;
}
function verifyApsReceipt(receipt) {
  eq(receipt.profile,'aps-receipt-v1','APS receipt profile');
  eq(apsReceiptId(receipt), receipt.receipt_id, 'APS receipt_id');
  requireTrue(Array.isArray(receipt.signatures) && receipt.signatures.length > 0,'APS receipt signatures missing');
  for (const sig of receipt.signatures) {
    eq(sig.alg,'Ed25519','APS signature algorithm');
    const key = APS_KEYS[`${sig.signer}#${sig.key_id}`];
    requireTrue(key, `APS key not pinned for ${sig.signer}#${sig.key_id}`);
    requireTrue(verifyEdRaw(key, apsReceiptSigPayload(receipt,sig), sig.value), `APS signature invalid for ${sig.signer}`);
  }
  requireTrue(receipt.signatures.some(s=>s.signer===receipt.issuer),'APS issuer signature missing');
  return true;
}
function apsDelegationId(delegation) {
  const body = strip(delegation,'delegation_id','signature');
  return `sha256:${sha256Text(`APS-AUTHORITY-DELEGATION-ID-V1\0${apsJcs(body)}`)}`;
}
function verifyApsDelegation(delegation) {
  eq(apsDelegationId(delegation), delegation.delegation_id, 'APS delegation_id');
  const keyId = String(delegation.verification_method).split('#').at(-1);
  const key = APS_KEYS[`${delegation.issuer}#${keyId}`];
  requireTrue(key,'APS principal key is not independently pinned');
  const unsigned = strip(delegation,'signature');
  requireTrue(verifyEdRaw(key, `APS-AUTHORITY-DELEGATION-SIGNATURE-V1\0${apsJcs(unsigned)}`, delegation.signature), 'APS delegation signature invalid');
  return true;
}
function normalizeDecisionOutput(v) {
  const out = structuredClone(v);
  out.constraints = [...new Set(out.constraints.map(x=>x.normalize('NFC')))].sort();
  return out;
}
function apsDecisionRef(receipt, evidence) {
  const tagged=(tag,v)=>sha256Text(`${tag}\0${apsJcs(v)}`);
  const input={
    profile:'aps-decision-ref-v1',
    action_ref:receipt.action_ref,
    authority_state_ref:tagged('APS-DECISION-AUTHORITY-V1',evidence.authority_state),
    policy_ref:tagged('APS-DECISION-POLICY-V1',evidence.policy_input),
    context_ref:tagged('APS-DECISION-CONTEXT-V1',evidence.decision_context),
    decision_output_ref:tagged('APS-DECISION-OUTPUT-V1',normalizeDecisionOutput(evidence.decision_output))
  };
  return sha256Text(`APS-DECISION-REF-V1\0${apsJcs(input)}`);
}
function parseManifest(manifestPath) {
  const raw=bytes(manifestPath);
  eq(sha256Bytes(raw), APS_MANIFEST_SHA256, 'APS manifest file hash');
  const lines=raw.toString('utf8').trim().split(/\r?\n/);
  return lines.map(line=>{
    const m=line.match(/^([0-9a-f]{64})\s+\*?(.+)$/);
    if(!m) fail(`bad APS manifest line: ${line}`);
    return {sha256:m[1], relative_path:m[2]};
  });
}
function verifyManifest(manifestPath, root) {
  const entries=parseManifest(manifestPath);
  for (const entry of entries) {
    const p=path.join(root,entry.relative_path);
    eq(sha256Bytes(bytes(p)),entry.sha256,`APS manifest member ${entry.relative_path}`);
  }
  return entries.length;
}
function verifyApsOwnerCopyBinding(ownerRoot, copiedRoot) {
  const ownerManifest=path.join(ownerRoot,'MANIFEST.sha256');
  const copiedManifest=path.join(copiedRoot,'MANIFEST.sha256');
  const ownerEntries=parseManifest(ownerManifest);
  const copiedEntries=parseManifest(copiedManifest);
  requireTrue(bytes(ownerManifest).equals(bytes(copiedManifest)),'APS copied manifest differs byte-for-byte from owner manifest');
  eq(copiedEntries.length,ownerEntries.length,'APS owner/copy manifest entry count');
  for (const entry of ownerEntries) {
    const ownerPath=path.join(ownerRoot,entry.relative_path);
    const copiedPath=path.join(copiedRoot,entry.relative_path);
    requireTrue(fs.existsSync(copiedPath),`APS copied fixture missing owner file ${entry.relative_path}`);
    const ownerBytes=bytes(ownerPath);
    const copiedBytes=bytes(copiedPath);
    eq(sha256Bytes(ownerBytes),entry.sha256,`APS owner fixture hash ${entry.relative_path}`);
    requireTrue(ownerBytes.equals(copiedBytes),`APS copied fixture differs from owner bytes: ${entry.relative_path}`);
  }
  return {
    owner_commit:APS_COMMIT,
    manifest_sha256:APS_MANIFEST_SHA256,
    compared_files:ownerEntries.length,
    byte_identical:true
  };
}

function verifyApsCase(caseDir) {
  const caseDoc=json(path.join(caseDir,'case.json'));
  const intent=json(path.join(caseDir,'action-intent-receipt.json'));
  const decision=json(path.join(caseDir,'policy-decision-receipt.json'));
  const evidence=json(path.join(caseDir,'decision-evidence.json'));
  verifyApsReceipt(intent); verifyApsReceipt(decision);
  eq(decision.prev,intent.receipt_id,'APS prev binding');
  eq(decision.action_ref,intent.action_ref,'APS action_ref continuity');
  eq(decision.delegation_ref,intent.delegation_ref,'APS delegation_ref continuity');
  eq(decision.result.profile,'aps-core-decision-output-v1','APS decision result profile');
  requireTrue(JSON.stringify(decision.result)===JSON.stringify(evidence.decision_output),'APS carried decision output differs from evidence');
  eq(apsDecisionRef(decision,evidence),decision.decision_ref,'APS decision_ref');
  const chain=evidence.authority_state?.selected_chain;
  requireTrue(Array.isArray(chain)&&chain.length===1,'bounded pilot expects one APS delegation');
  verifyApsDelegation(chain[0]);
  eq(chain[0].delegation_id,decision.delegation_ref,'APS decision delegation_ref');
  const validUntil=evidence.decision_output.valid_until;
  const temporal = typeof validUntil==='string' && Date.parse(validUntil)>Date.parse(decision.issued_at);
  const current = typeof validUntil==='string' && REFERENCE_MS<Date.parse(validUntil);
  return { caseDoc,intent,decision,evidence,temporal,current,delegation:chain[0] };
}

function verifyPriorSealHashes(r) {
  const auth=r.authorizationEvidence.authorization;
  const intent=auth.intent;
  eq(hashJson(strip(intent,'intentHash')), intent.intentHash, 'PriorSeal intentHash');
  eq(auth.intentHash,intent.intentHash,'PriorSeal authorization intentHash');
  const authId=`auth_${hashJson(strip(auth,'authorizationId','signature')).slice(0,32)}`;
  eq(authId,auth.authorizationId,'PriorSeal authorizationId');
  eq(hashJson(auth),r.authorizationHash,'PriorSeal authorizationHash');
  const acc=r.authorizationEvidence.acceptance;
  const entryHash=hashJson({sequence:acc.sequence,authorizationHash:acc.authorizationHash,acceptedAt:acc.acceptedAt,previousEntryHash:acc.previousEntryHash});
  eq(entryHash,acc.entryHash,'PriorSeal acceptance entryHash');
  eq(acc.authorizationHash,r.authorizationHash,'PriorSeal acceptance authorizationHash');
  eq(acc.intentHash,r.intentHash,'PriorSeal acceptance intentHash');
  eq(hashJson(r.execution),r.executionHash,'PriorSeal executionHash');
  const receiptId=`psr_${hashJson({schema:'priorseal.execution-receipt.v3',authorizationHash:r.authorizationHash,executionHash:r.executionHash,issuer:r.issuer,keyId:r.keyId}).slice(0,32)}`;
  eq(receiptId,r.receiptId,'PriorSeal receiptId');
}
function verifyPriorSealSignatures(r) {
  const auth=r.authorizationEvidence.authorization;
  const types={ PriorSealAuthorization:[
    {name:'intentHash',type:'bytes32'}, {name:'principalType',type:'string'}, {name:'principalId',type:'string'},
    {name:'principalAccount',type:'address'}, {name:'authorizerType',type:'string'}, {name:'authorizer',type:'address'},
    {name:'agentId',type:'string'}, {name:'executor',type:'address'}, {name:'issuedAt',type:'uint256'},
    {name:'notBefore',type:'uint256'}, {name:'expiresAt',type:'uint256'}, {name:'authorizationNonce',type:'bytes32'},
    {name:'maxUses',type:'uint256'}, {name:'audience',type:'string'}, {name:'policyHash',type:'bytes32'}
  ]};
  const domain={name:'PriorSeal',version:'2',chainId:Number(auth.intent.chainId)};
  const value={
    intentHash:`0x${auth.intentHash}`, principalType:auth.principal.type, principalId:auth.principal.id,
    principalAccount:auth.principal.account, authorizerType:auth.authorizer.type, authorizer:auth.authorizer.address,
    agentId:auth.delegate.agentId, executor:auth.delegate.executor, issuedAt:BigInt(auth.issuedAt), notBefore:BigInt(auth.notBefore),
    expiresAt:BigInt(auth.expiresAt), authorizationNonce:auth.authorizationNonce, maxUses:BigInt(auth.maxUses), audience:auth.audience, policyHash:auth.policyHash
  };
  const recovered=verifyTypedData(domain,types,value,auth.signature).toLowerCase();
  eq(recovered,auth.authorizer.address.toLowerCase(),'PriorSeal EIP-712 signer');
  eq(auth.authorizer.address.toLowerCase(),auth.principal.account.toLowerCase(),'PriorSeal principal account binding');
  const acc=r.authorizationEvidence.acceptance;
  eq(acc.issuer,PRIORSEAL_ISSUER,'PriorSeal acceptance issuer'); eq(acc.keyId,PRIORSEAL_KEY_ID,'PriorSeal acceptance key id');
  requireTrue(verifyEdPem(PRIORSEAL_PUBLIC_KEY_PEM,priorsealCanonical(strip(acc,'signature')),acc.signature),'PriorSeal acceptance signature invalid');
  eq(r.issuer,PRIORSEAL_ISSUER,'PriorSeal receipt issuer'); eq(r.keyId,PRIORSEAL_KEY_ID,'PriorSeal receipt key id');
  requireTrue(verifyEdPem(PRIORSEAL_PUBLIC_KEY_PEM,priorsealCanonical(strip(r,'signature')),r.signature),'PriorSeal receipt signature invalid');
}
function verifyPriorSealReceipt(r, aps) {
  verifyPriorSealHashes(r); verifyPriorSealSignatures(r);
  const auth=r.authorizationEvidence.authorization;
  requireTrue(auth.notBefore<=r.issuedAt && r.issuedAt<auth.expiresAt,'PriorSeal authorization not current at receipt issuance');
  eq(auth.audience,'priorseal','PriorSeal audience');
  const cc=auth.intent.contextCommitments.filter(x=>x.namespace==='aps.decision-ref.v1'&&x.algorithm==='sha256');
  requireTrue(cc.length===1,'PriorSeal must carry exactly one APS decision_ref commitment');
  eq(cc[0].digest,`0x${aps.decision.decision_ref}`,'PriorSeal APS decision_ref commitment');
  const requested=aps.evidence.policy_input.requested_call;
  eq(String(auth.intent.chainId),String(requested.chain_id),'exact call chainId');
  eq(auth.intent.callTarget.toLowerCase(),requested.to.toLowerCase(),'exact call target');
  eq(auth.intent.transactionValue,String(requested.value_wei),'exact call authorized value vs APS requested call');
  const observed=r.execution;
  const exactMatch = String(observed.chainId)===String(auth.intent.chainId)
    && observed.target.toLowerCase()===auth.intent.callTarget.toLowerCase()
    && observed.calldataHash.toLowerCase()===auth.intent.calldataHash.toLowerCase()
    && String(observed.nativeValue)===String(auth.intent.transactionValue);
  const cap=BigInt(aps.delegation.authority.spend.per_action);
  const withinCap=BigInt(observed.nativeValue)<=cap;
  return {exactMatch,withinCap,cap:cap.toString(),authorizedValue:String(auth.intent.transactionValue),observedValue:String(observed.nativeValue)};
}

function run({apsOwnerRoot,apsRoot,priorsealRoot}) {
  const sourceBinding=verifyApsOwnerCopyBinding(apsOwnerRoot,apsRoot);
  const manifestCount=verifyManifest(path.join(apsRoot,'MANIFEST.sha256'),apsRoot);
  const permit=verifyApsCase(path.join(apsRoot,'cases','permit'));
  const expired=verifyApsCase(path.join(apsRoot,'cases','expired'));
  const deny=verifyApsCase(path.join(apsRoot,'cases','deny'));
  const positivePath=path.join(priorsealRoot,'priorseal-inputs','payment-within-limit.json');
  const negativePath=path.join(priorsealRoot,'priorseal-inputs','payment-over-limit.json');
  const reportPath=path.join(priorsealRoot,'PAYMENT-LIMIT-REPORT.json');
  eq(sha256Bytes(bytes(positivePath)),POSITIVE_SHA256,'positive fixture digest');
  eq(sha256Bytes(bytes(negativePath)),OVER_LIMIT_SHA256,'over-limit fixture digest');
  eq(sha256Bytes(bytes(reportPath)),REPORT_SHA256,'producer report digest');
  const positive=json(positivePath), negative=json(negativePath);
  const pos=verifyPriorSealReceipt(positive,permit), neg=verifyPriorSealReceipt(negative,permit);

  const claims=[
    claim('aps.manifest.pinned',CLAIM.ESTABLISHED,[`sha256:${APS_MANIFEST_SHA256}`],null,`${manifestCount} manifest members rehashed`),
    claim('composition.aps_owner_fixture_copy.byte_identical',CLAIM.ESTABLISHED,[`aps_commit:${APS_COMMIT}`,`sha256:${APS_MANIFEST_SHA256}`,`files:${sourceBinding.compared_files}`],null,'PriorSeal copied APS manifest members are byte-for-byte identical to the owner-repository fixture set at the pinned APS commit'),
    claim('aps.permit.receipts.authentic',CLAIM.ESTABLISHED,[permit.intent.receipt_id,permit.decision.receipt_id]),
    claim('aps.permit.delegation.authentic',CLAIM.ESTABLISHED,[permit.delegation.delegation_id]),
    claim('aps.permit.decision_ref.bound',CLAIM.ESTABLISHED,[permit.decision.decision_ref]),
    claim('aps.permit.temporal_validity_at_reference',permit.current?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[REFERENCE_TIME]),
    claim('aps.expired.temporal_validity_at_reference',expired.current?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[REFERENCE_TIME]),
    claim('aps.deny.decision_verdict',deny.decision.result.verdict==='deny'?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[deny.decision.receipt_id]),
    claim('priorseal.principal_eip712_authorization.authentic',CLAIM.ESTABLISHED,[positive.authorizationHash]),
    claim('priorseal.issuer_acceptance.authentic',CLAIM.ESTABLISHED,[positive.authorizationEvidence.acceptance.entryHash]),
    claim('priorseal.execution_receipt.positive.authentic',CLAIM.ESTABLISHED,[`sha256:${POSITIVE_SHA256}`]),
    claim('priorseal.execution_receipt.over_limit.authentic',CLAIM.ESTABLISHED,[`sha256:${OVER_LIMIT_SHA256}`]),
    claim('composition.aps_decision_to_priorseal_authorization.bound',CLAIM.ESTABLISHED,[permit.decision.decision_ref,positive.authorizationHash]),
    claim('positive.observation.exact_call_agreement',pos.exactMatch?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[`observed=${pos.observedValue}`,`authorized=${pos.authorizedValue}`]),
    claim('positive.observation.aps_cap_compliance',pos.withinCap?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[`observed=${pos.observedValue}`,`cap=${pos.cap}`]),
    claim('over_limit.observation.exact_call_agreement',neg.exactMatch?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[`observed=${neg.observedValue}`,`authorized=${neg.authorizedValue}`]),
    claim('over_limit.observation.aps_cap_compliance',neg.withinCap?CLAIM.ESTABLISHED:CLAIM.CONTRADICTED,[`observed=${neg.observedValue}`,`cap=${neg.cap}`]),
    claim('live_chain.execution_occurred',CLAIM.NOT_ESTABLISHED,[], 'fixtures declare observationSource=fixture; no independent post-dispatch chain observation was supplied'),
    claim('aps.decision.single_use',CLAIM.NOT_ESTABLISHED,[], 'receipt verification does not consume decision_ref or establish durable single use'),
    claim('aps.live_currency_enforcement',CLAIM.NOT_ESTABLISHED,[], 'fixture-local EVM mapping and synthetic spend state do not establish live currency enforcement'),
    claim('observation.independent_external_witness',CLAIM.NOT_ESTABLISHED,[], 'both payment observations are producer fixtures'),
    claim('production.adoption',CLAIM.NOT_ESTABLISHED,[], 'bounded public interoperability fixture is not evidence of production deployment or endorsement')
  ];

  const adequacy={
    status:'NOT_RUN_PENDING_DISCRIMINATING_FIXTURES_AND_MAINTAINER_CONSENT',
    excluded_from_formal_result:true,
    reason:'Mutation/corpus adequacy is outside the formal result until the listed authenticity and binding mutations have discriminating fixtures and maintainers separately consent to that stage.',
    planned_targeted_mutations:[
      {id:'remove-cap-comparison',claim:'over_limit.observation.aps_cap_compliance',pinned_discriminator:true},
      {id:'ignore-observation-mismatch',claim:'over_limit.observation.exact_call_agreement',pinned_discriminator:true},
      {id:'remove-reference-time-expiry',claim:'aps.expired.temporal_validity_at_reference',pinned_discriminator:true},
      {id:'deny-as-permit',claim:'aps.deny.decision_verdict',pinned_discriminator:true},
      {id:'remove-signature-verification',claim:'artifact.authenticity',pinned_discriminator:false,classification:'CORPUS_DISCRIMINATION_LIMIT'},
      {id:'accept-wrong-key',claim:'artifact.authenticity',pinned_discriminator:false,classification:'CORPUS_DISCRIMINATION_LIMIT'},
      {id:'accept-altered-authorization',claim:'priorseal.principal_eip712_authorization.authentic',pinned_discriminator:false,classification:'CORPUS_DISCRIMINATION_LIMIT'},
      {id:'remove-decision-ref-binding',claim:'composition.aps_decision_to_priorseal_authorization.bound',pinned_discriminator:false,classification:'CORPUS_DISCRIMINATION_LIMIT'}
    ]
  };

  return {
    profile:PROFILE,
    generated_at:new Date().toISOString(),
    mode:'independent-public-artifact-assurance',
    implementation:{name:'Frequency APS x PriorSeal thin adapter',version:'0.1.1',producer_verifier_code_imported:false,generic_crypto_dependencies:['Node.js crypto','ethers verifyTypedData']},
    pins:{aps_commit:APS_COMMIT,aps_owner_fixture_binding:sourceBinding,priorseal_commit:PRIORSEAL_COMMIT,reference_time:REFERENCE_TIME,aps_manifest_sha256:APS_MANIFEST_SHA256,positive_fixture_sha256:POSITIVE_SHA256,over_limit_fixture_sha256:OVER_LIMIT_SHA256,producer_report_sha256:REPORT_SHA256},
    trust:{aps_public_keys:Object.entries(APS_KEYS).map(([id,key])=>({id,sha256:sha256Bytes(Buffer.from(key,'hex'))})),priorseal_issuer:PRIORSEAL_ISSUER,priorseal_key_id:PRIORSEAL_KEY_ID,trust_source:'adapter-local pins; artifact-adjacent keys are not trust anchors'},
    claims, adequacy,
    summary:{established:claims.filter(x=>x.result===CLAIM.ESTABLISHED).length,contradicted:claims.filter(x=>x.result===CLAIM.CONTRADICTED).length,not_established:claims.filter(x=>x.result===CLAIM.NOT_ESTABLISHED).length},
    disclosure_boundary:{public_contract:['input pins','trust-key identifiers/digests','claim IDs','evidence references','bounded results','claim ceilings','adequacy plan'],not_disclosed:['Frequency internal reasoning graph','private heuristics','repair ranking','internal orchestration','private assurance controls']}
  };
}

function selftest() {
  const sample={z:1,a:{y:'x',b:true},arr:[3,2,1]};
  eq(priorsealCanonical(sample),'{"a":{"b":true,"y":"x"},"arr":[3,2,1],"z":1}','canonical serializer');
  return {ok:true};
}

const args=process.argv.slice(2);
if(args.includes('--selftest')) { console.log(JSON.stringify(selftest(),null,2)); process.exit(0); }
let apsOwnerRoot, apsRoot, priorsealRoot, out;
for(let i=0;i<args.length;i++){
  if(args[i]==='--aps-owner') apsOwnerRoot=args[++i];
  else if(args[i]==='--aps') apsRoot=args[++i];
  else if(args[i]==='--priorseal') priorsealRoot=args[++i];
  else if(args[i]==='--out') out=args[++i];
}
if(!apsOwnerRoot||!apsRoot||!priorsealRoot){
  console.error('usage: node verify.mjs --aps-owner <owner-aps-fixture-root> --aps <copied-aps-inputs> --priorseal <aps-priorseal-decision-binding-v1> [--out report.json]');
  process.exit(2);
}
try {
  const report=run({apsOwnerRoot:path.resolve(apsOwnerRoot),apsRoot:path.resolve(apsRoot),priorsealRoot:path.resolve(priorsealRoot)});
  const rendered=JSON.stringify(report,null,2)+'\n';
  if(out) fs.writeFileSync(out,rendered,{mode:0o600}); else process.stdout.write(rendered);
} catch (error) {
  console.error(`Frequency assurance run failed closed: ${error?.stack||error}`);
  process.exit(1);
}
