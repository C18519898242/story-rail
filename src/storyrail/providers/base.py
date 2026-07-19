from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    fallback_text: str


class ModelProvider(Protocol):
    def generate(self, request: GenerationRequest) -> str:
        """Generate player-visible narration for a fixed story transition."""
        ...
