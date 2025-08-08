"""
重构后的ReAct Orchestrator Node

基于Function Calling的ReAct主控制器，采用模块化设计，降低代码复杂度。
将原来的单一大类拆分为多个专门的组件，每个组件负责特定的功能。
"""

import time
from typing import Dict, List, Any
from pocketflow import AsyncNode

# 导入OpenAI SDK和Function Calling工具
from utils.openai_client import get_openai_client
from agent.function_calling import get_agent_function_definitions

# 导入重构后的组件
from .constants import (
    StateKeys, ErrorMessages,
    DefaultValues
)
from .message_builder import MessageBuilder
from .tool_executor import ToolExecutor
from .state_manager import StateManager
from .stream_handler import StreamHandler


class ReActOrchestratorRefactored(AsyncNode):
    """重构后的ReAct主控制器 - 模块化设计"""

    def __init__(self):
        super().__init__()
        self.name = "ReActOrchestratorRefactored"
        self.description = "基于Function Calling的模块化ReAct主控制器"

        # 初始化OpenAI客户端
        self.openai_client = get_openai_client()

        # 获取可用的Function Calling工具
        self.available_tools = get_agent_function_definitions()

        # 初始化组件
        self.message_builder = MessageBuilder()
        self.tool_executor = ToolExecutor()
        self.state_manager = StateManager()
        # DecisionEngine已移除，让LLM完全负责决策
        self.stream_handler = StreamHandler(self.available_tools, self.tool_executor)

        # 性能统计
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tool_calls": 0
        }

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """异步准备ReAct执行环境"""
        try:
            print(f"🔍 [DEBUG] 准备阶段开始，shared类型: {type(shared)}")
            print(f"🔍 [DEBUG] shared是否为None: {shared is None}")

            # 获取最新用户消息
            print(f"🔍 [DEBUG] 调用get_user_message_from_history...")
            user_message = self.state_manager.get_user_message_from_history(shared)
            print(f"🔍 [DEBUG] 用户消息: {user_message}")

            # 获取当前状态
            current_stage = shared.get(StateKeys.CURRENT_STAGE, DefaultValues.DEFAULT_STAGE)

            # 构建状态描述
            print(f"🔍 [DEBUG] 调用build_state_description...")
            state_info = self.state_manager.build_state_description(shared, user_message)
            print(f"🔍 [DEBUG] build_state_description完成")

            return {
                "success": True,
                "user_message": user_message,
                "current_stage": current_stage,
                "state_info": state_info,
                "shared_data": shared
            }

        except Exception as e:
            print(f"🔍 [DEBUG] 准备阶段异常: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"{ErrorMessages.REACT_PREP_FAILED}: {str(e)}"}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步ReAct推理和决策逻辑 - 基于Function Calling"""
        start_time = time.time()
        self.performance_stats["total_requests"] += 1
        
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])

            user_message = prep_result["user_message"]
            state_info = prep_result["state_info"]
            shared_data = prep_result.get("shared_data", {})

            # 构建对话消息（使用增强版本，包含工具执行历史）
            messages = self.message_builder.build_enhanced_conversation_messages(
                user_message, state_info, shared_data
            )

            print(f"🔍 [DEBUG] 准备调用LLM，消息数量: {len(messages)}")
            print(f"🔍 [DEBUG] 可用工具数量: {len(self.available_tools)}")

            # 检查是否有流式回调
            stream_callback = shared_data.get(StateKeys.STREAM_CALLBACK)

            if stream_callback:
                # 使用流式Function Calling
                print(f"🔍 [DEBUG] 使用流式Function Calling...")
                result = await self.stream_handler.execute_with_function_calling_stream(
                    messages, stream_callback, shared_data
                )
                print(f"🔍 [DEBUG] 流式Function Calling完成")
            else:
                # 使用标准Function Calling
                print(f"🔍 [DEBUG] 使用标准Function Calling...")
                result = await self._execute_with_function_calling(messages, shared_data)
                print(f"🔍 [DEBUG] 标准Function Calling完成")

            # 更新性能统计
            self.performance_stats["successful_requests"] += 1
            self.performance_stats["total_tool_calls"] += len(result.get("tool_calls", []))
            
            response_time = time.time() - start_time
            self._update_average_response_time(response_time)

            return result

        except Exception as e:
            print(f"❌ ReAct执行失败: {e}")
            self.performance_stats["failed_requests"] += 1
            
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
        """异步更新共享状态 - 简化版，让LLM完全负责决策"""
        try:
            if "error" in exec_res:
                shared["react_error"] = exec_res["error"]
                return "error"

            # 更新ReAct循环计数
            self.state_manager.increment_react_cycle(shared)

            # 添加AI回复到对话历史
            user_message = exec_res.get("user_message", "")
            tool_calls = exec_res.get("tool_calls", [])
            reasoning = exec_res.get("reasoning", "")

            if user_message:
                self.state_manager.add_assistant_message_to_history(
                    shared, user_message, tool_calls, reasoning
                )

            # 处理工具调用结果
            if tool_calls:
                print(f"🔍 [DEBUG] 处理 {len(tool_calls)} 个工具调用结果")
                for tool_call in tool_calls:
                    tool_name = tool_call.get("tool_name")
                    tool_result = tool_call.get("result")
                    tool_args = tool_call.get("arguments", {})
                    execution_time = tool_call.get("execution_time")

                    print(f"🔍 [DEBUG] 工具: {tool_name}, 成功: {tool_result.get('success') if tool_result else 'None'}")
                    print(f"🔍 [DEBUG] 工具调用完整结构: {tool_call}")

                    # 记录工具执行历史
                    if tool_name and tool_result:
                        self.state_manager.record_tool_execution(
                            shared, tool_name, tool_args, tool_result, execution_time
                        )

                    # 更新共享状态（仅成功的工具调用）
                    print(f"🔍 [DEBUG] 准备更新共享状态: tool_name={tool_name}, tool_result存在={bool(tool_result)}, 成功={tool_result.get('success') if tool_result else 'None'}")
                    if tool_name and tool_result and tool_result.get("success"):
                        print(f"🔍 [DEBUG] 调用update_shared_state_with_tool_result")
                        self.state_manager.update_shared_state_with_tool_result(
                            shared, tool_name, tool_result
                        )
                    else:
                        print(f"🔍 [DEBUG] 跳过状态更新，条件不满足")

            # 简化路由：总是等待用户，让LLM在回复中自然引导下一步
            return "wait_for_user"

        except Exception as e:
            print(f"❌ ReAct post处理失败: {e}")
            shared["react_post_error"] = str(e)
            return "error"

    async def _execute_with_function_calling(
        self, 
        messages: List[Dict[str, str]], 
        shared_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """使用Function Calling执行ReAct逻辑 - 支持混合模式"""
        try:
            # 这些调试信息不再直接打印，避免干扰CLI界面
            # print(LogMessages.PREPARING_OPENAI_CALL.format(len(self.available_tools)))
            # print(LogMessages.MESSAGE_COUNT.format(len(messages)))

            # 启用并行工具调用
            print(f"🔍 [DEBUG] 开始调用OpenAI API...")
            response = await self.openai_client.chat_completion_async(
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                parallel_tool_calls=True
            )
            print(f"🔍 [DEBUG] OpenAI API调用成功")

            print("🔍 [DEBUG] 收到OpenAI响应")

            # 处理响应
            choice = response.choices[0]
            message = choice.message

            print(f"🔍 [DEBUG] LLM原生输出内容: {message.content}")
            print(f"🔍 [DEBUG] 是否有工具调用: {bool(message.tool_calls)}")
            if message.tool_calls:
                print(f"🔍 [DEBUG] 工具调用数量: {len(message.tool_calls)}")
                for i, tool_call in enumerate(message.tool_calls):
                    print(f"🔍 [DEBUG] 工具{i+1}: {tool_call.function.name}")
            print("🔍 [DEBUG] =" * 50)
            
            # 提取助手回复
            assistant_message = message.content or ""

            # 处理工具调用（支持多个并行调用）
            tool_calls = []

            # 检查标准的OpenAI Function Calling格式
            if message.tool_calls:
                # print(LogMessages.TOOL_CALLS_DETECTED.format(len(message.tool_calls)))
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
                "reasoning": self._build_simple_reasoning(tool_calls, assistant_message),
                "confidence": DefaultValues.DEFAULT_CONFIDENCE,
                "decision_success": True,
                "execution_mode": "parallel" if len(tool_calls) > 1 else "single"
            }

        except Exception as e:
            print(f"❌ Function Calling执行失败: {e}")
            return {
                "error": f"{ErrorMessages.FUNCTION_CALLING_FAILED}: {str(e)}",
                "user_message": ErrorMessages.GENERIC_ERROR,
                "decision_success": False
            }


    def _build_simple_reasoning(
        self,
        tool_calls: List[Dict[str, Any]],
        assistant_message: str
    ) -> str:
        """
        构建简单的推理说明（替代DecisionEngine）

        Args:
            tool_calls: 工具调用结果列表
            assistant_message: 助手消息

        Returns:
            推理说明字符串
        """
        if not tool_calls:
            return "LLM选择进行对话交互，未调用工具"

        successful_tools = [tc["tool_name"] for tc in tool_calls if tc.get("success", False)]
        failed_tools = [tc["tool_name"] for tc in tool_calls if not tc.get("success", False)]

        reasoning_parts = [f"LLM决策执行了 {len(tool_calls)} 个工具调用"]

        if successful_tools:
            reasoning_parts.append(f"成功: {', '.join(successful_tools)}")
        if failed_tools:
            reasoning_parts.append(f"失败: {', '.join(failed_tools)}")

        return "; ".join(reasoning_parts)

    def _update_average_response_time(self, response_time: float) -> None:
        """更新平均响应时间"""
        total_requests = self.performance_stats["total_requests"]
        current_avg = self.performance_stats["average_response_time"]
        
        # 计算新的平均值
        new_avg = ((current_avg * (total_requests - 1)) + response_time) / total_requests
        self.performance_stats["average_response_time"] = new_avg

    def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        stats = self.performance_stats.copy()
        stats.update({
            "tool_executor_stats": self.tool_executor.get_execution_stats()
            # DecisionEngine已移除，LLM负责所有决策
        })
        return stats

    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self.performance_stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "total_tool_calls": 0
        }
        self.tool_executor.reset_execution_stats()
