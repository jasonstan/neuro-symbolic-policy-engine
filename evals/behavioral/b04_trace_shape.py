"""C5 — every verdict ships a fully reconstructible evidence trace.

Structural assertion. For a representative case: the trace has the documented top-level
fields, every fact/judgment/merge step is present and well-shaped, and the trace JSON
round-trips through the Pydantic `Trace` model byte-for-byte (no data loss on serialize).

This guards against a future refactor that quietly drops a trace field — which would break
the auditability story even if `pytest` stayed green.
"""

from __future__ import annotations

from datetime import datetime, timezone

from evals._framework import EvalResult, EvalStatus, build_scripted_fake_llm
from nspk import evaluate
from nspk.adapters.synthetic import load_bundled_policy
from nspk.types import Case, Client, Event, Recommendation, Trace

ID = "b04_trace_shape"
CLAIM = "C5"
TIER = "behavioral"
DESCRIPTION = (
    "Trace JSON has the documented shape (fact steps with evidence + binding, judgment steps "
    "with claim + confidence + binding, merge step with contributed actions and selected) and "
    "round-trips through the Trace model without loss."
)


def _case() -> Case:
    return Case(
        id="b04_case",
        description="Generic case to exercise the full trace shape.",
        events=[
            Event(
                actor_id="advisor_a",
                action="open_account",
                account_id="acc_b04",
                timestamp=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            ),
            Event(
                actor_id="advisor_b",
                action="fund_account",
                account_id="acc_b04",
                timestamp=datetime(2026, 6, 1, 10, 5, tzinfo=timezone.utc),
            ),
        ],
        client=Client(id="client_b04", risk_profile="moderate"),
        recommendation=Recommendation(text="Balanced 60/40 portfolio."),
    )


def run() -> EvalResult:
    policy = load_bundled_policy("wealth_management")
    llm = build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "ok"},
        "no_exploitation": {"exploits_distress": "false", "rationale": "no distress"},
    })
    decision = evaluate(case=_case(), policy=policy, llm=llm)

    failures: list[str] = []

    if not decision.trace.case_id:
        failures.append("trace.case_id missing")
    if not decision.trace.policy_name:
        failures.append("trace.policy_name missing")
    if not decision.trace.steps:
        failures.append("trace.steps is empty")
    if decision.trace.final_verdict != decision.verdict:
        failures.append("trace.final_verdict diverges from decision.verdict")

    kinds = [s.kind for s in decision.trace.steps]
    for required in ("fact", "judgment", "merge"):
        if required not in kinds:
            failures.append(f"trace missing {required!r} step")

    for step in decision.trace.steps:
        if step.kind == "fact":
            if step.result is None or step.result.evidence is None:
                failures.append(f"fact step {step.clause_id}: result/evidence missing")
            if step.action is None:
                failures.append(f"fact step {step.clause_id}: action missing")
        elif step.kind == "judgment":
            if not step.claim:
                failures.append(f"judgment step {step.clause_id}: claim is empty")
            if step.confidence is None:
                failures.append(f"judgment step {step.clause_id}: confidence missing")
            if step.action is None:
                failures.append(f"judgment step {step.clause_id}: action missing")
        elif step.kind == "merge":
            if not step.contributed_actions:
                failures.append("merge step: contributed_actions empty")
            if step.selected is None:
                failures.append("merge step: selected missing")

    js = decision.trace.model_dump_json()
    reloaded = Trace.model_validate_json(js)
    if reloaded.model_dump_json() != js:
        failures.append("trace JSON round-trip is lossy")

    base = dict(id=ID, claim=CLAIM, tier=TIER, description=DESCRIPTION)
    if failures:
        return EvalResult(**base, status=EvalStatus.FAIL, reason="; ".join(failures))
    return EvalResult(**base, status=EvalStatus.PASS)
