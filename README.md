# StoryRail（故事轨道）

StoryRail 是一个 AI 驱动的文字冒险游戏实验项目。

它可以把小说整理成可游玩的结构化剧本。玩家在终端中扮演小说里的角色，通过预先生成的固定选项参与剧情；AI 根据玩家的选择实时生成对白、动作和场景描写，但关键事件、状态变化和剧情去向始终由剧本控制。

> 剧本决定故事往哪里走，AI 决定这一段如何演出来。

## 为什么做这个项目

完全由 AI 在游玩时生成剧情，虽然自由度很高，但容易出现人物性格变化、设定冲突、剧情无法收束和存档难以复现等问题。

StoryRail 采用更可控的方式：

1. 在剧本生成阶段分析小说，生成角色、世界观、章节、剧情节点和玩家选项。
2. 在游玩阶段只展示已经写入剧本的选项。
3. 玩家选择后，由剧情引擎确定固定结果和下一个节点。
4. AI 只在剧本限定范围内生成具体演出文本。

这样既保留 AI 互动内容的不确定性，也能确保故事不会偏离主线。

## 核心体验

```text
读取当前剧情节点
        ↓
显示场景和固定选项
        ↓
玩家在终端输入选择
        ↓
剧情引擎应用固定结果和状态变化
        ↓
AI 生成对白、动作和过渡描写
        ↓
保存记录并进入下一个固定节点
```

AI 无权自行修改下一个节点、关键剧情结果或核心游戏状态。如果 AI 调用失败，游戏仍应能够根据剧本继续运行。

## 当前可玩版本

当前版本提供一个确定性 CLI 剧情引擎和原创示例《雨夜相遇》。默认使用离线 mock Provider，直接显示固定结果；配置 OpenAI-compatible 或 Anthropic-compatible Provider 后，AI 会在不改变剧情跳转的前提下实时生成对白和场景描写。

## 快速启动（Windows PowerShell）

### 运行要求

- Windows PowerShell。
- Python 3.11 或更高版本。
- 能够安装 `pyproject.toml` 中声明的 Python 依赖。

可以使用下面的命令查看 Python 版本：

```powershell
python --version
```

### 第一次启动

打开 PowerShell，执行：

```powershell
cd C:\src\story-rail
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m storyrail.cli .\examples\rainy-night\script.json
```

### 以后再次启动

虚拟环境和项目依赖已经安装后，不需要重复安装，执行下面两行即可：

```powershell
cd C:\src\story-rail
.\.venv\Scripts\python.exe -m storyrail.cli .\examples\rainy-night\script.json
```

启动成功后，终端会显示场景和编号选项：

```text
《雨夜相遇》

深夜的雨笼罩着青石街……
1. 停下来询问她是否需要帮助
2. 装作没有看见，继续回家
请选择：
```

输入 `1` 或 `2` 后按回车，剧情就会进入对应的固定节点。可以随时按 `Ctrl+C` 退出游戏。是否联网由 `.env` 中的 Provider 配置决定；当前版本不会创建存档。

### 配置 AI Provider

CLI 启动时自动读取项目根目录的 `.env`，不需要传入 `--ai`。如果 `.env` 不存在或没有设置 `AI_PROVIDER`，默认使用不联网的 mock：

```dotenv
AI_PROVIDER=mock
```

可以复制 `.env.example` 后修改：

```powershell
Copy-Item .env.example .env
```

Anthropic-compatible 配置示例：

```dotenv
AI_PROVIDER=anthropic
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=replace-with-your-key
ANTHROPIC_MODEL=deepseek-v4-pro[1m]
```

也可以用标准变量 `ANTHROPIC_API_KEY` 代替 `ANTHROPIC_AUTH_TOKEN`；两者同时存在时优先使用 `ANTHROPIC_API_KEY`。

OpenAI-compatible 配置示例：

```dotenv
AI_PROVIDER=openai
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=replace-with-your-key
OPENAI_MODEL=deepseek-v4-pro
```

支持的 `AI_PROVIDER` 值为：

- `mock`：默认，不联网，直接显示剧本固定结果。
- `anthropic`：使用 Anthropic-compatible Messages API。
- `openai`：使用 OpenAI-compatible Chat Completions API。

项目 `.env` 中的配置优先于同名系统环境变量；如果 `.env` 没有设置某个变量，才会读取系统环境变量。真实密钥只保存在被 Git 忽略的 `.env` 中，不要写入 `.env.example`、README 或剧本文件。

### 运行自动化测试（可选）

测试使用 pytest。第一次运行测试前安装测试依赖：

