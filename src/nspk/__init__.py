"""Neuro-symbolic policy kernel.

Public API:
    evaluate(case, policy, llm) -> Decision
"""

from nspk.api import evaluate

__all__ = ["evaluate"]
__version__ = "0.1.0"
