from storyrail.cli import play
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


def run_with_inputs(values):
    inputs = iter(values)
    outputs = []
    exit_code = play(
        make_script(),
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
