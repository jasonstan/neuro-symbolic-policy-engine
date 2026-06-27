# neuro-symbolic-policy-kernel

> **Research demo, not production.** A small, legible artifact showing one way to govern AI-agent
> actions without sending everything to a single LLM judge.

## What this is

A policy decomposes into two kinds of clause, each routed to the mechanism that fits it, then
combined in one symbolic engine that is the only thing that renders a verdict.

- **Deterministic fact rail** — clauses that are facts about recorded state (same party did
  two things; amount exceeded a limit; action preceded its authorization). Rule-evaluated over
  structured state. No model. Exact every time.
- **Judgment rail** — clauses that need interpretation (was the recommendation suitable for the
  client's risk profile; did the agent exploit a client's distress). An LLM evaluates them, but its
  job is deliberately small: under constrained decoding it must emit a **typed claim** — a value
  from a fixed enum plus a confidence — never free prose, never the final verdict.
- **Symbolic engine** — consumes facts and typed claims, applies the named policy clauses, and
  renders one verdict from `{allow, log, route_to_review, block, escalate_for_signoff}`. Every
  decision emits a full **evidence trace**: which clauses fired, on which inputs, fact vs claim,
  the claim's confidence, and the threshold that gated it.

## Why typed claims

Typing controls the *form* of the model's output so the claim is consumable by the engine — it
does **not** make the claim *true*. The architectural payoff: the LLM is reduced to a typed
labeller, the verdict is determined by composable policy rules over those labels (plus facts),
and the trace shows exactly how the verdict was reached.

Two commitments make this load-bearing:

1. **Per-clause action binding.** What a typed claim triggers is policy config, not engine code.
   The same `suitable=false` claim can `block` under one clause and `route_to_review` under
   another.
2. **Confidence is independently sourced.** Never the model's self-report (a model is least
   calibrated exactly when out of its depth). This POC derives confidence from ensemble
   agreement; the interface accepts swap-in estimators (distance-from-traffic, trained
   error-predictors) later.

## Status

Milestone M1 (thin vertical slice) — current. One fact clause (C1: advisor dual-role) and one
judgment clause (C3: suitability) are wired end-to-end through the engine and the CLI prints a
real verdict and a real evidence trace. See [the milestone plan](#milestones) below.

## Run (once M1 lands)

```bash
uv sync
cp .env.example .env  # only needed for the --llm=anthropic mode
uv run pytest         # offline; uses FakeLLM
uv run python examples/run_examples.py examples/cases/01_clean_allow.yaml
```

## Architecture

See [`docs/architecture.md`](docs/architecture.md) (TODO) and the ADRs in
[`docs/adrs/`](docs/adrs/).

## Milestones

- [x] **M0** — scaffolding, license, ADRs, importability test
- [x] **M1** — thin vertical slice (1 fact clause + 1 judgment clause → verdict + trace, CLI)
- [ ] **M2** — complete the 4-clause seed policy + all 4 example cases
- [ ] **M3** — ensemble-agreement confidence estimator
- [ ] **M4** — web UI that shows the decision assembling
- [ ] **M5** — polish: architecture diagram, README pass

## Backlog (intentionally not built)

The synthetic wealth-management scenario is the hero artifact. Two future extensions build on
the adapter and library seams above; **neither is in this codebase**:

- **EnterpriseOps-Gym real-data track** — map captured gym episodes through the `CaseAdapter`
  interface to show the engine generalizes beyond the synthetic scenario.
- **DoomArena engine-as-defense eval** — the policy engine as a defense under a configured
  threat model, measuring residual attack success rate.

These are documented seams, not dependencies. See ADR-0003 for the scoping rationale.

## License

MIT. See [LICENSE](LICENSE).
