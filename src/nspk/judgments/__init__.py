"""Registered judgment-clause schemas.

Each registered judgment exposes:
  - `schema`           : the Pydantic model for the typed claim (constrains form, not truth)
  - `default_prompt`   : the system prompt (policy YAML can override per clause)
  - `build_user_message(case)` : the per-clause projection of the Case content into a user msg
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from nspk.judgments.suitability import (
    DEFAULT_PROMPT as SUITABILITY_PROMPT,
)
from nspk.judgments.suitability import (
    SuitabilityClaim,
)
from nspk.judgments.suitability import (
    build_user_message as suitability_build_user_message,
)


@dataclass(frozen=True)
class JudgmentSchemaEntry:
    name: str
    schema: type[BaseModel]
    default_prompt: str
    build_user_message: Callable[[Any], str]


JUDGMENT_SCHEMAS: dict[str, JudgmentSchemaEntry] = {
    "suitability": JudgmentSchemaEntry(
        name="suitability",
        schema=SuitabilityClaim,
        default_prompt=SUITABILITY_PROMPT,
        build_user_message=suitability_build_user_message,
    ),
}
