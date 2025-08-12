"""
智能上下文压缩器 - 基于LLM的异步上下文压缩

使用LLM智能压缩对话历史，保留关键信息和上下文关联性，
避免硬编码压缩导致的信息丢失。

特性：
1. 异步压缩，不阻塞主流程
2. 智能保留关键信息和决策链
3. 维护上下文连贯性
4. 支持增量压缩
5. 可配置压缩策略
"""

import asyncio
import json
import time
import atexit
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from utils.openai_client import OpenAIClient
from core.unified_context import Message, MessageRole


class CompressionLevel(Enum):
    """压缩级别"""
    LIGHT = "light"      # 轻度压缩，保留90%信息
    MEDIUM = "medium"    # 中度压缩，保留70%信息  
    HEAVY = "heavy"      # 重度压缩，保留50%信息
    SUMMARY = "summary"  # 摘要模式，保留30%信息


@dataclass
class CompressionTask:
    """压缩任务"""
    session_id: str
    messages: List[Message]
    level: CompressionLevel
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class CompressionResult:
    """压缩结果"""
    session_id: str
    original_count: int
    compressed_count: int
    compression_ratio: float
    compressed_messages: List[Message]
    summary: str
    key_decisions: List[str]
    execution_time: float
    success: bool
    error: Optional[str] = None


