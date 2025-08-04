"""
需求分析Agent子流程 (Requirements Analysis Flow)

协调需求解析节点完成完整的需求分析任务。
基于pocketflow.Flow实现，确保原子性操作和错误处理。

流程步骤：
1. 文本预处理和验证
2. 调用Node_Req进行需求提取
3. 结果验证和后处理
4. 更新共享状态
"""

from typing import Dict, Any, Optional
from pocketflow import Flow
from ..nodes.node_req import NodeReq
from ..shared import get_shared_state


class RequirementsAnalysisFlow(Flow):
    """需求分析Agent子流程"""
    
    def __init__(self, max_retries: int = 2, wait: float = 1.0):
        """
        初始化需求分析流程
        
        Args:
            max_retries: 最大重试次数
            wait: 重试等待时间
        """
        super().__init__(max_retries=max_retries, wait=wait)
        
        # 初始化节点
        self.node_req = NodeReq(max_retries=2, wait=1.0)
    
    def prep(self, shared_state=None) -> Dict[str, Any]:
        """
        准备阶段：验证输入和设置流程参数
        
        Args:
            shared_state: 共享状态对象
            
        Returns:
            准备结果字典
        """
        try:
            # 获取共享状态
            if shared_state is None:
                shared_state = get_shared_state()
            
            # 验证对话历史是否存在
            if not hasattr(shared_state, 'dialogue_history') or not shared_state.dialogue_history.messages:
                return {
                    "error": "No dialogue history available for requirements analysis",
                    "shared_state": shared_state,
                    "flow_config": {
                        "enable_validation": True,
                        "require_confirmation": False,
                        "min_confidence_threshold": 0.3
                    }
                }
            
            # 检查是否有用户消息
            user_messages = shared_state.dialogue_history.get_user_messages()
            if not user_messages:
                return {
                    "error": "No user messages found for requirements analysis",
                    "shared_state": shared_state,
                    "flow_config": {
                        "enable_validation": True,
                        "require_confirmation": False,
                        "min_confidence_threshold": 0.3
                    }
                }
            
            # 流程配置
            flow_config = {
                "enable_validation": True,
                "require_confirmation": False,
                "min_confidence_threshold": 0.3,
                "max_processing_time": 60000  # 60秒
            }
            
            return {
                "shared_state": shared_state,
                "flow_config": flow_config,
                "user_messages_count": len(user_messages),
                "total_messages_count": shared_state.dialogue_history.total_messages
            }
            
        except Exception as e:
            return {
                "error": f"Requirements analysis flow preparation failed: {str(e)}",
                "shared_state": shared_state or get_shared_state(),
                "flow_config": {
                    "enable_validation": True,
                    "require_confirmation": False,
                    "min_confidence_threshold": 0.3
                }
            }
    
    def exec(self, prep_res: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行阶段：运行需求分析流程
        
        Args:
            prep_res: 准备阶段的结果
            
        Returns:
            执行结果字典
        """
        if "error" in prep_res:
            raise ValueError(prep_res["error"])
        
        shared_state = prep_res["shared_state"]
        flow_config = prep_res["flow_config"]
        
        try:
            # 更新处理阶段
            shared_state.update_stage("requirements_analysis_started")
            
            # 步骤1: 执行需求解析
            self.node_req.params = {}  # 清空参数，让节点从共享状态获取数据
            
            # 调用Node_Req进行需求分析
            req_prep_result = self.node_req.prep(shared_state)
            if "error" in req_prep_result:
                raise RuntimeError(f"Node_Req preparation failed: {req_prep_result['error']}")
            
            req_exec_result = self.node_req.exec(req_prep_result)
            if "error" in req_exec_result:
                raise RuntimeError(f"Node_Req execution failed: {req_exec_result['error']}")
            
            # 调用Node_Req的后处理
            req_post_result = self.node_req.post(shared_state, req_prep_result, req_exec_result)
            if req_post_result == "error":
                raise RuntimeError("Node_Req post-processing failed")
            
            # 步骤2: 验证分析结果
            validation_result = self._validate_analysis_result(req_exec_result, flow_config)
            
            # 步骤3: 更新流程状态
            shared_state.update_stage("requirements_analysis_completed")
            
            return {
                "analysis_result": req_exec_result,
                "validation_result": validation_result,
                "flow_status": "completed",
                "confidence_score": req_exec_result.get("confidence_score", 0.0),
                "requirements_extracted": True,
                "processing_summary": {
                    "entities_count": len(req_exec_result.get("extracted_entities", {}).get("business_objects", [])),
                    "features_count": len(req_exec_result.get("functional_requirements", {}).get("core_features", [])),
                    "validation_passed": validation_result.get("passed", False)
                }
            }
            
        except Exception as e:
            # 记录错误到共享状态
            shared_state.record_error(e, "RequirementsAnalysisFlow.exec")
            shared_state.update_stage("requirements_analysis_failed")
            raise RuntimeError(f"Requirements analysis flow execution failed: {str(e)}")
    
    def post(self, shared_state, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """
        后处理阶段：完成流程并记录结果
        
        Args:
            shared_state: 共享状态对象
            prep_res: 准备阶段结果
            exec_res: 执行阶段结果
            
        Returns:
            下一步动作
        """
        try:
            if "error" in exec_res:
                shared_state.record_error(Exception(exec_res["error"]), "RequirementsAnalysisFlow.exec")
                return "error"
            
            # 添加流程完成的系统消息
            confidence_score = exec_res.get("confidence_score", 0.0)
            processing_summary = exec_res.get("processing_summary", {})
            
            shared_state.add_system_message(
                f"需求分析流程完成，置信度: {confidence_score:.2f}，"
                f"提取实体: {processing_summary.get('entities_count', 0)}个，"
                f"识别功能: {processing_summary.get('features_count', 0)}个",
                agent_source="RequirementsAnalysisFlow",
                flow_status=exec_res.get("flow_status", "completed"),
                confidence_score=confidence_score,
                validation_passed=processing_summary.get("validation_passed", False)
            )
            
            # 检查是否需要进入下一个流程
            if confidence_score >= prep_res["flow_config"]["min_confidence_threshold"]:
                return "proceed_to_planning"
            else:
                return "require_clarification"
            
        except Exception as e:
            shared_state.record_error(e, "RequirementsAnalysisFlow.post")
            return "error"
    
    def exec_fallback(self, prep_res: Dict[str, Any], exc: Exception) -> Dict[str, Any]:
        """
        执行失败时的降级处理
        
        Args:
            prep_res: 准备阶段结果
            exc: 异常对象
            
        Returns:
            降级结果
        """
        shared_state = prep_res.get("shared_state")
        if shared_state:
            shared_state.update_stage("requirements_analysis_fallback")
        
        return {
            "analysis_result": {
                "extracted_entities": {"business_objects": [], "actors": ["用户"], "systems": ["系统"]},
                "functional_requirements": {"core_features": ["基础功能"], "user_stories": [], "workflows": []},
                "non_functional_requirements": {"performance": [], "security": [], "scalability": []},
                "confidence_score": 0.1,
                "fallback_reason": str(exc)
            },
            "validation_result": {"passed": False, "issues": ["流程执行失败"], "warnings": []},
            "flow_status": "fallback",
            "confidence_score": 0.1,
            "requirements_extracted": False,
            "processing_summary": {
                "entities_count": 0,
                "features_count": 1,
                "validation_passed": False
            },
            "fallback_reason": str(exc)
        }
    
    def _validate_analysis_result(self, analysis_result: Dict[str, Any], 
                                 flow_config: Dict[str, Any]) -> Dict[str, Any]:
        """验证分析结果的质量"""
        validation_result = {
            "passed": True,
            "issues": [],
            "warnings": []
        }
        
        try:
            # 检查置信度
            confidence_score = analysis_result.get("confidence_score", 0.0)
            min_threshold = flow_config.get("min_confidence_threshold", 0.3)
            
            if confidence_score < min_threshold:
                validation_result["warnings"].append(f"置信度较低: {confidence_score:.2f} < {min_threshold}")
            
            # 检查实体提取
            entities = analysis_result.get("extracted_entities", {})
            if not entities.get("business_objects") and not entities.get("actors"):
                validation_result["warnings"].append("未提取到明确的业务实体或参与者")
            
            # 检查功能需求
            func_reqs = analysis_result.get("functional_requirements", {})
            if not func_reqs.get("core_features"):
                validation_result["issues"].append("未识别到核心功能需求")
                validation_result["passed"] = False
            
            # 检查用户意图
            user_intent = analysis_result.get("user_intent", {})
            if not user_intent.get("primary_goal"):
                validation_result["warnings"].append("用户主要目标不明确")
            
            # 检查项目概览
            project_overview = analysis_result.get("project_overview", {})
            if not project_overview.get("title"):
                validation_result["warnings"].append("项目标题未生成")
            
        except Exception as e:
            validation_result["issues"].append(f"验证过程出错: {str(e)}")
            validation_result["passed"] = False
        
        return validation_result
