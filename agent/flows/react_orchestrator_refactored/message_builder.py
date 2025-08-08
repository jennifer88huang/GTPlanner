"""
消息构建器

负责构建Function Calling对话消息，分离消息构建逻辑。
"""

from typing import Dict, List, Any
from .constants import MessageRoles, SystemPrompts, DefaultValues, StateKeys


class MessageBuilder:
    """消息构建器类"""
    
    def __init__(self):
        self.system_prompt = SystemPrompts.FUNCTION_CALLING_SYSTEM_PROMPT
    
    def build_conversation_messages(
        self, 
        user_message: str, 
        state_info: str, 
        shared_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        构建Function Calling对话消息
        
        Args:
            user_message: 用户消息
            state_info: 状态信息
            shared_data: 共享数据
            
        Returns:
            消息列表
        """
        messages = []
        
        # 添加系统消息
        messages.append({
            "role": MessageRoles.SYSTEM,
            "content": self.system_prompt
        })
        
        # 添加历史对话
        self._add_history_messages(messages, shared_data)
        
        # 添加当前用户消息和状态信息
        if user_message:
            current_content = f"用户消息: {user_message}\n\n当前状态:\n{state_info}"
            messages.append({
                "role": MessageRoles.USER,
                "content": current_content
            })
        
        return messages
    
    def _add_history_messages(self, messages: List[Dict], shared_data: Dict[str, Any]) -> None:
        """
        添加历史对话消息
        
        Args:
            messages: 消息列表
            shared_data: 共享数据
        """
        dialogue_history = shared_data.get(StateKeys.DIALOGUE_HISTORY, {})
        history_messages = dialogue_history.get("messages", [])
        
        # 只保留最近的几轮对话，避免上下文过长
        recent_messages = (
            history_messages[-DefaultValues.MAX_HISTORY_MESSAGES:] 
            if len(history_messages) > DefaultValues.MAX_HISTORY_MESSAGES 
            else history_messages
        )
        
        for msg in recent_messages:
            if msg.get("role") in [MessageRoles.USER, MessageRoles.ASSISTANT]:
                # 构建消息内容，包含工具调用信息
                content = msg["content"]

                # 如果是助手消息且包含工具调用信息，添加到内容中
                if (msg.get("role") == MessageRoles.ASSISTANT and
                    msg.get("metadata", {}).get("tool_calls")):

                    tool_calls = msg["metadata"]["tool_calls"]
                    if tool_calls:
                        tool_info = self._format_tool_calls_for_context(tool_calls)
                        content = f"{content}\n\n[工具调用记录: {tool_info}]"

                messages.append({
                    "role": msg["role"],
                    "content": content
                })
    
    def build_tool_result_messages(
        self, 
        messages: List[Dict], 
        collected_content: str,
        tool_calls_detected: List[Any],
        tool_results: List[Dict[str, Any]]
    ) -> List[Dict]:
        """
        构建包含工具结果的消息
        
        Args:
            messages: 原始消息列表
            collected_content: 收集的内容
            tool_calls_detected: 检测到的工具调用
            tool_results: 工具执行结果
            
        Returns:
            包含工具结果的消息列表
        """
        messages_with_results = messages.copy()
        
        # 添加助手的工具调用消息
        assistant_message = {
            "role": MessageRoles.ASSISTANT, 
            "content": collected_content
        }
        
        if tool_calls_detected:
            assistant_message["tool_calls"] = [
                {
                    "id": getattr(tc, 'id', f"call_{i}"),
                    "type": "function",
                    "function": {
                        "name": getattr(tc.function, 'name', 'unknown'),
                        "arguments": getattr(tc.function, 'arguments', '{}')
                    }
                } for i, tc in enumerate(tool_calls_detected)
            ]
        
        messages_with_results.append(assistant_message)
        
        # 添加工具结果消息
        for tool_result in tool_results:
            import json
            messages_with_results.append({
                "role": MessageRoles.TOOL,
                "tool_call_id": tool_result.get("call_id", "unknown"),
                "content": json.dumps(tool_result.get("result", {}), ensure_ascii=False)
            })
        
        return messages_with_results
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        设置系统提示词

        Args:
            prompt: 新的系统提示词
        """
        self.system_prompt = prompt

    def _format_tool_calls_for_context(self, tool_calls: List[Dict[str, Any]]) -> str:
        """
        格式化工具调用信息用于上下文传递

        Args:
            tool_calls: 工具调用列表

        Returns:
            格式化的工具调用信息字符串
        """
        if not tool_calls:
            return "无"

        tool_info_parts = []
        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name", "未知工具")
            success = tool_call.get("success", False)
            status = "成功" if success else "失败"

            # 添加简要的结果信息
            result_summary = ""
            if success and tool_call.get("result"):
                result = tool_call["result"]
                if isinstance(result, dict):
                    # 提取关键信息
                    if "project_overview" in result:
                        result_summary = " - 已生成需求分析"
                    elif "milestones" in result:
                        result_summary = " - 已生成项目规划"
                    elif "topics" in result:
                        result_summary = " - 已完成技术调研"
                    elif "architecture" in result:
                        result_summary = " - 已生成架构设计"

            tool_info_parts.append(f"{tool_name}({status}){result_summary}")

        return ", ".join(tool_info_parts)

    def build_enhanced_conversation_messages(
        self,
        user_message: str,
        state_info: str,
        shared_data: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        构建增强的Function Calling对话消息，包含工具执行历史

        Args:
            user_message: 用户消息
            state_info: 状态信息
            shared_data: 共享数据

        Returns:
            消息列表
        """
        messages = []

        # 添加系统消息
        messages.append({
            "role": MessageRoles.SYSTEM,
            "content": self.system_prompt
        })

        # 添加工具执行历史摘要到系统消息中
        tool_history = self._build_tool_execution_context(shared_data)
        print(f"🔍 [DEBUG] 工具执行历史: {tool_history}")
        if tool_history:
            messages.append({
                "role": MessageRoles.SYSTEM,
                "content": f"工具执行历史摘要：\n{tool_history}"
            })

        # 添加历史对话
        self._add_history_messages(messages, shared_data)

        # 添加当前用户消息和状态信息
        if user_message:
            current_content = f"用户消息: {user_message}\n\n当前状态:\n{state_info}"
            messages.append({
                "role": MessageRoles.USER,
                "content": current_content
            })

        print(f"🔍 [DEBUG] 构建的消息数量: {len(messages)}")
        print(f"🔍 [DEBUG] 最后一条消息内容预览: {messages[-1]['content'][:200]}...")

        # 调试：打印所有消息的角色和长度
        for i, msg in enumerate(messages):
            print(f"🔍 [DEBUG] 消息{i+1}: {msg['role']}, 长度: {len(msg['content'])}")

        return messages

    def _build_tool_execution_context(self, shared_data: Dict[str, Any]) -> str:
        """
        构建工具执行上下文信息

        Args:
            shared_data: 共享数据

        Returns:
            工具执行上下文字符串
        """
        tool_history = shared_data.get('tool_execution_history', [])
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

        context_parts.append("\n请避免重复调用已成功执行的工具，除非用户明确要求重新执行。")

        return "\n".join(context_parts)
