"""Neuro-symbolic policy kernel.

Public API:
    evaluate(case, policy, llm) -> Decision
    Case, Policy, Decision, Trace, TypedClaim, Verdict
"""

from nspk.api import evaluate
from nspk.types import Case, Decision, Policy, Trace, TypedClaim, Verdict

__all__ = ["Case", "Decision", "Policy", "Trace", "TypedClaim", "Verdict", "evaluate"]
__version__ = "0.1.0"
