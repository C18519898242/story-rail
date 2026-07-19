# Configurable AI Providers Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make StoryRail automatically select mock, OpenAI-compatible, or Anthropic-compatible narration from `.env`, while keeping plot transitions deterministic and falling back safely when generation fails.

**Architecture:** `config.py` turns environment variables into one validated `AIConfig`; a factory creates a provider behind one `ModelProvider` protocol. `narrator.py` converts story context into a constrained `GenerationRequest`, while the CLI applies the fixed transition first and uses generated text only as presentation.

**Tech Stack:** Python 3.11+, `python-dotenv`, Anthropic Python SDK, OpenAI Python SDK, pytest.

## Global Constraints

- `AI_PROVIDER` accepts `mock`, `openai`, or `anthropic`; missing configuration means `mock`.
- CLI has no `--ai` flag and reads `.env` automatically without overriding system environment variables.
- Mock mode performs no network request and returns the fixed result unchanged.
- AI providers cannot modify choices, state, or node transitions.
- Provider failures fall back to the fixed result and do not stop play.
- Automated tests never access the network.
- Real credentials exist only in ignored `.env`; committed `.env.example` contains placeholders.
- First release is non-streaming with an 800-token maximum response.

---

## File Structure

- Modify `pyproject.toml`: add three runtime dependencies.
- Modify `.gitignore`: already ignores `.env`; no rule change required.
- Create `.env.example`: document all provider variables without secrets.
- Create `src/storyrail/config.py`: dotenv loading and provider-specific validation.
- Modify `src/storyrail/errors.py`: add `ConfigurationError` and `ProviderError`.
- Replace `src/storyrail/providers/.gitkeep` with `base.py`, `mock.py`, `anthropic.py`, `openai_compatible.py`, `factory.py`, and `__init__.py`.
- Create `src/storyrail/narrator.py`: constrained prompt construction and provider invocation.
- Modify `src/storyrail/cli.py`: automatic factory creation and per-choice narration.
- Create `tests/test_config.py`, `tests/test_providers.py`, and `tests/test_narrator.py`.
- Modify `tests/test_cli.py`: generated narration and failure fallback coverage.
- Modify `README.md`: provider configuration and startup instructions.

### Task 1: Configuration and mock provider

**Files:**
- Modify: `pyproject.toml`
- Create: `.env.example`
- Modify: `src/storyrail/errors.py`
- Delete: `src/storyrail/providers/.gitkeep`
- Create: `src/storyrail/providers/__init__.py`
- Create: `src/storyrail/providers/base.py`
- Create: `src/storyrail/providers/mock.py`
- Create: `src/storyrail/config.py`
- Test: `tests/test_config.py`
- Test: `tests/test_providers.py`

**Interfaces:**
- Produces `AIConfig(provider: str, base_url: str | None, api_key: str | None, model: str | None)`.
- Produces `load_ai_config(environ: Mapping[str, str] | None = None, dotenv_path: str | Path = ".env") -> AIConfig`.
- Produces `GenerationRequest(system_prompt, user_prompt, fallback_text)` and `ModelProvider.generate(request) -> str`.
- Produces `MockProvider.generate(request) -> request.fallback_text`.

- [ ] **Step 1: Write failing configuration and mock tests**

Create tests that assert:

```python
def test_provider_defaults_to_mock():
    assert load_ai_config({}).provider == "mock"


def test_anthropic_auth_token_is_supported():
    config = load_ai_config({
        "AI_PROVIDER": "anthropic",
        "ANTHROPIC_AUTH_TOKEN": "test-token",
        "ANTHROPIC_MODEL": "test-model",
    })
    assert config.api_key == "test-token"


def test_invalid_provider_is_rejected():
    with pytest.raises(ConfigurationError, match="mock, openai, anthropic"):
        load_ai_config({"AI_PROVIDER": "unknown"})


def test_mock_returns_fixed_result():
    request = GenerationRequest("system", "user", "固定结果")
    assert MockProvider().generate(request) == "固定结果"
```

Also cover whitespace/case normalization, `ANTHROPIC_API_KEY` precedence, missing real-provider keys/models, and OpenAI variables.

- [ ] **Step 2: Verify RED**

Run `python -m pytest tests/test_config.py tests/test_providers.py -v`.

Expected: collection fails because `storyrail.config` and provider modules do not exist.

- [ ] **Step 3: Implement configuration and mock**

Add runtime dependencies:

```toml
dependencies = [
  "anthropic",
  "openai",
  "python-dotenv",
]
```

Define errors:

```python
class ConfigurationError(StoryRailError):
    """Raised when AI provider environment settings are invalid."""


class ProviderError(StoryRailError):
    """Raised when an AI provider cannot produce narration."""
```

Define base types:

```python
@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    fallback_text: str


class ModelProvider(Protocol):
    def generate(self, request: GenerationRequest) -> str: ...
```

`load_ai_config()` calls `load_dotenv(dotenv_path, override=False)` only when `environ` is not supplied, defaults to mock, and validates provider-specific variables exactly as specified in the design.

- [ ] **Step 4: Verify GREEN and commit**

Run:

```bash
python -m pytest tests/test_config.py tests/test_providers.py -v
python -m pytest -q
```

Expected: all tests pass.

Commit:

```bash
git add pyproject.toml .env.example src/storyrail tests/test_config.py tests/test_providers.py
git commit -m "feat: add environment provider configuration"
```

### Task 2: Anthropic and OpenAI-compatible providers

