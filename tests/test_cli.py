from storyrail.cli import main, play
from storyrail.errors import ProviderError
from storyrail.loader import parse_script


def make_script():
    return parse_script(
        {
            "schema_version": 1,
            "id": "cli-test",
            "title": "终端测试",
            "start_node": "start_internal",
            "nodes": [
                {
                    "id": "start_internal",
                    "text": "你站在门前。",
                    "choices": [
                        {
                            "id": "open_internal",
                            "text": "推开门",
                            "result": "门缓缓打开。",
                            "next": "ending_internal",
                        }
                    ],
                },
                {
                    "id": "ending_internal",
                    "text": "晨光落进房间。",
                    "ending": True,
                },
            ],
        }
    )


class FixedProvider:
    def __init__(self, text):
        self.text = text

    def generate(self, _request):
        return self.text


class FailingProvider:
    def generate(self, _request):
        raise ProviderError("network")


def run_with_inputs(values, provider=None):
    inputs = iter(values)
    outputs = []
    exit_code = play(
        make_script(),
        provider=provider,
        input_fn=lambda _prompt: next(inputs),
        output_fn=outputs.append,
    )
    return exit_code, "\n".join(outputs)


def test_play_reaches_ending_without_leaking_internal_ids():
    exit_code, output = run_with_inputs(["1"])
    assert exit_code == 0
    assert "《终端测试》" in output
    assert "1. 推开门" in output
    assert "门缓缓打开。" in output
    assert "晨光落进房间。" in output
    assert "故事结束" in output
    assert "start_internal" not in output
    assert "ending_internal" not in output
    assert "open_internal" not in output


def test_play_reprompts_for_non_numeric_and_out_of_range_input():
    exit_code, output = run_with_inputs(["不是数字", "2", "1"])
    assert exit_code == 0
    assert output.count("请输入有效的选项编号。") == 2


def test_play_displays_provider_narration_instead_of_fixed_result():
    exit_code, output = run_with_inputs(["1"], FixedProvider("AI 生成的演出。"))

    assert exit_code == 0
    assert "AI 生成的演出。" in output
    assert "门缓缓打开。" not in output


def test_play_falls_back_to_fixed_result_when_provider_fails():
    exit_code, output = run_with_inputs(["1"], FailingProvider())

    assert exit_code == 0
    assert "AI 生成失败，使用固定剧情结果。" in output
    assert "门缓缓打开。" in output
    assert "晨光落进房间。" in output


def test_main_loads_config_and_creates_provider(monkeypatch):
    calls = {}
    script = make_script()
    provider = FixedProvider("AI")

    monkeypatch.setattr("storyrail.cli.load_ai_config", lambda: "config")

    def fake_create_provider(config):
        calls["provider_config"] = config
        return provider

    monkeypatch.setattr("storyrail.cli.create_provider", fake_create_provider)
    monkeypatch.setattr("storyrail.cli.load_script", lambda path: script)

    def fake_play(received_script, provider=None):
        calls["script"] = received_script
        calls["provider"] = provider
        return 0

    monkeypatch.setattr("storyrail.cli.play", fake_play)

    assert main(["story.json"]) == 0
    assert calls["provider_config"] == "config"
    assert calls["script"] is script
    assert calls["provider"] is provider
