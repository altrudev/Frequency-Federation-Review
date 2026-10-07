# Validation contract

The public proposal is intended to be mechanically reviewable without access to Frequency-Dev.

A conforming Attribution Receipt v0.1 must:

- remain status PROPOSAL;
- bind its body with a sha256 receipt_id;
- identify at least one project artifact, role, evidence reference, and attestation;
- require verification evidence when an attestation is marked VERIFIED;
- keep economic.value, payment.entitlement, causal.importance, and external.execution.occurred at NOT_ESTABLISHED;
- reject unrecognized nested fields, which prevents adding economic/payment or customer fields through the schema.

A conforming Status Registry v0.1 must:

- remain status PROPOSAL;
- keep listing and technical participation distinct from active participation;
- require explicit opt-in evidence for ACTIVE_PARTICIPANT;
- require owner confirmation for project-owned entries;
- keep decisions non-retroactive;
- require explicit operator, support, and component-agreement records before a commercial-delivery entry may be ACTIVE;
- reject extra nested fields, preventing embedded revenue-allocation or customer information;
- preserve the semantic constants that the registry is not a source of authority and does not define an economic formula.

These schemas are proposal contracts. Passing them does not itself verify a signature, prove execution, establish completeness, create membership, or create a payment right.
