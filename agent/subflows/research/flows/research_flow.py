"""
Research Agent主流程

简化版本：使用pocketflow异步节点序列，不使用复杂的并发处理
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.llm_analysis_node import LLMAnalysisNode
from ..nodes.result_assembly_node import ResultAssemblyNode


@trace_flow(flow_name="ResearchFlow")
class TracedResearchFlow(AsyncFlow):
    """带有tracing的研究调研流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        print("🔄 启动研究调研流程...")
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "flow_id": "research_flow",
            "start_time": shared["flow_start_time"]
        }

    async def post_async(self, shared, prep_result, exec_result):
        """流程级后处理"""
        flow_duration = __import__('asyncio').get_event_loop().time() - prep_result["start_time"]

        shared["flow_metadata"] = {
            "flow_id": prep_result["flow_id"],
            "duration": flow_duration,
            "status": "completed"
        }

        print(f"✅ 研究调研流程完成，耗时: {flow_duration:.2f}秒")
        return exec_result


class ResearchFlow:
    """研究调研流程 - 简化异步版本"""
    
    def __init__(self):
        self.flow = self._create_flow()

    def _create_flow(self):
        """创建简化的研究流程"""
        # 创建节点
        analysis_node = LLMAnalysisNode()
        assembly_node = ResultAssemblyNode()
        
        # 设置节点名称以用于事件路由
        analysis_node.name = "llm_analysis"
        assembly_node.name = "result_assembly"
        
        # 设置节点连接（使用来源节点的事件字符串）
        analysis_node - "analysis_complete" >> assembly_node
        
        # 创建带tracing的异步流程
        flow = TracedResearchFlow()
        flow.start_node = analysis_node
        return flow

    async def run_async(self, shared: dict) -> bool:
        """
        异步运行研究调研流程
        
        Args:
            shared: 共享状态字典
            
        Returns:
            bool: 执行是否成功
        """
        try:
            print("🔄 启动研究调研流程...")
            
            # 从共享状态获取结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            if not structured_requirements:
                print("❌ 缺少结构化需求数据")
                return False
            
            # 提取项目信息
            project_overview = structured_requirements.get("project_overview", {})
            project_title = project_overview.get("title", "项目")
            project_description = project_overview.get("description", "")
            
            # 准备分析需求
            shared["analysis_requirements"] = f"针对{project_title}项目进行技术调研，项目描述：{project_description}"
            shared["research_keywords"] = [
                f"{project_title} 技术方案",
                f"{project_title} 架构设计",
                "最佳实践",
                "技术选型"
            ]
            shared["current_keyword"] = f"{project_title} 技术调研"

            # 提供模拟的URL内容，因为我们跳过了搜索和URL解析步骤
            shared["url_content"] = f"""
# {project_title} 技术调研资料

## 项目概述
{project_description}

## 技术要求
基于项目需求，需要进行以下方面的技术调研：
1. 技术架构选择
2. 开发框架对比
3. 数据库方案
4. 部署策略
5. 性能优化方案

## 调研重点
- 技术可行性分析
- 成本效益评估
- 风险评估
- 最佳实践总结
"""
            
            # 执行异步流程
            result = await self.flow.run_async(shared)
            
            if result:
                print("✅ 研究调研流程完成")
                return True
            else:
                print("❌ 研究调研流程失败")
                return False
                
        except Exception as e:
            print(f"❌ 研究调研流程失败: {e}")
            shared["research_error"] = str(e)
            return False
