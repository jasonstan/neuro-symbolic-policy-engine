# ADR-0002: Judgment rail uses Anthropic Structured Outputs

- **Status:** Accepted
- **Date:** 2026-06-26

## Context

The judgment rail's role is deliberately small: for each judgment clause, the LLM must emit a
**typed claim** — a value from a fixed enum (e.g. `suitable ∈ {true, false, unclear}`) and a
short rationale. The model must never emit prose, confidence, or the final verdict.

For this to be a load-bearing contract we need the output to be *guaranteed* to conform to the
schema, even when the model would otherwise hedge or refuse.

## Options considered

1. **Anthropic Structured Outputs.** `client.messages.parse(model=..., output_format=Schema)`
   where `Schema` is a Pydantic model. Documented as the dedicated feature for "extract /
   classify / structure", with constrained decoding and guaranteed schema conformance.
2. **Strict tool use.** `tools=[...]` + `tool_choice={"type":"tool","name":"emit_claim"}` +
   `strict: true`. Same conformance guarantee; different ergonomics. Tool-use framing
   encourages the model to *decide whether* to call a tool — the wrong framing for "the model
   is a labeller".
3. **Raw JSON + regex / retry.** What teams do badly. Rejected — defeats the contract.

## Decision

Option **(1): Anthropic Structured Outputs** via the SDK's `messages.parse` helper with a
Pydantic schema per judgment clause.

## Why

- It is the documented, dedicated path for "extract or classify into a typed shape".
- It maps cleanly to the framing we want for the judgment rail: *the model labels, the engine
  decides*. Tool-use semantics imply agency the model should not have here.
- Pydantic schemas are already our boundary-type vocabulary, so the schema for each judgment
  clause is just a Pydantic model — no separate JSON-schema authoring.
- Constrained decoding guarantees we never have to write retry / parse-error logic for the
  typed claim itself. (Network errors and rate limits are a different matter and handled by
  the LLM client wrapper.)

## What we give up

- Anthropic's tool-use ecosystem for things like parallel calls and downstream tool routing —
  but we don't need any of that here.
- A small system-prompt token tax for the constrained-decoding grammar (per the docs).

## Important invariants this preserves

- **The schema constrains form, not truth.** A model that is confidently wrong will still emit
  a syntactically valid claim. We treat that as a feature: the *content* of the claim is the
  model's responsibility; *trusting* the claim is the engine's threshold-gating job.
- **The model never reports its own confidence.** Confidence is sourced independently — see
  the ensemble-agreement estimator (M3).

## Operational notes

- Default model: `claude-sonnet-4-6`. Overridable via `NSPK_JUDGMENT_MODEL`.
- Default ensemble size in M3 onward: `N = 5`. Each sample uses an independent call. Confidence
  is the modal class's share.
- All judgment-rail tests use a `FakeLLM` fixture — no live API calls in CI.
