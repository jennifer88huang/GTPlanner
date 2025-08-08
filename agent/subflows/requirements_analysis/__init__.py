"""
Requirements Analysis Agent - 优化版本

基于pocketflow框架实现的需求分析专业Agent，负责将用户对话和意图转换为结构化的项目需求。

优化说明：
- 使用单一的UnifiedRequirementsNode替代原来的多个节点
- 减少LLM调用次数，提高效率
- 简化流程架构，降低维护成本
"""

from .flows.requirements_analysis_flow import RequirementsAnalysisFlow
from .nodes.process_requirements_node import ProcessRequirementsNode
from .nodes.unified_requirements_node import UnifiedRequirementsNode

__all__ = [
    'RequirementsAnalysisFlow',
    'ProcessRequirementsNode',
    'UnifiedRequirementsNode'
]
