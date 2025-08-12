"""
GTPlanner 系统级共享状态管理 - Agent层专用

本模块管理Agent层的共享变量，不直接访问统一上下文管理层。
遵循单向数据流原则：统一消息管理层 → shared.py → Agent层

Agent层通过此模块获取和操作共享状态，数据由上游传递。
"""

from typing import Dict, List, Any, Optional

class SharedState:
    """Agent层共享状态管理器 - 不直接访问统一上下文"""

    def __init__(self, initial_data: Dict[str, Any] = None):
        """
        初始化共享状态

        Args:
            initial_data: 由上游传递的初始数据
        """
        # 🔧 新架构：不直接访问get_context，数据由上游传递
        self.data = initial_data or {}
        self.session_id = self.data.get("session_id", "default_session")

    def update_stage(self, stage: str):
        """更新当前处理阶段"""
        self.data["current_stage"] = stage

    def record_error(self, error: Exception, context_info: str = ""):
        """记录错误"""
        error_info = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context_info,
            "timestamp": self.data.get("last_updated", "")
        }

        # 更新错误计数
        error_count = self.data.get("error_count", 0) + 1
        self.data["error_count"] = error_count
        self.data["last_error"] = error_info

    def get_current_stage_info(self) -> Dict[str, Any]:
        """获取当前阶段信息"""
        dialogue_history = self.data.get("dialogue_history", {})
        messages = dialogue_history.get("messages", [])

        return {
            "current_stage": self.data.get("current_stage", "initialization"),
            "total_messages": len(messages),
            "tool_execution_count": len(self.data.get("tool_execution_history", [])),
            "error_count": self.data.get("error_count", 0)
        }

    def is_processing_complete(self) -> bool:
        """判断处理是否完成"""
        return (
            self.data.get("current_stage") == "completed" and
            self._is_requirements_complete() and
            self._is_research_comprehensive() and
            self._is_architecture_complete()
        )

    def _is_requirements_complete(self) -> bool:
        """检查需求是否完整（已废弃，需求分析子工作流已取消）"""
        # 需求分析子工作流已取消，始终返回True
        return True

    def _is_research_comprehensive(self) -> bool:
        """检查研究是否全面"""
        research = self.data.get("research_findings", {})
        return bool(research.get("topics") and research.get("results"))

    def _is_architecture_complete(self) -> bool:
        """检查架构是否完整"""
        arch = self.data.get("agent_design_document", {})
        return bool(arch.get("diagrams") and arch.get("components"))

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        dialogue_history = self.data.get("dialogue_history", {})
        messages = dialogue_history.get("messages", [])

        return {
            "session_id": self.session_id,
            "current_stage": self.data.get("current_stage", "initialization"),
            "requirements_complete": self._is_requirements_complete(),
            "research_comprehensive": self._is_research_comprehensive(),
            "architecture_complete": self._is_architecture_complete(),
            "total_messages": len(messages),
            "tool_execution_count": len(self.data.get("tool_execution_history", [])),
            "error_count": self.data.get("error_count", 0),
            "last_updated": self.data.get("last_updated", "")
        }

    def get_data(self) -> Dict[str, Any]:
        """获取所有共享数据"""
        # 🔧 新架构：直接返回内部数据，不访问统一上下文
        return self.data.copy()

    def to_pocketflow_shared(self, extra_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        获取pocketflow格式的共享数据

        Args:
            extra_context: 额外的上下文数据（如流式回调）

        Returns:
            pocketflow的shared字典
        """
        # 基于内部数据构建pocketflow格式
        shared = {
            # 核心对话数据
            "dialogue_history": self.data.get("dialogue_history", {"messages": []}),
            "current_stage": self.data.get("current_stage", "initialization"),

            # 项目状态数据
            "research_findings": self.data.get("research_findings"),
            "agent_design_document": self.data.get("agent_design_document"),
            "confirmation_document": self.data.get("confirmation_document"),
            "structured_requirements": self.data.get("structured_requirements"),

            # 工具执行历史
            "tool_execution_history": self.data.get("tool_execution_history", []),

            # 流程元数据
            "flow_start_time": None,  # 将在prep_async中设置
            "flow_metadata": {},

            # 错误处理
            "react_error": None,
            "react_post_error": None,
        }

        # 添加额外的上下文数据
        if extra_context:
            shared.update(extra_context)

        return shared

    def update_data(self, key: str, value: Any) -> None:
        """更新共享数据"""
        self.data[key] = value

    def get_value(self, key: str, default: Any = None) -> Any:
        """获取指定键的值"""
        return self.data.get(key, default)

    def set_value(self, key: str, value: Any) -> None:
        """设置指定键的值"""
        self.data[key] = value

    def get_dialogue_history(self) -> Dict[str, Any]:
        """获取对话历史"""
        return self.data.get("dialogue_history", {})

    def get_messages(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取消息列表"""
        dialogue_history = self.data.get("dialogue_history", {})
        messages = dialogue_history.get("messages", [])
        if limit:
            messages = messages[-limit:]
        return messages

    def get_session_id(self) -> str:
        """获取会话ID"""
        return self.session_id

    @property
    def current_stage(self) -> str:
        """获取当前阶段"""
        return self.data.get("current_stage", "initialization")

    @property
    def error_count(self) -> int:
        """获取错误计数"""
        return self.data.get("error_count", 0)

    @property
    def dialogue_history(self) -> Dict[str, Any]:
        """获取对话历史"""
        return self.get_dialogue_history()

    @property
    def research_findings(self) -> Any:
        """获取研究发现"""
        return self.data.get("research_findings")

    @property
    def architecture_draft(self) -> Any:
        """获取架构草稿"""
        return self.data.get("agent_design_document")

    def get_summary(self) -> Dict[str, Any]:
        """获取状态摘要"""
        return self.get_progress_summary()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（兼容旧接口）"""
        return self.get_data()

    def save_to_file(self, filepath: str) -> bool:
        """保存状态到文件"""
        try:
            import json
            data = self.to_dict()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"保存状态到文件失败: {e}")
            return False


class SharedStateFactory:
    """SharedState工厂类 - 支持创建独立的SharedState实例"""

    @staticmethod
    def create_from_unified_context() -> SharedState:
        """
        从统一消息管理层创建SharedState实例

        Returns:
            新的SharedState实例
        """
        from core.unified_context import get_context
        context = get_context()

        # 构建LLM上下文消息（压缩后的）
        llm_messages = []
        for msg in context.llm_context:
            llm_messages.append({
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp,
                "tool_calls": msg.tool_calls
            })

        # 构建shared数据
        shared_data = {
            "session_id": context.session_id,
            "dialogue_history": {"messages": llm_messages},
            "current_stage": context.stage.value,
            "research_findings": context.get_state("research_findings"),
            "agent_design_document": context.get_state("architecture_document"),
            "confirmation_document": context.get_state("planning_document"),
            "structured_requirements": context.get_state("structured_requirements"),
            "tool_execution_history": context.tool_history.copy(),
            "last_updated": context.session_metadata.get("last_updated", ""),
        }

        return SharedState(shared_data)

    @staticmethod
    def create_from_data(data: Dict[str, Any]) -> SharedState:
        """
        从指定数据创建SharedState实例

        Args:
            data: 初始化数据

        Returns:
            新的SharedState实例
        """
        return SharedState(data)

    @staticmethod
    def create_empty() -> SharedState:
        """
        创建空的SharedState实例（用于测试）

        Returns:
            空的SharedState实例
        """
        return SharedState({})


# 🔧 新架构：保留向后兼容的全局实例（逐步废弃）
_global_shared_state = None


def get_shared_state() -> SharedState:
    """
    获取全局共享状态实例（已废弃，建议使用工厂模式）

    Returns:
        全局SharedState实例
    """
    global _global_shared_state
    if _global_shared_state is None:
        _global_shared_state = SharedStateFactory.create_empty()
    return _global_shared_state


def init_shared_state(data: Dict[str, Any]) -> SharedState:
    """
    初始化全局共享状态实例（已废弃，建议使用工厂模式）

    Args:
        data: 由上游传递的数据

    Returns:
        全局SharedState实例
    """
    global _global_shared_state
    _global_shared_state = SharedState(data)
    return _global_shared_state


def reset_shared_state() -> SharedState:
    """重置全局共享状态实例（已废弃，建议使用工厂模式）"""
    global _global_shared_state
    _global_shared_state = SharedStateFactory.create_empty()
    return _global_shared_state



