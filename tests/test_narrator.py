from storyrail.narrator import Narrator, build_generation_request


class RecordingProvider:
    def __init__(self, result="生成文本"):
        self.result = result
        self.requests = []

    def generate(self, request):
        self.requests.append(request)
        return self.result


def narration_values():
    return {
        "story_title": "测试故事",
        "scene_text": "你站在门前。",
        "choice_text": "推开门",
        "fixed_result": "门缓缓打开。",
        "next_scene_text": "晨光落进房间。",
    }


def test_generation_request_contains_story_constraints():
    request = build_generation_request(**narration_values())

    assert "中文" in request.system_prompt
    assert "不能改变固定结果" in request.system_prompt
    assert "不要创建新的选项" in request.system_prompt
    assert "测试故事" in request.user_prompt
    assert "你站在门前。" in request.user_prompt
    assert "推开门" in request.user_prompt
    assert "门缓缓打开。" in request.user_prompt
    assert "晨光落进房间。" in request.user_prompt
    assert request.fallback_text == "门缓缓打开。"


def test_narrator_passes_request_to_provider():
    provider = RecordingProvider()

    result = Narrator(provider).narrate(**narration_values())

    assert result == "生成文本"
    assert len(provider.requests) == 1
