"""
会话管理器 - CLI层本地文件管理

为GTPlanner CLI提供会话管理功能，重构后的职责：
1. 本地会话文件管理
2. 上下文压缩处理
3. 向统一消息管理层传递压缩后的数据
4. 会话列表管理

不再依赖统一上下文的持久化功能。
"""

import json
import uuid
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from cli.context_compressor import get_cli_compressor, Message


class SessionManager:
    """GTPlanner CLI会话管理器 - 本地文件管理"""

    def __init__(self, sessions_dir: str = ".gtplanner_sessions"):
        """
        初始化会话管理器

        Args:
            sessions_dir: 本地会话存储目录
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

        # 当前会话数据
        self.current_session_id: Optional[str] = None
        self.current_session_data: Dict[str, Any] = {}

        # 获取压缩器
        self.compressor = get_cli_compressor()

    def create_new_session(self, user_name: Optional[str] = None) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())[:8]
        title = f"{user_name}的会话" if user_name else "新会话"

        # 初始化会话数据
        self.current_session_data = {
            "session_id": session_id,
            "title": title,
            "stage": "initialization",
            "messages": [],
            "project_state": {},
            "tool_history": [],
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "user_name": user_name
            }
        }

        # 设置用户信息到项目状态
        if user_name:
            self.current_session_data["project_state"]["user_name"] = user_name

        self.current_session_id = session_id
        return session_id

    def load_session(self, session_id: str) -> bool:
        """从本地文件加载会话"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                self.current_session_data = json.load(f)

            self.current_session_id = session_id
            return True

        except Exception as e:
            print(f"❌ 加载会话失败: {e}")
            return False

    def save_session(self) -> bool:
        """保存当前会话到本地文件"""
        if not self.current_session_id or not self.current_session_data:
            return False

        try:
            session_file = self.sessions_dir / f"{self.current_session_id}.json"

            # 更新最后修改时间
            self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_session_data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"❌ 保存会话失败: {e}")
            return False

    def add_user_message(self, content: str) -> str:
        """
        添加用户消息到当前会话

        Args:
            content: 用户消息内容

        Returns:
            消息ID
        """
        if not self.current_session_data:
            raise ValueError("没有活跃的会话")

        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "role": "user",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": None,
            "tool_calls": None
        }

        self.current_session_data["messages"].append(message)
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

        return message_id

    def add_assistant_message(self, content: str, metadata: Optional[Dict[str, Any]] = None,
                            tool_calls: Optional[List[Dict[str, Any]]] = None) -> str:
        """
        添加助手消息到当前会话

        Args:
            content: 助手消息内容
            metadata: 消息元数据
            tool_calls: 工具调用信息

        Returns:
            消息ID
        """
        if not self.current_session_data:
            raise ValueError("没有活跃的会话")

        message_id = str(uuid.uuid4())
        message = {
            "id": message_id,
            "role": "assistant",
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
            "tool_calls": tool_calls
        }

        self.current_session_data["messages"].append(message)
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

        return message_id

    async def get_compressed_context_for_agent(self) -> Dict[str, Any]:
        """
        获取压缩后的上下文数据，用于传递给统一消息管理层

        Returns:
            压缩后的上下文数据
        """
        if not self.current_session_data:
            return {}

        # 转换消息格式
        messages = []
        for msg_data in self.current_session_data["messages"]:
            message = Message(
                id=msg_data["id"],
                role=msg_data["role"],
                content=msg_data["content"],
                timestamp=msg_data["timestamp"],
                metadata=msg_data.get("metadata"),
                tool_calls=msg_data.get("tool_calls")
            )
            messages.append(message)

        # 异步压缩消息
        compressed_messages = await self.compressor.compress_messages_async(messages)

        # 转换回字典格式
        compressed_msg_dicts = []
        for msg in compressed_messages:
            compressed_msg_dicts.append({
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "metadata": msg.metadata,
                "tool_calls": msg.tool_calls
            })

        # 构建压缩后的上下文
        compressed_context = {
            "session_id": self.current_session_id,
            "stage": self.current_session_data.get("stage", "initialization"),
            "messages": compressed_msg_dicts,
            "project_state": self.current_session_data.get("project_state", {}),
            "tool_history": self.current_session_data.get("tool_history", []),
            "metadata": self.current_session_data.get("metadata", {})
        }

        return compressed_context

    def get_session_data(self) -> Dict[str, Any]:
        """获取当前会话数据（兼容旧接口）"""
        if not self.current_session_data:
            return {
                "session_id": None,
                "title": None,
                "created_at": None,
                "current_stage": "initialization",
                "messages": [],
                "project_state": {},
                "tool_history": [],
                "metadata": {}
            }

        return {
            # 会话基本信息
            "session_id": self.current_session_data.get("session_id"),
            "title": self.current_session_data.get("title"),
            "created_at": self.current_session_data.get("created_at"),
            "current_stage": self.current_session_data.get("stage", "initialization"),

            # 消息和历史
            "messages": self.current_session_data.get("messages", []),
            "dialogue_history": {"messages": self.current_session_data.get("messages", [])},
            "tool_history": self.current_session_data.get("tool_history", []),
            "tool_execution_history": self.current_session_data.get("tool_history", []),

            # 项目状态
            "project_state": self.current_session_data.get("project_state", {}),
            "structured_requirements": self.current_session_data.get("project_state", {}).get("structured_requirements"),
            "confirmation_document": self.current_session_data.get("project_state", {}).get("planning_document"),
            "research_findings": self.current_session_data.get("project_state", {}).get("research_findings"),
            "agent_design_document": self.current_session_data.get("project_state", {}).get("architecture_document"),

            # 元数据
            "metadata": self.current_session_data.get("metadata", {})
        }

    def update_project_state(self, key: str, value: Any) -> None:
        """更新项目状态"""
        if not self.current_session_data:
            raise ValueError("没有活跃的会话")

        if "project_state" not in self.current_session_data:
            self.current_session_data["project_state"] = {}

        self.current_session_data["project_state"][key] = value
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

    def update_stage(self, stage: str) -> None:
        """更新当前阶段"""
        if not self.current_session_data:
            raise ValueError("没有活跃的会话")

        self.current_session_data["stage"] = stage
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

    def add_tool_execution(self, tool_execution: Dict[str, Any]) -> None:
        """添加工具执行记录"""
        if not self.current_session_data:
            raise ValueError("没有活跃的会话")

        if "tool_history" not in self.current_session_data:
            self.current_session_data["tool_history"] = []

        self.current_session_data["tool_history"].append(tool_execution)
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []

        for session_file in self.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                sessions.append({
                    "session_id": data["session_id"],
                    "title": data.get("title", data.get("metadata", {}).get("title", "未命名会话")),
                    "stage": data.get("stage", "initialization"),
                    "created_at": data.get("metadata", {}).get("created_at", ""),
                    "last_updated": data.get("metadata", {}).get("last_updated", ""),
                    "message_count": len(data.get("messages", []))
                })

            except Exception as e:
                print(f"⚠️ 读取会话文件失败 {session_file}: {e}")

        # 按最后更新时间排序
        sessions.sort(key=lambda x: x.get("last_updated", ""), reverse=True)
        return sessions

    def get_current_session_id(self) -> Optional[str]:
        """获取当前会话ID"""
        return self.current_session_id

    def has_active_session(self) -> bool:
        """检查是否有活跃会话"""
        return self.current_session_id is not None and bool(self.current_session_data)

    def get_conversation_summary(self, max_messages: int = 10) -> str:
        """获取对话摘要"""
        if not self.current_session_data:
            return "无对话历史"

        messages = self.current_session_data.get("messages", [])
        recent_messages = messages[-max_messages:] if len(messages) > max_messages else messages

        if not recent_messages:
            return "无对话历史"

        summary_parts = []
        for msg in recent_messages:
            role_name = {"user": "用户", "assistant": "助手", "system": "系统"}.get(
                msg["role"], msg["role"]
            )

            # 截断长消息
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            summary_parts.append(f"{role_name}: {content}")

        return "\n".join(summary_parts)

    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息摘要"""
        if not self.current_session_data:
            return {}

        messages = self.current_session_data.get("messages", [])
        return {
            "session_id": self.current_session_id,
            "stage": self.current_session_data.get("stage", "initialization"),
            "message_count": len(messages),
            "tool_execution_count": len(self.current_session_data.get("tool_history", [])),
            "created_at": self.current_session_data.get("metadata", {}).get("created_at", ""),
            "last_updated": self.current_session_data.get("metadata", {}).get("last_updated", "")
        }

    def cleanup_duplicate_messages(self) -> int:
        """清理重复消息"""
        if not self.current_session_data:
            return 0

        messages = self.current_session_data.get("messages", [])
        original_count = len(messages)

        # 使用内容哈希去重
        seen_hashes = set()
        unique_messages = []

        for msg in messages:
            # 简单的内容哈希
            content_hash = hash(f"{msg['role']}:{msg['content']}")
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_messages.append(msg)

        self.current_session_data["messages"] = unique_messages
        cleaned_count = original_count - len(unique_messages)

        if cleaned_count > 0:
            print(f"🧹 已清理 {cleaned_count} 条重复消息")
            self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

        return cleaned_count

    def delete_session(self, session_id: str) -> bool:
        """删除指定会话"""
        session_file = self.sessions_dir / f"{session_id}.json"

        if not session_file.exists():
            return False

        try:
            session_file.unlink()

            # 如果删除的是当前会话，清空当前状态
            if session_id == self.current_session_id:
                self.current_session_id = None
                self.current_session_data = {}

            return True

        except Exception as e:
            print(f"❌ 删除会话失败: {e}")
            return False

    def sync_tool_execution_history(self, tool_history: List[Dict[str, Any]]) -> None:
        """
        同步工具执行历史（兼容CLI调用）

        Args:
            tool_history: 工具执行历史列表
        """
        if not self.current_session_data:
            return

        # 将工具历史同步到当前会话
        current_tool_history = self.current_session_data.get("tool_history", [])

        for tool_record in tool_history:
            if tool_record not in current_tool_history:
                current_tool_history.append(tool_record)

        self.current_session_data["tool_history"] = current_tool_history
        self.current_session_data["metadata"]["last_updated"] = datetime.now().isoformat()

    def sync_tool_result_data(self, session_state: Dict[str, Any]) -> None:
        """
        同步工具结果数据（兼容CLI调用）

        Args:
            session_state: 会话状态数据
        """
        if not self.current_session_data:
            return

        # 同步各种工具结果到项目状态
        result_mappings = {
            "structured_requirements": "structured_requirements",
            "confirmation_document": "planning_document",
            "research_findings": "research_findings",
            "agent_design_document": "architecture_document"
        }

        for session_key, project_key in result_mappings.items():
            if session_key in session_state and session_state[session_key]:
                self.update_project_state(project_key, session_state[session_key])

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'compressor'):
            self.compressor.cleanup()