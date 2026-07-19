import json
from pathlib import Path
from typing import Any

from storyrail.errors import ScriptLoadError, ScriptValidationError
from storyrail.models import Choice, Node, Script


def _object(value: Any, context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ScriptValidationError(f"{context} 必须是 JSON 对象")
    return value


def _string(data: dict[str, Any], key: str, context: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ScriptValidationError(f"{context}.{key} 必须是非空字符串")
    return value


def parse_script(data: object) -> Script:
    root = _object(data, "剧本")
    version = root.get("schema_version")
    if type(version) is not int or version != 1:
        raise ScriptValidationError("schema_version 必须是整数 1")

    script_id = _string(root, "id", "剧本")
    title = _string(root, "title", "剧本")
    start_node = _string(root, "start_node", "剧本")
    raw_nodes = root.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ScriptValidationError("剧本.nodes 必须是非空数组")

    nodes: dict[str, Node] = {}
    for node_index, raw_node in enumerate(raw_nodes):
        context = f"nodes[{node_index}]"
        node_data = _object(raw_node, context)
        node_id = _string(node_data, "id", context)
        if node_id in nodes:
            raise ScriptValidationError(f"节点 ID 重复：{node_id}")
        text = _string(node_data, "text", context)
        ending = node_data.get("ending", False)
        if not isinstance(ending, bool):
            raise ScriptValidationError(f"{context}.ending 必须是布尔值")

        if ending:
            if "choices" in node_data:
                raise ScriptValidationError(f"结局节点不能包含 choices：{node_id}")
            choices: tuple[Choice, ...] = ()
        else:
            raw_choices = node_data.get("choices")
            if not isinstance(raw_choices, list) or not raw_choices:
                raise ScriptValidationError(f"普通节点至少包含一个选项：{node_id}")
            parsed_choices: list[Choice] = []
            choice_ids: set[str] = set()
            for choice_index, raw_choice in enumerate(raw_choices):
                choice_context = f"{context}.choices[{choice_index}]"
                choice_data = _object(raw_choice, choice_context)
                choice_id = _string(choice_data, "id", choice_context)
                if choice_id in choice_ids:
                    raise ScriptValidationError(
                        f"节点 {node_id} 的选项 ID 重复：{choice_id}"
                    )
                choice_ids.add(choice_id)
                parsed_choices.append(
                    Choice(
                        id=choice_id,
                        text=_string(choice_data, "text", choice_context),
                        result=_string(choice_data, "result", choice_context),
                        next_node=_string(choice_data, "next", choice_context),
                    )
                )
            choices = tuple(parsed_choices)

        nodes[node_id] = Node(id=node_id, text=text, choices=choices, ending=ending)

    if start_node not in nodes:
        raise ScriptValidationError(f"入口节点不存在：{start_node}")
    for node in nodes.values():
        for choice in node.choices:
            if choice.next_node not in nodes:
                raise ScriptValidationError(
                    f"节点 {node.id} 的选项 {choice.id} 指向不存在的节点："
                    f"{choice.next_node}"
                )

    return Script(
        schema_version=version,
        id=script_id,
        title=title,
        start_node=start_node,
        nodes=nodes,
    )


def load_script(path: str | Path) -> Script:
    script_path = Path(path)
    try:
        with script_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except OSError as error:
        raise ScriptLoadError(f"无法读取剧本文件：{script_path}") from error
    except json.JSONDecodeError as error:
        raise ScriptLoadError(
            f"剧本 JSON 格式错误：第 {error.lineno} 行，第 {error.colno} 列："
            f"{error.msg}"
        ) from error
    return parse_script(data)
