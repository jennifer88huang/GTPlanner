"""
流式处理器

负责处理流式Function Calling，提供实时反馈和进度显示。
"""

import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from utils.openai_client import get_openai_client
from .constants import MessageRoles
from .tool_executor import ToolExecutor
from .message_builder import MessageBuilder


class StreamHandler:
    """流式处理器类"""
    
    def __init__(self, available_tools: List[Dict], tool_executor: ToolExecutor):
        self.available_tools = available_tools
        self.tool_executor = tool_executor
        self.openai_client = get_openai_client()
        self.message_builder = MessageBuilder()
    
    async def execute_with_function_calling_stream(
        self,
        messages: List[Dict[str, str]],
        stream_callback: Callable,
        shared_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        使用流式Function Calling执行ReAct逻辑
        
        Args:
            messages: 消息列表
            stream_callback: 流式回调函数
            shared_data: 共享数据
            
        Returns:
            执行结果
        """
        try:
            # 第一步：流式获取LLM的初始响应和工具调用决策

            # 使用流式调用获取响应
            response = await self.openai_client.chat_completion_async(
                messages=messages,
                tools=self.available_tools,
                tool_choice="auto",
                parallel_tool_calls=True,
                stream=True  # 启用流式响应
            )
            
            # 处理流式响应
            initial_response, tool_calls_detected, tool_calls_buffer = await self._process_stream_response(
                response, stream_callback
            )

          
            # 🔧 新增：验证工具调用格式
            if tool_calls_detected:
                self._validate_tool_calls(tool_calls_detected)
            
            # 第二步：如果检测到工具调用，进行流式工具执行
            tool_results = []
            if tool_calls_detected:
                # 并行执行工具调用，状态标记在执行器内部发送
                tool_results = await self._execute_tools_with_stream_feedback(
                    tool_calls_detected, stream_callback
                )
          
            
            # 第三步：如果有工具结果，获取最终响应
            final_user_message = await self._get_final_response(
                messages, initial_response, tool_calls_detected,
                tool_results, stream_callback
            )
            
            # 构建返回结果
            return {
                "user_message": final_user_message,  # 最终的AI回复（可能基于工具结果）
                "tool_calls": tool_results,
                "decision_success": True,
                "execution_mode": "stream_advanced",
                "initial_response": initial_response  # 重命名：AI的初始响应（可能包含工具调用决策）
            }
            
        except Exception as e:
            print(f"❌ 流式Function Calling执行失败: {e}")
            if stream_callback:
                await stream_callback(f"\n❌ 执行过程中遇到错误: {str(e)}\n")
            
            return {
                "error": f"Stream function calling failed: {str(e)}",
                "user_message": "抱歉，处理您的请求时遇到了问题，请稍后再试。",
                "decision_success": False,
                "execution_mode": "stream_error"
            }
    
    async def _process_stream_response(
        self,
        response,
        stream_callback: Optional[Callable]
    ) -> tuple[str, List[Any], Dict]:
        """
        处理流式响应

        Args:
            response: OpenAI流式响应
            stream_callback: 流式回调函数

        Returns:
            (收集的内容, 检测到的工具调用, 工具调用缓冲区)
        """
        initial_response = ""
        tool_calls_detected = []
        tool_calls_buffer = {}  # 用于累积流式工具调用

      
        if hasattr(response, '__aiter__'):
            # 处理流式响应
            async for chunk in response:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta

                    # 处理内容流
                    if hasattr(delta, 'content') and delta.content:
                        initial_response += delta.content
                        if stream_callback:
                            await stream_callback(delta.content)

                    # 检测工具调用（流式累积）
                    if hasattr(delta, 'tool_calls') and delta.tool_calls:
                        for tool_call_delta in delta.tool_calls:
                            if hasattr(tool_call_delta, 'index'):
                                index = tool_call_delta.index

                                # 初始化或更新工具调用缓冲区
                                if index not in tool_calls_buffer:
                                    tool_calls_buffer[index] = {
                                        'id': getattr(tool_call_delta, 'id', f'call_{index}'),
                                        'function': {
                                            'name': '',
                                            'arguments': ''
                                        }
                                    }

                                # 累积工具调用信息
                                if hasattr(tool_call_delta, 'function') and tool_call_delta.function:
                                    func_delta = tool_call_delta.function
                                    if hasattr(func_delta, 'name') and func_delta.name:
                                        tool_calls_buffer[index]['function']['name'] = func_delta.name
                                    if hasattr(func_delta, 'arguments') and func_delta.arguments:
                                        tool_calls_buffer[index]['function']['arguments'] += func_delta.arguments

            # 转换缓冲区为最终的工具调用列表
            for index, tool_call_data in tool_calls_buffer.items():
                # 创建模拟的工具调用对象
                class MockToolCall:
                    def __init__(self, data):
                        self.id = data['id']
                        self.function = MockFunction(data['function'])

                class MockFunction:
                    def __init__(self, func_data):
                        self.name = func_data['name']
                        self.arguments = func_data['arguments']

                if tool_call_data['function']['name']:  # 只添加有名称的工具调用
                    tool_calls_detected.append(MockToolCall(tool_call_data))
        else:
            # 非流式响应的回退处理
            choice = response.choices[0]
            message = choice.message
            if message.content:
                initial_response = message.content
                if stream_callback:
                    await stream_callback(initial_response)
            if hasattr(message, 'tool_calls') and message.tool_calls:
                tool_calls_detected = message.tool_calls

        return initial_response, tool_calls_detected, tool_calls_buffer

    def _validate_tool_calls(self, tool_calls: List[Any]) -> None:
        """
        验证工具调用格式的正确性

        Args:
            tool_calls: 工具调用列表
        """
        for i, tc in enumerate(tool_calls):
            if not hasattr(tc, 'id'):
                print(f"⚠️ [StreamHandler] 工具调用{i}缺少id属性")
            if not hasattr(tc, 'function'):
                print(f"⚠️ [StreamHandler] 工具调用{i}缺少function属性")
                continue
            if not hasattr(tc.function, 'name'):
                print(f"⚠️ [StreamHandler] 工具调用{i}的function缺少name属性")
            if not hasattr(tc.function, 'arguments'):
                print(f"⚠️ [StreamHandler] 工具调用{i}的function缺少arguments属性")
            else:
                # 验证arguments是否为有效JSON
                try:
                    import json
                    json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    print(f"⚠️ [StreamHandler] 工具调用{i}的arguments不是有效JSON: {tc.function.arguments}")

    async def _execute_tools_with_stream_feedback(
        self,
        tool_calls: List[Any],
        stream_callback: Optional[Callable]
    ) -> List[Dict[str, Any]]:
        """
        并行执行工具调用并提供流式反馈
        
        Args:
            tool_calls: 工具调用列表
            stream_callback: 流式回调函数
            
        Returns:
            工具执行结果列表
        """
        tool_results = []
        
        # 为每个工具调用创建执行任务
        tasks = []
        for i, tool_call in enumerate(tool_calls):
            if hasattr(tool_call, 'function'):
                function = tool_call.function
                tool_name = getattr(function, 'name', 'unknown')
                arguments_str = getattr(function, 'arguments', '{}')
                call_id = getattr(tool_call, 'id', f"call_{i}")

                try:
                    arguments = json.loads(arguments_str) if arguments_str else {}
                except json.JSONDecodeError:
                    arguments = {}

                # 发送工具开始状态
                if stream_callback and tool_name != 'unknown':
                    await stream_callback(f"__TOOL_START__{tool_name}")

                # 创建工具执行任务
                task = self._execute_single_tool_with_status(
                    call_id, tool_name, arguments, stream_callback
                )
                tasks.append(task)
        
        # 并行执行所有工具调用
        if tasks:
            tool_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            processed_results = []
            for result in tool_results:
                if isinstance(result, Exception):
                    processed_results.append({
                        "tool_name": "unknown",
                        "arguments": {},
                        "result": {"success": False, "error": str(result)},
                        "call_id": "error",
                        "success": False
                    })
                else:
                    processed_results.append(result)
            
            tool_results = processed_results
        
        return tool_results
    
    async def _get_final_response(
        self,
        messages: List[Dict],
        initial_response: str,
        tool_calls_detected: List[Any],
        tool_results: List[Dict[str, Any]],
        stream_callback: Optional[Callable]
    ) -> str:
        """
        获取最终响应
        
        Args:
            messages: 原始消息列表
            initial_response: AI的初始响应内容
            tool_calls_detected: 检测到的工具调用
            tool_results: 工具执行结果
            stream_callback: 流式回调函数

        Returns:
            最终用户消息
        """
        final_user_message = initial_response
        
        if tool_results:
            # 发送新回复段落开始标记
            if stream_callback:
                await stream_callback("__NEW_AI_REPLY__")

            # 🔧 修复：直接构建包含工具结果的消息
            messages_with_results = messages.copy()

            # 添加助手的工具调用消息
            assistant_message = {
                "role": "assistant",
                "content": initial_response
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
                    "role": "tool",
                    "tool_call_id": tool_result.get("call_id", "unknown"),
                    "content": json.dumps(tool_result.get("result", {}), ensure_ascii=False)
                })

            # 获取最终响应
            final_response = await self.openai_client.chat_completion_async(
                messages=messages_with_results,
                stream=True
            )

            # 流式输出最终响应
            final_content = ""
            if hasattr(final_response, '__aiter__'):
                async for chunk in final_response:
                    if hasattr(chunk, 'choices') and chunk.choices:
                        choice = chunk.choices[0]
                        delta = choice.delta
                        if hasattr(delta, 'content') and delta.content:
                            final_content += delta.content
                            if stream_callback:
                                await stream_callback(delta.content)
            else:
                choice = final_response.choices[0]
                final_content = choice.message.content or ""
                if stream_callback:
                    await stream_callback(final_content)

            final_user_message = final_content
        
        return final_user_message

    async def _execute_single_tool_with_status(
        self,
        call_id: str,
        tool_name: str,
        arguments: Dict[str, Any],
        stream_callback: Optional[Callable]
    ) -> Dict[str, Any]:
        """
        执行单个工具并发送状态更新

        Args:
            call_id: 调用ID
            tool_name: 工具名称
            arguments: 工具参数
            stream_callback: 流式回调函数

        Returns:
            工具执行结果
        """
        # 执行工具
        result = await self.tool_executor._execute_single_tool_with_stream_feedback(
            call_id, tool_name, arguments, stream_callback
        )

        # 发送工具完成状态
        if stream_callback:
            success = result.get("success", False)
            execution_time = result.get("execution_time", 0)
            await stream_callback(f"__TOOL_END__{tool_name}__{success}__{execution_time:.1f}")

        return result


