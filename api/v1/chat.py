from typing import Any, Optional, List, Dict

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.multilingual_utils import determine_language
# from utils.context_manager import optimize_conversation_context  # 已禁用上下文压缩功能

# 导入规划相关的功能
from api.v1.planning import (
    short_planning, long_planning,
    short_planning_stream, long_planning_stream,
    ShortPlanningRequest, LongPlanningRequest
)

chat_router = APIRouter(prefix="/chat", tags=["chat"])


def stream_data(content: str) -> bytes:
    """
    封装流式输出数据，确保UTF-8编码，每行以换行符结尾（SSE格式要求）
    使用占位符保护markdown换行符，避免与SSE协议冲突
    """
    # 将换行符替换为占位符，避免与SSE消息分隔符冲突
    protected_content = content.replace('\n', '<|newline|>')
    return f"data: {protected_content}\n".encode('utf-8')


def stream_data_block(content: str) -> bytes:
    """
    封装流式输出数据块，确保UTF-8编码，并添加结束标记
    """
    return f"data: {content}\n\n".encode('utf-8')


class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str
    message_type: Optional[str] = "message"  # 'message', 'plan', 'document'
    timestamp: Optional[int] = None


class ConversationRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    session_id: Optional[str] = None
    language: Optional[str] = None
    action: Optional[str] = None  # 'generate_document'
    context: Optional[Dict[str, Any]] = None


class ConversationAction(BaseModel):
    type: str  # 'plan', 'document', 'suggestion'
    content: str
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []
    language: Optional[str] = None
    user_id: Optional[str] = None


class IntentAnalysisResult(BaseModel):
    intent: str  # 'requirement' or 'conversation'
    confidence: float
    reasoning: str

async def process_intent_actions(intent: str, message: str, current_plan: str, actions: List[Dict], language: str) -> List[ConversationAction]:
    """
    根据意图处理特殊操作，如生成规划或文档
    """
    processed_actions = []

    try:
        if intent == "requirement":
            # 生成短规划
            planning_request = ShortPlanningRequest(
                requirement=message,
                language=language
            )
            planning_result = await short_planning(planning_request)

            if "flow" in planning_result:
                processed_actions.append(ConversationAction(
                    type="plan",
                    content=planning_result["flow"],
                    title="项目规划" if language == "zh" else "Project Plan",
                    metadata={
                        "language": planning_result.get("language", language),
                        "version": 1
                    }
                ))

        elif intent == "optimization" and current_plan:
            # 优化现有规划
            planning_request = ShortPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )
            planning_result = await short_planning(planning_request)

            if "flow" in planning_result:
                processed_actions.append(ConversationAction(
                    type="plan",
                    content=planning_result["flow"],
                    title="优化规划" if language == "zh" else "Optimized Plan",
                    metadata={
                        "language": planning_result.get("language", language),
                        "based_on": current_plan[:100] + "..." if len(current_plan) > 100 else current_plan,
                        "version": 2
                    }
                ))

        elif intent == "document_generation" and current_plan:
            # 生成长文档
            doc_request = LongPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )
            doc_result = await long_planning(doc_request)

            if "flow" in doc_result:
                processed_actions.append(ConversationAction(
                    type="document",
                    content=doc_result["flow"],
                    title="设计文档" if language == "zh" else "Design Document",
                    metadata={
                        "language": doc_result.get("language", language),
                        "based_on": current_plan[:100] + "..." if len(current_plan) > 100 else current_plan
                    }
                ))

        # 处理LLM建议的其他actions
        for action in actions:
            if isinstance(action, dict) and "type" in action and "content" in action:
                processed_actions.append(ConversationAction(
                    type=action.get("type", "suggestion"),
                    content=action.get("content", ""),
                    title=action.get("title"),
                    metadata=action.get("metadata", {})
                ))

    except Exception as e:
        print(f"Error processing intent actions: {e}")
        # 如果处理失败，返回一个建议action
        processed_actions.append(ConversationAction(
            type="suggestion",
            content="处理您的请求时遇到问题，请尝试重新描述您的需求。" if language == "zh" else "There was an issue processing your request. Please try rephrasing your needs.",
            title="建议" if language == "zh" else "Suggestion"
        ))

    return processed_actions


