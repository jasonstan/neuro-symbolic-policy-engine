"""Shared test fixtures.

FakeLLM fixtures script BOTH judgment schemas (suitability, no_exploitation) so they work
against the bundled policy which now invokes both judgment clauses. A fixture's name describes
the *suitability* posture; no_exploitation defaults to false unless the fixture says otherwise.
"""

from datetime import datetime, timezone

import pytest

from nspk.adapters.synthetic import load_bundled_policy
from nspk.rails.llm_client import FakeLLM, build_scripted_fake_llm
from nspk.types import Case, Client, Event, Recommendation


@pytest.fixture
def fake_llm_suitable_true() -> FakeLLM:
    return build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "Aligned with profile."},
        "no_exploitation": {"exploits_distress": "false", "rationale": "No distress signals."},
    })


@pytest.fixture
def fake_llm_suitable_false() -> FakeLLM:
    return build_scripted_fake_llm({
        "suitability": {"suitable": "false", "rationale": "Mismatch with risk."},
        "no_exploitation": {"exploits_distress": "false", "rationale": "No distress signals."},
    })


@pytest.fixture
def fake_llm_wrong_but_conformant() -> FakeLLM:
    """Emits suitable='true' (and exploits_distress='false') regardless of input.

    Used to assert that the typed-claim shape holds even when the model is "wrong" — form vs.
    truth (ADR-0002).
    """
    return build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "(intentionally wrong)"},
        "no_exploitation": {"exploits_distress": "false", "rationale": "(intentionally wrong)"},
    })


@pytest.fixture
def fake_llm_exploits_true() -> FakeLLM:
    """Confidently labels exploitation; suitability stays true so only C4 contributes a verdict shift."""
    return build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "Product aligns with profile."},
        "no_exploitation": {
            "exploits_distress": "true",
            "rationale": "Wrap-fee program pushed on overwhelmed bereaved client.",
        },
    })


@pytest.fixture
def fake_llm_exploits_unclear() -> FakeLLM:
    return build_scripted_fake_llm({
        "suitability": {"suitable": "true", "rationale": "Product aligns with profile."},
        "no_exploitation": {"exploits_distress": "unclear", "rationale": "Ambiguous client state."},
    })


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


@pytest.fixture
def case_exploitation() -> Case:
    return Case(
        id="t_exploitation",
        description="Distressed client; advisor pushes wrap-fee program",
        events=[
            Event(
                actor_id="advisor_a",
                action="open_account",
                account_id="acc_t_exploit",
                timestamp=datetime(2026, 6, 15, 9, 0, tzinfo=timezone.utc),
            ),
            Event(
                actor_id="advisor_b",
                action="fund_account",
                account_id="acc_t_exploit",
                timestamp=datetime(2026, 6, 15, 9, 30, tzinfo=timezone.utc),
            ),
        ],
        client=Client(
            id="c_exploit",
            risk_profile="conservative",
            notes="Recently bereaved; expressed inability to evaluate options.",
        ),
        recommendation=Recommendation(
            text="Treasury bond ladder in our managed advisory program (1.5% AUM fee)."
        ),
        conversation_excerpt=(
            "Client: I just need someone to handle it.\n"
            "Advisor: Sign here for the managed program; we'll take care of everything."
        ),
    )
