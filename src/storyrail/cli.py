import argparse
import sys
from collections.abc import Callable, Sequence

from storyrail.config import load_ai_config
from storyrail.engine import StoryEngine
from storyrail.errors import ProviderError, StoryRailError
from storyrail.loader import load_script
from storyrail.models import Node, Script
from storyrail.narrator import Narrator
from storyrail.providers.base import ModelProvider
from storyrail.providers.factory import create_provider
from storyrail.providers.mock import MockProvider


def _read_choice_index(
    node: Node,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], None],
) -> int:
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
        return selected_index


def play(
    script: Script,
    provider: ModelProvider | None = None,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    engine = StoryEngine(script)
    narrator = Narrator(provider or MockProvider())
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

        selected_index = _read_choice_index(node, input_fn, output_fn)
        selected_choice = node.choices[selected_index]
        fixed_result = engine.choose(selected_index)
        output_fn("")
        try:
            narration = narrator.narrate(
                story_title=script.title,
                scene_text=node.text,
                choice_text=selected_choice.text,
                fixed_result=fixed_result,
                next_scene_text=engine.current_node.text,
            )
        except ProviderError:
            output_fn("AI 生成失败，使用固定剧情结果。")
            narration = fixed_result
        output_fn(narration)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="运行 StoryRail JSON 剧本")
    parser.add_argument("script", help="剧本 JSON 文件路径")
    args = parser.parse_args(argv)
    try:
        config = load_ai_config()
        provider = create_provider(config)
        script = load_script(args.script)
        return play(script, provider=provider)
    except StoryRailError as error:
        print(f"错误：{error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
