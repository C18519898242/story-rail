import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

from storyrail.errors import ConfigurationError


@dataclass(frozen=True)
class AIConfig:
    provider: str
    base_url: str | None = None
    api_key: str | None = None
    model: str | None = None


def _value(environ: Mapping[str, str], name: str) -> str | None:
    value = environ.get(name)
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


def _required(value: str | None, variable_name: str) -> str:
    if value is None:
        raise ConfigurationError(f"缺少环境变量：{variable_name}")
    return value


def load_ai_config(
    environ: Mapping[str, str] | None = None,
    dotenv_path: str | Path = ".env",
) -> AIConfig:
    dotenv_environ: Mapping[str, str] = {}
    if environ is None:
        dotenv_environ = {
            name: value
            for name, value in dotenv_values(dotenv_path=dotenv_path).items()
            if value is not None
        }
        environ = {**os.environ, **dotenv_environ}

    provider = (_value(environ, "AI_PROVIDER") or "mock").lower()
    if provider not in {"mock", "openai", "anthropic"}:
        raise ConfigurationError(
            "AI_PROVIDER 必须是以下值之一：mock, openai, anthropic"
        )

    if provider == "mock":
        return AIConfig(provider="mock")

    if provider == "openai":
        return AIConfig(
            provider="openai",
            base_url=_value(environ, "OPENAI_BASE_URL"),
            api_key=_required(_value(environ, "OPENAI_API_KEY"), "OPENAI_API_KEY"),
            model=_required(_value(environ, "OPENAI_MODEL"), "OPENAI_MODEL"),
        )

    anthropic_key = (
        _value(dotenv_environ, "ANTHROPIC_API_KEY")
        or _value(dotenv_environ, "ANTHROPIC_AUTH_TOKEN")
        or _value(environ, "ANTHROPIC_API_KEY")
        or _value(environ, "ANTHROPIC_AUTH_TOKEN")
    )
    return AIConfig(
        provider="anthropic",
        base_url=_value(environ, "ANTHROPIC_BASE_URL"),
        api_key=_required(
            anthropic_key,
            "ANTHROPIC_API_KEY 或 ANTHROPIC_AUTH_TOKEN",
        ),
        model=_required(_value(environ, "ANTHROPIC_MODEL"), "ANTHROPIC_MODEL"),
    )
