"""The symbolic engine.

Consumes a `Case` + `Policy` (and an `LLMClient` when judgment clauses are present), evaluates
each clause to an action via its bindings, and merges actions into one final verdict by
severity. Returns a `Decision` containing the verdict and a full evidence trace.

Engine semantics (see ADR-0001):
- Each clause produces one action via first-match binding lookup. If no binding matches, the
  clause contributes `allow`.
- The merge step selects the most severe action across clauses:
      block > escalate_for_signoff > route_to_review > log > allow
- The trace records each clause evaluation independently, plus the merge step.
"""

from typing import Any

from nspk.rails.fact_rail import run_fact_evaluator
from nspk.rails.judgment_rail import run_judgment_clause
from nspk.rails.llm_client import LLMClient
from nspk.types import (
    Binding,
    Case,
    Decision,
    FactClause,
    FactStep,
    JudgmentClause,
    JudgmentStep,
    MergeStep,
    Policy,
    Trace,
    TraceStep,
    Verdict,
)

_SEVERITY_RANK: dict[Verdict, int] = {
    Verdict.ALLOW: 0,
    Verdict.LOG: 1,
    Verdict.ROUTE_TO_REVIEW: 2,
    Verdict.ESCALATE_FOR_SIGNOFF: 3,
    Verdict.BLOCK: 4,
}


def evaluate(case: Case, policy: Policy, llm: LLMClient | None = None) -> Decision:
    steps: list[TraceStep] = []
    contributed: list[Verdict] = []

    for clause in policy.clauses:
        if isinstance(clause, FactClause):
            step: TraceStep = _evaluate_fact_clause(clause, case)
        elif isinstance(clause, JudgmentClause):
            if llm is None:
                raise ValueError(
                    f"Policy {policy.name!r} has judgment clause {clause.id!r} but no "
                    "LLMClient was provided to evaluate(). Pass an LLMClient (use FakeLLM in "
                    "tests, AnthropicLLM in production)."
                )
            step = _evaluate_judgment_clause(clause, case, llm)
        else:
            raise TypeError(f"Unknown clause type: {type(clause).__name__}")
        steps.append(step)
        contributed.append(step.action)

    final = _merge_by_severity(contributed)
    steps.append(MergeStep(contributed_actions=contributed, selected=final))

    return Decision(
        verdict=final,
        trace=Trace(
            case_id=case.id,
            policy_name=policy.name,
            steps=steps,
            final_verdict=final,
        ),
    )


def _evaluate_fact_clause(clause: FactClause, case: Case) -> FactStep:
    result = run_fact_evaluator(clause.evaluator, case)
    binding, action = _match_binding(clause.bindings, {"violated": result.violated})
    return FactStep(
        clause_id=clause.id,
        description=clause.description,
        evaluator=clause.evaluator,
        result=result,
        binding_matched=binding.model_dump(mode="json") if binding else None,
        action=action,
    )


def _evaluate_judgment_clause(
    clause: JudgmentClause, case: Case, llm: LLMClient
) -> JudgmentStep:
    claim = run_judgment_clause(clause, case, llm)
    context: dict[str, Any] = {**claim.payload, "confidence": claim.confidence}
    binding, action = _match_binding(clause.bindings, context)
    return JudgmentStep(
        clause_id=clause.id,
        description=clause.description,
        schema_name=claim.schema_name,
        claim=claim.payload,
        confidence=claim.confidence,
        samples=claim.samples,
        binding_matched=binding.model_dump(mode="json") if binding else None,
        action=action,
    )


def _match_binding(
    bindings: list[Binding], context: dict[str, Any]
) -> tuple[Binding | None, Verdict]:
    for binding in bindings:
        if _guard_matches(binding.when, context):
            return binding, binding.action
    return None, Verdict.ALLOW


def _guard_matches(when: dict[str, Any], context: dict[str, Any]) -> bool:
    for key, expected in when.items():
        if key.endswith("_gte"):
            base = key[:-4]
            val = context.get(base)
            if val is None or val < expected:
                return False
        elif key.endswith("_lt"):
            base = key[:-3]
            val = context.get(base)
            if val is None or val >= expected:
                return False
        else:
            if context.get(key) != expected:
                return False
    return True


def _merge_by_severity(actions: list[Verdict]) -> Verdict:
    if not actions:
        return Verdict.ALLOW
    return max(actions, key=_SEVERITY_RANK.__getitem__)
