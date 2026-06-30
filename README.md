# neuro-symbolic-policy-kernel

> **Research demo, not production.** A small, legible artifact showing one way to govern
> AI-agent actions without sending everything to a single LLM judge.

## What this demonstrates

Six claims (full statements + falsifiers in [`evals/BRIEF.md`](evals/BRIEF.md); each one is
asserted by a corresponding eval — see [`evals/run_evals.py`](evals/run_evals.py) for the
current scorecard):

| # | Claim |
|---|---|
| **C1** | **Disaggregation.** A policy splits into *fact clauses* (deterministic over recorded state) and *judgment clauses* (LLM-emitted typed claims), recombined by the engine into one verdict. |
| **C2** | **Boundary integrity.** The LLM emits only a *typed claim*; the verdict is a pure function of facts + claims + confidence + policy, computed by the engine. Prompt injection in unstructured content cannot change the verdict beyond what the typed claim alone justifies. |
| **C3** | **Fact authority.** A hard fact violation is never overridden by a permissive judgment, however confident. |
| **C4** | **Policy-bound action.** What a typed claim triggers lives in policy YAML, not engine code. The same claim can `block` under one clause and `route_to_review` under another. |
| **C5** | **Auditability.** Every verdict ships an evidence trace — clauses fired, inputs, fact vs claim, confidence, gating threshold, merge step — readable by someone who didn't write the code. |
| **C6** | **Honest uncertainty.** *(M3.)* Confidence is independently sourced (ensemble agreement), never the model's self-report; ambiguous judgments route to review. |

And one explicit known-failure, on purpose: **cross-decision composition** (two
individually-permitted actions that together violate intent) — the engine is per-decision and
cannot catch this. See [`evals/adversarial/a04_trajectory_composition.py`](evals/adversarial/a04_trajectory_composition.py).

## What this is

A policy decomposes into two kinds of clause, each routed to the mechanism that fits it, then
combined in one symbolic engine that is the only thing that renders a verdict.

- **Deterministic fact rail** — clauses that are facts about recorded state (same party did
  two things; amount exceeded a limit; action preceded its authorization). Rule-evaluated
  over structured state. No model. Exact every time.
- **Judgment rail** — clauses that need interpretation (was the recommendation suitable for
  the client's risk profile; did the agent exploit a client's distress). An LLM evaluates
  them, but its job is deliberately small: under constrained decoding it must emit a **typed
  claim** — a value from a fixed enum plus a confidence — never free prose, never the final
  verdict.
- **Symbolic engine** — consumes facts and typed claims, applies the named policy clauses,
  and renders one verdict from `{allow, log, route_to_review, block, escalate_for_signoff}`.
  Every decision emits a full **evidence trace**: which clauses fired, on which inputs, fact
  vs claim, the claim's confidence, and the threshold that gated it.

## Why typed claims

Typing controls the *form* of the model's output so the claim is consumable by the engine —
it does **not** make the claim *true*. The architectural payoff: the LLM is reduced to a
typed labeller, the verdict is determined by composable policy rules over those labels (plus
facts), and the trace shows exactly how the verdict was reached.

Two commitments make this load-bearing:

1. **Per-clause action binding.** Same `suitable=false` claim can `block` under one clause
   and `route_to_review` under another. Asserted by eval C4.
2. **Confidence is independently sourced.** Never the model's self-report. This POC derives
   confidence from ensemble agreement (M3); the interface accepts swap-in estimators
   (distance-from-traffic, trained error-predictors) later. Asserted by eval C6.

## Status

**Eval-driven acceptance is live** (foundation commit, 2026-06-30). The brief, the evals,
and the scorecard are the milestone-review surface — see [ADR-0004](docs/adrs/0004-eval-driven-acceptance.md).
M1 (vertical slice) shipped; M2 (complete seed policy) is next under the new bar.

## Run

```bash
uv sync
cp .env.example .env                          # only needed for --llm=anthropic
uv run pytest                                 # offline; correctness
uv run python -m evals.run_evals              # offline; thesis integrity (scorecard)
uv run python examples/run_examples.py examples/cases/01_clean_allow.yaml
```

## Architecture

ADRs in [`docs/adrs/`](docs/adrs/):

