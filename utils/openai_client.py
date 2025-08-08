"""
OpenAI SDK封装层

提供统一的OpenAI SDK接口，保持与现有API的兼容性，支持同步和异步调用。
集成配置管理、错误处理、重试机制和Function Calling功能。
"""

import asyncio
import json
import time
import random
from typing import Dict, List, Any, Optional, AsyncIterator, Iterator, Union, Callable
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import ChoiceDelta

from config.openai_config import get_openai_config, OpenAIConfig


class OpenAIClientError(Exception):
    """OpenAI客户端错误基类"""
    pass


class OpenAIRateLimitError(OpenAIClientError):
    """API速率限制错误"""
    pass


class OpenAITimeoutError(OpenAIClientError):
    """API超时错误"""
    pass


class OpenAIRetryableError(OpenAIClientError):
    """可重试的API错误"""
    pass


class RetryManager:
    """重试管理器"""

    def __init__(self, max_retries: int = 3, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay

    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行函数并在失败时重试

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)

            except Exception as e:
                last_error = e

                # 检查是否应该重试
                if not self._should_retry(e, attempt):
                    break

                # 计算延迟时间
                delay = self._calculate_delay(attempt)

                print(f"⚠️ API调用失败 (尝试 {attempt + 1}/{self.max_retries + 1}): {e}")
                print(f"🔄 {delay:.1f}秒后重试...")

                await asyncio.sleep(delay)

        # 所有重试都失败了
        raise last_error

    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该重试

        Args:
            error: 错误对象
            attempt: 当前尝试次数

        Returns:
            是否应该重试
        """
        if attempt >= self.max_retries:
            return False

        error_str = str(error).lower()

        # 可重试的错误类型
        retryable_errors = [
            "rate_limit",
            "timeout",
            "connection",
            "network",
            "server_error",
            "503",
            "502",
            "500",
            "429"
        ]

        return any(err in error_str for err in retryable_errors)

    def _calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟时间（指数退避 + 随机抖动）

        Args:
            attempt: 当前尝试次数

        Returns:
            延迟时间（秒）
        """
        import random

        # 指数退避
        delay = self.base_delay * (2 ** attempt)

        # 添加随机抖动（±25%）
        jitter = delay * 0.25 * (random.random() * 2 - 1)

        return max(0.1, delay + jitter)


