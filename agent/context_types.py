"""
GTPlanner Agent层无状态化数据结构定义

定义了Agent层无状态重构所需的核心数据类型：
- AgentContext: 客户端传入的完整上下文信息（只读）
- AgentResult: Agent处理结果，只包含当次对话新增的内容
- Message: 标准化的对话消息
- ToolExecution: 标准化的工具执行记录

设计原则：
1. Agent层完全无状态：不维护任何状态，不修改传入的上下文
2. 纯函数式处理：相同输入产生相同输出
3. 增量返回：只返回当次对话新增的内容，项目状态采用全量更新保证一致性
4. 客户端负责状态管理：所有状态的持久化和更新由客户端处理
5. 支持压缩上下文：客户端可以压缩历史上下文以控制token使用量

所有数据类都支持序列化/反序列化，确保在客户端和Agent层之间的数据传递。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ProjectStage(Enum):
    """项目阶段枚举"""
    INITIALIZATION = "initialization"
    REQUIREMENTS = "requirements"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


@dataclass
class Message:
    """标准化的对话消息数据结构"""
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp,
            "metadata": self.metadata or {},
            "tool_calls": self.tool_calls or []
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """从字典创建Message实例"""
        return cls(
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=data["timestamp"],
            metadata=data.get("metadata"),
            tool_calls=data.get("tool_calls")
        )


@dataclass
class ToolExecution:
    """标准化的工具执行记录数据结构"""
    id: str
    tool_name: str
    arguments: Dict[str, Any]
    result: Dict[str, Any]
    execution_time: Optional[float]
    timestamp: str
    success: bool
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp,
            "success": self.success,
            "error_message": self.error_message
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolExecution':
        """从字典创建ToolExecution实例"""
        return cls(
            id=data["id"],
            tool_name=data["tool_name"],
            arguments=data["arguments"],
            result=data["result"],
            execution_time=data.get("execution_time"),
            timestamp=data["timestamp"],
            success=data["success"],
            error_message=data.get("error_message")
        )


@dataclass
class AgentContext:
    """Agent上下文数据结构 - 客户端传入的上下文信息（可能已压缩）"""
    session_id: str
    dialogue_history: List[Message]  # 可能是压缩后的对话历史
    current_stage: ProjectStage
    project_state: Dict[str, Any]
    tool_execution_history: List[ToolExecution]  # 可能是压缩后的工具历史
    session_metadata: Dict[str, Any]
    last_updated: Optional[str] = None
    is_compressed: bool = False  # 标识上下文是否已被压缩
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "dialogue_history": [msg.to_dict() for msg in self.dialogue_history],
            "current_stage": self.current_stage.value,
            "project_state": self.project_state,
            "tool_execution_history": [te.to_dict() for te in self.tool_execution_history],
            "session_metadata": self.session_metadata,
            "last_updated": self.last_updated,
            "is_compressed": self.is_compressed
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentContext':
        """从字典创建AgentContext实例"""
        return cls(
            session_id=data["session_id"],
            dialogue_history=[
                Message.from_dict(msg_data)
                for msg_data in data.get("dialogue_history", [])
            ],
            current_stage=ProjectStage(data.get("current_stage", "initialization")),
            project_state=data.get("project_state", {}),
            tool_execution_history=[
                ToolExecution.from_dict(te_data)
                for te_data in data.get("tool_execution_history", [])
            ],
            session_metadata=data.get("session_metadata", {}),
            last_updated=data.get("last_updated"),
            is_compressed=data.get("is_compressed", False)
        )
    
    def get_recent_messages(self, count: int = 10) -> List[Message]:
        """获取最近的消息（只读操作）"""
        return self.dialogue_history[-count:] if self.dialogue_history else []

    def get_project_state_value(self, key: str, default: Any = None) -> Any:
        """获取项目状态值（只读操作）"""
        return self.project_state.get(key, default)

    def get_recent_tool_executions(self, count: int = 5) -> List[ToolExecution]:
        """获取最近的工具执行记录（只读操作）"""
        return self.tool_execution_history[-count:] if self.tool_execution_history else []


@dataclass
class AgentResult:
    """Agent处理结果数据结构 - 只包含当次对话新增的内容"""
    success: bool
    new_assistant_messages: List[Message]  # 当次对话新增的助手消息
    new_tool_executions: List[ToolExecution]  # 当次对话新增的工具执行

    stage_update: Optional[ProjectStage] = None  # 阶段更新（如果有）
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    execution_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "success": self.success,
            "new_assistant_messages": [msg.to_dict() for msg in self.new_assistant_messages],
            "new_tool_executions": [te.to_dict() for te in self.new_tool_executions],
            "stage_update": self.stage_update.value if self.stage_update else None,
            "metadata": self.metadata,
            "error": self.error,
            "execution_time": self.execution_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentResult':
        """从字典创建AgentResult实例"""
        return cls(
            success=data["success"],

            new_assistant_messages=[
                Message.from_dict(msg_data)
                for msg_data in data.get("new_assistant_messages", [])
            ],
            new_tool_executions=[
                ToolExecution.from_dict(te_data)
                for te_data in data.get("new_tool_executions", [])
            ],

            stage_update=ProjectStage(data["stage_update"]) if data.get("stage_update") else None,
            metadata=data.get("metadata", {}),
            error=data.get("error"),
            execution_time=data.get("execution_time")
        )
    
    @classmethod
    def create_success(
        cls,
        new_assistant_messages: Optional[List[Message]] = None,
        new_tool_executions: Optional[List[ToolExecution]] = None,
        stage_update: Optional[ProjectStage] = None,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> 'AgentResult':
        """创建成功结果"""
        return cls(
            success=True,
            new_assistant_messages=new_assistant_messages or [],
            new_tool_executions=new_tool_executions or [],
            stage_update=stage_update,
            metadata=metadata or {},
            execution_time=execution_time
        )
    
    @classmethod
    def create_error(
        cls,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time: Optional[float] = None
    ) -> 'AgentResult':
        """创建错误结果"""
        return cls(
            success=False,
            new_assistant_messages=[],
            new_tool_executions=[],
            metadata=metadata or {},
            error=error,
            execution_time=execution_time
        )


# 工具函数：用于数据验证和转换

def validate_agent_context(context_data: Dict[str, Any]) -> bool:
    """验证AgentContext数据的完整性"""
    required_fields = ["session_id", "current_stage"]
    
    for field in required_fields:
        if field not in context_data:
            return False
    
    # 验证stage值是否有效
    try:
        ProjectStage(context_data["current_stage"])
    except ValueError:
        return False
    
    return True


def create_user_message(content: str) -> Message:
    """创建用户消息的便捷函数"""
    return Message(
        role=MessageRole.USER,
        content=content,
        timestamp=datetime.now().isoformat()
    )


def create_assistant_message(
    content: str, 
    tool_calls: Optional[List[Dict[str, Any]]] = None
) -> Message:
    """创建助手消息的便捷函数"""
    return Message(
        role=MessageRole.ASSISTANT,
        content=content,
        timestamp=datetime.now().isoformat(),
        tool_calls=tool_calls
    )


def create_tool_execution(
    tool_name: str,
    arguments: Dict[str, Any],
    result: Dict[str, Any],
    execution_time: Optional[float] = None,
    success: bool = True,
    error_message: Optional[str] = None
) -> ToolExecution:
    """创建工具执行记录的便捷函数"""
    import uuid
    
    return ToolExecution(
        id=str(uuid.uuid4()),
        tool_name=tool_name,
        arguments=arguments,
        result=result,
        execution_time=execution_time,
        timestamp=datetime.now().isoformat(),
        success=success,
        error_message=error_message
    )