async def handle_action(action_content: str, original_message: str, current_plan: str, language: str, conversation_history: Optional[List[ChatMessage]] = None):
    """
    处理ACTION标签，调用相应的流式planning接口并返回流式结果
    """
    try:
        # 解析action类型和内容
        if action_content.startswith("short_plan:"):
            requirement = action_content[11:].strip() or original_message

            # 调用流式短规划接口
            planning_request = ShortPlanningRequest(
                requirement=requirement,
                language=language
            )
            async for chunk in short_planning_stream(planning_request):
                if isinstance(chunk, str):
                    # short_planning_stream已经返回格式化的SSE数据，直接输出
                    yield chunk.encode('utf-8')
                else:
                    yield chunk



        elif action_content.startswith("long_doc:"):
            # LONG_DOC_ACTION不使用标签内容，使用固定的文档生成需求
            doc_requirement = "基于当前规划生成详细的设计文档" if language == "zh" else "Generate detailed design document based on current plan"

            # 调用流式长文档生成，使用context.current_plan
            doc_request = LongPlanningRequest(
                requirement=doc_requirement,
                previous_flow=current_plan,
                language=language
            )
            async for chunk in long_planning_stream(doc_request):
                if isinstance(chunk, str):
                    # long_planning_stream已经返回格式化的SSE数据，直接输出
                    yield chunk.encode('utf-8')
                else:
                    yield chunk

        elif action_content.startswith("full_flow:"):
            requirement = action_content[10:].strip() or original_message

            # 先执行短规划
            planning_request = ShortPlanningRequest(
                requirement=requirement,
                language=language
            )

            # 收集短规划的结果
            plan_result = ""
            async for chunk in short_planning_stream(planning_request):
                if isinstance(chunk, str):
                    yield chunk.encode('utf-8')
                    # 提取规划内容（去除SSE格式）
                    if chunk.startswith("data: ") and not chunk.startswith("data: ["):
                        plan_content = chunk[6:].replace('<|newline|>', '\n').strip()
                        if plan_content:
                            plan_result += plan_content + "\n"
                else:
                    yield chunk

            # 等待短规划完成后，自动触发长文档生成
            if plan_result.strip():
                # 调用流式长文档生成，使用刚生成的规划作为previous_flow
                doc_request = LongPlanningRequest(
                    requirement=requirement,
                    previous_flow=plan_result.strip(),
                    language=language
                )
                async for chunk in long_planning_stream(doc_request):
                    if isinstance(chunk, str):
                        yield chunk.encode('utf-8')
                    else:
                        yield chunk

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in handle_action: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ An internal error occurred while processing the action. Please try again later.")
        yield stream_data_block("[ERROR_END]")


