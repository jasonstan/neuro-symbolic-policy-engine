# ADR-0003: Scope — synthetic wealth-management scenario as the hero; EnterpriseOps-Gym and DoomArena as backlog seams

- **Status:** Accepted
- **Date:** 2026-06-26

## Context

This is a research / portfolio demonstrator. Its value is in showing the *architecture* — typed
claims, two-rail decomposition, transparent engine — not in volume of supported scenarios. We
have to choose what to build at high fidelity now, and what to leave as a seam.

## Decision

- The **hero artifact** is a synthetic wealth-management conduct policy with exactly four
  clauses: dual-role (fact), settlement window (fact), suitability (judgment), and
  no-exploitation-of-distress (judgment). Four example cases exercise the decision paths:
  clean allow, fact violation, confident judgment violation, low-confidence judgment routed to
  review.
- **EnterpriseOps-Gym** is treated as a future "real-data track" — captured episodes mapped
  through the `CaseAdapter` seam — but **no gym dependency is pulled into this repo**.
- **DoomArena** is treated as a future "engine-as-defense eval" — wiring the engine in as a
  defense, measuring residual attack success rate under a configured threat model — but **no
  DoomArena dependency is pulled into this repo**.

## Why

- One high-fidelity scenario with crisp cases makes the trace legible. A reviewer can read four
  cases and four traces and see exactly how the architecture behaves on each decision path.
  Three half-built scenarios obscure the point.
- The two backlog tracks are valuable as *evidence the architecture generalizes*. Building them
  now would either (a) couple the core to a specific gym/eval framework, defeating the
  library-first commitment, or (b) ship them in name only, which is worse than not shipping
  them. We get the strongest signal from having clean seams plus a written intent to extend.
- Recording the scoping rationale in an ADR is on-brand for an auditability artifact: the
  scope is itself a design choice, and design choices should be inspectable.

## What this commits us to

- The synthetic adapter (`SyntheticAdapter`) and the abstract `CaseAdapter` interface ship in
  the core library. The gym-adapter and DoomArena-defense seams live in the README backlog
  with one paragraph each describing the integration shape.
- The engine is packaged as a library (`pip install nspk`) so a future research codebase can
  consume it without forking this repo.

## What we explicitly say "not now" to

- Any code import of `enterpriseops-gym`, `doomarena`, or their data formats.
- Any policy clause whose evaluation needs gym- or DoomArena-specific state shape.
- Any "demo mode" that mocks gym or DoomArena traffic — better to leave the seam empty than to
  fake it.

If a clear need for a real second scenario emerges, revisit this ADR before extending.
