"""Deterministic fact rail: pure rule evaluators over case state.

Each evaluator is a pure function `Case -> FactResult` — same inputs ⇒ identical FactResult,
including the evidence dict. The fact-rail determinism test asserts byte-equal traces.
"""

from collections.abc import Callable

from nspk.types import Case, FactResult

FactEvaluator = Callable[[Case], FactResult]


def advisor_dual_role(case: Case) -> FactResult:
    """Clause C1: one advisor may not both open AND fund the same account.

    `violated=True` iff any single advisor appears in BOTH an `open_account` and `fund_account`
    event for the same `account_id` within the case's event log. Evidence lists the offending
    (advisor, account) pairs in sorted order for deterministic trace output.
    """
    actions_by_actor_account: dict[tuple[str, str], set[str]] = {}
    for event in case.events:
        key = (event.actor_id, event.account_id)
        actions_by_actor_account.setdefault(key, set()).add(event.action)

    offenders = sorted(
        (
            {"advisor": actor, "account": account}
            for (actor, account), actions in actions_by_actor_account.items()
            if {"open_account", "fund_account"}.issubset(actions)
        ),
        key=lambda x: (x["advisor"], x["account"]),
    )

    return FactResult(
        violated=len(offenders) > 0,
        evidence={"offenders": offenders, "events_examined": len(case.events)},
    )


FACT_EVALUATORS: dict[str, FactEvaluator] = {
    "advisor_dual_role": advisor_dual_role,
}


def run_fact_evaluator(name: str, case: Case) -> FactResult:
    try:
        evaluator = FACT_EVALUATORS[name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown fact evaluator {name!r}. Available: {sorted(FACT_EVALUATORS)}"
        ) from exc
    return evaluator(case)
