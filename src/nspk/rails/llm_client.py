"""LLM-client abstraction for the judgment rail.

The judgment rail depends on this Protocol, not on the Anthropic SDK directly, so:
- the library imports and tests without an API key;
- the test suite uses `FakeLLM` to script responses (including "wrong but conformant" ones);
- swapping providers is a one-class change.

`emit_claim` is the only operation the rail needs: take a system prompt, a user message, and a
Pydantic schema; return the parsed instance. Constrained decoding (Anthropic Structured Outputs
in `AnthropicLLM`) guarantees the returned instance conforms to the schema by construction — no
parse-error handling at this seam (see ADR-0002).
"""

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    def emit_claim(self, *, system: str, user: str, schema: type[T]) -> T: ...


class AnthropicLLM:
    """Production judgment-rail client backed by Anthropic Structured Outputs.

    Uses `client.messages.parse(..., output_format=Schema)` — see ADR-0002. The model fills the
    schema's enum field and short rationale; it never emits confidence or a verdict.
    """

    def __init__(self, *, api_key: str | None = None, model: str = "claude-sonnet-4-6"):
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._model = model

    def emit_claim(self, *, system: str, user: str, schema: type[T]) -> T:
        response = self._client.messages.parse(
            model=self._model,
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": user}],
            output_format=schema,
        )
        return response.parsed_output  # type: ignore[no-any-return,attr-defined]


def build_scripted_fake_llm(scripts: dict[str, dict[str, Any]]) -> "FakeLLM":
    """Build a `FakeLLM` whose responder dispatches by judgment-schema registration name.

    `scripts` keys are JUDGMENT_SCHEMAS registration keys (e.g. ``"suitability"``,
    ``"no_exploitation"``); values are the response payload for that schema. The returned
    FakeLLM raises a clear error if the engine asks for a schema not covered by the script —
    important for catching missing scripts when a policy gains a new judgment clause.

    Shared between the eval framework and the test conftest so both layers script the rail the
    same way.
    """
    from nspk.judgments import JUDGMENT_SCHEMAS

    by_class_name: dict[str, BaseModel] = {}
    for reg_name, payload in scripts.items():
        try:
            entry = JUDGMENT_SCHEMAS[reg_name]
        except KeyError as exc:
            raise KeyError(
                f"Scripted FakeLLM references unknown judgment schema {reg_name!r}. "
                f"Registered: {sorted(JUDGMENT_SCHEMAS)}"
            ) from exc
        by_class_name[entry.schema.__name__] = entry.schema.model_validate(payload)

    def responder(*, system: str, user: str, schema: type[BaseModel]) -> BaseModel:
        try:
            return by_class_name[schema.__name__]
        except KeyError as exc:
            raise KeyError(
                f"Scripted FakeLLM has no response for {schema.__name__}. "
                f"Scripts cover: {sorted(by_class_name)}"
            ) from exc

    return FakeLLM(responder=responder)


class FakeLLM:
    """Test-time judgment-rail client. Returns scripted typed claims; never makes network calls.

    Two modes:
      - `response=<BaseModel>` : return this instance on every call (coerced into the requested
                                  schema if it's a different type — useful for asserting that the
                                  typed-claim contract holds even when the model is "wrong but
                                  well-typed").
      - `responder=callable`  : invoked with (system=, user=, schema=); returns a BaseModel.

    A FakeLLM that returns `SuitabilityClaim(suitable="true", ...)` on a case where the right
    answer is `false` is the canonical wrong-but-conformant fixture.
    """

    def __init__(
        self,
        *,
        response: BaseModel | None = None,
        responder: Callable[..., BaseModel] | None = None,
    ):
        if response is None and responder is None:
            raise ValueError("FakeLLM needs either `response` or `responder`.")
        self._response = response
        self._responder = responder
        self.calls: list[dict[str, Any]] = []

    def emit_claim(self, *, system: str, user: str, schema: type[T]) -> T:
        self.calls.append({"system": system, "user": user, "schema": schema.__name__})
        if self._responder is not None:
            obj = self._responder(system=system, user=user, schema=schema)
        else:
            assert self._response is not None
            obj = self._response
        if isinstance(obj, schema):
            return obj
        return schema.model_validate(obj.model_dump())
