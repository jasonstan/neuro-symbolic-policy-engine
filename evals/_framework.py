"""evals framework: spec models, runners, scripted FakeLLM, scorecard formatter.

Imported by evals.run_evals and by the Python eval modules in behavioral/ and adversarial/.
The framework is deliberately separate from tests/ — see ADR-0004 and evals/BRIEF.md.

Two ways to write an eval:
1. YAML — for single-run cases with declarative expectations. Schema is `EvalSpec`.
2. Python — for multi-run / structural evals. Module exposes ID/CLAIM/TIER/DESCRIPTION
   constants and a `run() -> EvalResult` function. Optional STATUS/KNOWN_FAILURE_REASON/
   PENDING_UNTIL constants tag pending-until-milestone or known-failure-on-purpose evals.

Statuses:
    PASS    — eval ran, assertions held.
    FAIL    — eval ran, assertions failed. CI-failing.
    XFAIL   — eval is a documented known-failure and it failed as documented (good).
    XPASS   — known-failure unexpectedly passed; architecture may have changed. CI-failing.
    PENDING — eval is gated on a future milestone; skipped.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from enum import Enum
from importlib import util as importlib_util
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

from nspk import Verdict, evaluate
from nspk.adapters.synthetic import load_bundled_policy
from nspk.rails.llm_client import build_scripted_fake_llm
from nspk.types import Case, Decision


class EvalStatus(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    XFAIL = "xfail"
    XPASS = "xpass"
    PENDING = "pending"


class EvalExpect(BaseModel):
    verdict: Verdict | None = None
    clause_actions: dict[str, Verdict] = Field(default_factory=dict)
    claim_values: dict[str, dict[str, Any]] = Field(default_factory=dict)
    fact_violated: dict[str, bool] = Field(default_factory=dict)


class EvalSpec(BaseModel):
    id: str
    claim: str
    tier: Literal["behavioral", "adversarial", "known_failure"]
    description: str
    status: Literal["active", "pending", "known_failure"] = "active"
    pending_until: str | None = None
    known_failure_reason: str | None = None
    fake_llm: dict[str, dict[str, Any]] = Field(default_factory=dict)
    case: dict[str, Any]
    policy: str = "wealth_management"
    expect: EvalExpect = Field(default_factory=EvalExpect)


class EvalResult(BaseModel):
    id: str
    claim: str
    tier: str
    description: str
    status: EvalStatus
    reason: str | None = None


# ---------- runners ----------

def run_yaml_eval(spec: EvalSpec) -> EvalResult:
    base = {
        "id": spec.id,
        "claim": spec.claim,
        "tier": spec.tier,
        "description": spec.description,
    }

    if spec.status == "pending":
        return EvalResult(
            **base,
            status=EvalStatus.PENDING,
            reason=f"gated on {spec.pending_until or 'future milestone'}",
        )

    try:
        case = Case.model_validate(spec.case)
        policy = load_bundled_policy(spec.policy)
        llm = build_scripted_fake_llm(spec.fake_llm)
        decision = evaluate(case=case, policy=policy, llm=llm)
    except Exception as exc:
        if spec.status == "known_failure":
            return EvalResult(
                **base,
                status=EvalStatus.XFAIL,
                reason=spec.known_failure_reason or f"expected exception: {exc!r}",
            )
        return EvalResult(**base, status=EvalStatus.FAIL, reason=f"unexpected exception: {exc!r}")

    failures = _check_assertions(decision, spec.expect)

    if spec.status == "known_failure":
        if failures:
            return EvalResult(
                **base,
                status=EvalStatus.XFAIL,
                reason=spec.known_failure_reason or "; ".join(failures),
            )
        return EvalResult(
            **base,
            status=EvalStatus.XPASS,
            reason=(
                "known-failure unexpectedly passed all assertions; the architecture may have "
                "changed — investigate"
            ),
        )

    if failures:
        return EvalResult(**base, status=EvalStatus.FAIL, reason="; ".join(failures))
    return EvalResult(**base, status=EvalStatus.PASS)


def _check_assertions(decision: Decision, expect: EvalExpect) -> list[str]:
    failures: list[str] = []

    if expect.verdict is not None and decision.verdict != expect.verdict:
        failures.append(f"verdict: expected {expect.verdict.value}, got {decision.verdict.value}")

    actions_by_clause = {
        s.clause_id: s.action
        for s in decision.trace.steps
        if s.kind in ("fact", "judgment")
    }
    for clause_id, expected_action in expect.clause_actions.items():
        actual = actions_by_clause.get(clause_id)
        if actual is None:
            failures.append(f"clause {clause_id}: not present in trace")
        elif actual != expected_action:
            failures.append(
                f"clause {clause_id}: expected action {expected_action.value}, got {actual.value}"
            )

    judgment_claims = {
        s.clause_id: s.claim for s in decision.trace.steps if s.kind == "judgment"
    }
    for clause_id, expected_partial in expect.claim_values.items():
        actual = judgment_claims.get(clause_id)
        if actual is None:
            failures.append(f"claim for {clause_id}: not present in trace")
            continue
        for key, val in expected_partial.items():
            if actual.get(key) != val:
                failures.append(
                    f"claim for {clause_id}: expected {key}={val!r}, got {actual.get(key)!r}"
                )

    fact_results = {s.clause_id: s.result for s in decision.trace.steps if s.kind == "fact"}
    for clause_id, expected_violated in expect.fact_violated.items():
        actual = fact_results.get(clause_id)
        if actual is None:
            failures.append(f"fact clause {clause_id}: not present in trace")
        elif actual.violated != expected_violated:
            failures.append(
                f"fact {clause_id}: expected violated={expected_violated}, got {actual.violated}"
            )

    return failures


def run_python_eval(module_path: Path) -> EvalResult:
    module = _import_module_from_path(module_path)

    required = ("ID", "CLAIM", "TIER", "DESCRIPTION")
    missing = [a for a in required if not hasattr(module, a)]
    if missing:
        raise ValueError(f"{module_path}: Python eval missing required attrs {missing}")

    status = getattr(module, "STATUS", "active")
    if status == "pending":
        return EvalResult(
            id=module.ID,
            claim=module.CLAIM,
            tier=module.TIER,
            description=module.DESCRIPTION,
            status=EvalStatus.PENDING,
            reason=f"gated on {getattr(module, 'PENDING_UNTIL', 'future milestone')}",
        )

    if not hasattr(module, "run"):
        raise ValueError(f"{module_path}: Python eval missing `run()` function")

    try:
        return module.run()
    except Exception as exc:
        if status == "known_failure":
            return EvalResult(
                id=module.ID,
                claim=module.CLAIM,
                tier=module.TIER,
                description=module.DESCRIPTION,
                status=EvalStatus.XFAIL,
                reason=getattr(module, "KNOWN_FAILURE_REASON", f"expected exception: {exc!r}"),
            )
        return EvalResult(
            id=module.ID,
            claim=module.CLAIM,
            tier=module.TIER,
            description=module.DESCRIPTION,
            status=EvalStatus.FAIL,
            reason=f"unexpected exception: {exc!r}",
        )


def _import_module_from_path(path: Path):
    spec = importlib_util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"could not load module from {path}")
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------- discovery ----------

def discover_yaml_specs(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.yaml")) if directory.exists() else []


def discover_python_evals(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(p for p in directory.glob("*.py") if not p.name.startswith("_"))


def load_yaml_spec(path: Path) -> EvalSpec:
    return EvalSpec.model_validate(yaml.safe_load(path.read_text()))


def run_all(roots: list[Path]) -> list[EvalResult]:
    results: list[EvalResult] = []
    for root in roots:
        for yaml_path in discover_yaml_specs(root):
            results.append(run_yaml_eval(load_yaml_spec(yaml_path)))
        for py_path in discover_python_evals(root):
            results.append(run_python_eval(py_path))
    return results


# ---------- scorecard ----------

CLAIM_TITLES: dict[str, str] = {
    "C1": "Disaggregation",
    "C2": "Boundary integrity",
    "C3": "Fact authority",
    "C4": "Policy-bound action",
    "C5": "Auditability",
    "C6": "Honest uncertainty",
}


def _format_status_label(r: EvalResult) -> str:
    return {
        EvalStatus.PASS: "PASS",
        EvalStatus.FAIL: "FAIL",
        EvalStatus.XFAIL: "XFAIL",
        EvalStatus.XPASS: "XPASS",
        EvalStatus.PENDING: "PENDING",
    }[r.status]


def format_scorecard(results: list[EvalResult], policy_name: str = "wealth_management_v1") -> str:
    today = date.today().isoformat()
    sep = "═" * 78
    thin = "─" * 78

    lines: list[str] = [
        sep,
        f" NSPK eval scorecard  ·  {today}  ·  policy: {policy_name}",
        sep,
    ]

    by_claim: dict[str, list[EvalResult]] = defaultdict(list)
    known_failures: list[EvalResult] = []
    for r in results:
        if r.tier == "known_failure":
            known_failures.append(r)
        else:
            by_claim[r.claim].append(r)

    claim_order = [c for c in CLAIM_TITLES if c in by_claim]
    claim_order += sorted(c for c in by_claim if c not in claim_order)

    for claim in claim_order:
        title = CLAIM_TITLES.get(claim, claim)
        lines.append("")
        lines.append(f" {claim}  {title}")
        for r in by_claim[claim]:
            lines.append(f"   [{r.tier:11}] {r.id:42}  {_format_status_label(r)}")
            if r.status in (EvalStatus.FAIL, EvalStatus.XPASS, EvalStatus.PENDING) and r.reason:
                lines.append(f"     ↳ {r.reason}")

    if known_failures:
        lines.append("")
        lines.append(" Known-failures (on purpose):")
        for r in known_failures:
            lines.append(f"   [{r.tier:13}] {r.id:42}  {_format_status_label(r)}")
            if r.reason:
                lines.append(f"     ↳ {r.reason}")

    lines.append(thin)
    counts = Counter(r.status for r in results)
    parts: list[str] = []
    for status, label in (
        (EvalStatus.PASS, "pass"),
        (EvalStatus.FAIL, "fail"),
        (EvalStatus.PENDING, "pending"),
        (EvalStatus.XFAIL, "known-failure"),
        (EvalStatus.XPASS, "unexpected-pass"),
    ):
        if counts.get(status):
            parts.append(f"{counts[status]} {label}")
    lines.append(f" Totals:  {' · '.join(parts) or 'none'}")
    lines.append(sep)
    return "\n".join(lines)


def has_real_failures(results: list[EvalResult]) -> bool:
    """True if any FAIL or unexpected XPASS — these are the statuses that should fail CI."""
    return any(r.status in (EvalStatus.FAIL, EvalStatus.XPASS) for r in results)
