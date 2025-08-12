"""
消息构建器 - 基于统一上下文管理

负责构建Function Calling对话消息，现在基于统一上下文管理器获取数据。
"""

from typing import Dict, List, Any
from core.unified_context import get_context
from .constants import MessageRoles, SystemPrompts, StateKeys


class MessageBuilder:
    """消息构建器类 - 基于统一上下文"""

    def __init__(self):
        self.system_prompt = SystemPrompts.FUNCTION_CALLING_SYSTEM_PROMPT
        self.context = get_context()
    
   
    def build_enhanced_conversation_messages(
        self,
        user_message: str,
        state_info: str,
        shared_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        构建增强的对话消息：系统提示 + 优化历史 + 当前用户消息

        Args:
            user_message: 最新用户输入
            state_info: 状态描述信息
            shared_data: 共享数据

        Returns:
            OpenAI Chat Completions 所需的消息列表
        """
        messages: List[Dict[str, Any]] = []

        # 1) 系统消息（包含系统提示与状态信息）
        system_content_parts: List[str] = [self.system_prompt]
        if state_info:
            system_content_parts.append("\n\n—— 状态信息 ——\n" + state_info)

        messages.append({
            "role": MessageRoles.SYSTEM,
            "content": "\n".join(system_content_parts)
        })

        # 2) 添加智能优化的历史消息（基于压缩后的上下文）
        self._add_intelligent_history_messages(messages, shared_data)

        # 3) 当前用户消息
        if user_message:
            messages.append({
                "role": MessageRoles.USER,
                "content": user_message
            })

        # 校验
        self._validate_messages(messages)

       

        return messages


    def _add_intelligent_history_messages(self, messages: List[Dict], shared_data: Dict[str, Any]) -> None:
        """
        添加智能优化的历史对话消息，使用LLM上下文（已压缩）

        Args:
            messages: 消息列表
            shared_data: 共享数据
        """
        # 从统一上下文获取LLM上下文（已经过智能压缩）
        llm_context_messages = self.context.llm_context

        if not llm_context_messages:
            return

        # 转换为兼容格式
        recent_messages = []
        for msg in llm_context_messages:
            recent_messages.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata or {}
            })

        # 按照OpenAI标准格式处理历史消息
        for msg in recent_messages:
            if msg.get("role") not in [MessageRoles.USER, MessageRoles.ASSISTANT]:
                continue

            # 构建基础消息
            message_dict = {
                "role": msg["role"],
                "content": msg.get("content", "")
            }

            # 正确处理assistant消息中的工具调用
            if (msg.get("role") == MessageRoles.ASSISTANT and
                msg.get("metadata", {}).get("tool_calls")):

                tool_calls = msg["metadata"]["tool_calls"]
                if tool_calls:
                    # 转换为OpenAI Function Calling标准格式
                    openai_tool_calls = self._convert_to_openai_tool_calls(tool_calls)

                    if openai_tool_calls:
                        message_dict["tool_calls"] = openai_tool_calls
                        messages.append(message_dict)

                        # 添加对应的工具结果消息
                        self._add_tool_result_messages(messages, tool_calls)
                        continue

            # 普通消息直接添加
            messages.append(message_dict)

    def _convert_to_openai_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将内部工具调用格式转换为OpenAI标准格式

        Args:
            tool_calls: 内部工具调用列表

        Returns:
            OpenAI标准格式的工具调用列表
        """
        openai_tool_calls = []

        for tc in tool_calls:
            if not tc.get("success", False):  # 只包含成功的工具调用
                continue

            import json
            # 确保arguments是JSON字符串格式
            arguments = tc.get("arguments", {})
            if isinstance(arguments, dict):
                arguments_str = json.dumps(arguments, ensure_ascii=False)
            else:
                arguments_str = str(arguments)

            openai_tool_calls.append({
                "id": tc.get("call_id", f"call_{len(openai_tool_calls)}"),
                "type": "function",
                "function": {
                    "name": tc.get("tool_name", "unknown"),
                    "arguments": arguments_str
                }
            })

        return openai_tool_calls

    def _add_tool_result_messages(self, messages: List[Dict], tool_calls: List[Dict[str, Any]]) -> None:
        """
        添加工具结果消息

        Args:
            messages: 消息列表
            tool_calls: 工具调用列表
        """
        for i, tc in enumerate(tool_calls):
            if not tc.get("success", False):
                continue

            import json
            # 确保tool_call_id与上面的id匹配
            call_id = tc.get("call_id", f"call_{i}")
            tool_result = tc.get("result", {})

            # 确保content是字符串格式
            if isinstance(tool_result, dict):
                content = json.dumps(tool_result, ensure_ascii=False)
            else:
                content = str(tool_result)

            messages.append({
                "role": MessageRoles.TOOL,
                "tool_call_id": call_id,
                "content": content
            })

    def _validate_messages(self, messages: List[Dict]) -> None:
        """
        验证消息格式的正确性

        Args:
            messages: 消息列表
        """
        for i, msg in enumerate(messages):
            role = msg.get("role")

            # 验证必需字段
            if not role:
                print(f"⚠️ [MessageBuilder] 消息{i}缺少role字段")
                continue

            if role not in [MessageRoles.SYSTEM, MessageRoles.USER, MessageRoles.ASSISTANT, MessageRoles.TOOL]:
                print(f"⚠️ [MessageBuilder] 消息{i}包含无效role: {role}")

            # 验证tool消息格式
            if role == MessageRoles.TOOL:
                if not msg.get("tool_call_id"):
                    print(f"⚠️ [MessageBuilder] Tool消息{i}缺少tool_call_id")
                if not msg.get("content"):
                    print(f"⚠️ [MessageBuilder] Tool消息{i}缺少content")

            # 验证assistant消息中的tool_calls格式
            if role == MessageRoles.ASSISTANT and "tool_calls" in msg:
                tool_calls = msg["tool_calls"]
                if not isinstance(tool_calls, list):
                    print(f"⚠️ [MessageBuilder] Assistant消息{i}的tool_calls不是列表格式")
                else:
                    for j, tc in enumerate(tool_calls):
                        if not tc.get("id"):
                            print(f"⚠️ [MessageBuilder] Tool call {j}缺少id")
                        if not tc.get("function", {}).get("name"):
                            print(f"⚠️ [MessageBuilder] Tool call {j}缺少function.name")

   