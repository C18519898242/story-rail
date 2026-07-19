from typing import Any

from openai import OpenAI

from storyrail.config import AIConfig
from storyrail.errors import ProviderError
from storyrail.providers.base import GenerationRequest


class OpenAICompatibleProvider:
    def __init__(self, config: AIConfig, client: Any | None = None) -> None:
        self._config = config
        if client is not None:
            self._client = client
            return

        client_options: dict[str, Any] = {"api_key": config.api_key}
        if config.base_url:
            client_options["base_url"] = config.base_url
        self._client = OpenAI(**client_options)

    def generate(self, request: GenerationRequest) -> str:
        try:
            response = self._client.chat.completions.create(
                model=self._config.model,
                max_tokens=800,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
            )
        except Exception as error:
            raise ProviderError("AI Provider 请求失败") from error

        if not response.choices:
            raise ProviderError("AI Provider 返回了空文本")
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ProviderError("AI Provider 返回了空文本")
        return content.strip()
