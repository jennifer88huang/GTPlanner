"""
Orchestrator ReAct Flow

完全基于pocketflow的ReAct流程，参考你的demo代码设计。
主Agent作为中心调度器，通过箭头函数动态路由到各个专业Agent。
"""

from typing import Dict, Any
from pocketflow import Flow, Node, AsyncFlow, AsyncNode
from .react_orchestrator_node import ReActOrchestratorNode


class AgentWrapperNode(AsyncNode):
    """异步Agent包装器节点，将Agent Flow包装成异步pocketflow Node"""

    def __init__(self, agent_type: str, agent_flow_class):
        super().__init__()
        self.agent_type = agent_type
        self.agent_flow_class = agent_flow_class
        self.name = f"{agent_type}_wrapper"
        self.description = f"异步包装器节点：{agent_type}"

    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """异步准备Agent执行"""
        return {"agent_type": self.agent_type, "shared": shared}

    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """异步执行Agent"""
        try:
            shared = prep_result["shared"]
            print(f"🚀 异步执行{self.agent_type} Agent...")

            # 创建并异步运行Agent
            agent = self.agent_flow_class()

            # 检查Agent是否支持异步
            if hasattr(agent, 'run_async'):
                result = await agent.run_async(shared)
            else:
                # 如果Agent不支持异步，在线程池中运行
                import asyncio
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    result = await asyncio.get_event_loop().run_in_executor(
                        executor, agent.run, shared
                    )

            return {
                "success": True,
                "agent_type": self.agent_type,
                "result": result
            }
        except Exception as e:
            print(f"❌ {self.agent_type} Agent异步执行失败: {e}")
            return {"error": str(e)}

    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Agent执行完成后返回主Agent"""
        if "error" in exec_res:
            shared[f"{self.agent_type}_error"] = exec_res["error"]
            print(f"❌ {self.agent_type} Agent失败")
            return "main_agent"  # 即使失败也返回主Agent继续决策

        print(f"✅ {self.agent_type} Agent完成")
        return "main_agent"  # 返回主Agent进行下一步决策


class OrchestratorReActFlow:
    """
    ReAct模式主控制器流程

    参考demo架构：
    主Agent → 动态选择子Agent → 子Agent完成后返回主Agent → 继续决策
    """

    def __init__(self):
        self.name = "OrchestratorReActFlow"
        self.description = "基于pocketflow的ReAct智能主控制器"

        # 创建主Agent节点
        main_agent = ReActOrchestratorNode()

        # 导入所有专业Agent
        from agent.subflows.requirements_analysis import RequirementsAnalysisFlow
        from agent.subflows.research import ResearchFlow
        from agent.subflows.short_planning.flows.short_planning_flow import ShortPlanningFlow
        from agent.subflows.architecture import ArchitectureFlow

        # 创建Agent节点包装器
        requirements_agent = AgentWrapperNode("requirements_analysis", RequirementsAnalysisFlow)
        short_planning_agent = AgentWrapperNode("short_planning", ShortPlanningFlow)
        research_agent = AgentWrapperNode("research", ResearchFlow)
        architecture_agent = AgentWrapperNode("architecture_design", ArchitectureFlow)

        # 主Agent的动态路由连接（参考demo的箭头函数设计）
        main_agent - "requirements_analysis" >> requirements_agent
        main_agent - "short_planning" >> short_planning_agent
        main_agent - "research" >> research_agent
        main_agent - "architecture_design" >> architecture_agent

        # 结束条件不需要显式连接，pocketflow会自动处理

        # 所有子Agent完成后都返回主Agent进行下一步决策（参考demo设计）
        requirements_agent - "main_agent" >> main_agent
        short_planning_agent - "main_agent" >> main_agent
        research_agent - "main_agent" >> main_agent
        architecture_agent - "main_agent" >> main_agent

        # 创建异步流程，从主Agent开始
        self.flow = AsyncFlow(start=main_agent)
    
    async def run_async(self, shared: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """
        异步运行ReAct主控制器流程（使用pocketflow原生异步能力）

        Args:
            shared: 共享状态字典
            stream_callback: 可选的流式回调函数

        Returns:
            处理结果
        """
        try:
            print(f"🚀 启动异步pocketflow ReAct主控制器...")

            # 初始化ReAct状态
            if "react_cycle_count" not in shared:
                shared["react_cycle_count"] = 0

            # 如果有流式回调，保存到shared中供节点使用
            if stream_callback:
                shared["_stream_callback"] = stream_callback

            # 直接使用pocketflow异步执行流程
            result = await self.flow._run_async(shared)

            # 清理回调
            if "_stream_callback" in shared:
                del shared["_stream_callback"]

            # 分析最终结果
            react_cycles = shared.get("react_cycle_count", 0)

            print(f"🏁 异步pocketflow ReAct流程完成")
            return {
                "flow_result": {
                    "cycles_completed": react_cycles,
                    "final_action": result or "wait_for_user"
                },
                "react_cycles": react_cycles,
                "success": result != "error"
            }

        except Exception as e:
            print(f"❌ 异步pocketflow ReAct主控制器执行失败: {e}")
            react_cycles = shared.get("react_cycle_count", 0)
            return {
                "flow_result": {
                    "cycles_completed": react_cycles,
                    "final_action": "error"
                },
                "react_cycles": react_cycles,
                "success": False,
                "error": str(e)
            }


    
    async def run_with_stream(self, shared: Dict[str, Any], stream_callback=None) -> Dict[str, Any]:
        """
        异步运行ReAct主控制器流程（支持流式回调）

        Args:
            shared: 共享状态字典
            stream_callback: 流式回调函数

        Returns:
            处理结果
        """
        try:
            print(f"🚀 启动流式异步pocketflow ReAct主控制器...")

            # 初始化ReAct状态
            if "react_cycle_count" not in shared:
                shared["react_cycle_count"] = 0

            # 保存流式回调到shared中，供节点使用
            if stream_callback:
                shared["_stream_callback"] = stream_callback

            # 使用异步pocketflow执行流程
            result = await self.flow._run_async(shared)

            # 清理回调
            if "_stream_callback" in shared:
                del shared["_stream_callback"]

            # 分析最终结果
            react_cycles = shared.get("react_cycle_count", 0)

            print(f"🏁 流式异步pocketflow ReAct流程完成")
            return {
                "flow_result": {
                    "cycles_completed": react_cycles,
                    "final_action": result or "wait_for_user"
                },
                "react_cycles": react_cycles,
                "success": result != "error"
            }

        except Exception as e:
            print(f"❌ 流式异步pocketflow ReAct主控制器执行失败: {e}")
            react_cycles = shared.get("react_cycle_count", 0)
            return {
                "flow_result": {
                    "cycles_completed": react_cycles,
                    "final_action": "error"
                },
                "react_cycles": react_cycles,
                "success": False,
                "error": str(e)
            }


def create_orchestrator_react_flow() -> OrchestratorReActFlow:
    """创建ReAct主控制器流程实例"""
    return OrchestratorReActFlow()