```powershell
cd C:\src\story-rail
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

测试全部通过时会看到类似输出：

```text
42 passed
```

## 剧本格式资源

项目提供两份可提交、可复用的剧本格式资源：

- `schemas/script.schema.json`：使用 JSON Schema Draft 2020-12 描述 StoryRail v1 剧本的数据结构、必填字段和字段类型。
- `templates/script.json`：一个可以直接被当前加载器读取的最小两节点剧本，供人工编写或小说脚本生成程序复制后修改。

完整的可玩内容可以参考 `examples/rainy-night/script.json`。三者的职责不同：

```text
Schema   定义什么结构是合法的
Template 提供生成新剧本时使用的最小骨架
Example  展示一个完整可玩的实际故事
```

小说脚本生成程序应把 Schema 和 Template 一起提供给 AI，要求 AI 只返回符合该结构的 JSON。生成结果建议先保存到 `content/scripts/`，再交给 StoryRail 加载器读取。

当前阶段没有引入 JSON Schema 校验库或新的校验命令。运行时仍由现有 Python 加载器检查基本结构、节点 ID 和 `next` 引用。

## 第一阶段目标：CLI 最小可玩版本

第一阶段只实现本地命令行版本，不开发前端、不启动长期运行的后端服务，也不引入数据库。

计划实现：

- 从本地 TXT 或 Markdown 小说读取原始内容。
- 使用 AI 提取世界观、角色和章节信息。
- 生成包含剧情节点、固定选项和跳转关系的 JSON 剧本。
- 在 CLI 中选择玩家扮演的角色并开始游戏。
- 使用数字选择剧情选项。
- 根据剧本结果调用 AI 生成受约束的实时回复。
- 使用 JSON 保存当前游戏状态。
- 使用 JSONL 追加记录完整游玩过程。
- 提供基础剧本校验，检查无效引用、缺失节点和无法到达的分支。

第一阶段暂不实现：

- 图形界面或网页界面。
- 用户注册、登录和云端同步。
- 多人游戏。
- 数据库。
- AI 在运行时创建新的永久剧情分支。
- 复杂的战斗、装备或数值养成系统。

## 设计原则

### 1. 剧情结果固定，表达方式可变

每个选项分为玩家可见内容和剧本内部约束。

玩家只需要知道自己当前可以采取什么行动，例如“停下来帮助她”或“假装没有看见”。选择之后可能造成的结果不应提前展示，以免泄露剧情或削弱选择时的不确定感。

剧本内部则必须为每个选项预先确定：

- 该行动最终造成的剧情结果。
- 需要更新的游戏状态。
- 接下来进入的剧情节点。

这些内部信息不会直接展示给玩家。AI 根据玩家选择生成对白、动作和过程描写，让固定结果自然发生，但不能改变剧本规定的结果、状态变化和节点跳转。

### 2. 剧情引擎是最终裁判

只有剧情引擎可以修改当前节点、人物关系、物品、标记和其他游戏状态。AI 的输出属于演出内容，不直接写入核心状态。

### 3. 剧本生成和游戏运行分离

生成剧本属于离线创作流程，可以反复生成、人工检查和修改。游玩时只读取已经确认的剧本，不临时创造新的选项。

### 4. 文件优先

所有内容使用普通文件保存，便于阅读、备份、比较、手工修改和调试。只有在未来出现多用户、并发写入或复杂查询需求时，才考虑引入数据库。

### 5. 核心逻辑与界面分离

CLI 只负责输入和输出，不包含剧情规则。未来增加网页或桌面前端时，可以复用同一个剧情引擎、剧本格式和存档格式。

## 建议技术栈

### 当前阶段

- **语言：Python**
  - 适合文本处理、AI 接口调用和快速构建 CLI。
  - 优先使用标准库，减少早期依赖。
- **CLI：`argparse` 或轻量命令封装**
  - MVP 可以先使用 Python 标准库 `argparse`。
  - 当命令增多后，再考虑 Typer 和 Rich 改善命令组织与终端显示。
- **数据格式：JSON + JSONL**
  - JSON 保存配置、角色、剧本节点和存档。
  - JSONL 追加保存每一次玩家选择和 AI 回复。
- **数据模型：Python `dataclasses`**
  - 初期使用标准库完成模型定义和基础校验。
  - 当剧本结构稳定、校验需求增加后，可引入 Pydantic。
- **AI 接口：可替换的 Provider 适配层**
  - 游戏引擎不直接依赖某一家模型服务。
  - OpenAI-compatible、Anthropic 和测试用模拟模型在内部使用统一的调用接口。
  - 第一阶段只实现实际会使用的协议，不为了完整性一次接入所有模型。
- **测试：pytest**
  - 重点测试剧情跳转、状态更新、存档恢复和剧本校验。
- **项目管理：`pyproject.toml`**
  - 统一管理项目元数据、依赖、测试和 CLI 入口。

### 为什么暂时不用数据库

单机 CLI 只有一个玩家进程，文件已经能够满足需求：

- 剧本主要是只读数据。
- 存档体积较小。
- 游玩记录可以顺序追加。
- JSON 可以直接查看和手工修复。
- 文件可以使用本地比较或备份工具追踪变化；需要公开的脱敏示例可以单独纳入 Git。

写入存档时应采用“写入临时文件，再原子替换正式文件”的方式，避免程序中断导致存档损坏。

## JSON 与 JSONL 使用约定

本项目同时使用 JSON 和 JSONL。两者用途不同，不应混用。

### JSON 用于保存完整状态

JSON 文件是一个完整的 JSON 对象或数组，适合保存需要整体读取和整体更新的数据，例如：

- 世界观和角色设定。
- 章节与剧情节点。
- 游戏配置。
- 当前存档状态。

例如，一个 JSON 存档可以写成：

```json
{
  "current_node": "scene_003",
  "player_role": "林默",
  "variables": {
    "suhe_trust": 2
  }
}
```

### JSONL 用于保存按时间追加的记录

JSONL 是 **JSON Lines** 的缩写，也常被称为 **NDJSON（Newline-Delimited JSON）**。它不是在一个 JSON 数组中保存所有记录，而是每一行保存一个独立、完整的 JSON 对象。

例如，下面是一个包含三条游戏互动记录的 `.jsonl` 文件：

```jsonl
{"sequence":1,"node":"scene_001","choice":"帮助她","ai_reply":"林默停下脚步，向她伸出了手。"}
{"sequence":2,"node":"scene_002","choice":"询问她的名字","ai_reply":"她迟疑片刻，低声说自己叫苏荷。"}
{"sequence":3,"node":"scene_003","choice":"带她离开","ai_reply":"两人冒着雨向街道尽头走去。"}
```

JSONL 格式必须遵守以下约定：

- 文件扩展名使用 `.jsonl`。
- 文件编码统一使用 UTF-8。
- 每一个非空行必须是一个能够独立解析的 JSON 对象。
- 一个对象必须完整写在同一行，不能跨行缩进。
- 文件最外层不能使用 `[` 和 `]` 包裹成数组。
- 两条记录之间不加逗号。
- 每条记录写完后追加一个换行符，包括文件中的最后一条记录。
- 读取时可以忽略空行，但写入时不主动产生空行。
- JSONL 文件只用于追加历史事件，不作为当前游戏状态的唯一来源。

换句话说，JSONL 中的每一行都是合法 JSON，但整个 JSONL 文件本身不是一个普通的 JSON 对象或 JSON 数组，不能直接使用一次 `json.load()` 读取全部内容。

### 为什么游玩记录使用 JSONL

玩家每完成一次选择，就可以直接在文件末尾增加一行，不需要读取并重写之前的全部记录。这有几个好处：

- 追加操作简单，适合不断增长的游玩历史。
- 文件很大时仍然可以逐行读取，不必全部载入内存。
- 可以快速定位某一次选择或某一行格式错误。
- 某一行损坏时，之前已经写入的其他行通常仍然可以读取。
- 以后可以方便地导入日志分析工具或转换成其他格式。

### StoryRail 中的职责划分

```text
JSON：  保存“游戏现在是什么状态”
JSONL：保存“游戏之前依次发生过什么”
```

建议每条游玩记录至少包含：

- `sequence`：会话内递增的事件序号。
- `node`：做出选择时所在的剧情节点 ID。
- `choice_id`：玩家选择的稳定 ID。
- `choice_text`：当时展示给玩家的选项文本。
- `ai_reply`：AI 最终生成并展示的内容。

可以根据需要增加时间、会话 ID、模型信息和错误状态，但不应把 API 密钥、完整系统提示词或其他敏感数据写入记录。

### Python 标准库读写方式

Python 不需要第三方 JSONL 库。使用标准库 `json` 逐行解析即可：

```python
import json
from pathlib import Path


