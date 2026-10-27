# Independent Probity synthetic replay — 2026-10-27

## Source and environment

- Upstream `probityai/probity`, branch `main`, source `f756419417f21bbd953d5dcdd64e0b880fb61a2b`.
- Isolated Python venv `/tmp/fed193-probity-venv` on Ubuntu VPS; checkout-runner declared package installed editable with its dependencies and pytest.
- Command from `examples/checkout-runner`: `python -m pytest -q tests/test_sandbox_executor.py tests/test_sandbox_signer.py` using the isolated venv.
- Observed: **58 passed in 1.47s** (local replay, exit 0). No provider network calls or real money.

## Compatibility boundary

At source revision cited above, `sandbox_executor.py:241` checks `typed_equal(pic.get("arguments"), record["arguments"])`; test fixtures assemble a synthetic PIC object containing `arguments` and `args_digest`. Federation proposal review-2026-10-23 section 4 describes a closed PIC result with `args_digest` but no `arguments`. These fixtures validate the implementation's own stand-in protocol only and do not demonstrate consumption of native closed PIC producer output. Independent cryptographic authority, hosted door semantics, original signed PIC verification, and external Default Settlement reading remain NOT_ESTABLISHED.

## DDC decision

PASS: independently reproduced synthetic signer/executor tests and source traceability.
HOLD: native closed PIC result and retained hash-bound proposal correlation, authenticated admission, stateful admission proof, per-attempt dispatch-time manifest source, connected producer run and independent downstream reader.

This evidence does not expand Frequency's accepted bounded v1 verifier or assume PIC, executor or admission ownership. The work is review-only and must not be cited as full Federation conformance.
