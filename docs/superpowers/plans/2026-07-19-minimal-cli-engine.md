# Minimal CLI Story Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, AI-free CLI story engine that loads a validated JSON script and lets a player reach one of multiple endings through fixed choices.

**Architecture:** A loader converts UTF-8 JSON into immutable dataclasses and validates all structural and cross-node references before play. A pure story engine owns node transitions without terminal or filesystem access, while a thin CLI adapter handles input and output. An original eight-node example proves the complete path without AI, saves, JSONL, databases, or a frontend.

**Tech Stack:** Python 3.11+, standard-library `json`, `dataclasses`, `argparse`, and pytest for tests.

## Global Constraints

- Script schema version is exactly `1`.
- The first playable script contains 5–10 nodes and at least two endings.
- Players see scene text and choice text, never node IDs or internal `next` values.
- Fixed choice results are displayed directly in this phase; no AI provider is implemented.
- No database, save system, JSONL transcript, state variables, or frontend code is introduced.
- All committed example and fixture content is original and safe to publish.

---

## File Structure

- Create `pyproject.toml`: package metadata, Python floor, pytest configuration.
- Replace `src/storyrail/.gitkeep` with `src/storyrail/__init__.py`: package metadata.
- Create `src/storyrail/models.py`: immutable script, node, and choice dataclasses.
- Create `src/storyrail/errors.py`: user-facing project exception types.
- Create `src/storyrail/loader.py`: JSON reading, parsing, and complete script validation.
- Create `src/storyrail/engine.py`: deterministic in-memory node transition engine.
- Create `src/storyrail/cli.py`: argument parsing and terminal play loop.
- Create `tests/test_loader.py`: loader and validation behavior.
- Create `tests/test_engine.py`: state transition behavior.
- Create `tests/test_cli.py`: terminal interaction behavior.
- Create `examples/rainy-night/script.json`: original eight-node playable story.
- Create `tests/test_sample_story.py`: end-to-end verification of every ending path.
- Modify `README.md`: add installation, quick-start, and MVP behavior.

### Task 1: Script models, loading, and validation

**Files:**
- Create: `pyproject.toml`
- Delete: `src/storyrail/.gitkeep`
- Create: `src/storyrail/__init__.py`
- Create: `src/storyrail/models.py`
- Create: `src/storyrail/errors.py`
- Create: `src/storyrail/loader.py`
- Create: `tests/test_loader.py`

**Interfaces:**
- Produces: `Choice`, `Node`, and `Script` dataclasses from `storyrail.models`.
- Produces: `ScriptLoadError` and `ScriptValidationError` from `storyrail.errors`.
- Produces: `load_script(path: str | Path) -> Script` and `parse_script(data: object) -> Script` from `storyrail.loader`.

- [ ] **Step 1: Add project metadata and write failing loader tests**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "storyrail"
version = "0.1.0"
description = "A deterministic CLI story engine for controlled AI-assisted interactive fiction."
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

Create `tests/test_loader.py`:

```python
import json

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
```

- [ ] **Step 2: Run the tests and verify the missing package failure**

Run:

```bash
python -m pytest tests/test_loader.py -v
```

Expected: collection fails with `ModuleNotFoundError: No module named 'storyrail.errors'`.

- [ ] **Step 3: Implement immutable models and project errors**

Delete `src/storyrail/.gitkeep` and create `src/storyrail/__init__.py`:

```python
"""StoryRail deterministic interactive fiction engine."""

__version__ = "0.1.0"
```

Create `src/storyrail/models.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Choice:
    id: str
    text: str
    result: str
    next_node: str


@dataclass(frozen=True)
class Node:
    id: str
    text: str
    choices: tuple[Choice, ...] = ()
    ending: bool = False


@dataclass(frozen=True)
class Script:
    schema_version: int
    id: str
    title: str
    start_node: str
    nodes: dict[str, Node]
```

Create `src/storyrail/errors.py`:

```python
class StoryRailError(Exception):
    """Base class for expected StoryRail failures."""


class ScriptLoadError(StoryRailError):
    """Raised when a script file cannot be read or decoded."""


class ScriptValidationError(StoryRailError):
    """Raised when decoded script data violates schema rules."""
```

- [ ] **Step 4: Implement strict JSON parsing and reference validation**

Create `src/storyrail/loader.py`:

```python
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
    if version != 1 or isinstance(version, bool):
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
```

- [ ] **Step 5: Run loader tests and the full suite**

Run:

```bash
python -m pytest tests/test_loader.py -v
python -m pytest -q
```

Expected: all loader tests pass and the suite exits with status `0`.

- [ ] **Step 6: Commit the loader deliverable**

```bash
git add pyproject.toml src/storyrail tests/test_loader.py
git commit -m "feat: add validated JSON script loader"
```

### Task 2: Deterministic story engine

