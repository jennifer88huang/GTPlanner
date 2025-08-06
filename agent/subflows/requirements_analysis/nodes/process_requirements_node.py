"""
Process Requirements Node

Requirements Analysis Agent的主节点，负责协调整个需求分析流程，
并更新主Agent的共享状态。
"""

import time
from typing import Dict, Any
from pocketflow import Node


class ProcessRequirementsNode(Node):
    """需求处理主节点"""
    
    def __init__(self):
        super().__init__()
        self.name = "ProcessRequirementsNode"
        self.description = "协调需求分析流程并更新主Agent共享状态"
    
    def prep(self, shared: Dict[str, Any]) -> Dict[str, Any]:
        """准备需求处理 - 使用pocketflow字典共享变量"""
        # 从主Agent共享状态获取输入数据
        dialogue_history = shared.get("dialogue_history", "")
        user_intent = shared.get("user_intent", {})
        
        # 如果没有对话历史，尝试从用户意图中获取原始请求
        if not dialogue_history and isinstance(user_intent, dict):
            dialogue_history = user_intent.get("original_request", "")
        
        if not dialogue_history and not user_intent:
            print("❌ 缺少必要的输入数据")
            # 返回错误标记，让exec方法处理
        
        return {
            "dialogue_history": dialogue_history,
            "user_intent": user_intent
        }
    
    def exec(self, prep_result: Dict[str, Any]) -> Dict[str, Any]:
        """执行需求分析流程"""
        try:
            # 检查prep阶段是否有错误
            if not prep_result.get("dialogue_history") and not prep_result.get("user_intent"):
                return {
                    "processing_success": False,
                    "error": "缺少必要的输入数据：dialogue_history 和 user_intent 都为空"
                }

            print("🔄 开始需求分析处理...")

            # 动态导入避免循环导入
            from ..flows.requirements_analysis_flow import RequirementsAnalysisFlow

            # 创建需求分析流程
            requirements_flow = RequirementsAnalysisFlow()

            # 准备子流程的共享变量
            subflow_shared = {
                "dialogue_history": prep_result["dialogue_history"],
                "user_intent": prep_result["user_intent"],

                # 用于存储流程中的数据
                "extracted_requirements": {},
                "structured_requirements": {},
                "validation_report": {}
            }

            # 执行需求分析流程
            try:
                flow_success = requirements_flow.run(subflow_shared)
            except Exception as flow_error:
                print(f"⚠️ 子流程执行出错: {flow_error}")
                # 即使子流程出错，也尝试继续处理
                flow_success = False
            
            if flow_success:
                return {
                    "processing_success": True,
                    "structured_requirements": subflow_shared.get("structured_requirements", {}),
                    "validation_report": subflow_shared.get("validation_report", {}),
                    "requirements_metadata": {
                        "analysis_completed_at": time.time(),
                        "analysis_success": True,
                        "quality_score": subflow_shared.get("validation_report", {}).get("overall_score", 0.8)
                    }
                }
            else:
                return {
                    "processing_success": False,
                    "error": "需求分析流程执行失败"
                }
                
        except Exception as e:
            print(f"❌ 需求分析处理出错: {e}")
            return {
                "processing_success": False,
                "error": str(e)
            }
    
    def post(self, shared: Dict[str, Any], prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """保存需求分析结果并更新主Agent共享状态 - 使用pocketflow字典共享变量"""
        # 检查执行结果
        if "error" in exec_res:
            error_msg = exec_res["error"]
            shared["requirements_analysis_error"] = error_msg
            shared["current_stage"] = "requirements_analysis_failed"

            # 添加错误系统消息
            system_messages = shared.get("system_messages", [])
            system_messages.append({
                "message": f"需求分析失败: {error_msg}",
                "agent_source": "ProcessRequirementsNode",
                "timestamp": time.time(),
                "error": True
            })
            shared["system_messages"] = system_messages

            print(f"❌ 需求分析失败: {error_msg}")
            return "error"
        
        processing_success = exec_res.get("processing_success", False)
        structured_requirements = exec_res.get("structured_requirements", {})
        validation_report = exec_res.get("validation_report", {})
        requirements_metadata = exec_res.get("requirements_metadata", {})
        
        # 保存结构化需求到主Agent共享状态
        if processing_success:
            if structured_requirements:
                shared["structured_requirements"] = structured_requirements
            if validation_report:
                shared["requirements_validation_report"] = validation_report
            if requirements_metadata:
                shared["requirements_metadata"] = requirements_metadata
        
        # 更新处理阶段
        shared["current_stage"] = "requirements_analysis_completed"
        
        # 添加系统消息
        system_messages = shared.get("system_messages", [])
        quality_score = requirements_metadata.get("quality_score", 0.8)
        core_features_count = len(structured_requirements.get("functional_requirements", {}).get("core_features", []))
        
        system_messages.append({
            "message": f"需求分析完成，质量评分: {quality_score:.2f}，识别了 {core_features_count} 个核心功能",
            "agent_source": "ProcessRequirementsNode",
            "timestamp": time.time(),
            "quality_score": quality_score,
            "core_features_count": core_features_count,
            "success": processing_success
        })
        shared["system_messages"] = system_messages
        
        # 更新元数据
        metadata = shared.get("metadata", {})
        processing_stages = metadata.get("processing_stages", [])
        if "requirements_analysis" not in processing_stages:
            processing_stages.append("requirements_analysis")
        metadata.update({
            "processing_stages": processing_stages,
            "last_updated": time.time(),
            "total_processing_time": metadata.get("total_processing_time", 0) + 30.0  # 估算处理时间
        })
        shared["metadata"] = metadata
        
        print(f"✅ 需求分析处理完成，质量评分: {quality_score:.2f}")
        
        # 返回下一步动作 - 基于pocketflow最佳实践
        if processing_success:
            return "success"  # 成功完成，可以继续下一个节点
        else:
            return "failed"   # 处理失败，需要错误处理
    

