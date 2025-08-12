"""
Architecture Flow - 重构版本

环环相扣的架构设计流程，确保设计的一致性和连贯性。

流程：
1. Agent需求分析 → 确定Agent类型和功能
2. Node识别 → 确定需要的所有Node
3. Flow编排 → 基于Node列表设计Flow
4. 数据结构设计 → 基于Flow确定shared结构
5. Node详细设计 → 基于shared结构设计Node实现
6. 文档生成 → 整合所有设计结果
"""

from pocketflow import AsyncFlow
from pocketflow_tracing import trace_flow
from ..nodes.agent_requirements_analysis_node import AgentRequirementsAnalysisNode
from ..nodes.node_identification_node import NodeIdentificationNode
from ..nodes.flow_design_node import FlowDesignNode
from ..nodes.data_structure_design_node import DataStructureDesignNode
from ..nodes.document_generation_node import DocumentGenerationNode
from ..nodes.node_design_dispatcher_node import NodeDesignDispatcherNode, NodeDesignAggregatorNode


@trace_flow(flow_name="ArchitectureFlow")
class TracedArchitectureFlow(AsyncFlow):
    """带有tracing的架构设计流程"""

    async def prep_async(self, shared):
        """流程级准备"""
        print("🏗️ 启动架构设计流程...")
        shared["flow_start_time"] = __import__('asyncio').get_event_loop().time()

        return {
            "flow_id": "architecture_flow",
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

        print(f"✅ 架构设计流程完成，耗时: {flow_duration:.2f}秒")
        return exec_result


def create_architecture_flow():
    """
    创建完整的Architecture Agent流程，支持批处理。

    流程设计：
    1. Agent需求分析 -> 2. Node识别 -> 3. Flow设计 -> 4. 数据结构设计
    5. Node详细设计（批处理） -> 6. 文档生成

    Node详细设计阶段使用批处理，为每个识别出的Node并行创建设计实例。

    Returns:
        Flow: 完整的架构设计流程
    """
    # 创建节点实例
    agent_analysis = AgentRequirementsAnalysisNode()
    node_identification = NodeIdentificationNode()
    flow_design = FlowDesignNode()
    data_structure = DataStructureDesignNode()

    # Node设计阶段 - 批处理控制节点
    node_design_dispatcher = NodeDesignDispatcherNode()
    node_design_aggregator = NodeDesignAggregatorNode()

    # 文档生成
    document_generation = DocumentGenerationNode()

    # 连接节点 - 环环相扣的设计流程
    agent_analysis - "analysis_complete" >> node_identification
    node_identification - "nodes_identified" >> flow_design
    flow_design - "flow_designed" >> data_structure
    data_structure - "data_structure_complete" >> node_design_dispatcher

    # 批处理：分发器会为每个Node创建设计任务，然后聚合器收集结果
    node_design_dispatcher - "dispatch_complete" >> node_design_aggregator
    node_design_aggregator - "aggregation_complete" >> document_generation

    # 创建并返回带tracing的AsyncFlow，从Agent需求分析开始
    flow = TracedArchitectureFlow()
    flow.start_node = agent_analysis
    return flow


class ArchitectureFlow:
    """
    架构设计流程包装器 - 兼容现有接口
    """

    def __init__(self):
        self.name = "ArchitectureFlow"
        self.description = "环环相扣的Agent设计流程"
        self.flow = create_architecture_flow()
    
    async def run_async(self, shared: dict) -> str:
        """
        异步运行架构设计流程

        Args:
            shared: pocketflow字典共享变量

        Returns:
            流程执行结果
        """
        try:
            print("🚀 启动Agent设计文档生成流程...")

            # 验证输入数据
            if not self._validate_input(shared):
                raise ValueError("输入数据验证失败")

            # 执行pocketflow异步流程
            result = await self.flow.run_async(shared)

            print("✅ Agent设计文档生成流程执行完成")
            return result

        except Exception as e:
            print(f"❌ Agent设计流程执行失败: {e}")
            # 在共享状态中记录错误
            shared["architecture_flow_error"] = str(e)
            raise e
    
    def _validate_input(self, shared: dict) -> bool:
        """验证输入数据"""
        try:
            # 检查必需的输入
            if "structured_requirements" not in shared:
                print("❌ 缺少必需输入: structured_requirements")
                return False
            
            # 检查结构化需求的完整性
            structured_requirements = shared["structured_requirements"]
            if not isinstance(structured_requirements, dict):
                print("❌ structured_requirements 必须是字典类型")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ 输入数据验证失败: {str(e)}")
            return False
