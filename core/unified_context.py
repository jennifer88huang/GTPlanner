"""
GTPlanner 统一上下文管理系统

这是GTPlanner的核心上下文管理组件，统一管理：
1. CLI会话数据
2. 后端Agent状态
3. 对话历史
4. 工具执行记录
5. 项目状态信息

设计原则：
- 单一数据源：所有组件都使用这个统一的上下文管理器
- 去重机制：自动防止重复内容
- 实时同步：所有组件的状态变更都实时同步
- 简洁接口：提供简单易用的API
"""

import json
import hashlib
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum


class MessageRole(Enum):
    """消息角色"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class ProjectStage(Enum):
    """项目阶段"""
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
    """标准化消息结构"""
    id: str
    role: MessageRole
    content: str
    timestamp: str
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def __post_init__(self):
        """生成内容哈希用于去重"""
        content_str = f"{self.role.value}:{self.content}"
        if self.tool_calls:
            content_str += f":tools:{json.dumps(self.tool_calls, sort_keys=True)}"
        self.content_hash = hashlib.md5(content_str.encode()).hexdigest()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['role'] = self.role.value
        return result


class UnifiedContext:
    """GTPlanner统一上下文管理器（无状态版本）"""

    _instance = None

    def __new__(cls):
        """简化的单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化统一上下文管理器（无状态版本）"""
        if hasattr(self, '_initialized'):
            return
        
        # 🔧 重构：无状态设计，数据由CLI层传入
        # 当前处理的会话数据（临时，仅在处理期间有效）
        self.session_id: Optional[str] = None
        self.messages: List[Message] = []  # 临时消息列表
        self.llm_context: List[Message] = []  # 临时LLM上下文（由CLI层压缩后传入）
        self.project_state: Dict[str, Any] = {}
        self.tool_history: List[Dict[str, Any]] = []
        self.stage: ProjectStage = ProjectStage.INITIALIZATION

        # 临时去重缓存
        self.message_hashes: set = set()

        # 会话元数据（临时）
        self.session_metadata: Dict[str, Any] = {}

        # 回调函数
        self.change_callbacks: List[Callable] = []

        self._initialized = True

    # ========== 无状态数据处理 ==========

    def load_context_from_cli(self, context_data: Dict[str, Any]) -> None:
        """
        从CLI层加载上下文数据（无状态处理）

        Args:
            context_data: CLI层传递的压缩后上下文数据
        """
        # 清空当前状态
        self.messages.clear()
        self.llm_context.clear()

        # 加载基本信息
        self.session_id = context_data.get("session_id")
        self.stage = ProjectStage(context_data.get("stage", "initialization"))
        self.project_state = context_data.get("project_state", {}).copy()
        self.tool_history = context_data.get("tool_history", []).copy()
        self.session_metadata = context_data.get("metadata", {}).copy()

        # 加载消息（CLI层已压缩）
        for msg_data in context_data.get("messages", []):
            message = Message(
                id=msg_data.get("id", str(uuid.uuid4())),
                role=MessageRole(msg_data["role"]),
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data.get("metadata"),
                tool_calls=msg_data.get("tool_calls")
            )
            # 同时添加到messages和llm_context（CLI层已处理压缩）
            self.messages.append(message)
            self.llm_context.append(message)

        self._notify_change("context_loaded", {
            "session_id": self.session_id,
            "message_count": len(self.messages),
            "stage": self.stage.value
        })

    def get_context_for_cli(self) -> Dict[str, Any]:
        """
        获取上下文数据返回给CLI层（用于持久化）

        Returns:
            包含新增数据的上下文字典
        """
        # 构建返回数据
        messages_data = []
        for msg in self.messages:
            messages_data.append({
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata,
                "tool_calls": msg.tool_calls
            })

        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "messages": messages_data,
            "project_state": self.project_state.copy(),
            "tool_history": self.tool_history.copy(),
            "metadata": self.session_metadata.copy()
        }
    
    # ========== 消息管理 ==========
    
    def add_message(
        self,
        role: Union[MessageRole, str],
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        force_add: bool = False
    ) -> Optional[str]:
        """添加消息（自动去重）"""
        if isinstance(role, str):
            role = MessageRole(role)
        
        message = Message(
            id=str(uuid.uuid4()),
            role=role,
            content=content,
            timestamp=datetime.now().isoformat(),
            metadata=metadata,
            tool_calls=tool_calls
        )
        
        # 去重检查
        if not force_add and message.content_hash in self.message_hashes:
            print(f"🔄 跳过重复消息: {message.content_hash[:8]}")
            return None
        
        # 🔧 重构：无状态处理，直接添加到临时列表
        self.messages.append(message)
        self.llm_context.append(message)

        self._notify_change("message_added", {
            "message_id": message.id,
            "role": role.value,
            "content_preview": content[:50] + "..." if len(content) > 50 else content
        })

        return message.id
    
    def get_messages(
        self,
        role_filter: Optional[Union[MessageRole, List[MessageRole]]] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """获取消息列表"""
        messages = self.messages.copy()
        
        if role_filter:
            if isinstance(role_filter, MessageRole):
                role_filter = [role_filter]
            messages = [msg for msg in messages if msg.role in role_filter]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def get_latest_user_message(self) -> Optional[str]:
        """获取最新用户消息内容"""
        user_messages = self.get_messages(role_filter=MessageRole.USER)
        return user_messages[-1].content if user_messages else None
    
    # ========== 项目状态管理 ==========
    
    def update_state(self, key: str, value: Any) -> None:
        """更新项目状态"""
        old_value = self.project_state.get(key)
        self.project_state[key] = value
        
        self._notify_change("state_updated", {
            "key": key,
            "old_value": old_value,
            "new_value": value
        })
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取项目状态"""
        return self.project_state.get(key, default)
    
    def update_stage(self, stage: Union[ProjectStage, str]) -> None:
        """更新项目阶段"""
        if isinstance(stage, str):
            stage = ProjectStage(stage)
        
        old_stage = self.stage
        self.stage = stage
        
        self._notify_change("stage_updated", {
            "old_stage": old_stage.value,
            "new_stage": stage.value
        })
    
    # ========== 工具执行管理 ==========
    
    def record_tool_execution(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        result: Dict[str, Any],
        execution_time: Optional[float] = None
    ) -> str:
        """记录工具执行"""
        execution_id = str(uuid.uuid4())
        
        execution_record = {
            "id": execution_id,
            "tool_name": tool_name,
            "arguments": arguments,
            "result": result,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat(),
            "success": result.get("success", False)
        }
        
        self.tool_history.append(execution_record)
        
        # 自动更新项目状态（如果工具执行成功）
        if result.get("success") and "result" in result:
            self._auto_update_state_from_tool(tool_name, result["result"])
        
        self._notify_change("tool_executed", {
            "execution_id": execution_id,
            "tool_name": tool_name,
            "success": execution_record["success"]
        })
        
        return execution_id
    
    def get_tool_summary(self, limit: int = 5) -> str:
        """获取工具执行摘要"""
        if not self.tool_history:
            return "无工具执行历史"
        
        recent_tools = self.tool_history[-limit:]
        summary_parts = []
        
        for tool in recent_tools:
            status = "✅" if tool["success"] else "❌"
            summary_parts.append(f"{status} {tool['tool_name']}")
        
        return " | ".join(summary_parts)
    
    # ========== 便捷方法 ==========
    
    def add_user_message(self, content: str) -> Optional[str]:
        """添加用户消息"""
        return self.add_message(MessageRole.USER, content)
    
    def add_assistant_message(
        self,
        content: str,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """添加助手消息"""
        final_metadata = metadata.copy() if metadata else {}
        if tool_calls:
            final_metadata.update({
                "tool_calls": tool_calls,
                "confidence": 0.9
            })
            # 如果没有指定agent_source，使用默认值
            if "agent_source" not in final_metadata:
                final_metadata["agent_source"] = "react_orchestrator"

        return self.add_message(
            MessageRole.ASSISTANT,
            content,
            metadata=final_metadata if final_metadata else None,
            tool_calls=tool_calls
        )
    
    def get_context_summary(self) -> Dict[str, Any]:
        """获取上下文摘要"""
        return {
            "session_id": self.session_id,
            "stage": self.stage.value,
            "message_count": len(self.messages),
            "tool_execution_count": len(self.tool_history),
            "project_state_keys": list(self.project_state.keys()),
            "last_updated": self.session_metadata.get("last_updated"),
            "title": self.session_metadata.get("title")
        }
    
    # ========== 内部方法 ==========
    
    def _auto_update_state_from_tool(self, tool_name: str, result: Any) -> None:
        """根据工具执行结果自动更新状态"""
        state_mapping = {
            "requirements_analysis": "structured_requirements",
            "short_planning": "planning_document",
            "research": "research_findings",
            "architecture_design": "architecture_document"
        }
        
        if tool_name in state_mapping:
            self.update_state(state_mapping[tool_name], result)
    
    def _notify_change(self, event_type: str, data: Dict[str, Any]) -> None:
        """通知变更事件"""
        for callback in self.change_callbacks:
            try:
                callback(event_type, data)
            except Exception as e:
                print(f"⚠️ 回调函数执行失败: {e}")
    
    def add_change_callback(self, callback: Callable) -> None:
        """添加变更回调"""
        self.change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable) -> None:
        """移除变更回调"""
        if callback in self.change_callbacks:
            self.change_callbacks.remove(callback)

    # ========== 清理完成：压缩功能已移至CLI层 ==========






# 全局实例
context = UnifiedContext()


# 便捷函数
def get_context() -> UnifiedContext:
    """获取全局上下文实例"""
    return context




def add_assistant_message(content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
    """添加助手消息"""
    return context.add_assistant_message(content, tool_calls)


def update_state(key: str, value: Any) -> None:
    """更新项目状态"""
    context.update_state(key, value)


def get_state(key: str, default: Any = None) -> Any:
    """获取项目状态"""
    return context.get_state(key, default)


def record_tool_execution(tool_name: str, arguments: Dict[str, Any], result: Dict[str, Any], execution_time: Optional[float] = None) -> str:
    """记录工具执行"""
    return context.record_tool_execution(tool_name, arguments, result, execution_time)


def cleanup_context():
    """清理上下文资源"""
    context.cleanup()