def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                yield json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"JSONL 第 {line_number} 行格式错误"
                ) from error
```

追加一条记录时，先把对象序列化成单行 JSON，再写入换行符：

```python
import json
from pathlib import Path


def append_jsonl(path: Path, record: dict) -> None:
    with path.open("a", encoding="utf-8") as file:
        line = json.dumps(record, ensure_ascii=False)
        file.write(line + "\n")
```

当要求 AI 直接生成 JSONL 时，应明确说明：

> 输出 JSONL（JSON Lines）格式。每行输出一个完整的 JSON 对象，不要使用最外层数组，不要在行尾添加逗号，不要跨行格式化对象，也不要输出 Markdown 代码围栏或解释文字。

## 建议项目结构

```text
story-rail/
├─ README.md
├─ pyproject.toml
├─ src/
│  └─ storyrail/
│     ├─ cli.py                 # CLI 入口和终端交互
│     ├─ models.py              # 剧本、选项和存档数据模型
│     ├─ engine.py              # 确定性剧情状态机
│     ├─ generator.py           # 小说到结构化剧本的生成流程
│     ├─ narrator.py            # 组织上下文并生成演出文本
│     ├─ storage.py             # JSON/JSONL 读写和存档管理
│     ├─ validator.py           # 剧本引用和连通性校验
│     └─ providers/
│        ├─ base.py             # Provider 接口契约，不调用网络
│        ├─ mock.py             # 无需联网的测试实现
│        ├─ openai_compatible.py # OpenAI-compatible API 实现
│        └─ anthropic.py        # Anthropic API 实现
├─ content/                      # 本地作品内容，默认不提交 Git
│  ├─ source/                   # 原始小说 TXT/Markdown
│  ├─ scripts/
│  │  ├─ manifest.json          # 作品信息和入口节点
│  │  ├─ world.json             # 世界观和规则
│  │  ├─ characters.json        # 角色设定
│  │  └─ chapters/              # 按章节保存的剧情节点
│  └─ prompts/                  # 剧本生成和运行时提示词
├─ examples/                     # 可公开提交的脱敏示例内容
├─ saves/                       # 本地存档，默认不提交 Git
├─ transcripts/                 # 游玩过程记录，默认不提交 Git
└─ tests/
   ├─ fixtures/                 # 小型测试剧本
   ├─ test_engine.py
   ├─ test_storage.py
   └─ test_validator.py
