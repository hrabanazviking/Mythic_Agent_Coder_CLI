# Provider Negotiation & Normalization (Slices 041–049)

The `mythic_agent.providers` package now negotiates provider-specific
wire shapes instead of forcing one shape on every backend. All
negotiation works on in-memory shapes — no network is touched — and
every function raises `ProviderError` (never raw `ValueError` /
`KeyError`) on malformed input.

## Structured output (`structured_output`)

```python
from mythic_agent.providers import structured_output

fragment = structured_output.negotiate(provider, schema, name="answer")
# merge into chat(): provider.chat(messages, **fragment)
```

- OpenAI-family providers get a native `response_format`
  `json_schema` fragment; `ollama` gets `{"format": schema}`;
  `google` gets a `generation_config` fragment
  (`response_mime_type` + `response_schema`), which
  `GoogleProvider.chat()` passes through to `generate_content`.
- Providers without native `json_mode` (e.g. `anthropic`) raise from
  `negotiate()` — use `prepare()` instead, which appends a JSON-schema
  system instruction and returns an empty fragment.
- `parse_json(provider, text)` decodes strictly for native providers
  and strips ```json fences / finds the first balanced `{...}` for
  the fallback path.

## Vision (`vision`)

```python
from mythic_agent.providers import vision

parts = [{"type": "text", "text": "What is this?"},
         {"type": "image_url",
          "image_url": {"url": "data:image/png;base64,..."}}]
payload = vision.normalize(provider, parts)          # or on_unsupported="strip"
```

Wire shapes: OpenAI `image_url` parts for the OpenAI family,
Anthropic `image`/`source` blocks, Gemini inline-data parts, and
message-level `images` for Ollama. Providers without vision either
raise (`on_unsupported="raise"`, default) or drop image parts and
report `payload.dropped` (`"strip"`).

## Reasoning (`reasoning`)

```python
from mythic_agent.providers.reasoning import ReasoningConfig, negotiate

fragment = negotiate(provider, ReasoningConfig(mode="on", budget_tokens=8000))
```

`mode` is `"off"` (always `{}`), `"on"`, or `"low"`/`"medium"`/`"high"`.
OpenAI gets `reasoning_effort`, OpenRouter `reasoning.effort`,
Anthropic `thinking` (default budget 1024 when unset), DeepSeek
reasoner models get `{}` (reasoning is model-inherent). Everything
else raises `ProviderError`.

## Streaming (`streaming`)

```python
from mythic_agent.providers.streaming import iter_events, collect

events = iter_events(provider, raw_lines)   # SSE or Ollama NDJSON -> StreamEvent
text = collect(events, cancel=lambda: stop_requested)
```

Events: `text`, `tool_call_delta`, `usage`, `error`, `done`.
`collect()` raises `CancelledStream` (with partial text) when the
cancel callable fires, and `ProviderError` on provider-sent error
frames. Generators are close-safe: `gen.close()` mid-stream discards
partial state without raising.

## Usage (`usage`)

```python
from mythic_agent.providers import usage

record = usage.normalize(provider, raw_body, fallback_text=reply_text)
```

Maps OpenAI / Anthropic (incl. cached tokens) / Google
`usageMetadata` / Ollama eval-count shapes into `ChatUsage`. With no
backend metadata, tokens are heuristically estimated (`len // 4`)
and the record is flagged `estimated=True`.

## Cost ledger (`cost_ledger`)

```python
from mythic_agent.providers.cost_ledger import CostLedger

ledger = CostLedger(workspace_root)   # persists .mythic/cost_ledger.json
call = ledger.record(provider.name, model, usage_record)
```

Prices `usage × model price` against the shared `core.costs` table
(vendor prefixes stripped; cached tokens bill at the input rate).
Unknown models bill `$0` and are listed by `unpriced_models()`.
Corrupt ledger files load as empty rather than crashing.

## Health scoring (`health`)

```python
from mythic_agent.providers.health import ProviderHealth

health = ProviderHealth()
health.record("openai", ok=True, latency_s=0.42)
score = health.score("openai")   # 0..1, recency-weighted
```

Sliding window (default 200 samples) with exponential recency decay
(default 300 s half-life). Score blends success rate (65%) and a
latency factor (35%). Unknown providers score 0.5 (neutral).

## Failover (`failover`)

```python
from mythic_agent.providers.failover import FailoverRouter, FailoverPolicy

router = FailoverRouter(FailoverPolicy(max_attempts=3))
result = router.chat(["openai", "anthropic"], messages,
                     provider_factory=lambda name: get_provider(name))
```

Tries candidates healthiest-first (each at most once per call —
same-provider retries stay in the adapter's transport layer),
records every attempt into the health tracker, and opens a circuit
breaker after `breaker_threshold` consecutive failures (skipped while
open, half-open after `cooldown_s`). All candidates failing raises
`FailoverExhausted` with per-provider errors.

## Conformance (`conformance`)

```python
from mythic_agent.providers import conformance

report = conformance.run_conformance(provider)   # fake fixtures only
print(conformance.render(report))
conformance.write_report(report, "reports/openai.json")
```

Eleven contract checks (capabilities, message validation, chat via
the injected fake transport, iter-chunks contract, structured
output, vision, reasoning, usage, cost, health, streaming parsers)
with `passed` / `failed` / `skipped` status each. `run_pantheon()`
runs the whole provider list. Live transports are never fired: the
chat check skips providers without an injected fake `transport=`
seam.
