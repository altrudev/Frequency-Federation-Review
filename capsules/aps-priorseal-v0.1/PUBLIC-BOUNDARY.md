# Public interoperability boundary

This adapter exposes only the minimum contract required to reproduce a bounded external-evidence evaluation:

- exact public input pins and hashes;
- byte-for-byte binding from the pinned APS owner fixture set to the copied APS bytes consumed from PriorSeal;
- independently configured public-key pins, with APS pins explicitly scoped to the published fixture test keys rather than production identity;
- external-profile canonicalization/signature/binding rules needed for the pinned case;
- machine-readable claim identifiers;
- evidence references;
- `ESTABLISHED`, `CONTRADICTED`, and `NOT_ESTABLISHED` outcomes;
- explicit claim ceilings; and
- a declared future corpus-adequacy plan.

It is not an API to Frequency's internal assurance engine. The following remain outside the interoperability contract and must not be inferred from this adapter: internal evidence-graph construction, reasoning heuristics, search strategy, repair generation/ranking, private controls, orchestration, model/provider selection, or unpublished assurance methods.

The adapter has no credentials, transport, remote code execution, or external side effects. It consumes caller-supplied local public artifacts and emits a local report. For file output it refuses an existing destination; the pinned runner additionally requires a fresh attempt directory and records the executed adapter commit/digest and exit status.
