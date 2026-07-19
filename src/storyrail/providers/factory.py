from storyrail.config import AIConfig
from storyrail.errors import ConfigurationError
from storyrail.providers.anthropic import AnthropicProvider
from storyrail.providers.base import ModelProvider
from storyrail.providers.mock import MockProvider
from storyrail.providers.openai_compatible import OpenAICompatibleProvider


def create_provider(config: AIConfig) -> ModelProvider:
    if config.provider == "mock":
        return MockProvider()
    if config.provider == "anthropic":
        return AnthropicProvider(config)
    if config.provider == "openai":
        return OpenAICompatibleProvider(config)
    raise ConfigurationError(f"不支持的 AI Provider：{config.provider}")
