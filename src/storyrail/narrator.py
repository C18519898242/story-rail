from storyrail.providers.base import GenerationRequest, ModelProvider


SYSTEM_PROMPT = """你是 StoryRail 的剧情演出器。
请使用中文，只输出玩家可见的对白、动作和场景描写。
不要输出分析、节点 ID、字段名或 Markdown 代码块。
不要创建新的选项，也不要替玩家决定新的关键行动。
不能改变固定结果，必须让文字自然衔接下一场景。
控制篇幅，保持人物行为和场景连续。"""


def build_generation_request(
    *,
    story_title: str,
    scene_text: str,
    choice_text: str,
    fixed_result: str,
    next_scene_text: str,
) -> GenerationRequest:
    user_prompt = f"""故事标题：{story_title}

当前场景：
{scene_text}

玩家选择：
{choice_text}

必须发生的固定结果：
{fixed_result}

下一场景的衔接目标：
{next_scene_text}

请将玩家选择自然演绎到固定结果，并为下一场景做好衔接。"""
    return GenerationRequest(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt,
        fallback_text=fixed_result,
    )


class Narrator:
    def __init__(self, provider: ModelProvider) -> None:
        self._provider = provider

    def narrate(
        self,
        *,
        story_title: str,
        scene_text: str,
        choice_text: str,
        fixed_result: str,
        next_scene_text: str,
    ) -> str:
        request = build_generation_request(
            story_title=story_title,
            scene_text=scene_text,
            choice_text=choice_text,
            fixed_result=fixed_result,
            next_scene_text=next_scene_text,
        )
        return self._provider.generate(request)
