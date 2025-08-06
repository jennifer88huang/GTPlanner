"""
Requirements Analysis Flow

基于pocketflow框架的需求分析主流程，将用户对话和意图转换为结构化的项目需求。

流程架构：
NodeReq → LLMStructureNode → ValidationNode → ProcessRequirementsNode
"""

from typing import Dict, Any
from pocketflow import Flow
from agent.nodes.node_req import NodeReq
from ..nodes.llm_structure_node import LLMStructureNode
from ..nodes.validation_node import ValidationNode


class RequirementsAnalysisFlow:
    """
    需求分析主流程

    流程架构：
    NodeReq → LLMStructureNode → ValidationNode
    """

    def __init__(self):
        self.name = "RequirementsAnalysisFlow"
        self.description = "将用户对话和意图转换为结构化的项目需求"

        # 创建节点实例
        req_extract_node = NodeReq()
        llm_structure_node = LLMStructureNode()
        validation_node = ValidationNode()

        # 使用pocketflow的条件转换语法
        req_extract_node - "success" >> llm_structure_node
        llm_structure_node - "success" >> validation_node

        # 错误处理：任何节点返回"error"都结束流程
        # pocketflow会自动处理没有后续节点的情况

        # 创建流程
        self.flow = Flow(start=req_extract_node)
    
    def run(self, shared: Dict[str, Any]) -> bool:
        """
        运行需求分析流程
        
        Args:
            shared: pocketflow字典共享变量，包含：
                - dialogue_history: 对话历史
                - user_intent: 用户意图（可选）
        
        Returns:
            bool: 是否成功完成
        """
        try:
            print(f"🔄 开始需求分析流程...")
            
            # 验证输入
            if not self._validate_input(shared):
                return False
            
            # 执行pocketflow流程
            result = self.flow.run(shared)
            
            if result:
                print(f"✅ 需求分析完成")
                return True
            else:
                print(f"❌ 需求分析失败")
                return False
                
        except Exception as e:
            print(f"❌ 需求分析流程出错: {e}")
            shared["requirements_analysis_error"] = str(e)
            return False
    
    def _validate_input(self, shared: Dict[str, Any]) -> bool:
        """验证输入数据"""
        dialogue_history = shared.get("dialogue_history", "")
        user_intent = shared.get("user_intent", {})
        
        if not dialogue_history and not user_intent:
            print("❌ 缺少必要的输入数据：dialogue_history 或 user_intent")
            return False
        
        return True


def create_requirements_analysis_flow() -> Flow:
    """创建需求分析流程实例"""
    return create_requirements_analysis_flow()
