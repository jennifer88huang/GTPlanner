"""
Research Agent 子流程包

完整的Research Agent实现，包含：
- 节点定义 (nodes/)
- 流程定义 (flows/)
- 工具类 (utils/)
- 测试文件 (test/)
"""


from .flows import ResearchFlow, create_keyword_research_subflow
from .nodes import LLMAnalysisNode, ResultAssemblyNode
from .nodes.process_research_node import ProcessResearch  # 单独导入避免循环
from .utils import ResearchAggregator

__all__ = [
    'ProcessResearch',
    'ResearchFlow',
    'create_keyword_research_subflow',
    'LLMAnalysisNode',
    'ResultAssemblyNode',
    'ResearchAggregator'
]
