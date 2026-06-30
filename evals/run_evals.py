"""CLI: run all evals and print a scorecard grouped by claim.

Usage:
    uv run python -m evals.run_evals
    uv run python evals/run_evals.py

Exit code:
    0 — scorecard clean (no FAIL, no unexpected XPASS).
    1 — at least one FAIL or unexpected XPASS — investigate.

This script does NOT call the Anthropic API. Every judgment claim is sourced from a scripted
FakeLLM defined inside each eval. A live-API smoke run, if needed later, lives behind a
separate flag (not implemented here).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Belt-and-suspenders sys.path so this runs either as `-m evals.run_evals` or as a script.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from evals._framework import format_scorecard, has_real_failures, run_all  # noqa: E402

_EVALS_ROOT = Path(__file__).resolve().parent


def main() -> int:
    roots = [_EVALS_ROOT / "behavioral", _EVALS_ROOT / "adversarial"]
    results = run_all(roots)
    print(format_scorecard(results))
    return 1 if has_real_failures(results) else 0


if __name__ == "__main__":
    sys.exit(main())