**Files:**
- Modify: `src/storyrail/errors.py`
- Create: `src/storyrail/engine.py`
- Create: `tests/test_engine.py`

**Interfaces:**
- Consumes: `Script` and `Node` from `storyrail.models`.
- Produces: `InvalidChoiceError` and `GameFinishedError` from `storyrail.errors`.
- Produces: `StoryEngine(script: Script)`, `.current_node -> Node`, `.is_finished -> bool`, and `.choose(index: int) -> str`.

- [ ] **Step 1: Write failing engine tests**

Create `tests/test_engine.py`:

```python
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
```

- [ ] **Step 2: Run the engine tests and verify import failure**

Run `python -m pytest tests/test_engine.py -v`.

Expected: collection fails because `storyrail.engine` does not exist.

- [ ] **Step 3: Add engine errors and minimal implementation**

Append to `src/storyrail/errors.py`:

```python
class InvalidChoiceError(StoryRailError):
    """Raised when a choice index is not available on the current node."""


class GameFinishedError(StoryRailError):
    """Raised when a choice is attempted after reaching an ending."""
```

Create `src/storyrail/engine.py`:

```python
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
```

- [ ] **Step 4: Run engine tests and full suite**

Run:

```bash
python -m pytest tests/test_engine.py -v
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the engine deliverable**

```bash
git add src/storyrail/errors.py src/storyrail/engine.py tests/test_engine.py
git commit -m "feat: add deterministic story engine"
```

### Task 3: Terminal play loop

**Files:**
- Create: `src/storyrail/cli.py`
- Create: `tests/test_cli.py`

**Interfaces:**
- Consumes: `load_script()` and `StoryEngine`.
- Produces: `play(script: Script, input_fn: Callable[[str], str], output_fn: Callable[[str], None]) -> int`.
- Produces: `main(argv: Sequence[str] | None = None) -> int`.

- [ ] **Step 1: Write failing CLI behavior tests**

Create `tests/test_cli.py`:

```python
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
```

- [ ] **Step 2: Run CLI tests and verify import failure**

Run `python -m pytest tests/test_cli.py -v`.

Expected: collection fails because `storyrail.cli` does not exist.

- [ ] **Step 3: Implement the terminal adapter**

Create `src/storyrail/cli.py`:

```python
import argparse
import sys
from collections.abc import Callable, Sequence

from storyrail.engine import StoryEngine
from storyrail.errors import StoryRailError
from storyrail.loader import load_script
from storyrail.models import Script


