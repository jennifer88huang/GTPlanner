"""
OpenAI错误处理和重试机制测试

测试OpenAI客户端的错误处理、重试机制和容错能力。
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, Mock, patch
from utils.openai_client import (
    OpenAIClient, 
    OpenAIClientError, 
    OpenAIRateLimitError, 
    OpenAITimeoutError,
    OpenAIRetryableError,
    RetryManager
)
from config.openai_config import OpenAIConfig


class TestRetryManager:
    """重试管理器测试"""
    
    @pytest.mark.asyncio
    async def test_successful_execution(self):
        """测试成功执行（无需重试）"""
        retry_manager = RetryManager(max_retries=3)
        
        async def success_func():
            return "success"
        
        result = await retry_manager.execute_with_retry(success_func)
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_retry_on_retryable_error(self):
        """测试可重试错误的重试机制"""
        retry_manager = RetryManager(max_retries=2, base_delay=0.1)
        
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("rate_limit exceeded")
            return "success"
        
        result = await retry_manager.execute_with_retry(failing_func)
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        retry_manager = RetryManager(max_retries=2, base_delay=0.1)
        
        async def always_failing_func():
            raise Exception("rate_limit exceeded")
        
        with pytest.raises(Exception, match="rate_limit exceeded"):
            await retry_manager.execute_with_retry(always_failing_func)
    
    def test_should_retry_logic(self):
        """测试重试判断逻辑"""
        retry_manager = RetryManager(max_retries=3)
        
        # 可重试的错误
        retryable_errors = [
            Exception("rate_limit exceeded"),
            Exception("timeout occurred"),
            Exception("connection failed"),
            Exception("server error 503"),
            Exception("429 too many requests")
        ]
        
        for error in retryable_errors:
            assert retry_manager._should_retry(error, 0) == True
        
        # 不可重试的错误
        non_retryable_errors = [
            Exception("authentication failed"),
            Exception("bad request"),
            Exception("permission denied")
        ]
        
        for error in non_retryable_errors:
            assert retry_manager._should_retry(error, 0) == False
        
        # 超过最大重试次数
        assert retry_manager._should_retry(Exception("rate_limit"), 3) == False
    
    def test_calculate_delay(self):
        """测试延迟计算"""
        retry_manager = RetryManager(base_delay=1.0)
        
        # 测试指数退避
        delay_0 = retry_manager._calculate_delay(0)
        delay_1 = retry_manager._calculate_delay(1)
        delay_2 = retry_manager._calculate_delay(2)
        
        # 基本的指数增长（考虑随机抖动）
        assert 0.5 <= delay_0 <= 1.5  # 1.0 ± 25%
        assert 1.5 <= delay_1 <= 2.5  # 2.0 ± 25%
        assert 3.0 <= delay_2 <= 5.0  # 4.0 ± 25%


class TestOpenAIClientErrorHandling:
    """OpenAI客户端错误处理测试"""
    
    def setup_method(self):
        """测试设置"""
        self.config = OpenAIConfig(
            api_key="test-key",
            max_retries=2,
            retry_delay=0.1
        )
        self.client = OpenAIClient(self.config)
    
    def test_handle_openai_rate_limit_error(self):
        """测试OpenAI速率限制错误处理"""
        import openai
        
        original_error = openai.RateLimitError(
            message="Rate limit exceeded",
            response=Mock(),
            body={}
        )
        
        handled_error = self.client._handle_error(original_error)
        assert isinstance(handled_error, OpenAIRateLimitError)
        assert "rate limit exceeded" in str(handled_error).lower()
    
    def test_handle_openai_timeout_error(self):
        """测试OpenAI超时错误处理"""
        import openai
        
        original_error = openai.APITimeoutError(request=Mock())
        
        handled_error = self.client._handle_error(original_error)
        assert isinstance(handled_error, OpenAITimeoutError)
        assert "timeout" in str(handled_error).lower()
    
    def test_handle_openai_connection_error(self):
        """测试OpenAI连接错误处理"""
        import openai
        
        original_error = openai.APIConnectionError(request=Mock())
        
        handled_error = self.client._handle_error(original_error)
        assert isinstance(handled_error, OpenAIRetryableError)
        assert "connection error" in str(handled_error).lower()
    
    def test_handle_openai_server_error(self):
        """测试OpenAI服务器错误处理"""
        import openai
        
        original_error = openai.InternalServerError(
            message="Internal server error",
            response=Mock(),
            body={}
        )
        
        handled_error = self.client._handle_error(original_error)
        assert isinstance(handled_error, OpenAIRetryableError)
        assert "server error" in str(handled_error).lower()
    
    def test_handle_openai_auth_error(self):
        """测试OpenAI认证错误处理"""
        import openai
        
        original_error = openai.AuthenticationError(
            message="Invalid API key",
            response=Mock(),
            body={}
        )
        
        handled_error = self.client._handle_error(original_error)
        assert isinstance(handled_error, OpenAIClientError)
        assert "authentication failed" in str(handled_error).lower()
    
    def test_handle_generic_errors(self):
        """测试通用错误处理"""
        # 速率限制（字符串匹配）
        error = Exception("429 rate limit exceeded")
        handled = self.client._handle_error(error)
        assert isinstance(handled, OpenAIRateLimitError)
        
        # 超时（字符串匹配）
        error = Exception("request timed out")
        handled = self.client._handle_error(error)
        assert isinstance(handled, OpenAITimeoutError)
        
        # 网络错误（字符串匹配）
        error = Exception("connection refused")
        handled = self.client._handle_error(error)
        assert isinstance(handled, OpenAIRetryableError)
        
        # 服务器错误（字符串匹配）
        error = Exception("500 internal server error")
        handled = self.client._handle_error(error)
        assert isinstance(handled, OpenAIRetryableError)
        
        # 其他错误
        error = Exception("unknown error")
        handled = self.client._handle_error(error)
        assert isinstance(handled, OpenAIClientError)
    
    @pytest.mark.asyncio
    async def test_chat_completion_with_retry(self):
        """测试聊天完成的重试机制"""
        with patch.object(self.client.async_client.chat.completions, 'create') as mock_create:
            # 模拟前两次失败，第三次成功
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "test response"
            mock_response.usage = Mock()
            mock_response.usage.total_tokens = 100
            
            mock_create.side_effect = [
                Exception("rate_limit exceeded"),
                Exception("timeout occurred"),
                mock_response
            ]
            
            messages = [{"role": "user", "content": "test"}]
            response = await self.client.chat_completion_async(messages)
            
            assert mock_create.call_count == 3
            assert response.choices[0].message.content == "test response"
    
    @pytest.mark.asyncio
    async def test_chat_completion_max_retries_exceeded(self):
        """测试聊天完成超过最大重试次数"""
        with patch.object(self.client.async_client.chat.completions, 'create') as mock_create:
            mock_create.side_effect = Exception("rate_limit exceeded")
            
            messages = [{"role": "user", "content": "test"}]
            
            with pytest.raises(OpenAIRateLimitError):
                await self.client.chat_completion_async(messages)
            
            # 应该尝试 max_retries + 1 次
            assert mock_create.call_count == self.config.max_retries + 1
    
    def test_stats_tracking(self):
        """测试统计信息跟踪"""
        initial_stats = self.client.get_stats()
        
        assert initial_stats["total_requests"] == 0
        assert initial_stats["successful_requests"] == 0
        assert initial_stats["failed_requests"] == 0
        assert initial_stats["retry_attempts"] == 0
        assert initial_stats["total_tokens"] == 0
        assert initial_stats["total_time"] == 0.0
        
        # 重置统计
        self.client.reset_stats()
        reset_stats = self.client.get_stats()
        assert reset_stats == initial_stats


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
