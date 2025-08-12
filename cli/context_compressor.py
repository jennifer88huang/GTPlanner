"""
CLI层上下文压缩器

从统一消息管理层移植的异步压缩功能，用于CLI层在发送给统一消息管理层前压缩上下文
"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Message:
    """消息数据结构"""
    id: str
    role: str
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None


class CLIContextCompressor:
    """CLI层上下文压缩器"""
    
    def __init__(self):
        """初始化压缩器"""
        # 智能压缩配置
        self.compression_enabled = True
        self.compression_config = {
            "auto_compress": True,
            "compression_threshold": 50,     # 消息数量阈值
            "preserve_recent": 10,           # 保留最近消息数
            "token_threshold": 6000,         # Token数量阈值
            "compression_ratio_target": 0.7, # 目标压缩比
        }
        self._compression_lock = threading.Lock()
        self._compression_pending = False
        self._last_compression_warning = 0
        
        # 压缩线程池
        self._compression_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="cli_compression")
        self._compression_running = False
    
    def should_compress(self, messages: List[Message]) -> tuple[bool, str]:
        """
        判断是否需要压缩
        
        Args:
            messages: 消息列表
            
        Returns:
            (是否需要压缩, 压缩级别)
        """
        message_count = len(messages)
        estimated_tokens = self._estimate_tokens(messages)
        
        # 检查是否需要压缩
        should_compress = (
            message_count >= self.compression_config["compression_threshold"] or
            estimated_tokens >= self.compression_config["token_threshold"]
        )
        
        if not should_compress:
            return False, "none"
        
        # 判断压缩级别
        msg_threshold = self.compression_config["compression_threshold"]
        token_threshold = self.compression_config["token_threshold"]
        
        msg_ratio = message_count / msg_threshold if msg_threshold > 0 else 0
        token_ratio = estimated_tokens / token_threshold if token_threshold > 0 else 0
        max_ratio = max(msg_ratio, token_ratio)
        
        if max_ratio >= 2.0:
            return True, "heavy"
        elif max_ratio >= 1.5:
            return True, "medium"
        else:
            return True, "light"
    
    async def compress_messages_async(self, messages: List[Message]) -> List[Message]:
        """
        异步压缩消息列表
        
        Args:
            messages: 原始消息列表
            
        Returns:
            压缩后的消息列表
        """
        should_compress, level = self.should_compress(messages)
        
        if not should_compress:
            return messages
        
        # 保留最近的消息
        preserve_count = self.compression_config["preserve_recent"]
        if len(messages) <= preserve_count:
            return messages
        
        messages_to_compress = messages[:-preserve_count]
        recent_messages = messages[-preserve_count:]
        
        try:
            # 执行压缩
            compressed_messages = await self._execute_compression_async(messages_to_compress, level)
            
            # 返回压缩后的消息 + 最近消息
            return compressed_messages + recent_messages
            
        except Exception as e:
            print(f"⚠️ 压缩失败，返回原始消息: {e}")
            return messages
    
    async def _execute_compression_async(self, messages: List[Message], level: str) -> List[Message]:
        """
        执行实际的压缩任务
        
        Args:
            messages: 要压缩的消息
            level: 压缩级别
            
        Returns:
            压缩后的消息列表
        """
        try:
            # 延迟导入避免循环依赖
            from core.context_compressor import get_compressor, CompressionLevel, CompressionTask
            
            compressor = get_compressor()
            
            # 确保压缩服务已启动
            if not compressor.is_running:
                await compressor.start_compression_service()
            
            # 转换压缩级别
            level_map = {
                "light": CompressionLevel.LIGHT,
                "medium": CompressionLevel.MEDIUM,
                "heavy": CompressionLevel.HEAVY,
            }
            compression_level = level_map.get(level, CompressionLevel.MEDIUM)
            
            # 转换消息格式
            from core.unified_context import Message as UnifiedMessage, MessageRole
            unified_messages = []
            for msg in messages:
                unified_msg = UnifiedMessage(
                    id=msg.id,
                    role=MessageRole(msg.role),
                    content=msg.content,
                    timestamp=msg.timestamp,
                    metadata=msg.metadata,
                    tool_calls=msg.tool_calls
                )
                unified_messages.append(unified_msg)
            
            # 创建压缩任务
            task = CompressionTask(
                session_id="cli_compression",
                messages=unified_messages,
                level=compression_level
            )
            
            # 执行压缩
            compression_result = await compressor._execute_compression(task)
            
            if compression_result.success:
                # 转换回CLI消息格式
                compressed_cli_messages = []
                for unified_msg in compression_result.compressed_messages:
                    cli_msg = Message(
                        id=unified_msg.id,
                        role=unified_msg.role.value,
                        content=unified_msg.content,
                        timestamp=unified_msg.timestamp,
                        metadata=unified_msg.metadata,
                        tool_calls=unified_msg.tool_calls
                    )
                    compressed_cli_messages.append(cli_msg)
                
                print(f"🗜️ CLI压缩完成: {len(messages)} → {len(compressed_cli_messages)} 条消息")
                return compressed_cli_messages
            else:
                print(f"⚠️ 压缩失败: {compression_result.error}")
                return messages
                
        except Exception as e:
            print(f"⚠️ 压缩异常: {e}")
            return messages
    
    def _estimate_tokens(self, messages: List[Message]) -> int:
        """估算消息的token数量"""
        total_tokens = 0
        for msg in messages:
            content = msg.content or ""
            chinese_chars = len([c for c in content if '\u4e00' <= c <= '\u9fff'])
            english_words = len(content.replace('，', ' ').replace('。', ' ').split())
            
            content_tokens = chinese_chars + english_words * 1.3
            
            metadata_tokens = 0
            if msg.metadata:
                metadata_str = str(msg.metadata)
                metadata_tokens = len(metadata_str) * 0.3
            
            if msg.tool_calls:
                tool_calls_str = str(msg.tool_calls)
                metadata_tokens += len(tool_calls_str) * 0.3
            
            total_tokens += content_tokens + metadata_tokens
        
        return int(total_tokens)
    
    def configure_compression(self, **kwargs) -> None:
        """配置压缩参数"""
        for key, value in kwargs.items():
            if key in self.compression_config:
                self.compression_config[key] = value
                print(f"🔧 CLI压缩配置更新: {key} = {value}")
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, '_compression_executor'):
            self._compression_executor.shutdown(wait=False)


# 全局实例
_cli_compressor = None


def get_cli_compressor() -> CLIContextCompressor:
    """获取CLI压缩器实例"""
    global _cli_compressor
    if _cli_compressor is None:
        _cli_compressor = CLIContextCompressor()
    return _cli_compressor


def cleanup_cli_compressor():
    """清理CLI压缩器"""
    global _cli_compressor
    if _cli_compressor:
        _cli_compressor.cleanup()
        _cli_compressor = None
