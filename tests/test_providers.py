from types import SimpleNamespace

import pytest

from storyrail.config import AIConfig
from storyrail.errors import ProviderError
from storyrail.providers.anthropic import AnthropicProvider
from storyrail.providers.base import GenerationRequest
from storyrail.providers.factory import create_provider
from storyrail.providers.mock import MockProvider
from storyrail.providers.openai_compatible import OpenAICompatibleProvider


def test_mock_returns_fixed_result():
    request = GenerationRequest(
        system_prompt="system",
        user_prompt="user",
        fallback_text="固定结果",
    )

    assert MockProvider().generate(request) == "固定结果"


def generation_request():
    return GenerationRequest(
        system_prompt="系统约束",
        user_prompt="生成演出",
        fallback_text="固定结果",
    )


class RecordingAnthropicMessages:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class RecordingAnthropicClient:
    def __init__(self, response=None, error=None):
        self.messages = RecordingAnthropicMessages(response=response, error=error)


class RecordingOpenAICompletions:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return self.response


class RecordingOpenAIClient:
    def __init__(self, response=None, error=None):
        completions = RecordingOpenAICompletions(response=response, error=error)
        self.chat = SimpleNamespace(completions=completions)


def test_anthropic_provider_sends_expected_request_and_joins_text_blocks():
    response = SimpleNamespace(
        content=[
            SimpleNamespace(type="thinking", thinking="internal"),
            SimpleNamespace(type="text", text="第一段"),
            SimpleNamespace(type="text", text="第二段"),
        ]
    )
    client = RecordingAnthropicClient(response=response)
    config = AIConfig("anthropic", "https://example.test", "key", "model-a")

    result = AnthropicProvider(config, client=client).generate(generation_request())

    assert result == "第一段\n第二段"
    assert client.messages.calls == [
        {
            "model": "model-a",
            "max_tokens": 800,
            "system": "系统约束",
            "messages": [{"role": "user", "content": "生成演出"}],
        }
    ]


def test_openai_provider_sends_expected_request_and_returns_content():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="生成文本"))]
    )
    client = RecordingOpenAIClient(response=response)
    config = AIConfig("openai", "https://example.test", "key", "model-o")

    result = OpenAICompatibleProvider(config, client=client).generate(
        generation_request()
    )

    assert result == "生成文本"
    assert client.chat.completions.calls == [
        {
            "model": "model-o",
            "max_tokens": 800,
            "messages": [
                {"role": "system", "content": "系统约束"},
                {"role": "user", "content": "生成演出"},
            ],
        }
    ]


@pytest.mark.parametrize(
    "provider",
    [
        AnthropicProvider(
            AIConfig("anthropic", api_key="key", model="model"),
            client=RecordingAnthropicClient(error=RuntimeError("network")),
        ),
        OpenAICompatibleProvider(
            AIConfig("openai", api_key="key", model="model"),
            client=RecordingOpenAIClient(error=RuntimeError("network")),
        ),
    ],
)
def test_provider_errors_are_converted(provider):
    with pytest.raises(ProviderError, match="AI Provider 请求失败"):
        provider.generate(generation_request())


@pytest.mark.parametrize(
    "provider",
    [
        AnthropicProvider(
            AIConfig("anthropic", api_key="key", model="model"),
            client=RecordingAnthropicClient(response=SimpleNamespace(content=[])),
        ),
        OpenAICompatibleProvider(
            AIConfig("openai", api_key="key", model="model"),
            client=RecordingOpenAIClient(
                response=SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="  "))]
                )
            ),
        ),
    ],
)
def test_empty_provider_responses_are_rejected(provider):
    with pytest.raises(ProviderError, match="空文本"):
        provider.generate(generation_request())


def test_factory_selects_each_provider():
    assert isinstance(create_provider(AIConfig("mock")), MockProvider)
    assert isinstance(
        create_provider(AIConfig("anthropic", api_key="key", model="model")),
        AnthropicProvider,
    )
    assert isinstance(
        create_provider(AIConfig("openai", api_key="key", model="model")),
        OpenAICompatibleProvider,
    )
