"""
ReAct Orchestrator 常量定义

简化版本 - 移除调试常量，让LLM完全负责决策
"""


class ToolNames:
    """工具名称常量"""
    REQUIREMENTS_ANALYSIS = "requirements_analysis"
    SHORT_PLANNING = "short_planning"
    RESEARCH = "research"
    ARCHITECTURE_DESIGN = "architecture_design"


class MessageRoles:
    """消息角色常量"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class StateKeys:
    """共享状态键名常量"""
    DIALOGUE_HISTORY = "dialogue_history"
    STRUCTURED_REQUIREMENTS = "structured_requirements"
    CONFIRMATION_DOCUMENT = "confirmation_document"
    RESEARCH_FINDINGS = "research_findings"
    AGENT_DESIGN_DOCUMENT = "agent_design_document"
    CURRENT_STAGE = "current_stage"
    REACT_CYCLE_COUNT = "react_cycle_count"
    USER_INTENT = "user_intent"
    STREAM_CALLBACK = "_stream_callback"


class DefaultValues:
    """默认值常量"""
    MAX_HISTORY_MESSAGES = 6
    DEFAULT_CONFIDENCE = 0.8
    DEFAULT_STAGE = "initialization"
    MAX_TOOL_ARGUMENT_DISPLAY = 3
    TOOL_ARGUMENT_MAX_LENGTH = 47


class ErrorMessages:
    """错误消息常量"""
    REACT_PREP_FAILED = "ReAct preparation failed"
    REACT_EXEC_FAILED = "ReAct execution failed"
    FUNCTION_CALLING_FAILED = "Function calling failed"
    STREAM_FUNCTION_CALLING_FAILED = "Stream function calling failed"
    TOOL_EXECUTION_FAILED = "Tool execution failed"
    JSON_PARSE_FAILED = "JSON解析失败"
    TOOL_VALIDATION_FAILED = "工具参数验证失败"
    GENERIC_ERROR = "抱歉，处理您的请求时遇到了问题，请稍后再试。"


class SystemPrompts:
    """系统提示词常量"""
    FUNCTION_CALLING_SYSTEM_PROMPT = """# 角色
你是一位名叫 "GTPlanner" 的AI项目策略师。

# 核心目标
将用户模糊的想法，转化为一个双方确认过的、范围清晰的项目计划。

# 工具集
- `short_planning`: (核心工具) 根据用户输入，生成一份包含核心功能点的项目范围简报，用于和用户对齐认知。**可以多次使用**来逐步细化和完善项目范围。
- `research`: 针对已确认的需求，调研技术实现方案。
- `architecture_design`: 绘制最终的工程架构图。**此工具会将完整的设计文档输出到文件中**，调用后无需重新输出内容，只需提示用户查看生成的文档即可。

# 核心工作流与规则

1.  **启动**: 收到用户请求后，用一句话简单回应（例如：“好的，正在为您分析…”），然后立即进入静默工作状态。

2.  **分析与执行**:
    *   **如果用户输入明确** (包含具体功能或目标): **立即自主调用 `short_planning` 工具**。如果用户提到了技术疑问或需要技术调研，可以选择性调用 `research`。
    *   **如果用户输入模糊** (例如“做一个聊天软件”): **必须先主动提问**，获取更具体的需求细节后，再调用 `short_planning`。
    *   **重要**: `short_planning` 工具可以**多次使用**。如果用户对初始范围有修改意见，或需要进一步细化，可以再次调用该工具来优化项目范围。

3.  **【关键沟通点：范围确认】**
    这是与用户沟通的最重要环节，必须遵守以下规则：
    *   **【绝对规则】**：在调用 `short_planning` 后，你必须将简报的核心功能点展示给用户，并以**获取用户对“项目范围”的明确同意**为唯一目标。
    *   **【绝对规则】**：在范围被用户确认前，**禁止**主动深入讨论任何 `research` 的技术细节或 `architecture_design` 的架构问题。
    *   **沟通结构指引**: 你的回复应遵循以下模式：
        1.  **陈述事实**: "根据您的想法，我为您梳理了一份核心功能简报。"
        2.  **列出要点**: 清晰列出 `short_planning` 生成的1, 2, 3点核心功能。
        3.  **引导确认**: 提出一个封闭式问题来锁定范围，并强调其重要性。例如："**您看这个范围是否准确？确认这一点后，我们才能高效地进行后续的技术选型。**"
    *   **范围调整**: 如果用户对范围有修改意见，**可以再次调用 `short_planning`** 来生成调整后的范围，直到双方达成一致。

4.  **【授权后推进】**
    *   **一旦用户确认了范围**，这就意味着你获得了“授权”。
    *   立即向用户宣告下一步行动，并调用相应工具。
    *   **话术模板**: "好的，既然范围达成一致。现在可以开始架构设计了。" (然后调用 `architecture_design`)。如果需要技术调研，可以说："下一步，我将为您调研..." (然后调用 `research`)。

5.  **【架构设计完成后】**
    *   **重要**: `architecture_design` 工具执行后会自动生成完整的设计文档并保存到文件中。
    *   **不要重新输出设计内容**，只需要简洁地告知用户：
        - 架构设计已完成
        - 文档已生成并保存
        - 提示用户查看输出目录中的设计文档
    *   **话术模板**: "✅ 架构设计已完成！完整的设计文档已生成并保存到输出目录中，包括：Agent需求分析、Node设计、Flow编排、数据结构等。请查看生成的文档了解详细的架构设计。"

# 工具使用要点
- **`short_planning`**: 可多次调用，用于逐步完善项目范围
- **`research`**: 可选工具，仅在需要技术调研时使用
- **`architecture_design`**: 输出到文件，调用后只需提示用户查看文档，无需重复输出内容"""


class ToolCallPatterns:
    """工具调用模式常量"""
    CUSTOM_TOOL_CALL_START = "<tool_call>"
    CUSTOM_TOOL_CALL_END = "</tool_call>"
    CUSTOM_TOOL_CALL_PATTERN = r'<tool_call>\[(.*?)\]</tool_call>'
