"""
流式响应系统

提供完整的流式响应功能，支持CLI和HTTP SSE客户端。
"""

from .stream_types import (
    StreamEvent,
    StreamEventType,
    StreamCallbackType,
    StreamEventBuilder,
    AssistantMessageChunk,
    ToolCallStatus,
    StreamEventIterator,
    StreamEventHandler
)

from .stream_interface import (
    StreamHandler,
    StreamProducer,
    StreamConsumer,
    StreamingSession,
    StreamingManager,
    StreamingCapable,
    StreamingResult,
    streaming_manager
)

from .cli_handler import CLIStreamHandler

__all__ = [
    # 核心类型
    "StreamEvent",
    "StreamEventType",
    "StreamCallbackType",
    "StreamEventBuilder",
    "AssistantMessageChunk",
    "ToolCallStatus",
    "StreamEventIterator",
    "StreamEventHandler",
    
    # 接口和管理
    "StreamHandler",
    "StreamProducer", 
    "StreamConsumer",
    "StreamingSession",
    "StreamingManager",
    "StreamingCapable",
    "StreamingResult",
    "streaming_manager",
    
    # 具体实现
    "CLIStreamHandler"
]