```

项目早期不必一次创建所有文件。建议先实现一条最短路径：手写一个小型 JSON 剧本，完成“读取节点 → 选择 → AI 演出 → 跳转 → 存档”，确认游戏体验成立后，再开发小说剧本生成器。

### Provider 目录的含义

这里的 Provider 指“模型服务适配器”，不是一个额外的后端服务。

`base.py` 不包含真实 API 地址、密钥或网络请求。它只定义 StoryRail 内部需要的统一 Python 接口，例如“接收生成请求并返回生成结果”。可以使用 Python `Protocol` 表达这个约定：

```python
from typing import Protocol


class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str:
        ...
```

其他文件负责把不同厂商的调用方式转换成这个统一接口：

- `mock.py`：返回固定文本，供剧情引擎测试使用，不访问网络。
- `openai_compatible.py`：调用 OpenAI-compatible 接口。许多云端服务和本地模型服务支持这种请求格式。
- `anthropic.py`：调用 Anthropic 自己的消息接口，因为它与 OpenAI-compatible 接口并不相同。

这里所说的是 **OpenAI-compatible API**，不是 **OpenAPI**。OpenAPI 是描述 HTTP API 的通用规范，与模型厂商的请求格式不是同一个概念。

不再使用含义不明确的 `api.py`。如果第一阶段只使用一种模型接口，只创建 `base.py`、`mock.py` 和对应的一个真实实现即可；等真正需要第二种协议时再添加，避免过度设计。

## Git 提交约定

`content/` 默认不提交 Git。这个目录可能包含受版权保护的小说原文、生成中的完整剧本、针对具体作品的提示词以及尚未准备公开的内容。

以下本地数据应加入 `.gitignore`：

```gitignore
/content/
/saves/
/transcripts/
.env
```

以下内容可以正常提交：

- `src/` 中的程序代码。
- `tests/fixtures/` 中为测试专门编写的小型虚构数据。
- `examples/` 中经过确认、允许公开的脱敏示例。
- README、项目配置和通用文档。

如果需要分享某个本地作品，不要直接取消对整个 `content/` 的忽略。应先确认版权和隐私，将允许公开的最小内容复制到 `examples/`，再单独提交。

## 剧本节点示例

```json
{
  "id": "chapter01_scene03",
  "context": "林默在雨夜遇见受伤的苏荷。",
  "player_role": "林默",
  "choices": [
    {
      "id": "help",
      "text": "停下来帮助她",
      "result": "林默救助苏荷，两人建立初步信任。",
      "effects": {
        "suhe_trust": 1
      },
      "next": "chapter01_scene04_help"
    },
    {
      "id": "leave",
      "text": "假装没有看见",
      "result": "林默暂时离开，但随后因愧疚返回。",
      "effects": {
        "guilt": 1
      },
      "next": "chapter01_scene04_return"
    }
  ]
}
```

运行时提供给 AI 的内容应包括当前场景、角色设定、玩家选择、固定结果、必要历史和下一节点的衔接要求。提示词必须明确禁止 AI 增加与固定结果冲突的事实。

## 存档示例

```json
{
  "script_id": "example-novel",
  "current_node": "chapter01_scene04_help",
  "player_role": "林默",
  "variables": {
    "suhe_trust": 1,
    "guilt": 0
  },
  "history": [
    {
      "node": "chapter01_scene03",
      "choice": "help"
    }
  ]
}
```

完整 AI 回复不一定全部写进存档，可以追加写入单独的 JSONL 游玩记录。存档只保留恢复游戏所需的最小状态。

## 预期 CLI

以下命令只是目标接口，尚未实现：

```bash
# 从小说生成剧本
storyrail generate content/source/example.txt

