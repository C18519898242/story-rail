from typing import Any

from anthropic import Anthropic

from storyrail.config import AIConfig
from storyrail.errors import ProviderError
from storyrail.providers.base import GenerationRequest


class AnthropicProvider:
    def __init__(self, config: AIConfig, client: Any | None = None) -> None:
        self._config = config
        if client is not None:
            self._client = client
            return

        client_options: dict[str, Any] = {"api_key": config.api_key}
        if config.base_url:
            client_options["base_url"] = config.base_url
        self._client = Anthropic(**client_options)

    def generate(self, request: GenerationRequest) -> str:
        try:
            response = self._client.messages.create(
                model=self._config.model,
                max_tokens=800,
                system=request.system_prompt,
                messages=[{"role": "user", "content": request.user_prompt}],
            )
        except Exception as error:
            raise ProviderError("AI Provider 请求失败") from error

        text_blocks = [
            block.text.strip()
            for block in response.content
            if getattr(block, "type", None) == "text"
            and isinstance(getattr(block, "text", None), str)
            and block.text.strip()
        ]
        if not text_blocks:
            raise ProviderError("AI Provider 返回了空文本")
        return "\n".join(text_blocks)
