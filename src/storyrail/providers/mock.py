from storyrail.providers.base import GenerationRequest


class MockProvider:
    def generate(self, request: GenerationRequest) -> str:
        return request.fallback_text
