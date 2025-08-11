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

        # 2) 添加优化后的历史消息（自动附带历史工具调用及其tool结果）
        self._add_optimized_history_messages(messages, shared_data, max_rounds=3)

        # 3) 当前用户消息
        if user_message:
            messages.append({
                "role": MessageRoles.USER,
                "content": user_message
            })

        # 校验
        self._validate_messages(messages)

        # 调试输出（与现有日志风格保持一致）
        try:
            print(f"🔍 [MessageBuilder] 构建的消息数量: {len(messages)}")
            for idx, msg in enumerate(messages):
                print(f"🔍 [MessageBuilder] 消息{idx}: {msg.get('role', '')}")
        except Exception:
            # 调试输出失败不应影响主流程
            pass

        return messages


    def _add_optimized_history_messages(self, messages: List[Dict], shared_data: Dict[str, Any], max_rounds: int = 3) -> None:
        """
        添加优化的历史对话消息，限制上下文长度

        Args:
            messages: 消息列表
            shared_data: 共享数据
            max_rounds: 最大对话轮数
        """
        # 从统一上下文获取消息历史
        context_messages = self.context.get_messages(limit=max_rounds * 4)

        if not context_messages:
            return

        # 转换为兼容格式
        recent_messages = []
        for msg in context_messages:
            recent_messages.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata or {}
            })

        # 🔧 优化：按照OpenAI标准格式处理历史消息
        for msg in recent_messages:
            if msg.get("role") not in [MessageRoles.USER, MessageRoles.ASSISTANT]:
                continue

            # 构建基础消息
            message_dict = {
                "role": msg["role"],
                "content": msg.get("content", "")
            }

            # 🔧 修复：正确处理assistant消息中的工具调用
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

    def _build_tool_execution_context(self, shared_data: Dict[str, Any]) -> str:
        """
        构建工具执行上下文信息

        Args:
            shared_data: 共享数据（保持兼容性，但实际使用统一上下文）

        Returns:
            工具执行上下文字符串
        """
        # 从统一上下文获取工具执行历史
        tool_history = self.context.tool_history
        if not tool_history:
            return ""

        # 获取最近的成功执行记录
        recent_successful = []
        for record in reversed(tool_history):
            if record.get("success", False):
                tool_name = record.get("tool_name")
                if tool_name and tool_name not in [r["tool_name"] for r in recent_successful]:
                    recent_successful.append({
                        "tool_name": tool_name,
                        "timestamp": record.get("timestamp", 0)
                    })
                    if len(recent_successful) >= 5:  # 最多显示5个
                        break

        if not recent_successful:
            return ""

        context_parts = ["本次会话中已成功执行的工具："]
        for record in reversed(recent_successful):  # 按时间顺序显示
            import time
            timestamp = record["timestamp"]
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            context_parts.append(f"- {record['tool_name']} (执行时间: {time_str})")

        context_parts.append("\n注意：避免重复调用相同的工具，但可以根据用户需求调用其他不同的工具。如果用户明确同意或要求执行多个工具，应该按计划执行。")

        return "\n".join(context_parts)
