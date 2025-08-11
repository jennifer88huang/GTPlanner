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
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import threading


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
    """GTPlanner统一上下文管理器"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, sessions_dir: str = ".gtplanner_sessions"):
        """初始化统一上下文管理器"""
        if hasattr(self, '_initialized'):
            return
        
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # 当前会话数据
        self.session_id: Optional[str] = None
        self.messages: List[Message] = []
        self.project_state: Dict[str, Any] = {}
        self.tool_history: List[Dict[str, Any]] = []
        self.stage: ProjectStage = ProjectStage.INITIALIZATION
        
        # 去重缓存
        self.message_hashes: set = set()
        
        # 回调函数
        self.change_callbacks: List[Callable] = []
        
        # 会话元数据
        self.session_metadata = {
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "title": "新会话"
        }
        
        self._initialized = True
    
    # ========== 会话管理 ==========
    
    def create_session(self, title: str = "新会话") -> str:
        """创建新会话"""
        self.session_id = str(uuid.uuid4())[:8]
        self.messages.clear()
        self.project_state.clear()
        self.tool_history.clear()
        self.message_hashes.clear()
        self.stage = ProjectStage.INITIALIZATION
        
        now = datetime.now().isoformat()
        self.session_metadata = {
            "created_at": now,
            "last_updated": now,
            "title": title
        }
        
        self._notify_change("session_created", {"session_id": self.session_id})
        return self.session_id
    
    def load_session(self, session_id: str) -> bool:
        """加载会话"""
        session_file = self.sessions_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return False
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.session_id = session_id
            self.stage = ProjectStage(data.get("stage", "initialization"))
            self.project_state = data.get("project_state", {})
            self.tool_history = data.get("tool_history", [])
            self.session_metadata = data.get("metadata", {})
            
            # 重建消息
            self.messages.clear()
            self.message_hashes.clear()
            
            for msg_data in data.get("messages", []):
                message = Message(
                    id=msg_data.get("id", str(uuid.uuid4())),
                    role=MessageRole(msg_data["role"]),
                    content=msg_data["content"],
                    timestamp=msg_data["timestamp"],
                    metadata=msg_data.get("metadata"),
                    tool_calls=msg_data.get("tool_calls")
                )
                self.messages.append(message)
                self.message_hashes.add(message.content_hash)
            
            self._notify_change("session_loaded", {"session_id": session_id})
            return True
            
        except Exception as e:
            print(f"❌ 加载会话失败: {e}")
            return False
    
    def save_session(self) -> bool:
        """保存当前会话"""
        if not self.session_id:
            return False
        
        try:
            session_file = self.sessions_dir / f"{self.session_id}.json"
            
            self.session_metadata["last_updated"] = datetime.now().isoformat()
            
            data = {
                "session_id": self.session_id,
                "stage": self.stage.value,
                "messages": [msg.to_dict() for msg in self.messages],
                "project_state": self.project_state,
                "tool_history": self.tool_history,
                "metadata": self.session_metadata
            }
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
            return False
    
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
        
        self.messages.append(message)
        self.message_hashes.add(message.content_hash)
        
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
        tool_calls: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """添加助手消息"""
        metadata = None
        if tool_calls:
            metadata = {
                "agent_source": "react_orchestrator",
                "tool_calls": tool_calls,
                "confidence": 0.9
            }
        
        return self.add_message(
            MessageRole.ASSISTANT,
            content,
            metadata=metadata,
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


# 全局实例
context = UnifiedContext()


# 便捷函数
def get_context() -> UnifiedContext:
    """获取全局上下文实例"""
    return context


def create_session(title: str = "新会话") -> str:
    """创建新会话"""
    return context.create_session(title)


def add_user_message(content: str) -> Optional[str]:
    """添加用户消息"""
    return context.add_user_message(content)


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
