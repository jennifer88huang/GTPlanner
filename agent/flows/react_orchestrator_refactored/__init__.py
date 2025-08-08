"""
重构后的ReAct Orchestrator模块

提供模块化的ReAct主控制器实现，将原来的单一大类拆分为多个专门的组件。

主要组件：
- ReActOrchestratorRefactored: 主控制器类
- MessageBuilder: 消息构建器
- ToolExecutor: 工具执行器
- StateManager: 状态管理器
- DecisionEngine: 决策引擎
- StreamHandler: 流式处理器
- constants: 常量定义

优势：
1. 单一职责原则：每个组件只负责特定功能
2. 降低复杂度：将944行代码拆分为多个小文件
3. 提高可维护性：修改某个功能只需要修改对应组件
4. 增强可测试性：每个组件可以独立测试
5. 便于扩展：新功能可以通过新组件或扩展现有组件实现
"""

from .react_orchestrator_refactored import ReActOrchestratorRefactored
from .message_builder import MessageBuilder
from .tool_executor import ToolExecutor
from .state_manager import StateManager
from .stream_handler import StreamHandler
from . import constants

__all__ = [
    "ReActOrchestratorRefactored",
    "MessageBuilder", 
    "ToolExecutor",
    "StateManager",
    "StreamHandler",
    "constants"
]

# 版本信息
__version__ = "1.0.0"
__author__ = "GTPlanner Team"
__description__ = "Refactored ReAct Orchestrator with modular design"
