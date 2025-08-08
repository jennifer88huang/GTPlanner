"""
Process Short Planning Node

Short Planning Agent的主节点，协调整个简化的短规划流程。
将结构化需求转换为功能导向的确认文档。
"""

import time
from typing import Dict, Any
from pocketflow import AsyncNode


class ProcessShortPlanningNode(AsyncNode):
    """短规划处理主节点 - 协调简化的短规划流程"""
    
    def __init__(self):
        super().__init__()
        self.name = "ProcessShortPlanningNode"
        self.description = "协调短规划流程，生成功能导向的确认文档"
    
    async def prep_async(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备阶段：验证输入数据"""
        try:
            # 检查结构化需求
            structured_requirements = shared.get("structured_requirements", {})
            if not structured_requirements:
                return {"error": "缺少必要的输入数据：structured_requirements 为空"}
            
            # 检查对话历史（可选）
            dialogue_history = shared.get("dialogue_history", {})
            
            return {
                "structured_requirements": structured_requirements,
                "dialogue_history": dialogue_history,
                "processing_start_time": time.time()
            }
            
        except Exception as e:
            return {"error": f"Short planning preparation failed: {str(e)}"}
    
    async def exec_async(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行短规划流程"""
        try:
            # 检查prep阶段是否有错误
            if "error" in prep_result:
                raise ValueError(prep_result["error"])
            
            print("🔄 开始短规划处理...")
            
            # 动态导入避免循环导入
            from ..flows.short_planning_flow import ShortPlanningFlow
            
            # 创建短规划流程
            planning_flow = ShortPlanningFlow()
            
            # 准备流程输入数据
            flow_input = {
                "structured_requirements": prep_result["structured_requirements"],
                "dialogue_history": prep_result.get("dialogue_history", {})
            }
            
            # 执行流程
            flow_result = planning_flow.run(flow_input)
            
            processing_time = time.time() - prep_result["processing_start_time"]
            
            return {
                "processing_success": True,
                "flow_result": flow_result,
                "processing_time": processing_time
            }
            
        except Exception as e:
            print(f"❌ 短规划流程执行失败: {e}")
            raise e
    
    async def post_async(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存短规划结果并更新共享状态"""
        
        # 检查执行结果
        if "error" in exec_res:
            error_msg = exec_res["error"]
            shared["short_planning_error"] = error_msg
            shared["current_stage"] = "short_planning_failed"
            
            # 添加错误系统消息
            system_messages = shared.get("system_messages", [])
            system_messages.append({
                "message": f"短规划失败: {error_msg}",
                "agent_source": "ProcessShortPlanningNode",
                "timestamp": time.time(),
                "error": True
            })
            shared["system_messages"] = system_messages
            
            print(f"❌ 短规划失败: {error_msg}")
            return "error"
        
        # 处理成功的情况
        if exec_res.get("processing_success"):
            # 更新当前阶段
            shared["current_stage"] = "short_planning_completed"
            
            # 保存处理时间
            processing_time = exec_res.get("processing_time", 0)
            shared["short_planning_processing_time"] = processing_time
            
            # 添加成功系统消息
            system_messages = shared.get("system_messages", [])
            
            # 检查是否有确认文档生成
            confirmation_document = shared.get("confirmation_document", {})
            
            if confirmation_document:
                structure = confirmation_document.get("structure", {})
                steps_count = len(structure.get("implementation_steps", []))
                functions_count = len(structure.get("core_functions", []))
                
                system_messages.append({
                    "message": f"短规划完成: 生成了包含{steps_count}个实现步骤、{functions_count}个核心功能的确认文档",
                    "agent_source": "ProcessShortPlanningNode", 
                    "timestamp": time.time(),
                    "processing_time": processing_time,
                    "success": True
                })
                
                print(f"✅ 短规划完成，处理时间: {processing_time:.2f}秒")
                print(f"   生成实现步骤: {steps_count}，核心功能: {functions_count}")
                
            else:
                system_messages.append({
                    "message": "短规划流程完成，但未生成确认文档",
                    "agent_source": "ProcessShortPlanningNode",
                    "timestamp": time.time(),
                    "warning": True
                })
                
                print("⚠️ 短规划流程完成，但未生成确认文档")
            
            shared["system_messages"] = system_messages
            
            # 更新元数据
            metadata = shared.get("metadata", {})
            processing_stages = metadata.get("processing_stages", [])
            processing_stages.append({
                "stage": "short_planning",
                "start_time": prep_res.get("processing_start_time", 0),
                "end_time": time.time(),
                "duration": processing_time,
                "success": True
            })
            metadata["processing_stages"] = processing_stages
            metadata["total_processing_time"] = metadata.get("total_processing_time", 0) + processing_time
            shared["metadata"] = metadata
            
            return "success"
        
        else:
            # 处理未知状态
            shared["short_planning_error"] = "Unknown processing state"
            shared["current_stage"] = "short_planning_failed"
            
            system_messages = shared.get("system_messages", [])
            system_messages.append({
                "message": "短规划处理状态未知",
                "agent_source": "ProcessShortPlanningNode",
                "timestamp": time.time(),
                "warning": True
            })
            shared["system_messages"] = system_messages
            
            print("⚠️ 短规划处理状态未知")
            return "warning"
