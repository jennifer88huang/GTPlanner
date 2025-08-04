"""
架构设计数据模型

定义架构设计相关的数据结构。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class MermaidDiagram:
    """Mermaid图表"""
    diagram_code: str = ""
    diagram_type: str = "flowchart"
    complexity_level: str = "medium"
    node_count: int = 0
    connection_count: int = 0
    validation_status: str = "pending"

    def update_metrics(self):
        """更新图表指标"""
        if self.diagram_code:
            # 简单的节点和连接计数
            lines = self.diagram_code.split('\n')
            self.node_count = len([line for line in lines if '-->' not in line and line.strip()])
            self.connection_count = len([line for line in lines if '-->' in line])

    def is_valid(self) -> bool:
        """判断图表是否有效"""
        return self.validation_status == "valid" and bool(self.diagram_code)

    def is_complex(self) -> bool:
        """判断是否为复杂图表"""
        return self.complexity_level == "complex" or self.node_count > 10


@dataclass
class NodeDefinition:
    """节点定义"""
    node_id: str
    node_name: str
    node_type: str  # "input" | "process" | "output" | "decision"
    description: str
    input_variables: List[str] = field(default_factory=list)
    output_variables: List[str] = field(default_factory=list)
    processing_logic: str = ""
    error_handling: str = ""
    performance_requirements: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后处理"""
        if not self.node_id:
            self.node_id = str(uuid.uuid4())[:8]

    def add_input_variable(self, variable: str):
        """添加输入变量"""
        if variable and variable not in self.input_variables:
            self.input_variables.append(variable)

    def add_output_variable(self, variable: str):
        """添加输出变量"""
        if variable and variable not in self.output_variables:
            self.output_variables.append(variable)

    def add_dependency(self, dependency: str):
        """添加依赖"""
        if dependency and dependency not in self.dependencies:
            self.dependencies.append(dependency)

    def is_input_node(self) -> bool:
        """判断是否为输入节点"""
        return self.node_type == "input"

    def is_output_node(self) -> bool:
        """判断是否为输出节点"""
        return self.node_type == "output"

    def has_dependencies(self) -> bool:
        """判断是否有依赖"""
        return len(self.dependencies) > 0


@dataclass
class SharedVariable:
    """共享变量定义"""
    variable_id: str
    variable_name: str
    data_type: str
    description: str
    scope: str  # "global" | "local" | "session"
    default_value: Any = None
    validation_rules: List[str] = field(default_factory=list)
    access_pattern: str = "read-write"  # "read-only" | "write-only" | "read-write"
    lifecycle: str = "session"  # "session" | "request" | "persistent"
    security_level: str = "internal"  # "public" | "internal" | "confidential"

    def __post_init__(self):
        """初始化后处理"""
        if not self.variable_id:
            self.variable_id = str(uuid.uuid4())[:8]

    def add_validation_rule(self, rule: str):
        """添加验证规则"""
        if rule and rule not in self.validation_rules:
            self.validation_rules.append(rule)

    def is_global(self) -> bool:
        """判断是否为全局变量"""
        return self.scope == "global"

    def is_read_only(self) -> bool:
        """判断是否为只读变量"""
        return self.access_pattern == "read-only"

    def is_confidential(self) -> bool:
        """判断是否为机密变量"""
        return self.security_level == "confidential"

    def is_persistent(self) -> bool:
        """判断是否为持久化变量"""
        return self.lifecycle == "persistent"


@dataclass
class ArchitectureDraft:
    """架构设计草稿"""
    mermaid_diagram: MermaidDiagram = field(default_factory=MermaidDiagram)
    nodes_definition: List[NodeDefinition] = field(default_factory=list)
    shared_variables: List[SharedVariable] = field(default_factory=list)
    design_metadata: Dict[str, Any] = field(default_factory=dict)

    def add_node(self, name: str, node_type: str, description: str) -> NodeDefinition:
        """添加节点定义"""
        node = NodeDefinition(
            node_id="",  # 将在__post_init__中生成
            node_name=name,
            node_type=node_type,
            description=description
        )
        self.nodes_definition.append(node)
        return node

    def add_variable(self, name: str, data_type: str, description: str, scope: str = "session") -> SharedVariable:
        """添加共享变量"""
        variable = SharedVariable(
            variable_id="",  # 将在__post_init__中生成
            variable_name=name,
            data_type=data_type,
            description=description,
            scope=scope
        )
        self.shared_variables.append(variable)
        return variable

    def get_node_by_id(self, node_id: str) -> NodeDefinition:
        """根据ID获取节点"""
        for node in self.nodes_definition:
            if node.node_id == node_id:
                return node
        return None

    def get_node_by_name(self, name: str) -> NodeDefinition:
        """根据名称获取节点"""
        for node in self.nodes_definition:
            if node.node_name == name:
                return node
        return None

    def get_variable_by_name(self, name: str) -> SharedVariable:
        """根据名称获取变量"""
        for variable in self.shared_variables:
            if variable.variable_name == name:
                return variable
        return None

    def get_input_nodes(self) -> List[NodeDefinition]:
        """获取输入节点"""
        return [node for node in self.nodes_definition if node.is_input_node()]

    def get_output_nodes(self) -> List[NodeDefinition]:
        """获取输出节点"""
        return [node for node in self.nodes_definition if node.is_output_node()]

    def get_global_variables(self) -> List[SharedVariable]:
        """获取全局变量"""
        return [var for var in self.shared_variables if var.is_global()]

    def get_confidential_variables(self) -> List[SharedVariable]:
        """获取机密变量"""
        return [var for var in self.shared_variables if var.is_confidential()]

    def update_diagram_code(self, code: str):
        """更新图表代码"""
        self.mermaid_diagram.diagram_code = code
        self.mermaid_diagram.update_metrics()

    def validate_architecture(self) -> Dict[str, Any]:
        """验证架构完整性"""
        validation_result = {
            "is_valid": True,
            "issues": [],
            "warnings": []
        }

        # 检查是否有节点定义
        if not self.nodes_definition:
            validation_result["is_valid"] = False
            validation_result["issues"].append("No nodes defined")

        # 检查是否有Mermaid图
        if not self.mermaid_diagram.diagram_code:
            validation_result["warnings"].append("No Mermaid diagram code")

        # 检查节点依赖是否存在
        node_names = {node.node_name for node in self.nodes_definition}
        for node in self.nodes_definition:
            for dep in node.dependencies:
                if dep not in node_names:
                    validation_result["warnings"].append(f"Node '{node.node_name}' depends on undefined node '{dep}'")

        return validation_result

    def get_complexity_score(self) -> float:
        """获取架构复杂度评分"""
        score = 0.0
        
        # 基于节点数量
        score += len(self.nodes_definition) * 0.1
        
        # 基于变量数量
        score += len(self.shared_variables) * 0.05
        
        # 基于依赖关系
        total_dependencies = sum(len(node.dependencies) for node in self.nodes_definition)
        score += total_dependencies * 0.02
        
        # 基于图表复杂度
        if self.mermaid_diagram.is_complex():
            score += 0.3
        
        return min(score, 1.0)  # 限制在0-1之间

    def is_complete(self) -> bool:
        """判断架构是否完整"""
        return (
            len(self.nodes_definition) > 0 and
            len(self.shared_variables) > 0 and
            bool(self.mermaid_diagram.diagram_code) and
            self.validate_architecture()["is_valid"]
        )
