"""Judgment rail: invokes the LLMClient under constrained decoding, returns a TypedClaim.

M1: confidence is stubbed to 1.0. M3 wraps this with an `EnsembleAgreement` estimator that
runs N independent samples and sets confidence to the modal class's share. The model never
reports confidence — see ADR-0002 and the typed-claim contract in CLAUDE.md.
"""

from nspk.judgments import JUDGMENT_SCHEMAS
from nspk.rails.llm_client import LLMClient
from nspk.types import Case, JudgmentClause, TypedClaim


def run_judgment_clause(clause: JudgmentClause, case: Case, llm: LLMClient) -> TypedClaim:
    try:
        entry = JUDGMENT_SCHEMAS[clause.schema_name]
    except KeyError as exc:
        raise KeyError(
            f"Unknown judgment schema {clause.schema_name!r}. "
            f"Available: {sorted(JUDGMENT_SCHEMAS)}"
        ) from exc

    system = clause.prompt or entry.default_prompt
    user = entry.build_user_message(case)
    parsed = llm.emit_claim(system=system, user=user, schema=entry.schema)

    return TypedClaim(
        schema_name=clause.schema_name,
        payload=parsed.model_dump(),
        confidence=1.0,  # M3 swaps for EnsembleAgreement
        samples=None,
    )
