# ADR-0001: Symbolic engine — embedded Datalog-style evaluator, not OPA/Rego

- **Status:** Accepted
- **Date:** 2026-06-26

## Context

The engine in this project is the only component that renders a verdict. It consumes facts
(from the deterministic rail) and typed claims (from the judgment rail), applies per-clause
action bindings from the policy, and produces one verdict plus a full **evidence trace**. The
trace is not a side effect: it is the artifact a reviewer reads to audit the decision. The
shape of that trace is the point of the demo.

## Options considered

1. **OPA / Rego (external binary).** Industry-standard policy-as-code with native decision logs
   and a mature ecosystem.
2. **Embedded Datalog-style evaluator (pure Python).** A small in-process evaluator we own
   end-to-end. Bespoke trace format.
3. **Pure Python rule functions, no formal engine.** Simplest. Loses the declarative policy and
   structured trace.

## Decision

Option **(2): embedded Datalog-style evaluator**.

## Why

- The demo's value rests on the **shape and inspectability of the evidence trace**. Owning the
  evaluator means we own the trace and can render every step in the web UI exactly as we want.
  OPA emits decision logs in *its* format and would require translating into our trace
  vocabulary anyway.
- Zero external runtime keeps the artifact a single `pip install` away — important for the
  "library-first" commitment in the project brief. No `opa` sidecar to manage, no language
  boundary inside the audit story.
- The clause logic we need is a flat evaluation: each clause has required facts and required
  claims (gated by a confidence threshold) that map to an action via per-clause bindings.
  This is well below what general Datalog can express; full fixpoint semantics, recursion, and
  negation-as-failure are unnecessary. We call the result "Datalog-style" because clauses are
  declarative rules over a fact base, not because we implement Datalog.

## What we give up

- OPA's familiarity to policy engineers, its ecosystem, and its battle-tested semantics. We
  mitigate by:
  - keeping the evaluator small (~hundreds of LOC), well-tested, and documenting its semantics
    here and in code;
  - structuring policies as declarative YAML so a future engine swap (including a future swap
    *to* OPA) requires no policy rewrite, just an adapter.

## Engine semantics (the evaluator's contract)

A **policy** is an ordered list of **clauses**. Each clause has:

- `id`, `description`, `type ∈ {fact, judgment}`
- one **input source**: a fact-evaluator name (fact clauses) or a typed-claim schema and prompt
  (judgment clauses)
- a **bindings** list: ordered guards `(condition → action)` where each guard tests the
  resulting fact or claim. The first matching guard contributes that clause's action; if none
  match, the clause contributes `allow`.

The engine merges clause-level actions into a final verdict using the **severity order**:

```
block > escalate_for_signoff > route_to_review > log > allow
```

The verdict is the most severe action contributed by any clause. The trace records each
clause's evaluation independently, plus the merge step that selected the final verdict.

## Out of scope

- Recursion, negation-as-failure semantics, fixpoint computation, rule chaining.
- Cross-clause constraints (only the merge step combines clauses, and it does so by severity
  alone).

If a future requirement needs more, revisit this ADR.
