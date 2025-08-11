"""
GTPlanner 系统级共享状态管理 - 基于统一上下文

本模块管理整个GTPlanner系统的共享变量，现在基于统一上下文管理器实现。
作为系统的"单一数据源"，确保数据在各个Agent和节点间的一致性和完整性。

重构后消除了重复的状态管理代码。
"""

from typing import Dict, List, Any, Optional
from core.unified_context import get_context

class SharedState:
    """系统级共享状态管理器 - 基于统一上下文"""

    def __init__(self):
        """初始化共享状态"""
        # 获取统一上下文实例
        self.context = get_context()
        
        # 如果没有活跃会话，创建一个
        if not self.context.session_id:
            self.context.create_session("系统会话")
        
        self.session_id = self.context.session_id

    def add_user_message(self, content: str, **metadata):
        """添加用户消息"""
        return self.context.add_user_message(content)

    def add_assistant_message(self, content: str, agent_source: str = "", **metadata):
        """添加助手消息"""
        if agent_source:
            metadata["agent_source"] = agent_source
        
        return self.context.add_assistant_message(content)

    def add_system_message(self, content: str, **metadata):
        """添加系统消息"""
        return self.context.add_message("system", content, metadata=metadata if metadata else None)

    def update_stage(self, stage: str):
        """更新当前处理阶段"""
        self.context.update_stage(stage)

    def record_error(self, error: Exception, context: str = ""):
        """记录错误"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": self.context.session_metadata.get("last_updated", "")
        }
        
        # 更新错误计数
        error_count = self.context.get_state("error_count", 0) + 1
        self.context.update_state("error_count", error_count)
        self.context.update_state("last_error", error_info)

    def get_current_stage_info(self) -> Dict[str, Any]:
        """获取当前阶段信息"""
        context_summary = self.context.get_context_summary()
        
        return {
            "current_stage": context_summary.get("stage", "initialization"),
            "total_messages": context_summary.get("message_count", 0),
            "tool_execution_count": context_summary.get("tool_execution_count", 0),
            "error_count": self.context.get_state("error_count", 0)
        }

    def is_processing_complete(self) -> bool:
        """判断处理是否完成"""
        return (
            self.context.stage.value == "completed" and
            self._is_requirements_complete() and
            self._is_research_comprehensive() and
            self._is_architecture_complete()
        )

    def _is_requirements_complete(self) -> bool:
        """检查需求是否完整"""
        req = self.context.get_state("structured_requirements", {})
        return bool(req.get("project_overview") and req.get("functional_requirements"))

    def _is_research_comprehensive(self) -> bool:
        """检查研究是否全面"""
        research = self.context.get_state("research_findings", {})
        return bool(research.get("topics") and research.get("results"))

    def _is_architecture_complete(self) -> bool:
        """检查架构是否完整"""
        arch = self.context.get_state("architecture_document", {})
        return bool(arch.get("diagrams") and arch.get("components"))

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        context_summary = self.context.get_context_summary()
        
        return {
            "session_id": self.session_id,
            "current_stage": context_summary.get("stage", "initialization"),
            "requirements_complete": self._is_requirements_complete(),
            "research_comprehensive": self._is_research_comprehensive(),
            "architecture_complete": self._is_architecture_complete(),
            "total_messages": context_summary.get("message_count", 0),
            "tool_execution_count": context_summary.get("tool_execution_count", 0),
            "error_count": self.context.get_state("error_count", 0),
            "last_updated": context_summary.get("last_updated", "")
        }

    def get_data(self) -> Dict[str, Any]:
        """获取所有共享数据（兼容旧接口）"""
        # 构建兼容的数据结构
        messages = []
        for msg in self.context.messages:
            messages.append({
                "timestamp": msg.timestamp,
                "role": msg.role.value,
                "content": msg.content,
                "message_type": "text",
                "metadata": msg.metadata or {}
            })
        
        return {
            "session_id": self.context.session_id,
            "dialogue_history": {
                "session_id": self.context.session_id,
                "start_time": self.context.session_metadata.get("created_at", ""),
                "messages": messages,
                "total_messages": len(messages),
                "last_activity": self.context.session_metadata.get("last_updated", "")
            },
            "current_stage": self.context.stage.value,
            "project_state": self.context.project_state.copy(),
            "tool_execution_history": self.context.tool_history.copy(),
            "structured_requirements": self.context.get_state("structured_requirements"),
            "research_findings": self.context.get_state("research_findings"),
            "architecture_document": self.context.get_state("architecture_document"),
            "planning_document": self.context.get_state("planning_document"),
            "error_count": self.context.get_state("error_count", 0),
            "last_error": self.context.get_state("last_error")
        }

    def update_data(self, key: str, value: Any) -> None:
        """更新共享数据"""
        self.context.update_state(key, value)

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取指定键的值"""
        return self.context.get_state(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """设置指定键的值"""
        self.context.update_state(key, value)

    def get_dialogue_history(self) -> Dict[str, Any]:
        """获取对话历史"""
        return self.get_data()["dialogue_history"]

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取消息列表"""
        messages = self.context.get_messages(limit=limit)
        return [msg.to_dict() for msg in messages]

    def clear_messages(self) -> None:
        """清空消息历史"""
        self.context.messages.clear()
        self.context.message_hashes.clear()

    def get_session_id(self) -> str:
        """获取会话ID"""
        return self.context.session_id

    def export_to_json(self) -> str:
        """导出为JSON字符串"""
        import json
        return json.dumps(self.get_data(), ensure_ascii=False, indent=2)

    def import_from_json(self, json_str: str) -> bool:
        """从JSON字符串导入数据"""
        try:
            import json
            data = json.loads(json_str)
            
            # 重建会话
            session_id = data.get("session_id")
            if session_id:
                return self.context.load_session(session_id)
            
            return False
        except Exception as e:
            print(f"导入JSON数据失败: {e}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
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
            print(f"🧹 SharedState已清理 {cleaned_count} 条重复消息")
        
        return cleaned_count

    def save_session(self) -> bool:
        """保存当前会话"""
        return self.context.save_session()

    def load_session(self, session_id: str) -> bool:
        """加载指定会话"""
        success = self.context.load_session(session_id)
        if success:
            self.session_id = self.context.session_id
        return success


# 全局实例（保持向后兼容）
shared_state = SharedState()


def get_shared_state() -> SharedState:
    """获取全局共享状态实例"""
    return shared_state


def reset_shared_state() -> SharedState:
    """重置全局共享状态实例"""
    global shared_state
    shared_state = SharedState()
    return shared_state
