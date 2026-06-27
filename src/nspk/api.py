"""Public API surface — the stable entry point.

External consumers should import only from this module (re-exported via `nspk.__init__`).
"""

from nspk.engine.evaluator import evaluate

__all__ = ["evaluate"]