async def generate_stream_response(
    message: str,
    conversation_history: List[ChatMessage],
    session_id: Optional[str],
    language: str,
    context: Dict[str, Any]
):
    """
    生成基于标签的流式响应
    """
    try:
        # 发送状态信息
        yield stream_data("[STATUS_START]")
        yield stream_data("🔄 正在分析您的需求...")
        yield stream_data_block("[STATUS_END]")

        # 提取上下文信息
        current_plan = context.get("current_plan", "")

        # 禁用上下文压缩功能，直接使用原始对话历史
        # TODO: 后续研究更智能的压缩方案时可以重新启用以下代码
        # try:
        #     # 转换消息格式
        #     history_dicts = []
        #     for msg in conversation_history:
        #         history_dicts.append({
        #             "role": msg.role,
        #             "content": msg.content,
        #             "message_type": msg.message_type,
        #             "timestamp": msg.timestamp
        #         })
        #
        #     # 优化上下文
        #     context_str, context_stats = await optimize_conversation_context(
        #         history_dicts, message
        #     )
        # except Exception as e:
        #     print(f"上下文优化失败，使用降级策略: {e}")

        # 直接处理原始对话历史，分离系统提示词和用户聊天记录
        user_conversation_history = []
        for msg in conversation_history:
            # 只包含用户和助手的对话消息，排除系统消息
            if msg.role in ["user", "assistant"] and msg.message_type == "message":
                msg_content = f"{msg.role}: {msg.content}"
                user_conversation_history.append(msg_content)

        # 构建纯净的用户对话历史字符串
        context_str = "\n".join(user_conversation_history) if user_conversation_history else "这是对话的开始。"

        # 构建分离的系统提示词和用户对话上下文
        if language == "zh":
            # 系统提示词部分（包含所有系统指令，独立于用户对话历史）
            system_prompt = """你是GTPlanner的AI助手，专门帮助用户进行项目规划和设计。

请分析用户的意图并相应回应。在分析时，请特别注意对话上下文和已有规划内容。可能的意图包括：

1. **项目需求(requirement)**：
   - 用户明确要求创建全新的系统/应用/项目
   - 用户在现有规划基础上提出新的功能需求或改进建议
   - ⚠️ **重要原则**：如果已有规划内容，用户的新需求是对现有项目的功能扩展，必须保持原项目的核心功能和主体架构，在此基础上集成新功能

2. **优化改进(optimization)**：用户对现有规划提出修改建议或优化意见。

3. **文档生成(document_generation)**：用户明确要求生成详细文档、设计文档、技术文档，或者说"基于当前规划生成文档"、"生成设计文档"等。

4. **普通对话(conversation)**：用户只是问候、感谢、询问概念、寻求建议或进行一般性讨论。

请严格按照以下标签格式输出，注意标签格式必须完全正确：

- 普通对话回复：[TEXT_START]您的回复内容（可包含建议、提示等）[TEXT_END]
- 触发短规划：[SHORT_PLAN_ACTION]完整描述用户需求，包括项目背景、目标、功能要求等详细信息[/SHORT_PLAN_ACTION]
- 触发长文档：[LONG_DOC_ACTION][/LONG_DOC_ACTION]
- 触发完整流程：[FULL_FLOW_ACTION]完整描述用户需求，包括项目背景、目标、功能要求等详细信息[/FULL_FLOW_ACTION]

注意：建议和提示内容应该直接包含在TEXT标签内，不要使用单独的SUGGESTION标签。

⚠️ 标签格式要求（必须严格遵守）：
1. TEXT标签格式：开始用[TEXT_START]，结束用[TEXT_END]（注意：TEXT_END没有斜杠！）
2. ACTION标签格式：开始用[ACTION_NAME]，结束用[/ACTION_NAME]（注意：结束标签有斜杠！）
3. 错误示例：[/TEXT_START]、[/TEXT_END]、[SHORT_PLAN_ACTION/] 都是错误的
4. 正确示例：[TEXT_START]内容[TEXT_END]、[SHORT_PLAN_ACTION]内容[/SHORT_PLAN_ACTION]
5. 不要在标签名前后添加任何额外字符
6. 标签必须独立成行或紧贴内容，不要有多余空格

根据用户意图选择合适的标签输出：

**何时使用SHORT_PLAN_ACTION：**
- 用户提出新的项目需求或功能需求（如：开发XX系统、创建XX应用、设计XX功能）
- 用户要求创建、开发、设计具体的系统/应用/插件/工具
- 用户描述了具体的产品功能和特性
- 用户在现有项目基础上提出新功能或改进建议
- 需要生成步骤化的实施规划时

**明确的项目需求关键词：**
- "开发"、"创建"、"设计"、"制作"、"构建"
- "系统"、"应用"、"插件"、"工具"、"平台"
- "功能"、"特性"、"模块"、"组件"、"添加"、"集成"、"支持"
- 描述具体的技术实现或产品特性

**⚠️ 功能扩展规划的核心原则：**
当用户在现有项目基础上提出新功能时（如"添加XX功能"、"集成XX"、"支持XX"），生成的规划必须：
1. **保持原项目的完整性**：包含原有的所有核心功能和架构
2. **明确新功能的集成方式**：说明新功能如何与现有功能协同工作
3. **提供完整的项目规划**：不是独立的功能模块规划，而是包含原有功能+新功能的完整项目规划
4. **保持项目主题一致性**：确保新功能服务于原项目的核心目标

**何时使用LONG_DOC_ACTION：**
- 用户明确要求生成详细文档、设计文档、技术文档
- 用户说"生成文档"、"基于规划生成文档"、"详细设计"等
- 已有规划内容，用户需要更详细的文档说明
- 需要将规划转化为完整设计文档时

**何时使用FULL_FLOW_ACTION：**
- 用户提出完整的项目需求，且你认为需要同时提供规划和详细文档
- 用户的需求足够复杂，值得生成完整的项目流程（规划+文档）
- 当你判断用户最终需要的是完整的项目方案时
- 不需要用户明确要求，你可以主动判断是否适合使用完整流程

**灵活使用策略：**

**直接使用规则：**
- 如果用户需求已经足够明确和完整，可以直接使用SHORT_PLAN_ACTION生成规划
- 如果用户明确要求生成文档且已有完整的项目背景信息，可以直接使用LONG_DOC_ACTION

**必须先用SHORT_PLAN_ACTION的情况：**
- 当用户要求生成文档(LONG_DOC_ACTION)但当前对话中缺少完整的项目规划时
- 当需要先建立项目的基础规划框架，再生成详细文档时
- 当用户的需求描述不够具体，需要先通过规划过程明确具体实施步骤时

**判断原则：**
- 优先考虑用户需求的完整性和可执行性
- 确保生成的内容有足够的上下文支撑
- 避免在缺少基础规划的情况下直接生成详细文档

**基本输出规则：**
- 项目需求：直接使用SHORT_PLAN_ACTION或FULL_FLOW_ACTION，不需要先用TEXT回复
- 文档生成请求：直接使用LONG_DOC_ACTION，不需要先用TEXT回复
- 普通对话：只用TEXT标签回复

**重要：当识别到项目需求时，必须直接触发相应的ACTION，不要只用TEXT回复！**

**判断示例：**
- "多语言词汇量提升设计文档" → 项目需求 → 使用SHORT_PLAN_ACTION
- "浏览器插件，为用户提供划词即时翻译" → 项目需求 → 使用SHORT_PLAN_ACTION
- "开发一个在线购物系统" → 项目需求 → 使用SHORT_PLAN_ACTION
- "你好，请问你能做什么？" → 普通对话 → 使用TEXT标签
- "基于当前规划生成详细文档" → 文档生成 → 使用LONG_DOC_ACTION

⚠️ 重要提示：
1. **SHORT_PLAN_ACTION标签**：输出完整的用户需求描述，包括项目背景、目标、功能要求、技术需求等
2. **LONG_DOC_ACTION标签**：标签内不需要包含任何内容，系统会使用当前上下文中的规划内容
3. **FULL_FLOW_ACTION标签**：输出完整的用户需求描述，供短规划节点使用，确保需求描述足够详细和准确
4. 基于当前对话上下文，准确理解用户的真实意图和需求
5. **如果用户是在现有项目基础上提出新需求，需求描述中必须包含：**
   - 原项目的完整背景和核心功能描述
   - 新增功能的具体要求
   - 新功能与原有功能的集成方式
   - 确保生成的是完整项目规划，而不是独立的功能模块规划

**需求描述模板（用于功能扩展场景）：**
"基于现有的[原项目描述]，在保持其[核心功能列表]的基础上，新增[新功能描述]。新功能应与现有功能[集成方式]，最终形成一个完整的[项目类型]，具备[完整功能列表]。"""

            # 用户对话上下文部分（纯净的用户数据，不包含系统指令）
            user_context = f"""
用户对话历史：
{context_str}

当前规划内容：
{current_plan if current_plan else "暂无规划内容"}

用户当前消息：{message}"""

            # 组合完整提示词
            prompt = f"""{system_prompt}

{user_context}"""


        else:
            # 系统提示词部分（包含所有系统指令，独立于用户对话历史）
            system_prompt = """You are GTPlanner's AI assistant, specialized in helping users with project planning and design.

Please analyze the user's intent and respond accordingly. When analyzing, pay special attention to conversation context and existing plan content. Possible intents include:

1. **Project Requirement (requirement)**:
   - User explicitly requests to create a completely new system/application/project
   - User proposes new functional requirements or improvements based on existing plan
   - ⚠️ **Important Principle**: If there's existing plan content, user's new requirements are functional extensions to the existing project. Must maintain the core functionality and main architecture of the original project while integrating new features

2. **Optimization (optimization)**: User provides feedback or suggestions to improve an existing plan.

3. **Document Generation (document_generation)**: User explicitly requests to generate a detailed document or to create documentation based on an existing plan.

4. **Normal Conversation (conversation)**: User is just greeting, thanking, asking about concepts, seeking advice, or having general discussion.

Please strictly follow the tag format below, ensuring the tag format is completely correct:

- Normal conversation: [TEXT_START]Your response content (can include suggestions, tips, etc.)[TEXT_END]
- Trigger short planning: [SHORT_PLAN_ACTION]Completely describe user requirements, including project background, objectives, functional requirements and other detailed information[/SHORT_PLAN_ACTION]
- Trigger long documentation: [LONG_DOC_ACTION][/LONG_DOC_ACTION]
- Trigger full flow: [FULL_FLOW_ACTION]Completely describe user requirements, including project background, objectives, functional requirements and other detailed information[/FULL_FLOW_ACTION]

Note: Suggestions and tips should be included directly within TEXT tags, do not use separate SUGGESTION tags.

⚠️ Tag Format Requirements (Must Follow Strictly):
1. TEXT tag format: Start with [TEXT_START], end with [TEXT_END] (Note: TEXT_END has NO slash!)
2. ACTION tag format: Start with [ACTION_NAME], end with [/ACTION_NAME] (Note: End tag has slash!)
3. Wrong examples: [/TEXT_START], [/TEXT_END], [SHORT_PLAN_ACTION/] are all WRONG
4. Correct examples: [TEXT_START]content[TEXT_END], [SHORT_PLAN_ACTION]content[/SHORT_PLAN_ACTION]
5. Do not add any extra characters before or after tag names
6. Tags must be on separate lines or directly adjacent to content, no extra spaces

Choose the appropriate tag based on user intent:

**When to use SHORT_PLAN_ACTION:**
- User proposes new project requirements or functional requirements (e.g.: develop XX system, create XX app, design XX feature)
- User requests to create, develop, design specific systems/applications/plugins/tools
- User describes specific product features and characteristics
- User proposes new features or improvements based on existing project
- When step-by-step implementation planning is needed

**Clear Project Requirement Keywords:**
- "develop", "create", "design", "build", "construct"
- "system", "application", "plugin", "tool", "platform"
- "feature", "functionality", "module", "component", "add", "integrate", "support"
- Descriptions of specific technical implementations or product characteristics

**⚠️ Core Principles for Feature Extension Planning:**
When users propose new features based on existing projects (e.g., "add XX feature", "integrate XX", "support XX"), the generated plan must:
1. **Maintain original project integrity**: Include all existing core functions and architecture
2. **Clarify new feature integration**: Explain how new features work with existing functionality
3. **Provide complete project planning**: Not an independent feature module plan, but a complete project plan including original + new features
4. **Maintain project theme consistency**: Ensure new features serve the core objectives of the original project

**When to use LONG_DOC_ACTION:**
- User explicitly requests detailed documents, design documents, technical documents
- User says "generate document", "create documentation based on plan", "detailed design", etc.
- There's existing plan content and user needs more detailed documentation
- When converting plans into complete design documents

**When to use FULL_FLOW_ACTION:**
- User proposes complete project requirements and you think both planning and detailed documentation are needed
- User's requirements are complex enough to warrant a complete project flow (planning + documentation)
- When you judge that user ultimately needs a complete project solution
- No explicit user request needed, you can proactively judge if full flow is appropriate

**Flexible Usage Strategy:**

**Direct Usage Rules:**
- If user requirements are already clear and complete, can directly use SHORT_PLAN_ACTION to generate planning
- If user explicitly requests document generation and has complete project background information, can directly use LONG_DOC_ACTION

**Must Use SHORT_PLAN_ACTION First When:**
- User requests document generation (LONG_DOC_ACTION) but current conversation lacks complete project planning
- Need to establish basic project planning framework before generating detailed documents
- User's requirement description is not specific enough, need to clarify implementation steps through planning process first

**Judgment Principles:**
- Prioritize completeness and executability of user requirements
- Ensure generated content has sufficient contextual support
- Avoid generating detailed documents when lacking basic planning foundation

**Basic Output Rules:**
- Project requirements: Directly use SHORT_PLAN_ACTION or FULL_FLOW_ACTION, no need to reply with TEXT first
- Document generation requests: Directly use LONG_DOC_ACTION, no need to reply with TEXT first
- Normal conversation: Only use TEXT tags

**Important: When identifying project requirements, must directly trigger corresponding ACTION, don't just reply with TEXT!**

**Judgment Examples:**
- "Multi-language vocabulary improvement design document" → Project requirement → Use SHORT_PLAN_ACTION
- "Browser extension for instant translation" → Project requirement → Use SHORT_PLAN_ACTION
- "Develop an online shopping system" → Project requirement → Use SHORT_PLAN_ACTION
- "Hello, what can you do?" → Normal conversation → Use TEXT tags
- "Generate detailed document based on current plan" → Document generation → Use LONG_DOC_ACTION

⚠️ Important Note:
1. **SHORT_PLAN_ACTION tags**: Output complete user requirement description, including project background, objectives, functional requirements, technical needs, etc.
2. **LONG_DOC_ACTION tags**: No content needed inside tags, system will use current planning content from context
3. **FULL_FLOW_ACTION tags**: Output complete user requirement description for short planning node, ensure requirement description is detailed and accurate
4. Based on current conversation context, accurately understand user's real intent and requirements
5. **If user is proposing new requirements based on existing project, requirement description must include:**
   - Complete background and core functionality description of the original project
   - Specific requirements for new features
   - Integration approach between new and existing features
   - Ensure the generated plan is a complete project plan, not an independent feature module plan

**Requirement Description Template (for feature extension scenarios):**
"Based on the existing [original project description], while maintaining its [core functionality list], add [new feature description]. The new feature should [integration approach] with existing features, ultimately forming a complete [project type] with [complete functionality list]."""

            # 用户对话上下文部分（纯净的用户数据，不包含系统指令）
            user_context = f"""
User conversation history:
{context_str}

Current plan content:
{current_plan if current_plan else "No current plan available"}

Current user message: {message}"""

            # 组合完整提示词
            prompt = f"""{system_prompt}

{user_context}"""

        # 调用LLM进行意图识别和响应生成
        yield stream_data("[STATUS_START]")
        yield stream_data("🤖 正在生成回复...")
        yield stream_data_block("[STATUS_END]")

        # 导入流式LLM调用
        from utils.call_llm import call_llm_stream_async

        # 流式输出LLM的响应并监听ACTION标签
        action_buffer = []
        in_action = False
        action_type = None
        content_buffer = ""
        pending_output = ""  # 缓冲待输出的内容

        async for chunk in call_llm_stream_async(prompt):
            if chunk:
                content_buffer += chunk
                pending_output += chunk

                # 处理缓冲区中的完整标签
                while True:
                    # 查找标签开始
                    start_pos = pending_output.find('[')
                    if start_pos == -1:
                        # 没有标签，输出所有内容
                        if pending_output and not in_action:
                            yield stream_data(pending_output)
                        elif pending_output and in_action:
                            action_buffer.append(pending_output)
                        pending_output = ""
                        break

                    # 输出标签前的内容
                    if start_pos > 0:
                        before_tag = pending_output[:start_pos]
                        if not in_action:
                            yield stream_data(before_tag)
                        else:
                            action_buffer.append(before_tag)

                    # 查找标签结束
                    end_pos = pending_output.find(']', start_pos)
                    if end_pos == -1:
                        # 标签不完整，保留从标签开始的所有内容
                        pending_output = pending_output[start_pos:]
                        break

                    # 提取完整标签
                    complete_tag = pending_output[start_pos:end_pos + 1]
                    remaining_content = pending_output[end_pos + 1:]

                    # 处理标签
                    if complete_tag == "[SHORT_PLAN_ACTION]":
                        in_action = True
                        action_buffer = []
                        action_type = "short_plan"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[LONG_DOC_ACTION]":
                        in_action = True
                        action_buffer = []
                        action_type = "long_doc"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[FULL_FLOW_ACTION]":
                        in_action = True
                        action_buffer = []
                        action_type = "full_flow"
                        # ACTION标签不发送到前端

                    elif complete_tag in ["[/SHORT_PLAN_ACTION]", "[/LONG_DOC_ACTION]", "[/FULL_FLOW_ACTION]"] and in_action:
                        # 处理ACTION内容
                        action_content = ''.join(action_buffer).strip()
                        if action_content:
                            # 根据action_type构造action_content
                            full_action_content = f"{action_type}:{action_content}"
                            async for planning_chunk in handle_action(full_action_content, message, current_plan, language, conversation_history):
                                yield planning_chunk
                        in_action = False
                        action_buffer = []
                        action_type = None
                        # ACTION标签不发送到前端
                    else:
                        # 非ACTION标签，正常发送
                        if not in_action:
                            yield stream_data(complete_tag)
                        else:
                            action_buffer.append(complete_tag)

                    # 继续处理剩余内容
                    pending_output = remaining_content

        # 处理可能剩余的内容
        if pending_output:
            if not in_action:
                yield stream_data(pending_output)
            else:
                action_buffer.append(pending_output)

        yield stream_data_block("")  # 空行表示结束

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_stream_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ An internal error occurred while generating response. Please try again later.")
        yield stream_data_block("[ERROR_END]")


