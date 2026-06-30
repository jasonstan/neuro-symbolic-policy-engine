# Evals

This directory turns the [intent brief](BRIEF.md) into an executable acceptance bar. A
milestone is "done" when the evals for its claims pass, the adversarial set has been
extended to probe new surface, and the scorecard renders cleanly. Tests in `tests/` cover
*correctness*; evals here cover *thesis integrity*.

## Run

```bash
uv run python -m evals.run_evals
```

Exit code is `0` when no eval is `FAIL` or `XPASS`. `PENDING` (gated on a future milestone)
and `XFAIL` (known-failure, documented limit) do not fail CI.

## Tiers

- **`behavioral/`** — cases-with-expected-decisions that demonstrate a claim holds under
  representative inputs. The CLI example cases are lifted into this tier.
- **`adversarial/`** — cases designed to *break* a claim. Each adversarial eval names the
  claim it tries to falsify; if the eval passes, the claim survived the attack.
- **`tier: known_failure`** — cases the architecture cannot handle *on purpose*, with the
  documented reason recorded inline. Surfaces in the scorecard as `XFAIL`. Flips to `XPASS`
  (and CI-fails) if the architecture ever starts catching them — we want that signal.

## Claim → eval mapping (current)

| Claim | Eval | Tier | Status |
|---|---|---|---|
| C1 Disaggregation | `behavioral/b01_clean_allow.yaml` | behavioral | PASS |
| C1 Disaggregation | `behavioral/b02_fact_violation_dual_role.yaml` | behavioral | PASS |
| C2 Boundary integrity | `adversarial/a02_prompt_injection_in_content.py` | adversarial | PASS |
| C3 Fact authority | `adversarial/a01_confident_wrong_vs_fact.yaml` | adversarial | PASS |
| C4 Policy-bound action | `behavioral/b03_per_clause_binding.py` | behavioral | PASS |
| C5 Auditability | `behavioral/b04_trace_shape.py` | behavioral | PASS |
| C6 Honest uncertainty | `adversarial/a03_ambiguous_judgment.yaml` | adversarial | PENDING (M3) |
| (documented limit) | `adversarial/a04_trajectory_composition.py` | known-failure | XFAIL |

## Adding an eval

Every new clause or feature must name the claim in `BRIEF.md` that it advances and add or
extend an eval. Two ways to write one:

- **YAML** for single-run cases with declarative expectations. Schema: `EvalSpec` in
  `_framework.py` — `id`, `claim`, `tier`, `description`, optional `status` (`active` |
  `pending` | `known_failure`), `fake_llm` scripts keyed by judgment-schema registration
  name, `case`, and `expect` (verdict, per-clause actions, partial claim matches, fact
  violations).
- **Python** for multi-run or structural evals. Module exposes module-level constants
  `ID`, `CLAIM`, `TIER`, `DESCRIPTION` (optional `STATUS`, `KNOWN_FAILURE_REASON`,
  `PENDING_UNTIL`) and a `run() -> EvalResult` function.

If a change advances no claim in `BRIEF.md`, surface that before building.

## Live-API mode

Not implemented. The eval suite runs offline against `FakeLLM`. A live-API smoke run (for
shape-validation of `messages.parse`) lives behind a `pytest -m live` mark and is not the
acceptance gate.
