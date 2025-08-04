"""
需求分析数据模型

定义需求分析相关的数据结构。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class ProjectOverview:
    """项目概览"""
    title: str = ""
    description: str = ""
    scope: str = ""
    objectives: List[str] = field(default_factory=list)
    success_criteria: List[str] = field(default_factory=list)

    def add_objective(self, objective: str):
        """添加项目目标"""
        if objective and objective not in self.objectives:
            self.objectives.append(objective)

    def add_success_criterion(self, criterion: str):
        """添加成功标准"""
        if criterion and criterion not in self.success_criteria:
            self.success_criteria.append(criterion)


@dataclass
class FeatureRequirement:
    """功能需求"""
    feature_id: str
    name: str
    description: str
    priority: str  # "high" | "medium" | "low"
    user_stories: List[str] = field(default_factory=list)
    acceptance_criteria: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.feature_id:
            self.feature_id = str(uuid.uuid4())[:8]

    def add_user_story(self, story: str):
        """添加用户故事"""
        if story and story not in self.user_stories:
            self.user_stories.append(story)

    def add_acceptance_criterion(self, criterion: str):
        """添加验收标准"""
        if criterion and criterion not in self.acceptance_criteria:
            self.acceptance_criteria.append(criterion)

    def is_high_priority(self) -> bool:
        """判断是否为高优先级"""
        return self.priority == "high"


@dataclass
class WorkflowRequirement:
    """工作流需求"""
    workflow_id: str
    name: str
    steps: List[str] = field(default_factory=list)
    actors: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)

    def __post_init__(self):
        """初始化后处理"""
        if not self.workflow_id:
            self.workflow_id = str(uuid.uuid4())[:8]

    def add_step(self, step: str):
        """添加工作流步骤"""
        if step and step not in self.steps:
            self.steps.append(step)

    def add_actor(self, actor: str):
        """添加参与者"""
        if actor and actor not in self.actors:
            self.actors.append(actor)

    def add_trigger(self, trigger: str):
        """添加触发条件"""
        if trigger and trigger not in self.triggers:
            self.triggers.append(trigger)


@dataclass
class FunctionalRequirements:
    """功能性需求"""
    core_features: List[FeatureRequirement] = field(default_factory=list)
    workflows: List[WorkflowRequirement] = field(default_factory=list)

    def add_feature(self, name: str, description: str, priority: str = "medium") -> FeatureRequirement:
        """添加功能需求"""
        feature = FeatureRequirement(
            feature_id="",  # 将在__post_init__中生成
            name=name,
            description=description,
            priority=priority
        )
        self.core_features.append(feature)
        return feature

    def add_workflow(self, name: str) -> WorkflowRequirement:
        """添加工作流需求"""
        workflow = WorkflowRequirement(
            workflow_id="",  # 将在__post_init__中生成
            name=name
        )
        self.workflows.append(workflow)
        return workflow

    def get_high_priority_features(self) -> List[FeatureRequirement]:
        """获取高优先级功能"""
        return [f for f in self.core_features if f.is_high_priority()]


@dataclass
class NonFunctionalRequirements:
    """非功能性需求"""
    performance: Dict[str, str] = field(default_factory=dict)
    security: Dict[str, List[str]] = field(default_factory=dict)
    usability: Dict[str, List[str]] = field(default_factory=dict)

    def add_performance_requirement(self, key: str, value: str):
        """添加性能需求"""
        self.performance[key] = value

    def add_security_requirement(self, category: str, requirement: str):
        """添加安全需求"""
        if category not in self.security:
            self.security[category] = []
        if requirement not in self.security[category]:
            self.security[category].append(requirement)

    def add_usability_requirement(self, category: str, requirement: str):
        """添加可用性需求"""
        if category not in self.usability:
            self.usability[category] = []
        if requirement not in self.usability[category]:
            self.usability[category].append(requirement)


@dataclass
class StructuredRequirements:
    """结构化需求"""
    project_overview: ProjectOverview = field(default_factory=ProjectOverview)
    functional_requirements: FunctionalRequirements = field(default_factory=FunctionalRequirements)
    non_functional_requirements: NonFunctionalRequirements = field(default_factory=NonFunctionalRequirements)
    constraints: Dict[str, List[str]] = field(default_factory=dict)
    analysis_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_constraint(self, category: str, constraint: str):
        """添加约束条件"""
        if category not in self.constraints:
            self.constraints[category] = []
        if constraint not in self.constraints[category]:
            self.constraints[category].append(constraint)

    def get_total_features_count(self) -> int:
        """获取功能总数"""
        return len(self.functional_requirements.core_features)

    def get_total_workflows_count(self) -> int:
        """获取工作流总数"""
        return len(self.functional_requirements.workflows)

    def is_complete(self) -> bool:
        """判断需求是否完整"""
        return (
            bool(self.project_overview.title) and
            bool(self.project_overview.description) and
            len(self.functional_requirements.core_features) > 0
        )
