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

            # 使用Function Calling执行（从shared_data中获取流式响应参数）
            result = await self._execute_with_function_calling(messages, shared_data)

            return result

        except Exception as e:
            print(f"❌ ReAct执行失败: {e}")
            
            return {
                "error": f"{ErrorMessages.REACT_EXEC_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False
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
            print(f"❌ ReAct post处理失败: {e}")
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
        shared: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """使用Function Calling执行ReAct逻辑（支持流式响应）"""
        try:
            # 检查是否启用流式响应
            streaming_session = shared.get("streaming_session") if shared else None
            streaming_callbacks = shared.get("streaming_callbacks", {}) if shared else {}

            if streaming_session and streaming_callbacks:
                # 流式响应模式
                return await self._execute_with_streaming(
                    messages, streaming_session, streaming_callbacks
                )
            else:
                # 非流式响应模式（向后兼容）
                return await self._execute_without_streaming(messages)

        except Exception as e:
            return {
                "user_message": "",
                "tool_calls": [],
                "reasoning": f"执行失败: {str(e)}",
                "confidence": 0.0,
                "decision_success": False,
                "execution_mode": "error"
            }

    async def _execute_without_streaming(
        self,
        messages: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """非流式执行（向后兼容）"""
        # 使用新的API接口：分离系统提示词和消息
        response = await self.openai_client.chat_completion_async(
            system_prompt=SystemPrompts.FUNCTION_CALLING_SYSTEM_PROMPT,
            messages=messages,
            tools=self.available_tools,
            tool_choice="auto",
            parallel_tool_calls=True
        )

        # 处理响应
        choice = response.choices[0]
        message = choice.message

        # 提取助手回复
        assistant_message = message.content or ""

        # 处理工具调用（支持多个并行调用）
        tool_calls = []

        # 检查标准的OpenAI Function Calling格式
        if message.tool_calls:
            tool_calls = await self.tool_executor.execute_tools_parallel(message.tool_calls)

        # 如果没有标准格式的工具调用，检查自定义格式
        elif assistant_message and "<tool_call>" in assistant_message:
            print("🔧 检测到自定义格式的工具调用")
            custom_tool_calls = self.tool_executor.parse_custom_tool_calls(assistant_message)

            if custom_tool_calls:
                tool_calls = await self.tool_executor.execute_custom_tool_calls(custom_tool_calls)
                # 清理assistant_message中的工具调用标记
                assistant_message = self.tool_executor.clean_tool_call_markers(assistant_message)

        # LLM已经通过Function Calling做出了决策，我们只需要处理结果
        return {
            "user_message": assistant_message,
            "tool_calls": tool_calls,
            "reasoning": f"LLM执行了{len(tool_calls)}个工具调用" if tool_calls else "LLM进行了对话回复",
            "confidence": DefaultValues.DEFAULT_CONFIDENCE,
            "decision_success": True,
            "execution_mode": "parallel" if len(tool_calls) > 1 else "single"
        }

    async def _execute_with_streaming(
        self,
        messages: List[Dict[str, str]],
        streaming_session,
        streaming_callbacks: Dict[str, Any]
    ) -> Dict[str, Any]:
        """流式执行（实时响应）"""
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

            # 收集流式响应
            assistant_message = ""
            tool_calls_data = []
            chunk_index = 0

            async for chunk in stream:
                if chunk.choices and len(chunk.choices) > 0:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 处理内容片段
                    if delta.content:
                        assistant_message += delta.content

                        # 触发流式内容回调
                        if StreamCallbackType.ON_LLM_CHUNK in streaming_callbacks:
                            await streaming_callbacks[StreamCallbackType.ON_LLM_CHUNK](
                                streaming_session,
                                chunk_content=delta.content,
                                chunk_index=chunk_index
                            )
                        chunk_index += 1

                    # 处理工具调用
                    if delta.tool_calls:
                        for tool_call in delta.tool_calls:
                            # 收集工具调用数据
                            if tool_call.function:
                                tool_calls_data.append(tool_call)

            # 触发LLM结束回调
            if StreamCallbackType.ON_LLM_END in streaming_callbacks:
                await streaming_callbacks[StreamCallbackType.ON_LLM_END](
                    streaming_session,
                    complete_message=assistant_message
                )

            # 处理工具调用
            tool_calls = []
            if tool_calls_data:
                # 触发工具调用开始回调
                for tool_call in tool_calls_data:
                    if StreamCallbackType.ON_TOOL_START in streaming_callbacks and tool_call.function:
                        # 解析arguments（可能是JSON字符串）
                        import json
                        try:
                            arguments = json.loads(tool_call.function.arguments) if isinstance(tool_call.function.arguments, str) else tool_call.function.arguments
                        except:
                            arguments = tool_call.function.arguments

                        await streaming_callbacks[StreamCallbackType.ON_TOOL_START](
                            streaming_session,
                            tool_name=tool_call.function.name,
                            arguments=arguments
                        )

                # 执行工具调用
                tool_calls = await self.tool_executor.execute_tools_parallel(tool_calls_data)

                # 触发工具调用结束回调
                for tool_call in tool_calls:
                    if StreamCallbackType.ON_TOOL_END in streaming_callbacks:
                        await streaming_callbacks[StreamCallbackType.ON_TOOL_END](
                            streaming_session,
                            tool_name=tool_call.get("tool_name", "unknown"),
                            result=tool_call.get("result", {}),
                            execution_time=tool_call.get("execution_time", 0),
                            success=tool_call.get("success", True),
                            error_message=tool_call.get("error")
                        )

            return {
                "user_message": assistant_message,
                "tool_calls": tool_calls,
                "reasoning": f"LLM执行了{len(tool_calls)}个工具调用" if tool_calls else "LLM进行了对话回复",
                "confidence": DefaultValues.DEFAULT_CONFIDENCE,
                "decision_success": True,
                "execution_mode": "parallel" if len(tool_calls) > 1 else "single"
            }

        except Exception as e:
            print(f"❌ 流式Function Calling执行失败: {e}")
            return {
                "error": f"{ErrorMessages.FUNCTION_CALLING_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False
            }


