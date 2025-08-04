"""
GTPlanner 数据模型模块

本模块包含GTPlanner系统中使用的所有数据结构定义。
将复杂的数据模型拆分为独立的模块，便于维护和扩展。

模块列表：
- dialogue: 对话相关数据结构
- user_intent: 用户意图分析数据结构
- requirements: 需求分析数据结构
- research: 研究调研数据结构
- architecture: 架构设计数据结构
"""

from .dialogue import DialogueHistory, DialogueMessage
from .user_intent import UserIntent
from .requirements import (
    StructuredRequirements, 
    ProjectOverview, 
    FunctionalRequirements, 
    NonFunctionalRequirements,
    FeatureRequirement,
    WorkflowRequirement
)
from .research import (
    ResearchFindings,
    ResearchTopic,
    ResearchSource
)
from .architecture import (
    ArchitectureDraft,
    MermaidDiagram,
    NodeDefinition,
    SharedVariable
)

__all__ = [
    # 对话模型
    'DialogueHistory',
    'DialogueMessage',
    
    # 用户意图模型
    'UserIntent',
    
    # 需求模型
    'StructuredRequirements',
    'ProjectOverview',
    'FunctionalRequirements', 
    'NonFunctionalRequirements',
    'FeatureRequirement',
    'WorkflowRequirement',
    
    # 研究模型
    'ResearchFindings',
    'ResearchTopic',
    'ResearchSource',
    
    # 架构模型
    'ArchitectureDraft',
    'MermaidDiagram',
    'NodeDefinition',
    'SharedVariable'
]
