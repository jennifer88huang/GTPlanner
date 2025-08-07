"""
Short Planning Flow

协调简化的Short Planning Agent的所有节点，实现功能导向的短规划流程。

流程架构：
FunctionAnalysisNode → StepGenerationNode → ConfirmationFormattingNode
"""

from pocketflow import AsyncFlow
from ..nodes.function_analysis_node import FunctionAnalysisNode
from ..nodes.step_generation_node import StepGenerationNode
from ..nodes.confirmation_formatting_node import ConfirmationFormattingNode


class ShortPlanningFlow:
    """
    简化的短规划流程
    
    流程架构：
    FunctionAnalysisNode → StepGenerationNode → ConfirmationFormattingNode
    """
    
    def __init__(self):
        self.name = "ShortPlanningFlow"
        self.description = "将结构化需求转换为功能导向的确认文档"
        
        # 创建节点实例
        function_analysis_node = FunctionAnalysisNode()
        step_generation_node = StepGenerationNode()
        confirmation_formatting_node = ConfirmationFormattingNode()
        
        # 使用pocketflow的条件转换语法
        function_analysis_node - "success" >> step_generation_node
        step_generation_node - "success" >> confirmation_formatting_node
        
        # 错误处理：任何节点返回"error"都结束流程
        # pocketflow会自动处理没有后续节点的情况
        
        # 创建异步流程（因为包含异步节点）
        self.flow = AsyncFlow(start=function_analysis_node)
    
    async def run_async(self, shared: dict) -> str:
        """
        异步运行短规划流程

        Args:
            shared: pocketflow字典共享变量

        Returns:
            流程执行结果
        """
        try:
            print("🚀 启动异步简化短规划流程...")

            # 验证输入数据
            if not self._validate_input(shared):
                raise ValueError("输入数据验证失败")

            # 执行异步pocketflow流程
            result = await self.flow._run_async(shared)

            print("✅ 异步短规划流程执行完成")
            return result

        except Exception as e:
            print(f"❌ 异步短规划流程执行失败: {e}")
            # 在共享状态中记录错误
            shared["short_planning_flow_error"] = str(e)
            raise e

    def run(self, shared: dict) -> str:
        """
        同步运行短规划流程（兼容性）
        """
        import asyncio
        return asyncio.run(self.run_async(shared))
    
    def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""
        
        # 检查必需的结构化需求
        structured_requirements = shared.get("structured_requirements", {})
        if not structured_requirements:
            print("❌ 缺少结构化需求数据")
            return False
        
        # 检查项目概览
        project_overview = structured_requirements.get("project_overview", {})
        if not project_overview.get("title"):
            print("⚠️ 项目标题缺失，可能影响规划质量")
        
        # 检查功能需求
        functional_requirements = structured_requirements.get("functional_requirements", {})
        core_features = functional_requirements.get("core_features", [])
        if not core_features:
            print("⚠️ 核心功能列表为空，将基于项目描述推断功能模块")
        
        print("✅ 输入数据验证通过")
        return True
