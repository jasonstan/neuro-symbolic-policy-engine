# neuro-symbolic-policy-engine

A working demo of the layer that decides what an AI agent is allowed to *do*, action
by action, under an organization's own policy, and records why.

## The larger problem

When an organization puts an AI agent into a real workflow, two kinds of safety are
reasonably well understood: keeping the model from producing harmful content, and
securing the infrastructure it runs on. A third layer sits between them and is rarely
owned as a product: deciding what the agent is permitted to do. Which actions clear,
which are blocked, which go to a human, under whose authority, and with what record
afterward.

Owning that layer lets an organization state its own conduct policy, enforce it on
every agent action with the model kept out of the decision, and produce an audit trail
an internal reviewer or a regulator can check. The layer is unclaimed, and it is prone
to becoming theater: a governance story that holds until a confident-but-wrong model
judgment overrides a hard fact.

This repository is a small first slice of that surface, not the whole of it. The path
from here (policy ingestion, coverage testing, configurable resolution, and breadth
across domains) is in `docs/BACKLOG.md`.

## What this MVP proves

Before it is worth building that layer, one assumption has to hold: that a conduct
policy can be split into hard facts and bounded model judgments and recombined so that
the model never issues the verdict and a confident-but-wrong judgment never overrides a
hard fact, with an auditable trace as output. If the split does not hold, the layer is
not worth building. This MVP tests that assumption on one scenario and states where it
stops.

It is a product artifact, not a product. The acceptance criteria are written as
runnable evals with a POC built against them, so agreement on what "done" means is
executable rather than a document to review. The artifact does two things: it de-risks
the core assumption, and it is the alignment surface for scoping the work the backlog
defers.

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
- **A decision walked end to end:** `docs/case-study.md`. Auditability shown on a real
  case, not asserted.
- **How "done" gets decided:** `docs/adrs/0004-eval-driven-acceptance.md`.
- **Where it stops:** the limitations section below, and the known-failure evals.
- **Deferred work:** `docs/BACKLOG.md`. Roadmap index, not a re-statement of scope.

## How acceptance works

A milestone is not done when the code runs. It is done when the evals for the claims
it advances pass. The acceptance criteria (`BRIEF.md`) were written before the code
that satisfies them, and every change has to name the claim it advances, or flag that
it advances none, before being built. The scorecard, grouped by claim, is what you
read to decide whether a milestone is real. This keeps new work tied to the claims in
the brief rather than letting the codebase grow past them.

## Limitations

- **No trajectory control.** Two actions that are each permitted but together violate
  intent are out of scope for this flat, per-decision engine. This ships as a
  known-failure eval rather than being hidden. Trajectory-level control is on the
  backlog.
- **Policy is authored, not ingested.** The engine starts from the typed-clause YAML.
  Producing that YAML from a prose corporate policy, splitting it into clauses,
  labeling each fact or judgment, and designing the bindings, is out of scope. See
  `docs/BACKLOG.md`.
- **The evals prove invariants, not coverage.** The suite is a small fixed set of
  claim-integrity checks, not a behavioral benchmark over many policies and inputs.
  Broad coverage is deferred. See `docs/BACKLOG.md`.
- **The merge is fixed, not configurable.** Only the per-clause bindings are
  policy-editable. Cross-clause resolution and fact authority are engine logic, by
  design. Configurable resolution is backlogged, with fact authority intended to stay
  locked.
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
