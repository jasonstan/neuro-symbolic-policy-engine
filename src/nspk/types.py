"""Core types: cases, policies, claims, decisions, traces.

These are the engine's vocabulary. The engine consumes `Case` + `Policy` (+ an `LLMClient`
when judgment clauses are present) and produces a `Decision`. All boundary types are Pydantic
v2 BaseModels so policy YAML and case YAML round-trip through validation.
"""

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field


class Verdict(str, Enum):
    ALLOW = "allow"
    LOG = "log"
    ROUTE_TO_REVIEW = "route_to_review"
    ESCALATE_FOR_SIGNOFF = "escalate_for_signoff"
    BLOCK = "block"


# ---------- Case shape (currently wealth-management-specific) ----------

class Event(BaseModel):
    actor_id: str
    action: str
    account_id: str
    timestamp: datetime


class Client(BaseModel):
    id: str
    risk_profile: str
    notes: str | None = None


class Recommendation(BaseModel):
    text: str


class Case(BaseModel):
    """A unit of agent activity to be evaluated.

    The shape is currently the wealth-management hero domain (see ADR-0003). The CaseAdapter
    seam in `nspk.adapters.base` is where future domains plug in: they either subclass Case or
    marshal their state into this shape. The engine itself does not introspect domain fields;
    only registered fact-evaluators and judgment-input-builders do.
    """
    id: str
    description: str
    events: list[Event] = Field(default_factory=list)
    client: Client | None = None
    recommendation: Recommendation | None = None
    conversation_excerpt: str | None = None  # M2 — used by the no-exploitation clause


# ---------- Policy shape ----------

class Binding(BaseModel):
    """A guard → action rule on a clause's result.

    Guard keys may use `_gte` / `_lt` suffixes for numeric thresholds (used by confidence):
        {"suitable": "false", "confidence_gte": 0.8}  →  block
    All keys must match for the binding to fire; first match wins. If no binding matches the
    clause contributes `allow`.
    """
    when: dict[str, Any]
    action: Verdict


class FactClause(BaseModel):
    type: Literal["fact"] = "fact"
    id: str
    description: str
    evaluator: str
    bindings: list[Binding] = Field(default_factory=list)


class JudgmentClause(BaseModel):
    type: Literal["judgment"] = "judgment"
    id: str
    description: str
    schema_name: str = Field(alias="schema")  # YAML key `schema`; Python attr `schema_name`
    prompt: str
    bindings: list[Binding] = Field(default_factory=list)
    model_config = ConfigDict(populate_by_name=True)


Clause = Annotated[Union[FactClause, JudgmentClause], Field(discriminator="type")]


class Policy(BaseModel):
    name: str
    description: str | None = None
    clauses: list[Clause]


# ---------- Rail outputs ----------

class FactResult(BaseModel):
    """Output of a fact-rail evaluator."""
    violated: bool
    evidence: dict[str, Any] = Field(default_factory=dict)


class TypedClaim(BaseModel):
    """Output of the judgment rail for one clause.

    `payload` is the model's parsed Pydantic claim, serialized to dict for trace transport.
    `confidence` is set by the ConfidenceEstimator — never by the model itself. `samples` carries
    the per-sample distribution under ensemble agreement (populated in M3).
    """
    schema_name: str
    payload: dict[str, Any]
    confidence: float
    samples: list[dict[str, Any]] | None = None


# ---------- Trace ----------

class FactStep(BaseModel):
    kind: Literal["fact"] = "fact"
    clause_id: str
    description: str
    evaluator: str
    result: FactResult
    binding_matched: dict[str, Any] | None
    action: Verdict


class JudgmentStep(BaseModel):
    kind: Literal["judgment"] = "judgment"
    clause_id: str
    description: str
    schema_name: str
    claim: dict[str, Any]
    confidence: float
    samples: list[dict[str, Any]] | None = None
    binding_matched: dict[str, Any] | None
    action: Verdict


class MergeStep(BaseModel):
    kind: Literal["merge"] = "merge"
    contributed_actions: list[Verdict]
    selected: Verdict
    rule: str = "most-severe wins (block > escalate_for_signoff > route_to_review > log > allow)"


TraceStep = Annotated[Union[FactStep, JudgmentStep, MergeStep], Field(discriminator="kind")]


class Trace(BaseModel):
    case_id: str
    policy_name: str
    steps: list[TraceStep]
    final_verdict: Verdict


class Decision(BaseModel):
    verdict: Verdict
    trace: Trace
