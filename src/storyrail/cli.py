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
