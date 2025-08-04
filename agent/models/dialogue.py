"""
对话相关数据模型

定义对话历史记录和消息结构。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DialogueMessage:
    """对话消息结构"""
    timestamp: str
    role: str  # "user" | "assistant" | "system"
    content: str
    message_type: str = "text"  # "text" | "confirmation" | "error"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DialogueHistory:
    """对话历史记录"""
    session_id: str
    start_time: str
    messages: List[DialogueMessage] = field(default_factory=list)
    total_messages: int = 0
    last_activity: str = ""

    def add_message(self, role: str, content: str, message_type: str = "text", **metadata):
        """添加新消息"""
        message = DialogueMessage(
            timestamp=datetime.now().isoformat(),
            role=role,
            content=content,
            message_type=message_type,
            metadata=metadata
        )
        self.messages.append(message)
        self.total_messages += 1
        self.last_activity = message.timestamp

    def get_user_messages(self) -> List[DialogueMessage]:
        """获取所有用户消息"""
        return [msg for msg in self.messages if msg.role == "user"]

    def get_assistant_messages(self) -> List[DialogueMessage]:
        """获取所有助手消息"""
        return [msg for msg in self.messages if msg.role == "assistant"]

    def get_recent_messages(self, count: int = 5) -> List[DialogueMessage]:
        """获取最近的消息"""
        return self.messages[-count:] if count <= len(self.messages) else self.messages

    def get_messages_by_type(self, message_type: str) -> List[DialogueMessage]:
        """根据消息类型获取消息"""
        return [msg for msg in self.messages if msg.message_type == message_type]
