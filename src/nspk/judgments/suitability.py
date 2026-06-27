"""Judgment clause C3: recommendation suits the client's risk profile.

The model emits a 3-class typed claim under constrained decoding. Confidence is sourced
independently (M3); the model never reports its own confidence. The model labels, the engine
decides.
"""

from typing import Literal

from pydantic import BaseModel, Field

from nspk.types import Case


class SuitabilityClaim(BaseModel):
    """Typed claim emitted by the judgment rail for clause C3.

    Constrained decoding guarantees `suitable` is one of the three literals. `rationale` is
    captured for the trace; the engine does NOT consume it as a decision input.
    """

    suitable: Literal["true", "false", "unclear"]
    rationale: str = Field(max_length=400)


DEFAULT_PROMPT = (
    "You are a financial-conduct evaluator. Given a client's risk profile and a recommendation, "
    "label whether the recommendation suits that risk profile.\n"
    '- suitable: "true" if it does.\n'
    '- suitable: "false" if it does not.\n'
    '- suitable: "unclear" if the information is insufficient.\n'
    "- rationale: one short sentence (max 30 words). Do NOT propose any action.\n"
    "You are labelling, not deciding."
)


def build_user_message(case: Case) -> str:
    if case.client is None or case.recommendation is None:
        return f"Case description: {case.description}"
    notes = f"Client notes: {case.client.notes}\n" if case.client.notes else ""
    return (
        f"Client risk profile: {case.client.risk_profile}\n"
        f"{notes}"
        f"\nRecommendation:\n{case.recommendation.text}"
    )