**Files:**
- Create: `src/storyrail/providers/anthropic.py`
- Create: `src/storyrail/providers/openai_compatible.py`
- Create: `src/storyrail/providers/factory.py`
- Modify: `tests/test_providers.py`

**Interfaces:**
- Produces `AnthropicProvider(config: AIConfig, client: object | None = None)`.
- Produces `OpenAICompatibleProvider(config: AIConfig, client: object | None = None)`.
- Produces `create_provider(config: AIConfig) -> ModelProvider`.

- [ ] **Step 1: Write failing provider adapter tests**

Use small recording clients rather than network mocks. For Anthropic, the fake exposes `messages.create(**kwargs)` and returns content blocks with `type="text"`. For OpenAI, the fake exposes `chat.completions.create(**kwargs)` and returns `choices[0].message.content`.

Assert both adapters:

- pass the configured model;
- send system and user prompts in the proper SDK shape;
- set `max_tokens=800`;
- join/return non-empty response text;
- convert SDK exceptions and empty content into `ProviderError`;
- are selected correctly by `create_provider()`.

- [ ] **Step 2: Verify RED**

Run `python -m pytest tests/test_providers.py -v`.

Expected: imports fail because the real adapter and factory modules do not exist.

- [ ] **Step 3: Implement adapters and factory**

Anthropic request:

```python
response = self._client.messages.create(
    model=self._config.model,
    max_tokens=800,
    system=request.system_prompt,
    messages=[{"role": "user", "content": request.user_prompt}],
)
```

OpenAI-compatible request:

```python
response = self._client.chat.completions.create(
    model=self._config.model,
    max_tokens=800,
    messages=[
        {"role": "system", "content": request.system_prompt},
        {"role": "user", "content": request.user_prompt},
    ],
)
```

If no client is injected, construct the appropriate SDK client using `api_key` and optional `base_url`. Catch SDK exceptions at the adapter boundary and raise `ProviderError("AI Provider 请求失败")` without credentials.

- [ ] **Step 4: Verify GREEN and commit**

Run provider tests and the full suite, then commit:

```bash
git add src/storyrail/providers tests/test_providers.py
git commit -m "feat: add OpenAI and Anthropic providers"
```

### Task 3: Narrator and automatic CLI integration

**Files:**
- Create: `src/storyrail/narrator.py`
- Modify: `src/storyrail/cli.py`
- Create: `tests/test_narrator.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- Produces `build_generation_request(story_title, scene_text, choice_text, fixed_result, next_scene_text) -> GenerationRequest`.
- Produces `Narrator(provider: ModelProvider).narrate(...) -> str`.
- Extends `play(script, provider: ModelProvider | None = None, input_fn=input, output_fn=print) -> int`.

- [ ] **Step 1: Write failing narrator and CLI tests**

Assert the generated user prompt contains the current scene, selected action, fixed result, and next scene. Assert a recording provider's output is displayed instead of the raw fixed result. Assert a provider raising `ProviderError` causes the CLI to print a short fallback notice and the fixed result, then continue to the ending.

Update `main()` behavior test by patching `load_ai_config` and `create_provider`, proving startup automatically selects a provider without a CLI option.

- [ ] **Step 2: Verify RED**

Run `python -m pytest tests/test_narrator.py tests/test_cli.py -v`.

Expected: narrator import or new provider behavior assertions fail.

- [ ] **Step 3: Implement constrained narration**

The system prompt requires Chinese, plain narration only, no IDs/analysis/options, no changes to the fixed result, and a natural transition to the next scene. In `play()`, capture the selected `Choice`, call `engine.choose()` first, then narrate using the new current node as `next_scene_text`.

When `provider` is omitted, use `MockProvider`. In `main()`, load config and create the configured provider before calling `play()`.

- [ ] **Step 4: Verify GREEN and commit**

Run narrator/CLI tests and the full suite, then commit:

```bash
git add src/storyrail/narrator.py src/storyrail/cli.py tests/test_narrator.py tests/test_cli.py
git commit -m "feat: narrate fixed story transitions with AI"
```

### Task 4: Documentation, local configuration, and live smoke test

**Files:**
- Modify: `README.md`
- Local only: `.env`

**Interfaces:**
- Documents exact mock, OpenAI-compatible, and Anthropic-compatible configuration.
- Uses the ignored `.env` for one real request without logging credentials.

- [ ] **Step 1: Update README**

Document that CLI automatically loads `.env`, defaults to mock, and switches providers through `AI_PROVIDER`. Include the committed `.env.example`, dependency installation command, and exact CLI startup command with no `--ai`.

- [ ] **Step 2: Create ignored local `.env`**

Write the user-supplied Anthropic-compatible base URL, token, and model plus `AI_PROVIDER=anthropic`. Verify `git check-ignore .env` succeeds before any commit.

- [ ] **Step 3: Install dependencies and run one live smoke request**

Install the project dependencies into `.venv`. Use `load_ai_config()`, `create_provider()`, and one short `GenerationRequest` with a small fixed result. Confirm a non-empty response and print only provider/model/output length, never the token.

- [ ] **Step 4: Final verification**

Run:

```bash
python -m pytest -q
python -m compileall -q src tests
git diff --check
git status --short
```

Expected: all tests pass, compileall and diff check are clean, `.env` is absent from Git status, and only `.idea/` remains unrelated/untracked.

- [ ] **Step 5: Commit documentation**

```bash
git add README.md
git commit -m "docs: explain AI provider configuration"
```
