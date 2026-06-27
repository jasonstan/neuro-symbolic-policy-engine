# Working in this repo (CLAUDE.md)

This is a **research / portfolio demonstrator**, not production code. Optimize for clarity,
auditability, and a demo that makes the architecture legible. Do not optimize for scale.

## Quick start

```bash
uv sync                                       # install (uv fetches Python 3.11+ if needed)
cp .env.example .env && $EDITOR .env          # only required for --llm=anthropic
uv run pytest                                 # offline; uses FakeLLM
uv run python examples/run_examples.py examples/cases/01_clean_allow.yaml
uv run uvicorn demo.app:app --reload          # web demo (lands in M4)
```

## Architecture in one paragraph

A policy decomposes into **fact clauses** (rule over structured state) and **judgment clauses**
(LLM emits a *typed claim* — enum value + confidence — under constrained decoding). A small
**symbolic engine** consumes facts and typed claims and renders one **verdict** from
`{allow, log, route_to_review, block, escalate_for_signoff}`, emitting a full **evidence trace**.
The engine is the only component that decides; the LLM never emits the verdict.

## The typed-claim contract (load-bearing — do not break)

1. Every judgment clause has a Pydantic schema with **one enum-typed field** for the claim
   and an optional short string rationale.
2. The judgment rail uses Anthropic Structured Outputs (`client.messages.parse(...)`) — the
   claim is *always* well-typed by construction, including when the model is "wrong".
3. **The model never emits confidence.** Confidence comes from a `ConfidenceEstimator`
   (default: `EnsembleAgreement(N=5)`, lands in M3; M1 stubs to 1.0).
4. **The model never emits the final verdict.** Verdict is a function of facts, claims,
   confidence, and per-clause policy config — computed by the engine.
5. A clause's action binding (which verdict on which claim value at which confidence) is in
   the **policy YAML**, not in engine code.

If a change to this repo would break any of (1)–(5), stop and surface the trade-off in the PR
description before implementing.

## Conventions

- Python 3.11+, type hints everywhere, Pydantic v2 for all boundary types.
- `src/`-layout. Library code in `nspk/` has **no** web / FastAPI imports.
- `ruff` for lint + format.
- No comments unless the WHY is non-obvious (an invariant, a workaround, a citation).
- One commit = one logical change; commit messages explain the WHY.

## Scope boundary

- The synthetic wealth-management scenario is the hero artifact.
- EnterpriseOps-Gym and DoomArena are **documented backlog seams** (adapter and eval).
  Do not import them or pull them into the core.

## Testing conventions

- `tests/unit/test_fact_rail_determinism.py` — same inputs ⇒ byte-identical trace.
- `tests/unit/test_judgment_claim_well_typed.py` — uses `FakeLLM`. Asserts the typed claim
  conforms to the schema even when the fake model returns garbage. **Do not delete this test.**
- `tests/unit/test_engine_per_clause_binding.py` (M2) — same claim, different policies, different
  verdicts.
- Judgment-rail tests must use `FakeLLM` — no live network in `pytest`.
- A separate `pytest -m live` mark runs the real-API smoke test (one call, opt-in).

## When in doubt

If a refactor would make the engine harder to import as a library, or would let the model emit
a verdict, or would hard-code an action in engine code that should live in policy config —
push back. These are the demo's whole point.
