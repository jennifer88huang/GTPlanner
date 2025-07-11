import asyncio
from typing import Any, Optional, List, Dict
import re

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.call_llm import call_llm_async
from utils.multilingual_utils import determine_language

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
    action: Optional[str] = None  # 'generate_document', 'optimize_plan'
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


async def handle_action(action_content: str, original_message: str, current_plan: str, language: str):
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

        elif action_content.startswith("optimize_plan:"):
            optimization = action_content[14:].strip() or original_message

            # 调用流式规划优化
            planning_request = ShortPlanningRequest(
                requirement=optimization,
                previous_flow=current_plan,
                language=language
            )
            async for chunk in short_planning_stream(planning_request):
                if isinstance(chunk, str):
                    # short_planning_stream已经返回格式化的SSE数据，直接输出
                    yield chunk.encode('utf-8')
                else:
                    yield chunk

        elif action_content.startswith("long_doc:"):
            doc_requirement = action_content[9:].strip() or original_message

            # 调用流式长文档生成
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

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in handle_action: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ 处理操作时出现内部错误，请稍后重试")
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

        # 构建完整的对话上下文
        context_messages = []
        for msg in conversation_history:
            msg_type = f" [{msg.message_type}]" if msg.message_type != "message" else ""
            context_messages.append(f"{msg.role}{msg_type}: {msg.content}")

        context_str = "\n".join(context_messages) if context_messages else "这是对话的开始。"

        # 构建统一对话提示词，使用标签输出格式
        if language == "zh":
            prompt = f"""你是GTPlanner的AI助手，专门帮助用户进行项目规划和设计。

对话历史：
{context_str}

用户当前消息：{message}

当前规划内容：
{current_plan if current_plan else "暂无规划内容"}

请分析用户的意图并相应回应。可能的意图包括：

1. **项目需求(requirement)**：用户明确要求创建、开发、设计、构建具体的系统/应用/项目，或描述了具体的功能需求和技术方案。

2. **优化改进(optimization)**：用户对现有规划提出修改建议或优化意见。
   {"当前规划内容：" + current_plan + "..." if current_plan else ""}

3. **文档生成(document_generation)**：用户明确要求生成详细文档、设计文档、技术文档，或者说"基于当前规划生成文档"、"生成设计文档"等。

4. **普通对话(conversation)**：用户只是问候、感谢、询问概念、寻求建议或进行一般性讨论。

请严格按照以下标签格式输出，注意标签格式必须完全正确：

- 普通对话回复：[TEXT_START]您的回复内容（可包含建议、提示等）[TEXT_END]
- 触发短规划：[SHORT_PLAN_ACTION]用户需求描述[/SHORT_PLAN_ACTION]
- 触发长文档：[LONG_DOC_ACTION]基于现有规划生成文档[/LONG_DOC_ACTION]
- 触发规划优化：[OPTIMIZE_PLAN_ACTION]优化建议[/OPTIMIZE_PLAN_ACTION]

注意：建议和提示内容应该直接包含在TEXT标签内，不要使用单独的SUGGESTION标签。

⚠️ 标签格式要求（必须严格遵守）：
1. 普通标签结束格式：[TEXT_END] - 绝对不要加斜杠
2. ACTION标签结束格式：[/SHORT_PLAN_ACTION] - 必须有斜杠
3. 不要在标签名前后添加任何额外字符
4. 标签必须独立成行或紧贴内容，不要有多余空格

根据用户意图选择合适的标签输出。如果是项目需求，先用TEXT回复然后触发相应ACTION；如果是文档生成请求，先回复然后触发LONG_DOC_ACTION；如果是普通对话，只用TEXT标签回复。"""


        else:
            prompt = f"""You are GTPlanner's AI assistant, specialized in helping users with project planning and design.

Conversation history:
{context_str}

Current user message: {message}

Please analyze the user's intent and respond accordingly. Possible intents include:

1. **Project Requirement (requirement)**: User explicitly requests to create, develop, design, or build specific systems/applications/projects, or describes specific functional requirements and technical solutions.

2. **Optimization (optimization)**: User provides feedback or suggestions to improve an existing plan.
   {f"Current plan content: {current_plan[:200]}..." if current_plan else ""}

3. **Document Generation (document_generation)**: User explicitly requests to generate a detailed document or to create documentation based on an existing plan.

4. **Normal Conversation (conversation)**: User is just greeting, thanking, asking about concepts, seeking advice, or having general discussion.

Please strictly follow the tag format below, ensuring the tag format is completely correct:

- Normal conversation: [TEXT_START]Your response content (can include suggestions, tips, etc.)[TEXT_END]
- Trigger short planning: [SHORT_PLAN_ACTION]user requirement description[/SHORT_PLAN_ACTION]
- Trigger long documentation: [LONG_DOC_ACTION]generate document based on existing plan[/LONG_DOC_ACTION]
- Trigger plan optimization: [OPTIMIZE_PLAN_ACTION]optimization suggestions[/OPTIMIZE_PLAN_ACTION]

Note: Suggestions and tips should be included directly within TEXT tags, do not use separate SUGGESTION tags.

⚠️ Tag Format Requirements (Must Follow Strictly):
1. Regular tag end format: [TEXT_END] - absolutely no slash
2. ACTION tag end format: [/SHORT_PLAN_ACTION] - must have slash
3. Do not add any extra characters before or after tag names
4. Tags must be on separate lines or directly adjacent to content, no extra spaces

Choose the appropriate tag based on user intent. For project requirements, reply with TEXT first then trigger corresponding ACTION; for document generation requests, reply first then trigger LONG_DOC_ACTION; for normal conversation, only use TEXT tags."""

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
                    elif complete_tag == "[OPTIMIZE_PLAN_ACTION]":
                        in_action = True
                        action_buffer = []
                        action_type = "optimize_plan"
                        # ACTION标签不发送到前端
                    elif complete_tag in ["[/SHORT_PLAN_ACTION]", "[/LONG_DOC_ACTION]", "[/OPTIMIZE_PLAN_ACTION]"] and in_action:
                        # 处理ACTION内容
                        action_content = ''.join(action_buffer).strip()
                        if action_content:
                            # 根据action_type构造action_content
                            full_action_content = f"{action_type}:{action_content}"
                            async for planning_chunk in handle_action(full_action_content, message, current_plan, language):
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
        yield stream_data("❌ 生成回复时出现内部错误，请稍后重试")
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
                yield stream_data("❌ 没有找到当前规划，无法生成文档")
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

        elif action == "optimize_plan":
            # 直接调用规划优化
            if not current_plan:
                yield stream_data("[ERROR_START]")
                yield stream_data("❌ 没有找到当前规划，无法进行优化")
                yield stream_data_block("[ERROR_END]")
                return

            yield stream_data("[STATUS_START]")
            yield stream_data("🔧 正在优化规划...")
            yield stream_data_block("[STATUS_END]")

            # 调用短规划优化流式接口
            from api.v1.planning import short_planning_stream, ShortPlanningRequest

            planning_request = ShortPlanningRequest(
                requirement=message,
                previous_flow=current_plan,
                language=language
            )

            async for chunk in short_planning_stream(planning_request):
                yield chunk

        else:
            yield stream_data("[ERROR_START]")
            yield stream_data(f"❌ 不支持的操作类型: {action}")
            yield stream_data_block("[ERROR_END]")

    except Exception as e:
        # 记录详细错误信息用于调试
        import logging
        logging.error(f"Error in generate_direct_action_response: {str(e)}", exc_info=True)

        # 向用户返回通用错误信息，不暴露内部细节
        yield stream_data("[ERROR_START]")
        yield stream_data("❌ 处理操作时出现内部错误，请稍后重试")
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

    # 确定语言
    if not language:
        language = determine_language(message, None, None)

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