async def generate_direct_action_response(
    action: str,
    message: str,
    conversation_history: List[ChatMessage],
    session_id: Optional[str],
    language: str,
    context: Dict[str, Any]
):
    """
    根据明确的action直接生成响应，跳过AI意图识别
    """
    try:
        # 发送状态信息
        yield stream_data("[STATUS_START]")
        yield stream_data("🔄 正在处理您的请求...")
        yield stream_data_block("[STATUS_END]")

        # 提取上下文信息
        current_plan = context.get("current_plan", "")

        if action == "generate_document":
            # 直接调用长文档生成
            if not current_plan:
                yield stream_data("[ERROR_START]")
                yield stream_data("❌ No current plan found. Cannot generate document.")
                yield stream_data_block("[ERROR_END]")
                return

            yield stream_data("[STATUS_START]")
            yield stream_data("📄 正在生成详细设计文档...")
            yield stream_data_block("[STATUS_END]")

            # 调用长文档生成流式接口
            from api.v1.planning import long_planning_stream, LongPlanningRequest

            doc_request = LongPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )

            async for chunk in long_planning_stream(doc_request):
                yield chunk



        else:
            yield stream_data("[ERROR_START]")
            yield stream_data(f"❌ Unsupported action type: {action}")
            yield stream_data_block("[ERROR_END]")

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_direct_action_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ An internal error occurred while processing the operation. Please try again later.")
        yield stream_data_block("[ERROR_END]")


@chat_router.post("/unified")
async def unified_conversation(body: ConversationRequest):
    """
    统一对话接口：集成意图识别、对话回复、规划生成和文档生成功能
    完全使用流式响应
    """
    message = body.message
    conversation_history = body.conversation_history or []
    session_id = body.session_id
    language = body.language
    action = body.action
    context = body.context or {}

    if not message:
        async def error_stream():
            yield stream_data("[ERROR_START]")
            yield stream_data("❌ Missing message in request body.")
            yield stream_data_block("[ERROR_END]")
        return StreamingResponse(error_stream(), media_type="text/plain")

    # 确定语言 - 优先使用前端传递的界面语言，确保界面语言和LLM输出语言的一致性
    language = determine_language(message, None, language)

    # 根据action字段直接调用相应功能，或使用AI意图识别
    if action:
        return StreamingResponse(
            generate_direct_action_response(action, message, conversation_history, session_id, language, context),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )
    else:
        # 返回流式响应（使用AI意图识别）
        return StreamingResponse(
            generate_stream_response(message, conversation_history, session_id, language, context),
            media_type="text/plain; charset=utf-8",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/plain; charset=utf-8"
            }
        )


