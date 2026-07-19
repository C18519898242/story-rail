import pytest

from storyrail.engine import StoryEngine
from storyrail.errors import GameFinishedError, InvalidChoiceError
from storyrail.loader import parse_script


def make_script():
    return parse_script(
        {
            "schema_version": 1,
            "id": "engine-test",
            "title": "引擎测试",
            "start_node": "start",
            "nodes": [
                {
                    "id": "start",
                    "text": "开始。",
                    "choices": [
                        {
                            "id": "go",
                            "text": "前进",
                            "result": "你向前走去。",
                            "next": "ending",
                        }
                    ],
                },
                {"id": "ending", "text": "结束。", "ending": True},
            ],
        }
    )


def test_engine_starts_at_entry_node():
    engine = StoryEngine(make_script())
    assert engine.current_node.id == "start"
    assert engine.is_finished is False


def test_choose_returns_result_and_moves_to_next_node():
    engine = StoryEngine(make_script())
    result = engine.choose(0)
    assert result == "你向前走去。"
    assert engine.current_node.id == "ending"
    assert engine.is_finished is True


@pytest.mark.parametrize("index", [-1, 1])
def test_invalid_choice_does_not_change_node(index):
    engine = StoryEngine(make_script())
    with pytest.raises(InvalidChoiceError, match="无效选项"):
        engine.choose(index)
    assert engine.current_node.id == "start"


def test_cannot_choose_after_ending():
    engine = StoryEngine(make_script())
    engine.choose(0)
    with pytest.raises(GameFinishedError, match="故事已经结束"):
        engine.choose(0)
