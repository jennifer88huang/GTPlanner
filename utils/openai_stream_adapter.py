"""
OpenAI流式输出适配器

提供OpenAI SDK流式输出与现有JSONStreamParser的兼容性层，
支持Function Calling的流式处理和实时显示。
"""

import json
import asyncio
from typing import AsyncIterator, Dict, List, Any, Optional, Callable, Union
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from utils.openai_client import get_openai_client
from utils.json_stream_parser import JSONStreamParser


class OpenAIStreamAdapter:
    """OpenAI流式输出适配器"""
    
    def __init__(self):
        self.client = get_openai_client()
        self.current_content = ""
        self.current_tool_calls = {}
        self.message_complete = False
    
    async def stream_chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        json_mode: bool = False,
        field_callback: Optional[Callable] = None,
        tool_call_callback: Optional[Callable] = None,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        流式聊天完成，支持JSON解析和Function Calling
        
        Args:
            messages: 消息列表
            tools: Function Calling工具列表
            json_mode: 是否启用JSON模式
            field_callback: JSON字段更新回调
            tool_call_callback: 工具调用回调
            **kwargs: 其他参数
            
        Yields:
            流式内容块
        """
        # 重置状态
        self.current_content = ""
        self.current_tool_calls = {}
        self.message_complete = False
        
        # 设置JSON模式
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}
        
        # 创建JSON解析器（如果需要）
        json_parser = None
        if json_mode and field_callback:
            json_parser = JSONStreamParser()
            json_parser.subscribe_field("user_message", field_callback)
        
        try:
            # 执行流式调用
            async for chunk in self.client.chat_completion_stream_async(
                messages, tools=tools, **kwargs
            ):
                # 处理内容流
                content_chunk = await self._process_content_chunk(
                    chunk, json_parser, tool_call_callback
                )
                
                if content_chunk:
                    yield content_chunk
            
            # 处理完成后的工具调用
            if self.current_tool_calls and tool_call_callback:
                await self._finalize_tool_calls(tool_call_callback)
                
        except Exception as e:
            print(f"⚠️ 流式处理错误: {e}")
            raise
    
    async def _process_content_chunk(
        self,
        chunk: ChatCompletionChunk,
        json_parser: Optional[JSONStreamParser] = None,
        tool_call_callback: Optional[Callable] = None
    ) -> Optional[str]:
        """
        处理单个内容块
        
        Args:
            chunk: OpenAI响应块
            json_parser: JSON解析器
            tool_call_callback: 工具调用回调
            
        Returns:
            处理后的内容块
        """
        if not chunk.choices:
            return None
        
        choice = chunk.choices[0]
        delta = choice.delta
        
        # 处理内容
        if delta.content:
            self.current_content += delta.content
            
            # JSON解析
            if json_parser:
                json_parser.add_chunk(delta.content)
            
            return delta.content
        
        # 处理工具调用
        if delta.tool_calls:
            await self._process_tool_calls(delta.tool_calls, tool_call_callback)
        
        # 检查是否完成
        if choice.finish_reason:
            self.message_complete = True
            
            # 最终JSON解析
            if json_parser:
                json_parser.finalize()
        
        return None
    
    async def _process_tool_calls(
        self,
        tool_calls: List[Any],
        tool_call_callback: Optional[Callable] = None
    ) -> None:
        """
        处理工具调用流
        
        Args:
            tool_calls: 工具调用列表
            tool_call_callback: 工具调用回调
        """
        for tool_call in tool_calls:
            call_id = tool_call.id
            
            # 初始化工具调用记录
            if call_id not in self.current_tool_calls:
                self.current_tool_calls[call_id] = {
                    "id": call_id,
                    "type": tool_call.type,
                    "function": {
                        "name": "",
                        "arguments": ""
                    },
                    "complete": False
                }
            
            # 更新工具调用信息
            current_call = self.current_tool_calls[call_id]
            
            if tool_call.function:
                if tool_call.function.name:
                    current_call["function"]["name"] = tool_call.function.name
                
                if tool_call.function.arguments:
                    current_call["function"]["arguments"] += tool_call.function.arguments
            
            # 实时回调（如果有）
            if tool_call_callback:
                await self._call_tool_callback(
                    tool_call_callback,
                    current_call,
                    is_complete=False
                )
    
    async def _finalize_tool_calls(
        self,
        tool_call_callback: Callable
    ) -> None:
        """
        完成工具调用处理
        
        Args:
            tool_call_callback: 工具调用回调
        """
        for call_id, call_data in self.current_tool_calls.items():
            call_data["complete"] = True
            
            await self._call_tool_callback(
                tool_call_callback,
                call_data,
                is_complete=True
            )
    
    async def _call_tool_callback(
        self,
        callback: Callable,
        call_data: Dict[str, Any],
        is_complete: bool
    ) -> None:
        """
        调用工具回调函数
        
        Args:
            callback: 回调函数
            call_data: 工具调用数据
            is_complete: 是否完成
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(call_data, is_complete)
            else:
                callback(call_data, is_complete)
        except Exception as e:
            print(f"⚠️ 工具回调错误: {e}")


