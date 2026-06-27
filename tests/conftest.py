"""Shared test fixtures."""

from datetime import datetime, timezone

import pytest

from nspk.adapters.synthetic import load_bundled_policy
from nspk.judgments.suitability import SuitabilityClaim
from nspk.rails.llm_client import FakeLLM
from nspk.types import Case, Client, Event, Recommendation


@pytest.fixture
def fake_llm_suitable_true() -> FakeLLM:
    return FakeLLM(response=SuitabilityClaim(suitable="true", rationale="Aligned with profile."))


@pytest.fixture
def fake_llm_suitable_false() -> FakeLLM:
    return FakeLLM(response=SuitabilityClaim(suitable="false", rationale="Mismatch with risk."))


@pytest.fixture
def fake_llm_wrong_but_conformant() -> FakeLLM:
    """Emits suitable='true' for a case where the right answer would be 'false'.

    The point isn't that the LLM is wrong (it is); the point is that the typed-claim shape
    holds regardless. Form vs. truth — see ADR-0002.
    """
    return FakeLLM(response=SuitabilityClaim(suitable="true", rationale="(intentionally wrong)"))


@pytest.fixture
def policy():
    return load_bundled_policy("wealth_management")


@pytest.fixture
def case_clean_allow() -> Case:
    return Case(
        id="t_clean_allow",
        description="Two different advisors; suitable recommendation",
        events=[
            Event(
                actor_id="advisor_a",
                action="open_account",
                account_id="acc_test",
                timestamp=datetime(2026, 6, 1, 10, 0, tzinfo=timezone.utc),
            ),
            Event(
                actor_id="advisor_b",
                action="fund_account",
                account_id="acc_test",
                timestamp=datetime(2026, 6, 1, 10, 5, tzinfo=timezone.utc),
            ),
        ],
        client=Client(id="c_t", risk_profile="moderate"),
        recommendation=Recommendation(text="Balanced 60/40."),
    )


@pytest.fixture
def case_dual_role_violation() -> Case:
    return Case(
        id="t_dual_role",
        description="Same advisor opens and funds",
        events=[
            Event(
                actor_id="advisor_a",
                action="open_account",
                account_id="acc_test",
                timestamp=datetime(2026, 6, 1, 11, 0, tzinfo=timezone.utc),
            ),
            Event(
                actor_id="advisor_a",
                action="fund_account",
                account_id="acc_test",
                timestamp=datetime(2026, 6, 1, 11, 5, tzinfo=timezone.utc),
            ),
        ],
        client=Client(id="c_t2", risk_profile="conservative"),
        recommendation=Recommendation(text="Conservative bonds."),
    )
