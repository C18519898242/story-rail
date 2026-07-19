# StoryRail 可配置 AI Provider 设计

日期：2026-07-19

## 目标

让 StoryRail 在启动 CLI 时自动读取项目根目录的 `.env`，根据 `AI_PROVIDER` 选择叙事文本生成方式。未配置时默认使用 `mock`，保持当前离线玩法；配置 `openai` 或 `anthropic` 时，通过对应兼容接口实时生成玩家选择之后的对白和场景描写。

剧情引擎仍然是剧情状态的唯一裁判。Provider 只能演绎已经确定的选择、固定结果和下一场景，不能修改节点跳转。

## 本阶段范围

实现：

- 从 `.env` 和系统环境变量读取 Provider 配置。
- `mock`、`openai`、`anthropic` 三种 Provider。
- 默认 `mock`，CLI 不增加 `--ai` 参数。
- 玩家选择后实时生成演出文本。
- API 或配置失败时提供清楚的错误或安全回退。
- `.env.example` 和 README 配置说明。
- 使用真实 Anthropic-compatible DeepSeek 接口做一次小规模冒烟测试。

暂不实现：

- 流式输出。
- 对话历史压缩或长期记忆。
- AI 动态创建选项、节点或游戏状态。
- 自动重试、限流队列或请求缓存。
- GUI 配置页面。

## 环境变量

### Provider 选择

```dotenv
AI_PROVIDER=mock
```

允许值：

- `mock`：默认值，不访问网络，直接返回剧本固定结果。
- `openai`：使用 OpenAI-compatible Chat Completions API。
- `anthropic`：使用 Anthropic-compatible Messages API。

Provider 名称忽略首尾空白并转成小写。其他值视为配置错误，CLI 显示错误并以非零状态退出。

### OpenAI-compatible 配置

```dotenv
AI_PROVIDER=openai
OPENAI_BASE_URL=https://api.deepseek.com
OPENAI_API_KEY=replace-with-your-key
OPENAI_MODEL=deepseek-v4-pro
```

`OPENAI_API_KEY` 和 `OPENAI_MODEL` 必填。`OPENAI_BASE_URL` 可选；未提供时由 OpenAI SDK 使用自身默认地址。

### Anthropic-compatible 配置

```dotenv
AI_PROVIDER=anthropic
ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic
ANTHROPIC_AUTH_TOKEN=replace-with-your-key
ANTHROPIC_MODEL=deepseek-v4-pro[1m]
```

认证字段支持：

1. 优先读取 `ANTHROPIC_API_KEY`。
2. 如果没有，再读取 `ANTHROPIC_AUTH_TOKEN`。

读取到的值统一作为 Anthropic SDK 的 `api_key` 参数。`ANTHROPIC_MODEL` 必填；`ANTHROPIC_BASE_URL` 可选，未提供时由 Anthropic SDK 使用自身默认地址。

`.env` 已由 `.gitignore` 排除。仓库只提交不含真实密钥的 `.env.example`。

## 组件设计

### 配置模块

`config.py` 使用 `python-dotenv` 加载当前工作目录的 `.env`，且不覆盖已经存在的系统环境变量。

它产生统一的 `AIConfig`：

- `provider`：`mock`、`openai` 或 `anthropic`。
- `base_url`：可选 API 基础地址。
- `api_key`：真实认证信息，只保存在内存中。
- `model`：真实模型名称。

`mock` 不要求其他配置。真实 Provider 缺少必填变量时抛出 `ConfigurationError`。

### Provider 接口

`providers/base.py` 定义统一请求和协议：

```python
@dataclass(frozen=True)
class GenerationRequest:
    system_prompt: str
    user_prompt: str
    fallback_text: str


class ModelProvider(Protocol):
    def generate(self, request: GenerationRequest) -> str:
        ...
```

`system_prompt` 和 `user_prompt` 由叙事层构造；`fallback_text` 是剧本固定结果，供 mock 模式直接返回。真实 Provider 只负责发送提示词并返回非空文本。SDK 异常、空响应或无法识别的响应统一转换成 `ProviderError`。

### Mock Provider

`providers/mock.py` 不访问网络，直接返回 `GenerationRequest.fallback_text`，保持现有 CLI 输出完全不变。CLI 和叙事层不需要判断当前 Provider 的具体类型。

### Anthropic Provider

`providers/anthropic.py` 使用官方 `anthropic` Python SDK：

- `Anthropic(api_key=..., base_url=...)`
- `client.messages.create(...)`
- 非流式请求。
- 默认最大输出 800 tokens。
- 收集响应中所有 `type == "text"` 的内容块。

### OpenAI-compatible Provider

`providers/openai_compatible.py` 使用官方 `openai` Python SDK：

- `OpenAI(api_key=..., base_url=...)`
- `client.chat.completions.create(...)`
- 非流式请求。
- 默认最大输出 800 tokens。
- 读取第一个 choice 的 message content。

### Provider Factory

`providers/factory.py` 根据 `AIConfig.provider` 创建对应实例。CLI 和剧情逻辑不直接判断厂商名称。

## 叙事约束

`narrator.py` 负责构造提示词。系统提示要求模型：

- 使用中文输出。
- 只输出玩家可见的对白、动作和场景描写。
- 不输出分析、节点 ID、字段名或 Markdown 代码块。
- 不创建新选项。
- 不改变固定结果。
- 让生成内容自然衔接下一场景。
- 控制篇幅，避免替玩家决定新的关键行动。

用户提示包含当前场景、玩家选择、固定结果和下一场景衔接要求。

## CLI 数据流

```text
CLI 启动
→ 加载 .env 和 AIConfig
→ Provider Factory 创建 Provider
→ 加载剧本
→ 展示场景和固定选项
→ 玩家选择
→ 剧情引擎应用固定结果并进入下一节点
→ Narrator 将选择、固定结果和下一场景交给 Provider
→ 显示生成文本
→ 展示下一节点
```

CLI 不提供 `--ai`。切换 Provider 只修改 `.env` 后重新启动游戏。

## 错误处理

- 配置的 Provider 名称无效：启动失败，显示允许值。
- 真实 Provider 缺少密钥或模型：启动失败，指出缺少的环境变量，不显示其他敏感值。
- SDK 请求失败或返回空文本：本次互动显示“AI 生成失败，使用固定剧情结果。”，然后显示 `fixed_result`，剧情继续。
- `mock`：始终返回 `fixed_result`，不会产生网络请求。

## 依赖

新增运行时依赖：

- `python-dotenv`
- `anthropic`
- `openai`

Provider SDK 延迟到对应 Provider 被创建时才实例化，但三个包作为项目正式依赖统一安装，降低用户配置复杂度。

## 测试策略

自动化测试不得访问真实网络：

- 配置测试覆盖默认 mock、三种合法值、无效值和缺失变量。
- Mock Provider 测试确认原样返回固定结果。
- Anthropic 和 OpenAI Provider 使用注入的假客户端测试请求字段、模型选择、文本提取和异常转换。
- Narrator 测试确认提示词包含固定结果和下一场景约束。
- CLI 测试覆盖默认 mock 行为与 Provider 失败回退。
- 原有加载器、引擎和示例测试继续通过。

完成自动化测试后，使用本地 `.env` 发起一次最大输出受限的 Anthropic-compatible 请求，确认真实连接、认证、模型和响应解析正常。测试输出不记录密钥。
