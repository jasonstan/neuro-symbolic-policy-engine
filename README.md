# neuro-symbolic-policy-engine

A working demo of the layer that decides what an AI agent is allowed to *do*, action
by action, under an organization's own policy, and records why.

## What this is for

This is a product artifact, not a product. Its job is to align product, engineering,
and leadership quickly on four things: what the problem is, who has it, what a
good-enough solution has to do (the acceptance criteria), and whether a given
approach can meet them.

The acceptance criteria are written as runnable evals, with a POC built against them.
"Do we agree on what done means?" stops being a document people skim and becomes
something you run and watch pass or fail.

## The problem this is about

When an organization puts an AI agent into a real workflow, two kinds of safety are
reasonably well understood: keeping the model from producing harmful content, and
securing the infrastructure it runs on. A third layer sits between them and is rarely
owned as a product: deciding what the agent is actually permitted to do. Which
actions clear, which get blocked, which go to a human, under whose authority, with a
record a reviewer can read afterward.

That layer is a real, ownable surface. It is also the part most prone to becoming
theater: a governance story that sounds airtight but, under pressure, lets a
confident-but-wrong model judgment override a hard fact. This demo shows the surface
is concrete and testable, and is precise about where it stops.

## The idea in one sentence

A policy for governing an agent's actions can be split into typed deterministic facts
and typed bounded judgments, then recombined by a transparent engine into a single
auditable verdict, so the model never decides and a confident-but-wrong judgment
cannot override a hard fact.

The "neuro-symbolic" label refers to that split: a deterministic rule engine (the
symbolic side) consuming bounded LLM judgments (the neural side), with the engine,
never the model, making the call.

## Where to look first

- **What it claims, and what would prove each claim wrong:** `evals/BRIEF.md`. Six
  claims, each paired with the falsifier that would make a skeptic concede it is
  false.
- **Whether the claims hold right now:** the eval scorecard,
  `uv run python -m evals.run_evals`. This is the review surface, not raw test
  output.
- **How "done" gets decided:** `docs/adrs/0004-eval-driven-acceptance.md`.
- **Where it stops:** the limitations section below, and the known-failure evals.
- **Deferred work:** `docs/BACKLOG.md`. Roadmap index, not a re-statement of scope.

## How acceptance works

A milestone is not done when the code runs. It is done when the evals for the claims
it advances pass. The acceptance criteria (`BRIEF.md`) were written before the code
that satisfies them, and every change has to name the claim it advances, or flag that
it advances none, before being built. The scorecard, grouped by claim, is what you
read to decide whether a milestone is real. This keeps the demo from drifting away
from what it is meant to prove as features land.

## Limitations

- **No trajectory control.** Two actions that are each permitted but together violate
  intent are out of scope for this flat, per-decision engine. This ships as a
  known-failure eval rather than being hidden. Trajectory-level control is on the
  backlog.
- **Confidence is a POC mechanism,** not a calibrated estimate, with a clean swap-in
  point.
- **One scenario** (wealth-management conduct), not breadth. Generality is argued
  through the adapter seam, not demonstrated across domains.
- **Not legally authoritative.** The policy clauses are illustrative and do not
  encode current regulation.
- **A demo, not production.** No scale, latency, or hardening claims.

## How it was built

Built with an AI coding agent (Claude Code), directed from the written acceptance
criteria above rather than a feature list: thesis and falsifiers first, evals as the
bar, every change mapped to a claim.

## Repo map

```
.
├── evals/
│   ├── BRIEF.md                  intent brief — 6 claims, falsifiers, scope boundary
│   ├── run_evals.py              CLI; prints the scorecard grouped by claim
│   ├── _framework.py             EvalSpec, EvalResult, scripted FakeLLM, runners
│   ├── behavioral/               claim demonstrations under representative inputs
│   └── adversarial/              claim falsifiers + one known-failure (on purpose)
├── docs/adrs/                    architectural decision records (0001–0004)
├── src/nspk/                     the installable library (Python import name `nspk`)
│   ├── api.py                    evaluate(case, policy, llm) -> Decision
│   ├── types.py                  Case, Policy, Verdict, TypedClaim, Decision, Trace
│   ├── engine/                   the symbolic engine + severity merge + trace builder
│   ├── rails/                    fact_rail (rules) and judgment_rail (LLM client)
│   ├── judgments/                registered typed-claim Pydantic schemas
│   ├── adapters/                 CaseAdapter Protocol + synthetic YAML adapter
│   └── policies/                 bundled wealth-management policy YAML
├── examples/                     human-runnable cases for the CLI demo
├── tests/                        correctness gate (types, determinism, well-typedness)
├── README.md  CLAUDE.md  LICENSE  pyproject.toml
```

## Quick start

```bash
uv sync                                                # install Python + deps
uv run python -m evals.run_evals                       # scorecard — read this first
uv run pytest                                          # correctness tests
uv run python examples/run_examples.py examples/cases/01_clean_allow.yaml
```
