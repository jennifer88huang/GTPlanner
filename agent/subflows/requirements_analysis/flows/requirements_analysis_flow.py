"""
Requirements Analysis Flow

基于pocketflow框架的需求分析主流程，将用户对话和意图转换为结构化的项目需求。

极简化流程架构：
UnifiedRequirementsNode (单节点完成所有工作)

通过单一节点完成需求分析，最大化效率。
"""

from typing import Dict, Any
from pocketflow import AsyncFlow
from ..nodes.unified_requirements_node import UnifiedRequirementsNode


class RequirementsAnalysisFlow:
    """
    需求分析主流程 - 极简版本

    流程架构：
    UnifiedRequirementsNode (单节点)

    优化说明：
    - 将原来的NodeReq + LLMStructureNode + ValidationNode 简化为单个UnifiedRequirementsNode
    - 减少LLM调用次数从2次降为1次
    - 移除复杂的验证逻辑，LLM本身已足够可靠
    - 保持相同的输出质量和接口兼容性
    """

    def __init__(self):
        self.name = "RequirementsAnalysisFlow"
        self.description = "将用户对话和意图转换为结构化的项目需求（极简版本）"

        # 创建节点实例 - 只使用统一的需求分析节点
        unified_requirements_node = UnifiedRequirementsNode()

        # 单节点流程，无需连接其他节点
        # 错误处理：节点返回"error"会自动结束流程

        # 创建异步流程
        self.flow = AsyncFlow(start=unified_requirements_node)

    async def run_async(self, shared: Dict[str, Any]) -> bool:
        """
        运行需求分析流程（极简版本）

        Args:
            shared: pocketflow字典共享变量，包含：
                - dialogue_history: 对话历史
                - user_intent: 用户意图（可选）

        Returns:
            bool: 是否成功完成
        """
        try:

            # 验证输入
            if not self._validate_input(shared):
                return False

            # 执行pocketflow异步流程
            result = await self.flow.run_async(shared)

            if result:
                # 输出优化效果
                if "structured_requirements" in shared:
                    req = shared["structured_requirements"]
                    features_count = len(req.get("functional_requirements", {}).get("core_features", []))
                    confidence = req.get("analysis_metadata", {}).get("confidence_score", 0)
                    project_title = req.get("project_overview", {}).get("title", "未定义")
                    
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


def create_requirements_analysis_flow() -> RequirementsAnalysisFlow:
    """创建需求分析流程实例"""
    return RequirementsAnalysisFlow()
