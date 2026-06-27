"""Typed-claim contract: the judgment rail returns a well-typed claim, even when the model is
wrong. The schema constrains form, not truth — see ADR-0002 and CLAUDE.md."""

import pytest

from nspk import evaluate
from nspk.judgments.suitability import SuitabilityClaim
from nspk.rails.llm_client import FakeLLM


def _judgment_step(decision, clause_id: str):
    return next(
        s for s in decision.trace.steps if s.kind == "judgment" and s.clause_id == clause_id
    )


def test_claim_field_is_an_enum_value(case_clean_allow, policy, fake_llm_suitable_true):
    decision = evaluate(case=case_clean_allow, policy=policy, llm=fake_llm_suitable_true)
    js = _judgment_step(decision, "C3_suitability")
    assert js.claim["suitable"] in {"true", "false", "unclear"}


def test_confidence_is_a_float_not_self_reported(
    case_clean_allow, policy, fake_llm_suitable_true
):
    decision = evaluate(case=case_clean_allow, policy=policy, llm=fake_llm_suitable_true)
    js = _judgment_step(decision, "C3_suitability")
    assert isinstance(js.confidence, float)
    assert 0.0 <= js.confidence <= 1.0
    # M1 stub — replaced by EnsembleAgreement in M3.
    assert js.confidence == 1.0


def test_well_typed_even_when_model_is_wrong(
    case_dual_role_violation, policy, fake_llm_wrong_but_conformant
):
    # FakeLLM emits suitable='true' regardless of the input. The contract: the trace's claim
    # field is still one of the enum literals, and the binding still resolves cleanly.
    decision = evaluate(
        case=case_dual_role_violation, policy=policy, llm=fake_llm_wrong_but_conformant
    )
    js = _judgment_step(decision, "C3_suitability")
    assert js.claim["suitable"] == "true"
    assert js.action.value == "allow"


def test_engine_rejects_judgment_clauses_without_an_llm(case_clean_allow, policy):
    with pytest.raises(ValueError, match="LLMClient"):
        evaluate(case=case_clean_allow, policy=policy, llm=None)


def test_fake_llm_records_calls(case_clean_allow, policy):
    fake = FakeLLM(response=SuitabilityClaim(suitable="unclear", rationale="r"))
    evaluate(case=case_clean_allow, policy=policy, llm=fake)
    assert len(fake.calls) == 1
    assert fake.calls[0]["schema"] == "SuitabilityClaim"


def test_unclear_claim_routes_to_review(case_clean_allow, policy):
    fake = FakeLLM(
        response=SuitabilityClaim(suitable="unclear", rationale="ambiguous")
    )
    decision = evaluate(case=case_clean_allow, policy=policy, llm=fake)
    js = _judgment_step(decision, "C3_suitability")
    # Per the policy YAML, {suitable: unclear} → route_to_review.
    assert js.action.value == "route_to_review"
    assert decision.verdict.value == "route_to_review"
