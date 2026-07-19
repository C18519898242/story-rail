from storyrail.providers.base import GenerationRequest
from storyrail.providers.mock import MockProvider


def test_mock_returns_fixed_result():
    request = GenerationRequest(
        system_prompt="system",
        user_prompt="user",
        fallback_text="固定结果",
    )

    assert MockProvider().generate(request) == "固定结果"
