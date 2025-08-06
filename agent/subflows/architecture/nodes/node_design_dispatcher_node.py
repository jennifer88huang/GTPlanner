"""
Node Design Dispatcher Node

批处理分发器节点，负责将Node设计任务分发给多个并行的NodeDesignNode实例。
在Flow层面实现批处理，而不是在单个Node内部循环处理。
"""

import time
from typing import Dict, Any, List
from pocketflow import Node


class NodeDesignDispatcherNode(Node):
    """Node设计分发器节点 - 为每个Node创建并行设计任务"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignDispatcherNode"
        self.description = "分发Node设计任务到并行处理节点"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：收集需要设计的Node列表和相关数据"""
        try:
            # 获取前面步骤的结果
            identified_nodes = shared.get("identified_nodes", [])
            flow_design = shared.get("flow_design", {})
            data_structure = shared.get("data_structure", {})
            agent_analysis = shared.get("agent_analysis", {})
            
            # 检查必需的输入
            if not identified_nodes:
                return {"error": "缺少识别的Node列表"}
            
            if not flow_design:
                return {"error": "缺少Flow设计结果"}
            
            if not data_structure:
                return {"error": "缺少数据结构设计结果"}
            
            return {
                "identified_nodes": identified_nodes,
                "flow_design": flow_design,
                "data_structure": data_structure,
                "agent_analysis": agent_analysis,
                "total_nodes": len(identified_nodes),
                "timestamp": time.time()
            }
            
        except Exception as e:
            return {"error": f"Node design dispatch preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：准备批处理任务数据"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            identified_nodes = prep_result["identified_nodes"]
            flow_design = prep_result["flow_design"]
            data_structure = prep_result["data_structure"]
            agent_analysis = prep_result["agent_analysis"]
            
            # 为每个Node准备设计任务数据
            design_tasks = []
            for i, node_info in enumerate(identified_nodes):
                task = {
                    "task_id": f"node_design_{i}",
                    "node_info": node_info,
                    "node_name": node_info.get("node_name", f"Node_{i}"),
                    "context_data": {
                        "flow_design": flow_design,
                        "data_structure": data_structure,
                        "agent_analysis": agent_analysis,
                        "all_nodes": identified_nodes
                    }
                }
                design_tasks.append(task)
            
            return {
                "design_tasks": design_tasks,
                "total_tasks": len(design_tasks),
                "dispatch_success": True
            }
            
        except Exception as e:
            return {"error": f"Node design dispatch failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：将任务数据保存到shared，供后续批处理使用"""
        try:
            if "error" in exec_res:
                shared["node_design_dispatch_error"] = exec_res["error"]
                print(f"❌ Node设计任务分发失败: {exec_res['error']}")
                return "error"
            
            # 保存设计任务到shared
            design_tasks = exec_res["design_tasks"]
            shared["node_design_tasks"] = design_tasks
            shared["node_design_batch_size"] = len(design_tasks)
            
            # 初始化批处理结果容器
            shared["node_design_results"] = {}
            shared["node_design_completed_count"] = 0
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design_dispatch",
                "status": "completed",
                "message": f"Node设计任务分发完成：{len(design_tasks)}个任务"
            })
            
            print(f"✅ Node设计任务分发完成")
            print(f"   分发任务数: {len(design_tasks)}")
            for task in design_tasks:
                print(f"   - {task['node_name']}: {task['task_id']}")
            
            return "dispatch_complete"
            
        except Exception as e:
            shared["node_design_dispatch_post_error"] = str(e)
            print(f"❌ Node设计任务分发后处理失败: {str(e)}")
            return "error"


