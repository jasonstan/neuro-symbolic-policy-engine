#!/usr/bin/env python3
"""Run a YAML case through the wealth-management seed policy and print verdict + trace.

Default LLM is the `FakeLLM` that scripts a `SuitabilityClaim(suitable='true', ...)` for every
case so the CLI runs offline without an Anthropic API key. Use `--llm anthropic` to hit the
real API (requires `ANTHROPIC_API_KEY`).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# Make the repo's src/ importable when running this file directly from a checkout.
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "src"))

from nspk import Verdict, evaluate  # noqa: E402
from nspk.adapters.synthetic import SyntheticAdapter, load_bundled_policy  # noqa: E402
from nspk.judgments.suitability import SuitabilityClaim  # noqa: E402
from nspk.rails.llm_client import AnthropicLLM, FakeLLM  # noqa: E402

_HRULE = "=" * 70
_THIN = "-" * 70


def _make_llm(kind: str):
    if kind == "fake":
        # Demo default: always labels recommendations as suitable. This makes case 01 a clean
        # allow and case 02 a pure fact-rail block — exercising the separation of the two rails
        # without conflating their contributions.
        return FakeLLM(
            response=SuitabilityClaim(
                suitable="true",
                rationale="Demo FakeLLM default — assumes suitability.",
            )
        )
    if kind == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            sys.exit("ANTHROPIC_API_KEY not set; either export it or pass --llm fake.")
        model = os.environ.get("NSPK_JUDGMENT_MODEL", "claude-sonnet-4-6")
        return AnthropicLLM(api_key=api_key, model=model)
    raise ValueError(f"Unknown --llm kind: {kind!r}")


def _print_decision(decision) -> None:
    print(_HRULE)
    print(f"Case:    {decision.trace.case_id}")
    print(f"Policy:  {decision.trace.policy_name}")
    print(_THIN)
    for step in decision.trace.steps:
        if step.kind == "fact":
            print(f"Clause {step.clause_id}  (fact)")
            print(f"  description:     {step.description}")
            print(f"  evaluator:       {step.evaluator}")
            print(f"  violated:        {step.result.violated}")
            print(f"  evidence:        {json.dumps(step.result.evidence, default=str)}")
            print(f"  binding matched: {step.binding_matched}")
            print(f"  action:          {step.action.value}")
        elif step.kind == "judgment":
            print(f"Clause {step.clause_id}  (judgment)")
            print(f"  description:     {step.description}")
            print(f"  schema:          {step.schema_name}")
            print(f"  claim:           {json.dumps(step.claim, default=str)}")
            print(f"  confidence:      {step.confidence:.2f}")
            print(f"  binding matched: {step.binding_matched}")
            print(f"  action:          {step.action.value}")
        elif step.kind == "merge":
            print("Merge step (most-severe wins)")
            print(f"  contributed:     {[v.value for v in step.contributed_actions]}")
            print(f"  rule:            {step.rule}")
            print(f"  selected:        {step.selected.value}")
        print(_THIN)
    print(f"FINAL VERDICT: {decision.verdict.value.upper()}")
    print(_HRULE)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a YAML case through the seed policy.")
    parser.add_argument("case", type=Path, help="Path to a case YAML file.")
    parser.add_argument(
        "--policy",
        type=Path,
        default=None,
        help="Path to a policy YAML. Defaults to the bundled wealth_management policy.",
    )
    parser.add_argument(
        "--llm",
        choices=["fake", "anthropic"],
        default="fake",
        help="Which judgment-rail client to use. Default: fake (no network).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit the decision as one JSON object on stdout (machine-readable).",
    )
    args = parser.parse_args(argv)

    case = SyntheticAdapter.load_case(args.case)
    policy = (
        SyntheticAdapter.load_policy(args.policy)
        if args.policy is not None
        else load_bundled_policy("wealth_management")
    )
    llm = _make_llm(args.llm)
    decision = evaluate(case=case, policy=policy, llm=llm)

    if args.json:
        print(decision.model_dump_json(indent=2))
    else:
        _print_decision(decision)
    return 0 if decision.verdict == Verdict.ALLOW else 1


if __name__ == "__main__":
    sys.exit(main())
