# Federation technical glossary

This glossary translates project-specific Frequency and A1 federation terminology into commonly used engineering and standards language. The mapping describes *similar functions*, not conformance to a named standard. Normative compliance requires a separately scoped test.

| Frequency / federation term | Established technical terminology | Scope and boundary |
| --- | --- | --- |
| Frequency | Adaptive orchestration and assurance system | System architecture; not a standardized protocol |
| DDC / problem graph | Typed dependency graph / workflow state machine | Represents dependencies and state transitions; not automatically a W3C PROV graph |
| Transformation | Auditable change transaction / workflow execution record | Captures intent, authorization, action, observation, and verification |
| EDRG / release gate | Evidence-based acceptance gate / deployment control | Internal acceptance process, not a standards certification |
| Federation | Decentralized interoperability arrangement | Independent projects retain separate governance and trust domains |
| Federation edge | Cross-system integration relationship / interface contract | Edge existence does not prove interoperability or production adoption |
| Federation node | Participating project or independently administered system | Node identity and claims require owner confirmation |
| Sovereignty | Administrative and cryptographic authority boundary | A participant controls its own claims, keys, and consent |
| APS | Authorization and delegation evidence producer | Product name, not a general authorization standard |
| PriorSeal | Transaction authorization and execution-receipt producer | Product name, not a general payment standard |
| A1 | Bounded interoperability verification stage | Pinned fixture-level assessment, not production validation |
| Review capsule | Reproducible test package / evidence bundle | Public subset of artifacts for independent inspection |
| Verification Offer | Test plan and reproducibility contract | Declares assertions, inputs, procedures, ceilings, and consent rules |
| Reproduction Record | Test execution record / provenance evidence | Captures actual observed run and artifact digests |
| Producer consent | Explicit authorization from artifact/system owner | Distinct from operator execution and publication rights |
| Pre-run gate | Authorization precondition / admission control | Checks retained approval and exact input identity |
| Readiness gate | Preflight validation | READY does not imply the formal test has run |
| Pinned commit | Immutable source revision identifier | Git commit SHA; tag names alone are insufficient |
| Artifact digest | Content integrity checksum | SHA-256 validates bytes, not semantic correctness |
| Trust pins | Explicit public-key trust anchors | Here restricted to fixture test keys, not production identity |
| decision_ref | Cryptographic reference to an authorization decision | Exact binding is implementation-specific; not a universal token format |
| Permit receipt | Signed authorization evidence | Signature validity alone does not establish enforcement |
| Delegation | Delegated authority / capability constraint | Must distinguish granted authority from exercised authority |
| EIP-712 authorization | Ethereum typed structured-data signature | Signature verification does not prove on-chain execution |
| Execution receipt | Signed execution assertion or evidence artifact | Producer statement is not automatically independent observation |
| Observation | Recorded measurement or event evidence | Observation must not be conflated with intended effect |
| Exact-call agreement | Argument / transaction-intent binding check | Checks chain, target, calldata hash, and native value for this fixture |
| Spend cap | Transaction-level authorization constraint | Fixture comparison does not establish durable budget accounting |
| Negative control | Deliberately invalid or adversarial test case | Expected rejection or contradiction verifies discrimination |
| ESTABLISHED | Assertion supported within the declared evidence scope | Not a universal guarantee |
| CONTRADICTED | Assertion falsified by available test evidence | For A1, three negative controls must produce this disposition |
| NOT_ESTABLISHED | Insufficient evidence / unverified claim | Not equivalent to a negative finding |
| Claim ceiling | Maximum justified assurance level | Prevents promotion from fixture checks to live-system claims |
| Independent verifier | Separate reviewer / independent implementation | Independence requires scrutiny of control, authorship, and shared dependencies |
| Shared-record admission | Multi-party evidence acceptance / governance approval | Separate from execution and technical verification |
| Publication approval | Disclosure authorization / release approval | Separate from producer consent and shared-record admission |
| Single-use decision | Replay prevention / durable authorization consumption | Cannot be inferred from a signed receipt |
| Idempotent execution | Retry-safe execution of one logical operation | Different from one-time authorization admission |
| Live-chain execution | Actual network transaction and resulting state transition | Not established by synthetic fixture reports |
| Production adoption | Real-world deployment and operator acceptance | Not established by reproducible conformance fixtures |
| Provenance | Origin and processing lineage of artifacts | Related to W3C PROV concepts, without asserting PROV conformance |
| Content-addressed artifact | Object identified by cryptographic digest | Hashes authenticate content only relative to trusted reference |
| Evidence bundle | Test artifacts, metadata, logs, digests, and provenance | Must retain raw stdout/stderr, exit status, environment, and inputs |

## Normative references and boundaries

- **RFC 8785 (JCS)**: JSON canonicalization when explicitly used by a particular protocol; ordinary sorted-key JSON is not necessarily JCS.
- **RFC 8032 (Ed25519)**: signature algorithm used for the pinned fixture keys; cryptographic validity does not establish signer authority.
- **EIP-712**: typed structured-data signing for Ethereum-related authorization.
- **W3C PROV**: reference vocabulary for provenance concepts; Frequency records are not claimed to implement PROV without a mapping and validation.
- **NIST SP 800-53**: control-family vocabulary may inform evidence and change-control discussions; this glossary does not claim assessment or compliance.
- **Supply-chain provenance / reproducible builds**: analogous verification disciplines; a pinned test run is not proof of a reproducible build.

## A1 status and claim boundaries

The A1 offer declares 22 expected claim dispositions: 14 ESTABLISHED, 3 CONTRADICTED negative controls, and 5 NOT_ESTABLISHED. These are **expected** dispositions, not observed results until the formal procedure is executed and its captured output independently checked.

The five NOT_ESTABLISHED boundaries are live-chain execution, durable single-use decision consumption, live-currency enforcement, independent external observation, and production adoption.

A formal run requires the exact pinned sources and retained authorization of **both** APS and PriorSeal. A successful operator run is not automatically an independently approved federation record; publication requires separate authorization.

## Scope of rights

This glossary does not expand the permissions in `REVIEW-ONLY-NOTICE.md`, disclose Frequency's private implementation, or confer a license to use third-party artifacts beyond their own terms.