class OpenAIClient:
    """OpenAI SDK封装客户端"""

    def __init__(self, config: Optional[OpenAIConfig] = None):
        """
        初始化OpenAI客户端

        Args:
            config: OpenAI配置对象，如果为None则使用默认配置
        """
        self.config = config or get_openai_config()

        # 创建异步和同步客户端
        client_kwargs = self.config.to_openai_client_kwargs()
        self.async_client = AsyncOpenAI(**client_kwargs)
        self.sync_client = OpenAI(**client_kwargs)

        # 创建重试管理器
        self.retry_manager = RetryManager(
            max_retries=self.config.max_retries,
            base_delay=self.config.retry_delay
        )

        # 性能统计
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "retry_attempts": 0,
            "total_tokens": 0,
            "total_time": 0.0
        }

        # 全局系统提示词
        self.global_system_prompt = "如果是JSON输出，最终输出只包含JSON文本，不要使用代码块包裹"

    def _prepare_messages_with_global_system_prompt(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        为消息列表添加全局系统提示词

        Args:
            messages: 原始消息列表

        Returns:
            添加了全局系统提示词的消息列表
        """
        if not messages:
            return [{"role": "system", "content": self.global_system_prompt}]

        # 检查是否已有系统消息
        has_system_message = any(msg.get("role") == "system" for msg in messages)

        if has_system_message:
            # 如果已有系统消息，在第一个系统消息前添加全局系统提示词
            prepared_messages = []
            global_system_added = False

            for msg in messages:
                if msg.get("role") == "system" and not global_system_added:
                    # 在第一个系统消息前添加全局系统提示词
                    prepared_messages.append({"role": "system", "content": self.global_system_prompt})
                    global_system_added = True
                prepared_messages.append(msg)

            return prepared_messages
        else:
            # 如果没有系统消息，在开头添加全局系统提示词
            return [{"role": "system", "content": self.global_system_prompt}] + messages

    async def chat_completion_async(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        异步聊天完成调用
        
        Args:
            messages: 消息列表
            tools: Function Calling工具列表
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # 准备消息列表（添加全局系统提示词）
            prepared_messages = self._prepare_messages_with_global_system_prompt(messages)

            # 合并配置参数
            params = self.config.to_chat_completion_kwargs()
            params.update(kwargs)
            params["messages"] = prepared_messages

            # 添加工具支持
            if tools and self.config.function_calling_enabled:
                params["tools"] = tools
                if "tool_choice" not in params:
                    params["tool_choice"] = self.config.tool_choice

            # 记录请求日志
            if self.config.log_requests:
                self._log_request("chat_completion", params)

            # 使用重试机制执行API调用
            async def _api_call():
                return await self.async_client.chat.completions.create(**params)

            response = await self.retry_manager.execute_with_retry(_api_call)

            # 更新统计信息
            self.stats["successful_requests"] += 1
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens"] += response.usage.total_tokens

            # 记录响应日志
            if self.config.log_responses:
                self._log_response("chat_completion", response)

            return response

        except Exception as e:
            self.stats["failed_requests"] += 1
            raise self._handle_error(e)
        
        finally:
            self.stats["total_time"] += time.time() - start_time
    
    async def chat_completion_stream_async(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> AsyncIterator[ChatCompletionChunk]:
        """
        异步流式聊天完成调用
        
        Args:
            messages: 消息列表
            tools: Function Calling工具列表
            **kwargs: 其他参数
            
        Yields:
            聊天完成流式响应块
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # 准备消息列表（添加全局系统提示词）
            prepared_messages = self._prepare_messages_with_global_system_prompt(messages)

            # 合并配置参数
            params = self.config.to_chat_completion_kwargs()
            params.update(kwargs)
            params["messages"] = prepared_messages
            params["stream"] = True
            
            # 添加工具支持
            if tools and self.config.function_calling_enabled:
                params["tools"] = tools
                if "tool_choice" not in params:
                    params["tool_choice"] = self.config.tool_choice
            
            # 记录请求日志
            if self.config.log_requests:
                self._log_request("chat_completion_stream", params)
            
            # 执行流式API调用
            stream = await self.async_client.chat.completions.create(**params)
            
            async for chunk in stream:
                yield chunk
            
            self.stats["successful_requests"] += 1
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            raise self._handle_error(e)
        
        finally:
            self.stats["total_time"] += time.time() - start_time
    
    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> ChatCompletion:
        """
        同步聊天完成调用
        
        Args:
            messages: 消息列表
            tools: Function Calling工具列表
            **kwargs: 其他参数
            
        Returns:
            聊天完成响应
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # 准备消息列表（添加全局系统提示词）
            prepared_messages = self._prepare_messages_with_global_system_prompt(messages)

            # 合并配置参数
            params = self.config.to_chat_completion_kwargs()
            params.update(kwargs)
            params["messages"] = prepared_messages
            
            # 添加工具支持
            if tools and self.config.function_calling_enabled:
                params["tools"] = tools
                if "tool_choice" not in params:
                    params["tool_choice"] = self.config.tool_choice
            
            # 记录请求日志
            if self.config.log_requests:
                self._log_request("chat_completion", params)
            
            # 执行API调用
            response = self.sync_client.chat.completions.create(**params)
            
            # 更新统计信息
            self.stats["successful_requests"] += 1
            if hasattr(response, 'usage') and response.usage:
                self.stats["total_tokens"] += response.usage.total_tokens
            
            # 记录响应日志
            if self.config.log_responses:
                self._log_response("chat_completion", response)
            
            return response
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            raise self._handle_error(e)
        
        finally:
            self.stats["total_time"] += time.time() - start_time
    
    def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        **kwargs
    ) -> Iterator[ChatCompletionChunk]:
        """
        同步流式聊天完成调用
        
        Args:
            messages: 消息列表
            tools: Function Calling工具列表
            **kwargs: 其他参数
            
        Yields:
            聊天完成流式响应块
        """
        start_time = time.time()
        self.stats["total_requests"] += 1
        
        try:
            # 准备消息列表（添加全局系统提示词）
            prepared_messages = self._prepare_messages_with_global_system_prompt(messages)

            # 合并配置参数
            params = self.config.to_chat_completion_kwargs()
            params.update(kwargs)
            params["messages"] = prepared_messages
            params["stream"] = True
            
            # 添加工具支持
            if tools and self.config.function_calling_enabled:
                params["tools"] = tools
                if "tool_choice" not in params:
                    params["tool_choice"] = self.config.tool_choice
            
            # 记录请求日志
            if self.config.log_requests:
                self._log_request("chat_completion_stream", params)
            
            # 执行流式API调用
            stream = self.sync_client.chat.completions.create(**params)
            
            for chunk in stream:
                yield chunk
            
            self.stats["successful_requests"] += 1
            
        except Exception as e:
            self.stats["failed_requests"] += 1
            raise self._handle_error(e)
        
        finally:
            self.stats["total_time"] += time.time() - start_time
    
    def _handle_error(self, error: Exception) -> OpenAIClientError:
        """
        处理和转换错误

        Args:
            error: 原始错误

        Returns:
            转换后的错误
        """
        import openai

        # OpenAI SDK特定错误
        if isinstance(error, openai.RateLimitError):
            return OpenAIRateLimitError(f"API rate limit exceeded: {error}")

        if isinstance(error, openai.APITimeoutError):
            return OpenAITimeoutError(f"API request timeout: {error}")

        if isinstance(error, openai.APIConnectionError):
            return OpenAIRetryableError(f"API connection error: {error}")

        if isinstance(error, openai.InternalServerError):
            return OpenAIRetryableError(f"Internal server error: {error}")

        if isinstance(error, openai.BadRequestError):
            return OpenAIClientError(f"Bad request: {error}")

        if isinstance(error, openai.AuthenticationError):
            return OpenAIClientError(f"Authentication failed: {error}")

        if isinstance(error, openai.PermissionDeniedError):
            return OpenAIClientError(f"Permission denied: {error}")

        if isinstance(error, openai.NotFoundError):
            return OpenAIClientError(f"Resource not found: {error}")

        # 通用错误处理
        error_message = str(error)

        # 速率限制错误（字符串匹配）
        if "rate_limit" in error_message.lower() or "429" in error_message:
            return OpenAIRateLimitError(f"API rate limit exceeded: {error_message}")

        # 超时错误（字符串匹配）
        if "timeout" in error_message.lower() or "timed out" in error_message.lower():
            return OpenAITimeoutError(f"API request timeout: {error_message}")

        # 网络错误（字符串匹配）
        if any(keyword in error_message.lower() for keyword in ["connection", "network", "dns"]):
            return OpenAIRetryableError(f"Network error: {error_message}")

        # 服务器错误（字符串匹配）
        if any(code in error_message for code in ["500", "502", "503", "504"]):
            return OpenAIRetryableError(f"Server error: {error_message}")

        # 其他错误
        return OpenAIClientError(f"OpenAI API error: {error_message}")
    
    def _log_request(self, method: str, params: Dict[str, Any]) -> None:
        """记录请求日志"""
        if self.config.debug_enabled:
            # 隐藏敏感信息
            safe_params = params.copy()
            if "messages" in safe_params:
                safe_params["messages"] = f"[{len(safe_params['messages'])} messages]"
            
            print(f"🔄 OpenAI {method} request: {safe_params}")
    
    def _log_response(self, method: str, response: Any) -> None:
        """记录响应日志"""
        if self.config.debug_enabled:
            if hasattr(response, 'usage') and response.usage:
                print(f"✅ OpenAI {method} response: {response.usage.total_tokens} tokens")
            else:
                print(f"✅ OpenAI {method} response received")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        return self.stats.copy()
    
    def reset_stats(self) -> None:
        """重置性能统计信息"""
        self.stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "total_tokens": 0,
            "total_time": 0.0
        }


# 全局客户端实例
_global_client: Optional[OpenAIClient] = None


def get_openai_client(config: Optional[OpenAIConfig] = None) -> OpenAIClient:
    """
    获取全局OpenAI客户端实例

    Args:
        config: OpenAI配置对象

    Returns:
        OpenAI客户端实例
    """
    global _global_client

    if _global_client is None or config is not None:
        _global_client = OpenAIClient(config)

    return _global_client





# ============================================================================
# Function Calling工具调用支持
# ============================================================================

class FunctionCallResult:
    """Function Calling调用结果"""

    def __init__(
        self,
        function_name: str,
        arguments: Dict[str, Any],
        result: Any,
        success: bool = True,
        error: Optional[str] = None
    ):
        self.function_name = function_name
        self.arguments = arguments
        self.result = result
        self.success = success
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "function_name": self.function_name,
            "arguments": self.arguments,
            "result": self.result,
            "success": self.success,
            "error": self.error
        }


async def execute_function_calls(
    messages: List[Dict[str, str]],
    tools: List[Dict],
    tool_executor: Callable[[str, Dict[str, Any]], Any],
    max_iterations: int = 5
) -> List[FunctionCallResult]:
    """
    执行Function Calling调用

    Args:
        messages: 消息历史
        tools: 可用工具列表
        tool_executor: 工具执行器函数
        max_iterations: 最大迭代次数

    Returns:
        工具调用结果列表
    """
    client = get_openai_client()
    results = []
    current_messages = messages.copy()

    for _ in range(max_iterations):
        # 调用LLM
        response = await client.chat_completion_async(
            current_messages,
            tools=tools,
            tool_choice="auto"
        )

        # 检查是否有工具调用
        if not response.choices[0].message.tool_calls:
            break

        # 添加助手消息
        current_messages.append({
            "role": "assistant",
            "content": response.choices[0].message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in response.choices[0].message.tool_calls
            ]
        })

        # 执行工具调用
        for tool_call in response.choices[0].message.tool_calls:
            try:
                # 解析参数
                arguments = json.loads(tool_call.function.arguments)

                # 执行工具
                result = await tool_executor(tool_call.function.name, arguments)

                # 记录结果
                function_result = FunctionCallResult(
                    function_name=tool_call.function.name,
                    arguments=arguments,
                    result=result,
                    success=True
                )
                results.append(function_result)

                # 添加工具结果消息
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                })

            except Exception as e:
                # 记录错误
                function_result = FunctionCallResult(
                    function_name=tool_call.function.name,
                    arguments=json.loads(tool_call.function.arguments) if tool_call.function.arguments else {},
                    result=None,
                    success=False,
                    error=str(e)
                )
                results.append(function_result)

                # 添加错误消息
                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": f"Error: {str(e)}"
                })

    return results
