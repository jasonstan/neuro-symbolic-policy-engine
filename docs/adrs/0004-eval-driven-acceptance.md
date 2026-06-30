# ADR-0004 — Eval-driven acceptance, on top of pytest

- **Status:** Accepted
- **Date:** 2026-06-30

## Context

Until this point, the acceptance bar for milestone work was *pytest green*. That gate
protects **correctness** — types hold, the fact rail is deterministic, the typed-claim
contract survives at the boundary — but it doesn't protect the **thesis** the demo exists to
make legible. A demo whose only gate is "code runs" can pass while quietly drifting away
from its rhetorical point as features land.

`evals/BRIEF.md` (introduced in this change) names what the demo claims (six claims, C1–C6,
each with a falsifier) and what it explicitly does not (the "where this stops" list,
including the trajectory-composition known-failure). Without an executable counterpart, the
brief would degrade to aspirational documentation.

## Decision

Ship an **eval suite** as a first-class artifact, on top of `tests/`:

- Three tiers: **behavioral** (claim demonstrations), **adversarial** (claim falsifiers),
  **known-failure** (documented architectural limits, surfaced on purpose).
- Each eval names the claim in `BRIEF.md` it advances (or `out_of_scope` for documented
  limits).
- A scorecard (`uv run python -m evals.run_evals`) groups results by claim, with `PENDING`
  for evals gated on future milestones and `XFAIL` for known-failures.
- A milestone is accepted when:
  1. `uv run pytest` is green (correctness),
  2. behavioral evals for the milestone's claims pass, and
  3. adversarial evals are *extended* wherever the milestone introduces new surface.

Tests in `tests/` keep their role; the eval suite layers above, not replaces.

## Claim → eval mapping (at the time of this ADR)

| Claim | Eval | Tier | Status |
|---|---|---|---|
| C1 Disaggregation | `behavioral/b01_clean_allow.yaml` | behavioral | PASS |
| C1 Disaggregation | `behavioral/b02_fact_violation_dual_role.yaml` | behavioral | PASS |
| C2 Boundary integrity | `adversarial/a02_prompt_injection_in_content.py` | adversarial | PASS |
| C3 Fact authority | `adversarial/a01_confident_wrong_vs_fact.yaml` | adversarial | PASS |
| C4 Policy-bound action | `behavioral/b03_per_clause_binding.py` | behavioral | PASS |
| C5 Auditability | `behavioral/b04_trace_shape.py` | behavioral | PASS |
| C6 Honest uncertainty | `adversarial/a03_ambiguous_judgment.yaml` | adversarial | PENDING (M3) |
| (documented limit) | `adversarial/a04_trajectory_composition.py` | known-failure | XFAIL |

## Consequences

- **Every clause or feature must name the claim it advances.** A change that serves no claim
  in the brief surfaces that gap before building — work should not advance the artifact
  without advancing its thesis.
- **The scorecard is the milestone-review surface.** Maintainers review the scorecard (and
  the brief) before declaring a milestone done, not raw test output.
- **The acceptance bar travels with the project.** A future contributor can read
  `BRIEF.md`, run `evals/run_evals.py`, and tell what the demo claims and where it stops in
  60 seconds.
- **Known-failures must remain documented.** If a known-failure eval starts passing
  (`XPASS`), CI fails until the cause is investigated — either embrace the new behavior
  (move the eval to a real claim, remove from known-failures) or explain it (the
  architecture changed, the brief needs updating).

## Out of scope

- **Live-API evals.** The eval suite runs offline and deterministically via `FakeLLM`. A
  future `pytest -m live` lane can shape-check the real `messages.parse` call, but the
  value-claim suite stays scripted.
- **Coverage maximization.** The brief's claims are a small fixed set; evals encode them.
  Adding evals because we can — without naming a claim — is the failure mode this ADR
  exists to prevent.
