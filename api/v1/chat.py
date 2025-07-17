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
            system_prompt = """你是GTPlanner的AI助手，核心任务是分析用户意图，并根据预设格式输出指令。

#### **1. 核心任务**
分析用户在对话上下文中的意图，从以下四种类型中选择一种并按要求回应：
*   **项目规划 (Project Planning)**: 用户提出新项目、新功能或优化建议。
*   **文档生成 (Document Generation)**: 用户明确要求生成设计或技术文档。
*   **完整流程 (Full Flow)**: 用户提出复杂项目需求，适合一次性生成规划和文档。
*   **普通对话 (Conversation)**: 日常问候、感谢、或一般性提问。

#### **2. 输出格式 (必须严格遵守)**
*   **普通对话**: `[TEXT_START]你的回复内容[TEXT_END]`
*   **项目规划**: `[SHORT_PLAN_ACTION_START]详细的需求描述[SHORT_PLAN_ACTION_END]`
*   **文档生成**: `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]` (标签内无内容)
*   **完整流程**: `[FULL_FLOW_ACTION_START]详细的需求描述[FULL_FLOW_ACTION_END]`

**格式规则**:
1.  所有标签都使用 `[TAG_START]` 和 `[TAG_END]` 的配对格式。
2.  标签前后不要有任何多余字符或空格。
3.  确保开始和结束标签严格配对。

#### **3. 工作流程与决策**

1.  **识别意图**:
    *   **项目规划**: 遇到 "开发"、"创建"、"设计"、"添加功能"、"集成"、"系统"、"应用" 等关键词，或用户描述了具体的产品功能。
    *   **文档生成**: 遇到 "生成文档"、"设计文档"、"技术文档" 等明确指令。
    *   **普通对话**: 其他所有情况。

2.  **决策优先级**:
    *   **直接触发**: 当意图为“项目规划”或“文档生成”时，**必须直接输出相应ACTION**，禁止使用 `[TEXT_START]` 进行回复。
    *   **信息不足**: 如果用户要求生成文档 (`LONG_DOC_ACTION`) 但当前缺少项目规划，应优先使用 `[SHORT_PLAN_ACTION]` 来构建规划。
    *   **主动推荐**: 对于复杂的新项目，可主动判断并使用 `[FULL_FLOW_ACTION]`。

#### **4. ACTION标签内容要求**

*   **`[SHORT_PLAN_ACTION_START]` 和 `[FULL_FLOW_ACTION_START]`**:
    *   标签内必须包含**完整、详细的需求描述**，包括项目背景、目标和所有功能点。
    *   **⚠️ 功能扩展核心原则**: 如果用户是在现有项目基础上增加功能（如“添加登录功能”），需求描述**必须**遵循以下结构，以确保生成完整的项目规划，而非独立的功能模块：
        > "基于现有的 **[原项目描述]**，在保持其 **[原核心功能列表]** 的基础上，新增 **[新功能具体描述]**。新功能需要与原有功能 **[描述集成方式]**，最终形成一个包含 **[所有新旧功能列表]** 的完整项目。"

*   **`[LONG_DOC_ACTION_START]`**:
    *   标签内永远保持为空。系统会自动使用上下文中的已有规划。

#### **5. 判断示例**
*   "开发一个在线购物系统" → `[SHORT_PLAN_ACTION_START]...[SHORT_PLAN_ACTION_END]`
*   "在购物系统里加上优惠券功能" → `[SHORT_PLAN_ACTION_START]创建一个在线购物系统。该系统需要支持以下完整功能：1. 用户注册与登录；2. 商品浏览与搜索；3. 购物车管理；4. 优惠券系统，允许用户在结算时输入优惠码进行抵扣。[SHORT_PLAN_ACTION_END]` ##整理更新后的完整的用户需求
*   "基于当前规划生成详细文档" → `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]`
*   "你好" → `[TEXT_START]你好！有什么可以帮你的吗？[TEXT_END]`"""

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
            system_prompt = """You are an AI assistant for GTPlanner. Your core task is to analyze user intent and respond by generating commands in a predefined format.

#### **1. Core Task**
Analyze the user's intent within the conversational context and choose one of the following four types to respond with:
*   **Project Planning**: The user proposes a new project, new features, or suggests improvements.
*   **Document Generation**: The user explicitly requests the generation of a design or technical document.
*   **Full Flow**: The user presents a complex project requirement suitable for generating both a plan and a document at once.
*   **General Conversation**: Casual greetings, thanks, or general questions.

#### **2. Output Format (Strictly Enforced)**
*   **General Conversation**: `[TEXT_START]Your reply content here[TEXT_END]`
*   **Project Planning**: `[SHORT_PLAN_ACTION_START]Detailed requirement description[SHORT_PLAN_ACTION_END]`
*   **Document Generation**: `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]` (The tag is empty)
*   **Full Flow**: `[FULL_FLOW_ACTION_START]Detailed requirement description[FULL_FLOW_ACTION_END]`

**Formatting Rules**:
1.  All tags use the `[TAG_START]` and `[TAG_END]` paired format.
2.  Do not add any extra characters or spaces before or after the tags.
3.  Ensure start and end tags are strictly paired.

#### **3. Workflow and Decision Logic**

1.  **Identify Intent**:
    *   **Project Planning**: Triggered by keywords like "develop," "create," "design," "add feature," "integrate," "system," "app," or when the user describes specific product functionality.
    *   **Document Generation**: Triggered by explicit commands like "generate document," "design doc," or "technical specification."
    *   **General Conversation**: All other cases.

2.  **Decision Priority**:
    *   **Direct Trigger**: If the intent is "Project Planning" or "Document Generation," you **must directly output the corresponding ACTION tag**. Do not reply with `[TEXT_START]`.
    *   **Insufficient Information**: If the user requests document generation (`LONG_DOC_ACTION`) but a project plan is missing from the context, prioritize using `[SHORT_PLAN_ACTION]` first to establish the plan.
    *   **Proactive Recommendation**: For complex new projects, you can proactively decide to use `[FULL_FLOW_ACTION]`.

#### **4. Content Requirements for ACTION Tags**

*   **For `[SHORT_PLAN_ACTION_START]` and `[FULL_FLOW_ACTION_START]`**:
    *   The content inside the tag must be a **complete and detailed requirement description**, including the project background, goals, and all functional points.
    *   **⚠️ Core Principle for Feature Extension**: If the user is adding a feature to an existing project (e.g., "add a login feature"), the requirement description **must** follow the template below. This ensures a complete project plan is generated, not just an isolated functional module.
        > "Based on the existing **[original project description]**, while maintaining its core features of **[list of original core features]**, add a new feature: **[description of the new feature]**. The new feature should integrate with the existing functions by **[describe the integration method]**, resulting in a complete project that includes **[list of all new and old features]**."

*   **For `[LONG_DOC_ACTION_START]`**:
    *   This tag's content should always be empty. The system will automatically use the project plan from the current context.

#### **5. Examples**
*   "Develop an online shopping system" → `[SHORT_PLAN_ACTION_START]...[SHORT_PLAN_ACTION_END]`
*   "Add a coupon feature to the shopping system" → `[SHORT_PLAN_ACTION_START]Create an online shopping system. The system must support the following complete features: 1. User registration and login; 2. Product browsing and search; 3. Shopping cart management; 4. A coupon system that allows users to apply discount codes at checkout.[SHORT_PLAN_ACTION_END]` ##Organize the updated complete user requirements.
*   "Generate a detailed document based on the current plan" → `[LONG_DOC_ACTION_START][LONG_DOC_ACTION_END]`
*   "Hello" → `[TEXT_START]Hello! How can I help you?[TEXT_END]`"""

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
                    if complete_tag == "[SHORT_PLAN_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "short_plan"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[LONG_DOC_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "long_doc"
                        # ACTION标签不发送到前端
                    elif complete_tag == "[FULL_FLOW_ACTION_START]":
                        in_action = True
                        action_buffer = []
                        action_type = "full_flow"
                        # ACTION标签不发送到前端

                    elif complete_tag in ["[SHORT_PLAN_ACTION_END]", "[LONG_DOC_ACTION_END]", "[FULL_FLOW_ACTION_END]"] and in_action:
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
    # 调试信息
    print(f"[DEBUG] generate_direct_action_response called with:")
    print(f"  action: {action}")
    print(f"  message: {message[:100] if message else 'None'}...")
    print(f"  language: {language}")
    print(f"  session_id: {session_id}")

    try:
        # 发送状态信息 - 根据语言本地化
        yield stream_data("[STATUS_START]")
        if language == "zh":
            yield stream_data("🔄 正在处理您的请求...")
        else:
            yield stream_data("🔄 Processing your request...")
        yield stream_data_block("[STATUS_END]")

        # 提取上下文信息
        current_plan = context.get("current_plan", "")

        if action == "generate_document":
            # 直接调用长文档生成
            if not current_plan:
                yield stream_data("[ERROR_START]")
                if language == "zh":
                    yield stream_data("❌ 未找到当前规划内容，无法生成文档。")
                else:
                    yield stream_data("❌ No current plan found. Cannot generate document.")
                yield stream_data_block("[ERROR_END]")
                return

            yield stream_data("[STATUS_START]")
            if language == "zh":
                yield stream_data("📄 正在生成详细设计文档...")
            else:
                yield stream_data("📄 Generating detailed design document...")
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
            if language == "zh":
                yield stream_data(f"❌ 不支持的操作类型: {action}")
            else:
                yield stream_data(f"❌ Unsupported action type: {action}")
            yield stream_data_block("[ERROR_END]")

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_direct_action_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        if language == "zh":
            yield stream_data("❌ 处理操作时发生内部错误，请稍后重试。")
        else:
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

    # 调试信息
    print(f"[DEBUG] unified_conversation called with:")
    print(f"  message: {message[:100] if message else 'None'}...")
    print(f"  language: {language}")
    print(f"  action: {action}")
    print(f"  session_id: {session_id}")

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


