"""
ReAct Orchestrator Node

基于Function Calling的ReAct主控制器节点，采用模块化设计。
负责处理单次ReAct推理和决策逻辑。
"""


from typing import Dict, List, Any
from pocketflow import AsyncNode

# 导入OpenAI SDK和Function Calling工具
from utils.openai_client import get_openai_client
from agent.function_calling import get_agent_function_definitions

# 导入流式响应类型
from agent.streaming.stream_types import StreamCallbackType
from agent.streaming.stream_interface import StreamingSession

# 导入重构后的组件
from .constants import (
    ErrorMessages,
    DefaultValues, 
    SystemPrompts
)

from .tool_executor import ToolExecutor




class ReActOrchestratorNode(AsyncNode):
    """ReAct主控制器节点 - 模块化设计"""

    def __init__(self):
        super().__init__()
        self.name = "ReActOrchestratorNode"
        self.description = "基于Function Calling的模块化ReAct主控制器节点"

        # 初始化OpenAI客户端
        self.openai_client = get_openai_client()

        # 获取可用的Function Calling工具
        self.available_tools = get_agent_function_definitions()

        # 初始化组件
        self.tool_executor = ToolExecutor()

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """异步准备ReAct执行环境（无状态版本）"""
        try:
            return {
                "success": True,
                "shared_data": shared
            }

        except Exception as e:
            return {"error": f"{ErrorMessages.REACT_PREP_FAILED}: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步ReAct推理和决策逻辑 - 基于Function Calling（支持流式响应）"""

        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            shared_data = prep_result.get("shared_data", {})

            # 直接使用dialogue_history中的messages（完整或压缩过的聊天记录）
            dialogue_history = shared_data.get("dialogue_history", {})
            messages = dialogue_history.get("messages", [])

            # 使用Function Calling执行（传递shared_data作为shared参数）
            result = await self._execute_with_function_calling(messages, shared_data)

            return result

        except Exception as e:
            # 在没有shared字典访问权限时，只能返回错误
            return {
                "error": f"{ErrorMessages.REACT_EXEC_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False,
                "exec_error": str(e)  # 添加详细错误信息供post_async处理
            }

    async def post_async(
        self,
        shared: Dict[str, Any],
        prep_res: Dict[str, Any],
        exec_res: Dict[str, Any]
    ) -> str:
        """异步更新共享状态（无状态版本）"""
        try:
            if "error" in exec_res:
                # 记录exec阶段的错误到shared
                if "errors" not in shared:
                    shared["errors"] = []
                shared["errors"].append({
                    "source": "ReActOrchestratorNode.exec",
                    "error": exec_res.get("exec_error", exec_res["error"]),
                    "timestamp": __import__('time').time()
                })
                shared["react_error"] = exec_res["error"]
                return "error"

            # 更新ReAct循环计数
            self._increment_react_cycle(shared)

            # 获取执行结果
            assistant_message = exec_res.get("user_message", "")
            tool_calls = exec_res.get("tool_calls", [])

            # 如果有助手消息，添加到预留字段
            if assistant_message:
                self._add_assistant_message(shared, assistant_message, tool_calls)

            # 处理工具调用结果
            if tool_calls:
                self._process_tool_calls(shared, tool_calls)

            # 简化路由：总是等待用户，让LLM在回复中自然引导下一步
            return "wait_for_user"

        except Exception as e:
            # 记录错误到shared字典，不打印到控制台
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": "ReActOrchestratorNode.post",
                "error": str(e),
                "timestamp": __import__('time').time()
            })
            shared["react_post_error"] = str(e)
            return "error"



    def _add_assistant_message(self, shared: Dict[str, Any], message: str, tool_calls: List[Dict[str, Any]]) -> None:
        """添加助手消息到预留字段"""
        from datetime import datetime

        assistant_message = {
            "role": "assistant",
            "content": message,
            "timestamp": datetime.now().isoformat(),
            "metadata": {}
        }

        if tool_calls:
            assistant_message["metadata"]["tool_calls"] = tool_calls

        # 添加到预留字段
        if "new_assistant_messages" not in shared:
            shared["new_assistant_messages"] = []

        shared["new_assistant_messages"].append(assistant_message)

    def _process_tool_calls(self, shared: Dict[str, Any], tool_calls: List[Dict[str, Any]]) -> None:
        """处理工具调用结果"""
        import uuid
        from datetime import datetime

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            tool_result = tool_call.get("result")
            tool_args = tool_call.get("arguments", {})
            execution_time = tool_call.get("execution_time")

            if tool_name and tool_result:
                # 创建工具执行记录
                tool_execution = {
                    "id": str(uuid.uuid4()),
                    "tool_name": tool_name,
                    "arguments": tool_args,
                    "result": tool_result,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "success": tool_result.get("success", True),
                    "error_message": tool_result.get("error")
                }

                # 添加到预留字段
                if "new_tool_executions" not in shared:
                    shared["new_tool_executions"] = []

                shared["new_tool_executions"].append(tool_execution)

    def _increment_react_cycle(self, shared: Dict[str, Any]) -> int:
        """增加ReAct循环计数"""
        current_count = shared.get("react_cycle_count", 0)
        new_count = current_count + 1
        shared["react_cycle_count"] = new_count
        return new_count

    async def _execute_with_function_calling(
        self,
        messages: List[Dict[str, str]],
        shared: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用Function Calling执行ReAct逻辑（统一流式架构）"""
        try:
            # 获取流式响应参数
            streaming_session = shared.get("streaming_session")
            streaming_callbacks = shared.get("streaming_callbacks", {})

            # 如果有流式会话，使用流式响应；否则使用简化的非流式处理
            if streaming_session and streaming_callbacks:
                return await self._execute_with_streaming(
                    messages, shared, streaming_session, streaming_callbacks
                )
            else:
                # 简化的非流式处理
                return await self._execute_without_streaming_simple(messages, shared)

        except Exception as e:
            return {
                "user_message": "",
                "tool_calls": [],
                "reasoning": f"执行失败: {str(e)}",
                "confidence": 0.0,
                "decision_success": False,
                "execution_mode": "error"
            }



    async def _execute_with_streaming(
        self,
        messages: List[Dict[str, str]],
        shared: Dict[str, Any],
        streaming_session: StreamingSession,
        streaming_callbacks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """流式执行（统一流式架构）"""
        try:
            # 触发LLM开始回调
            if StreamCallbackType.ON_LLM_START in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_START](streaming_session)

            # 使用流式API（支持system_prompt参数）
            stream = self.openai_client.chat_completion_stream_async(
                system_prompt=SystemPrompts.FUNCTION_CALLING_SYSTEM_PROMPT,
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                parallel_tool_calls=True
            )

            # 收集流式响应 - 使用OpenAI SDK标准格式
            assistant_message_content = ""
            assistant_tool_calls = []
            current_tool_calls = {}
            chunk_index = 0

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 处理内容片段
                    if delta.content:
                        assistant_message_content += delta.content

                        # 触发流式内容回调
                        if StreamCallbackType.ON_LLM_CHUNK in streaming_callbacks:
                            await streaming_callbacks[StreamCallbackType.ON_LLM_CHUNK](
                                streaming_session,
                                chunk_content=delta.content,
                                chunk_index=chunk_index
                            )
                        chunk_index += 1

                    # 处理工具调用 - 使用OpenAI SDK标准格式
                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            index = tool_call_delta.index

                            # 初始化工具调用对象
                            if index not in current_tool_calls:
                                current_tool_calls[index] = {
                                    "id": tool_call_delta.id or "",
                                    "type": "function",
                                    "function": {
                                        "name": "",
                                        "arguments": ""
                                    }
                                }

                            # 累积工具调用信息
                            if tool_call_delta.id:
                                current_tool_calls[index]["id"] = tool_call_delta.id
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_calls[index]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    current_tool_calls[index]["function"]["arguments"] += tool_call_delta.function.arguments

            # 构建完整的assistant消息（OpenAI标准格式）
            assistant_tool_calls = [tool_call for tool_call in current_tool_calls.values() if tool_call["id"]]

            # 构建完整的assistant消息（OpenAI标准格式）
            assistant_message = {
                "role": "assistant",
                "content": assistant_message_content,
                "tool_calls": assistant_tool_calls if assistant_tool_calls else None
            }

            # 触发LLM结束回调
            if StreamCallbackType.ON_LLM_END in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_END](
                    streaming_session,
                    complete_message=assistant_message_content
                )

            # 处理工具调用 - 使用OpenAI SDK标准格式
            if assistant_tool_calls:
                # 将assistant消息添加到历史
                messages.append(assistant_message)

                # 直接使用OpenAI标准格式的工具调用
                tool_calls_data = assistant_tool_calls

                # 🔄 使用统一的递归Function Calling循环处理
                return await self._process_function_calling_cycle(
                    messages, tool_calls_data, streaming_session, streaming_callbacks, recursion_depth=0
                )
            else:
                # 没有工具调用，直接返回LLM的回复
                return {
                    "user_message": assistant_message_content,
                    "tool_calls": [],
                    "reasoning": "LLM直接回复，无需工具调用",
                    "confidence": 0.9,
                    "decision_success": True,
                    "execution_mode": "direct_response"
                }

        except Exception as e:
            # 在流式执行中记录错误到shared（如果可用）
            if "errors" not in shared:
                shared["errors"] = []
            shared["errors"].append({
                "source": "ReActOrchestratorNode.streaming",
                "error": str(e),
                "timestamp": __import__('time').time()
            })
            return {
                "error": f"{ErrorMessages.FUNCTION_CALLING_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False,
                "exec_error": str(e)  # 添加详细错误信息
            }

    async def _process_function_calling_cycle(
        self,
        messages: List[Dict[str, Any]],
        tool_calls: List[Dict[str, Any]],
        streaming_session,
        streaming_callbacks: Dict,
        recursion_depth: int = 0,
        max_recursion_depth: int = 5
    ) -> Dict[str, Any]:
        """
        递归处理Function Calling循环

        Args:
            messages: 消息历史
            tool_calls: 当前需要执行的工具调用
            streaming_session: 流式会话
            streaming_callbacks: 流式回调
            recursion_depth: 当前递归深度
            max_recursion_depth: 最大递归深度限制

        Returns:
            最终的执行结果
        """
        # 防止无限递归
        if recursion_depth >= max_recursion_depth:
            return {
                "user_message": f"已达到最大递归深度({max_recursion_depth})，停止进一步的工具调用。",
                "tool_calls": tool_calls,
                "reasoning": f"递归深度限制，停止在第{recursion_depth}轮",
                "confidence": 0.7,
                "decision_success": True,
                "execution_mode": "recursion_limit_reached"
            }

        try:
            # 触发工具调用开始回调
            for tool_call in tool_calls:
                if StreamCallbackType.ON_TOOL_START in streaming_callbacks:
                    import json
                    try:
                        arguments = json.loads(tool_call["function"]["arguments"])
                    except:
                        arguments = tool_call["function"]["arguments"]

                    await streaming_callbacks[StreamCallbackType.ON_TOOL_START](
                        streaming_session,
                        tool_name=tool_call["function"]["name"],
                        arguments=arguments
                    )

            # 执行工具调用
            tool_execution_results = await self.tool_executor.execute_tools_parallel(
                tool_calls, {}, streaming_session  # 使用空的shared字典，因为这是递归调用
            )

            # 触发工具调用结束回调
            for tool_result in tool_execution_results:
                if StreamCallbackType.ON_TOOL_END in streaming_callbacks:
                    await streaming_callbacks[StreamCallbackType.ON_TOOL_END](
                        streaming_session,
                        tool_name=tool_result.get("tool_name", "unknown"),
                        result=tool_result.get("result", {}),
                        execution_time=tool_result.get("execution_time", 0),
                        success=tool_result.get("success", True),
                        error_message=tool_result.get("error")
                    )

            # 将工具结果添加到消息历史
            for i, tool_result in enumerate(tool_execution_results):
                tool_call_id = tool_calls[i]["id"]
                result_content = json.dumps(tool_result.get("result", {}), ensure_ascii=False)

                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": result_content
                }
                messages.append(tool_message)

            # 再次调用LLM处理工具结果
            if StreamCallbackType.ON_LLM_START in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_START](streaming_session)

            stream = self.openai_client.chat_completion_stream_async(
                system_prompt=SystemPrompts.FUNCTION_CALLING_SYSTEM_PROMPT,
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                parallel_tool_calls=True
            )

            # 收集流式响应
            assistant_message_content = ""
            new_tool_calls = []
            current_tool_calls = {}
            chunk_index = 0

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    if delta.content:
                        assistant_message_content += delta.content
                        if StreamCallbackType.ON_LLM_CHUNK in streaming_callbacks:
                            await streaming_callbacks[StreamCallbackType.ON_LLM_CHUNK](
                                streaming_session,
                                chunk_content=delta.content,
                                chunk_index=chunk_index
                            )
                        chunk_index += 1

                    if delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            index = tool_call_delta.index

                            if index not in current_tool_calls:
                                current_tool_calls[index] = {
                                    "id": tool_call_delta.id or "",
                                    "type": "function",
                                    "function": {"name": "", "arguments": ""}
                                }

                            if tool_call_delta.id:
                                current_tool_calls[index]["id"] = tool_call_delta.id
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    current_tool_calls[index]["function"]["name"] = tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    current_tool_calls[index]["function"]["arguments"] += tool_call_delta.function.arguments

            new_tool_calls = [tool_call for tool_call in current_tool_calls.values() if tool_call["id"]]

            if StreamCallbackType.ON_LLM_END in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_END](
                    streaming_session,
                    complete_message=assistant_message_content
                )

            # 递归处理或返回最终结果
            if new_tool_calls:
                # 添加当前assistant消息到历史
                assistant_message_obj = {
                    "role": "assistant",
                    "content": assistant_message_content,
                    "tool_calls": new_tool_calls
                }
                messages.append(assistant_message_obj)

                # 递归处理新的工具调用
                return await self._process_function_calling_cycle(
                    messages, new_tool_calls, streaming_session, streaming_callbacks,
                    recursion_depth + 1, max_recursion_depth
                )
            else:
                # 没有更多工具调用，返回最终结果
                return {
                    "user_message": assistant_message_content,
                    "tool_calls": [],
                    "reasoning": f"完成{recursion_depth + 1}轮Function Calling循环",
                    "confidence": 0.9,
                    "decision_success": True,
                    "execution_mode": f"multi_turn_complete_depth_{recursion_depth + 1}"
                }

        except Exception as e:
            return {
                "user_message": f"在第{recursion_depth + 1}轮Function Calling中出现错误：{str(e)}",
                "tool_calls": [],
                "reasoning": f"第{recursion_depth + 1}轮执行失败",
                "confidence": 0.0,
                "decision_success": False,
                "execution_mode": "recursion_error"
            }





