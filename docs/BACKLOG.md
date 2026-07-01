# Backlog

Index of deferred work for `neuro-symbolic-policy-engine`. Two kinds of entry:

- **Candidates for inclusion.** Items surfaced in review that are not yet planned. Each
  states what it is, which claim (C1-C6) it advances or which capability it enables, its
  trigger or precondition, and whether it would need its own ADR when picked up. Items
  marked as enabling or infrastructure are upstream of the claim set rather than tied to
  a single claim.
- **Documented deferrals.** Items already recorded elsewhere (BRIEF's "Where this stops,"
  ADRs, milestone plan) and indexed here so the roadmap has one entry point. Pointers
  only, not restatements.

Scope-of-claims lives in `evals/BRIEF.md`. Acceptance discipline lives in
`docs/adrs/0004-eval-driven-acceptance.md` and `CLAUDE.md`. This file is a roadmap index,
not a re-statement of either.

## Candidate for inclusion (surfaced in review)

### 1. Policy ingestion and disaggregation

- **What.** A step that turns a prose corporate policy into the typed-clause YAML: split
  into clauses, label each fact or judgment, design the control logic and the
  claim-to-verdict bindings. Currently assumed to already exist; the YAML is its output.
- **Enables.** The pipeline for policies the project did not hand-author. Upstream of
  C1-C6, not one of them.
- **Trigger.** When the project moves past a single hand-authored hero policy.
- **Notes.** A design-time, human-reviewed trust surface, distinct from the runtime
  boundary. LLM-assisted authoring is consistent with "the model never decides at
  runtime" as long as the YAML stays reviewed and audited.
- **ADR when picked up.** Yes. Authoring trust model. Also introduces the
  expected-disaggregation eval category in item 2.

### 2. Behavioral coverage benchmark

- **What.** Many policies, a wide input distribution, and expected verdicts across them,
  run continuously and scored. Includes a category the repo has none of yet:
  expected-disaggregation scoring (given a prose policy, was it split correctly).
- **Distinct from.** The current claim-integrity evals, which are a small fixed set
  proving the architecture's invariants. This is coverage and regression, not thesis
  integrity.
- **Enables.** Safely shipping items 1 and 4, both of which introduce variation that
  needs broad coverage to stay safe.
- **Trigger.** Prerequisite for items 1 or 4.
- **Notes.** Keep separate from the claim-integrity suite (different directory and
  purpose). ADR-0004 deliberately scoped the current suite to claims, not coverage.
  This is the other half, for the next phase.
- **ADR when picked up.** Optional. Directory and scoring conventions can extend
  ADR-0004 rather than take their own file, unless a scoring methodology emerges that
  is worth its own record.

### 3. Fact-rail delegation to Rego or embedded Datalog

- **What.** Move the deterministic fact rail onto a mature declarative engine while
  keeping the bespoke judgment-and-merge layer on top and the YAML as the authoring
  interface.
- **Advances.** Maintainability and expressiveness of the fact rail. Does not change
  the claims.
- **Trigger.** When fact-clause count rises, clauses conflict or need priorities, or
  relational logic across entities appears. Not before. While the engine is flat and
  per-decision this buys nothing (Datalog's recursion is unused; see the `a04`
  known-failure).
- **Notes.** Revisit the engine-choice ADR (the bespoke-now decision) when the trigger
  hits. This item would update or supersede ADR-0001.
- **ADR when picked up.** Yes. Update or supersede ADR-0001.

### 4. Editable and weightable cross-clause merge

- **What.** Expose configurable cross-clause conflict resolution: clause priorities,
  weighting of soft judgment signals, which verdict wins when clauses disagree.
- **Advances.** C4 territory, extended from within-clause bindings to cross-clause
  resolution.
- **Constraint.** Fact authority stays locked, or is behind elevated sign-off with its
  own audit record. A customer must not be able to weight away the rule that a hard
  fact beats a confident-but-wrong judgment; that would rebuild the governance theater
  the engine refuses.
- **Trigger.** When a second scenario or a real customer needs conflict resolution the
  fixed precedence does not cover.
- **Depends on.** Item 2 (coverage benchmark) for regression safety.
- **ADR when picked up.** Yes. The locked-versus-configurable boundary is
  safety-critical.

### 5. Case-study page with a real trace printout

- **What.** A `docs/case-study.md` page pairing the pipeline diagram with one real
  end-to-end run: the YAML excerpt, the decision request, and the literal evidence
  trace the engine emits.
- **Advances.** C5 (auditability), as a demonstrated human-readable artifact rather
  than an asserted one. Also the repo's legibility to a non-author reviewer.
- **Trigger.** Near-term and small. Hero case likely case 02 (fact authority beats
  confident judgment) or case 05 (escalate).
- **Notes.** Docs artifact, not engine work.
- **ADR when picked up.** No.

## Documented deferrals (recorded elsewhere; indexed here)

- **Independent confidence estimator (`EnsembleAgreement`).** Planned for M3. Unblocks
  C6 and case 04. Tracked in the milestone plan and the CLAUDE.md typed-claim contract
  note.
- **Trajectory / cross-decision composition control.** The `a04` XFAIL and BRIEF
  "Where this stops." Advancing it would move `a04` from known-failure to a real claim.
- **Breadth beyond the single wealth-management scenario.** Asserted via the adapter
  and library seams, not demonstrated. See BRIEF "Where this stops."
- **EnterpriseOps-Gym adapter.** Documented backlog seam in the CLAUDE.md scope
  boundary; also the bridge to a separate research project. Do not import into the
  core.
