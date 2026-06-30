"""Fact rail determinism: same case ⇒ byte-identical trace.

The fact rail is the "no model" rail. Its outputs must be a pure function of the case. The
determinism test is also the regression test for any future change that accidentally
introduces dict-ordering, time, or randomness into the rail.
"""

from nspk import evaluate


def _run(case, policy, llm):
    return evaluate(case=case, policy=policy, llm=llm)


def test_dual_role_evaluation_is_byte_deterministic(
    case_dual_role_violation, policy, fake_llm_suitable_true
):
    d1 = _run(case_dual_role_violation, policy, fake_llm_suitable_true)
    d2 = _run(case_dual_role_violation, policy, fake_llm_suitable_true)
    assert d1.trace.model_dump_json() == d2.trace.model_dump_json()


def test_dual_role_detects_violation(
    case_dual_role_violation, policy, fake_llm_suitable_true
):
    decision = _run(case_dual_role_violation, policy, fake_llm_suitable_true)
    fact_step = next(
        s for s in decision.trace.steps if s.kind == "fact" and s.clause_id == "C1_dual_role"
    )
    assert fact_step.result.violated is True
    assert fact_step.action.value == "block"
    offenders = fact_step.result.evidence["offenders"]
    assert offenders == [{"advisor": "advisor_a", "account": "acc_test"}]


def test_dual_role_clears_clean_case(case_clean_allow, policy, fake_llm_suitable_true):
    decision = _run(case_clean_allow, policy, fake_llm_suitable_true)
    fact_step = next(
        s for s in decision.trace.steps if s.kind == "fact" and s.clause_id == "C1_dual_role"
    )
    assert fact_step.result.violated is False
    assert fact_step.action.value == "allow"


def test_block_wins_over_allow_in_merge(
    case_dual_role_violation, policy, fake_llm_suitable_true
):
    # FakeLLM scripts suitable=true (C3 → allow) and exploits_distress=false (C4 → allow).
    # C1 contributes block. Merge picks block as the most severe.
    decision = _run(case_dual_role_violation, policy, fake_llm_suitable_true)
    assert decision.verdict.value == "block"
    merge = next(s for s in decision.trace.steps if s.kind == "merge")
    assert [v.value for v in merge.contributed_actions] == ["block", "allow", "allow"]
    assert merge.selected.value == "block"


def test_clean_case_yields_allow(case_clean_allow, policy, fake_llm_suitable_true):
    decision = _run(case_clean_allow, policy, fake_llm_suitable_true)
    assert decision.verdict.value == "allow"
