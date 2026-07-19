import pytest

from storyrail.config import load_ai_config
from storyrail.errors import ConfigurationError


def test_provider_defaults_to_mock():
    config = load_ai_config({})

    assert config.provider == "mock"
    assert config.api_key is None
    assert config.model is None


def test_provider_name_is_normalized():
    config = load_ai_config({"AI_PROVIDER": "  MoCk  "})

    assert config.provider == "mock"


def test_invalid_provider_is_rejected():
    with pytest.raises(ConfigurationError, match="mock, openai, anthropic"):
        load_ai_config({"AI_PROVIDER": "unknown"})


def test_anthropic_auth_token_is_supported():
    config = load_ai_config(
        {
            "AI_PROVIDER": "anthropic",
            "ANTHROPIC_BASE_URL": "https://example.test/anthropic",
            "ANTHROPIC_AUTH_TOKEN": "auth-token",
            "ANTHROPIC_MODEL": "test-model",
        }
    )

    assert config.provider == "anthropic"
    assert config.base_url == "https://example.test/anthropic"
    assert config.api_key == "auth-token"
    assert config.model == "test-model"


def test_anthropic_api_key_takes_precedence():
    config = load_ai_config(
        {
            "AI_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "api-key",
            "ANTHROPIC_AUTH_TOKEN": "auth-token",
            "ANTHROPIC_MODEL": "test-model",
        }
    )

    assert config.api_key == "api-key"


@pytest.mark.parametrize(
    ("environ", "missing_name"),
    [
        ({"AI_PROVIDER": "anthropic", "ANTHROPIC_MODEL": "model"}, "ANTHROPIC_API_KEY"),
        ({"AI_PROVIDER": "anthropic", "ANTHROPIC_AUTH_TOKEN": "key"}, "ANTHROPIC_MODEL"),
        ({"AI_PROVIDER": "openai", "OPENAI_MODEL": "model"}, "OPENAI_API_KEY"),
        ({"AI_PROVIDER": "openai", "OPENAI_API_KEY": "key"}, "OPENAI_MODEL"),
    ],
)
def test_real_providers_require_credentials_and_model(environ, missing_name):
    with pytest.raises(ConfigurationError, match=missing_name):
        load_ai_config(environ)


def test_openai_configuration_is_loaded():
    config = load_ai_config(
        {
            "AI_PROVIDER": "openai",
            "OPENAI_BASE_URL": "https://example.test/v1",
            "OPENAI_API_KEY": "test-key",
            "OPENAI_MODEL": "test-model",
        }
    )

    assert config.provider == "openai"
    assert config.base_url == "https://example.test/v1"
    assert config.api_key == "test-key"
    assert config.model == "test-model"
