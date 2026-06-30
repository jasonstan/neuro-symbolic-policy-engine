"""C4 — per-clause action binding lives in policy, not engine code.

The same SuitabilityClaim(suitable='false') yields BLOCK under one policy and
ROUTE_TO_REVIEW under another, simply by swapping the clause's bindings. If the binding-action
mapping leaked into engine code this eval would be impossible to write, or it would fail.
"""

from __future__ import annotations

from evals._framework import EvalResult, EvalStatus, build_scripted_fake_llm
from nspk import Verdict, evaluate
from nspk.types import Binding, Case, Client, JudgmentClause, Policy, Recommendation

ID = "b03_per_clause_binding"
CLAIM = "C4"
TIER = "behavioral"
DESCRIPTION = (
    "Same SuitabilityClaim(suitable='false') ⇒ BLOCK under one policy, ROUTE_TO_REVIEW under "
    "another. Bindings are policy config, not engine code."
)

_PROMPT_STUB = (
    "Label whether the recommendation suits the client's risk profile. Emit only a typed claim."
)


def _policy(action_for_false: Verdict) -> Policy:
    return Policy(
        name=f"policy_suit_false_is_{action_for_false.value}",
        clauses=[
            JudgmentClause(
                id="C3_suitability",
                description="Suitability under a single configurable binding.",
                schema_name="suitability",
                prompt=_PROMPT_STUB,
                bindings=[
                    Binding(when={"suitable": "false"}, action=action_for_false),
                    Binding(when={"suitable": "true"}, action=Verdict.ALLOW),
                ],
            )
        ],
    )


def _case() -> Case:
    return Case(
        id="b03_case",
        description="Boundary case exercising two bindings.",
        events=[],
        client=Client(id="client_b03", risk_profile="conservative"),
        recommendation=Recommendation(text="Recommending an aggressive growth portfolio."),
    )


def run() -> EvalResult:
    llm = build_scripted_fake_llm(
        {"suitability": {"suitable": "false", "rationale": "Aggressive growth misaligned with conservative profile."}}
    )

    d_block = evaluate(case=_case(), policy=_policy(Verdict.BLOCK), llm=llm)
    d_review = evaluate(case=_case(), policy=_policy(Verdict.ROUTE_TO_REVIEW), llm=llm)

    failures: list[str] = []
    if d_block.verdict != Verdict.BLOCK:
        failures.append(f"policy-A (suit_false→block): expected block, got {d_block.verdict.value}")
    if d_review.verdict != Verdict.ROUTE_TO_REVIEW:
        failures.append(
            f"policy-B (suit_false→route_to_review): expected route_to_review, "
            f"got {d_review.verdict.value}"
        )
    if d_block.verdict == d_review.verdict:
        failures.append(
            "same claim ⇒ same verdict across both policies; binding may be hard-coded in the engine"
        )

    base = dict(id=ID, claim=CLAIM, tier=TIER, description=DESCRIPTION)
    if failures:
        return EvalResult(**base, status=EvalStatus.FAIL, reason="; ".join(failures))
    return EvalResult(**base, status=EvalStatus.PASS)
