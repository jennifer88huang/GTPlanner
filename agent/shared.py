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

class SharedState:
    """系统级共享状态管理器 - 基于pocketflow字典设计"""

    def __init__(self):
        """初始化共享状态"""
        self.session_id = str(uuid.uuid4())

        # 使用字典存储所有数据，与pocketflow保持一致
        self.data = {
            "session_id": self.session_id,
            "dialogue_history": {
                "session_id": self.session_id,
                "start_time": datetime.now().isoformat(),
                "messages": [],
                "total_messages": 0,
                "last_activity": ""
            },
            "user_intent": {},
            "structured_requirements": {},
            "research_findings": {},
            "confirmation_document": "",

            # === Architecture Agent输出字段 ===
            "agent_analysis": {},
            "identified_nodes": [],
            "flow_design": {},
            "data_structure": {},
            "detailed_nodes": [],
            "agent_design_document": "",

            # === 文件生成相关 ===
            "generated_files": [],
            "output_directory": "",

            # 处理状态跟踪
            "current_stage": "initialization",
            "processing_history": [],
            "error_count": 0,
            "last_error": None,
            "system_messages": [],
            "metadata": {
                "processing_stages": [],
                "total_processing_time": 0.0,
                "last_updated": datetime.now().isoformat()
            }
        }

    def add_user_message(self, content: str, **metadata):
        """添加用户消息"""
        self._add_message("user", content, **metadata)

    def add_assistant_message(self, content: str, agent_source: str = "", **metadata):
        """添加助手消息"""
        metadata.update({"agent_source": agent_source})
        self._add_message("assistant", content, **metadata)

    def add_system_message(self, content: str, **metadata):
        """添加系统消息"""
        self._add_message("system", content, **metadata)

    def _add_message(self, role: str, content: str, message_type: str = "text", **metadata):
        """内部方法：添加消息到字典格式的对话历史"""
        message = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "message_type": message_type,
            "metadata": metadata
        }

        self.data["dialogue_history"]["messages"].append(message)
        self.data["dialogue_history"]["total_messages"] += 1
        self.data["dialogue_history"]["last_activity"] = message["timestamp"]

    def update_stage(self, stage: str):
        """更新当前处理阶段"""
        self.data["processing_history"].append({
            "from_stage": self.data["current_stage"],
            "to_stage": stage,
            "timestamp": datetime.now().isoformat()
        })
        self.data["current_stage"] = stage

    def record_error(self, error: Exception, context: str = ""):
        """记录错误"""
        self.data["error_count"] += 1
        self.data["last_error"] = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }

    def get_current_stage_info(self) -> Dict[str, Any]:
        """获取当前阶段信息"""
        return {
            "current_stage": self.data["current_stage"],
            "stage_duration": self._calculate_stage_duration(),
            "total_stages": len(self.data["processing_history"]),
            "error_count": self.data["error_count"]
        }

    def _calculate_stage_duration(self) -> float:
        """计算当前阶段持续时间（秒）"""
        if not self.data["processing_history"]:
            return 0.0

        last_transition = self.data["processing_history"][-1]
        last_time = datetime.fromisoformat(last_transition["timestamp"])
        current_time = datetime.now()
        return (current_time - last_time).total_seconds()

    def is_processing_complete(self) -> bool:
        """判断处理是否完成"""
        return (
            self.data["current_stage"] == "completed" and
            self._is_requirements_complete() and
            self._is_research_comprehensive() and
            self._is_architecture_complete()
        )

    def _is_requirements_complete(self) -> bool:
        """检查需求是否完整"""
        req = self.data.get("structured_requirements", {})
        return bool(req.get("project_overview") and req.get("functional_requirements"))

    def _is_research_comprehensive(self) -> bool:
        """检查研究是否全面"""
        research = self.data.get("research_findings", {})
        return bool(research.get("topics") and research.get("sources"))

    def _is_architecture_complete(self) -> bool:
        """检查架构是否完整"""
        arch = self.data.get("architecture_draft", {})
        return bool(arch.get("diagrams") and arch.get("components"))

    def get_progress_summary(self) -> Dict[str, Any]:
        """获取进度摘要"""
        return {
            "session_id": self.session_id,
            "current_stage": self.data["current_stage"],
            "requirements_complete": self._is_requirements_complete(),
            "research_comprehensive": self._is_research_comprehensive(),
            "architecture_complete": self._is_architecture_complete(),
            "total_messages": self.data["dialogue_history"]["total_messages"],
            "error_count": self.data["error_count"],
            "processing_time": self._calculate_total_processing_time()
        }

    def _calculate_total_processing_time(self) -> float:
        """计算总处理时间（秒）"""
        if not self.data["processing_history"]:
            return 0.0

        start_time = datetime.fromisoformat(self.data["dialogue_history"]["start_time"])
        current_time = datetime.now()
        return (current_time - start_time).total_seconds()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式 - 现在直接返回内部字典"""
        result = self.data.copy()
        result["progress_summary"] = self.get_progress_summary()
        return result

    def save_to_file(self, filepath: str):
        """保存状态到文件"""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> 'SharedState':
        """从文件加载状态"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        instance = cls()
        instance.data = data
        instance.session_id = data.get("session_id", instance.session_id)
        return instance

    # 便捷访问方法，保持API兼容性
    @property
    def dialogue_history(self):
        """获取对话历史"""
        return self.data["dialogue_history"]

    @property
    def user_intent(self):
        """获取用户意图"""
        return self.data["user_intent"]

    @property
    def structured_requirements(self):
        """获取结构化需求"""
        return self.data["structured_requirements"]

    @property
    def research_findings(self):
        """获取研究发现"""
        return self.data["research_findings"]

    @property
    def architecture_draft(self):
        """获取架构草稿"""
        return self.data["architecture_draft"]

    @property
    def current_stage(self):
        """获取当前阶段"""
        return self.data["current_stage"]


# 全局共享状态实例
shared_state = SharedState()


def get_shared_state() -> SharedState:
    """获取全局共享状态实例"""
    return shared_state


def reset_shared_state():
    """重置全局共享状态"""
    global shared_state
    shared_state = SharedState()
