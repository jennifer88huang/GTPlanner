"""
会话管理器 - 基于统一上下文管理

为GTPlanner CLI提供会话管理功能，现在基于统一上下文管理器实现：
1. 会话创建和恢复
2. 对话历史管理
3. 会话列表管理
4. 与统一上下文的集成

重构后的设计更加简洁，消除了重复代码。
"""

import json
from typing import Dict, List, Any, Optional
from core.unified_context import get_context, UnifiedContext


class SessionManager:
    """GTPlanner CLI会话管理器 - 基于统一上下文"""

    def __init__(self, sessions_dir: str = ".gtplanner_sessions"):
        """
        初始化会话管理器

        Args:
            sessions_dir: 会话存储目录（传递给统一上下文）
        """
        # 获取统一上下文实例
        self.context = get_context()

        # 如果需要自定义目录，重新初始化上下文
        if sessions_dir != ".gtplanner_sessions":
            self.context = UnifiedContext(sessions_dir)

        # 当前会话ID（从统一上下文获取）
        self.current_session_id = self.context.session_id

    def create_new_session(self, user_name: Optional[str] = None) -> str:
        """创建新会话"""
        title = f"{user_name}的会话" if user_name else "新会话"
        session_id = self.context.create_session(title)

        # 设置用户信息到项目状态
        if user_name:
            self.context.update_state("user_name", user_name)

        self.current_session_id = session_id
        return session_id

    def load_session(self, session_id: str) -> bool:
        """加载指定会话"""
        success = self.context.load_session(session_id)
        if success:
            self.current_session_id = session_id
        return success

    def save_session(self) -> bool:
        """保存当前会话"""
        return self.context.save_session()

    def add_user_message(self, content: str) -> Optional[str]:
        """添加用户消息"""
        return self.context.add_user_message(content)

    def add_assistant_message(self, content: str, tool_calls: Optional[List[Dict]] = None) -> Optional[str]:
        """添加AI助手消息"""
        return self.context.add_assistant_message(content, tool_calls)

    def get_session_data(self) -> Dict[str, Any]:
        """获取当前会话数据（兼容旧接口）"""
        if not self.context.session_id:
            return {}

        # 转换为旧格式以保持兼容性
        messages = []
        for msg in self.context.messages:
            msg_dict = {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
            if msg.metadata:
                msg_dict["metadata"] = msg.metadata
            messages.append(msg_dict)

        return {
            "dialogue_history": {"messages": messages},
            "current_stage": self.context.stage.value,
            "structured_requirements": self.context.get_state("structured_requirements"),
            "confirmation_document": self.context.get_state("planning_document"),
            "research_findings": self.context.get_state("research_findings"),
            "agent_design_document": self.context.get_state("architecture_document"),
            "tool_execution_history": self.context.tool_history
        }

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []

        for session_file in self.context.sessions_dir.glob("*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                sessions.append({
                    "session_id": data["session_id"],
                    "title": data.get("metadata", {}).get("title", "未命名会话"),
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
        return self.current_session_id is not None

    def get_conversation_summary(self, max_messages: int = 10) -> str:
        """获取对话摘要"""
        recent_messages = self.context.get_messages(limit=max_messages)

        if not recent_messages:
            return "无对话历史"

        summary_parts = []
        for msg in recent_messages:
            role_name = {"user": "用户", "assistant": "助手", "system": "系统"}.get(
                msg.role.value, msg.role.value
            )

            # 截断长消息
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{role_name}: {content}")

        return "\n".join(summary_parts)

    def get_session_info(self) -> Dict[str, Any]:
        """获取会话信息摘要"""
        return self.context.get_context_summary()

    def cleanup_duplicate_messages(self) -> int:
        """清理重复消息"""
        if not self.context.session_id:
            return 0

        original_count = len(self.context.messages)

        # 使用内容哈希去重
        seen_hashes = set()
        unique_messages = []

        for msg in self.context.messages:
            if msg.content_hash not in seen_hashes:
                seen_hashes.add(msg.content_hash)
                unique_messages.append(msg)

        self.context.messages = unique_messages

        # 重建缓存
        self.context.message_hashes.clear()
        for msg in unique_messages:
            self.context.message_hashes.add(msg.content_hash)

        cleaned_count = original_count - len(unique_messages)

        if cleaned_count > 0:
            print(f"🧹 已清理 {cleaned_count} 条重复消息")

        return cleaned_count

    def sync_tool_execution_history(self, tool_history: List[Dict[str, Any]]) -> None:
        """
        同步工具执行历史（兼容CLI调用）

        Args:
            tool_history: 工具执行历史列表
        """
        # 将工具历史同步到统一上下文
        for tool_record in tool_history:
            if tool_record not in self.context.tool_history:
                self.context.tool_history.append(tool_record)

    def sync_tool_result_data(self, session_state: Dict[str, Any]) -> None:
        """
        同步工具结果数据（兼容CLI调用）

        Args:
            session_state: 会话状态数据
        """
        # 同步各种工具结果到统一上下文
        result_mappings = {
            "structured_requirements": "structured_requirements",
            "confirmation_document": "planning_document",
            "research_findings": "research_findings",
            "agent_design_document": "architecture_document"
        }

        for session_key, context_key in result_mappings.items():
            if session_key in session_state and session_state[session_key]:
                self.context.update_state(context_key, session_state[session_key])

    def save_current_session(self) -> bool:
        """
        保存当前会话（兼容CLI调用）

        Returns:
            是否保存成功
        """
        return self.save_session()