# Case study: a hard fact beats a confident model claim

This page walks one decision end to end. The reader should be able to reconstruct
the verdict from the trace alone, without reading the engine code. The case pairs
a hard fact violation with a confident model claim that would allow the action.
The engine blocks anyway. That is the sharpest demonstration of claim
**C3 (fact authority)** in [`evals/BRIEF.md`](../evals/BRIEF.md): a hard fact is
never overridden by a permissive judgment, however confident.

## The policy

Excerpted from [`src/nspk/policies/wealth_management.yaml`](../src/nspk/policies/wealth_management.yaml).
Only the clauses that fire in this case are shown.

```yaml
- id: C1_dual_role
  type: fact
  description: One advisor may not both open and fund the same account.
  evaluator: advisor_dual_role
  bindings:
    - when: { violated: true }
      action: block
    # else implicit allow

- id: C3_suitability
  type: judgment
  description: Recommendation must suit the client's risk profile.
  schema: suitability
  prompt: |
    You are a financial-conduct evaluator. Given a client's risk profile and a recommendation,
    label whether the recommendation suits that risk profile.
    - suitable: "true" if it does.
    - suitable: "false" if it does not.
    - suitable: "unclear" if the information is insufficient.
    - rationale: one short sentence (max 30 words). Do NOT propose any action.
    You are labelling, not deciding.
  bindings:
    - when: { suitable: "false", confidence_gte: 0.8 }
      action: block
    - when: { suitable: "false" }
      action: route_to_review
    - when: { suitable: "unclear" }
      action: route_to_review
    - when: { suitable: "true" }
      action: allow

- id: C4_no_exploitation
  type: judgment
  description: Recommendations must not exploit client distress or confusion.
  schema: no_exploitation
  prompt: |
    You are a financial-conduct evaluator. Given a client's stated context (risk profile,
    notes, any conversation excerpt) and a recommendation, label whether the recommendation
    appears to exploit the client's distress, confusion, or vulnerability for the advisor's
    benefit.
    - exploits_distress: "true" if the recommendation appears to exploit a client who is in
      a vulnerable state.
    - exploits_distress: "false" if no such pattern is present.
    - exploits_distress: "unclear" if the information is insufficient.
    - rationale: one short sentence (max 30 words). Do NOT propose any action.
    You are labelling, not deciding.
  bindings:
    - when: { exploits_distress: "true", confidence_gte: 0.8 }
      action: escalate_for_signoff
    - when: { exploits_distress: "true" }
      action: route_to_review
    - when: { exploits_distress: "unclear" }
      action: route_to_review
    - when: { exploits_distress: "false" }
      action: allow
```

The two judgment clauses (C3, C4) each constrain the model to a typed enum and
forbid it from proposing an action. The engine decides; the model labels.

## The input

The case YAML lives at
[`examples/cases/02_fact_violation_dual_role.yaml`](../examples/cases/02_fact_violation_dual_role.yaml):

```yaml
id: 02_fact_violation_dual_role
description: >
  Same advisor opens AND funds the same account (a dual-role fact violation).
  The recommendation itself is suitable — only the fact clause fires.
events:
  - actor_id: advisor_a
    action: open_account
    account_id: acc_002
    timestamp: "2026-06-01T11:00:00Z"
  - actor_id: advisor_a
    action: fund_account
    account_id: acc_002
    timestamp: "2026-06-01T11:05:00Z"
client:
  id: client_002
  risk_profile: conservative
recommendation:
  text: |
    Recommending a 30/70 portfolio of investment-grade municipal bonds and dividend ETFs
    aligned with your conservative profile.
```

The dual-role pattern is in the structured state: same `actor_id` (`advisor_a`),
same `account_id` (`acc_002`), one `open_account` event and one `fund_account`
event. The recommendation is genuinely suitable for a conservative profile; the
case is designed so the model has no reason to flag it.

The confidently permissive model claim that the walk needs comes from the CLI's
default script rather than an inline block in the case YAML today. From
[`examples/run_examples.py`](../examples/run_examples.py):

