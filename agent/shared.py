"""
GTPlanner 系统级共享状态管理

本模块管理整个GTPlanner系统的共享变量，作为系统的"单一数据源"，
确保数据在各个Agent和节点间的一致性和完整性。

基于架构文档中定义的系统级共享变量结构实现。
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import uuid

# 导入各个数据模型模块
from .models.dialogue import DialogueHistory, DialogueMessage
from .models.user_intent import UserIntent
from .models.requirements import StructuredRequirements
from .models.research import ResearchFindings
from .models.architecture import ArchitectureDraft


class SharedState:
    """系统级共享状态管理器"""

    def __init__(self):
        """初始化共享状态"""
        self.session_id = str(uuid.uuid4())
        self.dialogue_history = DialogueHistory(
            session_id=self.session_id,
            start_time=datetime.now().isoformat()
        )
        self.user_intent = UserIntent()
        self.structured_requirements = StructuredRequirements()
        self.research_findings = ResearchFindings()
        self.architecture_draft = ArchitectureDraft()

        # 处理状态跟踪
        self.current_stage = "initialization"  # 当前处理阶段
        self.processing_history = []  # 处理历史记录
        self.error_count = 0  # 错误计数
        self.last_error = None  # 最后一个错误

    def add_user_message(self, content: str, **metadata):
        """添加用户消息"""
        self.dialogue_history.add_message("user", content, **metadata)

    def add_assistant_message(self, content: str, agent_source: str = "", **metadata):
        """添加助手消息"""
        metadata.update({"agent_source": agent_source})
        self.dialogue_history.add_message("assistant", content, **metadata)

    def add_system_message(self, content: str, **metadata):
        """添加系统消息"""
        self.dialogue_history.add_message("system", content, **metadata)

    def update_stage(self, stage: str):
        """更新当前处理阶段"""
        self.processing_history.append({
            "from_stage": self.current_stage,
            "to_stage": stage,
            "timestamp": datetime.now().isoformat()
        })
        self.current_stage = stage

    def record_error(self, error: Exception, context: str = ""):
        """记录错误"""
        self.error_count += 1
        self.last_error = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

    def get_current_stage_info(self) -> Dict[str, Any]:
        """获取当前阶段信息"""
        return {
            "current_stage": self.current_stage,
            "stage_duration": self._calculate_stage_duration(),
            "total_stages": len(self.processing_history),
            "error_count": self.error_count
        }

    def _calculate_stage_duration(self) -> float:
        """计算当前阶段持续时间（秒）"""
        if not self.processing_history:
            return 0.0

        last_transition = self.processing_history[-1]
        last_time = datetime.fromisoformat(last_transition["timestamp"])
        current_time = datetime.now()
        return (current_time - last_time).total_seconds()

    def is_processing_complete(self) -> bool:
        """判断处理是否完成"""
        return (
            self.current_stage == "completed" and
            self.structured_requirements.is_complete() and
            self.research_findings.is_comprehensive() and
            self.architecture_draft.is_complete()
        )

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return {
            "session_id": self.session_id,
            "current_stage": self.current_stage,
            "requirements_complete": self.structured_requirements.is_complete(),
            "research_comprehensive": self.research_findings.is_comprehensive(),
            "architecture_complete": self.architecture_draft.is_complete(),
            "total_messages": self.dialogue_history.total_messages,
            "error_count": self.error_count,
            "processing_time": self._calculate_total_processing_time()
        }

    def _calculate_total_processing_time(self) -> float:
        """计算总处理时间（秒）"""
        if not self.processing_history:
            return 0.0

        start_time = datetime.fromisoformat(self.dialogue_history.start_time)
        current_time = datetime.now()
        return (current_time - start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "session_id": self.session_id,
            "dialogue_history": self._dataclass_to_dict(self.dialogue_history),
            "user_intent": self._dataclass_to_dict(self.user_intent),
            "structured_requirements": self._dataclass_to_dict(self.structured_requirements),
            "research_findings": self._dataclass_to_dict(self.research_findings),
            "architecture_draft": self._dataclass_to_dict(self.architecture_draft),
            "current_stage": self.current_stage,
            "processing_history": self.processing_history,
            "error_count": self.error_count,
            "last_error": self.last_error,
            "progress_summary": self.get_progress_summary()
        }

    def _dataclass_to_dict(self, obj) -> Dict[str, Any]:
        """递归转换dataclass为字典"""
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                if hasattr(value, '__dict__'):
                    result[key] = self._dataclass_to_dict(value)
                elif isinstance(value, list):
                    result[key] = [self._dataclass_to_dict(item) if hasattr(item, '__dict__') else item for item in value]
                else:
                    result[key] = value
            return result
        return obj

    def save_to_file(self, filepath: str):
        """保存状态到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'SharedState':
        """从文件加载状态"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 这里可以实现更复杂的反序列化逻辑
        # 目前简化处理，实际使用时可能需要更完善的实现
        instance = cls()
        instance.session_id = data.get("session_id", instance.session_id)
        instance.current_stage = data.get("current_stage", "initialization")
        instance.processing_history = data.get("processing_history", [])
        instance.error_count = data.get("error_count", 0)
        instance.last_error = data.get("last_error")

        return instance


# 全局共享状态实例
shared_state = SharedState()


def get_shared_state() -> SharedState:
    """获取全局共享状态实例"""
    return shared_state


def reset_shared_state():
    """重置全局共享状态"""
    global shared_state
    shared_state = SharedState()