# 校验生成的剧本
storyrail validate content/scripts/example

# 开始新游戏
storyrail play content/scripts/example

# 从存档继续
storyrail play --save saves/example-save.json
```

## 推荐开发顺序

### 阶段一：最小剧情引擎

- 手写一个包含 5～10 个节点的测试剧本。
- 完成节点读取、选项显示、跳转和存档。
- 使用 Mock Provider 返回固定演出文本，暂时不调用真实 AI。

### 阶段二：AI 演出

- 接入一个模型 Provider。
- 设计运行时上下文和约束提示词。
- 实现超时、重试和无 AI 时的降级文本。
- 验证 AI 不会改变剧本规定的结果。

### 阶段三：小说剧本生成

- 分阶段提取世界观、角色、章节和事件。
- 生成固定选项与节点跳转。
- 校验引用、入口、终点和不可达节点。
- 支持人工修改后重新校验。

### 阶段四：改善创作与游玩体验

- 更友好的终端显示。
- 剧本生成进度和错误报告。
- 多存档管理。
- 对话历史压缩和上下文预算控制。

## 未来引入前端

CLI 版本稳定后，可以在不修改核心剧本规则的前提下增加应用层接口。

建议演进路线：

```text
当前：CLI → 剧情引擎 → 文件存储 → AI Provider

未来：Web 前端 → HTTP/SSE API → 剧情引擎 → 文件或数据库 → AI Provider
```

### 未来后端

- 使用 FastAPI 为现有 Python 核心提供 HTTP API。
- 使用 SSE 流式返回 AI 生成文本；只有确实需要双向实时通信时才引入 WebSocket。
- 保持剧情引擎为独立模块，不依赖 FastAPI。
- 单机或个人版本可以继续使用 JSON 文件。

### 未来 Web 前端

- 使用 React + TypeScript。
- 如果只需要独立游戏界面，可以选择 Vite 构建单页应用。
- 如果需要官网、内容展示和服务端页面，再评估 Next.js。
- 前端只负责展示场景、选项、角色状态和流式文本，不自行计算剧情结果。

### 未来桌面版本

如果需要发布独立桌面应用，可以在 Web 界面成熟后评估 Tauri 等桌面封装方案。核心游戏逻辑仍保留在 Python 服务或迁移为可嵌入模块，具体方案届时根据发布平台决定。

### 什么时候需要数据库

出现以下需求后再引入数据库：

- 多用户账号和云端存档。
- 多设备同步。
- 多个进程同时写入状态。
- 在线剧本库、搜索、评论或发布系统。
- 需要运营分析和复杂查询。

如果只是本地单机版，没有必要为了“以后可能用到”提前增加数据库。

## 项目边界

StoryRail 的目标不是让 AI 完全替代作者，也不是生成没有终点的聊天内容。它希望提供一种介于传统视觉小说和自由角色扮演之间的体验：

- 作者或生成器控制世界、角色、关键事件和结局。
- 玩家通过有限但有意义的选择参与故事。
- AI 让每一次互动在措辞、情绪和细节上有所不同。
- 相同剧本可以被验证、修改、复现和长期保存。

## 当前状态

项目处于概念验证阶段，尚未开始实现。第一项里程碑是完成一个不依赖真实 AI、可以从头走到结局的 CLI 小剧本。