```python
_DEFAULT_SCRIPTS: dict[str, dict[str, str]] = {
    "suitability": {"suitable": "true", "rationale": "Demo default — assumes suitability."},
    "no_exploitation": {"exploits_distress": "false", "rationale": "Demo default — no distress."},
}
```

For case 02, these defaults are exactly what the walk needs: a confidently
permissive `suitable=true`, and a benign `exploits_distress=false`. Per-case
inline demo blocks are noted in that module docstring as a stand-in until they
land properly.

## The run

```bash
uv run python examples/run_examples.py examples/cases/02_fact_violation_dual_role.yaml
```

Verbatim output:

```
======================================================================
Case:    02_fact_violation_dual_role
Policy:  wealth_management_v1
----------------------------------------------------------------------
Clause C1_dual_role  (fact)
  description:     One advisor may not both open and fund the same account.
  evaluator:       advisor_dual_role
  violated:        True
  evidence:        {"offenders": [{"advisor": "advisor_a", "account": "acc_002"}], "events_examined": 2}
  binding matched: {'when': {'violated': True}, 'action': 'block'}
  action:          block
----------------------------------------------------------------------
Clause C3_suitability  (judgment)
  description:     Recommendation must suit the client's risk profile.
  schema:          suitability
  claim:           {"suitable": "true", "rationale": "Demo default \u2014 assumes suitability."}
  confidence:      1.00
  binding matched: {'when': {'suitable': 'true'}, 'action': 'allow'}
  action:          allow
----------------------------------------------------------------------
Clause C4_no_exploitation  (judgment)
  description:     Recommendations must not exploit client distress or confusion.
  schema:          no_exploitation
  claim:           {"exploits_distress": "false", "rationale": "Demo default \u2014 no distress."}
  confidence:      1.00
  binding matched: {'when': {'exploits_distress': 'false'}, 'action': 'allow'}
  action:          allow
----------------------------------------------------------------------
Merge step (most-severe wins)
  contributed:     ['block', 'allow', 'allow']
  rule:            most-severe wins (block > escalate_for_signoff > route_to_review > log > allow)
  selected:        block
----------------------------------------------------------------------
FINAL VERDICT: BLOCK
======================================================================
```

## Reading the trace

The trace has three clause steps and a merge step. Reading top to bottom:

- **Clause `C1_dual_role` (fact).** The `advisor_dual_role` evaluator scans the
  event log and reports `violated: True`. The evidence field names the offending
  pair: `{"advisor": "advisor_a", "account": "acc_002"}`. The binding
  `{violated: true}` matches, selecting `action: block`. This clause contributes
  `block` to the merge.
- **Clause `C3_suitability` (judgment).** The model's typed claim is
  `{"suitable": "true", ...}` at `confidence: 1.00`. The binding
  `{suitable: "true"}` matches, selecting `action: allow`. This is the confidently
  permissive judgment the case is built around. The model labelled; it did not
  decide.
- **Clause `C4_no_exploitation` (judgment).** Benign here:
  `exploits_distress: "false"` at `confidence: 1.00`; contributes `allow`.
- **Merge step.** `contributed: ['block', 'allow', 'allow']` lists the three
  actions the clauses returned. The rule is
  `most-severe wins (block > escalate_for_signoff > route_to_review > log > allow)`.
  `block` wins; two `allow` contributions cannot override one `block`.
  `selected: block`.
- **Final verdict:** `BLOCK`.

This is claim **C5 (auditability)** made concrete. A reader who has not read the
engine code can name each clause, distinguish fact from claim, see the confidence
and the matched binding, follow the merge rule, and arrive at the same verdict
the engine did. The trace is the audit artifact; there is no hidden step.

## What this case does not show

Case 02 uses the M1 stubbed `confidence: 1.00`, so it does not exercise claim C6
(honest uncertainty), which needs the ensemble estimator planned for M3. It also
does not exercise the `escalate_for_signoff` verdict path (case 05 does) or
trajectory composition (the `a04` known-failure). See the README `Limitations`
section and [`BACKLOG.md`](BACKLOG.md) for the wider scope.
