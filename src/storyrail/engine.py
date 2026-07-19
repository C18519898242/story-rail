from storyrail.errors import GameFinishedError, InvalidChoiceError
from storyrail.models import Node, Script


class StoryEngine:
    def __init__(self, script: Script) -> None:
        self._script = script
        self._current_node_id = script.start_node

    @property
    def current_node(self) -> Node:
        return self._script.nodes[self._current_node_id]

    @property
    def is_finished(self) -> bool:
        return self.current_node.ending

    def choose(self, index: int) -> str:
        if self.is_finished:
            raise GameFinishedError("故事已经结束，不能继续选择")
        choices = self.current_node.choices
        if index < 0 or index >= len(choices):
            raise InvalidChoiceError(f"无效选项：{index + 1}")
        choice = choices[index]
        self._current_node_id = choice.next_node
        return choice.result
