import pytest

from storyrail.errors import ScriptLoadError, ScriptValidationError
from storyrail.loader import load_script, parse_script


def valid_script_data() -> dict:
    return {
        "schema_version": 1,
        "id": "test-story",
        "title": "测试故事",
        "start_node": "start",
        "nodes": [
            {
                "id": "start",
                "text": "故事开始。",
                "choices": [
                    {
                        "id": "continue",
                        "text": "继续前进",
                        "result": "你继续向前。",
                        "next": "ending",
                    }
                ],
            },
            {"id": "ending", "text": "故事结束。", "ending": True},
        ],
    }


def test_parse_valid_script():
    script = parse_script(valid_script_data())

    assert script.title == "测试故事"
    assert script.start_node == "start"
    assert script.nodes["start"].choices[0].next_node == "ending"
    assert script.nodes["ending"].ending is True


def test_load_script_reports_missing_file(tmp_path):
    with pytest.raises(ScriptLoadError, match="无法读取剧本文件"):
        load_script(tmp_path / "missing.json")


def test_load_script_reports_json_location(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"nodes": [}', encoding="utf-8")

    with pytest.raises(ScriptLoadError, match=r"第 1 行，第 12 列"):
        load_script(path)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data["nodes"].append(data["nodes"][0].copy()), "节点 ID 重复"),
        (lambda data: data.update(start_node="missing"), "入口节点不存在"),
        (
            lambda data: data["nodes"][0]["choices"][0].update(next="missing"),
            "指向不存在的节点",
        ),
        (lambda data: data["nodes"][0].update(choices=[]), "至少包含一个选项"),
        (lambda data: data["nodes"][1].update(choices=[]), "结局节点不能包含 choices"),
    ],
)
def test_rejects_invalid_scripts(mutate, message):
    data = valid_script_data()
    mutate(data)

    with pytest.raises(ScriptValidationError, match=message):
        parse_script(data)
