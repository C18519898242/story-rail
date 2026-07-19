from pathlib import Path

from storyrail.engine import StoryEngine
from storyrail.loader import load_script


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1] / "examples" / "rainy-night" / "script.json"
)


def follow_path(choice_indexes):
    engine = StoryEngine(load_script(SCRIPT_PATH))
    for index in choice_indexes:
        engine.choose(index)
    return engine.current_node


def test_sample_has_expected_size_and_endings():
    script = load_script(SCRIPT_PATH)
    endings = [node for node in script.nodes.values() if node.ending]
    assert 5 <= len(script.nodes) <= 10
    assert len(endings) >= 2


def test_all_sample_endings_are_reachable():
    assert follow_path([0, 0, 0]).id == "dawn_ending"
    assert follow_path([0, 1, 0]).id == "safe_ending"
    assert follow_path([1, 1]).id == "lonely_ending"
