# Intent brief — neuro-symbolic-policy-kernel

*What this artifact is for, who it must convince, and what would prove it wrong. This is the
value layer the build serves; evals exist to make these claims (and their falsifiers)
executable. A milestone is "done" when the evals for the claims it advances pass — not when
the code merely runs.*

This demonstrator's "user" is not an end-user, and its job is not functional — it is
**rhetorical**: make one architectural claim legible to a skeptical viewer, and show where
the claim stops.

## The thesis (one sentence)

A policy for governing AI-agent actions can be disaggregated into **typed deterministic facts**
and **typed bounded judgments**, then recombined by a **transparent symbolic engine** into a
single, **auditable, policy-bound verdict** — so that the model never decides, and a
confident-but-wrong judgment can never override a hard fact.

## What this artifact is not

Not a product. Not production-ready. Not a regulatory accuracy claim. Not a general-purpose
policy language.

## Who this must convince, and what each needs to see

- **Product leader** — *Is this a real, ownable surface (a behavioral governance layer
  someone could own as a product), or a clever toy?* Needs to see that the policy YAML is a
  customer-editable artifact, the evidence trace is shippable as audit, and the same engine
  can serve more than one scenario via the documented adapter seam.
- **Safety lead** — *Is the fact/judgment boundary real, or theater?* Needs to see it hold
  under adversarial pressure (confident-but-wrong judgments, prompt injection in the
  unstructured content), and needs the demo to be honest about where it doesn't.
- **Engineering lead** — *Is it shippable and maintainable, or over-engineered?* Needs to
  see a small, well-tested core with clean seams: a library with zero web dependencies, a
  public API of six names, three ADRs justifying each architectural choice, and an
  explicitly bounded scope.

## Claims and falsifiers

Each claim names what would make a skeptic concede it's false. The falsifiers are the
adversarial eval spec.

- **C1 — Disaggregation.** A policy splits into fact clauses (deterministic over recorded
  state) and judgment clauses (LLM-emitted typed claims), recombined by the engine into one
  verdict. *Falsifier:* a clause whose evaluation collapses both rails back into a single LLM
  call — i.e., the split buys nothing.
- **C2 — Boundary integrity.** The LLM emits only a *typed claim*; the verdict is a pure
  function of facts + claims + confidence + policy, computed by the engine. *For:* safety
  lead. *Falsifier:* any path where model output text reaches the verdict directly, or where
  injected instructions in the unstructured content change the decision rather than just the
  claim's value.
- **C3 — Fact authority.** A hard fact violation is never overridden by a permissive
  judgment, however confident. *For:* safety lead. *Falsifier:* a confident `suitable=true`
  flips a dual-role (open+fund) **block** to **allow**.
- **C4 — Policy-bound action.** What a typed claim triggers lives in policy YAML, not engine
  code. The same claim can `block` under one clause and `route_to_review` under another.
  *For:* product + engineering lead. *Falsifier:* a clause→action mapping exists in engine
  code, or the same `suitable=false` claim cannot be bound to different actions across
  clauses without editing the engine.
- **C5 — Auditability.** Every verdict ships an evidence trace — which clauses fired, on
  which inputs, fact vs. claim, confidence, gating threshold, **merge step** — legible to
  someone who didn't write the code. *For:* product + safety. *Falsifier:* a reviewer cannot
  reconstruct *why* a verdict was reached from the trace alone; or the fact portion of the
  trace is non-deterministic for identical inputs; or the judgment portion does not record
  the full per-sample distribution that confidence is derived from.
- **C6 — Honest uncertainty.** *(Pending M3.)* Confidence is independently sourced (ensemble
  agreement), never the model's self-report; a low-confidence judgment routes to review
  rather than being forced to allow or block. *For:* safety lead. *Falsifier:* the model's
  own stated confidence is what gates the decision, or an ambiguous case is confidently
  decided instead of escalated.

## What this demo does *not* claim (on purpose)

Stating the boundary is part of the credibility, not a hedge against it.

- **No composition / trajectory control.** Two individually-permitted actions that *together*
  violate intent are out of scope for the flat, per-decision engine. This ships as a
  **known-failure eval**, with trajectory-level control noted as documented backlog — not
  hidden.
- **Confidence is a POC mechanism**, not a calibrated estimator. Ensemble agreement is a
  stand-in with a clean swap-in seam; it is not claimed to be well-calibrated.
- **One synthetic scenario**, not breadth. The wealth-management policy is the hero case;
  generality is asserted via the adapter and library seams, not demonstrated across domains.
- **Not legally authoritative.** The wealth-management clauses (settlement window,
  suitability) are illustrative; they do not encode current regulation.
- **Research demonstrator, not production.** No scale, latency, or hardening claims.

## How this brief is used

This document is the **acceptance bar** for milestone work. A milestone is done when the
behavioral evals for its claims pass and the adversarial set has been extended where the
milestone introduces new surface. The eval scorecard (`evals/run_evals.py`) is the surface
the maintainer reviews at each milestone — not "pytest is green." Every new clause or
feature must name the claim in this brief that it advances; if it advances no claim, surface
that before building.