class LegacyStreamAdapter:
    """传统流式输出适配器（兼容现有call_llm接口）"""
    
    def __init__(self):
        self.adapter = OpenAIStreamAdapter()
    
    async def call_llm_stream_async_compatible(
        self,
        prompt: str,
        is_json: bool = False,
        **kwargs
    ) -> AsyncIterator[str]:
        """
        兼容现有call_llm_stream_async接口
        
        Args:
            prompt: 提示词
            is_json: 是否JSON模式
            **kwargs: 其他参数
            
        Yields:
            流式内容
        """
        messages = [{"role": "user", "content": prompt}]
        
        # JSON模式处理
        if is_json:
            messages[0]["content"] += "\n\n请以JSON格式回复，确保输出是有效的JSON。"
        
        async for chunk in self.adapter.stream_chat_completion(
            messages,
            json_mode=is_json,
            **kwargs
        ):
            yield chunk


# ============================================================================
# 高级流式处理功能
# ============================================================================

class FunctionCallingStreamProcessor:
    """Function Calling流式处理器"""
    
    def __init__(self):
        self.adapter = OpenAIStreamAdapter()
        self.active_tools = {}
        self.conversation_history = []
    
    async def process_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict],
        tool_executor: Callable,
        max_iterations: int = 5,
        stream_callback: Optional[Callable] = None,
        tool_callback: Optional[Callable] = None
    ) -> List[Dict[str, Any]]:
        """
        处理带工具调用的流式对话
        
        Args:
            messages: 消息历史
            tools: 可用工具列表
            tool_executor: 工具执行器
            max_iterations: 最大迭代次数
            stream_callback: 流式内容回调
            tool_callback: 工具调用回调
            
        Returns:
            完整的对话历史
        """
        current_messages = messages.copy()
        results = []
        
        for iteration in range(max_iterations):
            print(f"🔄 对话迭代 {iteration + 1}/{max_iterations}")
            
            # 收集流式内容
            content_buffer = ""
            tool_calls_buffer = []
            
            # 定义内部回调
            async def content_callback(content: str):
                nonlocal content_buffer
                content_buffer += content
                if stream_callback:
                    await self._safe_callback(stream_callback, content)
            
            async def internal_tool_callback(call_data: Dict, is_complete: bool):
                if is_complete:
                    tool_calls_buffer.append(call_data)
                if tool_callback:
                    await self._safe_callback(tool_callback, call_data, is_complete)
            
            # 执行流式调用
            async for chunk in self.adapter.stream_chat_completion(
                current_messages,
                tools=tools,
                tool_call_callback=internal_tool_callback
            ):
                await content_callback(chunk)
            
            # 添加助手消息
            assistant_message = {
                "role": "assistant",
                "content": content_buffer or None
            }
            
            if tool_calls_buffer:
                assistant_message["tool_calls"] = tool_calls_buffer
            
            current_messages.append(assistant_message)
            
            # 如果没有工具调用，结束对话
            if not tool_calls_buffer:
                break
            
            # 执行工具调用
            for tool_call in tool_calls_buffer:
                try:
                    # 解析参数
                    arguments = json.loads(tool_call["function"]["arguments"])
                    
                    # 执行工具
                    print(f"🔧 执行工具: {tool_call['function']['name']}")
                    result = await tool_executor(
                        tool_call["function"]["name"],
                        arguments
                    )
                    
                    # 添加工具结果消息
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": json.dumps(result, ensure_ascii=False)
                    })
                    
                    results.append({
                        "tool_name": tool_call["function"]["name"],
                        "arguments": arguments,
                        "result": result,
                        "success": True
                    })
                    
                except Exception as e:
                    print(f"❌ 工具执行失败: {e}")
                    
                    # 添加错误消息
                    current_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": f"Error: {str(e)}"
                    })
                    
                    results.append({
                        "tool_name": tool_call["function"]["name"],
                        "arguments": json.loads(tool_call["function"]["arguments"]) if tool_call["function"]["arguments"] else {},
                        "result": None,
                        "success": False,
                        "error": str(e)
                    })
        
        return current_messages
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """安全调用回调函数"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            print(f"⚠️ 回调函数错误: {e}")


# ============================================================================
# 全局实例和便捷函数
# ============================================================================

_stream_adapter: Optional[OpenAIStreamAdapter] = None
_legacy_adapter: Optional[LegacyStreamAdapter] = None
_function_processor: Optional[FunctionCallingStreamProcessor] = None


def get_stream_adapter() -> OpenAIStreamAdapter:
    """获取流式适配器实例"""
    global _stream_adapter
    if _stream_adapter is None:
        _stream_adapter = OpenAIStreamAdapter()
    return _stream_adapter


def get_legacy_adapter() -> LegacyStreamAdapter:
    """获取传统适配器实例"""
    global _legacy_adapter
    if _legacy_adapter is None:
        _legacy_adapter = LegacyStreamAdapter()
    return _legacy_adapter


def get_function_processor() -> FunctionCallingStreamProcessor:
    """获取Function Calling处理器实例"""
    global _function_processor
    if _function_processor is None:
        _function_processor = FunctionCallingStreamProcessor()
    return _function_processor