class ContextCompressor:
    """智能上下文压缩器"""
    
    def __init__(self, openai_client: Optional[OpenAIClient] = None):
        """初始化压缩器"""
        self.openai_client = openai_client or OpenAIClient()
        self.compression_queue = asyncio.Queue()
        self.is_running = False
        self.compression_task = None
        
        # 压缩配置
        self.config = {
            "max_context_length": 8000,      # 最大上下文长度（token估算）
            "compression_threshold": 1000,    # 触发压缩的token阈值（进一步降低用于测试）
            "min_messages_to_compress": 10,   # 最少压缩消息数
            "preserve_recent_count": 5,       # 保留最近消息数
            "quality_threshold": 0.8,         # 压缩质量阈值
        }
        
        # 压缩提示模板
        self.compression_prompts = {
            CompressionLevel.LIGHT: self._get_light_compression_prompt(),
            CompressionLevel.MEDIUM: self._get_medium_compression_prompt(),
            CompressionLevel.HEAVY: self._get_heavy_compression_prompt(),
            CompressionLevel.SUMMARY: self._get_summary_compression_prompt(),
        }
    
    def _get_light_compression_prompt(self) -> str:
        """轻度压缩提示"""
        return """
你是一个专业的对话历史压缩助手。请对以下对话历史进行轻度压缩，要求：

1. 保留90%的关键信息
2. 合并相似的对话轮次
3. 保留所有重要决策和结论
4. 维护逻辑关系和上下文连贯性
5. 保留工具调用的关键结果

请以JSON格式返回压缩结果：
{
    "compressed_messages": [
        {
            "role": "user|assistant|system",
            "content": "压缩后的内容",
            "metadata": {"compression_note": "轻度压缩", "compression_level": "light"}
        }
    ],
    "summary": "整体对话摘要",
    "key_decisions": ["关键决策1", "关键决策2"],
    "compression_ratio": 0.9
}

对话历史：
"""

    def _get_medium_compression_prompt(self) -> str:
        """中度压缩提示"""
        return """
你是一个专业的对话历史压缩助手。请对以下对话历史进行中度压缩，要求：

1. 保留70%的关键信息
2. 合并重复和冗余内容
3. 保留核心决策链和重要结论
4. 简化详细描述，保留要点
5. 保留关键工具调用结果

请以JSON格式返回压缩结果：
{
    "compressed_messages": [
        {
            "role": "user|assistant|system",
            "content": "压缩后的内容",
            "metadata": {"compression_note": "中度压缩", "compression_level": "medium"}
        }
    ],
    "summary": "整体对话摘要",
    "key_decisions": ["关键决策1", "关键决策2"],
    "compression_ratio": 0.7
}

对话历史：
"""

    def _get_heavy_compression_prompt(self) -> str:
        """重度压缩提示"""
        return """
你是一个专业的对话历史压缩助手。请对以下对话历史进行重度压缩，要求：

1. 保留50%的核心信息
2. 大幅合并相关内容
3. 只保留最重要的决策和结论
4. 去除细节，保留核心逻辑
5. 合并工具调用结果为摘要

请以JSON格式返回压缩结果：
{
    "compressed_messages": [
        {
            "role": "user|assistant|system",
            "content": "高度压缩的内容",
            "metadata": {"compression_note": "重度压缩", "compression_level": "heavy"}
        }
    ],
    "summary": "核心对话摘要",
    "key_decisions": ["核心决策1", "核心决策2"],
    "compression_ratio": 0.5
}

对话历史：
"""

    def _get_summary_compression_prompt(self) -> str:
        """摘要压缩提示"""
        return """
你是一个专业的对话历史压缩助手。请将以下对话历史压缩为摘要模式，要求：

1. 保留30%的精华信息
2. 生成高度概括的摘要
3. 只保留最关键的决策点
4. 极简化表达，突出核心
5. 工具调用结果合并为关键结论

请以JSON格式返回压缩结果：
{
    "compressed_messages": [
        {
            "role": "system",
            "content": "对话历史摘要：[摘要内容]",
            "metadata": {"compression_note": "摘要压缩", "compression_level": "summary"}
        }
    ],
    "summary": "极简对话摘要",
    "key_decisions": ["最关键决策"],
    "compression_ratio": 0.3
}

对话历史：
"""

    async def start_compression_service(self):
        """启动压缩服务"""
        if self.is_running:
            return
            
        self.is_running = True
        self.compression_task = asyncio.create_task(self._compression_worker())
        print("🗜️ 智能上下文压缩服务已启动")

    async def stop_compression_service(self):
        """停止压缩服务"""
        if not self.is_running:
            return

        self.is_running = False

        # 取消压缩任务
        if self.compression_task:
            self.compression_task.cancel()
            try:
                await self.compression_task
            except asyncio.CancelledError:
                pass
            self.compression_task = None

        # 清空队列中的待处理任务
        while not self.compression_queue.empty():
            try:
                self.compression_queue.get_nowait()
                self.compression_queue.task_done()
            except asyncio.QueueEmpty:
                break

        print("🗜️ 智能上下文压缩服务已停止")

    async def _compression_worker(self):
        """压缩工作线程"""
        while self.is_running:
            try:
                # 等待压缩任务
                task = await asyncio.wait_for(
                    self.compression_queue.get(), 
                    timeout=1.0
                )
                
                # 执行压缩
                result = await self._execute_compression(task)
                
                # 标记任务完成
                self.compression_queue.task_done()
                
                if result.success:
                    print(f"✅ 会话 {task.session_id} 压缩完成，"
                          f"压缩比: {result.compression_ratio:.1%}, "
                          f"耗时: {result.execution_time:.1f}s")
                else:
                    print(f"❌ 会话 {task.session_id} 压缩失败: {result.error}")
                    
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"⚠️ 压缩工作线程异常: {e}")

    async def _execute_compression(self, task: CompressionTask) -> CompressionResult:
        """执行压缩任务"""
        start_time = time.time()
        
        try:
            # 准备压缩数据
            messages_data = self._prepare_messages_for_compression(task.messages)
            prompt = self.compression_prompts[task.level]
            
            # 调用LLM进行压缩
            full_prompt = prompt + "\n" + messages_data
            
            response = await self.openai_client.chat_completion_async(
                messages=[
                    {"role": "system", "content": "你是专业的对话历史压缩助手。"},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0.1,
                max_tokens=4000
            )
            
            # 解析压缩结果
            result_data = json.loads(response.choices[0].message.content)
            
            # 转换为Message对象
            compressed_messages = []
            for msg_data in result_data["compressed_messages"]:
                message = Message(
                    id=f"compressed_{int(time.time())}_{len(compressed_messages)}",
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=None,  # 压缩后的消息不保留时间戳
                    metadata=msg_data.get("metadata", {})
                )
                compressed_messages.append(message)
            
            execution_time = time.time() - start_time
            
            return CompressionResult(
                session_id=task.session_id,
                original_count=len(task.messages),
                compressed_count=len(compressed_messages),
                compression_ratio=result_data.get("compression_ratio", 0.7),
                compressed_messages=compressed_messages,
                summary=result_data.get("summary", ""),
                key_decisions=result_data.get("key_decisions", []),
                execution_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return CompressionResult(
                session_id=task.session_id,
                original_count=len(task.messages),
                compressed_count=0,
                compression_ratio=0.0,
                compressed_messages=[],
                summary="",
                key_decisions=[],
                execution_time=execution_time,
                success=False,
                error=str(e)
            )

    def _prepare_messages_for_compression(self, messages: List[Message]) -> str:
        """准备消息数据用于压缩"""
        formatted_messages = []

        for i, msg in enumerate(messages, 1):
            role_name = {"user": "用户", "assistant": "助手", "system": "系统"}.get(
                msg.role.value, msg.role.value
            )

            # 处理工具调用信息
            tool_info = ""
            if msg.metadata and msg.metadata.get("tool_calls"):
                tool_names = [tc.get("name", "未知工具") for tc in msg.metadata["tool_calls"]]
                tool_info = f" [调用工具: {', '.join(tool_names)}]"

            formatted_messages.append(
                f"[消息{i}] {role_name}{tool_info}: {msg.content}"
            )

        return "\n".join(formatted_messages)

    async def schedule_compression(
        self, 
        session_id: str, 
        messages: List[Message], 
        level: CompressionLevel = CompressionLevel.MEDIUM,
        priority: int = 0
    ) -> bool:
        """调度压缩任务"""
        if len(messages) < self.config["min_messages_to_compress"]:
            return False
            
        task = CompressionTask(
            session_id=session_id,
            messages=messages,
            level=level,
            priority=priority
        )
        
        try:
            await self.compression_queue.put(task)
            return True
        except Exception as e:
            print(f"⚠️ 调度压缩任务失败: {e}")
            return False

    def should_compress(self, messages: List[Message]) -> Tuple[bool, CompressionLevel]:
        """判断是否需要压缩以及压缩级别"""
        if len(messages) < self.config["min_messages_to_compress"]:
            return False, CompressionLevel.LIGHT
            
        # 估算token数量（简单估算：中文1字符≈1token，英文1词≈1token）
        total_tokens = 0
        for msg in messages:
            # 简单估算：中文字符数 + 英文单词数
            chinese_chars = len([c for c in msg.content if '\u4e00' <= c <= '\u9fff'])
            english_words = len(msg.content.replace('，', ' ').replace('。', ' ').split())
            total_tokens += chinese_chars + english_words
        
        if total_tokens > self.config["compression_threshold"]:
            if total_tokens > self.config["max_context_length"]:
                return True, CompressionLevel.HEAVY
            elif total_tokens > self.config["compression_threshold"] * 1.5:
                return True, CompressionLevel.MEDIUM
            else:
                return True, CompressionLevel.LIGHT
                
        return False, CompressionLevel.LIGHT

    def get_compression_stats(self) -> Dict[str, Any]:
        """获取压缩统计信息"""
        return {
            "is_running": self.is_running,
            "queue_size": self.compression_queue.qsize(),
            "config": self.config.copy()
        }


# 全局压缩器实例
_compressor = None


def get_compressor() -> ContextCompressor:
    """获取全局压缩器实例"""
    global _compressor
    if _compressor is None:
        _compressor = ContextCompressor()
    return _compressor


async def start_compression_service():
    """启动全局压缩服务"""
    compressor = get_compressor()
    await compressor.start_compression_service()


async def stop_compression_service():
    """停止全局压缩服务"""
    compressor = get_compressor()
    await compressor.stop_compression_service()


def cleanup_compression():
    """清理压缩相关资源（同步版本）"""
    global _compressor
    if _compressor and _compressor.is_running:
        try:
            # 在新的事件循环中停止服务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(_compressor.stop_compression_service())
            finally:
                loop.close()
        except Exception:
            pass
        finally:
            _compressor = None
