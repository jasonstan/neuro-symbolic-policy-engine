"""KNOWN-FAILURE: cross-decision composition is out of scope, on purpose.

The brief's "where this stops" section says: "Two individually-permitted actions that
together violate intent are out of reach — surfaced as the trajectory-violation known-failure
eval." This module is that eval.

Two cases run sequentially:
  Step 1 — move client from conservative → moderate (per stated profile)
  Step 2 — move client from moderate    → aggressive (per stated profile)

Each step is individually justifiable. Together they represent a risk shift that human review
would catch but that the current per-decision engine cannot — it sees one Case at a time and
has no trajectory state. The eval expects both per-decision verdicts to be `allow` (the
documented limit). If a future change to the architecture catches this, the eval flips to
XPASS — and we want that signal.
"""

from __future__ import annotations

from evals._framework import EvalResult, EvalStatus, build_scripted_fake_llm
from nspk import Verdict, evaluate
from nspk.adapters.synthetic import load_bundled_policy
from nspk.types import Case, Client, Recommendation

ID = "a04_trajectory_composition"
CLAIM = "out_of_scope"
TIER = "known_failure"
STATUS = "known_failure"
KNOWN_FAILURE_REASON = (
    "Engine is per-decision. Cross-decision composition (a trajectory of individually suitable "
    "recommendations that aggregates into a risk shift) is documented backlog — see "
    "evals/BRIEF.md §'Where this stops'. Two cases run sequentially are each `allow` by the "
    "per-decision engine even though together they violate intent."
)
DESCRIPTION = "Two individually-permitted recommendations that jointly violate intent."


def _step_one() -> Case:
    return Case(
        id="a04_step_1_conservative_to_moderate",
        description="Move client from conservative → moderate; individually defensible.",
        events=[],
        client=Client(id="client_a04", risk_profile="moderate", notes="Was conservative."),
        recommendation=Recommendation(
            text="Recommending a moderate 50/50 portfolio appropriate to your updated profile."
        ),
    )


def _step_two() -> Case:
    return Case(
        id="a04_step_2_moderate_to_aggressive",
        description="Move client from moderate → aggressive; individually defensible.",
        events=[],
        client=Client(id="client_a04", risk_profile="aggressive", notes="Was moderate."),
        recommendation=Recommendation(
            text="Recommending an aggressive 80/20 portfolio appropriate to your updated profile."
        ),
    )


def run() -> EvalResult:
    policy = load_bundled_policy("wealth_management")
    llm = build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "matches stated profile"},
        "no_exploitation": {"exploits_distress": "false", "rationale": "no distress signals"},
    })

    d1 = evaluate(case=_step_one(), policy=policy, llm=llm)
    d2 = evaluate(case=_step_two(), policy=policy, llm=llm)

    architecture_caught = d1.verdict != Verdict.ALLOW or d2.verdict != Verdict.ALLOW

    base = dict(id=ID, claim=CLAIM, tier=TIER, description=DESCRIPTION)
    if architecture_caught:
        return EvalResult(
            **base,
            status=EvalStatus.XPASS,
            reason=(
                f"architecture unexpectedly caught the composition (step1={d1.verdict.value}, "
                f"step2={d2.verdict.value}). Investigate — either the per-decision engine "
                "gained trajectory awareness, or one of the two cases became per-decision "
                "blockable for an unrelated reason."
            ),
        )
    return EvalResult(**base, status=EvalStatus.XFAIL, reason=KNOWN_FAILURE_REASON)