def play(
    script: Script,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    engine = StoryEngine(script)
    output_fn(f"《{script.title}》")

    while True:
        node = engine.current_node
        output_fn("")
        output_fn(node.text)
        if engine.is_finished:
            output_fn("")
            output_fn("—— 故事结束 ——")
            return 0

        for number, choice in enumerate(node.choices, start=1):
            output_fn(f"{number}. {choice.text}")

        while True:
            raw_choice = input_fn("请选择：").strip()
            try:
                selected_index = int(raw_choice) - 1
            except ValueError:
                output_fn("请输入有效的选项编号。")
                continue
            if selected_index < 0 or selected_index >= len(node.choices):
                output_fn("请输入有效的选项编号。")
                continue
            break

        output_fn("")
        output_fn(engine.choose(selected_index))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行 StoryRail JSON 剧本")
    parser.add_argument("script", help="剧本 JSON 文件路径")
    args = parser.parse_args(argv)
    try:
        script = load_script(args.script)
        return play(script)
    except StoryRailError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run CLI tests and full suite**

Run:

```bash
python -m pytest tests/test_cli.py -v
python -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 5: Commit the CLI deliverable**

```bash
git add src/storyrail/cli.py tests/test_cli.py
git commit -m "feat: add interactive terminal play loop"
```

### Task 4: Original sample story and end-to-end documentation

**Files:**
- Delete: `examples/.gitkeep`
- Create: `examples/rainy-night/script.json`
- Delete: `tests/fixtures/.gitkeep`
- Create: `tests/test_sample_story.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: public loader and engine interfaces from Tasks 1 and 2.
- Produces: a publishable eight-node story with three reachable endings.
- Produces: documented commands for test and manual play.

- [ ] **Step 1: Write failing sample-story integration tests**

Create `tests/test_sample_story.py`:

```python
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
```

- [ ] **Step 2: Run the sample test and verify missing file failure**

Run `python -m pytest tests/test_sample_story.py -v`.

Expected: tests fail with `ScriptLoadError` because `examples/rainy-night/script.json` does not exist.

- [ ] **Step 3: Add an original eight-node story**

Create `examples/rainy-night/script.json`:

```json
{
  "schema_version": 1,
  "id": "rainy-night",
  "title": "雨夜相遇",
  "start_node": "rainy_night",
  "nodes": [
    {
      "id": "rainy_night",
      "text": "深夜的雨笼罩着青石街。你正准备回家，忽然看见一名陌生少女靠在路灯下，手臂上有一道正在渗血的伤口。",
      "choices": [
        {
          "id": "stop_to_help",
          "text": "停下来询问她是否需要帮助",
          "result": "你撑伞走近。少女虽然戒备，却没有拒绝你的帮助。",
          "next": "under_eaves"
        },
        {
          "id": "walk_away",
          "text": "装作没有看见，继续回家",
          "result": "你从她身边走过，但雨声始终压不住心里的不安。",
          "next": "regret"
        }
      ]
    },
    {
      "id": "under_eaves",
      "text": "你扶她躲到屋檐下。她自称苏荷，只说自己不能去官署，也不肯解释伤口从何而来。",
      "choices": [
        {
          "id": "find_shelter",
          "text": "先带她去附近的旧旅店避雨",
          "result": "你尊重她的沉默，带她穿过小巷，来到仍亮着灯的旧旅店。",
          "next": "old_inn"
        },
        {
          "id": "find_doctor",
          "text": "坚持先找一位可信的医生",
          "result": "你说服她先处理伤口，并敲开了老医生家的后门。",
          "next": "clinic"
        }
      ]
    },
    {
      "id": "regret",
      "text": "走出半条街后，你发现她的血迹正被雨水冲进排水沟。身后的街道安静得令人不安。",
      "choices": [
        {
          "id": "turn_back",
          "text": "立刻折返回去",
          "result": "你转身跑回路灯下，终于在她倒下前扶住了她。",
          "next": "under_eaves"
        },
        {
          "id": "keep_walking",
          "text": "告诉自己不要惹麻烦",
          "result": "你没有回头，脚步却越来越沉。",
          "next": "lonely_ending"
        }
      ]
    },
    {
      "id": "old_inn",
      "text": "旅店老板认出了苏荷腕上的旧徽记，却没有声张，只把钥匙和一封落满灰尘的信放到柜台上。",
      "choices": [
        {
          "id": "trust_innkeeper",
          "text": "相信老板，让苏荷读信",
          "result": "信中留下了一条安全离城的路线，也解开了苏荷多年的误会。",
          "next": "dawn_ending"
        },
        {
          "id": "leave_inn",
          "text": "不冒险停留，带苏荷从后门离开",
          "result": "你们避开追踪者，在老医生的接应下穿过了城门。",
          "next": "safe_ending"
        }
      ]
    },
    {
      "id": "clinic",
      "text": "老医生替苏荷包扎伤口，并认出追踪她的人来自城外。他打开一条通往河岸的隐秘通道。",
      "choices": [
        {
          "id": "take_tunnel",
          "text": "陪苏荷沿密道离开小镇",
          "result": "你们赶在追踪者到来前抵达河岸，登上了清晨的第一艘船。",
          "next": "safe_ending"
        }
      ]
    },
    {
      "id": "dawn_ending",
      "text": "天亮时，苏荷带着那封信踏上回乡的路。她在桥头回身向你挥手，而你知道这场相遇已经改变了两个人的命运。",
      "ending": true
    },
    {
      "id": "safe_ending",
      "text": "晨雾掩住了你们离开的方向。苏荷终于放下戒备，第一次向你讲起她真正寻找的东西。",
      "ending": true
    },
    {
      "id": "lonely_ending",
      "text": "第二天，路灯下只剩一把被雨水打翻的旧伞。你再也没有见过那名少女，也始终不知道昨夜错过了什么。",
      "ending": true
    }
  ]
}
```

- [ ] **Step 4: Run integration tests and manually play one route**

Run:

```bash
python -m pytest tests/test_sample_story.py -v
python -m pytest -q
python -m storyrail.cli examples/rainy-night/script.json
```

For manual play, enter `1`, `1`, `1`. Expected: the story reaches `dawn_ending` without displaying that internal ID.

- [ ] **Step 5: Add a concise quick-start section to README**

Add after the introductory core flow:

````markdown
## 当前可玩版本

当前版本提供一个不依赖 AI 的确定性 CLI 剧情引擎和原创示例《雨夜相遇》。固定结果会直接显示，后续阶段再由 AI 生成受约束的演出文本。

### 运行测试

```bash
python -m pytest -q
```

### 开始游戏

```bash
$env:PYTHONPATH = "src"
python -m storyrail.cli examples/rainy-night/script.json
```

按照终端提示输入选项编号即可。程序不会联网，也不会创建存档。
````

- [ ] **Step 6: Run final checks**

Run:

```bash
python -m pytest -q
python -m compileall -q src tests
git diff --check
```

Expected: pytest exits with status `0`, compileall prints no errors, and `git diff --check` prints nothing.

- [ ] **Step 7: Commit the playable MVP**

```bash
git add README.md examples/rainy-night/script.json tests/test_sample_story.py
git commit -m "feat: add playable rainy night sample"
```