class NodeDesignAggregatorNode(Node):
    """Node设计聚合器节点 - 收集并整合所有Node设计结果"""
    
    def __init__(self):
        super().__init__()
        self.name = "NodeDesignAggregatorNode"
        self.description = "聚合所有Node设计结果"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：检查批处理任务状态"""
        try:
            # 检查是否有设计任务
            design_tasks = shared.get("node_design_tasks", [])
            if not design_tasks:
                return {"error": "没有找到Node设计任务"}
            
            # 检查批处理结果
            design_results = shared.get("node_design_results", {})
            completed_count = shared.get("node_design_completed_count", 0)
            expected_count = len(design_tasks)
            
            return {
                "design_tasks": design_tasks,
                "design_results": design_results,
                "completed_count": completed_count,
                "expected_count": expected_count,
                "all_completed": completed_count >= expected_count
            }
            
        except Exception as e:
            return {"error": f"Node design aggregation preparation failed: {str(e)}"}
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行阶段：聚合设计结果"""
        try:
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            design_tasks = prep_result["design_tasks"]
            design_results = prep_result["design_results"]
            
            # 模拟批处理结果聚合（实际应该从并行任务中收集）
            # 这里我们简化处理，直接使用原来的NodeDesignNode逻辑
            from .node_design_node import NodeDesignNode
            
            detailed_nodes = []
            node_design_node = NodeDesignNode()
            
            print(f"🔄 开始聚合{len(design_tasks)}个Node设计任务...")
            
            for i, task in enumerate(design_tasks, 1):
                print(f"🔧 处理Node {i}/{len(design_tasks)}: {task['node_name']}")

                # 为每个Node执行设计
                # 这里简化了批处理逻辑，实际应该是并行执行的结果聚合
                try:
                    print(f"   📝 开始设计Node: {task['node_name']}")
                    start_time = time.time()

                    # 模拟单个Node的设计过程
                    node_result = self._design_single_node(node_design_node, task)

                    design_time = time.time() - start_time

                    if node_result:
                        detailed_nodes.append(node_result)
                        print(f"   ✅ Node {task['node_name']} 设计完成 (耗时: {design_time:.2f}秒)")
                        print(f"      设计类型: {node_result.get('node_type', 'Unknown')}")
                        print(f"      设计详情: {len(str(node_result.get('design_details', {})))} 字符")
                    else:
                        print(f"   ❌ Node {task['node_name']} 设计返回空结果")

                except Exception as e:
                    print(f"   ❌ Node {task['node_name']} 设计失败: {e}")
                    import traceback
                    print(f"   📋 错误详情: {traceback.format_exc()}")
                    continue
            
            return {
                "detailed_nodes": detailed_nodes,
                "aggregation_success": True,
                "processed_count": len(detailed_nodes)
            }
            
        except Exception as e:
            return {"error": f"Node design aggregation failed: {str(e)}"}
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """后处理阶段：保存聚合结果"""
        try:
            if "error" in exec_res:
                shared["node_design_aggregation_error"] = exec_res["error"]
                print(f"❌ Node设计结果聚合失败: {exec_res['error']}")
                return "error"
            
            # 保存聚合的设计结果
            detailed_nodes = exec_res["detailed_nodes"]
            shared["detailed_nodes"] = detailed_nodes
            
            # 生成文件输出
            from ..utils.file_output_util import generate_stage_file
            generate_stage_file("node_design", detailed_nodes, shared)
            
            # 更新系统消息
            if "system_messages" not in shared:
                shared["system_messages"] = []
            
            shared["system_messages"].append({
                "timestamp": time.time(),
                "stage": "node_design_aggregation",
                "status": "completed",
                "message": f"Node设计聚合完成：{len(detailed_nodes)}个节点"
            })
            
            print(f"✅ Node设计聚合完成")
            print(f"   设计节点数: {len(detailed_nodes)}")
            
            return "aggregation_complete"
            
        except Exception as e:
            shared["node_design_aggregation_post_error"] = str(e)
            print(f"❌ Node设计聚合后处理失败: {str(e)}")
            return "error"
    
    def _design_single_node(self, node_design_node: 'NodeDesignNode', task: Dict[str, Any]) -> Dict[str, Any]:
        """为单个Node执行设计（简化版本）"""
        try:
            node_info = task["node_info"]
            context_data = task["context_data"]
            node_name = task["node_name"]

            print(f"      🔍 准备设计数据...")
            print(f"         Node信息: {node_info.get('purpose', 'Unknown')}")
            print(f"         上下文数据: Flow设计({len(str(context_data['flow_design']))}字符)")

            # 构建简化的prep_result
            prep_result = {
                "flow_design": context_data["flow_design"],
                "data_structure": context_data["data_structure"],
                "identified_nodes": context_data["all_nodes"],
                "agent_analysis": context_data["agent_analysis"]
            }

            print(f"      🤖 调用LLM进行Node设计...")
            llm_start_time = time.time()

            # 调用原来的设计逻辑
            design_result = node_design_node._design_single_node_detailed(prep_result, node_info)

            llm_time = time.time() - llm_start_time
            print(f"      ✅ LLM调用完成 (耗时: {llm_time:.2f}秒)")

            if design_result:
                print(f"      📊 设计结果验证:")
                print(f"         Node名称: {design_result.get('node_name', 'Unknown')}")
                print(f"         设计详情: {'有' if design_result.get('design_details') else '无'}")
                print(f"         数据访问: {'有' if design_result.get('data_access') else '无'}")
            else:
                print(f"      ⚠️ 设计结果为空")

            return design_result

        except Exception as e:
            print(f"      ❌ 单个Node设计异常: {e}")
            import traceback
            print(f"      📋 异常详情: {traceback.format_exc()}")
            return None
