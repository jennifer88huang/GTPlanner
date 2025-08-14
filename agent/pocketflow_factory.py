"""
PocketFlow工厂 - 无状态版本

负责从AgentContext创建pocketflow shared字典，以及从shared字典中提取AgentResult。
实现上下文数据和pocketflow格式之间的转换。

设计原则：
1. 纯静态方法：所有方法都是静态的，不维护任何状态
2. 单向转换：只负责数据格式转换，不修改原始数据
3. 简洁实用：专注核心功能，避免过度设计
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from .context_types import (
    AgentContext, AgentResult, Message, ToolExecution,
    MessageRole
)


class PocketFlowSharedFactory:
    """PocketFlow Shared字典工厂 - 纯静态方法"""
    
    @staticmethod
    def create_shared_dict(
        user_input: str,
        context: AgentContext
    ) -> Dict[str, Any]:
        """
        从用户输入和AgentContext创建pocketflow shared字典

        Args:
            user_input: 当前用户输入
            context: Agent上下文（只读，可能已压缩）

        Returns:
            pocketflow shared字典

        Raises:
            ValueError: 当上下文数据无效时
        """
        # 验证上下文数据
        PocketFlowSharedFactory._validate_context(context)
        # 构建对话历史（包含当前用户输入）
        # 注意：context.dialogue_history 可能已经被客户端压缩
        current_messages = []

        # 添加历史消息（可能是压缩后的）
        for msg in context.dialogue_history:
            current_messages.append({
                "role": msg.role.value,
                "content": msg.content
            })

        # 添加当前用户输入
        current_messages.append({
            "role": "user",
            "content": user_input
        })
        
        # 构建基础shared字典
        shared = {
            # 核心对话数据
            "dialogue_history": {"messages": current_messages},
            "session_id": context.session_id,

            # 工具执行结果数据（统一字段名）- 只设置非空值，避免覆盖工具执行结果
            # 注意：工具节点会在执行后设置这些字段，这里只设置已有的非空值
        }

        # 只设置已存在且非空的工具执行结果
        for key in ["recommended_tools", "research_findings", "short_planning"]:
            value = context.tool_execution_results.get(key)
            if value is not None:
                shared[key] = value

        # 继续添加其他字段
        shared.update({
            # 工具执行历史
            "tool_execution_history": [
                {
                    "id": te.id,
                    "tool_name": te.tool_name,
                    "arguments": te.arguments,
                    "result": te.result,
                    "execution_time": te.execution_time,
                    "timestamp": te.timestamp,
                    "success": te.success,
                    "error_message": te.error_message
                }
                for te in context.tool_execution_history
            ],

            # 流程控制数据
            "flow_start_time": None,  # 将在prep_async中设置
            "flow_metadata": {},
            "react_error": None,
            "react_post_error": None,

            # 会话元数据
            "session_metadata": context.session_metadata.copy(),
            "last_updated": context.last_updated,

            # Agent执行过程中新增的内容（初始化为空）
            "new_assistant_messages": [],  # 新增的助手消息
            "new_tool_executions": [],     # 新增的工具执行记录
        })
        
        return shared
    
    @staticmethod
    def create_agent_result(
        shared: Dict[str, Any],
        execution_time: Optional[float] = None
    ) -> AgentResult:
        """
        从执行后的shared字典创建AgentResult

        Args:
            shared: 执行后的shared字典
            execution_time: 执行时间

        Returns:
            AgentResult对象
        """
        try:
            # 检查是否有错误
            error = shared.get("react_error") or shared.get("react_post_error")

            if error:
                return AgentResult.create_error(
                    error=str(error),
                    metadata=shared.get("flow_metadata", {}),
                    execution_time=execution_time
                )

            # 直接从预留字段获取新增内容
            new_messages = PocketFlowSharedFactory._parse_new_messages(
                shared.get("new_assistant_messages", [])
            )

            new_tool_executions = PocketFlowSharedFactory._parse_new_tool_executions(
                shared.get("new_tool_executions", [])
            )

            # 提取工具执行结果更新 - 从shared字典中提取工具执行结果
            tool_execution_results_updates = {}

            # 检查各个工具的执行结果（统一字段名）
            if "recommended_tools" in shared:
                tool_execution_results_updates["recommended_tools"] = shared["recommended_tools"]

            if "research_findings" in shared:
                tool_execution_results_updates["research_findings"] = shared["research_findings"]

            if "short_planning" in shared:
                tool_execution_results_updates["short_planning"] = shared["short_planning"]

            result = AgentResult.create_success(
                new_assistant_messages=new_messages,
                new_tool_executions=new_tool_executions,
                tool_execution_results_updates=tool_execution_results_updates,
                metadata=shared.get("flow_metadata", {}),
                execution_time=execution_time
            )

            return result

        except Exception as e:
            return AgentResult.create_error(
                error=f"Failed to create agent result: {str(e)}",
                execution_time=execution_time
            )
    
    @staticmethod
    def _parse_new_messages(message_data_list: List[Dict[str, Any]]) -> List[Message]:
        """解析新增的消息数据"""
        new_messages = []

        for msg_data in message_data_list:
            try:
                message = Message(
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=msg_data["timestamp"],
                    metadata=msg_data.get("metadata", {}),
                    tool_calls=msg_data.get("tool_calls", [])
                )
                new_messages.append(message)
            except (KeyError, ValueError) as e:
                print(f"Warning: Failed to parse message: {e}")
                continue

        return new_messages
    
    @staticmethod
    def _parse_new_tool_executions(execution_data_list: List[Dict[str, Any]]) -> List[ToolExecution]:
        """解析新增的工具执行数据"""
        new_executions = []

        for exec_data in execution_data_list:
            try:
                tool_execution = ToolExecution(
                    id=exec_data["id"],
                    tool_name=exec_data["tool_name"],
                    arguments=exec_data["arguments"],
                    result=exec_data["result"],
                    execution_time=exec_data.get("execution_time"),
                    timestamp=exec_data["timestamp"],
                    success=exec_data["success"],
                    error_message=exec_data.get("error_message")
                )
                new_executions.append(tool_execution)
            except (KeyError, ValueError) as e:
                print(f"Warning: Failed to parse tool execution: {e}")
                continue

        return new_executions



    @staticmethod
    def _validate_context(context: AgentContext) -> None:
        """
        验证AgentContext的完整性

        Args:
            context: 要验证的上下文

        Raises:
            ValueError: 当上下文数据无效时
        """
        if not context.session_id:
            raise ValueError("session_id不能为空")

        if not isinstance(context.dialogue_history, list):
            raise ValueError("dialogue_history必须是列表")

        if not isinstance(context.tool_execution_history, list):
            raise ValueError("tool_execution_history必须是列表")

        if not isinstance(context.tool_execution_results, dict):
            raise ValueError("tool_execution_results必须是字典")

        if not isinstance(context.session_metadata, dict):
            raise ValueError("session_metadata必须是字典")
    

    



# 便捷函数

def create_pocketflow_shared(
    user_input: str,
    context: AgentContext
) -> Dict[str, Any]:
    """
    创建pocketflow shared字典的便捷函数

    Args:
        user_input: 用户输入
        context: Agent上下文

    Returns:
        pocketflow shared字典
    """
    return PocketFlowSharedFactory.create_shared_dict(user_input, context)


def create_agent_result(
    shared: Dict[str, Any],
    execution_time: Optional[float] = None
) -> AgentResult:
    """
    创建Agent结果的便捷函数

    Args:
        shared: 执行后的shared字典
        execution_time: 执行时间

    Returns:
        AgentResult对象
    """
    return PocketFlowSharedFactory.create_agent_result(shared, execution_time)