- [ADR-0001](docs/adrs/0001-symbolic-engine-choice.md) — embedded Datalog-style evaluator over OPA/Rego
- [ADR-0002](docs/adrs/0002-judgment-rail-constrained-decoding.md) — Anthropic Structured Outputs for the judgment rail
- [ADR-0003](docs/adrs/0003-scope-synthetic-hero-scenario.md) — synthetic hero scenario; gym + DoomArena as backlog seams
- [ADR-0004](docs/adrs/0004-eval-driven-acceptance.md) — eval-driven acceptance, on top of pytest

## Evals

Three tiers in [`evals/`](evals/) — each eval mapped to a claim in the brief:

- **Behavioral** — cases-with-expected-decisions that demonstrate a claim holds.
- **Adversarial** — cases designed to *break* a claim. If they pass, the claim survived.
- **Known-failures** — cases the architecture cannot handle, on purpose, with the reason
  recorded inline. Surface as `XFAIL`; flip to `XPASS` (and CI-fail) if the architecture
  ever starts catching them.

Sample scorecard (foundation commit):

```
══════════════════════════════════════════════════════════════════════════════
 NSPK eval scorecard  ·  2026-06-30  ·  policy: wealth_management_v1
══════════════════════════════════════════════════════════════════════════════

 C1  Disaggregation                                                  2/2 PASS
 C2  Boundary integrity                                              1/1 PASS
 C3  Fact authority                                                  1/1 PASS
 C4  Policy-bound action                                             1/1 PASS
 C5  Auditability                                                    1/1 PASS
 C6  Honest uncertainty                                          PENDING (M3)

 Known-failures (on purpose):
   a04_trajectory_composition                                       XFAIL
     ↳ Engine is per-decision; cross-decision composition is documented backlog.
──────────────────────────────────────────────────────────────────────────────
 Totals:  6 pass · 1 pending · 1 known-failure
══════════════════════════════════════════════════════════════════════════════
```

See [`evals/README.md`](evals/README.md) for tier conventions and the full claim→eval table.

## Milestones

Each milestone names the claims it advances and the evals that gate it. A milestone is
*done* when `pytest` is green, the relevant evals pass, and the adversarial set has been
extended to probe new surface.

| Milestone | Status | Claims advanced | Eval gates |
|---|---|---|---|
| M0 — scaffolding, ADRs, importability gate | ✅ | — | importability test |
| M1 — thin vertical slice (1 fact + 1 judgment → verdict + trace) | ✅ | C1, C5 (mechanism) | (lifted into behavioral evals at foundation) |
| **Foundation — intent brief + evals + acceptance bar** | ✅ (this commit) | encodes all claims | scorecard renders; load-bearing trio (C2, C3, trajectory known-failure) all green |
| M2 — complete the 4-clause seed policy + cases | next | C1, C3, C4, C5 (extended) | C2 settlement-window + C4 no-exploitation evals; new adversarial probes for each new judgment surface |
| M3 — ensemble-agreement confidence estimator | future | C6 (full) | `a03_ambiguous_judgment` flips PENDING → PASS |
| M4 — web UI that shows the decision assembling | future | C5 (human-readable rendering) | trace renders in browser; `b04_trace_shape` still passes |
| M5 — polish (architecture diagram, README pass) | future | — | final scorecard committed in README |

## Backlog (intentionally not built)

The synthetic wealth-management scenario is the hero artifact. Two future extensions build on
the adapter and library seams; **neither is in this codebase**:

- **EnterpriseOps-Gym real-data track** — map captured gym episodes through the `CaseAdapter`
  interface to show the engine generalizes beyond the synthetic scenario.
- **DoomArena engine-as-defense eval** — the policy engine as a defense under a configured
  threat model, measuring residual attack success rate.

A third is on-architecture but explicitly out of reach for the per-decision engine:

- **Cross-decision / trajectory composition.** Two individually-permitted actions that
  jointly violate intent. Surfaced as a `known-failure` eval, not hidden. See
  [`evals/adversarial/a04_trajectory_composition.py`](evals/adversarial/a04_trajectory_composition.py).

See [ADR-0003](docs/adrs/0003-scope-synthetic-hero-scenario.md) for the scoping rationale and
[`evals/BRIEF.md`](evals/BRIEF.md) §"Where this stops" for the full boundary list.

## License

MIT. See [LICENSE](LICENSE).
